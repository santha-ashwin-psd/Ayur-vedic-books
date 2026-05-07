import frappe

def run():
    rows = frappe.db.sql("""
        SELECT name, voucher_type, voucher_no, account, debit, credit,
               is_cancelled, is_reversal, posting_date
        FROM `tabGeneral Ledger Entry`
        WHERE voucher_type IN ('Bank Account', 'Bank Transaction')
        ORDER BY creation
    """, as_dict=True)

    print(f"\nBank Account / Bank Transaction GL entries ({len(rows)} rows):")
    for r in rows:
        print(f"  {r.name[:20]:20} | {r.voucher_type:16} | {r.voucher_no:30} | {r.account:30} | DR={r.debit:8.0f} CR={r.credit:8.0f} | cancelled={r.is_cancelled} reversal={r.is_reversal}")

    # Also check docstatus of Bank Transactions
    btxns = frappe.db.sql("""
        SELECT name, docstatus, status FROM `tabBank Transaction`
        ORDER BY creation
    """, as_dict=True)
    print(f"\nBank Transactions ({len(btxns)} rows):")
    for b in btxns:
        print(f"  {b.name}: docstatus={b.docstatus}, status={b.status}")

    # Check what accounts are now at zero that shouldn't be
    zero_accounts = frappe.db.sql("""
        SELECT name, account_type, balance FROM `tabAccount`
        WHERE company = 'Eiffele gaming'
        ORDER BY account_type, name
    """, as_dict=True)
    print(f"\nAccount balances:")
    for a in zero_accounts:
        print(f"  {a.account_type:20} {a.name:40} balance={a.balance:.2f}")
