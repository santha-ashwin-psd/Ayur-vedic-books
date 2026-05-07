import frappe
from frappe.utils import flt, today

COMPANY = "Eiffele gaming"

def run():
    # Check the two suspicious SIs
    for inv in ["INV-2026-00034", "INV-2026-00035"]:
        si_status = frappe.db.get_value("Sales Invoice", inv, "docstatus") if frappe.db.exists("Sales Invoice", inv) else "NOT FOUND"
        gl_rows = frappe.db.sql("""
            SELECT name, account, debit, credit, is_cancelled, is_reversal
            FROM `tabGeneral Ledger Entry` WHERE voucher_no=%s
        """, inv, as_dict=True)
        print(f"\n{inv}: docstatus={si_status}, GL rows={len(gl_rows)}")
        for r in gl_rows:
            print(f"  {r.account}: DR={r.debit:.0f} CR={r.credit:.0f} cancelled={r.is_cancelled} reversal={r.is_reversal}")

    # Accounting equation gap analysis
    rows = frappe.db.sql("""
        SELECT a.account_type, COALESCE(SUM(g.debit)-SUM(g.credit),0) AS net
        FROM `tabGeneral Ledger Entry` g JOIN `tabAccount` a ON a.name=g.account
        WHERE g.company=%s AND g.is_cancelled=0
        GROUP BY a.account_type
    """, COMPANY, as_dict=True)
    print("\nGL by account_type:")
    for r in rows:
        print(f"  {r.account_type}: {flt(r.net):.2f}")

    # Income accounts net (credit-normal: negative means earned)
    income_net = next((r.net for r in rows if r.account_type == "Income"), 0)
    expense_net = next((r.net for r in rows if r.account_type == "Expense"), 0)
    cogs_net = next((r.net for r in rows if r.account_type == "Cost of Goods Sold"), 0)
    equity_net = next((r.net for r in rows if r.account_type == "Equity"), 0)
    print(f"\nP&L balances in GL (debit-credit convention):")
    print(f"  Income net (DR-CR): {income_net:.2f}  → P&L income = {-income_net:.2f}")
    print(f"  Expense net (DR-CR): {expense_net:.2f}  → P&L expense = {-expense_net:.2f}")
    print(f"  COGS net (DR-CR): {cogs_net:.2f}")
    print(f"  Net profit: {-income_net - expense_net - cogs_net:.2f}")
    print(f"  Equity net (DR-CR): {equity_net:.2f}  → equity balance = {-equity_net:.2f}")

    # Payable sub-ledger detail
    print("\nPayable GL detail:")
    payable_gl = frappe.db.sql("""
        SELECT g.voucher_type, g.voucher_no, SUM(g.credit)-SUM(g.debit) AS balance
        FROM `tabGeneral Ledger Entry` g JOIN `tabAccount` a ON a.name=g.account
        WHERE g.company=%s AND g.is_cancelled=0 AND a.account_type='Payable'
        GROUP BY g.voucher_no, g.voucher_type
        HAVING ABS(balance)>0.01
    """, COMPANY, as_dict=True)
    total_payable_gl = 0
    for r in payable_gl:
        print(f"  {r.voucher_type} {r.voucher_no}: {flt(r.balance):.2f}")
        total_payable_gl += flt(r.balance)
    print(f"  Total GL Payable balance: {total_payable_gl:.2f}")

    pinv_outstanding = flt(frappe.db.sql(
        "SELECT COALESCE(SUM(outstanding_amount),0) AS t FROM `tabPurchase Invoice` WHERE company=%s AND docstatus=1",
        COMPANY, as_dict=True)[0].t)
    print(f"  PINV outstanding_amount sum: {pinv_outstanding:.2f}")
