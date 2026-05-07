"""Deeper AP/AR investigation."""
import frappe
from frappe.utils import flt

COMPANY = "Eiffele gaming"

def run():
    # PINV details with is_return
    print("=== PINVs with is_return ===")
    pinvs = frappe.db.sql("""
        SELECT name, grand_total, outstanding_amount, is_return, return_against
        FROM `tabPurchase Invoice`
        WHERE company = %s AND docstatus = 1
        ORDER BY name
    """, COMPANY, as_dict=True)
    for p in pinvs:
        print(f"  {p.name}: grand_total={p.grand_total:.0f}, outstanding={p.outstanding_amount:.0f}, is_return={p.is_return}, return_against={p.return_against}")

    # GL Payable per PINV with detail
    print("\n=== GL Payable detail per PINV (all rows, is_cancelled=0) ===")
    gl_detail = frappe.db.sql("""
        SELECT g.voucher_no, g.account, g.debit, g.credit, g.is_cancelled, g.is_reversal
        FROM `tabGeneral Ledger Entry` g
        JOIN `tabAccount` a ON a.name = g.account
        WHERE g.company = %s
          AND g.is_cancelled = 0
          AND a.account_type = 'Payable'
        ORDER BY g.voucher_no, g.creation
    """, COMPANY, as_dict=True)
    for r in gl_detail:
        print(f"  {r.voucher_no}: DR={r.debit:.0f} CR={r.credit:.0f}")

    # Credit Notes detail
    print("\n=== Credit Notes (Sales Returns) ===")
    cns = frappe.db.sql("""
        SELECT name, grand_total, outstanding_amount, is_return
        FROM `tabSales Invoice`
        WHERE company = %s AND docstatus = 1 AND is_return = 1
        ORDER BY name
    """, COMPANY, as_dict=True)
    for c in cns:
        print(f"  {c.name}: grand_total={c.grand_total:.0f}, outstanding={c.outstanding_amount:.0f}")

    cn_standalone = frappe.db.sql("""
        SELECT name, grand_total, outstanding_amount
        FROM `tabCredit Note`
        WHERE company = %s AND docstatus = 1
        ORDER BY name
    """, COMPANY, as_dict=True) if frappe.db.table_exists("tabCredit Note") else []
    if cn_standalone:
        print("\n=== Standalone Credit Notes ===")
        for c in cn_standalone:
            print(f"  {c.name}: grand_total={c.grand_total:.0f}, outstanding={c.outstanding_amount:.0f}")

    # Find CN GL entries
    print("\n=== GL Receivable entries for Credit Notes (CN-*) ===")
    cn_gl = frappe.db.sql("""
        SELECT g.voucher_type, g.voucher_no, g.account, g.debit, g.credit
        FROM `tabGeneral Ledger Entry` g
        JOIN `tabAccount` a ON a.name = g.account
        WHERE g.is_cancelled = 0
          AND a.account_type = 'Receivable'
          AND g.voucher_no LIKE 'CN-%%'
        ORDER BY g.voucher_no
    """, as_dict=True)
    for r in cn_gl:
        print(f"  {r.voucher_type} {r.voucher_no}: {r.account} DR={r.debit:.0f} CR={r.credit:.0f}")

    # Check Credit Note doctype
    cn_docs = frappe.db.sql("""
        SELECT name, grand_total, outstanding_amount, docstatus
        FROM `tabCredit Note`
        ORDER BY name
        LIMIT 10
    """, as_dict=True) if frappe.db.table_exists("tabCredit Note") else []
    if cn_docs:
        print("\n=== Credit Note records ===")
        for c in cn_docs:
            print(f"  {c.name}: grand_total={c.grand_total:.0f}, outstanding={c.outstanding_amount:.0f}, docstatus={c.docstatus}")
