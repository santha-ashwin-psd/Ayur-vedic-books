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
        self.db_set("status", "Submitted", update_modified=False)

    def on_cancel(self):
        self._adjust_so_delivered(direction=-1)
        self.db_set("status", "Cancelled", update_modified=False)

    def _adjust_so_delivered(self, direction: int):
        """Bump (direction=+1) or decrement (-1) delivered_qty on linked SO rows."""
        if not self.sales_order:
            return
        for row in self.items:
            if not row.so_item:
                continue
            cur = flt(frappe.db.get_value("Sales Order Item", row.so_item, "delivered_qty"))
            new_qty = max(0.0, cur + direction * flt(row.qty))
            frappe.db.set_value("Sales Order Item", row.so_item, "delivered_qty",
                                new_qty, update_modified=False)
        # Optional: refresh SO status from fulfillment
        try:
            from zoho_books_clone.api.docs import _so_status_from_fulfillment
            new_status = _so_status_from_fulfillment(self.sales_order)
            frappe.db.set_value("Sales Order", self.sales_order, "status",
                                new_status, update_modified=True)
        except Exception:
            pass
