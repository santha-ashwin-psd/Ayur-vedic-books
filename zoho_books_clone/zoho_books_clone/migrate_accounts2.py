import frappe

def run():
    frappe.flags.in_patch = True
    accounts = frappe.get_all("Account", fields=["name", "account_name", "company", "parent_account"])
    
    # First revert the parent_account
    for acc in accounts:
        if acc.parent_account and f" - {acc.company}" in acc.parent_account:
            old_parent = acc.parent_account.replace(f" - {acc.company}", "")
            frappe.db.set_value("Account", acc.name, "parent_account", old_parent)
    frappe.db.commit()

    # Now rename
    for acc in accounts:
        if f" - {acc.company}" in acc.name:
            continue
            
        new_name = f"{acc.account_name} - {acc.company}"
        print(f"Renaming {acc.name} to {new_name}")
        
        try:
            frappe.rename_doc("Account", acc.name, new_name, force=True)
        except Exception as e:
            print(f"Failed to rename {acc.name}: {e}")
            
    frappe.db.commit()
    print("Migration complete.")
