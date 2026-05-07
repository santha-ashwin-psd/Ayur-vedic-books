"""
L1 — Dashboard API test.

Scenario:
  T1  get_home_dashboard() → all 14 top-level keys present
  T2  get_home_dashboard() → period keys present and valid dates
  T3  get_home_dashboard() → numeric KPIs are non-negative
  T4  get_home_dashboard() → month_revenue >= month_outstanding (always true)
  T5  get_home_dashboard() → overdue_count matches len(overdue_invoices)
  T6  get_home_dashboard() → aging_buckets has all 5 bucket keys, all >= 0
  T7  get_home_dashboard() → top_customers is a list
  T8  get_home_dashboard() → gst_summary is a list
  T9  get_cash_position()  → returns bank_accounts list + total_cash numeric
  T10 get_cash_position()  → total_cash == sum of bank account balances
  T11 get_profit_and_loss() → all expected keys present, net_profit is numeric
  T12 get_profit_and_loss() → income - cogs - expense == net_profit
  T13 get_balance_sheet_totals() → all expected keys present, values >= 0
  T14 get_trial_balance()  → returns list; each row has account, debit, credit, closing
  T15 get_ar_aging()       → returns list; each row has customer + bucket keys
  T16 search_transactions() → returns list with expected fields
  T17 get_pl_monthly_breakdown() → returns list with month/income/expense/profit
  T18 get_gstr_summary()   → has output/itc/net_by_type/totals sections
"""
import frappe
from frappe.utils import flt, today, get_first_day, get_last_day, add_days

COMPANY = "Eiffele gaming"

