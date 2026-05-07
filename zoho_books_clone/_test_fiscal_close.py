"""
L1 — Fiscal Year Close test.

Scenario:
  T1  Create an isolated TEST-2025 fiscal year
  T2  Post income (10 000) + expense (3 000) GL entries dated within it
  T3  close_fiscal_year() → JE created, net_profit=7000, RE balance updated, is_closed=1
  T4  Double-close is blocked
  T5  New JE dated inside closed period is rejected by central_validator
  T6  reopen_fiscal_year() → is_closed=0, same JE insert now passes validate
  T7  Cleanup
"""
import frappe
from frappe.utils import flt
from zoho_books_clone.accounts.doctype.general_ledger_entry.general_ledger_entry import make_gl_entries
from zoho_books_clone.accounts.fiscal_close import close_fiscal_year, reopen_fiscal_year

COMPANY   = "Eiffele gaming"
TEST_YEAR = "TEST-2020"          # 2020 has no existing FY — safe for isolated test
COMPANY_  = "Eiffele gaming"     # local alias to avoid collision with module-level
TEST_FY   = f"{TEST_YEAR}-{COMPANY_}"   # autoname: {year}-{company}
START     = "2020-01-01"
END       = "2020-12-31"
MID       = "2020-06-01"        # posting date for test GL entries


def _gl_bal(account):
    if not account:
        return 0.0
    r = frappe.db.sql(
        "SELECT COALESCE(SUM(debit)-SUM(credit),0) AS b FROM `tabGeneral Ledger Entry` "
        "WHERE account=%s AND IFNULL(is_cancelled,0)=0",
        account, as_dict=True,
    )
    return flt(r[0].b) if r else 0.0


