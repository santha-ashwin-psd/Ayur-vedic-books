"""
L1 — Sales Order, Purchase Order, Quotation → SO → SI chain test.

Scenario:
  ── Sales Order ──
  T1   Create SO with 2 items + tax → totals correct
  T2   Zero-qty item rejected
  T3   No-items rejected
  T4   Status lifecycle (Draft → Confirmed → Processing)
  T5   Create SI from SO manually (copy items, set ref), submit SI, verify GL

  ── Purchase Order ──
  T6   Create PO with 2 items + tax → totals correct
  T7   No-items rejected
  T8   Create PINV from PO manually, submit PINV, verify GL

  ── Quotation → SO → SI chain ──
  T9   Create Quotation → status Sent
  T10  Create SO with ref_quote → items/totals match Quotation
  T11  Create SI from SO → submit → 2 GL rows, DR = CR
  T12  Cleanup all test documents
"""
import frappe
from frappe import _
from frappe.utils import flt, today, add_days

COMPANY = "Eiffele gaming"
DATE    = today()


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _make_doc(data):
    doc = frappe.get_doc(data)
    doc.flags.ignore_permissions = True
    doc.insert()
    frappe.db.commit()
    return doc


def _gl_count(voucher_no, cancelled=0):
    return frappe.db.count("General Ledger Entry",
                           {"voucher_no": voucher_no, "is_cancelled": cancelled})


def _gl_balance(voucher_no, cancelled=0):
    rows = frappe.db.get_all("General Ledger Entry",
                             filters={"voucher_no": voucher_no, "is_cancelled": cancelled},
                             fields=["debit", "credit"])
    return sum(flt(r.debit) for r in rows), sum(flt(r.credit) for r in rows)


