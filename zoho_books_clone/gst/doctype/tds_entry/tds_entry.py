import frappe
from frappe.model.document import Document
from frappe.utils import flt


class TDSEntry(Document):
    def before_insert(self):
        if not self.tds_total and self.amount and self.rate:
            self.tds_total = round(
                flt(self.amount) * (flt(self.rate) + flt(self.surcharge) + flt(self.cess)) / 100, 2
            )

    def after_insert(self):
        if self.expense_account and flt(self.amount) > 0 and flt(self.tds_total) > 0 and not self.voucher_no:
            try:
                from zoho_books_clone.api.gst import create_tds_entry
                result = create_tds_entry(
                    company=self.company,
                    party=self.party or "",
                    expense_account=self.expense_account,
                    amount=str(flt(self.amount)),
                    tds_amount=str(flt(self.tds_total)),
                    tds_section=self.section or "",
                    date=str(self.date),
                    remarks=self.remarks or "",
                )
                frappe.db.set_value("TDS Entry", self.name, "voucher_no", result.get("voucher_no", ""))
                frappe.db.commit()
            except Exception:
                pass
