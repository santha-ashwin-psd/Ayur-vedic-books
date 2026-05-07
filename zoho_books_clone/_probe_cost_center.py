import frappe

def run():
    ccs = frappe.db.sql("SELECT name, cost_center_name, is_group, parent_cost_center FROM `tabCost Center`", as_dict=True)
    print(f"Cost Centers ({len(ccs)}):")
    for c in ccs:
        print(f"  {c.name}: name={c.cost_center_name}, is_group={c.is_group}, parent={c.parent_cost_center}")

    # Check GL entries that have cost_center set
    gl_cc = frappe.db.sql("""
        SELECT DISTINCT cost_center, COUNT(*) as cnt
        FROM `tabGeneral Ledger Entry`
        WHERE cost_center IS NOT NULL AND cost_center != ''
        GROUP BY cost_center
        LIMIT 10
    """, as_dict=True)
    print(f"\nGL entries with cost_center ({len(gl_cc)} distinct values):")
    for r in gl_cc:
        print(f"  {r.cost_center}: {r.cnt} entries")

    # Check Journal Entry doctype fields
    je_fields = frappe.db.sql("""
        SELECT fieldname, fieldtype, options FROM `tabDocField`
        WHERE parent = 'Journal Entry' AND fieldname LIKE '%cost%'
    """, as_dict=True)
    print(f"\nJournal Entry cost fields: {je_fields}")
