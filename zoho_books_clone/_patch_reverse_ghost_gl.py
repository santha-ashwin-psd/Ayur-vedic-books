"""
One-shot patch: reverse ghost GL entries for vouchers that were cancelled
but whose GL entries were never reversed (due to the old idempotency bug).
Run once with:
  bench --site site1.local execute zoho_books_clone._patch_reverse_ghost_gl.run
"""
import frappe
from zoho_books_clone.accounts.doctype.general_ledger_entry.general_ledger_entry import (
    _reverse_gl_entries,
    _update_account_balance,
)


def run():
    # Find all vouchers that are cancelled (docstatus=2) but still have
    # active (is_cancelled=0, is_reversal=0) GL entries — these are "ghosts".
    rows = frappe.db.sql("""
        SELECT DISTINCT gle.voucher_type, gle.voucher_no
        FROM `tabGeneral Ledger Entry` gle
        WHERE gle.is_cancelled = 0
          AND gle.is_reversal  = 0
          AND NOT EXISTS (
            -- exclude vouchers that are still legitimately submitted
            SELECT 1 FROM `tabSales Invoice`   WHERE name = gle.voucher_no AND docstatus = 1
            UNION ALL
            SELECT 1 FROM `tabPurchase Invoice` WHERE name = gle.voucher_no AND docstatus = 1
            UNION ALL
            SELECT 1 FROM `tabPayment Entry`    WHERE name = gle.voucher_no AND docstatus = 1
            UNION ALL
            SELECT 1 FROM `tabJournal Entry`    WHERE name = gle.voucher_no AND docstatus = 1
            UNION ALL
            SELECT 1 FROM `tabStock Entry`      WHERE name = gle.voucher_no AND docstatus = 1
          )
    """, as_dict=True)

    if not rows:
        print("No ghost GL entries found — nothing to do.")
        return

    print(f"Found {len(rows)} voucher(s) with ghost GL entries:")
    all_accounts = set()
    for r in rows:
        print(f"  Reversing: {r.voucher_type} {r.voucher_no}")
        affected = _reverse_gl_entries(r.voucher_type, r.voucher_no)
        all_accounts.update(affected)
        print(f"    → reversed {len(affected)} account(s): {affected}")

    print(f"\nRefreshing balances for {len(all_accounts)} account(s)...")
    for acct in all_accounts:
        _update_account_balance(acct)

    frappe.db.commit()
    print("Done. Ghost GL entries reversed and balances updated.")