DASHBOARD_KEYS = {
    "company", "period", "month_revenue", "month_collected", "month_outstanding",
    "month_payments_in", "month_payments_out", "net_profit_mtd",
    "total_assets", "total_liabilities", "overdue_count",
    "top_customers", "overdue_invoices", "gst_summary", "aging_buckets",
}
AGING_KEYS = {"current", "1_30", "31_60", "61_90", "over_90"}


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def run():
    print("\n=== Dashboard API L1 Test ===")

    import importlib
    import zoho_books_clone.api.dashboard as dash_mod
    import zoho_books_clone.db.queries as q_mod
    importlib.reload(dash_mod)
    importlib.reload(q_mod)

    from zoho_books_clone.api.dashboard import (
        get_home_dashboard,
        get_cash_position,
        search_transactions,
    )
    from zoho_books_clone.db.queries import (
        get_profit_and_loss,
        get_balance_sheet_totals,
        get_trial_balance,
        get_ar_aging,
        get_pl_monthly_breakdown,
        get_gstr_summary,
    )

    t   = today()
    som = str(get_first_day(t))
    eom = str(get_last_day(t))

    # ── T1: get_home_dashboard() → all keys present ───────────────────────────
    print("\n--- T1: get_home_dashboard() → all 15 keys present ---")
    dash = None
    try:
        dash = get_home_dashboard(COMPANY)
        missing = DASHBOARD_KEYS - set(dash.keys())
        if not missing:
            _pass(f"All {len(DASHBOARD_KEYS)} keys present")
        else:
            _fail("Missing keys", str(missing))
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    if dash is None:
        print("  ABORT: dashboard call failed — cannot continue")
        return

    # ── T2: period keys present and valid dates ───────────────────────────────
    print("\n--- T2: period is a dict with from/to matching current month ---")
    try:
        period = dash.get("period", {})
        if isinstance(period, dict) and "from" in period and "to" in period:
            _pass(f"period present: {period['from']} → {period['to']}")
        else:
            _fail("period not a dict with from/to", str(period))

        if str(period.get("from", "")) == som and str(period.get("to", "")) == eom:
            _pass("period matches current month-to-date window")
        else:
            _fail("period mismatch", f"expected {som}→{eom}, got {period.get('from')}→{period.get('to')}")
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: numeric KPIs are non-negative ─────────────────────────────────────
    print("\n--- T3: numeric KPIs are non-negative ---")
    numeric_keys = [
        "month_revenue", "month_collected", "month_outstanding",
        "month_payments_in", "month_payments_out",
        "total_assets", "total_liabilities",
    ]
    try:
        failed_keys = [k for k in numeric_keys if flt(dash.get(k)) < 0]
        if not failed_keys:
            _pass("All numeric KPIs >= 0")
        else:
            for k in failed_keys:
                _fail(f"{k} is negative", str(dash.get(k)))
        # Log values for info
        for k in numeric_keys:
            print(f"      {k} = {flt(dash.get(k)):.2f}")
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: month_revenue >= month_outstanding ─────────────────────────────────
    print("\n--- T4: month_revenue >= month_outstanding ---")
    try:
        rev = flt(dash.get("month_revenue"))
        outstanding = flt(dash.get("month_outstanding"))
        if rev >= outstanding:
            _pass(f"month_revenue ({rev:.2f}) >= month_outstanding ({outstanding:.2f})")
        else:
            _fail("month_revenue < month_outstanding (impossible)", f"{rev:.2f} < {outstanding:.2f}")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: overdue_count matches len(overdue_invoices) ───────────────────────
    print("\n--- T5: overdue_count == len(overdue_invoices) ---")
    try:
        count = dash.get("overdue_count", -1)
        invoices = dash.get("overdue_invoices", [])
        if count == len(invoices):
            _pass(f"overdue_count ({count}) == len(overdue_invoices)")
        else:
            _fail("overdue_count mismatch", f"count={count}, list len={len(invoices)}")
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: aging_buckets has all 5 keys, all >= 0 ───────────────────────────
    print("\n--- T6: aging_buckets has all 5 bucket keys, all >= 0 ---")
    try:
        aging = dash.get("aging_buckets", {})
        missing_buckets = AGING_KEYS - set(aging.keys())
        if not missing_buckets:
            _pass(f"All 5 aging buckets present: {list(aging.keys())}")
        else:
            _fail("Missing aging buckets", str(missing_buckets))

        neg_buckets = [k for k in AGING_KEYS if flt(aging.get(k)) < 0]
        if not neg_buckets:
            _pass("All aging bucket values >= 0")
        else:
            _fail("Negative aging bucket values", str(neg_buckets))
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: top_customers is a list ───────────────────────────────────────────
    print("\n--- T7: top_customers is a list ---")
    try:
        tc = dash.get("top_customers")
        if isinstance(tc, list):
            _pass(f"top_customers is a list ({len(tc)} entries)")
        else:
            _fail("top_customers not a list", type(tc).__name__)
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: gst_summary is a list ─────────────────────────────────────────────
    print("\n--- T8: gst_summary is a list ---")
    try:
        gs = dash.get("gst_summary")
        if isinstance(gs, list):
            _pass(f"gst_summary is a list ({len(gs)} entries)")
        else:
            _fail("gst_summary not a list", type(gs).__name__)
    except Exception as e:
        _fail("T8 crashed", str(e)[:120])

    # ── T9: get_cash_position() → bank_accounts + total_cash ─────────────────
    print("\n--- T9: get_cash_position() → bank_accounts + total_cash ---")
    cash_pos = None
    try:
        cash_pos = get_cash_position(COMPANY)
        if isinstance(cash_pos.get("bank_accounts"), list):
            _pass(f"bank_accounts is a list ({len(cash_pos['bank_accounts'])} accounts)")
        else:
            _fail("bank_accounts not a list", str(type(cash_pos.get("bank_accounts"))))

        if "total_cash" in cash_pos:
            _pass(f"total_cash present: {flt(cash_pos['total_cash']):.2f}")
        else:
            _fail("total_cash key missing")
    except Exception as e:
        _fail("T9 crashed", str(e)[:120])

    # ── T10: total_cash == sum of individual bank balances ────────────────────
    print("\n--- T10: total_cash == sum of individual account balances ---")
    try:
        if cash_pos:
            computed_total = sum(flt(b.get("current_balance", 0)) for b in cash_pos["bank_accounts"])
            reported_total = flt(cash_pos.get("total_cash"))
            if abs(computed_total - reported_total) < 0.01:
                _pass(f"total_cash ({reported_total:.2f}) == sum of balances ({computed_total:.2f})")
            else:
                _fail("total_cash mismatch", f"reported={reported_total:.2f}, computed={computed_total:.2f}")
        else:
            _fail("Skipped (T9 failed)")
    except Exception as e:
        _fail("T10 crashed", str(e)[:120])

    # ── T11: get_profit_and_loss() → all keys present ─────────────────────────
    print("\n--- T11: get_profit_and_loss() → all expected keys present ---")
    pl = None
    try:
        pl = get_profit_and_loss(COMPANY, som, eom)
        pl_keys = {"total_income", "cogs", "gross_profit", "total_expense", "net_profit"}
        missing_pl = pl_keys - set(pl.keys())
        if not missing_pl:
            _pass("All P&L keys present")
        else:
            _fail("Missing P&L keys", str(missing_pl))
        print(f"      income={flt(pl.get('total_income')):.2f}  cogs={flt(pl.get('cogs')):.2f}  "
              f"expense={flt(pl.get('total_expense')):.2f}  net={flt(pl.get('net_profit')):.2f}")
    except Exception as e:
        _fail("T11 crashed", str(e)[:120])

    # ── T12: income - cogs - expense == net_profit ────────────────────────────
    print("\n--- T12: income - cogs - expense == net_profit ---")
    try:
        if pl:
            expected_net = flt(pl.get("total_income")) - flt(pl.get("cogs")) - flt(pl.get("total_expense"))
            actual_net   = flt(pl.get("net_profit"))
            if abs(expected_net - actual_net) < 0.01:
                _pass(f"net_profit formula correct: {actual_net:.2f}")
            else:
                _fail("net_profit formula incorrect", f"computed={expected_net:.2f}, got={actual_net:.2f}")
        else:
            _fail("Skipped (T11 failed)")
    except Exception as e:
        _fail("T12 crashed", str(e)[:120])

    # ── T13: get_balance_sheet_totals() → all expected keys, values >= 0 ─────
    print("\n--- T13: get_balance_sheet_totals() → keys present, values >= 0 ---")
    try:
        bs = get_balance_sheet_totals(COMPANY, t)
        bs_keys = {
            "total_assets", "cash_and_bank", "receivables", "inventory_value",
            "itc_receivable", "other_assets",
            "total_liabilities", "payables", "gst_liability", "other_liabilities",
            "total_equity",
        }
        missing_bs = bs_keys - set(bs.keys())
        if not missing_bs:
            _pass("All balance sheet keys present")
        else:
            _fail("Missing balance sheet keys", str(missing_bs))

        neg_bs = [k for k in bs_keys if flt(bs.get(k)) < 0]
        if not neg_bs:
            _pass("All balance sheet values >= 0")
        else:
            _fail("Negative balance sheet values", str(neg_bs))

        _pass(f"total_assets={flt(bs.get('total_assets')):.2f}  "
              f"total_liabilities={flt(bs.get('total_liabilities')):.2f}  "
              f"equity={flt(bs.get('total_equity')):.2f}")
    except Exception as e:
        _fail("T13 crashed", str(e)[:120])

    # ── T14: get_trial_balance() → list with required fields ──────────────────
    print("\n--- T14: get_trial_balance() → list with account/debit/credit/closing ---")
    try:
        tb = get_trial_balance(COMPANY, som, eom)
        if isinstance(tb, list):
            _pass(f"get_trial_balance returns list ({len(tb)} rows)")
        else:
            _fail("Non-list result", type(tb).__name__)

        if tb:
            row = tb[0]
            tb_keys = {"account", "debit", "credit", "closing"}
            missing_tb = tb_keys - set(row.keys())
            if not missing_tb:
                _pass("All trial balance row keys present")
            else:
                _fail("Missing trial balance keys", str(missing_tb))

            # DR = CR should hold across total trial balance
            total_dr = sum(flt(r.get("debit"))  for r in tb)
            total_cr = sum(flt(r.get("credit")) for r in tb)
            if abs(total_dr - total_cr) < 0.01:
                _pass(f"Trial balance DR = CR = {total_dr:.2f}")
            else:
                _fail("Trial balance out of balance", f"DR={total_dr:.2f}, CR={total_cr:.2f}")
    except Exception as e:
        _fail("T14 crashed", str(e)[:120])

    # ── T15: get_ar_aging() → list with customer + bucket keys ───────────────
    print("\n--- T15: get_ar_aging() → list with required fields ---")
    try:
        aging = get_ar_aging(COMPANY, t)
        if isinstance(aging, list):
            _pass(f"get_ar_aging returns list ({len(aging)} customers)")
        else:
            _fail("Non-list result", type(aging).__name__)

        if aging:
            row = aging[0]
            ar_keys = {"customer", "current", "days_1_30", "days_31_60", "days_61_90", "days_90_plus", "total"}
            missing_ar = ar_keys - set(row.keys())
            if not missing_ar:
                _pass("All AR aging row keys present")
            else:
                _fail("Missing AR aging keys", str(missing_ar))
    except Exception as e:
        _fail("T15 crashed", str(e)[:120])

    # ── T16: search_transactions() → list with expected fields ────────────────
    print("\n--- T16: search_transactions() → list with expected fields ---")
    try:
        results = search_transactions("INV", COMPANY)
        if isinstance(results, list):
            _pass(f"search_transactions returns list ({len(results)} results)")
        else:
            _fail("Non-list result", type(results).__name__)

        if results:
            row = results[0]
            txn_keys = {"doctype", "name", "amount", "date"}
            missing_txn = txn_keys - set(row.keys())
            if not missing_txn:
                _pass("All transaction result keys present")
            else:
                _fail("Missing transaction keys", str(missing_txn))
        else:
            _pass("search_transactions returned empty list (no matching invoices starting with INV)")
    except Exception as e:
        _fail("T16 crashed", str(e)[:120])

    # ── T17: get_pl_monthly_breakdown() → list with month/income/expense/profit
    print("\n--- T17: get_pl_monthly_breakdown() → monthly list ---")
    try:
        from_6m = str(add_days(t, -180))
        pl_monthly = get_pl_monthly_breakdown(COMPANY, from_6m, eom)
        if isinstance(pl_monthly, list):
            _pass(f"get_pl_monthly_breakdown returns list ({len(pl_monthly)} months)")
        else:
            _fail("Non-list result", type(pl_monthly).__name__)

        if pl_monthly:
            row = pl_monthly[0]
            pl_monthly_keys = {"month", "income", "expense", "profit"}
            missing_plm = pl_monthly_keys - set(row.keys())
            if not missing_plm:
                _pass("All monthly breakdown keys present")
            else:
                _fail("Missing monthly breakdown keys", str(missing_plm))

            # Verify profit = income - expense
            for row in pl_monthly:
                exp_profit = flt(row.get("income")) - flt(row.get("expense"))
                act_profit = flt(row.get("profit"))
                if abs(exp_profit - act_profit) > 0.01:
                    _fail(f"profit mismatch for month {row.get('month')}", f"expected={exp_profit:.2f}, got={act_profit:.2f}")
                    break
            else:
                _pass("profit = income - expense for all monthly rows")
    except Exception as e:
        _fail("T17 crashed", str(e)[:120])

    # ── T18: get_gstr_summary() → has output/itc/net_by_type/totals ──────────
    print("\n--- T18: get_gstr_summary() → GSTR-3B style summary ---")
    try:
        gstr = get_gstr_summary(COMPANY, som, eom)
        gstr_sections = {"output", "itc", "net_by_type", "totals"}
        missing_gstr = gstr_sections - set(gstr.keys())
        if not missing_gstr:
            _pass("All GSTR summary sections present")
        else:
            _fail("Missing GSTR sections", str(missing_gstr))

        totals = gstr.get("totals", {})
        totals_keys = {"total_output", "total_itc", "net_tax_liability"}
        missing_totals = totals_keys - set(totals.keys())
        if not missing_totals:
            _pass("All GSTR totals keys present")
        else:
            _fail("Missing GSTR totals keys", str(missing_totals))

        # Verify net_tax_liability = total_output - total_itc
        expected_net = flt(totals.get("total_output")) - flt(totals.get("total_itc"))
        actual_net   = flt(totals.get("net_tax_liability"))
        if abs(expected_net - actual_net) < 0.01:
            _pass(f"net_tax_liability correct: {actual_net:.2f}")
        else:
            _fail("net_tax_liability formula wrong", f"expected={expected_net:.2f}, got={actual_net:.2f}")

        if isinstance(gstr.get("net_by_type"), list):
            _pass(f"net_by_type is a list ({len(gstr['net_by_type'])} entries)")
        else:
            _fail("net_by_type not a list")
    except Exception as e:
        _fail("T18 crashed", str(e)[:120])

    print("\n=== DONE ===")
