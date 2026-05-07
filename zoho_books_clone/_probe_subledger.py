"""Investigate AR/AP sub-ledger discrepancies."""
import frappe
from frappe.utils import flt

COMPANY = "Eiffele gaming"

def run():
    # ── AR: submitted SIs ─────────────────────────────────────────────────
    print("\n=== AR Sub-ledger ===")
    sis = frappe.db.sql("""
        SELECT name, customer, grand_total, outstanding_amount
        FROM `tabSales Invoice`
        WHERE company = %s AND docstatus = 1
        ORDER BY name
    """, COMPANY, as_dict=True)
    print(f"Submitted SIs ({len(sis)}):")
    total_si_outstanding = 0
    for s in sis:
        print(f"  {s.name}: customer={s.customer}, grand_total={s.grand_total:.0f}, outstanding={s.outstanding_amount:.0f}")
        total_si_outstanding += flt(s.outstanding_amount)
    print(f"  Total SI outstanding: {total_si_outstanding:.2f}")

    # GL Receivable per voucher
    print("\nGL Receivable per voucher (is_cancelled=0):")
    gl_ar = frappe.db.sql("""
        SELECT g.voucher_type, g.voucher_no,
               SUM(g.debit) - SUM(g.credit) AS balance
        FROM `tabGeneral Ledger Entry` g
        JOIN `tabAccount` a ON a.name = g.account
        WHERE g.company = %s
          AND g.is_cancelled = 0
          AND a.account_type = 'Receivable'
        GROUP BY g.voucher_no, g.voucher_type
        HAVING ABS(balance) > 0.01
        ORDER BY g.voucher_no
    """, COMPANY, as_dict=True)
    total_gl_ar = 0
    for r in gl_ar:
        print(f"  {r.voucher_type} {r.voucher_no}: {flt(r.balance):.2f}")
        total_gl_ar += flt(r.balance)
    print(f"  Total GL Receivable: {total_gl_ar:.2f}")

    # ── AP: submitted PINVs ───────────────────────────────────────────────
    print("\n=== AP Sub-ledger ===")
    pinvs = frappe.db.sql("""
        SELECT name, supplier, grand_total, outstanding_amount
        FROM `tabPurchase Invoice`
        WHERE company = %s AND docstatus = 1
        ORDER BY name
    """, COMPANY, as_dict=True)
    print(f"Submitted PINVs ({len(pinvs)}):")
    total_pinv_outstanding = 0
    for p in pinvs:
        print(f"  {p.name}: grand_total={p.grand_total:.0f}, outstanding={p.outstanding_amount:.0f}")
        total_pinv_outstanding += flt(p.outstanding_amount)
    print(f"  Total PINV outstanding: {total_pinv_outstanding:.2f}")

    # GL Payable per voucher
    print("\nGL Payable per voucher (is_cancelled=0):")
    gl_ap = frappe.db.sql("""
        SELECT g.voucher_type, g.voucher_no,
               SUM(g.credit) - SUM(g.debit) AS balance
        FROM `tabGeneral Ledger Entry` g
        JOIN `tabAccount` a ON a.name = g.account
        WHERE g.company = %s
          AND g.is_cancelled = 0
          AND a.account_type = 'Payable'
        GROUP BY g.voucher_no, g.voucher_type
        HAVING ABS(balance) > 0.01
        ORDER BY g.voucher_no
    """, COMPANY, as_dict=True)
    total_gl_ap = 0
    for r in gl_ap:
        print(f"  {r.voucher_type} {r.voucher_no}: {flt(r.balance):.2f}")
        total_gl_ap += flt(r.balance)
    print(f"  Total GL Payable: {total_gl_ap:.2f}")

    # Payment entries and which invoices they reference
    print("\nPayment Entry References (submitted):")
    pay_refs = frappe.db.sql("""
        SELECT pe.name, pe.payment_type, per.reference_doctype, per.reference_name, per.allocated_amount
        FROM `tabPayment Entry` pe
        JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
        WHERE pe.company = %s AND pe.docstatus = 1
        ORDER BY pe.name
    """, COMPANY, as_dict=True)
    for r in pay_refs:
        print(f"  {r.name} ({r.payment_type}): {r.reference_doctype} {r.reference_name} allocated={r.allocated_amount:.0f}")
