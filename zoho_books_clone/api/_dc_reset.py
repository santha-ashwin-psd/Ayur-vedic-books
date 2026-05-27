def run():
    """Reset all SO-2026-00006 delivered_qty to the correct value computed from
    the single submitted DN-2026-00001 (so we know the on_submit hook landed
    correctly without my console double-bump)."""
    import frappe
    from frappe.utils import flt

    # Zero out so we can recompute cleanly
    frappe.db.sql("UPDATE `tabSales Order Item` SET delivered_qty=0 WHERE parent=%s", ("SO-2026-00006",))
    frappe.db.commit()

    # Re-run the on_submit logic for DN-2026-00001 only
    dn = frappe.get_doc("Delivery Note", "DN-2026-00001")
    dn._adjust_so_delivered(direction=+1)
    frappe.db.commit()

    items = frappe.db.sql("SELECT idx, name, item_code, qty, delivered_qty FROM `tabSales Order Item` WHERE parent=%s ORDER BY idx", ("SO-2026-00006",), as_dict=True)
    return {"so": "SO-2026-00006", "status": frappe.db.get_value("Sales Order","SO-2026-00006","status"), "items": items}
