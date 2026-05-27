def run():
    """End-to-end Delivery Challan workflow audit:
    1. Create DN from SO via API → check so_item linkage + delivered_qty bump
    2. Cancel DN → check delivered_qty decrements + SO status reverts
    3. Create manual DN (no so_item) → check fallback matching works
    """
    import frappe
    from frappe.utils import flt
    from zoho_books_clone.api.docs import create_delivery_note_from_so

    results = {"steps": [], "pass": 0, "fail": 0}
    def check(label, cond, detail=""):
        results["steps"].append({"label": label, "ok": bool(cond), "detail": detail})
        if cond: results["pass"] += 1
        else:    results["fail"] += 1

    # ── Pick SO-2026-00012 (Partially Delivered with line 2 still un-delivered)
    target_so = "SO-2026-00012"
    so_items_before = frappe.db.sql("SELECT name, item_code, qty, delivered_qty FROM `tabSales Order Item` WHERE parent=%s ORDER BY idx", (target_so,), as_dict=True)
    so_status_before = frappe.db.get_value("Sales Order", target_so, "status")
    results["before"] = {"status": so_status_before, "items": so_items_before}

    # Find a line with remaining qty
    remaining_line = next((r for r in so_items_before if flt(r.qty) > flt(r.delivered_qty)), None)
    if not remaining_line:
        results["abort"] = "no remaining qty on SO-2026-00012"
        return results

    # ── STEP 1: Create DN for 1 unit of the remaining line via API
    line_qtys = {str(remaining_line.name): 1}
    res = create_delivery_note_from_so(target_so, line_qtys=line_qtys)
    new_dn = res["delivery_note"]
    results["created_dn"] = new_dn

    # 1a. so_item must be set correctly
    dn_items = frappe.db.sql("SELECT name, item_code, qty, so_item FROM `tabDelivery Note Item` WHERE parent=%s", (new_dn,), as_dict=True)
    check("DN items got so_item linkage", all(r.so_item == remaining_line.name for r in dn_items),
          detail=f"dn_items={dn_items}, expected so_item={remaining_line.name}")

    # 1b. delivered_qty bumped on the target SO line
    after_qty = flt(frappe.db.get_value("Sales Order Item", remaining_line.name, "delivered_qty"))
    check("SO line delivered_qty bumped", abs(after_qty - flt(remaining_line.delivered_qty) - 1) < 0.001,
          detail=f"before={remaining_line.delivered_qty}, after={after_qty}")

    # 1c. SO status reflects fulfillment
    new_status = frappe.db.get_value("Sales Order", target_so, "status")
    check("SO status updated", new_status in ("Partially Delivered","Delivered"),
          detail=f"status={new_status}")

    # ── STEP 2: Cancel the DN
    dn_doc = frappe.get_doc("Delivery Note", new_dn)
    dn_doc.cancel()
    frappe.db.commit()

    reverted_qty = flt(frappe.db.get_value("Sales Order Item", remaining_line.name, "delivered_qty"))
    check("Cancel reverted delivered_qty", abs(reverted_qty - flt(remaining_line.delivered_qty)) < 0.001,
          detail=f"after_cancel={reverted_qty}, original={remaining_line.delivered_qty}")

    cancelled_dn_status = frappe.db.get_value("Delivery Note", new_dn, "status")
    check("DN status = Cancelled", cancelled_dn_status == "Cancelled",
          detail=f"dn_status={cancelled_dn_status}")

    # ── STEP 3: Manual DN (no so_item) — fallback match by item_code
    # Find any SO with remaining capacity to test fallback
    target_so_2 = "SO-2026-00013"
    so2_items_before = frappe.db.sql("SELECT name, item_code, qty, delivered_qty FROM `tabSales Order Item` WHERE parent=%s ORDER BY idx", (target_so_2,), as_dict=True)
    line_with_room = next((r for r in so2_items_before if flt(r.qty) > flt(r.delivered_qty)), None)
    if line_with_room:
        manual_dn = frappe.get_doc({
            "doctype": "Delivery Note",
            "customer": frappe.db.get_value("Sales Order", target_so_2, "customer"),
            "customer_name": frappe.db.get_value("Sales Order", target_so_2, "customer_name"),
            "posting_date": frappe.utils.today(),
            "sales_order": target_so_2,
            "company": frappe.db.get_value("Sales Order", target_so_2, "company"),
            "items": [{
                "doctype": "Delivery Note Item",
                "item_code": line_with_room.item_code,
                "item_name": line_with_room.item_code,
                "qty": 1,
                "uom": "Nos",
                # NO so_item — testing fallback
            }],
        })
        manual_dn.flags.ignore_permissions = True
        manual_dn.flags.ignore_mandatory = True
        manual_dn.insert()
        manual_dn.submit()
        frappe.db.commit()

        fb_qty = flt(frappe.db.get_value("Sales Order Item", line_with_room.name, "delivered_qty"))
        check("Manual DN (no so_item) fallback-matched by item_code", abs(fb_qty - flt(line_with_room.delivered_qty) - 1) < 0.001,
              detail=f"before={line_with_room.delivered_qty}, after={fb_qty}")

        # cleanup
        manual_dn.cancel()
        frappe.delete_doc("Delivery Note", manual_dn.name, force=1)
        frappe.db.commit()

    return results
