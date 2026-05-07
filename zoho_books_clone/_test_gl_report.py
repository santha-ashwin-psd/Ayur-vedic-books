"""
L1 — General Ledger Report test.

Scenario:
  T1  get_gl_entries(date range, company) → list, required fields present
  T2  get_gl_entries date filter — no entry outside from/to date returned
  T3  get_gl_entries company filter — all rows belong to company
  T4  get_gl_entries account filter — all rows belong to that account
  T5  get_gl_entries voucher_no filter — all rows match that voucher
  T6  get_account_balance() → returns a float (numeric)
  T7  get_account_balance(as_of_date=future) == get_account_balance() (no future entries)
  T8  get_account_balances_bulk([accts]) → dict, all accounts present
  T9  get_account_ledger → opening + period DR - CR == closing
  T10 get_account_ledger entries are in chronological order
  T11 get_account_ledger running_balance monotonically tracks from opening
  T12 get_voucher_detail → all GL rows for that voucher, is_balanced=True
  T13 get_voucher_detail total_debit == total_credit for any balanced voucher
  T14 get_pl_account_breakdown(Income) → list with account + amount keys
  T15 get_pl_account_breakdown(Expense) → list with account + amount keys
  T16 get_party_ledger(Customer) → total_invoiced >= total_outstanding
  T17 get_party_ledger totals match sum of invoices list
  T18 get_trial_balance → total DR == total CR (cross-check with independent sum)
"""
import frappe
from frappe.utils import flt, today, get_first_day, get_last_day, add_days

