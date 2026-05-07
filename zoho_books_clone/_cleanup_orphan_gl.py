import frappe

def run():
    result = frappe.db.sql(
        "UPDATE `tabGeneral Ledger Entry` SET is_cancelled=1 WHERE account='Office Supplies'",
    )
    frappe.db.commit()
    count = frappe.db.sql("SELECT ROW_COUNT() AS n", as_dict=True)[0].n
    print(f"Cancelled GL entries with account='Office Supplies'")
    print("Done")
