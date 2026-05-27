def run():
    import frappe
    out = {}
    for so_name in ["SO-2026-00006","SO-2026-00012","SO-2026-00013","SO-2026-00014"]:
        if not frappe.db.exists("Sales Order", so_name):
            continue
        items = frappe.db.sql("SELECT idx, name, item_code, qty, delivered_qty FROM `tabSales Order Item` WHERE parent=%s ORDER BY idx", (so_name,), as_dict=True)
        status = frappe.db.get_value("Sales Order", so_name, "status")
        out[so_name] = {"status": status, "items": items}
    return out
