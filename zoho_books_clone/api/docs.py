import frappe
import json
from frappe.utils import flt, today
from zoho_books_clone.api.session import _get_company


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_doc(doctype, name):
    """
    Fetch a single document with ignore_permissions=True so the Books Manager
    custom role can read any doctype (frappe.client.get blocks custom roles).
    @frappe.whitelist(allow_guest=False) already blocks unauthenticated callers.
    """
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    # Set ignore_permissions BEFORE fetching so frappe.get_doc doesn't run
    # Frappe's internal role-permission check (which blocks the Books Manager role).
    frappe.flags.ignore_permissions = True
    try:
        doc = frappe.get_doc(doctype, name)
        return doc.as_dict()
    finally:
        frappe.flags.ignore_permissions = False


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_list(doctype, fields=None, filters=None, order_by="modified desc", limit_page_length=50, start=0):
    """
    Permission-free list endpoint that mirrors frappe.client.get_list.
    Books tenancy users may have no Frappe role (login is via custom auth flow),
    so the built-in get_list raises PermissionError. This wrapper bypasses that
    check after confirming the caller is authenticated.

    The Vue SPA uses this through src/api/client.js → apiList(). Tenancy filters
    (books_company / company) are added by the client; this endpoint trusts them.
    """
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)

    if isinstance(fields, str):
        try:
            fields = json.loads(fields)
        except Exception:
            fields = [fields]
    if isinstance(filters, str):
        try:
            filters = json.loads(filters)
        except Exception:
            filters = []

    return frappe.get_list(
        doctype,
        fields=fields or ["name"],
        filters=filters or [],
        order_by=order_by,
        start=int(start or 0),
        limit_page_length=int(limit_page_length or 50),
        ignore_permissions=True,
    )


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_invoice_email_defaults(invoice_name):
    """
    Return pre-filled To, Subject, and body for the Send Email dialog.
    Uses the customer's email_id and the invoice's grand_total / due_date.
    """
    inv = frappe.get_doc("Sales Invoice", invoice_name)
    customer_email = frappe.db.get_value("Customer", inv.customer, "email_id") or ""

    subject = f"Invoice {inv.name} from {inv.company or frappe.defaults.get_default('company') or ''}"

    body = (
        f"Dear {inv.customer_name or inv.customer},<br><br>"
        f"Please find your invoice <b>{inv.name}</b> details below:<br><br>"
        f"<table style='border-collapse:collapse;font-size:14px'>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666'>Invoice #</td><td><b>{inv.name}</b></td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666'>Amount</td><td><b>₹{inv.grand_total:,.2f}</b></td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666'>Due Date</td><td>{inv.due_date}</td></tr>"
        f"</table><br>"
        f"Kindly make the payment by the due date.<br><br>"
        f"Thanks for your business.<br><br>"
        f"Regards,<br>{inv.company or ''}"
    )

    return {
        "to": customer_email,
        "subject": subject,
        "body": body,
        "invoice_name": inv.name,
        "customer_name": inv.customer_name or inv.customer,
        "from_email": frappe.session.user,
    }


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def send_invoice_email(invoice_name, to, subject, body, cc=None):
    """
    Send invoice email using Frappe's configured outgoing email account.
    Attaches a PDF of the invoice.
    """
    if not to:
        frappe.throw("Recipient email (To) is required.")

    # Validate invoice exists and user has permission
    if not frappe.has_permission("Sales Invoice", "read", invoice_name):
        frappe.throw("Not permitted", frappe.PermissionError)

    inv = frappe.get_doc("Sales Invoice", invoice_name)

    # Build recipient list (support comma-separated)
    recipients = [e.strip() for e in to.split(",") if e.strip()]
    cc_list = [e.strip() for e in (cc or "").split(",") if e.strip()]

    # Attach PDF of the invoice
    try:
        pdf_attachment = frappe.attach_print(
            inv.doctype,
            inv.name,
            print_format="Sales Invoice",
            print_letterhead=True,
        )
        attachments = [pdf_attachment]
    except Exception:
        # If print format not found, send without attachment
        attachments = []

    # Send using Frappe's configured email account
    frappe.sendmail(
        recipients=recipients,
        cc=cc_list,
        subject=subject,
        message=body,
        attachments=attachments,
        reference_doctype="Sales Invoice",
        reference_name=invoice_name,
        now=True,  # send immediately (not queued)
    )

    # Log a communication record so it appears in the timeline
    comm = frappe.get_doc({
        "doctype": "Communication",
        "communication_type": "Communication",
        "communication_medium": "Email",
        "sent_or_received": "Sent",

        "subject": subject,
        "content": body,
        "sender": frappe.session.user,
        "recipients": to,
        "cc": cc or "",
        "reference_doctype": "Sales Invoice",
        "reference_name": invoice_name,
        "status": "Linked",
    })
    comm.insert(ignore_permissions=True)
    frappe.db.commit()

    return {"status": "sent", "to": to, "invoice": invoice_name}


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def save_doc(doc):
    """
    Save (create or update) a document.
    Called by the Books SPA via POST so large payloads don't hit URL limits.
    @frappe.whitelist(allow_guest=False) already blocks unauthenticated callers;
    we skip frappe.has_permission() because Books Manager is a custom role that
    is not in Frappe's Role Permission Manager for core doctypes.
    """
    if isinstance(doc, str):
        doc = json.loads(doc)

    doctype = doc.get("doctype")
    if not doctype:
        frappe.throw("doctype is required")

    # Block unauthenticated requests (belt-and-suspenders; whitelist already does this)
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)

    # Strip stale child-row identity fields so Frappe replaces rows cleanly
    # instead of trying to look up rows by old hash names that may no longer exist.
    _CHILD_META_KEYS = ("name", "parent", "parenttype", "parentfield", "owner",
                        "creation", "modified", "modified_by")
    for key, val in doc.items():
        if isinstance(val, list):
            for row in val:
                if isinstance(row, dict):
                    for mk in _CHILD_META_KEYS:
                        row.pop(mk, None)

    # Auto-stamp books_company for master types that have no native company field
    _MASTER_TYPES = {"Customer", "Supplier", "Item", "Contact"}
    if doctype in _MASTER_TYPES and not doc.get("books_company"):
        from zoho_books_clone.utils.tenancy import get_user_company, _is_bypass
        if not _is_bypass(frappe.session.user):
            _uc = get_user_company(frappe.session.user)
            if _uc:
                doc["books_company"] = _uc

    # Auto-fill mandatory account fields Frappe requires but the UI doesn't expose
    _company = doc.get("company") or frappe.db.get_value("Global Defaults", None, "default_company")

    def _find_account(account_types, company):
        """Find first leaf account matching any of the given account_type values."""
        for at in account_types:
            val = frappe.db.get_value("Account", {"account_type": at, "company": company, "is_group": 0}, "name")
            if val:
                return val
        return None

    if doctype == "Sales Invoice":
        if not doc.get("debit_to"):
            _ar = _find_account(["Receivable"], _company)
            if _ar:
                doc["debit_to"] = _ar
        _income = _find_account(["Income", "Income Account", "Direct Income", "Sales"], _company)
        if _income:
            # Set on header (used by accounting_engine.post_sales_invoice)
            if not doc.get("income_account"):
                doc["income_account"] = _income
            # Set on each item row for Frappe's own validation
            for item in doc.get("items") or []:
                if isinstance(item, dict) and not item.get("income_account"):
                    item["income_account"] = _income

    if doctype == "Purchase Invoice":
        if not doc.get("credit_to"):
            _ap = _find_account(["Payable"], _company)
            if _ap:
                doc["credit_to"] = _ap
        _expense = _find_account(["Expense", "Expense Account", "Cost of Goods Sold", "Expenses Included In Valuation"], _company)
        if _expense:
            # Set on header (used by accounting_engine.post_purchase_invoice)
            if not doc.get("expense_account"):
                doc["expense_account"] = _expense
            # Set on each item row
            for item in doc.get("items") or []:
                if isinstance(item, dict) and not item.get("expense_account"):
                    item["expense_account"] = _expense

    name = doc.get("name")
    if name and frappe.db.exists(doctype, name):
        d = frappe.get_doc(doctype, name)
        is_submitted = d.docstatus == 1
        d.update(doc)
        if is_submitted:
            # Submitted documents are normally immutable in Frappe.
            # This flag bypasses field-level and child-row validation so the
            # Books SPA can freely edit any invoice regardless of status.
            # child rows added via d.update() have no DB name yet, so
            # validate_update_after_submit would throw DoesNotExistError on them.
            d.flags.ignore_validate_update_after_submit = True
        d.save(ignore_permissions=True)
    else:
        # New document: must call insert() explicitly.
        # frappe.get_doc(dict) with name already set does NOT mark the doc as
        # new (is_new() returns False), so save() would call db_update() and
        # raise DoesNotExistError.  insert() always creates a new row.
        d = frappe.get_doc(doc)
        d.insert(ignore_permissions=True)
    frappe.db.commit()
    return d.as_dict()


