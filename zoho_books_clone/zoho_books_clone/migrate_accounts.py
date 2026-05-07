import frappe

def run():
    frappe.flags.in_patch = True
    accounts = frappe.get_all("Account", fields=["name", "account_name", "company", "parent_account"])
    for acc in accounts:
        # Check if already renamed
        if f" - {acc.company}" in acc.name:
            continue
            
        new_name = f"{acc.account_name} - {acc.company}"
        print(f"Renaming {acc.name} to {new_name}")
        
        # Rename the document
        try:
            frappe.rename_doc("Account", acc.name, new_name, force=True)
        except Exception as e:
            print(f"Failed to rename {acc.name}: {e}")
            
    # Also fix parent_accounts that were renamed
    accounts = frappe.get_all("Account", fields=["name", "parent_account", "company"])
    for acc in accounts:
        if acc.parent_account and f" - {acc.company}" not in acc.parent_account:
            new_parent = f"{acc.parent_account} - {acc.company}"
            print(f"Updating parent of {acc.name} to {new_parent}")
            frappe.db.set_value("Account", acc.name, "parent_account", new_parent)
            
    frappe.db.commit()
    print("Migration complete.")
