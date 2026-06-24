import frappe
from frappe import _
from frappe.utils import flt, today, getdate
from frappe.model.document import Document
from zoho_books_clone.accounts.accounting_engine import (
    post_purchase_invoice, reverse_voucher,
)
from zoho_books_clone.db.validators import (
    validate_fiscal_year, validate_account_company, validate_account_type
)


class PurchaseInvoice(Document):

    def validate(self):
        if not self.items:
            frappe.throw(_("Please add at least one item"))
        for item in self.items:
            item.amount = round(flt(item.qty) * flt(item.rate), 2)
        self.calculate_totals()
        self.set_outstanding_amount()
        self.validate_accounts()
        self.set_status()
        if self.posting_date and self.company:
            try:
                self.fiscal_year = validate_fiscal_year(self.posting_date, self.company)
            except Exception:
                self.fiscal_year = ""

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
        if self.docstatus == 0:
            self.outstanding_amount = self.grand_total

    def validate_accounts(self):
        if self.credit_to:
            validate_account_company(self.credit_to, self.company)
            validate_account_type(self.credit_to, ["Payable"])
        if self.expense_account:
            validate_account_company(self.expense_account, self.company)
            validate_account_type(self.expense_account, ["Expense"])

    def set_status(self):
        if self.docstatus == 2:   self.status = "Cancelled"
        elif self.docstatus == 1:
            if flt(self.outstanding_amount) <= 0:                            self.status = "Paid"
            elif flt(self.outstanding_amount) < flt(self.grand_total):       self.status = "Partly Paid"
            elif self.due_date and getdate(self.due_date) < getdate(today()): self.status = "Overdue"
            else:                                                             self.status = "Submitted"
        else:
            self.status = "Draft"

    def on_submit(self):
        if self.update_stock and not getattr(self, "is_return", 0):
            self._move_stock(direction=+1)
        if getattr(self, "is_return", 0):
            from zoho_books_clone.accounts.accounting_engine import post_debit_note
            dn_amount = abs(flt(self.grand_total))

            # Guard: check that the source bill still has enough outstanding
            if getattr(self, "return_against", None):
                src_outstanding = flt(frappe.db.get_value(
                    "Purchase Invoice", self.return_against, "outstanding_amount"
                ) or 0)
                if src_outstanding < dn_amount - 0.01:
                    frappe.throw(_(
                        "Cannot submit Debit Note {0}: the Purchase Invoice {1} "
                        "already has its balance fully claimed "
                        "(remaining: ₹{2:,.2f}, this note: ₹{3:,.2f})."
                    ).format(
                        self.name,
                        self.return_against,
                        src_outstanding,
                        dn_amount,
                    ))

            # A return doesn't create new debt; it offsets the source bill.
            self.db_set("outstanding_amount", 0, update_modified=False)
            self.db_set("status", "Paid", update_modified=False)
            remark = (getattr(self, "remark", "") or "").strip()
            return_type = "inventory" if "Goods Returned" in remark else "expense"
            post_debit_note(self, return_type=return_type)
            self._adjust_source_bill_outstanding(direction=-1)
        else:
            self.db_set("outstanding_amount", self.grand_total, update_modified=False)
            self.db_set("status", "Submitted", update_modified=False)
            self.outstanding_amount = self.grand_total
            self.status = "Submitted"
            post_purchase_invoice(self)

    def on_cancel(self):
        self.status = "Cancelled"
        self.outstanding_amount = 0
        reverse_voucher(self.doctype, self.name)
        if self.update_stock and not getattr(self, "is_return", 0):
            self._move_stock(direction=-1)
        if getattr(self, "is_return", 0):
            self._adjust_source_bill_outstanding(direction=+1)

    def _move_stock(self, direction: int):
        """
        Move stock when the invoice is used as the stock document (update_stock=1).
        Only called for normal (non-return) purchase invoices.

        Purchase adds stock (stock_sign=+1):
          - PI submit:  +1 * +1 * +qty = +qty  (stock in)
          - PI cancel:  -1 * +1 * +qty = -qty  (stock reversed)
        """
        from zoho_books_clone.inventory.utils import update_bin, make_sle
        warehouse = getattr(self, "set_warehouse", None) or ""
        if not warehouse:
            return

        stock_sign = +1  # purchasing adds stock

        for row in (self.items or []):
            if not row.item_code:
                continue
            is_stock = frappe.db.get_value("Item", row.item_code, "is_stock_item")
            if not is_stock:
                continue

            actual_delta = direction * stock_sign * flt(row.qty)
            rate = flt(row.rate) if direction > 0 else 0

            make_sle(
                item_code=row.item_code,
                warehouse=warehouse,
                actual_qty=actual_delta,
                voucher_type="Purchase Invoice",
                voucher_no=self.name,
                company=self.company or "",
                incoming_rate=rate,
                posting_date=self.posting_date or "",
            )
            update_bin(
                item_code=row.item_code,
                warehouse=warehouse,
                actual_qty_delta=actual_delta,
                incoming_rate=rate,
                company=self.company or "",
            )

    def _adjust_source_bill_outstanding(self, direction: int):
        """Reduce (direction=-1) or restore (+1) outstanding on the source PINV.

        Always uses abs(grand_total) because debit note items carry negative qty,
        making grand_total negative. Without abs(), direction=-1 would ADD to
        outstanding instead of reducing it.
        """
        if not getattr(self, "return_against", None):
            return
        src = frappe.db.get_value(
            "Purchase Invoice", self.return_against,
            ["outstanding_amount", "grand_total", "due_date", "docstatus"],
            as_dict=True,
        )
        if not src:
            return
        dn_amount = abs(flt(self.grand_total))
        new_outstanding = max(0.0, round(flt(src.outstanding_amount) + direction * dn_amount, 2))
        if src.docstatus == 1:
            if flt(new_outstanding) <= 0:                            new_status = "Paid"
            elif flt(new_outstanding) < flt(src.grand_total):        new_status = "Partly Paid"
            elif src.due_date and getdate(src.due_date) < getdate(today()): new_status = "Overdue"
            else:                                                    new_status = "Submitted"
        else:
            new_status = "Cancelled" if src.docstatus == 2 else "Draft"
        frappe.db.set_value(
            "Purchase Invoice", self.return_against,
            {"outstanding_amount": new_outstanding, "status": new_status},
            update_modified=False,
        )