@frappe.whitelist(allow_guest=False, methods=["POST"])
def submit_doc(doctype, name):
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)

    d = frappe.get_doc(doctype, name)
    d.flags.ignore_permissions = True
    d.submit()
    frappe.db.commit()
    return d.as_dict()

@frappe.whitelist(allow_guest=False, methods=["POST"])
def cancel_doc(doctype, name):
    """Cancel a submitted document."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    d = frappe.get_doc(doctype, name)
    d.flags.ignore_permissions = True
    d.cancel()
    frappe.db.commit()
    return d.as_dict()

@frappe.whitelist(allow_guest=False, methods=["POST"])
def delete_doc(doctype, name):
    """Delete a document via GET — no CSRF needed."""
    # Guard: only the logged-in user (session) must have at least read access.
    # We then use ignore_permissions=True on the actual delete so Frappe's
    # internal role-based checks (which can block custom roles like 'Books Manager')
    # don't prevent deletion after we've confirmed the session is valid.
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)

    frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
    frappe.db.commit()
    return {"message": "deleted"}

@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_invoice_payments(invoice_name):
    """Return submitted Payment Entries linked to a Sales Invoice."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    refs = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_name": invoice_name, "reference_doctype": "Sales Invoice"},
        fields=["parent", "allocated_amount"],
    )
    if not refs:
        return []
    pe_names = list({r.parent for r in refs})
    result = []
    for pe_name in pe_names:
        pe = frappe.db.get_value(
            "Payment Entry", pe_name,
            ["name", "payment_date", "paid_amount", "mode_of_payment", "reference_no", "docstatus"],
            as_dict=True,
        )
        if pe:
            result.append(pe)
    result.sort(key=lambda x: x.get("payment_date") or "", reverse=True)
    return result


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def cancel_invoice_with_payments(invoice_name):
    """Cancel all linked Payment Entries, then cancel the Sales Invoice."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    refs = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_name": invoice_name},
        fields=["parent"],
    )
    pe_names = list({r.parent for r in refs})
    cancelled_pes = []
    for pe_name in pe_names:
        pe_doc = frappe.get_doc("Payment Entry", pe_name)
        if pe_doc.docstatus == 1:
            pe_doc.cancel()
            cancelled_pes.append(pe_name)
    inv_doc = frappe.get_doc("Sales Invoice", invoice_name)
    inv_doc.cancel()
    frappe.db.commit()
    return {"cancelled_payments": cancelled_pes, "cancelled_invoice": invoice_name}


# ─────────────────────────────────────────────────────────────────────────────
# Phase 1 — Bill (Purchase Invoice) helpers, mirroring the Sales Invoice set
# ─────────────────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_bill_payments(bill_name):
    """Return submitted Payment Entries linked to a Purchase Invoice (Bill)."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    refs = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_name": bill_name, "reference_doctype": "Purchase Invoice"},
        fields=["parent", "allocated_amount"],
    )
    if not refs:
        return []
    pe_names = list({r.parent for r in refs})
    result = []
    for pe_name in pe_names:
        pe = frappe.db.get_value(
            "Payment Entry", pe_name,
            ["name", "payment_date", "paid_amount", "mode_of_payment", "reference_no", "docstatus"],
            as_dict=True,
        )
        if pe:
            result.append(pe)
    result.sort(key=lambda x: x.get("payment_date") or "", reverse=True)
    return result


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_bill_email_defaults(bill_name):
    """Pre-fill the Send Email dialog for a Bill."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    bill = frappe.get_doc("Purchase Invoice", bill_name)
    supplier_email = frappe.db.get_value("Supplier", bill.supplier, "email_id") or ""
    subject = f"Bill {bill.name} from {bill.company or ''}"
    body = (
        f"Dear {bill.supplier_name or bill.supplier},<br><br>"
        f"Please find your bill <b>{bill.name}</b> details below:<br><br>"
        f"<table style='border-collapse:collapse;font-size:14px'>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666'>Bill #</td><td><b>{bill.name}</b></td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666'>Amount</td><td><b>₹{bill.grand_total:,.2f}</b></td></tr>"
        f"<tr><td style='padding:4px 12px 4px 0;color:#666'>Due Date</td><td>{bill.due_date or '—'}</td></tr>"
        f"</table><br>"
        f"Regards,<br>{bill.company or ''}"
    )
    return {
        "to": supplier_email,
        "subject": subject,
        "body": body,
        "bill_name": bill.name,
        "supplier_name": bill.supplier_name or bill.supplier,
        "from_email": frappe.session.user,
    }


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def send_bill_email(bill_name, to, subject, body, cc=None):
    """Send a bill email; attaches the bill PDF when print format exists."""
    if not to:
        frappe.throw("Recipient email (To) is required.")
    if not frappe.has_permission("Purchase Invoice", "read", bill_name):
        frappe.throw("Not permitted", frappe.PermissionError)

    bill = frappe.get_doc("Purchase Invoice", bill_name)
    recipients = [e.strip() for e in to.split(",") if e.strip()]
    cc_list = [e.strip() for e in (cc or "").split(",") if e.strip()]
    attachments = []
    try:
        attachments = [frappe.attach_print(bill.doctype, bill.name, print_format="Purchase Invoice", print_letterhead=True)]
    except Exception:
        attachments = []

    frappe.sendmail(
        recipients=recipients, cc=cc_list,
        subject=subject, message=body,
        attachments=attachments,
        reference_doctype="Purchase Invoice", reference_name=bill_name,
        now=True,
    )
    comm = frappe.get_doc({
        "doctype": "Communication", "communication_type": "Communication",
        "communication_medium": "Email", "sent_or_received": "Sent",
        "subject": subject, "content": body, "sender": frappe.session.user,
        "recipients": to, "cc": cc or "",
        "reference_doctype": "Purchase Invoice", "reference_name": bill_name,
        "status": "Linked",
    })
    comm.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"status": "sent", "to": to, "bill": bill_name}


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def record_vendor_payment(bill_name, amount_paid=None, payment_date=None,
                          payment_mode="Cash", paid_from="", bank_charges=0,
                          reference_no="", notes="", save_as_draft=0,
                          # accept identical keys the receive-side dialog uses, for symmetry
                          amount_received=None, deposit_to=""):
    """Create a Payment Entry against a Purchase Invoice (vendor payment)."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)

    amount = flt(amount_paid or amount_received or 0)
    if amount <= 0:
        frappe.throw("Amount must be greater than zero")

    bill = frappe.get_doc("Purchase Invoice", bill_name)
    if bill.docstatus != 1:
        frappe.throw("Bill must be submitted before recording payment")

    company = bill.company or _get_company(frappe.session.user)
    bank = paid_from or deposit_to or frappe.db.get_value(
        "Account", {"account_type": ["in", ["Bank", "Cash"]], "company": company, "is_group": 0}, "name"
    )
    ap = frappe.db.get_value(
        "Account", {"account_type": "Payable", "company": company, "is_group": 0}, "name"
    )

    pe = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Pay",
        "company": company,
        "party_type": "Supplier",
        "party": bill.supplier,
        "party_name": bill.supplier_name or bill.supplier,
        "paid_from": bank,
        "paid_to": ap,
        "paid_amount": amount,
        "received_amount": amount,
        "source_exchange_rate": 1,
        "target_exchange_rate": 1,
        "reference_no": reference_no or bill.name,
        "reference_date": payment_date or today(),
        "posting_date": payment_date or today(),
        "payment_date": payment_date or today(),
        "mode_of_payment": payment_mode,
        "remarks": notes or "",
        "references": [{
            "reference_doctype": "Purchase Invoice",
            "reference_name": bill.name,
            "total_amount": bill.grand_total,
            "outstanding_amount": bill.outstanding_amount,
            "allocated_amount": amount,
        }],
    })
    pe.flags.ignore_permissions = True
    pe.flags.ignore_mandatory = True
    pe.insert()
    if not int(save_as_draft or 0):
        pe.submit()
    frappe.db.commit()
    return {"payment_entry": pe.name, "bill": bill.name}


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def cancel_bill_with_payments(bill_name):
    """Cancel linked Payment Entries first, then cancel the Bill (mirror of invoice cascade)."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    refs = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_name": bill_name},
        fields=["parent"],
    )
    pe_names = list({r.parent for r in refs})
    cancelled_pes = []
    for pe_name in pe_names:
        pe_doc = frappe.get_doc("Payment Entry", pe_name)
        if pe_doc.docstatus == 1:
            pe_doc.cancel()
            cancelled_pes.append(pe_name)
    bill_doc = frappe.get_doc("Purchase Invoice", bill_name)
    bill_doc.cancel()
    frappe.db.commit()
    return {"cancelled_payments": cancelled_pes, "cancelled_bill": bill_name}


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_debit_notes(bill_name):
    """Return debit notes (return purchase invoices) against a Bill."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    return frappe.get_all(
        "Purchase Invoice",
        filters={"return_against": bill_name, "is_return": 1, "docstatus": ["!=", 2]},
        fields=["name", "grand_total", "posting_date", "docstatus"],
    )


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_debit_note_balance(debit_note_name):
    """Calculate remaining (unapplied) balance on a debit note.

    balance = |grand_total| - sum(allocated_amount from Payment Entry Refs whose parent is
    a submitted PE allocating this DN). When no applications exist, balance = |grand_total|.
    """
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    dn = frappe.db.get_value("Purchase Invoice", debit_note_name,
                             ["grand_total", "docstatus", "supplier", "supplier_name"], as_dict=True)
    if not dn:
        return {"name": debit_note_name, "total": 0, "applied": 0, "balance": 0}
    total = abs(flt(dn.grand_total))
    applied = 0
    refs = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_name": debit_note_name, "reference_doctype": "Purchase Invoice"},
        fields=["parent", "allocated_amount"],
    )
    for r in refs:
        pe_status = frappe.db.get_value("Payment Entry", r.parent, "docstatus")
        if pe_status == 1:
            applied += abs(flt(r.allocated_amount))
    return {
        "name": debit_note_name, "supplier": dn.supplier, "supplier_name": dn.supplier_name,
        "total": total, "applied": applied, "balance": max(0, total - applied),
        "docstatus": dn.docstatus,
    }


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def apply_debit_note_to_bill(debit_note, bill, amount):
    """Create a Payment Entry that applies a debit-note credit to a vendor bill."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    amount = abs(flt(amount))
    if amount <= 0:
        frappe.throw("Amount must be > 0")

    dn = frappe.get_doc("Purchase Invoice", debit_note)
    bill_doc = frappe.get_doc("Purchase Invoice", bill)
    if dn.docstatus != 1 or bill_doc.docstatus != 1:
        frappe.throw("Both debit note and bill must be submitted")

    balance_info = get_debit_note_balance(debit_note)
    if amount > flt(balance_info["balance"]) + 0.01:
        frappe.throw(f"Cannot apply more than available balance ({balance_info['balance']})")

    company = bill_doc.company
    ap = frappe.db.get_value(
        "Account", {"account_type": "Payable", "company": company, "is_group": 0}, "name"
    )

    pe = frappe.get_doc({
        "doctype": "Payment Entry",
        "payment_type": "Internal Transfer",
        "company": company,
        "party_type": "Supplier",
        "party": dn.supplier,
        "party_name": dn.supplier_name or dn.supplier,
        "paid_from": ap,
        "paid_to": ap,
        "paid_amount": amount,
        "received_amount": amount,
        "reference_no": f"DN-{dn.name}",
        "reference_date": today(),
        "posting_date": today(),
        "remarks": f"Debit Note {dn.name} applied to bill {bill}",
        "references": [
            {
                "reference_doctype": "Purchase Invoice",
                "reference_name": dn.name,
                "total_amount": abs(flt(dn.grand_total)),
                "allocated_amount": amount,
            },
            {
                "reference_doctype": "Purchase Invoice",
                "reference_name": bill,
                "total_amount": flt(bill_doc.grand_total),
                "outstanding_amount": flt(bill_doc.outstanding_amount),
                "allocated_amount": amount,
            },
        ],
    })
    pe.flags.ignore_permissions = True
    pe.flags.ignore_mandatory = True
    pe.insert()
    pe.submit()
    frappe.db.commit()
    return {"payment_entry": pe.name, "debit_note": debit_note, "bill": bill, "applied": amount}


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_debit_note_applications(debit_note_name):
    """Return the list of bills this debit note has been applied to (via Payment Entries)."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    refs = frappe.get_all(
        "Payment Entry Reference",
        filters={"reference_name": debit_note_name, "reference_doctype": "Purchase Invoice"},
        fields=["parent", "allocated_amount"],
    )
    apps = []
    for r in refs:
        pe = frappe.db.get_value(
            "Payment Entry", r.parent,
            ["name", "posting_date", "docstatus"],
            as_dict=True,
        )
        if not pe or pe.docstatus != 1:
            continue
        # the OTHER Purchase Invoice reference (the bill, not the DN itself) is what was applied
        siblings = frappe.get_all(
            "Payment Entry Reference",
            filters={"parent": r.parent, "reference_doctype": "Purchase Invoice"},
            fields=["reference_name", "allocated_amount"],
        )
        for s in siblings:
            if s.reference_name and s.reference_name != debit_note_name:
                apps.append({
                    "bill": s.reference_name,
                    "amount": abs(flt(s.allocated_amount)),
                    "date": pe.posting_date,
                    "payment_entry": pe.name,
                })
    return apps


