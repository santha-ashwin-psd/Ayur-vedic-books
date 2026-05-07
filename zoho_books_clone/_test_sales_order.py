"""
L1 — Sales Order test.

Scenario:
  T1  Create draft SO with 2 items → net_total, total_tax, grand_total correct
  T2  SO with zero-qty item → ValidationError
  T3  SO with no items → ValidationError
  T4  Submit SO → status = Confirmed
  T5  make_sales_invoice() → SI created with matching totals, sales_order field set
  T6  Submit SI → GL posted (DR AR, CR Income); SO billed_amount updated
  T7  SO status → Invoiced after full billing
  T8  Attempt make_sales_invoice on already-Invoiced SO → rejected
  T9  Cancel SO that has not been invoiced → status = Cancelled
  T10 Cleanup
"""
import frappe
from frappe.utils import flt, today
import importlib

COMPANY  = "Eiffele gaming"
CUSTOMER = "CUST-2026-00009"

_to_cancel  = []   # (doctype, name, docstatus)
_so_names   = []


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _make_so(items, taxes=None, submit=False):
    so = frappe.new_doc("Sales Order")
    so.customer          = CUSTOMER
    so.company           = COMPANY
    so.transaction_date  = today()
    for it in items:
        so.append("items", it)
    for tx in (taxes or []):
        so.append("taxes", tx)
    so.flags.ignore_permissions = True
    so.flags.ignore_mandatory   = True
    so.flags.ignore_links       = True
    so.insert(ignore_links=True)
    _so_names.append(so.name)
    if submit:
        so.submit()
    frappe.db.commit()
    return so


def _gl(voucher_no, cancelled=0):
    return frappe.db.get_all(
        "General Ledger Entry",
        filters={"voucher_no": voucher_no, "is_cancelled": cancelled},
        fields=["account", "debit", "credit"],
    )


