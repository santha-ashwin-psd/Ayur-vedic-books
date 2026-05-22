# Copyright (c) 2026
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document


class PurchaseReceipt(Document):

    def validate(self):
        if not self.items:
            frappe.throw(_("Purchase Receipt must have at least one item row."))
        for row in self.items:
            if flt(row.qty) <= 0:
                frappe.throw(_("Row {0}: qty must be > 0").format(row.idx))
        self.total_qty = sum(flt(r.qty) for r in self.items)

    def on_submit(self):
        self._adjust_po_received(direction=+1)
        self.db_set("status", "Submitted", update_modified=False)

    def on_cancel(self):
        self._adjust_po_received(direction=-1)
        self.db_set("status", "Cancelled", update_modified=False)

    def _adjust_po_received(self, direction: int):
        if not self.purchase_order:
            return
        for row in self.items:
            if not row.po_item:
                continue
            cur = flt(frappe.db.get_value("Purchase Order Item", row.po_item, "received_qty"))
            new_qty = max(0.0, cur + direction * flt(row.qty))
            frappe.db.set_value("Purchase Order Item", row.po_item, "received_qty",
                                new_qty, update_modified=False)
        try:
            from zoho_books_clone.api.docs import _po_status_from_fulfillment
            new_status = _po_status_from_fulfillment(self.purchase_order)
            frappe.db.set_value("Purchase Order", self.purchase_order, "status",
                                new_status, update_modified=True)
        except Exception:
            pass
