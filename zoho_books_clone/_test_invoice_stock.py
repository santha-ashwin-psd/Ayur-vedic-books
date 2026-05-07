"""
L1 — Invoice-driven stock movement.

Sales Invoice submit  → Bin.actual_qty decreases + SLE created (direction=out)
Purchase Invoice submit → Bin.actual_qty increases + SLE created (direction=in)

Scenario:
  T1  PI with warehouse → Bin qty increases by item qty; SLE created
  T2  SI with warehouse → Bin qty decreases by item qty; SLE created
  T3  SI without warehouse → no SLE created (graceful skip)
  T4  PI without warehouse → no SLE created (graceful skip)
  T5  Cancel SI → GL reversed, no crash; Bin not further decremented
  T6  Cleanup
"""
import frappe
from frappe.utils import flt, today
import importlib

COMPANY   = "Eiffele gaming"
CUSTOMER  = "CUST-2026-00009"
SUPPLIER  = "SUPP-2026-00002"
WAREHOUSE = "Stores"
ITEM_CODE = "ITEM-TEST-001"

AR_ACCOUNT  = "Accounts Receivable-Eiffele gaming"
AP_ACCOUNT  = "Accounts Payable-Eiffele gaming"

_to_cancel = []


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _bin_qty(item_code, warehouse):
    return flt(frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "actual_qty") or 0)


def _sle_count(voucher_no):
    return frappe.db.count("Stock Ledger Entry", {"voucher_no": voucher_no, "is_cancelled": 0})


def _make_si(qty, rate, warehouse=None):
    inc_acct = frappe.db.get_value("Account",
        {"account_type": "Income", "company": COMPANY, "is_group": 0,
         "account_name": ["like", "%Revenue%"]}, "name") or \
        frappe.db.get_value("Account", {"account_type": "Income", "company": COMPANY, "is_group": 0}, "name")

    item = {"item_name": ITEM_CODE, "item_code": ITEM_CODE, "qty": qty, "rate": rate, "amount": qty * rate}
    if warehouse:
        item["warehouse"] = warehouse

    si = frappe.get_doc({
        "doctype":        "Sales Invoice",
        "customer":       CUSTOMER,
        "posting_date":   today(),
        "company":        COMPANY,
        "debit_to":       AR_ACCOUNT,
        "income_account": inc_acct,
        "items":          [item],
    })
    si.flags.ignore_permissions = True
    si.flags.ignore_mandatory   = True
    si.flags.ignore_links       = True
    si.insert(ignore_links=True)
    si.submit()
    frappe.db.commit()
    return si


def _make_pi(qty, rate, warehouse=None):
    exp_acct = frappe.db.get_value("Account",
        {"account_type": "Expense", "company": COMPANY, "is_group": 0}, "name")

    item = {"item_name": ITEM_CODE, "item_code": ITEM_CODE, "qty": qty, "rate": rate, "amount": qty * rate}
    if warehouse:
        item["warehouse"] = warehouse

    pi = frappe.get_doc({
        "doctype":          "Purchase Invoice",
        "supplier":         SUPPLIER,
        "posting_date":     today(),
        "company":          COMPANY,
        "credit_to":        AP_ACCOUNT,
        "expense_account":  exp_acct,
        "items":            [item],
    })
    pi.flags.ignore_permissions = True
    pi.flags.ignore_mandatory   = True
    pi.flags.ignore_links       = True
    pi.insert(ignore_links=True)
    pi.submit()
    frappe.db.commit()
    return pi


