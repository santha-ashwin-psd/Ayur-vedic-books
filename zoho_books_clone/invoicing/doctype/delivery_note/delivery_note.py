# Copyright (c) 2026
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document


class DeliveryNote(Document):

    def validate(self):
        if not self.items:
            frappe.throw(_("Delivery Note must have at least one item row."))
        for row in self.items:
            if flt(row.qty) <= 0:
                frappe.throw(_("Row {0}: qty must be > 0").format(row.idx))
        self.total_qty = sum(flt(r.qty) for r in self.items)

    def on_submit(self):
        self._adjust_so_delivered(direction=+1)
        self._release_reserved_qty(direction=-1)   # goods shipped → release reservation
        self.db_set("status", "Submitted", update_modified=False)

    def on_cancel(self):
        self._adjust_so_delivered(direction=-1)
        self._release_reserved_qty(direction=+1)   # shipment reversed → restore reservation
        self.db_set("status", "Cancelled", update_modified=False)

    def _release_reserved_qty(self, direction: int):
        """
        Release (direction=-1) or restore (direction=+1) reserved_qty in Bin
        when goods are shipped via this Delivery Note.

        actual_qty is managed separately by stock_link.py → Stock Entry.
        This method only touches reserved_qty and recalculates projected_qty.
        """
        from zoho_books_clone.inventory.utils import update_bin
        warehouse = getattr(self, "set_warehouse", None) or ""

        for row in self.items:
            wh = getattr(row, "warehouse", None) or warehouse
            if not wh or not row.item_code:
                continue
            is_stock = frappe.db.get_value("Item", row.item_code, "is_stock_item")
            if not is_stock:
                continue
            update_bin(
                item_code=row.item_code,
                warehouse=wh,
                reserved_qty_delta=direction * flt(row.qty),
                company=self.company or "",
            )

    def _adjust_so_delivered(self, direction: int):
        """Bump (direction=+1) or decrement (-1) delivered_qty on linked SO rows."""
        if not self.sales_order:
            return

        so_items = frappe.db.sql("""
            SELECT name, item_code, qty, delivered_qty
            FROM `tabSales Order Item` WHERE parent=%s ORDER BY idx
        """, (self.sales_order,), as_dict=True)
        by_code = {}
        for r in so_items:
            by_code.setdefault(r.item_code, []).append(r)

        def _bump(so_item_id, dn_qty):
            cur = flt(frappe.db.get_value("Sales Order Item", so_item_id, "delivered_qty"))
            new_qty = max(0.0, cur + direction * flt(dn_qty))
            frappe.db.set_value("Sales Order Item", so_item_id, "delivered_qty",
                                new_qty, update_modified=False)

        for row in self.items:
            if row.so_item:
                _bump(row.so_item, row.qty)
                continue
            pool = by_code.get(row.item_code) or []
            remaining = flt(row.qty)
            for so_row in pool:
                if remaining <= 0:
                    break
                available = max(0.0, flt(so_row.qty) - flt(so_row.delivered_qty))
                if available <= 0 and direction > 0:
                    continue
                take = min(available, remaining) if direction > 0 else min(flt(so_row.delivered_qty), remaining)
                if take <= 0:
                    continue
                _bump(so_row.name, take)
                so_row.delivered_qty = flt(so_row.delivered_qty) + direction * take
                remaining -= take

        try:
            from zoho_books_clone.api.docs import _so_status_from_fulfillment
            new_status = _so_status_from_fulfillment(self.sales_order)
            frappe.db.set_value("Sales Order", self.sales_order, "status",
                                new_status, update_modified=True)
        except Exception:
            pass
