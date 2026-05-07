import frappe
from zoho_books_clone.api.auth import signup_user, verify_signup_otp, complete_onboarding

def run():
    test_email = "test_onboarding@example.com"
    test_company = "Test Onboarding Corp"

    if frappe.db.exists("User", test_email):
        frappe.db.delete("User", test_email)

    print("--- SIGNUP ---")
    res = signup_user(first_name="Test", email=test_email, password="Strong!Password#123", company_name=test_company)
    print("Signup Response:", res)

    key = f"books_signup:{test_email}"
    data = frappe.cache.get_value(key)
    otp = data["otp"]
    print("Generated OTP:", otp)

    print("--- VERIFY OTP ---")
    res2 = verify_signup_otp(email=test_email, otp=otp)
    print("Verify OTP Response:", res2)

    user_doc = frappe.get_doc("User", test_email)
    print(f"User created: {user_doc.name}, Roles: {[r.role for r in user_doc.roles]}")

    print("--- COMPLETE ONBOARDING ---")
    frappe.session.user = test_email
    res3 = complete_onboarding(company_name=test_company, currency="USD", fy_start="01-01")
    print("Complete Onboarding Response:", res3)

    accounts = frappe.get_all("Account", filters={"company": test_company}, fields=["name", "account_type", "is_group"])
    print(f"COA Created for {test_company}: {len(accounts)} accounts.")
    for acc in accounts:
        print(f" - {acc.name} ({acc.account_type}) - Group: {acc.is_group}")