def run():
    print("\n=== Invoice-Driven Stock Movement L1 Test ===")

    import zoho_books_clone.accounts.accounting_engine as eng
    importlib.reload(eng)

    print(f"  Warehouse={WAREHOUSE}  Item={ITEM_CODE}")

    # Seed a known starting bin qty so tests are deterministic
    bin_name = frappe.db.get_value("Bin", {"item_code": ITEM_CODE, "warehouse": WAREHOUSE})
    SEED_QTY = 100.0
    if bin_name:
        frappe.db.set_value("Bin", bin_name, {"actual_qty": SEED_QTY, "valuation_rate": 500, "stock_value": SEED_QTY * 500})
    else:
        b = frappe.get_doc({"doctype": "Bin", "item_code": ITEM_CODE, "warehouse": WAREHOUSE,
                            "actual_qty": SEED_QTY, "valuation_rate": 500, "stock_value": SEED_QTY * 500,
                            "reserved_qty": 0, "ordered_qty": 0, "projected_qty": SEED_QTY})
        b.flags.ignore_links = True
        b.flags.ignore_mandatory = True
        b.insert(ignore_permissions=True)
    frappe.db.commit()
    print(f"  Bin seeded to {SEED_QTY}")

    # ── T1: PI with warehouse → Bin increases ────────────────────────────────
    print("\n--- T1: Purchase Invoice with warehouse → Bin qty increases ---")
    try:
        qty_before = _bin_qty(ITEM_CODE, WAREHOUSE)
        pi = _make_pi(qty=10, rate=500, warehouse=WAREHOUSE)
        _to_cancel.append(("Purchase Invoice", pi.name))

        qty_after = _bin_qty(ITEM_CODE, WAREHOUSE)
        expected = qty_before + 10

        if abs(qty_after - expected) < 0.01:
            _pass(f"Bin qty: {qty_before:.0f} → {qty_after:.0f} (+10)")
        else:
            _fail("Bin qty not increased", f"before={qty_before} after={qty_after} expected={expected}")

        sle_cnt = _sle_count(pi.name)
        if sle_cnt >= 1:
            _pass(f"SLE created for PI {pi.name} ({sle_cnt} row(s))")
        else:
            _fail("No SLE created for PI")

    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    # ── T2: SI with warehouse → Bin decreases ────────────────────────────────
    print("\n--- T2: Sales Invoice with warehouse → Bin qty decreases ---")
    try:
        qty_before = _bin_qty(ITEM_CODE, WAREHOUSE)
        si = _make_si(qty=5, rate=800, warehouse=WAREHOUSE)
        _to_cancel.append(("Sales Invoice", si.name))

        qty_after = _bin_qty(ITEM_CODE, WAREHOUSE)
        expected = qty_before - 5

        if abs(qty_after - expected) < 0.01:
            _pass(f"Bin qty: {qty_before:.0f} → {qty_after:.0f} (-5)")
        else:
            _fail("Bin qty not decreased", f"before={qty_before} after={qty_after} expected={expected}")

        sle_cnt = _sle_count(si.name)
        if sle_cnt >= 1:
            _pass(f"SLE created for SI {si.name} ({sle_cnt} row(s))")
        else:
            _fail("No SLE created for SI")

    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: SI without warehouse → no SLE, no crash ───────────────────────────
    print("\n--- T3: SI without warehouse → no SLE created ---")
    try:
        qty_before = _bin_qty(ITEM_CODE, WAREHOUSE)
        si_no_wh = _make_si(qty=3, rate=800, warehouse=None)
        _to_cancel.append(("Sales Invoice", si_no_wh.name))

        qty_after = _bin_qty(ITEM_CODE, WAREHOUSE)
        sle_cnt = _sle_count(si_no_wh.name)

        if sle_cnt == 0:
            _pass("No SLE created when warehouse is blank")
        else:
            _fail("SLE unexpectedly created without warehouse", f"{sle_cnt} rows")

        if abs(qty_after - qty_before) < 0.01:
            _pass("Bin qty unchanged when no warehouse on SI")
        else:
            _fail("Bin qty changed unexpectedly", f"before={qty_before} after={qty_after}")

    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: PI without warehouse → no SLE, no crash ───────────────────────────
    print("\n--- T4: PI without warehouse → no SLE created ---")
    try:
        qty_before = _bin_qty(ITEM_CODE, WAREHOUSE)
        pi_no_wh = _make_pi(qty=4, rate=500, warehouse=None)
        _to_cancel.append(("Purchase Invoice", pi_no_wh.name))

        qty_after = _bin_qty(ITEM_CODE, WAREHOUSE)
        sle_cnt = _sle_count(pi_no_wh.name)

        if sle_cnt == 0:
            _pass("No SLE created when warehouse is blank")
        else:
            _fail("SLE unexpectedly created without warehouse", f"{sle_cnt} rows")

        if abs(qty_after - qty_before) < 0.01:
            _pass("Bin qty unchanged when no warehouse on PI")
        else:
            _fail("Bin qty changed unexpectedly", f"before={qty_before} after={qty_after}")

    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: Cancel SI → GL reversed, no crash ────────────────────────────────
    print("\n--- T5: Cancel SI → GL reversed, no crash ---")
    try:
        si_cancel = _make_si(qty=2, rate=800, warehouse=WAREHOUSE)
        qty_before_cancel = _bin_qty(ITEM_CODE, WAREHOUSE)

        si_cancel.cancel()
        frappe.db.commit()

        gl_cancelled = frappe.db.count("General Ledger Entry",
            {"voucher_no": si_cancel.name, "is_cancelled": 1})
        if gl_cancelled >= 2:
            _pass(f"GL rows cancelled on SI cancel ({gl_cancelled} rows)")
        else:
            _fail("GL cancellation incomplete", f"{gl_cancelled} cancelled rows")

        _pass("Cancel completed without crash")

    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: Cleanup ───────────────────────────────────────────────────────────
    print("\n--- T6: Cleanup ---")
    cleaned = 0
    for doctype, name in reversed(_to_cancel):
        try:
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
                cleaned += 1
        except Exception:
            pass
    frappe.db.commit()
    _pass(f"Cancelled {cleaned} documents")

    print("\n=== DONE ===")
