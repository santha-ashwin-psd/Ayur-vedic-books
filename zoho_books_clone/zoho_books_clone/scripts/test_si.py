
import frappe
from frappe.utils import nowdate, add_days

def test_sales_invoice_workflow():
    print("Starting Sales Invoice Workflow Test...")
    
    company = "PS Digitise"
    
    # 1. Ensure Customer exists
    customer_name = "Test Customer"
    if not frappe.db.exists("Customer", customer_name):
        c = frappe.get_doc({
            "doctype": "Customer",
            "customer_name": customer_name,
        }).insert()
        customer_name = c.name
        print(f"Created Test Customer: {customer_name}")
    else:
        customer_name = frappe.db.get_value("Customer", customer_name, "name")

    # 2. Ensure Item exists
    item_code = "TEST-ITEM-001"
    if not frappe.db.exists("Item", {"item_code": item_code}):
        it = frappe.get_doc({
            "doctype": "Item",
            "item_name": "Test Item",
            "item_code": item_code,
            "standard_rate": 100,
            "is_stock_item": 1
        }).insert()
        item_code = it.name
        print(f"Created Test Item: {item_code}")
    else:
        item_code = frappe.db.get_value("Item", {"item_code": item_code}, "name")

    # 3. Create Sales Invoice
    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "company": company,
        "customer": customer_name,
        "posting_date": nowdate(),
        "due_date": add_days(nowdate(), 30),
        "debit_to": "Accounts Receivable",
        "income_account": "Sales Revenue",
        "currency": "INR",
        "items": [
            {
                "item_name": "Test Item",
                "qty": 10,
                "rate": 100,
                "amount": 1000
            }
        ],
        "taxes": [
            {
                "tax_type": "CGST",
                "description": "CGST @ 9%",
                "rate": 9,
                "tax_amount": 90,
                "account_head": "CGST Payable"
            },
            {
                "tax_type": "SGST",
                "description": "SGST @ 9%",
                "rate": 9,
                "tax_amount": 90,
                "account_head": "SGST Payable"
            }
        ]
    })
    
    # Recalculate totals (as the JS does)
    si.net_total = 1000
    si.total_tax = 180
    si.grand_total = 1180
    
    si.insert()
    print(f"Sales Invoice {si.name} created (Draft)")
    
    # 4. Submit
    si.submit()
    print(f"Sales Invoice {si.name} submitted")
    
    # 5. Check GL Entries
    gl_entries = frappe.get_all("General Ledger Entry", filters={"voucher_no": si.name}, fields=["account", "debit", "credit"])
    print("\nGL Entries:")
    for gle in gl_entries:
        print(f"Account: {gle.account}, Debit: {gle.debit}, Credit: {gle.credit}")
    
    # Verification Logic
    expected_gle = [
        {"account": "Accounts Receivable", "debit": 1180, "credit": 0},
        {"account": "Sales Revenue", "debit": 0, "credit": 1000},
        {"account": "CGST Payable", "debit": 0, "credit": 90},
        {"account": "SGST Payable", "debit": 0, "credit": 90},
    ]
    
    for expected in expected_gle:
        match = any(e["account"] == expected["account"] and e["debit"] == expected["debit"] and e["credit"] == expected["credit"] for e in gl_entries)
        if not match:
            print(f"❌ MISMATCH: Expected {expected} not found or value mismatch")
        else:
            print(f"✅ MATCH: {expected['account']}")

if __name__ == "__main__":
    frappe.connect(site="books.local")
    try:
        test_sales_invoice_workflow()
    finally:
        frappe.db.rollback() # Don't commit for now, just testing logic
        frappe.destroy()