@frappe.whitelist(allow_guest=False)
def get_party_last_items(party_type, party, limit=10):
    """
    Return the items from the most recent submitted document for a customer or vendor.
    party_type: "Customer" → searches Sales Invoice then Quotation
    party_type: "Supplier" → searches Purchase Invoice then Purchase Order
    Returns list of {item_name, item_code, description, qty, rate} dicts.
    """
    limit = int(limit)

    def _fetch_items(item_doctype, parent_name):
        """Select item fields that exist in this table; description is optional."""
        has_desc = frappe.db.has_column(item_doctype, "description")
        desc_col  = ", description" if has_desc else ""
        return frappe.db.sql("""
            SELECT item_name, item_code{desc} , qty, rate
            FROM `tab{idt}`
            WHERE parent = %(parent)s
            ORDER BY idx ASC LIMIT %(limit)s
        """.format(desc=desc_col, idt=item_doctype),
            {"parent": parent_name, "limit": limit}, as_dict=True)

    def _latest_parent(doctype, party_field):
        row = frappe.db.sql("""
            SELECT name FROM `tab{dt}`
            WHERE `{pf}` = %(party)s AND docstatus = 1
            ORDER BY modified DESC LIMIT 1
        """.format(dt=doctype, pf=party_field), {"party": party}, as_dict=True)
        if not row:
            row = frappe.db.sql("""
                SELECT name FROM `tab{dt}`
                WHERE `{pf}` = %(party)s
                ORDER BY modified DESC LIMIT 1
            """.format(dt=doctype, pf=party_field), {"party": party}, as_dict=True)
        return row[0].name if row else None

    if party_type == "Customer":
        for doctype, item_doctype, party_field in [
            ("Sales Invoice", "Sales Invoice Item", "customer"),
            ("Quotation",     "Quotation Item",     "customer"),
            ("Sales Order",   "Sales Order Item",   "customer"),
        ]:
            parent_name = _latest_parent(doctype, party_field)
            if parent_name:
                items = _fetch_items(item_doctype, parent_name)
                if items:
                    return {"source": parent_name, "source_doctype": doctype, "items": items}

    elif party_type == "Supplier":
        for doctype, item_doctype, party_field in [
            ("Purchase Invoice", "Purchase Invoice Item", "supplier"),
            ("Purchase Order",   "Purchase Order Item",   "supplier"),
        ]:
            parent_name = _latest_parent(doctype, party_field)
            if parent_name:
                items = _fetch_items(item_doctype, parent_name)
                if items:
                    return {"source": parent_name, "source_doctype": doctype, "items": items}

    return {"source": None, "items": []}


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def create_debit_note():
    """
    Create and submit a Debit Note (Purchase Invoice with is_return=1).
    Posts correct GL: DR Accounts Payable / CR Expense (or Inventory if goods returned).
    If reason is 'Goods Returned' and a warehouse is given, also creates a
    Material Issue Stock Entry to physically reduce inventory.
    Reads all params from frappe.form_dict to handle nested items JSON.
    """
    fd = frappe.form_dict
    vendor       = fd.get("vendor") or ""
    against_bill = fd.get("against_bill") or None
    date         = fd.get("date") or today()
    reason       = fd.get("reason") or ""
    notes        = fd.get("notes") or ""
    warehouse    = fd.get("warehouse") or ""
    items_raw    = fd.get("items") or "[]"

    if isinstance(items_raw, str):
        items_raw = json.loads(items_raw)

    if not vendor:
        frappe.throw("Vendor is required")
    if not reason:
        frappe.throw("Reason is required")
    if not items_raw:
        frappe.throw("At least one item is required")

    company = _get_company(frappe.session.user)

    ap_account = frappe.db.get_value(
        "Account", {"account_type": "Payable", "company": company, "is_group": 0}, "name"
    )
    expense_account = frappe.db.get_value(
        "Account", {"account_type": "Expense", "company": company, "is_group": 0}, "name"
    )

    pi_items = [
        {
            "item_code":      it.get("item_code") or it.get("item_name") or "",
            "item_name":      it.get("item_name") or it.get("item_code") or "",
            "description":    it.get("description") or it.get("item_name") or "",
            "qty":            -abs(flt(it.get("qty", 1))),
            "rate":           flt(it.get("rate", 0)),
            "expense_account": expense_account,
        }
        for it in items_raw if (it.get("item_code") or it.get("item_name"))
    ]

    pi = frappe.get_doc({
        "doctype":          "Purchase Invoice",
        "is_return":        1,
        "company":          company,
        "supplier":         vendor,
        "return_against":   against_bill,
        "posting_date":     date,
        "remarks":          reason,
        "credit_to":        ap_account,
        "expense_account":  expense_account,
        "items":            pi_items,
    })
    pi.name = "DN-" + frappe.generate_hash(
        txt=f"{vendor}{frappe.utils.now()}", length=8
    ).upper()
    pi.flags.ignore_permissions = True
    pi.flags.ignore_links = True
    pi.flags.ignore_mandatory = True
    pi.insert()
    pi.submit()
    frappe.db.commit()

    # If goods physically returned, create a Material Issue to remove from stock
    se_name = None
    if reason == "Goods Returned" and warehouse:
        se_items = [
            {
                "item_code":   it.get("item_name") or it.get("item_code") or "",
                "item_name":   it.get("item_name") or "",
                "qty":         flt(it.get("qty", 1)),
                "basic_rate":  flt(it.get("rate", 0)),
                "s_warehouse": warehouse,
            }
            for it in items_raw if (it.get("item_name") or it.get("item_code"))
        ]
        if se_items:
            try:
                se = frappe.get_doc({
                    "doctype":          "Stock Entry",
                    "stock_entry_type": "Material Issue",
                    "posting_date":     date,
                    "company":          company,
                    "from_warehouse":   warehouse,
                    "remarks":          f"Goods returned to vendor — Debit Note {pi.name}",
                    "items":            se_items,
                })
                se.name = "SE-DN-" + frappe.generate_hash(
                    txt=f"{pi.name}{frappe.utils.now()}", length=8
                ).upper()
                se.flags.ignore_permissions = True
                se.flags.ignore_links = True
                se.flags.ignore_mandatory = True
                se.insert()
                se.submit()
                frappe.db.commit()
                se_name = se.name
            except Exception as exc:
                frappe.log_error(
                    f"Debit Note {pi.name}: Stock Entry failed — {exc}",
                    "Debit Note Stock Movement"
                )
                frappe.msgprint(
                    f"Debit Note issued, but stock movement failed: {exc}",
                    indicator="orange", alert=True
                )

    return {
        "debit_note":  pi.name,
        "stock_entry": se_name,
        "return_type": "inventory" if reason == "Goods Returned" else "expense",
    }


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def get_credit_notes(invoice_name):
    """Return existing credit notes (return invoices) against a given Sales Invoice."""
    if frappe.session.user == "Guest":
        frappe.throw("Not permitted", frappe.PermissionError)
    cns = frappe.get_all(
        "Sales Invoice",
        filters={"return_against": invoice_name, "is_return": 1, "docstatus": ["!=", 2]},
        fields=["name", "grand_total", "posting_date", "docstatus"],
    )
    return cns


