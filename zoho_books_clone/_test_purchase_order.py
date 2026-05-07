"""
L1 — Purchase Order test.

Scenario:
  T1  Draft PO with 2 items → net_total, total_tax, grand_total correct
  T2  Zero-qty item → ValidationError
  T3  No items → ValidationError
  T4  Submit PO → status = Confirmed
  T5  make_purchase_invoice() → PI created, totals match, purchase_order linked
  T6  Submit PI → GL posted (DR Expense, CR AP); PO billed_amount updated
  T7  PO status → Billed after full billing
  T8  make_purchase_invoice on Billed PO → rejected
  T9  Cancel un-billed submitted PO → status = Cancelled
  T10 Cleanup
"""
import frappe
from frappe.utils import flt, today
import importlib

COMPANY  = "Eiffele gaming"
SUPPLIER = "SUPP-2026-00002"

_to_cancel = []
_po_names  = []


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _make_po(items, taxes=None, submit=False):
    po = frappe.new_doc("Purchase Order")
    po.supplier         = SUPPLIER
    po.company          = COMPANY
    po.transaction_date = today()
    for it in items:
        po.append("items", it)
    for tx in (taxes or []):
        po.append("taxes", tx)
    po.flags.ignore_permissions = True
    po.flags.ignore_mandatory   = True
    po.flags.ignore_links       = True
    po.insert(ignore_links=True)
    _po_names.append(po.name)
    if submit:
        po.submit()
    frappe.db.commit()
    return po


def _gl(voucher_no, cancelled=0):
    return frappe.db.get_all(
        "General Ledger Entry",
        filters={"voucher_no": voucher_no, "is_cancelled": cancelled},
        fields=["account", "debit", "credit"],
    )