def run():
    print("\n=== Sales Order / Purchase Order / Quotation L1 Test ===")

    customer = frappe.db.get_value("Customer", {}, "name")
    supplier = frappe.db.get_value("Supplier", {}, "name")
    ar_acct  = frappe.db.get_value("Account", {"account_type": "Receivable", "company": COMPANY, "is_group": 0}, "name")
    inc_acct = frappe.db.get_value("Account", {"account_type": "Income",     "company": COMPANY, "is_group": 0}, "name")
    exp_acct = frappe.db.get_value("Account", {"account_type": "Expense",    "company": COMPANY, "is_group": 0}, "name")
    pay_acct = frappe.db.get_value("Account", {"account_type": "Payable",    "company": COMPANY, "is_group": 0}, "name")

    print(f"  customer={customer}  supplier={supplier}")
    if not all([customer, supplier, ar_acct, inc_acct, exp_acct, pay_acct]):
        print("  ABORT: required master data missing")
        return

    # Track docs for cleanup
    created = []

    # ════════════════════════ SALES ORDER ════════════════════════════════════════

    print("\n────── Sales Order ──────")

    # ── T1: Totals ────────────────────────────────────────────────────────────────
    print("\n--- T1: SO with 2 items + 9% tax → totals ---")
    so1 = None
    try:
        so1 = _make_doc({
            "doctype":          "Sales Order",
            "customer":         customer,
            "transaction_date": DATE,
            "company":          COMPANY,
            "items": [
                {"item_name": "Widget A", "qty": 5, "rate": 1000},
                {"item_name": "Widget B", "qty": 2, "rate": 500},
            ],
            "taxes": [{"description": "GST 9%", "rate": 9}],
        })
        created.append(("Sales Order", so1.name))

        expected_net   = round(5 * 1000 + 2 * 500, 2)          # 6000
        expected_tax   = round(expected_net * 9 / 100, 2)       # 540
        expected_grand = round(expected_net + expected_tax, 2)  # 6540

        if abs(flt(so1.net_total) - expected_net) < 0.01:
            _pass(f"net_total = {so1.net_total:.2f}")
        else:
            _fail("net_total wrong", f"got {so1.net_total:.2f}, expect {expected_net:.2f}")

        if abs(flt(so1.total_tax) - expected_tax) < 0.01:
            _pass(f"total_tax = {so1.total_tax:.2f}")
        else:
            _fail("total_tax wrong", f"got {so1.total_tax:.2f}, expect {expected_tax:.2f}")

        if abs(flt(so1.grand_total) - expected_grand) < 0.01:
            _pass(f"grand_total = {so1.grand_total:.2f}")
        else:
            _fail("grand_total wrong", f"got {so1.grand_total:.2f}, expect {expected_grand:.2f}")

        if so1.status == "Draft":
            _pass("Initial status = Draft")
        else:
            _fail("Initial status wrong", so1.status)

    except Exception as e:
        _fail("T1 crashed", str(e)[:100])

    # ── T2: Zero-qty rejected ─────────────────────────────────────────────────────
    print("\n--- T2: Zero-qty item rejected ---")
    try:
        _make_doc({
            "doctype": "Sales Order", "customer": customer,
            "transaction_date": DATE, "company": COMPANY,
            "items": [{"item_name": "Bad Item", "qty": 0, "rate": 100}],
        })
        _fail("Zero-qty accepted (should throw)")
    except Exception as e:
        if "qty" in str(e).lower() or "0" in str(e):
            _pass(f"Zero-qty rejected: {str(e)[:60]}")
        else:
            _fail("Wrong error for zero qty", str(e)[:60])

    # ── T3: No items rejected ─────────────────────────────────────────────────────
    print("\n--- T3: No items rejected ---")
    try:
        _make_doc({
            "doctype": "Sales Order", "customer": customer,
            "transaction_date": DATE, "company": COMPANY,
            "items": [],
        })
        _fail("Empty items accepted (should throw)")
    except Exception as e:
        if "item" in str(e).lower():
            _pass(f"No items rejected: {str(e)[:60]}")
        else:
            _fail("Wrong error for no items", str(e)[:60])

    # ── T4: Status lifecycle ──────────────────────────────────────────────────────
    print("\n--- T4: Status lifecycle Draft → Confirmed → Processing ---")
    if so1:
        try:
            frappe.db.set_value("Sales Order", so1.name, "status", "Confirmed")
            s1 = frappe.db.get_value("Sales Order", so1.name, "status")
            if s1 == "Confirmed":
                _pass("Status set to Confirmed")
            else:
                _fail("Status not Confirmed", s1)

            frappe.db.set_value("Sales Order", so1.name, "status", "Processing")
            s2 = frappe.db.get_value("Sales Order", so1.name, "status")
            if s2 == "Processing":
                _pass("Status set to Processing")
            else:
                _fail("Status not Processing", s2)
        except Exception as e:
            _fail("T4 crashed", str(e)[:80])
    else:
        _fail("T4 skipped — no SO")

    # ── T5: Create SI from SO, submit, verify GL ──────────────────────────────────
    print("\n--- T5: Create SI from SO → submit → GL ---")
    if so1:
        try:
            si = _make_doc({
                "doctype":        "Sales Invoice",
                "customer":       customer,
                "posting_date":   DATE,
                "due_date":       add_days(DATE, 30),
                "company":        COMPANY,
                "debit_to":       ar_acct,
                "income_account": inc_acct,
                "items": [
                    {"item_name": r.item_name, "qty": flt(r.qty), "rate": flt(r.rate)}
                    for r in so1.items
                ],
            })
            created.append(("Sales Invoice", si.name))
            si.submit()
            frappe.db.commit()

            n_gl = _gl_count(si.name)
            dr, cr = _gl_balance(si.name)
            if n_gl >= 2:
                _pass(f"SI {si.name} posted {n_gl} GL rows")
            else:
                _fail("GL rows missing", f"{n_gl}")
            if abs(dr - cr) < 0.01:
                _pass(f"GL balanced (DR=CR={dr:.2f})")
            else:
                _fail("GL not balanced", f"DR={dr:.2f} CR={cr:.2f}")
            if abs(dr - flt(si.grand_total)) < 0.01:
                _pass(f"GL total = grand_total ({dr:.2f})")
            else:
                _fail("GL total ≠ grand_total", f"GL={dr:.2f} SI={si.grand_total:.2f}")
        except Exception as e:
            _fail("T5 crashed", str(e)[:100])
    else:
        _fail("T5 skipped — no SO")

    # ════════════════════════ PURCHASE ORDER ══════════════════════════════════════

    print("\n────── Purchase Order ──────")

    # ── T6: Totals ────────────────────────────────────────────────────────────────
    print("\n--- T6: PO with 2 items + 18% tax → totals ---")
    po1 = None
    try:
        po1 = _make_doc({
            "doctype":          "Purchase Order",
            "supplier":         supplier,
            "transaction_date": DATE,
            "company":          COMPANY,
            "items": [
                {"item_name": "Raw Material X", "qty": 10, "rate": 800},
                {"item_name": "Raw Material Y", "qty": 3,  "rate": 200},
            ],
            "taxes": [{"description": "GST 18%", "rate": 18}],
        })
        created.append(("Purchase Order", po1.name))

        expected_net   = round(10 * 800 + 3 * 200, 2)           # 8600
        expected_tax   = round(expected_net * 18 / 100, 2)      # 1548
        expected_grand = round(expected_net + expected_tax, 2)  # 10148

        if abs(flt(po1.net_total) - expected_net) < 0.01:
            _pass(f"net_total = {po1.net_total:.2f}")
        else:
            _fail("net_total wrong", f"got {po1.net_total:.2f}")

        if abs(flt(po1.grand_total) - expected_grand) < 0.01:
            _pass(f"grand_total = {po1.grand_total:.2f}")
        else:
            _fail("grand_total wrong", f"got {po1.grand_total:.2f}")

    except Exception as e:
        _fail("T6 crashed", str(e)[:100])

    # ── T7: No items rejected ─────────────────────────────────────────────────────
    print("\n--- T7: PO no items rejected ---")
    try:
        _make_doc({
            "doctype": "Purchase Order", "supplier": supplier,
            "transaction_date": DATE, "company": COMPANY,
            "items": [],
        })
        _fail("Empty items accepted")
    except Exception as e:
        if "item" in str(e).lower():
            _pass(f"No items rejected: {str(e)[:60]}")
        else:
            _fail("Wrong error", str(e)[:60])

    # ── T8: Create PINV from PO, submit, verify GL ────────────────────────────────
    print("\n--- T8: Create PINV from PO → submit → GL ---")
    if po1:
        try:
            pinv = _make_doc({
                "doctype":         "Purchase Invoice",
                "supplier":        supplier,
                "posting_date":    DATE,
                "company":         COMPANY,
                "credit_to":       pay_acct,
                "expense_account": exp_acct,
                "items": [
                    {"item_name": r.item_name, "qty": flt(r.qty), "rate": flt(r.rate)}
                    for r in po1.items
                ],
            })
            created.append(("Purchase Invoice", pinv.name))
            pinv.submit()
            frappe.db.commit()

            n_gl = _gl_count(pinv.name)
            dr, cr = _gl_balance(pinv.name)
            if n_gl >= 2:
                _pass(f"PINV {pinv.name} posted {n_gl} GL rows")
            else:
                _fail("GL rows missing", f"{n_gl}")
            if abs(dr - cr) < 0.01:
                _pass(f"GL balanced (DR=CR={dr:.2f})")
            else:
                _fail("GL not balanced", f"DR={dr:.2f} CR={cr:.2f}")
        except Exception as e:
            _fail("T8 crashed", str(e)[:100])
    else:
        _fail("T8 skipped — no PO")

    # ════════════════════════ QUOTATION → SO → SI CHAIN ══════════════════════════

    print("\n────── Quotation → SO → SI chain ──────")

    # ── T9: Create Quotation ──────────────────────────────────────────────────────
    print("\n--- T9: Create Quotation → status Sent ---")
    qt = None
    try:
        qt = _make_doc({
            "doctype":          "Quotation",
            "customer":         customer,
            "transaction_date": DATE,
            "valid_till":       add_days(DATE, 30),
            "company":          COMPANY,
            "items": [
                {"item_name": "Service A", "qty": 1, "rate": 15000},
                {"item_name": "Service B", "qty": 2, "rate": 3000},
            ],
        })
        created.append(("Quotation", qt.name))

        expected_net = round(1 * 15000 + 2 * 3000, 2)  # 21000
        if abs(flt(qt.net_total) - expected_net) < 0.01:
            _pass(f"Quotation {qt.name}: net_total = {qt.net_total:.2f}")
        else:
            _fail("Quotation net_total wrong", f"{qt.net_total:.2f}")

        frappe.db.set_value("Quotation", qt.name, "status", "Sent")
        status = frappe.db.get_value("Quotation", qt.name, "status")
        if status == "Sent":
            _pass("Quotation status = Sent")
        else:
            _fail("Status not Sent", status)

    except Exception as e:
        _fail("T9 crashed", str(e)[:100])

    # ── T10: Create SO from Quotation ─────────────────────────────────────────────
    print("\n--- T10: Create SO referencing Quotation ---")
    so2 = None
    if qt:
        try:
            so2 = _make_doc({
                "doctype":          "Sales Order",
                "customer":         customer,
                "transaction_date": DATE,
                "company":          COMPANY,
                "ref_quote":        qt.name,
                "items": [
                    {"item_name": r.item_name, "qty": flt(r.qty), "rate": flt(r.rate)}
                    for r in qt.items
                ],
            })
            created.append(("Sales Order", so2.name))

            if flt(so2.net_total) == flt(qt.net_total):
                _pass(f"SO {so2.name}: net_total matches Quotation ({so2.net_total:.2f})")
            else:
                _fail("SO net_total mismatch", f"SO={so2.net_total:.2f} QT={qt.net_total:.2f}")

            if so2.ref_quote == qt.name:
                _pass(f"SO.ref_quote = {qt.name}")
            else:
                _fail("ref_quote not set", so2.ref_quote)

        except Exception as e:
            _fail("T10 crashed", str(e)[:100])
    else:
        _fail("T10 skipped — no Quotation")

    # ── T11: Create SI from SO, submit ────────────────────────────────────────────
    print("\n--- T11: Create SI from SO → submit → GL balanced ---")
    if so2:
        try:
            si2 = _make_doc({
                "doctype":        "Sales Invoice",
                "customer":       customer,
                "posting_date":   DATE,
                "due_date":       add_days(DATE, 30),
                "company":        COMPANY,
                "debit_to":       ar_acct,
                "income_account": inc_acct,
                "items": [
                    {"item_name": r.item_name, "qty": flt(r.qty), "rate": flt(r.rate)}
                    for r in so2.items
                ],
            })
            created.append(("Sales Invoice", si2.name))
            si2.submit()
            frappe.db.commit()

            n_gl = _gl_count(si2.name)
            dr, cr = _gl_balance(si2.name)
            if n_gl >= 2:
                _pass(f"SI {si2.name}: {n_gl} GL rows")
            else:
                _fail("GL rows missing", f"{n_gl}")
            if abs(dr - cr) < 0.01 and abs(dr - flt(si2.grand_total)) < 0.01:
                _pass(f"GL balanced, DR=CR={dr:.2f} = grand_total")
            else:
                _fail("GL wrong", f"DR={dr:.2f} CR={cr:.2f} GT={si2.grand_total:.2f}")

            # Verify chain: QT net → SO net → SI net all match
            if abs(flt(si2.net_total) - flt(qt.net_total)) < 0.01:
                _pass(f"Full chain: QT→SO→SI net_total = {qt.net_total:.2f}")
            else:
                _fail("Chain net_total mismatch", f"SI={si2.net_total:.2f} QT={qt.net_total:.2f}")

        except Exception as e:
            _fail("T11 crashed", str(e)[:100])
    else:
        _fail("T11 skipped — no SO from chain")

    # ── T12: Cleanup ──────────────────────────────────────────────────────────────
    print("\n--- T12: Cleanup ---")
    cancelled = 0
    deleted   = 0
    # Cancel submittable docs first (Sales Invoice, Purchase Invoice)
    for doctype, name in reversed(created):
        try:
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
                frappe.db.commit()
                cancelled += 1
        except Exception:
            pass
    # Delete non-submittable docs and cancelled submittables
    for doctype, name in reversed(created):
        try:
            frappe.delete_doc(doctype, name, force=True, ignore_permissions=True)
            frappe.db.commit()
            deleted += 1
        except Exception:
            pass
    _pass(f"Cancelled {cancelled}, deleted {deleted} test documents")

    print("\n=== DONE ===")
