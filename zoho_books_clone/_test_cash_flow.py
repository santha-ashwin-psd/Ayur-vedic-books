"""
L1 — Cash Flow Statement test.

Scenario:
  T1  get_cash_flow() → dict with 4 required keys
  T2  All values numeric
  T3  net_change == operating + investing + financing (arithmetic consistency)
  T4  operating == get_profit_and_loss().net_profit (same formula, different sign conv)
  T5  Empty company → all zeros
  T6  Future period (no entries) → all zeros
  T7  operating + investing + financing == net change in all asset accounts
  T8  get_pl_monthly_breakdown income/expense relates to get_cash_flow operating
  T9  Broader period — same formula consistency holds
  T10 Verify investing = net movement in Asset+Stock accounts (spot-check)
"""
import frappe
from frappe.utils import flt, today, add_days, get_first_day, get_last_day

COMPANY = "Eiffele gaming"

REQUIRED_KEYS = {"operating", "investing", "financing", "net_change"}


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def run():
    print("\n=== Cash Flow Statement L1 Test ===")

    import importlib
    import zoho_books_clone.db.queries as q_mod
    importlib.reload(q_mod)
    from zoho_books_clone.db.queries import (
        get_cash_flow,
        get_profit_and_loss,
        get_pl_monthly_breakdown,
    )

    t   = today()
    # Use a wide period to capture historical GL data
    wide_from = str(add_days(t, -730))    # 2 years back
    wide_to   = t
    som = str(get_first_day(t))
    eom = str(get_last_day(t))

    # ── T1: returns dict with required keys ──────────────────────────────────
    print("\n--- T1: get_cash_flow() → dict with 4 required keys ---")
    cf = None
    try:
        cf = get_cash_flow(COMPANY, wide_from, wide_to)
        missing = REQUIRED_KEYS - set(cf.keys())
        if not missing:
            _pass(f"All 4 keys present: {list(cf.keys())}")
        else:
            _fail("Missing keys", str(missing))
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    if cf is None:
        print("  ABORT: get_cash_flow failed")
        return

    print(f"  operating={flt(cf.get('operating')):.2f}  investing={flt(cf.get('investing')):.2f}  "
          f"financing={flt(cf.get('financing')):.2f}  net_change={flt(cf.get('net_change')):.2f}")

    # ── T2: all values numeric ────────────────────────────────────────────────
    print("\n--- T2: all values are numeric ---")
    try:
        non_numeric = [k for k in REQUIRED_KEYS if not isinstance(cf.get(k), (int, float))]
        if not non_numeric:
            _pass("All values are numeric")
        else:
            _fail("Non-numeric values", str({k: type(cf[k]) for k in non_numeric}))
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: net_change == operating + investing + financing ───────────────────
    print("\n--- T3: net_change == operating + investing + financing ---")
    try:
        expected = flt(cf.get("operating")) + flt(cf.get("investing")) + flt(cf.get("financing"))
        actual   = flt(cf.get("net_change"))
        if abs(expected - actual) < 0.01:
            _pass(f"net_change = {actual:.2f} = {flt(cf['operating']):.2f} + {flt(cf['investing']):.2f} + {flt(cf['financing']):.2f}")
        else:
            _fail("net_change arithmetic wrong", f"sum={expected:.2f}, reported={actual:.2f}")
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: operating == get_profit_and_loss().net_profit ─────────────────────
    print("\n--- T4: operating == P&L net_profit (same underlying GL data) ---")
    try:
        pl = get_profit_and_loss(COMPANY, wide_from, wide_to)
        pl_net = flt(pl.get("net_profit"))
        cf_op  = flt(cf.get("operating"))
        if abs(cf_op - pl_net) < 0.01:
            _pass(f"operating ({cf_op:.2f}) == P&L net_profit ({pl_net:.2f})")
        else:
            _fail("operating != P&L net_profit — formula bug",
                  f"cf.operating={cf_op:.2f}, pl.net_profit={pl_net:.2f}")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: empty company → all zeros ─────────────────────────────────────────
    print("\n--- T5: non-existent company → all zeros ---")
    try:
        cf_empty = get_cash_flow("NONEXISTENT CO", wide_from, wide_to)
        all_zero = all(abs(flt(cf_empty.get(k))) < 0.01 for k in REQUIRED_KEYS)
        if all_zero:
            _pass("All zero for unknown company")
        else:
            _fail("Non-zero values for unknown company", str(cf_empty))
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: future period → all zeros ─────────────────────────────────────────
    print("\n--- T6: future period (no GL entries) → all zeros ---")
    try:
        future_from = str(add_days(t, 365))
        future_to   = str(add_days(t, 730))
        cf_future = get_cash_flow(COMPANY, future_from, future_to)
        all_zero = all(abs(flt(cf_future.get(k))) < 0.01 for k in REQUIRED_KEYS)
        if all_zero:
            _pass("All zero for future period with no GL entries")
        else:
            _fail("Non-zero values for future period", str(cf_future))
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: investing = net movement in Asset + Stock GL accounts ─────────────
    print("\n--- T7: investing == net movement in Asset+Stock GL accounts ---")
    try:
        asset_stock_net = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(g.debit) - SUM(g.credit), 0) AS net
            FROM `tabGeneral Ledger Entry` g
            JOIN `tabAccount` a ON a.name = g.account
            WHERE g.company = %(co)s
              AND g.is_cancelled = 0
              AND g.posting_date BETWEEN %(fd)s AND %(td)s
              AND a.account_type IN ('Asset', 'Stock')
        """, {"co": COMPANY, "fd": wide_from, "td": wide_to}, as_dict=True)[0].net)

        cf_investing = flt(cf.get("investing"))
        if abs(cf_investing - asset_stock_net) < 0.01:
            _pass(f"investing ({cf_investing:.2f}) == Asset+Stock GL net ({asset_stock_net:.2f})")
        else:
            _fail("investing != Asset+Stock GL net",
                  f"cf={cf_investing:.2f}, direct={asset_stock_net:.2f}")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: monthly P&L income/expense relates to operating ───────────────────
    print("\n--- T8: monthly breakdown income/expense sums relate to operating ---")
    try:
        monthly = get_pl_monthly_breakdown(COMPANY, wide_from, wide_to)
        if isinstance(monthly, list):
            total_monthly_profit = sum(flt(m.get("profit")) for m in monthly)
            # The total monthly profit over all months should equal P&L net_profit
            pl = get_profit_and_loss(COMPANY, wide_from, wide_to)
            pl_net = flt(pl.get("net_profit"))
            if abs(total_monthly_profit - pl_net) < 0.01:
                _pass(f"Sum of monthly profits ({total_monthly_profit:.2f}) == P&L net_profit ({pl_net:.2f})")
            else:
                _fail("Monthly profit sum != P&L net_profit",
                      f"monthly_sum={total_monthly_profit:.2f}, pl={pl_net:.2f}")
        else:
            _fail("get_pl_monthly_breakdown returned non-list")
    except Exception as e:
        _fail("T8 crashed", str(e)[:120])

    # ── T9: formula consistency holds across a shorter period too ─────────────
    print("\n--- T9: formula consistency for current-month period ---")
    try:
        cf_month = get_cash_flow(COMPANY, som, eom)
        pl_month = get_profit_and_loss(COMPANY, som, eom)

        # net_change arithmetic
        expected_nc = (flt(cf_month.get("operating")) +
                       flt(cf_month.get("investing")) +
                       flt(cf_month.get("financing")))
        actual_nc   = flt(cf_month.get("net_change"))
        if abs(expected_nc - actual_nc) < 0.01:
            _pass(f"Monthly net_change arithmetic correct: {actual_nc:.2f}")
        else:
            _fail("Monthly net_change arithmetic wrong",
                  f"sum={expected_nc:.2f}, reported={actual_nc:.2f}")

        # operating == P&L net_profit for same period
        op_month = flt(cf_month.get("operating"))
        pl_net_m = flt(pl_month.get("net_profit"))
        if abs(op_month - pl_net_m) < 0.01:
            _pass(f"Monthly operating ({op_month:.2f}) == monthly P&L net_profit ({pl_net_m:.2f})")
        else:
            _fail("Monthly operating != monthly P&L net_profit",
                  f"cf={op_month:.2f}, pl={pl_net_m:.2f}")
    except Exception as e:
        _fail("T9 crashed", str(e)[:120])

    # ── T10: financing = Equity net - Liability net ────────────────────────────
    print("\n--- T10: financing == Equity_net - Liability_net GL accounts ---")
    try:
        eq_liab_net = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(g.debit) - SUM(g.credit), 0) AS net
            FROM `tabGeneral Ledger Entry` g
            JOIN `tabAccount` a ON a.name = g.account
            WHERE g.company = %(co)s
              AND g.is_cancelled = 0
              AND g.posting_date BETWEEN %(fd)s AND %(td)s
              AND a.account_type = 'Equity'
        """, {"co": COMPANY, "fd": wide_from, "td": wide_to}, as_dict=True)[0].net)

        liab_net = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(g.debit) - SUM(g.credit), 0) AS net
            FROM `tabGeneral Ledger Entry` g
            JOIN `tabAccount` a ON a.name = g.account
            WHERE g.company = %(co)s
              AND g.is_cancelled = 0
              AND g.posting_date BETWEEN %(fd)s AND %(td)s
              AND a.account_type = 'Liability'
        """, {"co": COMPANY, "fd": wide_from, "td": wide_to}, as_dict=True)[0].net)

        expected_fin = eq_liab_net - liab_net
        cf_fin       = flt(cf.get("financing"))
        if abs(cf_fin - expected_fin) < 0.01:
            _pass(f"financing ({cf_fin:.2f}) == Equity_net ({eq_liab_net:.2f}) - Liability_net ({liab_net:.2f})")
        else:
            _fail("financing formula mismatch",
                  f"cf={cf_fin:.2f}, expected={expected_fin:.2f}")
    except Exception as e:
        _fail("T10 crashed", str(e)[:120])

    print("\n=== DONE ===")
