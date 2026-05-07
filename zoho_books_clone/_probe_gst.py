import frappe
from frappe.utils import flt, today, get_first_day, get_last_day, add_days

COMPANY = "Eiffele gaming"

def run():
    t = today()
    som = str(get_first_day(add_days(t, -60)))
    eom = str(get_last_day(t))

    # Tax Lines on submitted SIs
    si_tax_lines = frappe.db.sql("""
        SELECT tl.tax_type, tl.account_head, tl.tax_amount, tl.parent
        FROM `tabTax Line` tl
        JOIN `tabSales Invoice` si ON si.name = tl.parent
        WHERE si.company = %(co)s AND si.docstatus = 1
        ORDER BY tl.parent, tl.idx
    """, {"co": COMPANY}, as_dict=True)
    print("SI Tax Lines:")
    for r in si_tax_lines:
        print(f"  {r.parent}: type={r.tax_type}  account={r.account_head}  amt={r.tax_amount}")

    # Tax Lines on submitted PINVs
    pi_tax_lines = frappe.db.sql("""
        SELECT tl.tax_type, tl.account_head, tl.tax_amount, tl.parent
        FROM `tabTax Line` tl
        JOIN `tabPurchase Invoice` pi ON pi.name = tl.parent
        WHERE pi.company = %(co)s AND pi.docstatus = 1
        ORDER BY tl.parent, tl.idx
    """, {"co": COMPANY}, as_dict=True)
    print("\nPINV Tax Lines:")
    for r in pi_tax_lines:
        print(f"  {r.parent}: type={r.tax_type}  account={r.account_head}  amt={r.tax_amount}")

    # Tax GL account balances
    tax_accounts = frappe.get_all("Account",
        filters={"company": COMPANY, "account_type": "Tax", "is_group": 0},
        fields=["name", "account_name"])
    print("\nTax Accounts:")
    for a in tax_accounts:
        bal = frappe.db.sql("""
            SELECT COALESCE(SUM(debit),0) AS dr, COALESCE(SUM(credit),0) AS cr
            FROM `tabGeneral Ledger Entry`
            WHERE account=%s AND is_cancelled=0
        """, a.name, as_dict=True)
        b = bal[0] if bal else {}
        print(f"  {a.name}: DR={flt(b.get('dr')):.2f}  CR={flt(b.get('cr')):.2f}  net={flt(b.get('dr'))-flt(b.get('cr')):.2f}")
