"""
L1 — Reorder Alerts test.

Tests check_reorder(), get_reorder_alerts(), and get_reorder_items()
using controlled Bin records.

  T1  check_reorder → False when Bin doesn't exist
  T2  check_reorder → False when reorder_level = 0 (no threshold set)
  T3  check_reorder → False when actual_qty >= reorder_level (at threshold)
  T4  check_reorder → False when actual_qty == reorder_level exactly
  T5  check_reorder → True when actual_qty < reorder_level
  T6  get_reorder_alerts includes item below threshold
  T7  get_reorder_alerts excludes item at/above threshold
  T8  get_reorder_alerts shortage_qty == reorder_level - actual_qty
  T9  get_reorder_alerts company filter — item not returned for wrong company
  T10 get_reorder_alerts ordering — largest shortage first
  T11 get_reorder_items API delegates to get_reorder_alerts correctly
  T12 Bin actual_qty update: alert disappears after stock receipt
  T13 Cleanup
"""
import frappe
from frappe.utils import flt, today

COMPANY = "Eiffele gaming"
WH      = "Stores"
ITEM_A  = "TEST-REORDER-A"
ITEM_B  = "TEST-REORDER-B"

_test_bins   = []   # (item_code, warehouse) to clean up
_test_items  = []
_test_sle    = []   # SLE names to cancel/delete
_test_se     = []   # Stock Entry names


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _ensure_item(item_code: str) -> None:
    if not frappe.db.exists("Item", item_code):
        doc = frappe.new_doc("Item")
        doc.item_code    = item_code
        doc.item_name    = item_code
        doc.item_group   = frappe.db.get_value("Item Group", {"is_group": 0}, "name") or "All Item Groups"
        doc.stock_uom    = "Nos"
        doc.is_stock_item = 1
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory   = True
        doc.insert(ignore_links=True)
        _test_items.append(item_code)
        frappe.db.commit()


def _set_bin(item_code: str, warehouse: str, actual_qty: float,
             reorder_level: float, reorder_qty: float = 0.0) -> None:
    """Upsert a Bin record with explicit qty and reorder thresholds."""
    existing = frappe.db.get_value("Bin", {"item_code": item_code, "warehouse": warehouse}, "name")
    if existing:
        frappe.db.set_value("Bin", existing, {
            "actual_qty":   actual_qty,
            "reorder_level": reorder_level,
            "reorder_qty":  reorder_qty,
            "company":      COMPANY,
        }, update_modified=False)
    else:
        doc = frappe.new_doc("Bin")
        doc.item_code    = item_code
        doc.warehouse    = warehouse
        doc.actual_qty   = actual_qty
        doc.reorder_level = reorder_level
        doc.reorder_qty  = reorder_qty
        doc.company      = COMPANY
        doc.stock_uom    = "Nos"
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory   = True
        doc.insert(ignore_links=True)
        _test_bins.append((item_code, warehouse))
    frappe.db.commit()


