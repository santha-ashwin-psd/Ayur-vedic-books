import frappe

def run():
    frappe.db.delete("User", {"email": "test_onboarding@example.com"})
    frappe.db.delete("Account", {"company": "Test Onboarding Corp"})
    frappe.db.commit()
