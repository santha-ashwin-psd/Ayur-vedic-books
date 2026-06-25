import frappe
from frappe import _
from frappe.utils import flt, today, getdate
from frappe.model.document import Document
from zoho_books_clone.accounts.accounting_engine import (
    post_sales_invoice, reverse_voucher,
)
from zoho_books_clone.db.validators import (
    validate_fiscal_year, validate_account_company, validate_account_type,
)


class SalesInvoice(Document):

    def validate(self):
        self.validate_items()
        self.calculate_totals()
        self.set_outstanding_amount()
        self.validate_accounts()
        self.set_status()
        self.set_due_date()
        self._set_customer_gstin()
        if self.posting_date and self.company:
            try:
                self.fiscal_year = validate_fiscal_year(self.posting_date, self.company)
            except Exception:
                pass  # Don't block save if fiscal year not set yet

    def _set_customer_gstin(self):
        if self.customer and not self.customer_gstin:
            gstin = frappe.db.get_value("Customer", self.customer, "tax_id")
            if gstin:
                self.customer_gstin = gstin

    def validate_items(self):
        if not self.items:
            frappe.throw(_("Please add at least one item"))
        for item in self.items:
            # Return invoices (credit notes) carry negative qty by design
            if not self.is_return and flt(item.qty) <= 0:
                frappe.throw(_("Qty must be > 0 for {0}").format(item.item_name))
            item.amount = round(flt(item.qty) * flt(item.rate), 2)

    def calculate_totals(self):
        net = sum(flt(i.qty) * flt(i.rate) for i in self.items)
        for tax in (self.taxes or []):
            if flt(tax.rate) and not flt(tax.tax_amount):
                tax.tax_amount = round(net * flt(tax.rate) / 100, 2)
        tax_total = sum(flt(t.tax_amount) for t in (self.taxes or []))
        self.net_total   = round(net, 2)
        self.total_tax   = round(tax_total, 2)
        self.grand_total = round(net + tax_total, 2)

    def set_outstanding_amount(self):
        # For credit notes, outstanding is always 0 (balance tracked separately)
        if self.is_return:
            return
        if self.docstatus == 0:
            # Draft: always keep outstanding_amount in sync with grand_total
            # so that editing items reflects the correct balance immediately
            self.outstanding_amount = self.grand_total

    def validate_accounts(self):
        if self.debit_to:
            validate_account_company(self.debit_to, self.company)
            validate_account_type(self.debit_to, ["Receivable"])
        if self.income_account:
            validate_account_company(self.income_account, self.company)
            validate_account_type(self.income_account, ["Income"])

    def set_status(self):
        if self.docstatus == 2:
            self.status = "Cancelled"
        elif self.docstatus == 1:
            if flt(self.outstanding_amount) <= 0:
                self.status = "Paid"
            elif flt(self.outstanding_amount) < flt(self.grand_total):
                self.status = "Partly Paid"
            elif self.due_date and getdate(self.due_date) < getdate(today()):
                self.status = "Overdue"
            else:
                self.status = "Submitted"
        else:
            self.status = "Draft"

    def set_due_date(self):
        if not self.due_date:
            # Try payment terms first
            if self.payment_terms and self.posting_date:
                try:
                    from zoho_books_clone.books_setup.doctype.payment_terms.payment_terms import get_due_date
                    self.due_date = get_due_date(self.payment_terms, self.posting_date)
                    return
                except Exception:
                    pass
            self.due_date = self.posting_date

    def on_submit(self):
        new_outstanding = flt(self.grand_total)
        self.outstanding_amount = new_outstanding
        self.status = "Submitted"
        self.db_set("outstanding_amount", new_outstanding, update_modified=False)
        self.db_set("status", "Submitted", update_modified=False)
        post_sales_invoice(self)
        if getattr(self, "update_stock", 0) and getattr(self, "sales_order", None):
            self._release_reserved_qty(direction=-1)

    def on_cancel(self):
        self.status = "Cancelled"
        self._check_no_payments_before_cancel()
        reverse_voucher(self.doctype, self.name)
        if getattr(self, "update_stock", 0) and getattr(self, "sales_order", None):
            self._release_reserved_qty(direction=+1)
        # Reverse billed_qty on linked SO lines so the SO becomes re-invoiceable
        if getattr(self, "sales_order", None):
            self._reverse_billed_qty()

    def _reverse_billed_qty(self):
        """Decrement billed_qty on the linked Sales Order lines and refresh SO status."""
        so_name = self.sales_order
        for row in (self.items or []):
            if not row.item_code or flt(row.qty) <= 0:
                continue
            so_rows = frappe.db.sql("""
                SELECT name, billed_qty FROM `tabSales Order Item`
                WHERE parent = %s AND item_code = %s
                ORDER BY idx
            """, (so_name, row.item_code), as_dict=True)
            remaining_to_reverse = flt(row.qty)
            for sr in so_rows:
                if remaining_to_reverse <= 0:
                    break
                take = min(flt(sr.billed_qty), remaining_to_reverse)
                if take <= 0:
                    continue
                frappe.db.set_value(
                    "Sales Order Item", sr.name, "billed_qty",
                    max(0.0, flt(sr.billed_qty) - take),
                    update_modified=False,
                )
                remaining_to_reverse -= take
        # Recalculate SO status so the Invoice button reappears
        try:
            from zoho_books_clone.api.docs import _so_status_from_fulfillment
            new_status = _so_status_from_fulfillment(so_name)
            frappe.db.set_value("Sales Order", so_name, "status",
                                new_status, update_modified=True)
        except Exception:
            pass

    def _release_reserved_qty(self, direction: int):
        """Release (direction=-1) or restore (+1) reserved_qty when invoicing directly against an SO."""
        from zoho_books_clone.inventory.utils import update_bin
        warehouse = getattr(self, "set_warehouse", None) or ""
        for row in (self.items or []):
            wh = getattr(row, "warehouse", None) or warehouse
            if not wh or not row.item_code:
                continue
            qty = flt(row.qty)
            if qty <= 0:
                continue
            is_stock = frappe.db.get_value("Item", row.item_code, "is_stock_item")
            if not is_stock:
                continue
            update_bin(
                item_code=row.item_code,
                warehouse=wh,
                reserved_qty_delta=direction * qty,
                company=self.company or "",
            )

    def _check_no_payments_before_cancel(self):
        linked = frappe.db.sql("""
            SELECT per.parent FROM `tabPayment Entry Reference` per
            JOIN `tabPayment Entry` pe ON pe.name = per.parent
            WHERE per.reference_name = %s AND pe.docstatus = 1
        """, self.name, as_dict=True)
        if linked:
            frappe.throw(_(
                "Cannot cancel {0} — linked payment(s) exist: {1}"
            ).format(self.name, ", ".join(r.parent for r in linked)))

    def _get_currency_symbol(self):
        cur = self.currency or "INR"
        sym = frappe.db.get_value("Currency", cur, "symbol")
        return sym or (cur + " ")

    @frappe.whitelist()
    def send_invoice_email(self):
        customer_email = frappe.db.get_value("Customer", self.customer, "email_id")
        if not customer_email:
            frappe.throw(_("Customer {0} has no email").format(self.customer))
        sym = self._get_currency_symbol()
        cur = self.currency or "INR"
        frappe.sendmail(
            recipients=[customer_email],
            subject=f"Invoice {self.name} ({cur})",
            message=(f"Dear {self.customer_name},<br><br>"
                     f"Your invoice <b>{self.name}</b> for <b>{sym}{self.grand_total:,.2f} {cur}</b> is attached.<br>"
                     f"Due: {self.due_date}"),
            attachments=[frappe.attach_print(self.doctype, self.name, print_format="Sales Invoice")],
        )
        frappe.msgprint(_("Invoice emailed to {0}").format(customer_email))

    @frappe.whitelist()
    def get_payment_status(self):
        payments = frappe.db.sql("""
            SELECT pe.name, pe.payment_date, per.allocated_amount
            FROM `tabPayment Entry` pe
            JOIN `tabPayment Entry Reference` per ON per.parent = pe.name
            WHERE per.reference_name = %s AND pe.docstatus = 1
            ORDER BY pe.payment_date
        """, self.name, as_dict=True)
        return {
            "payments":           payments,
            "total_paid":         sum(flt(p.allocated_amount) for p in payments),
            "outstanding_amount": self.outstanding_amount,
            "grand_total":        self.grand_total,
        }