def run():
    print("\n=== Reorder Alerts L1 Test ===")

    import importlib
    import zoho_books_clone.inventory.utils as inv_mod
    import zoho_books_clone.api.inventory as api_mod
    importlib.reload(inv_mod)
    importlib.reload(api_mod)
    from zoho_books_clone.inventory.utils import check_reorder, get_reorder_alerts
    from zoho_books_clone.api.inventory import get_reorder_items

    # Create test items
    _ensure_item(ITEM_A)
    _ensure_item(ITEM_B)

    # ── T1: check_reorder → False when Bin doesn't exist ─────────────────────
    print("\n--- T1: check_reorder → False when no Bin record exists ---")
    try:
        # Ensure no Bin exists for this item+warehouse combo
        frappe.db.delete("Bin", {"item_code": "TEST-REORDER-NONEXISTENT", "warehouse": WH})
        result = check_reorder("TEST-REORDER-NONEXISTENT", WH)
        if result is False:
            _pass("Returns False when Bin doesn't exist")
        else:
            _fail("Expected False, got True for non-existent Bin")
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    # ── T2: check_reorder → False when reorder_level = 0 ─────────────────────
    print("\n--- T2: check_reorder → False when reorder_level = 0 ---")
    try:
        _set_bin(ITEM_A, WH, actual_qty=5.0, reorder_level=0.0)
        result = check_reorder(ITEM_A, WH)
        if result is False:
            _pass("Returns False when reorder_level = 0 (no threshold set)")
        else:
            _fail("Expected False when reorder_level=0, got True")
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: check_reorder → False when actual_qty > reorder_level ────────────
    print("\n--- T3: check_reorder → False when actual_qty > reorder_level ---")
    try:
        _set_bin(ITEM_A, WH, actual_qty=50.0, reorder_level=20.0)
        result = check_reorder(ITEM_A, WH)
        if result is False:
            _pass("Returns False when actual_qty (50) > reorder_level (20)")
        else:
            _fail("Expected False when above reorder level, got True")
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: check_reorder → False when actual_qty == reorder_level ───────────
    print("\n--- T4: check_reorder → False when actual_qty == reorder_level ---")
    try:
        _set_bin(ITEM_A, WH, actual_qty=20.0, reorder_level=20.0)
        result = check_reorder(ITEM_A, WH)
        if result is False:
            _pass("Returns False when actual_qty (20) == reorder_level (20) — not strictly below")
        else:
            _fail("Expected False when at reorder level, got True")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: check_reorder → True when actual_qty < reorder_level ─────────────
    print("\n--- T5: check_reorder → True when actual_qty < reorder_level ---")
    try:
        _set_bin(ITEM_A, WH, actual_qty=5.0, reorder_level=20.0, reorder_qty=50.0)
        result = check_reorder(ITEM_A, WH)
        if result is True:
            _pass("Returns True when actual_qty (5) < reorder_level (20)")
        else:
            _fail("Expected True when below reorder level, got False")
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: get_reorder_alerts includes item below threshold ──────────────────
    print("\n--- T6: get_reorder_alerts includes item when below threshold ---")
    try:
        _set_bin(ITEM_A, WH, actual_qty=5.0, reorder_level=20.0, reorder_qty=50.0)
        alerts = get_reorder_alerts(company=COMPANY)
        alert_items = [a.item_code for a in alerts]
        if ITEM_A in alert_items:
            _pass(f"ITEM_A ({ITEM_A}) appears in reorder alerts")
        else:
            _fail(f"ITEM_A not in alerts", f"alerts={alert_items}")
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: get_reorder_alerts excludes item at/above threshold ───────────────
    print("\n--- T7: get_reorder_alerts excludes item at/above threshold ---")
    try:
        _set_bin(ITEM_A, WH, actual_qty=25.0, reorder_level=20.0)  # above threshold
        alerts = get_reorder_alerts(company=COMPANY)
        alert_items = [a.item_code for a in alerts]
        if ITEM_A not in alert_items:
            _pass(f"ITEM_A excluded when actual_qty (25) >= reorder_level (20)")
        else:
            _fail(f"ITEM_A in alerts despite being above threshold")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: shortage_qty == reorder_level - actual_qty ────────────────────────
    print("\n--- T8: shortage_qty == reorder_level - actual_qty ---")
    try:
        _set_bin(ITEM_A, WH, actual_qty=3.0, reorder_level=30.0, reorder_qty=100.0)
        alerts = get_reorder_alerts(company=COMPANY)
        item_alert = next((a for a in alerts if a.item_code == ITEM_A), None)
        if not item_alert:
            _fail("ITEM_A not in alerts", "setup error")
        else:
            expected_shortage = 30.0 - 3.0  # = 27
            actual_shortage   = flt(item_alert.get("shortage_qty"))
            if abs(actual_shortage - expected_shortage) < 0.01:
                _pass(f"shortage_qty = {actual_shortage:.1f} = reorder_level(30) - actual_qty(3)")
            else:
                _fail("shortage_qty wrong",
                      f"expected={expected_shortage:.1f}, got={actual_shortage:.1f}")
    except Exception as e:
        _fail("T8 crashed", str(e)[:120])

    # ── T9: company filter — item from different company not returned ──────────
    print("\n--- T9: company filter excludes items from other companies ---")
    try:
        # Set up ITEM_B on a different company
        _set_bin(ITEM_B, WH, actual_qty=1.0, reorder_level=100.0)
        frappe.db.set_value("Bin",
                            {"item_code": ITEM_B, "warehouse": WH},
                            "company", "NONEXISTENT_CO",
                            update_modified=False)
        frappe.db.commit()

        alerts = get_reorder_alerts(company=COMPANY)
        alert_items = [a.item_code for a in alerts]
        if ITEM_B not in alert_items:
            _pass("ITEM_B (different company) excluded from COMPANY alerts")
        else:
            _fail("ITEM_B from different company wrongly included in alerts")

        # Restore ITEM_B to correct company for cleanup
        frappe.db.set_value("Bin",
                            {"item_code": ITEM_B, "warehouse": WH},
                            "company", COMPANY,
                            update_modified=False)
        frappe.db.commit()
    except Exception as e:
        _fail("T9 crashed", str(e)[:120])

    # ── T10: ordering — largest shortage first ────────────────────────────────
    print("\n--- T10: get_reorder_alerts ordered by shortage_qty DESC ---")
    try:
        # ITEM_A: shortage = 30 - 3 = 27 (large)
        _set_bin(ITEM_A, WH, actual_qty=3.0, reorder_level=30.0)
        # ITEM_B: shortage = 10 - 2 = 8 (smaller)
        _set_bin(ITEM_B, WH, actual_qty=2.0, reorder_level=10.0)
        frappe.db.commit()

        alerts = get_reorder_alerts(company=COMPANY)
        our_alerts = [a for a in alerts if a.item_code in (ITEM_A, ITEM_B)]

        if len(our_alerts) < 2:
            _fail("Both items expected in alerts", f"got {len(our_alerts)}")
        else:
            shortages = [flt(a.shortage_qty) for a in our_alerts]
            if shortages == sorted(shortages, reverse=True):
                _pass(f"Alerts ordered by shortage DESC: {shortages}")
            else:
                _fail("Alerts not ordered by shortage DESC", str(shortages))
    except Exception as e:
        _fail("T10 crashed", str(e)[:120])

    # ── T11: get_reorder_items API endpoint ───────────────────────────────────
    print("\n--- T11: get_reorder_items returns same data as get_reorder_alerts ---")
    try:
        alerts   = get_reorder_alerts(company=COMPANY)
        api_items = get_reorder_items(company=COMPANY)

        alerts_set   = {a.item_code for a in alerts}
        api_items_set = {a.get("item_code") for a in api_items}

        if alerts_set == api_items_set:
            _pass(f"get_reorder_items == get_reorder_alerts ({len(alerts)} items)")
        else:
            _fail("get_reorder_items differs from get_reorder_alerts",
                  f"alerts={alerts_set}, api={api_items_set}")
    except Exception as e:
        _fail("T11 crashed", str(e)[:120])

    # ── T12: alert clears after restocking above threshold ────────────────────
    print("\n--- T12: alert disappears after actual_qty brought above threshold ---")
    try:
        _set_bin(ITEM_A, WH, actual_qty=3.0, reorder_level=20.0)
        before = check_reorder(ITEM_A, WH)

        _set_bin(ITEM_A, WH, actual_qty=50.0, reorder_level=20.0)  # restock
        after  = check_reorder(ITEM_A, WH)

        if before is True and after is False:
            _pass("Alert fires at qty=3 below threshold=20, clears after restock to qty=50")
        else:
            _fail("Alert state transition wrong",
                  f"before={before}, after={after}")
    except Exception as e:
        _fail("T12 crashed", str(e)[:120])

    # ── T13: Cleanup ──────────────────────────────────────────────────────────
    print("\n--- T13: Cleanup ---")
    try:
        deleted_bins = 0
        for item_code in (ITEM_A, ITEM_B):
            rows = frappe.db.sql(
                "SELECT name FROM `tabBin` WHERE item_code = %s", item_code, as_dict=True
            )
            for r in rows:
                frappe.db.delete("Bin", r.name)
                deleted_bins += 1

        deleted_items = 0
        for item_code in _test_items:
            if frappe.db.exists("Item", item_code):
                frappe.db.delete("Item", item_code)
                deleted_items += 1

        frappe.db.commit()
        _pass(f"Removed {deleted_bins} Bin records and {deleted_items} Item records")
    except Exception as e:
        _fail("T13 cleanup crashed", str(e)[:120])

    print("\n=== DONE ===")
