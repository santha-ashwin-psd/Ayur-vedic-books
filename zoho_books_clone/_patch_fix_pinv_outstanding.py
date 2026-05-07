"""
Fix PINV-2026-00005.outstanding_amount to reflect the debit note PINV-2026-00006.
The debit note (is_return=1, grand_total=500) reduced the payable by 500, but
recompute_outstanding_from_gl only counts Payment Entry references (not debit notes),
so the outstanding was never decremented.

Correct value: 2000 - 500 (debit note) = 1500.
"""
import frappe
from zoho_books_clone.accounts.doctype.general_ledger_entry.general_ledger_entry import (
    recompute_outstanding_from_gl,
)

def run():
    # Verify current state
    curr = frappe.db.get_value("Purchase Invoice", "PINV-2026-00005", "outstanding_amount")
    print(f"PINV-2026-00005 outstanding_amount before: {curr}")

    # Correct value based on GL: 2000 (PINV CR) - 500 (debit note DR) = 1500
    frappe.db.set_value("Purchase Invoice", "PINV-2026-00005", "outstanding_amount", 1500,
                        update_modified=False)
    frappe.db.commit()

    curr = frappe.db.get_value("Purchase Invoice", "PINV-2026-00005", "outstanding_amount")
    print(f"PINV-2026-00005 outstanding_amount after:  {curr}")
    print("Done.")
