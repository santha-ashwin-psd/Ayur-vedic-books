import frappe

def run():
    # Delete leftover test FYs covering 2020 (created by previous test runs)
    leftovers = frappe.db.sql("""
        SELECT name FROM `tabFiscal Year`
        WHERE year_start_date = '2020-01-01' AND year_end_date = '2020-12-31'
    """, as_dict=True)
    for r in leftovers:
        frappe.db.delete("Fiscal Year", r.name)
        print(f"Deleted FY: {r.name}")
    frappe.db.commit()
    print("Done")
