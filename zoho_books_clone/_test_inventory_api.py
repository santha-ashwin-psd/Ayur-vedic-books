"""
L1 — Inventory API test.

Scenario:
  T1  get_stock_summary() → list, each row has required keys, actual_qty >= 0
  T2  get_stock_summary(warehouse=X) → all rows are for that warehouse
  T3  get_stock_summary(show_zero_stock=1) → includes zero-stock bins
  T4  get_stock_ledger_entries() → list of SLE rows with required fields
  T5  get_stock_ledger_entries(item_code=X) → all rows match that item
  T6  get_stock_ledger_entries(from_date, to_date) → date range honoured
  T7  get_reorder_items() → returns list (may be empty); set a reorder_level and verify
  T8  check_stock_availability: sufficient=True when stock > required
  T9  check_stock_availability: sufficient=False + shortage when stock < required
  T10 get_inventory_kpis() → dict with expected keys, values >= 0
  T11 Reorder alert: set bin reorder_level above actual_qty → item appears in alerts
  T12 Cleanup reorder_level change
"""
import frappe
from frappe.utils import flt, today, add_days

COMPANY  = "Eiffele gaming"
REQUIRED_SUMMARY_KEYS = {
    "item_code", "item_name", "warehouse",
    "actual_qty", "valuation_rate", "stock_value", "below_reorder",
}
REQUIRED_SLE_KEYS = {
    "name", "item_code", "warehouse", "posting_date",
    "actual_qty", "qty_after_transaction",
}


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def run():
    print("\n=== Inventory API L1 Test ===")

    import importlib
    import zoho_books_clone.api.inventory as inv_mod
    importlib.reload(inv_mod)
    from zoho_books_clone.api.inventory import (
        get_stock_summary,
        get_stock_ledger_entries,
        get_reorder_items,
        check_stock_availability,
        get_inventory_kpis,
    )

    # Pick a known item + warehouse with stock
    bin_row = frappe.db.get_value(
        "Bin", {"actual_qty": [">", 0]},
        ["item_code", "warehouse", "actual_qty", "reorder_level"],
        as_dict=True, order_by="actual_qty desc",
    )
    if not bin_row:
        print("  ABORT: no Bin rows with stock found")
        return

    TEST_ITEM = bin_row.item_code
    TEST_WH   = bin_row.warehouse
    TEST_QTY  = flt(bin_row.actual_qty)
    print(f"  test item={TEST_ITEM}  wh={TEST_WH}  qty={TEST_QTY:.0f}")

    # ── T1: get_stock_summary → list with required keys ───────────────────────────
    print("\n--- T1: get_stock_summary() → list, required keys present ---")
    try:
        summary = get_stock_summary()
        if isinstance(summary, list) and len(summary) > 0:
            _pass(f"Returns list of {len(summary)} rows")
        else:
            _fail("Empty or non-list result", type(summary).__name__)

        row = next((r for r in summary if r.get("item_code") == TEST_ITEM and r.get("warehouse") == TEST_WH), None)
        if row:
            missing = REQUIRED_SUMMARY_KEYS - set(row.keys())
            if not missing:
                _pass(f"All required keys present in {TEST_ITEM} row")
            else:
                _fail("Missing keys", str(missing))
            if flt(row.get("actual_qty")) > 0:
                _pass(f"actual_qty = {row['actual_qty']:.0f}")
            else:
                _fail("actual_qty not positive", str(row.get("actual_qty")))
        else:
            _fail(f"{TEST_ITEM}/{TEST_WH} not in summary")
    except Exception as e:
        _fail("T1 crashed", str(e)[:100])

    # ── T2: filter by warehouse ───────────────────────────────────────────────────
    print("\n--- T2: get_stock_summary(warehouse=X) → all rows for that warehouse ---")
    try:
        wh_summary = get_stock_summary(warehouse=TEST_WH)
        if isinstance(wh_summary, list):
            wrong_wh = [r for r in wh_summary if r.get("warehouse") != TEST_WH]
            if not wrong_wh:
                _pass(f"All {len(wh_summary)} rows belong to warehouse {TEST_WH}")
            else:
                _fail("Rows from wrong warehouse", str(wrong_wh[0]))
        else:
            _fail("Non-list result", type(wh_summary).__name__)
    except Exception as e:
        _fail("T2 crashed", str(e)[:100])

    # ── T3: show_zero_stock=1 → includes bins ─────────────────────────────────────
    print("\n--- T3: get_stock_summary(show_zero_stock=1) ---")
    try:
        all_summary  = get_stock_summary(show_zero_stock=1)
        some_summary = get_stock_summary(show_zero_stock=0)
        if len(all_summary) >= len(some_summary):
            _pass(f"show_zero_stock=1 returns >= show_zero_stock=0 ({len(all_summary)} >= {len(some_summary)})")
        else:
            _fail("show_zero_stock=1 returned fewer rows", f"{len(all_summary)} < {len(some_summary)}")
    except Exception as e:
        _fail("T3 crashed", str(e)[:100])

    # ── T4: get_stock_ledger_entries() → list with required fields ────────────────
    print("\n--- T4: get_stock_ledger_entries() → list with required fields ---")
    try:
        sles = get_stock_ledger_entries()
        if isinstance(sles, list) and len(sles) > 0:
            _pass(f"Returns {len(sles)} SLE rows")
        else:
            _fail("Empty or non-list SLE result", type(sles).__name__)

        if sles:
            row = sles[0]
            missing = REQUIRED_SLE_KEYS - set(row.keys())
            if not missing:
                _pass("All required SLE fields present")
            else:
                _fail("Missing SLE fields", str(missing))
    except Exception as e:
        _fail("T4 crashed", str(e)[:100])

    # ── T5: filter by item_code ───────────────────────────────────────────────────
    print("\n--- T5: get_stock_ledger_entries(item_code=X) ---")
    try:
        item_sles = get_stock_ledger_entries(item_code=TEST_ITEM)
        if isinstance(item_sles, list):
            wrong = [r for r in item_sles if r.get("item_code") != TEST_ITEM]
            if not wrong:
                _pass(f"{len(item_sles)} SLE rows all for item {TEST_ITEM}")
            else:
                _fail("Rows for wrong item", str(wrong[0]))
        else:
            _fail("Non-list result")
    except Exception as e:
        _fail("T5 crashed", str(e)[:100])

    # ── T6: date range filter ─────────────────────────────────────────────────────
    print("\n--- T6: SLE date range filter ---")
    try:
        from_d = add_days(today(), -365)
        to_d   = today()
        dated  = get_stock_ledger_entries(from_date=from_d, to_date=to_d)
        all_in_range = all(
            from_d <= str(r.get("posting_date", "")) <= to_d
            for r in dated
        )
        if isinstance(dated, list):
            _pass(f"{len(dated)} SLE rows in date range")
        else:
            _fail("Non-list result")
        if all_in_range:
            _pass("All rows within date range")
        else:
            _fail("Some rows outside date range")
    except Exception as e:
        _fail("T6 crashed", str(e)[:100])

    # ── T7: get_reorder_items() baseline ─────────────────────────────────────────
    print("\n--- T7: get_reorder_items() baseline (list returned) ---")
    try:
        alerts_before = get_reorder_items()
        if isinstance(alerts_before, list):
            _pass(f"get_reorder_items() returns list ({len(alerts_before)} items)")
        else:
            _fail("Non-list result", type(alerts_before).__name__)
    except Exception as e:
        _fail("T7 crashed", str(e)[:100])

    # ── T8: check_stock_availability — sufficient ─────────────────────────────────
    print("\n--- T8: check_stock_availability — sufficient ---")
    try:
        needed = max(1, TEST_QTY - 1)   # 1 less than actual → should be sufficient
        result = check_stock_availability(TEST_ITEM, TEST_WH, str(needed))
        if result.get("sufficient"):
            _pass(f"sufficient=True for {needed:.0f} needed, {TEST_QTY:.0f} available")
        else:
            _fail("sufficient=False when there is enough stock", str(result))
        if flt(result.get("shortage")) == 0:
            _pass("shortage = 0")
        else:
            _fail("shortage non-zero", str(result.get("shortage")))
    except Exception as e:
        _fail("T8 crashed", str(e)[:100])

    # ── T9: check_stock_availability — insufficient ───────────────────────────────
    print("\n--- T9: check_stock_availability — insufficient ---")
    try:
        needed = TEST_QTY + 999999
        result = check_stock_availability(TEST_ITEM, TEST_WH, str(needed))
        if not result.get("sufficient"):
            _pass("sufficient=False when stock is insufficient")
        else:
            _fail("sufficient=True when stock is clearly insufficient", str(result))
        if flt(result.get("shortage")) > 0:
            _pass(f"shortage = {result['shortage']:.0f}")
        else:
            _fail("shortage = 0 when there should be a shortage")
    except Exception as e:
        _fail("T9 crashed", str(e)[:100])

    # ── T10: get_inventory_kpis() ─────────────────────────────────────────────────
    print("\n--- T10: get_inventory_kpis() ---")
    try:
        kpis = get_inventory_kpis()
        required_keys = {"total_stock_value", "unique_items_in_stock",
                         "warehouses_with_stock", "reorder_alerts"}
        missing = required_keys - set(kpis.keys())
        if not missing:
            _pass("All KPI keys present")
        else:
            _fail("Missing KPI keys", str(missing))
        if flt(kpis.get("total_stock_value")) >= 0:
            _pass(f"total_stock_value = {kpis['total_stock_value']:.2f}")
        else:
            _fail("total_stock_value negative")
        if int(kpis.get("unique_items_in_stock", 0)) > 0:
            _pass(f"unique_items_in_stock = {kpis['unique_items_in_stock']}")
        else:
            _fail("unique_items_in_stock = 0 (expected > 0)")
    except Exception as e:
        _fail("T10 crashed", str(e)[:100])

    # ── T11: reorder alert triggered when qty < reorder_level ────────────────────
    print("\n--- T11: Reorder alert — set reorder_level above actual_qty ---")
    orig_reorder = flt(frappe.db.get_value("Bin",
                        {"item_code": TEST_ITEM, "warehouse": TEST_WH}, "reorder_level"))
    try:
        # Set reorder_level higher than actual_qty to force an alert
        high_level = TEST_QTY + 1000
        frappe.db.set_value("Bin",
                            {"item_code": TEST_ITEM, "warehouse": TEST_WH},
                            "reorder_level", high_level, update_modified=False)
        frappe.db.commit()

        alerts_after = get_reorder_items()
        item_alert = next(
            (a for a in alerts_after
             if a.get("item_code") == TEST_ITEM and a.get("warehouse") == TEST_WH),
            None,
        )
        if item_alert:
            _pass(f"Item appears in reorder alerts (level={high_level:.0f}, qty={TEST_QTY:.0f})")
            if flt(item_alert.get("shortage_qty")) > 0:
                _pass(f"shortage_qty = {item_alert['shortage_qty']:.0f}")
            else:
                _fail("shortage_qty not positive", str(item_alert.get("shortage_qty")))
        else:
            _fail("Item NOT in reorder alerts after setting level above qty")

        # Also verify below_reorder flag in get_stock_summary
        wh_sum = get_stock_summary(warehouse=TEST_WH)
        item_row = next((r for r in wh_sum if r.get("item_code") == TEST_ITEM), None)
        if item_row and item_row.get("below_reorder"):
            _pass("below_reorder=True in get_stock_summary after level raised")
        else:
            _fail("below_reorder not True in stock_summary", str(item_row))

    except Exception as e:
        _fail("T11 crashed", str(e)[:100])

    # ── T12: Cleanup — restore reorder_level ─────────────────────────────────────
    print("\n--- T12: Cleanup — restore reorder_level ---")
    try:
        frappe.db.set_value("Bin",
                            {"item_code": TEST_ITEM, "warehouse": TEST_WH},
                            "reorder_level", orig_reorder, update_modified=False)
        frappe.db.commit()
        restored = flt(frappe.db.get_value("Bin",
                        {"item_code": TEST_ITEM, "warehouse": TEST_WH}, "reorder_level"))
        if abs(restored - orig_reorder) < 0.01:
            _pass(f"reorder_level restored to {orig_reorder:.0f}")
        else:
            _fail("reorder_level not restored", f"{restored:.0f}")
    except Exception as e:
        _fail("T12 crashed", str(e)[:100])

    print("\n=== DONE ===")
