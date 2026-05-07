import frappe

def run():
    # Check GL currency column
    gl_cols = frappe.db.sql("SHOW COLUMNS FROM `tabGeneral Ledger Entry` LIKE '%currency%'", as_dict=True)
    print(f"GL currency columns: {[c['Field'] for c in gl_cols]}")

    # Check SI exchange columns in DB
    si_cols = frappe.db.sql("SHOW COLUMNS FROM `tabSales Invoice` LIKE '%exchange%'", as_dict=True)
    print(f"SI exchange columns: {[c['Field'] for c in si_cols]}")

    # Check PE exchange columns
    pe_cols = frappe.db.sql("SHOW COLUMNS FROM `tabPayment Entry` LIKE '%exchange%'", as_dict=True)
    print(f"PE exchange columns: {[c['Field'] for c in pe_cols]}")

    # Check SI currency column
    si_curr = frappe.db.sql("SHOW COLUMNS FROM `tabSales Invoice` LIKE '%currency%'", as_dict=True)
    print(f"SI currency columns: {[c['Field'] for c in si_curr]}")

    # Accounts with 'exchange' or 'gain' or 'loss' in name
    accts = frappe.get_all("Account", filters=[["name", "like", "%xchange%"]], fields=["name","account_type"])
    print(f"\nExchange accounts: {accts}")

    accts2 = frappe.get_all("Account", filters=[["account_type", "=", "Income"]], fields=["name","account_type"], limit=5)
    print(f"Sample Income accounts: {accts2}")

    # What currencies exist
    curs = frappe.get_all("Currency", filters={"enabled": 1}, fields=["name", "fraction"], limit=15)
    print(f"\nEnabled currencies: {[c.name for c in curs]}")