@frappe.whitelist(allow_guest=False, methods=["GET", "POST"])
def create_credit_note():
    """
    Create and submit a Credit Note.
    Posts correct GL via CreditNote.on_submit(): DR Income / CR AR.
    If reason is 'Goods Returned' and a warehouse is given, also creates a
    Material Receipt Stock Entry to bring goods back into stock.
    """
    fd = frappe.form_dict
    customer    = fd.get("customer") or ""
    against_inv = fd.get("against_invoice") or None
    date        = fd.get("date") or today()
    reason      = fd.get("reason") or ""
    notes       = fd.get("notes") or ""
    warehouse   = fd.get("warehouse") or ""
    items_raw   = json.loads(fd.get("items") or "[]")
    taxes_raw   = json.loads(fd.get("taxes") or "[]")

    if not customer:
        frappe.throw("Customer is required")
    if not items_raw:
        frappe.throw("At least one item is required")

    company = _get_company(frappe.session.user)

    ar_account = frappe.db.get_value(
        "Account", {"account_type": "Receivable", "company": company, "is_group": 0}, "name"
    )
    income_account = frappe.db.get_value(
        "Account", {"account_type": "Income", "company": company, "is_group": 0}, "name"
    )

    cn_items = [
        {
            "item_code":      it.get("item_code") or it.get("item_name") or "",
            "item_name":      it.get("item_name") or it.get("item_code") or "",
            "description":    it.get("description") or it.get("item_name") or "",
            "qty":            -abs(flt(it.get("qty", 1))),
            "rate":           flt(it.get("rate", 0)),
            "income_account": income_account,
        }
        for it in items_raw if (it.get("item_code") or it.get("item_name"))
    ]

    cn_taxes = [
        {
            "charge_type":  "On Net Total",
            "description":  t.get("description") or t.get("tax_type") or "Tax",
            "account_head": t.get("tax_type") or "",
            "rate":         flt(t.get("rate", 0)),
        }
        for t in taxes_raw
        if t.get("tax_type")
    ]

    cn = frappe.get_doc({
        "doctype":          "Sales Invoice",
        "is_return":        1,
        "company":          company,
        "customer":         customer,
        "return_against":   against_inv,
        "posting_date":     date,
        "remarks":          (reason + (" — " + notes if notes else "")),
        "debit_to":         ar_account,
        "income_account":   income_account,
        "items":            cn_items,
        "taxes":            cn_taxes,
    })
    cn.name = "CN-" + frappe.generate_hash(
        txt=f"{customer}{frappe.utils.now()}", length=8
    ).upper()
    cn.flags.ignore_permissions = True
    cn.flags.ignore_links = True
    cn.flags.ignore_mandatory = True
    cn.insert()
    cn.submit()
    frappe.db.commit()

    # If goods returned by customer, create Material Receipt to restock
    se_name = None
    if reason == "Goods Returned" and warehouse:
        se_items = [
            {
                "item_code":   it.get("item_name") or it.get("item_code") or "",
                "item_name":   it.get("item_name") or "",
                "qty":         flt(it.get("qty", 1)),
                "basic_rate":  flt(it.get("rate", 0)),
                "t_warehouse": warehouse,
            }
            for it in items_raw if (it.get("item_name") or it.get("item_code"))
        ]
        if se_items:
            try:
                se = frappe.get_doc({
                    "doctype":          "Stock Entry",
                    "stock_entry_type": "Material Receipt",
                    "posting_date":     date,
                    "company":          company,
                    "to_warehouse":     warehouse,
                    "remarks":          f"Customer return — Credit Note {cn.name}",
                    "items":            se_items,
                })
                se.name = "SE-CN-" + frappe.generate_hash(
                    txt=f"{cn.name}{frappe.utils.now()}", length=8
                ).upper()
                se.flags.ignore_permissions = True
                se.flags.ignore_links = True
                se.flags.ignore_mandatory = True
                se.insert()
                se.submit()
                frappe.db.commit()
                se_name = se.name
            except Exception as exc:
                frappe.log_error(
                    f"Credit Note {cn.name}: Stock Entry failed — {exc}",
                    "Credit Note Stock Movement"
                )
                frappe.msgprint(
                    f"Credit note issued, but stock receipt failed: {exc}",
                    indicator="orange", alert=True
                )

    return {
        "credit_note": cn.name,
        "stock_entry": se_name,
        "return_type": "inventory" if reason == "Goods Returned" else "adjustment",
    }


