"""
Corrective patch: un-cancel GL entries that were incorrectly reversed by
_patch_reverse_ghost_gl.py for:
  1. Bank Account opening balance entries (master records, not submittable docs)
  2. Bank Transaction GL entries where the transaction is still submitted (docstatus=1)

Run once with:
  bench --site site1.local execute zoho_books_clone._patch_restore_bank_gl.run
"""
import frappe
from zoho_books_clone.accounts.doctype.general_ledger_entry.general_ledger_entry import (
    _update_account_balance,
)


def run():
    affected_accounts = set()

    # 1. Restore Bank Account opening balance GL entries (always legitimate)
    ba_originals = frappe.db.sql("""
        SELECT name, account FROM `tabGeneral Ledger Entry`
        WHERE voucher_type = 'Bank Account'
          AND is_cancelled = 1
          AND is_reversal  = 0
    """, as_dict=True)
    print(f"Bank Account original entries to restore: {len(ba_originals)}")
    for r in ba_originals:
        frappe.db.set_value("General Ledger Entry", r.name, "is_cancelled", 0,
                            update_modified=False)
        affected_accounts.add(r.account)
        print(f"  Restored: {r.name} ({r.account})")

    # 2. Restore Bank Transaction GL entries for still-submitted transactions
    submitted_btxns = frappe.db.sql("""
        SELECT name FROM `tabBank Transaction` WHERE docstatus = 1
    """, as_dict=True)
    submitted_names = [r.name for r in submitted_btxns]

    if submitted_names:
        placeholders = ", ".join(["%s"] * len(submitted_names))
        bt_originals = frappe.db.sql(f"""
            SELECT name, account FROM `tabGeneral Ledger Entry`
            WHERE voucher_type = 'Bank Transaction'
              AND voucher_no IN ({placeholders})
              AND is_cancelled = 1
              AND is_reversal  = 0
        """, submitted_names, as_dict=True)
        print(f"\nBank Transaction original entries to restore: {len(bt_originals)}")
        for r in bt_originals:
            frappe.db.set_value("General Ledger Entry", r.name, "is_cancelled", 0,
                                update_modified=False)
            affected_accounts.add(r.account)
            print(f"  Restored: {r.name} ({r.account})")

    # Refresh balances
    print(f"\nRefreshing {len(affected_accounts)} account balance(s)...")
    for acct in affected_accounts:
        _update_account_balance(acct)

    frappe.db.commit()
    print("Done.")
