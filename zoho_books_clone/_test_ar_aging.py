"""
L1 — AR Aging Report test.

Scenario:
  T1  get_ar_aging(company, today) → list returned
  T2  each row has all required keys (customer, 5 buckets, total)
  T3  total = current + days_1_30 + days_31_60 + days_61_90 + days_90_plus (per customer)
  T4  sum of all customer totals == total outstanding from tabSales Invoice directly
  T5  bucket assignment is mathematically correct (verify each invoice → correct bucket)
  T6  current bucket only has invoices with due_date >= as_of_date
  T7  docstatus=0 and docstatus=2 invoices excluded from aging
  T8  _get_aging_buckets aggregate sums match sum of customer-level buckets
  T9  empty company returns empty list
  T10 get_outstanding_invoices matches what get_ar_aging reports for a customer
  T11 older as_of_date shifts invoices toward more-overdue buckets
  T12 get_ar_aging all bucket values >= 0
"""
import frappe
from frappe.utils import flt, today, add_days

COMPANY = "Eiffele gaming"

REQUIRED_ROW_KEYS = {
    "customer", "customer_name",
    "current", "days_1_30", "days_31_60", "days_61_90", "days_90_plus",
    "total",
}


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _aging_bucket_for(overdue_days: int) -> str:
    if overdue_days <= 0:
        return "current"
    elif overdue_days <= 30:
        return "days_1_30"
    elif overdue_days <= 60:
        return "days_31_60"
    elif overdue_days <= 90:
        return "days_61_90"
    else:
        return "days_90_plus"


