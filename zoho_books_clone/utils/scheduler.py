import frappe
from frappe.utils import today, add_days, getdate, flt


def send_payment_reminders():
    """
    Per-company payment reminders driven by Books Settings.
    Sends:
      - "upcoming" reminder: N days before due_date (if reminder_days_before > 0)
      - "overdue" reminder: N days after due_date (if reminder_days_after > 0)
    Only runs when send_payment_reminders = 1 in Books Settings.
    """
    try:
        settings = frappe.get_single("Books Settings")
    except Exception:
        return

    if not settings.get("send_payment_reminders"):
        return

    days_before = int(settings.get("reminder_days_before") or 3)
    days_after  = int(settings.get("reminder_days_after")  or 7)
    company     = settings.get("default_company") or ""

    base_filters = {"docstatus": 1, "outstanding_amount": [">", 0]}
    if company:
        base_filters["company"] = company

    fields = ["name", "customer", "customer_name", "grand_total",
              "outstanding_amount", "due_date", "company"]

    sent = set()

    # 1. Upcoming — due in exactly N days
    if days_before > 0:
        remind_date = add_days(today(), days_before)
        upcoming = frappe.get_all(
            "Sales Invoice",
            filters={**base_filters, "due_date": remind_date},
            fields=fields,
        )
        for inv in upcoming:
            _send_reminder(inv, kind="upcoming", sent=sent)

    # 2. Overdue — due exactly N days ago
    if days_after > 0:
        overdue_date = add_days(today(), -days_after)
        overdue = frappe.get_all(
            "Sales Invoice",
            filters={**base_filters, "due_date": overdue_date},
            fields=fields,
        )
        for inv in overdue:
            _send_reminder(inv, kind="overdue", sent=sent)

    # 3. Also catch anything past due with no recent reminder sent
    #    (belt-and-suspenders for invoices that slipped through)
    very_overdue = frappe.get_all(
        "Sales Invoice",
        filters={**base_filters, "due_date": ["<", today()]},
        fields=fields,
    )
    for inv in very_overdue:
        _send_reminder(inv, kind="overdue", sent=sent)


def _send_reminder(inv, kind, sent):
    key = (inv["name"], kind)
    if key in sent:
        return
    sent.add(key)

    email = frappe.db.get_value("Customer", inv["customer"], "email_id") or ""
    if not email:
        return

    name     = inv["name"]
    cname    = inv["customer_name"] or inv["customer"]
    amount   = flt(inv["outstanding_amount"])
    due      = inv["due_date"]
    company  = inv.get("company") or ""

    if kind == "upcoming":
        subject = f"Upcoming Payment Due – Invoice {name}"
        body = (
            f"Dear {cname},<br><br>"
            f"This is a friendly reminder that invoice <b>{name}</b> of <b>₹{amount:,.2f}</b> "
            f"is due on <b>{due}</b>.<br>"
            "Please arrange payment before the due date to avoid any late fees.<br><br>"
            f"Regards,<br>{company}"
        )
    else:
        subject = f"Payment Overdue – Invoice {name}"
        body = (
            f"Dear {cname},<br><br>"
            f"Invoice <b>{name}</b> of <b>₹{amount:,.2f}</b> was due on <b>{due}</b> "
            "and is now overdue.<br>"
            "Please arrange payment at your earliest convenience.<br><br>"
            f"Regards,<br>{company}"
        )

    try:
        frappe.sendmail(
            recipients=[email],
            subject=subject,
            message=body,
            reference_doctype="Sales Invoice",
            reference_name=name,
        )
    except Exception as e:
        frappe.log_error(str(e), f"Payment reminder failed: {name}")


def generate_monthly_reports():
    """Placeholder: generate and email monthly P&L to admin."""
    pass