def run():
    print("\n=== Sales Order L1 Test ===")

    # Reload controller so any edits in this session take effect
    import zoho_books_clone.invoicing.doctype.sales_order.sales_order as so_mod
    importlib.reload(so_mod)

    ar_acct  = frappe.db.get_value("Account", {"account_type": "Receivable", "company": COMPANY, "is_group": 0}, "name")
    inc_acct = frappe.db.get_value("Account", {"account_type": "Income",     "company": COMPANY, "is_group": 0, "account_name": ["like", "%Revenue%"]}, "name") \
               or frappe.db.get_value("Account", {"account_type": "Income", "company": COMPANY, "is_group": 0}, "name")

    cgst_acct = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY, "is_group": 0,
                                                  "account_name": ["like", "%CGST%Payable%"]}, "name")
    sgst_acct = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY, "is_group": 0,
                                                  "account_name": ["like", "%SGST%Payable%"]}, "name")

    print(f"  AR={ar_acct}  Inc={inc_acct}  CGST={cgst_acct}  SGST={sgst_acct}")

    # ── T1: Draft SO — totals calculated correctly ────────────────────────────
    print("\n--- T1: Draft SO — totals ---")
    try:
        so1 = _make_so(
            items=[
                {"item_name": "Widget A", "qty": 5, "rate": 1000},
                {"item_name": "Widget B", "qty": 2, "rate": 2500},
            ],
            taxes=[
                {"description": "CGST 9%", "rate": 9,  "tax_amount": 0, "account_head": cgst_acct},
                {"description": "SGST 9%", "rate": 9,  "tax_amount": 0, "account_head": sgst_acct},
            ] if cgst_acct and sgst_acct else [],
        )
        # net = 5*1000 + 2*2500 = 10000
        # tax = 18% of 10000 = 1800 (if tax accounts found)
        expected_net = 10000.0
        if abs(flt(so1.net_total) - expected_net) < 0.01:
            _pass(f"net_total = {so1.net_total:.0f} (expect 10000)")
        else:
            _fail("net_total wrong", f"got {so1.net_total}")

        if cgst_acct and sgst_acct:
            expected_tax = 1800.0
            if abs(flt(so1.total_tax) - expected_tax) < 0.01:
                _pass(f"total_tax = {so1.total_tax:.0f} (expect 1800)")
            else:
                _fail("total_tax wrong", f"got {so1.total_tax}")
            expected_grand = 11800.0
        else:
            expected_grand = 10000.0

        if abs(flt(so1.grand_total) - expected_grand) < 0.01:
            _pass(f"grand_total = {so1.grand_total:.0f} (expect {expected_grand:.0f})")
        else:
            _fail("grand_total wrong", f"got {so1.grand_total}")

        item_amts = [flt(i.amount) for i in so1.items]
        if item_amts == [5000.0, 5000.0]:
            _pass("Item amounts calculated: [5000, 5000]")
        else:
            _fail("Item amounts wrong", str(item_amts))

    except Exception as e:
        _fail("T1 crashed", str(e)[:120])
        so1 = None

    # ── T2: Zero-qty item → rejected ─────────────────────────────────────────
    print("\n--- T2: Zero qty item → ValidationError ---")
    try:
        _make_so(items=[{"item_name": "Bad Item", "qty": 0, "rate": 100}])
        _fail("Zero qty accepted (should have thrown)")
    except frappe.exceptions.ValidationError:
        _pass("ValidationError raised for zero-qty item")
    except Exception as e:
        _fail("Wrong exception type", str(e)[:80])

    # ── T3: No items → rejected ───────────────────────────────────────────────
    print("\n--- T3: No items → ValidationError ---")
    try:
        so_empty = frappe.new_doc("Sales Order")
        so_empty.customer = CUSTOMER
        so_empty.company  = COMPANY
        so_empty.flags.ignore_permissions = True
        so_empty.flags.ignore_mandatory   = True
        so_empty.insert()
        _fail("Empty SO accepted (should have thrown)")
    except frappe.exceptions.ValidationError:
        _pass("ValidationError raised for no items")
    except Exception as e:
        _fail("Wrong exception type", str(e)[:80])

    # ── T4: Submit SO → status Confirmed ─────────────────────────────────────
    print("\n--- T4: Submit SO → status = Confirmed ---")
    try:
        so_sub = _make_so(
            items=[{"item_name": "Service A", "qty": 1, "rate": 5000}],
            submit=True,
        )
        _to_cancel.append(("Sales Order", so_sub.name, 1))
        status = frappe.db.get_value("Sales Order", so_sub.name, "status")
        if status == "Confirmed":
            _pass(f"SO {so_sub.name} status = Confirmed")
        else:
            _fail("Status not Confirmed", f"got {status}")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])
        so_sub = None

    # ── T5: make_sales_invoice() → SI created with matching totals ────────────
    print("\n--- T5: make_sales_invoice() → SI totals match SO ---")
    si_from_so = None
    so_for_si  = None
    try:
        so_for_si = _make_so(
            items=[{"item_name": "Consulting", "qty": 3, "rate": 4000}],
            submit=True,
        )
        _to_cancel.append(("Sales Order", so_for_si.name, 1))

        si_from_so = so_for_si.make_sales_invoice()
        frappe.db.commit()
        _to_cancel.append(("Sales Invoice", si_from_so.name, 0))

        # Totals match
        if abs(flt(si_from_so.net_total) - flt(so_for_si.net_total)) < 0.01:
            _pass(f"SI net_total = {si_from_so.net_total:.0f} matches SO")
        else:
            _fail("SI net_total mismatch",
                  f"SI={si_from_so.net_total} SO={so_for_si.net_total}")

        if abs(flt(si_from_so.grand_total) - flt(so_for_si.grand_total)) < 0.01:
            _pass(f"SI grand_total = {si_from_so.grand_total:.0f} matches SO")
        else:
            _fail("SI grand_total mismatch",
                  f"SI={si_from_so.grand_total} SO={so_for_si.grand_total}")

        # sales_order field linked back
        if si_from_so.sales_order == so_for_si.name:
            _pass(f"SI.sales_order = '{so_for_si.name}'")
        else:
            _fail("SI.sales_order not linked", f"got '{si_from_so.sales_order}'")

        # Items copied
        if len(si_from_so.items) == len(so_for_si.items):
            _pass(f"{len(si_from_so.items)} items copied to SI")
        else:
            _fail("Item count mismatch",
                  f"SI={len(si_from_so.items)} SO={len(so_for_si.items)}")

    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: Submit SI → GL posted; SO billed_amount updated ──────────────────
    print("\n--- T6: Submit SI → GL posted + SO.billed_amount updated ---")
    try:
        if si_from_so and so_for_si:
            si_from_so.flags.ignore_permissions = True
            si_from_so.flags.ignore_mandatory   = True
            si_from_so.flags.ignore_links       = True
            si_from_so.submit()
            frappe.db.commit()
            # Update cancel list (now submitted)
            for i, (dt, nm, ds) in enumerate(_to_cancel):
                if dt == "Sales Invoice" and nm == si_from_so.name:
                    _to_cancel[i] = ("Sales Invoice", si_from_so.name, 1)

            gl_rows = _gl(si_from_so.name)
            if len(gl_rows) >= 2:
                _pass(f"GL posted: {len(gl_rows)} rows for SI {si_from_so.name}")
            else:
                _fail("GL not posted", f"got {len(gl_rows)} rows")

            total_dr = sum(flt(r.debit)  for r in gl_rows)
            total_cr = sum(flt(r.credit) for r in gl_rows)
            if abs(total_dr - total_cr) < 0.01:
                _pass(f"GL balanced: DR = CR = {total_dr:.0f}")
            else:
                _fail("GL unbalanced", f"DR={total_dr:.2f} CR={total_cr:.2f}")

            # Trigger billed_amount update
            so_doc = frappe.get_doc("Sales Order", so_for_si.name)
            so_doc.update_billed_amount()
            frappe.db.commit()

            billed = flt(frappe.db.get_value("Sales Order", so_for_si.name, "billed_amount"))
            expected_billed = flt(so_for_si.grand_total)
            if abs(billed - expected_billed) < 0.01:
                _pass(f"SO.billed_amount = {billed:.0f} (matches grand_total)")
            else:
                _fail("SO.billed_amount wrong", f"got {billed:.2f}, expect {expected_billed:.2f}")
        else:
            _fail("T6 skipped — T5 SI not available")
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: SO status → Invoiced after full billing ───────────────────────────
    print("\n--- T7: SO status = Invoiced after full billing ---")
    try:
        if so_for_si:
            status = frappe.db.get_value("Sales Order", so_for_si.name, "status")
            if status == "Invoiced":
                _pass(f"SO status = Invoiced")
            else:
                _fail("SO status not Invoiced", f"got {status}")
        else:
            _fail("T7 skipped — SO not available")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: make_sales_invoice on Invoiced SO → rejected ─────────────────────
    print("\n--- T8: make_sales_invoice on Invoiced SO → rejected ---")
    try:
        if so_for_si:
            so_doc = frappe.get_doc("Sales Order", so_for_si.name)
            so_doc.make_sales_invoice()
            _fail("Double-invoice accepted (should have thrown)")
        else:
            _fail("T8 skipped — SO not available")
    except frappe.exceptions.ValidationError as e:
        _pass(f"Invoiced SO rejected: {str(e)[:60]}")
    except Exception as e:
        _fail("Wrong exception type", str(e)[:80])

    # ── T9: Cancel un-invoiced submitted SO → status = Cancelled ─────────────
    print("\n--- T9: Cancel un-invoiced SO → status = Cancelled ---")
    try:
        so_to_cancel = _make_so(
            items=[{"item_name": "Temp Service", "qty": 1, "rate": 100}],
            submit=True,
        )
        so_to_cancel.cancel()
        frappe.db.commit()
        status = frappe.db.get_value("Sales Order", so_to_cancel.name, "status")
        if status == "Cancelled":
            _pass(f"SO {so_to_cancel.name} cancelled, status = Cancelled")
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

    # Cancel un-submitted draft SOs
    for name in _so_names:
        try:
            doc = frappe.get_doc("Sales Order", name)
            if doc.docstatus == 0:
                frappe.delete_doc("Sales Order", name, force=True, ignore_permissions=True)
        except Exception:
            pass
    frappe.db.commit()
    _pass(f"Cancelled/deleted {cleaned} documents")

    print("\n=== DONE ===")