def run():
    print("\n=== AR Aging Report L1 Test ===")

    import importlib
    import zoho_books_clone.db.queries as q_mod
    import zoho_books_clone.api.dashboard as dash_mod
    importlib.reload(q_mod)
    importlib.reload(dash_mod)

    from zoho_books_clone.db.queries import (
        get_ar_aging,
        get_outstanding_invoices,
    )
    from zoho_books_clone.api.dashboard import _get_aging_buckets

    t = today()

    # ── T1: get_ar_aging returns a list ──────────────────────────────────────
    print("\n--- T1: get_ar_aging(company, today) → list ---")
    aging = None
    try:
        aging = get_ar_aging(COMPANY, t)
        if isinstance(aging, list):
            _pass(f"Returns list of {len(aging)} customer rows")
        else:
            _fail("Non-list result", type(aging).__name__)
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    if aging is None:
        print("  ABORT: get_ar_aging failed")
        return

    # ── T2: required keys on each row ────────────────────────────────────────
    print("\n--- T2: each row has all required keys ---")
    try:
        if aging:
            bad_rows = []
            for row in aging:
                missing = REQUIRED_ROW_KEYS - set(row.keys())
                if missing:
                    bad_rows.append((row.get("customer"), missing))
            if not bad_rows:
                _pass(f"All {len(aging)} rows have required keys")
            else:
                for cust, miss in bad_rows[:3]:
                    _fail(f"Missing keys for {cust}", str(miss))
        else:
            _pass("No aging rows (no outstanding invoices for company)")
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: total = sum of all buckets per customer ───────────────────────────
    print("\n--- T3: total == sum of 5 buckets for each customer ---")
    try:
        mismatched = []
        for row in aging:
            computed = (
                flt(row.get("current"))    +
                flt(row.get("days_1_30"))  +
                flt(row.get("days_31_60")) +
                flt(row.get("days_61_90")) +
                flt(row.get("days_90_plus"))
            )
            reported = flt(row.get("total"))
            if abs(computed - reported) > 0.01:
                mismatched.append((row["customer"], computed, reported))
        if not mismatched:
            _pass(f"Bucket sums == total for all {len(aging)} customers")
        else:
            for cust, comp, rep in mismatched[:3]:
                _fail(f"Bucket sum mismatch for {cust}", f"sum={comp:.2f}, total={rep:.2f}")
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: sum of all customer totals == total SI outstanding ────────────────
    print("\n--- T4: sum of customer totals == tabSales Invoice total outstanding ---")
    try:
        aging_total = sum(flt(r.get("total")) for r in aging)

        db_total = frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0) AS total
            FROM `tabSales Invoice`
            WHERE company = %(co)s AND docstatus = 1 AND outstanding_amount > 0
        """, {"co": COMPANY}, as_dict=True)
        db_total = flt(db_total[0].total) if db_total else 0.0

        if abs(aging_total - db_total) < 0.01:
            _pass(f"AR aging total ({aging_total:.2f}) == DB total ({db_total:.2f})")
        else:
            _fail("Totals mismatch", f"aging={aging_total:.2f}, db={db_total:.2f}")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: bucket assignment is correct (verify each invoice) ───────────────
    print("\n--- T5: each invoice lands in the correct bucket ---")
    try:
        raw_invoices = frappe.db.sql("""
            SELECT customer, outstanding_amount, due_date,
                   DATEDIFF(%(today)s, due_date) AS overdue_days
            FROM `tabSales Invoice`
            WHERE company = %(co)s AND docstatus = 1 AND outstanding_amount > 0
        """, {"today": t, "co": COMPANY}, as_dict=True)

        # Build expected buckets per customer from raw invoice data
        expected: dict = {}
        for inv in raw_invoices:
            cust = inv.customer
            if cust not in expected:
                expected[cust] = {k: 0.0 for k in REQUIRED_ROW_KEYS if k not in ("customer", "customer_name")}
            bucket = _aging_bucket_for(inv.overdue_days or 0)
            expected[cust][bucket] += flt(inv.outstanding_amount)
            expected[cust]["total"] += flt(inv.outstanding_amount)

        # Compare against get_ar_aging output
        aging_by_cust = {r["customer"]: r for r in aging}
        errors = []
        for cust, exp in expected.items():
            got = aging_by_cust.get(cust, {})
            for bucket in ("current", "days_1_30", "days_31_60", "days_61_90", "days_90_plus", "total"):
                if abs(flt(exp.get(bucket)) - flt(got.get(bucket))) > 0.01:
                    errors.append(f"{cust}.{bucket}: expected={exp[bucket]:.2f}, got={got.get(bucket, 0):.2f}")

        if not errors:
            _pass(f"All bucket assignments correct across {len(raw_invoices)} invoices")
        else:
            for err in errors[:5]:
                _fail("Bucket mismatch", err)
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: current bucket only has invoices with due_date >= as_of_date ─────
    print("\n--- T6: current bucket only has not-yet-overdue invoices ---")
    try:
        current_total_from_aging = sum(flt(r.get("current")) for r in aging)
        current_total_from_db = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0) AS total
            FROM `tabSales Invoice`
            WHERE company = %(co)s AND docstatus = 1 AND outstanding_amount > 0
              AND DATEDIFF(%(today)s, due_date) <= 0
        """, {"today": t, "co": COMPANY}, as_dict=True)[0].total)

        if abs(current_total_from_aging - current_total_from_db) < 0.01:
            _pass(f"current bucket total matches DB ({current_total_from_db:.2f})")
        else:
            _fail("current bucket mismatch",
                  f"aging={current_total_from_aging:.2f}, db={current_total_from_db:.2f}")
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: docstatus=0 and docstatus=2 invoices excluded ────────────────────
    print("\n--- T7: draft and cancelled invoices excluded from aging ---")
    try:
        # Count of non-submitted outstanding invoices
        draft_cancelled = frappe.db.sql("""
            SELECT COUNT(*) AS cnt FROM `tabSales Invoice`
            WHERE company = %(co)s AND docstatus != 1 AND outstanding_amount > 0
        """, {"co": COMPANY}, as_dict=True)
        non_submitted = draft_cancelled[0].cnt if draft_cancelled else 0

        # Verify aging only contains submitted invoice data (indirect: total matches docstatus=1 sum)
        aging_total = sum(flt(r.get("total")) for r in aging)
        submitted_total = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(outstanding_amount), 0) AS total
            FROM `tabSales Invoice`
            WHERE company = %(co)s AND docstatus = 1 AND outstanding_amount > 0
        """, {"co": COMPANY}, as_dict=True)[0].total)

        if abs(aging_total - submitted_total) < 0.01:
            _pass(f"Aging total matches submitted-only total ({submitted_total:.2f}); "
                  f"{non_submitted} non-submitted invoices correctly excluded")
        else:
            _fail("Aging includes non-submitted invoices",
                  f"aging={aging_total:.2f}, submitted_only={submitted_total:.2f}")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: _get_aging_buckets aggregate matches sum of customer buckets ──────
    print("\n--- T8: _get_aging_buckets aggregate == sum of customer-level buckets ---")
    try:
        agg = _get_aging_buckets(COMPANY, t)
        bucket_map = {
            "current":    "current",
            "1_30":       "days_1_30",
            "31_60":      "days_31_60",
            "61_90":      "days_61_90",
            "over_90":    "days_90_plus",
        }
        errors = []
        for agg_key, cust_key in bucket_map.items():
            agg_val  = flt(agg.get(agg_key))
            cust_sum = sum(flt(r.get(cust_key)) for r in aging)
            if abs(agg_val - cust_sum) > 0.01:
                errors.append(f"{agg_key}: agg={agg_val:.2f}, cust_sum={cust_sum:.2f}")

        if not errors:
            _pass("Aggregate buckets == sum of customer buckets for all 5 ranges")
        else:
            for err in errors:
                _fail("Aggregate/customer mismatch", err)
    except Exception as e:
        _fail("T8 crashed", str(e)[:120])

    # ── T9: empty/non-existent company returns empty list ────────────────────
    print("\n--- T9: non-existent company returns empty list ---")
    try:
        empty = get_ar_aging("NONEXISTENT CO", t)
        if isinstance(empty, list) and len(empty) == 0:
            _pass("Empty list for unknown company")
        else:
            _fail("Non-empty result for unknown company", str(empty[:2]))
    except Exception as e:
        _fail("T9 crashed", str(e)[:120])

    # ── T10: get_outstanding_invoices matches aging total for a customer ──────
    print("\n--- T10: get_outstanding_invoices consistent with aging total for a customer ---")
    try:
        if aging:
            test_customer = aging[0]["customer"]
            outstanding_list = get_outstanding_invoices("Customer", test_customer, company=COMPANY)
            oi_total = sum(flt(inv.get("outstanding_amount")) for inv in outstanding_list)
            aging_total = flt(next(r for r in aging if r["customer"] == test_customer)["total"])

            if abs(oi_total - aging_total) < 0.01:
                _pass(f"get_outstanding_invoices total ({oi_total:.2f}) == aging total ({aging_total:.2f}) "
                      f"for {test_customer}")
            else:
                _fail("Outstanding invoices total mismatch",
                      f"oi={oi_total:.2f}, aging={aging_total:.2f}")

            # All returned invoices should have outstanding_amount > 0
            zero_out = [i for i in outstanding_list if flt(i.get("outstanding_amount")) <= 0]
            if not zero_out:
                _pass("All returned invoices have outstanding_amount > 0")
            else:
                _fail("Invoice with outstanding_amount <= 0 included", str(zero_out[0]))
        else:
            _pass("Skipped (no outstanding invoices in DB)")
    except Exception as e:
        _fail("T10 crashed", str(e)[:120])

    # ── T11: older as_of_date shifts invoices toward more-overdue buckets ────
    print("\n--- T11: older as_of_date shifts balances toward higher-overdue buckets ---")
    try:
        aging_today = get_ar_aging(COMPANY, t)
        aging_old   = get_ar_aging(COMPANY, add_days(t, 60))   # 60 days in the future → everything looks 60 days older

        # total should be the same (same invoices)
        total_today = sum(flt(r.get("total")) for r in aging_today)
        total_old   = sum(flt(r.get("total")) for r in aging_old)
        if abs(total_today - total_old) < 0.01:
            _pass(f"Total outstanding unchanged across as_of_date shift ({total_today:.2f})")
        else:
            _fail("Total outstanding changed with as_of_date shift",
                  f"today={total_today:.2f}, +60d={total_old:.2f}")

        # current bucket should be <= with older date (some move to overdue)
        current_today = sum(flt(r.get("current")) for r in aging_today)
        current_old   = sum(flt(r.get("current")) for r in aging_old)
        if current_old <= current_today + 0.01:
            _pass(f"current bucket shrinks/stays with older as_of (today={current_today:.2f}, +60d={current_old:.2f})")
        else:
            _fail("current bucket grew with older as_of_date (unexpected)",
                  f"today={current_today:.2f}, +60d={current_old:.2f}")
    except Exception as e:
        _fail("T11 crashed", str(e)[:120])

    # ── T12: all bucket values >= 0 ──────────────────────────────────────────
    print("\n--- T12: all aging bucket values >= 0 ---")
    try:
        bucket_keys = ("current", "days_1_30", "days_31_60", "days_61_90", "days_90_plus", "total")
        neg_found = []
        for row in aging:
            for k in bucket_keys:
                if flt(row.get(k)) < 0:
                    neg_found.append(f"{row['customer']}.{k}={row.get(k)}")
        if not neg_found:
            _pass("All aging values >= 0")
        else:
            for n in neg_found[:3]:
                _fail("Negative bucket value", n)
    except Exception as e:
        _fail("T12 crashed", str(e)[:120])

    print("\n=== DONE ===")