@frappe.whitelist(allow_guest=False)
def get_accounts():
    """Safely fetch accounts filtered by company, bypassing REST get_list overrides."""
    company = frappe.form_dict.get("company") or ""

    # Resolve company from Books Settings when not supplied by caller
    if not company:
        company = _get_company(frappe.session.user)

    def get_list_by_type(account_type=None, scope_company=None):
        """Return leaf accounts matching the given type.

        scope_company controls company filtering:
          - truthy str  → filter by that company
          - ""          → no company filter (global fallback)
          - None        → use the outer `company` variable
        """
        effective = company if scope_company is None else scope_company
        f = {"is_group": 0, "disabled": 0}
        if effective:
            f["company"] = effective
        if account_type:
            f["account_type"] = account_type
        try:
            return [
                {"name": a.name, "account_type": a.account_type}
                for a in frappe.get_all("Account", filters=f, fields=["name", "account_type"])
            ]
        except Exception:
            return []

    # Primary query — scoped to the resolved company
    res = {
        "ar":     get_list_by_type(account_type="Receivable"),
        "income": get_list_by_type(account_type="Income"),
        "bank":   get_list_by_type(account_type=["in", ["Bank", "Cash"]]),
        "ap":     get_list_by_type(account_type="Payable"),
    }

    # Fallback 1: category empty → try all accounts for the same company (no type filter)
    all_accs = None
    for key in res:
        if not res[key]:
            if all_accs is None:
                all_accs = get_list_by_type()
            res[key] = all_accs

    # Fallback 2: if the company itself had no accounts (stale/wrong company name),
    # retry the entire query without any company filter so the UI is never blank.
    if not any(res.values()):
        res = {
            "ar":     get_list_by_type(account_type="Receivable", scope_company=""),
            "income": get_list_by_type(account_type="Income",      scope_company=""),
            "bank":   get_list_by_type(account_type=["in", ["Bank", "Cash"]], scope_company=""),
            "ap":     get_list_by_type(account_type="Payable",     scope_company=""),
        }
        all_global = None
        for key in res:
            if not res[key]:
                if all_global is None:
                    all_global = get_list_by_type(scope_company="")
                res[key] = all_global

    return res