def _gl_count(voucher_no):
    r = frappe.db.sql(
        "SELECT COUNT(*) AS n FROM `tabGeneral Ledger Entry` "
        "WHERE voucher_no=%s AND IFNULL(is_cancelled,0)=0",
        voucher_no, as_dict=True,
    )
    return r[0].n if r else 0


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def run():
    print("\n=== Fiscal Year Close L1 Test ===")

    ar_acct  = frappe.db.get_value("Account", {"account_type": "Receivable", "company": COMPANY, "is_group": 0}, "name")
    inc_acct = frappe.db.get_value("Account", {"account_type": "Income",     "company": COMPANY, "is_group": 0}, "name")
    exp_acct = frappe.db.get_value("Account", {"account_type": "Expense",    "company": COMPANY, "is_group": 0}, "name")
    pay_acct = frappe.db.get_value("Account", {"account_type": "Payable",    "company": COMPANY, "is_group": 0}, "name")
    re_acct  = frappe.db.get_value("Account",
        {"account_type": "Equity", "company": COMPANY, "is_group": 0, "account_name": ["like", "%Retained%"]},
        "name",
    ) or frappe.db.get_value("Account", {"account_type": "Equity", "company": COMPANY, "is_group": 0}, "name")

    print(f"  AR={ar_acct}  Inc={inc_acct}  Exp={exp_acct}  Pay={pay_acct}  RE={re_acct}")
    if not all([ar_acct, inc_acct, exp_acct, pay_acct, re_acct]):
        print("  ABORT: one or more required accounts missing")
        return

    # ── T1: Create test Fiscal Year ───────────────────────────────────────────
    print("\n--- T1: Create test Fiscal Year ---")
    # Clean any overlapping FY from prior runs
    overlapping = frappe.db.sql("""
        SELECT name FROM `tabFiscal Year`
        WHERE year_start_date <= %s AND year_end_date >= %s
    """, (END, START), as_dict=True)
    for r in overlapping:
        frappe.db.delete("Fiscal Year", r.name)
    frappe.db.commit()

    fy = frappe.get_doc({
        "doctype":         "Fiscal Year",
        "year":            TEST_YEAR,
        "year_start_date": START,
        "year_end_date":   END,
        "company":         COMPANY,
        "is_closed":       0,
    })
    fy.flags.ignore_permissions = True
    fy.insert()
    frappe.db.commit()
    actual_fy = fy.name   # Frappe autoname; use this for all downstream calls

    if frappe.db.exists("Fiscal Year", actual_fy):
        _pass(f"Fiscal Year created: {actual_fy}")
    else:
        _fail("Fiscal Year creation failed")
        return

    # ── T2: Post Income + Expense GL entries in the test period ───────────────
    print("\n--- T2: Post Income 10000 + Expense 3000 into TEST-2025 ---")
    INCOME_VOUCHER  = "TEST-FY-INC-001"
    EXPENSE_VOUCHER = "TEST-FY-EXP-001"

    # Clean any leftover from a prior run
    frappe.db.sql(
        "UPDATE `tabGeneral Ledger Entry` SET is_cancelled=1 "
        "WHERE voucher_no IN (%s, %s)",
        (INCOME_VOUCHER, EXPENSE_VOUCHER),
    )

    make_gl_entries([
        {"account": ar_acct,  "debit": 10000, "credit": 0,
         "posting_date": MID, "voucher_type": "Sales Invoice",
         "voucher_no": INCOME_VOUCHER, "company": COMPANY, "remarks": "Test income"},
        {"account": inc_acct, "debit": 0, "credit": 10000,
         "posting_date": MID, "voucher_type": "Sales Invoice",
         "voucher_no": INCOME_VOUCHER, "company": COMPANY, "remarks": "Test income"},
    ])
    make_gl_entries([
        {"account": exp_acct, "debit": 3000, "credit": 0,
         "posting_date": MID, "voucher_type": "Purchase Invoice",
         "voucher_no": EXPENSE_VOUCHER, "company": COMPANY, "remarks": "Test expense"},
        {"account": pay_acct, "debit": 0, "credit": 3000,
         "posting_date": MID, "voucher_type": "Purchase Invoice",
         "voucher_no": EXPENSE_VOUCHER, "company": COMPANY, "remarks": "Test expense"},
    ])
    frappe.db.commit()
    _pass("GL entries posted: income voucher + expense voucher")

    # ── T3: Close the fiscal year ──────────────────────────────────────────────
    print("\n--- T3: close_fiscal_year() ---")
    b_re = _gl_bal(re_acct)
    print(f"  RE balance before close (debit-credit): {b_re:.2f}")

    result = close_fiscal_year(actual_fy, retained_earnings_account=re_acct)
    frappe.db.commit()

    print(f"  Result: {result}")
    je_name    = result.get("journal_entry")
    net_profit = flt(result.get("net_profit"))

    if je_name:
        _pass(f"Closing JE created: {je_name}")
    else:
        _fail("No closing JE returned")

    if abs(net_profit - 7000) < 0.01:
        _pass(f"net_profit = {net_profit:.2f} (expect 7000)")
    else:
        _fail("net_profit wrong", f"got {net_profit:.2f}, expect 7000")

    is_closed = flt(frappe.db.get_value("Fiscal Year", actual_fy, "is_closed"))
    if is_closed == 1:
        _pass("Fiscal Year is_closed = 1")
    else:
        _fail("is_closed not set", f"got {is_closed}")

    if je_name:
        gl_rows = _gl_count(je_name)
        if gl_rows == 2:
            _pass("Closing JE has exactly 2 GL rows")
        else:
            _fail("Closing JE GL rows wrong", f"got {gl_rows}, expect 2")

        # RE should be credited 7000 → debit-credit decreases by 7000
        a_re = _gl_bal(re_acct)
        if abs((b_re - a_re) - 7000) < 0.01:
            _pass(f"Retained Earnings credited 7000 (bal {b_re:.0f} → {a_re:.0f})")
        else:
            _fail("Retained Earnings balance wrong",
                  f"Δ={b_re - a_re:.2f}, expect 7000")

    # ── T4: Double-close blocked ───────────────────────────────────────────────
    print("\n--- T4: Double-close must be rejected ---")
    try:
        close_fiscal_year(actual_fy)
        _fail("Double-close accepted (should have thrown)")
    except Exception as e:
        msg = str(e)
        if "already closed" in msg.lower():
            _pass(f"Double-close blocked: {msg[:70]}")
        else:
            _fail("Double-close threw wrong error", msg[:70])

    # ── T5: Period lock — new JE inside closed FY is rejected ─────────────────
    print("\n--- T5: Period lock — JE dated 2025-06-01 must be blocked ---")
    try:
        je_blocked = frappe.get_doc({
            "doctype":      "Journal Entry",
            "posting_date": MID,           # inside TEST-2025
            "company":      COMPANY,
            "accounts": [
                {"account": ar_acct,  "debit": 100, "credit": 0},
                {"account": inc_acct, "debit": 0,   "credit": 100},
            ],
        })
        je_blocked.flags.ignore_permissions = True
        je_blocked.insert()
        _fail("Period-locked JE was accepted (should have been blocked)")
        je_blocked.cancel()
    except Exception as e:
        msg = str(e)
        if "closed" in msg.lower() or "locked" in msg.lower():
            _pass(f"Period lock working: {msg[:80]}")
        else:
            _fail("Blocked but wrong error", msg[:80])

    # ── T6: Reopen + verify lock lifts ────────────────────────────────────────
    print("\n--- T6: reopen_fiscal_year() ---")
    reopen_fiscal_year(actual_fy)
    frappe.db.commit()

    is_closed2 = flt(frappe.db.get_value("Fiscal Year", actual_fy, "is_closed"))
    if is_closed2 == 0:
        _pass("Fiscal Year reopened (is_closed = 0)")
    else:
        _fail("Reopen failed", f"is_closed still {is_closed2}")

    # After reopen the same JE should insert cleanly
    try:
        je_ok = frappe.get_doc({
            "doctype":      "Journal Entry",
            "posting_date": MID,
            "company":      COMPANY,
            "accounts": [
                {"account": ar_acct,  "debit": 100, "credit": 0},
                {"account": inc_acct, "debit": 0,   "credit": 100},
            ],
        })
        je_ok.flags.ignore_permissions = True
        je_ok.insert()
        _pass("JE insert passes after reopen")
        frappe.db.rollback()          # discard — we don't want it in the DB
    except Exception as e:
        _fail("JE insert still blocked after reopen", str(e)[:80])

    # ── T7: Cleanup ───────────────────────────────────────────────────────────
    print("\n--- T7: Cleanup ---")
    # Cancel closing JE GL rows
    if je_name:
        frappe.db.sql(
            "UPDATE `tabGeneral Ledger Entry` SET is_cancelled=1 WHERE voucher_no=%s",
            je_name,
        )
        try:
            frappe.delete_doc("Journal Entry", je_name, force=True, ignore_permissions=True)
        except Exception:
            pass

    # Cancel test GL entries
    frappe.db.sql(
        "UPDATE `tabGeneral Ledger Entry` SET is_cancelled=1 "
        "WHERE voucher_no IN (%s, %s)",
        (INCOME_VOUCHER, EXPENSE_VOUCHER),
    )

    # Delete test FY
    frappe.delete_doc("Fiscal Year", actual_fy, force=True, ignore_permissions=True)
    frappe.db.commit()

    if not frappe.db.exists("Fiscal Year", actual_fy):
        _pass("Test Fiscal Year deleted")
    else:
        _fail("Test Fiscal Year still exists")

    print("\n=== DONE ===")
