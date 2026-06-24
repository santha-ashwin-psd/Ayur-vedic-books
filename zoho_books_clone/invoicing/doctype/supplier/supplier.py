import re
import frappe
from frappe import _
from frappe.model.document import Document

_GSTIN_RE = re.compile(r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$')

class Supplier(Document):
    def validate(self):
        if not self.supplier_name:
            frappe.throw(_("Supplier Name is required"))
        if self.email_id and "@" not in self.email_id:
            frappe.throw(_("Please enter a valid email address"))
        if self.tax_id:
            self.tax_id = self.tax_id.strip().upper()
            if not _GSTIN_RE.match(self.tax_id):
                frappe.throw(_("Invalid GSTIN: {0}. Expected format: 22AAAAA0000A1Z5").format(self.tax_id))

    @frappe.whitelist()
    def get_outstanding_bills(self):
        return frappe.get_all(
            "Purchase Invoice",
            filters={"supplier": self.name, "docstatus": 1, "outstanding_amount": [">", 0]},
            fields=["name", "posting_date", "due_date", "grand_total", "outstanding_amount"],
            order_by="due_date asc",
        )
