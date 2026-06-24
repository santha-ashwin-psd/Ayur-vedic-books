# Copyright (c) 2026
import frappe
from frappe.utils import flt
from frappe.model.document import Document


class PurchaseOrder(Document):

    def validate(self):
        self._calculate_totals()

    def _calculate_totals(self):
        for item in (self.items or []):
            item.amount = round(flt(item.qty) * flt(item.rate), 2)
        net = sum(flt(i.amount) for i in (self.items or []))
        for tax in (self.taxes or []):
            if flt(tax.rate) and not flt(tax.tax_amount):
                tax.tax_amount = round(net * flt(tax.rate) / 100, 2)
        tax_total = sum(flt(t.tax_amount) for t in (self.taxes or []))
        self.net_total   = round(net, 2)
        self.total_tax   = round(tax_total, 2)
        self.grand_total = round(net + tax_total, 2)

    def on_submit(self):
        self._update_ordered_qty(direction=+1)

    def on_cancel(self):
        self._update_ordered_qty(direction=-1)

    def _update_ordered_qty(self, direction: int):
        """Increase (submit) or decrease (cancel) ordered_qty in Bin for each PO line."""
        from zoho_books_clone.inventory.utils import update_bin
        warehouse = getattr(self, "set_warehouse", None) or ""
        for row in (self.items or []):
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