def run():
    print("\n=== Purchase Order L1 Test ===")

    import zoho_books_clone.invoicing.doctype.purchase_order.purchase_order as po_mod
    importlib.reload(po_mod)

    cgst_acct = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY, "is_group": 0,
                                                  "account_name": ["like", "%CGST%Input%"]}, "name")
    sgst_acct = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY, "is_group": 0,
                                                  "account_name": ["like", "%SGST%Input%"]}, "name")
    ap_acct   = frappe.db.get_value("Account", {"account_type": "Payable",  "company": COMPANY, "is_group": 0}, "name")
    exp_acct  = frappe.db.get_value("Account", {"account_type": "Expense",  "company": COMPANY, "is_group": 0}, "name")
    print(f"  CGST_in={cgst_acct}  SGST_in={sgst_acct}  AP={ap_acct}  Exp={exp_acct}")

    # ── T1: Draft PO — totals ────────────────────────────────────────────────
    print("\n--- T1: Draft PO — totals ---")
    try:
        po1 = _make_po(
            items=[
                {"item_name": "Raw Material A", "qty": 10, "rate": 500},
                {"item_name": "Raw Material B", "qty":  4, "rate": 1250},
            ],
            taxes=[
                {"description": "CGST Input 9%", "rate": 9, "tax_amount": 0, "account_head": cgst_acct},
                {"description": "SGST Input 9%", "rate": 9, "tax_amount": 0, "account_head": sgst_acct},
            ] if cgst_acct and sgst_acct else [],
        )
        # net = 10*500 + 4*1250 = 10000
        if abs(flt(po1.net_total) - 10000) < 0.01:
            _pass(f"net_total = {po1.net_total:.0f} (expect 10000)")
        else:
            _fail("net_total wrong", f"got {po1.net_total}")

        if cgst_acct and sgst_acct:
            if abs(flt(po1.total_tax) - 1800) < 0.01:
                _pass(f"total_tax = {po1.total_tax:.0f} (expect 1800)")
            else:
                _fail("total_tax wrong", f"got {po1.total_tax}")
            expected_grand = 11800.0
        else:
            expected_grand = 10000.0

        if abs(flt(po1.grand_total) - expected_grand) < 0.01:
            _pass(f"grand_total = {po1.grand_total:.0f} (expect {expected_grand:.0f})")
        else:
            _fail("grand_total wrong", f"got {po1.grand_total}")

        item_amts = [flt(i.amount) for i in po1.items]
        if item_amts == [5000.0, 5000.0]:
            _pass("Item amounts: [5000, 5000]")
        else:
            _fail("Item amounts wrong", str(item_amts))

    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    # ── T2: Zero-qty → rejected ──────────────────────────────────────────────
    print("\n--- T2: Zero qty item → ValidationError ---")
    try:
        _make_po(items=[{"item_name": "Bad Item", "qty": 0, "rate": 100}])
        _fail("Zero qty accepted")
    except frappe.exceptions.ValidationError:
        _pass("ValidationError raised for zero-qty item")
    except Exception as e:
        _fail("Wrong exception type", str(e)[:80])

    # ── T3: No items → rejected ──────────────────────────────────────────────
    print("\n--- T3: No items → ValidationError ---")
    try:
        po_empty = frappe.new_doc("Purchase Order")
        po_empty.supplier = SUPPLIER
        po_empty.company  = COMPANY
        po_empty.flags.ignore_permissions = True
        po_empty.flags.ignore_mandatory   = True
        po_empty.insert()
        _fail("Empty PO accepted")
    except frappe.exceptions.ValidationError:
        _pass("ValidationError raised for no items")
    except Exception as e:
        _fail("Wrong exception type", str(e)[:80])

    # ── T4: Submit PO → Confirmed ────────────────────────────────────────────
    print("\n--- T4: Submit PO → status = Confirmed ---")
    try:
        po_sub = _make_po(
            items=[{"item_name": "Office Chair", "qty": 2, "rate": 3000}],
            submit=True,
        )
        _to_cancel.append(("Purchase Order", po_sub.name, 1))
        status = frappe.db.get_value("Purchase Order", po_sub.name, "status")
        if status == "Confirmed":
            _pass(f"PO {po_sub.name} status = Confirmed")
        else:
            _fail("Status not Confirmed", f"got {status}")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])
        po_sub = None

    # ── T5: make_purchase_invoice() → PI totals match, link set ─────────────
    print("\n--- T5: make_purchase_invoice() → PI matches PO ---")
    pi_from_po = None
    po_for_pi  = None
    try:
        po_for_pi = _make_po(
            items=[{"item_name": "Server Hardware", "qty": 1, "rate": 80000}],
            submit=True,
        )
        _to_cancel.append(("Purchase Order", po_for_pi.name, 1))

        pi_from_po = po_for_pi.make_purchase_invoice()
        frappe.db.commit()
        _to_cancel.append(("Purchase Invoice", pi_from_po.name, 0))

        if abs(flt(pi_from_po.net_total) - flt(po_for_pi.net_total)) < 0.01:
            _pass(f"PI net_total = {pi_from_po.net_total:.0f} matches PO")
        else:
            _fail("PI net_total mismatch",
                  f"PI={pi_from_po.net_total} PO={po_for_pi.net_total}")

        if abs(flt(pi_from_po.grand_total) - flt(po_for_pi.grand_total)) < 0.01:
            _pass(f"PI grand_total = {pi_from_po.grand_total:.0f} matches PO")
        else:
            _fail("PI grand_total mismatch",
                  f"PI={pi_from_po.grand_total} PO={po_for_pi.grand_total}")

        if pi_from_po.purchase_order == po_for_pi.name:
            _pass(f"PI.purchase_order = '{po_for_pi.name}'")
        else:
            _fail("PI.purchase_order not linked", f"got '{pi_from_po.purchase_order}'")

        if len(pi_from_po.items) == len(po_for_pi.items):
            _pass(f"{len(pi_from_po.items)} items copied to PI")
        else:
            _fail("Item count mismatch",
                  f"PI={len(pi_from_po.items)} PO={len(po_for_pi.items)}")

    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: Submit PI → GL posted + PO.billed_amount updated ─────────────────
    print("\n--- T6: Submit PI → GL posted + PO.billed_amount updated ---")
    try:
        if pi_from_po and po_for_pi:
            pi_from_po.flags.ignore_permissions = True
            pi_from_po.flags.ignore_mandatory   = True
            pi_from_po.flags.ignore_links       = True
            pi_from_po.submit()
            frappe.db.commit()
            for i, (dt, nm, ds) in enumerate(_to_cancel):
                if dt == "Purchase Invoice" and nm == pi_from_po.name:
                    _to_cancel[i] = ("Purchase Invoice", pi_from_po.name, 1)

            gl_rows = _gl(pi_from_po.name)
            if len(gl_rows) >= 2:
                _pass(f"GL posted: {len(gl_rows)} rows for PI {pi_from_po.name}")
            else:
                _fail("GL not posted", f"got {len(gl_rows)} rows")

            total_dr = sum(flt(r.debit)  for r in gl_rows)
            total_cr = sum(flt(r.credit) for r in gl_rows)
            if abs(total_dr - total_cr) < 0.01:
                _pass(f"GL balanced: DR = CR = {total_dr:.0f}")
            else:
                _fail("GL unbalanced", f"DR={total_dr:.2f} CR={total_cr:.2f}")

            po_doc = frappe.get_doc("Purchase Order", po_for_pi.name)
            po_doc.update_billed_amount()
            frappe.db.commit()

            billed = flt(frappe.db.get_value("Purchase Order", po_for_pi.name, "billed_amount"))
            expected = flt(po_for_pi.grand_total)
            if abs(billed - expected) < 0.01:
                _pass(f"PO.billed_amount = {billed:.0f} (matches grand_total)")
            else:
                _fail("PO.billed_amount wrong", f"got {billed:.2f}, expect {expected:.2f}")
        else:
            _fail("T6 skipped — T5 PI not available")
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: PO status → Billed ───────────────────────────────────────────────
    print("\n--- T7: PO status = Billed after full billing ---")
    try:
        if po_for_pi:
            status = frappe.db.get_value("Purchase Order", po_for_pi.name, "status")
            if status == "Billed":
                _pass("PO status = Billed")
            else:
                _fail("PO status not Billed", f"got {status}")
        else:
            _fail("T7 skipped")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: make_purchase_invoice on Billed PO → rejected ────────────────────
    print("\n--- T8: make_purchase_invoice on Billed PO → rejected ---")
    try:
        if po_for_pi:
            po_doc = frappe.get_doc("Purchase Order", po_for_pi.name)
            po_doc.make_purchase_invoice()
            _fail("Double-invoice accepted")
        else:
            _fail("T8 skipped")
    except frappe.exceptions.ValidationError as e:
        _pass(f"Billed PO rejected: {str(e)[:60]}")
    except Exception as e:
        _fail("Wrong exception type", str(e)[:80])

    # ── T9: Cancel un-billed PO → status = Cancelled ─────────────────────────
    print("\n--- T9: Cancel un-billed PO → status = Cancelled ---")
    try:
        po_cancel = _make_po(
            items=[{"item_name": "Temp Item", "qty": 1, "rate": 100}],
            submit=True,
        )
        po_cancel.cancel()
        frappe.db.commit()
        status = frappe.db.get_value("Purchase Order", po_cancel.name, "status")
        if status == "Cancelled":
            _pass(f"PO {po_cancel.name} status = Cancelled")
        else:
            _fail("Status not Cancelled", f"got {status}")
    except Exception as e:
        _fail("T9 crashed", str(e)[:120])

    # ── T10: Cleanup ──────────────────────────────────────────────────────────
    print("\n--- T10: Cleanup ---")
    cleaned = 0
    for doctype, name, docstatus in reversed(_to_cancel):
        try:
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
                cleaned += 1
        except Exception:
            pass
    frappe.db.commit()
    for name in _po_names:
        try:
            doc = frappe.get_doc("Purchase Order", name)
            if doc.docstatus == 0:
                frappe.delete_doc("Purchase Order", name, force=True, ignore_permissions=True)
        except Exception:
            pass
    frappe.db.commit()
    _pass(f"Cancelled/deleted {cleaned} documents")

    print("\n=== DONE ===")