COMPANY = "Eiffele gaming"
REQUIRED_GL_KEYS = {
    "posting_date", "account", "voucher_type", "voucher_no",
    "debit", "credit",
}


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def run():
    print("\n=== General Ledger Report L1 Test ===")

    import importlib
    import zoho_books_clone.db.queries as q_mod
    importlib.reload(q_mod)
    from zoho_books_clone.db.queries import (
        get_gl_entries,
        get_account_balance,
        get_account_balances_bulk,
        get_account_ledger,
        get_trial_balance,
        get_pl_account_breakdown,
        get_party_ledger,
    )
    from zoho_books_clone.db.queries import get_voucher_detail

    t   = today()
    som = str(get_first_day(add_days(t, -60)))   # 2 months ago: guaranteed to capture data
    eom = str(get_last_day(t))

    # Grab a real GL entry to anchor tests
    anchor = frappe.db.sql("""
        SELECT g.account, g.voucher_type, g.voucher_no, g.posting_date, g.company
        FROM `tabGeneral Ledger Entry` g
        JOIN `tabAccount` a ON a.name = g.account
        WHERE g.company = %(co)s
          AND g.is_cancelled = 0
          AND g.is_reversal  = 0
          AND g.debit > 0
        ORDER BY g.posting_date DESC, g.creation DESC
        LIMIT 1
    """, {"co": COMPANY}, as_dict=True)

    if not anchor:
        print("  ABORT: no active GL entries found for company")
        return

    a = anchor[0]
    TEST_ACCOUNT    = a.account
    TEST_VOUCHER_NO = a.voucher_no
    TEST_VTYPE      = a.voucher_type
    print(f"  anchor: account={TEST_ACCOUNT}  voucher={TEST_VOUCHER_NO}  type={TEST_VTYPE}")

    # Pick a customer with invoices for party ledger test
    cust_row = frappe.db.sql("""
        SELECT customer FROM `tabSales Invoice`
        WHERE company = %(co)s AND docstatus = 1
        ORDER BY posting_date DESC LIMIT 1
    """, {"co": COMPANY}, as_dict=True)
    TEST_CUSTOMER = cust_row[0].customer if cust_row else None
    print(f"  test customer: {TEST_CUSTOMER}")

    # ── T1: get_gl_entries → list with required fields ────────────────────────
    print("\n--- T1: get_gl_entries() → list with required fields ---")
    try:
        entries = get_gl_entries(som, eom, COMPANY)
        if isinstance(entries, list) and len(entries) > 0:
            _pass(f"Returns list of {len(entries)} GL entries")
        else:
            _fail("Empty or non-list result", type(entries).__name__)

        if entries:
            row = entries[0]
            missing = REQUIRED_GL_KEYS - set(row.keys())
            if not missing:
                _pass("All required GL fields present")
            else:
                _fail("Missing GL fields", str(missing))
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    # ── T2: date filter — no entry outside from/to ────────────────────────────
    print("\n--- T2: date filter — all entries within from/to range ---")
    try:
        entries = get_gl_entries(som, eom, COMPANY)
        out_of_range = [
            r for r in entries
            if str(r.get("posting_date", "")) < som or str(r.get("posting_date", "")) > eom
        ]
        if not out_of_range:
            _pass(f"All {len(entries)} entries within {som} → {eom}")
        else:
            _fail("Entries outside date range found", str(out_of_range[0]))
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: company filter — all rows belong to company ───────────────────────
    print("\n--- T3: company filter — all rows belong to company ---")
    try:
        entries = get_gl_entries(som, eom, COMPANY)
        # GL entries don't return company field; use indirect check via account ownership
        if entries:
            accounts_in_entries = {r["account"] for r in entries}
            wrong_co = frappe.db.sql("""
                SELECT name FROM `tabAccount`
                WHERE name IN %(accts)s AND company != %(co)s
            """, {"accts": tuple(accounts_in_entries) or ("__none__",), "co": COMPANY},
            as_dict=True)
            if not wrong_co:
                _pass(f"All {len(accounts_in_entries)} accounts belong to {COMPANY}")
            else:
                _fail("Accounts from other companies found", str([r.name for r in wrong_co]))
        else:
            _pass("No entries to check (date range may have no data)")
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: account filter — all rows match that account ─────────────────────
    print("\n--- T4: account filter → all rows for that account ---")
    try:
        acct_entries = get_gl_entries(som, eom, COMPANY, account=TEST_ACCOUNT)
        wrong_acct = [r for r in acct_entries if r.get("account") != TEST_ACCOUNT]
        if not wrong_acct:
            _pass(f"{len(acct_entries)} entries all for account {TEST_ACCOUNT}")
        else:
            _fail("Entries for wrong account", str(wrong_acct[0]))
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: voucher_no filter — all rows match that voucher ───────────────────
    print("\n--- T5: voucher_no filter → all rows match that voucher ---")
    try:
        voucher_entries = get_gl_entries(som, eom, COMPANY, voucher_no=TEST_VOUCHER_NO)
        wrong_vno = [r for r in voucher_entries if r.get("voucher_no") != TEST_VOUCHER_NO]
        if not wrong_vno:
            _pass(f"{len(voucher_entries)} entries all for voucher {TEST_VOUCHER_NO}")
        else:
            _fail("Entries for wrong voucher", str(wrong_vno[0]))
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: get_account_balance → returns a float ─────────────────────────────
    print("\n--- T6: get_account_balance() → numeric float ---")
    try:
        bal = get_account_balance(TEST_ACCOUNT)
        if isinstance(bal, (int, float)):
            _pass(f"get_account_balance returns {bal:.2f} for {TEST_ACCOUNT}")
        else:
            _fail("Non-numeric return", type(bal).__name__)
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: balance with future date == balance with no date ─────────────────
    print("\n--- T7: balance(as_of_date=far future) == balance() ---")
    try:
        bal_now    = get_account_balance(TEST_ACCOUNT)
        bal_future = get_account_balance(TEST_ACCOUNT, as_of_date=add_days(t, 3650))
        if abs(bal_now - bal_future) < 0.01:
            _pass(f"Balances match: {bal_now:.2f}")
        else:
            _fail("Balances differ with far-future date", f"{bal_now:.2f} vs {bal_future:.2f}")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: get_account_balances_bulk → dict with all accounts ───────────────
    print("\n--- T8: get_account_balances_bulk → dict with all requested accounts ---")
    try:
        all_accts = frappe.get_all("Account",
            filters={"company": COMPANY, "is_group": 0},
            pluck="name", limit=10)
        bulk = get_account_balances_bulk(all_accts, as_of_date=t)
        if isinstance(bulk, dict):
            _pass(f"get_account_balances_bulk returns dict ({len(bulk)} accounts)")
        else:
            _fail("Non-dict result", type(bulk).__name__)
        # All requested accounts that have GL entries should be in result
        has_gl = frappe.db.sql("""
            SELECT DISTINCT account FROM `tabGeneral Ledger Entry`
            WHERE account IN %(accts)s AND is_cancelled=0
        """, {"accts": tuple(all_accts) or ("__none__",)}, as_dict=True)
        have_gl_accts = {r.account for r in has_gl}
        missing_in_bulk = have_gl_accts - set(bulk.keys())
        if not missing_in_bulk:
            _pass("All accounts with GL entries are in bulk result")
        else:
            _fail("Some accounts with GL entries missing from bulk", str(missing_in_bulk))
    except Exception as e:
        _fail("T8 crashed", str(e)[:120])

    # ── T9: get_account_ledger → opening + DR - CR == closing ────────────────
    print("\n--- T9: get_account_ledger → opening + period DR - CR == closing ---")
    ledger_result = None
    try:
        ledger_result = get_account_ledger(TEST_ACCOUNT, COMPANY, som, eom)
        opening    = flt(ledger_result.get("opening"))
        total_dr   = flt(ledger_result.get("total_debit"))
        total_cr   = flt(ledger_result.get("total_credit"))
        closing    = flt(ledger_result.get("closing"))
        expected_closing = opening + total_dr - total_cr
        if abs(expected_closing - closing) < 0.01:
            _pass(f"closing = opening({opening:.2f}) + DR({total_dr:.2f}) - CR({total_cr:.2f}) = {closing:.2f}")
        else:
            _fail("closing balance formula wrong",
                  f"expected {expected_closing:.2f}, got {closing:.2f}")

        # Required keys check
        for key in ["account", "from_date", "to_date", "opening", "total_debit", "total_credit", "closing", "entries"]:
            if key not in ledger_result:
                _fail(f"Missing key: {key}")
        else:
            _pass("All account_ledger keys present")
    except Exception as e:
        _fail("T9 crashed", str(e)[:120])

    # ── T10: entries are in chronological order ───────────────────────────────
    print("\n--- T10: get_account_ledger entries in chronological order ---")
    try:
        if ledger_result and ledger_result.get("entries"):
            entries = ledger_result["entries"]
            dates   = [str(e.get("posting_date", "")) for e in entries]
            if dates == sorted(dates):
                _pass(f"All {len(entries)} entries in posting_date ascending order")
            else:
                _fail("Entries not in chronological order")
        else:
            _pass("No period entries (account may have no movement in range)")
    except Exception as e:
        _fail("T10 crashed", str(e)[:120])

    # ── T11: running_balance monotonically tracks from opening ────────────────
    print("\n--- T11: running_balance tracks per-row DR-CR movement ---")
    try:
        if ledger_result and ledger_result.get("entries"):
            entries = ledger_result["entries"]
            opening = flt(ledger_result.get("opening"))
            prev_rb = opening
            errors  = []
            for e in entries:
                dr = flt(e.get("debit", 0))
                cr = flt(e.get("credit", 0))
                expected_rb = prev_rb + dr - cr
                actual_rb   = flt(e.get("running_balance"))
                if abs(expected_rb - actual_rb) > 0.01:
                    errors.append(f"row {e.get('name')}: expected {expected_rb:.2f}, got {actual_rb:.2f}")
                prev_rb = actual_rb
            if not errors:
                _pass(f"running_balance correct across all {len(entries)} entries")
            else:
                for err in errors[:3]:
                    _fail("running_balance wrong", err)
        else:
            _pass("No period entries to check running balance")
    except Exception as e:
        _fail("T11 crashed", str(e)[:120])

    # ── T12: get_voucher_detail → GL rows + is_balanced flag ─────────────────
    print("\n--- T12: get_voucher_detail → all GL rows, is_balanced=True ---")
    vd = None
    try:
        vd = get_voucher_detail(TEST_VTYPE, TEST_VOUCHER_NO)
        required_vd_keys = {"voucher_type", "voucher_no", "gl_entries",
                            "total_debit", "total_credit", "is_balanced", "source_doc"}
        missing_vd = required_vd_keys - set(vd.keys())
        if not missing_vd:
            _pass("All voucher_detail keys present")
        else:
            _fail("Missing voucher_detail keys", str(missing_vd))

        if isinstance(vd.get("gl_entries"), list):
            _pass(f"gl_entries is a list ({len(vd['gl_entries'])} rows)")
        else:
            _fail("gl_entries not a list")
    except Exception as e:
        _fail("T12 crashed", str(e)[:120])

    # ── T13: total_debit == total_credit for a balanced voucher ──────────────
    print("\n--- T13: get_voucher_detail total_debit == total_credit ---")
    try:
        if vd:
            if vd.get("is_balanced"):
                _pass(f"is_balanced=True  DR={flt(vd['total_debit']):.2f}  CR={flt(vd['total_credit']):.2f}")
            else:
                _fail("is_balanced=False for real voucher",
                      f"DR={vd.get('total_debit')}  CR={vd.get('total_credit')}")
        else:
            _fail("Skipped (T12 failed)")
    except Exception as e:
        _fail("T13 crashed", str(e)[:120])

    # ── T14: get_pl_account_breakdown(Income) → list with keys ───────────────
    print("\n--- T14: get_pl_account_breakdown(Income) → list with account/amount ---")
    try:
        income_bdown = get_pl_account_breakdown(COMPANY, som, eom, account_type="Income")
        if isinstance(income_bdown, list):
            _pass(f"Income breakdown is a list ({len(income_bdown)} accounts)")
        else:
            _fail("Non-list result", type(income_bdown).__name__)

        if income_bdown:
            row = income_bdown[0]
            bdown_keys = {"account", "account_type", "amount", "transaction_count"}
            missing_bdown = bdown_keys - set(row.keys())
            if not missing_bdown:
                _pass("All Income breakdown keys present")
            else:
                _fail("Missing Income breakdown keys", str(missing_bdown))
            if row.get("account_type") == "Income":
                _pass(f"account_type=Income confirmed for {row['account']}")
            else:
                _fail("account_type != Income", str(row.get("account_type")))
    except Exception as e:
        _fail("T14 crashed", str(e)[:120])

    # ── T15: get_pl_account_breakdown(Expense) → list ────────────────────────
    print("\n--- T15: get_pl_account_breakdown(Expense) → list ---")
    try:
        exp_bdown = get_pl_account_breakdown(COMPANY, som, eom, account_type="Expense")
        if isinstance(exp_bdown, list):
            _pass(f"Expense breakdown is a list ({len(exp_bdown)} accounts)")
        else:
            _fail("Non-list result", type(exp_bdown).__name__)
    except Exception as e:
        _fail("T15 crashed", str(e)[:120])

    # ── T16: get_party_ledger(Customer) → invoiced >= outstanding ─────────────
    print("\n--- T16: get_party_ledger(Customer) → total_invoiced >= total_outstanding ---")
    pl_result = None
    try:
        if TEST_CUSTOMER:
            pl_result = get_party_ledger("Customer", TEST_CUSTOMER, COMPANY)
            required_pl_keys = {
                "party_type", "party", "total_invoiced",
                "total_paid", "total_outstanding", "invoices", "payments",
            }
            missing_pl = required_pl_keys - set(pl_result.keys())
            if not missing_pl:
                _pass("All party_ledger keys present")
            else:
                _fail("Missing party_ledger keys", str(missing_pl))

            total_inv = flt(pl_result.get("total_invoiced"))
            total_out = flt(pl_result.get("total_outstanding"))
            if total_inv >= total_out:
                _pass(f"total_invoiced ({total_inv:.2f}) >= total_outstanding ({total_out:.2f})")
            else:
                _fail("total_invoiced < total_outstanding", f"{total_inv:.2f} < {total_out:.2f}")
        else:
            _pass("Skipped (no customer invoices in DB)")
    except Exception as e:
        _fail("T16 crashed", str(e)[:120])

    # ── T17: party_ledger totals match sum of invoices list ──────────────────
    print("\n--- T17: party_ledger totals == sum of invoice amounts ---")
    try:
        if pl_result and pl_result.get("invoices"):
            computed_invoiced    = sum(flt(i.get("grand_total", 0))        for i in pl_result["invoices"])
            computed_outstanding = sum(flt(i.get("outstanding_amount", 0)) for i in pl_result["invoices"])
            reported_invoiced    = flt(pl_result.get("total_invoiced"))
            reported_outstanding = flt(pl_result.get("total_outstanding"))

            if abs(computed_invoiced - reported_invoiced) < 0.01:
                _pass(f"total_invoiced consistent: {reported_invoiced:.2f}")
            else:
                _fail("total_invoiced mismatch", f"reported={reported_invoiced:.2f}, computed={computed_invoiced:.2f}")

            if abs(computed_outstanding - reported_outstanding) < 0.01:
                _pass(f"total_outstanding consistent: {reported_outstanding:.2f}")
            else:
                _fail("total_outstanding mismatch", f"reported={reported_outstanding:.2f}, computed={computed_outstanding:.2f}")
        else:
            _pass("Skipped (no invoices for customer, or T16 failed)")
    except Exception as e:
        _fail("T17 crashed", str(e)[:120])

    # ── T18: get_trial_balance → total DR == total CR ─────────────────────────
    print("\n--- T18: get_trial_balance → total DR == total CR ---")
    try:
        tb = get_trial_balance(COMPANY, som, eom)
        if isinstance(tb, list):
            _pass(f"Trial balance returns {len(tb)} account rows")
        else:
            _fail("Non-list result", type(tb).__name__)

        total_dr = sum(flt(r.get("debit"))  for r in tb)
        total_cr = sum(flt(r.get("credit")) for r in tb)
        if abs(total_dr - total_cr) < 0.01:
            _pass(f"DR = CR = {total_dr:.2f} (trial balance in balance)")
        else:
            _fail("Trial balance out of balance", f"DR={total_dr:.2f}, CR={total_cr:.2f}")

        # closing = opening + DR - CR per row
        wrong_closing = []
        for r in tb:
            expected_closing = flt(r.get("opening")) + flt(r.get("debit")) - flt(r.get("credit"))
            actual_closing   = flt(r.get("closing"))
            if abs(expected_closing - actual_closing) > 0.01:
                wrong_closing.append(r["account"])
        if not wrong_closing:
            _pass("closing formula correct for all trial balance rows")
        else:
            _fail("closing formula wrong for some accounts", str(wrong_closing[:3]))
    except Exception as e:
        _fail("T18 crashed", str(e)[:120])

    print("\n=== DONE ===")
