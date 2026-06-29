# Copyright (c) 2026
import frappe
from frappe import _
from frappe.utils import flt
from frappe.model.document import Document
from zoho_books_clone.db.validators import validate_fiscal_year


class PurchaseReceipt(Document):

    def validate(self):
        # Purchase Receipt is not wired to central_validator, so fiscal year
        # validation must run here.  Block saves into closed or missing periods
        # before any inventory or fulfilment logic runs.
        if self.posting_date and self.company:
            validate_fiscal_year(self.posting_date, self.company)

        if not self.items:
            frappe.throw(_("Purchase Receipt must have at least one item row."))
        for row in self.items:
            if flt(row.qty) <= 0:
                frappe.throw(_("Row {0}: qty must be > 0").format(row.idx))
        self.total_qty = sum(flt(r.qty) for r in self.items)

    def on_submit(self):
        self._adjust_po_received(direction=+1)
        self._release_ordered_qty(direction=-1)    # goods arrived → release "on order"
        self.db_set("status", "Submitted", update_modified=False)

    def on_cancel(self):
        self._adjust_po_received(direction=-1)
        self._release_ordered_qty(direction=+1)    # receipt reversed → restore "on order"
        self.db_set("status", "Cancelled", update_modified=False)

    def _release_ordered_qty(self, direction: int):
        """
        Release (direction=-1) or restore (direction=+1) ordered_qty in Bin
        when goods are received via this Purchase Receipt.

        actual_qty is managed separately by stock_link.py → Stock Entry.
        This method only touches ordered_qty and recalculates projected_qty.
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
                ordered_qty_delta=direction * flt(row.qty),
                company=self.company or "",
            )

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