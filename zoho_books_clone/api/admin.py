from __future__ import annotations
"""
Administration API — users, roles, profile, notifications, audit log.
All endpoints require an authenticated session (allow_guest=False by default).
"""
import secrets
import string

import frappe
from frappe import _
from frappe.utils import today, now_datetime, getdate, flt
from frappe.utils.password import update_password, check_password


BOOKS_ROLES = ("Books Admin", "Books Manager", "Accountant", "Books Viewer")
MODULE_FIELDS = (
    "mod_invoices", "mod_bills", "mod_payments", "mod_banking",
    "mod_inventory", "mod_accounts", "mod_reports", "mod_customers",
    "mod_taxes", "mod_admin",
)


def _require_admin():
    """Allow Books Admin, System Manager, or Administrator."""
    if frappe.session.user == "Administrator":
        return
    roles = set(frappe.get_roles(frappe.session.user))
    if roles & {"System Manager", "Books Admin"}:
        return
    # Books Manager can read but not invite — see _require_company_admin
    frappe.throw(_("You do not have permission to perform this action"), frappe.PermissionError)


def _require_company_admin() -> str:
    """Stricter check: must be flagged as company admin in Books Company Member.
    Returns the admin's company name."""
    user = frappe.session.user
    if user == "Administrator":
        return frappe.db.get_value("Books Company Member", {}, "company") or ""
    row = frappe.db.get_value(
        "Books Company Member",
        {"user": user},
        ["company", "is_company_admin", "books_role"],
        as_dict=True,
    )
    if not row:
        frappe.throw(_("Your user is not linked to any Books Company."), frappe.PermissionError)
    if not (row.is_company_admin or row.books_role == "Books Admin"):
        frappe.throw(_("Only the company admin can perform this action."), frappe.PermissionError)
    return row.company


def _gen_temp_password(n: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(secrets.choice(alphabet) for _ in range(n))


# ─── Users (scoped to admin's company) ───────────────────────────────────────

def _company_member_row(user: str) -> dict | None:
    return frappe.db.get_value(
        "Books Company Member",
        {"user": user},
        ["name", "company", "books_role", "is_company_admin", *MODULE_FIELDS],
        as_dict=True,
    )


@frappe.whitelist()
def get_users_list():
    """Return users that belong to the current admin's company."""
    company = _require_company_admin()
    members = frappe.get_all(
        "Books Company Member",
        filters={"company": company},
        fields=["user", "books_role", "is_company_admin", "joined_on", *MODULE_FIELDS],
        ignore_permissions=True,
        order_by="joined_on desc",
        limit=500,
    )
    if not members:
        return []

    user_names = [m["user"] for m in members]
    user_rows = {
        u["name"]: u
        for u in frappe.get_all(
            "User",
            filters=[["name", "in", user_names]],
            fields=["name", "full_name", "email", "enabled", "last_login",
                    "creation", "user_image"],
            ignore_permissions=True,
        )
    }

    out = []
    for m in members:
        u = user_rows.get(m["user"], {})
        out.append({
            "name": m["user"],
            "email": m["user"],
            "full_name": u.get("full_name") or "",
            "user_image": u.get("user_image") or "",
            "enabled": bool(u.get("enabled")),
            "last_login": u.get("last_login"),
            "creation": u.get("creation"),
            "books_role": m["books_role"],
            "is_company_admin": bool(m["is_company_admin"]),
            "modules": {f.removeprefix("mod_"): bool(m[f]) for f in MODULE_FIELDS},
            "joined_on": m["joined_on"],
        })
    return out


@frappe.whitelist(methods=["POST"])
def invite_user(email, first_name, last_name="", role="Books Viewer", modules=None):
    """Create a new user, link them to the admin's company, and email login credentials.
    `modules` is an optional dict like {"invoices": 1, "banking": 0, ...}."""
    company = _require_company_admin()
    email = email.strip().lower()

    if frappe.db.exists("User", email):
        frappe.throw(_("User {0} already exists").format(email))

    if role not in BOOKS_ROLES:
        frappe.throw(_("Invalid role: {0}").format(role))

    if isinstance(modules, str):
        try:
            import json
            modules = json.loads(modules)
        except Exception:
            modules = {}
    modules = modules or {}

    temp_password = _gen_temp_password()

    # ── Create User
    user = frappe.new_doc("User")
    user.email = email
    user.first_name = (first_name or "").strip() or email.split("@")[0]
    user.last_name = (last_name or "").strip()
    user.user_type = "System User"
    user.send_welcome_email = 0  # we send our own via system SMTP
    user.enabled = 1
    user.new_password = temp_password
    user.append("roles", {"role": role})
    user.insert(ignore_permissions=True)

    # ── Link to company
    member = frappe.new_doc("Books Company Member")
    member.user = email
    member.company = company
    member.books_role = role
    member.is_company_admin = 1 if role == "Books Admin" else 0
    member.invited_by = frappe.session.user

    if role == "Books Admin":
        for f in MODULE_FIELDS:
            member.set(f, 1)
    else:
        # Apply requested module toggles, defaulting to the doctype's default for unspecified fields
        for f in MODULE_FIELDS:
            key = f.removeprefix("mod_")
            if key in modules:
                member.set(f, 1 if int(modules[key]) else 0)

    member.insert(ignore_permissions=True)

    # Per-user company default
    try:
        frappe.defaults.set_user_default("company", company, user=email)
    except Exception:
        pass

    frappe.db.commit()

    # ── Send invite email via system SMTP
    _send_invite_email(email, user.first_name, company, temp_password, role)

    return {"success": True, "user": email, "company": company, "role": role}


def _send_invite_email(email: str, first_name: str, company: str, temp_password: str, role: str):
    from zoho_books_clone.utils.email_system import send_system_email
    site_url = frappe.utils.get_url()
    html = f"""
<div style="font-family:'DM Sans',sans-serif;max-width:520px;margin:0 auto;padding:32px 24px;background:#fff">
  <h2 style="color:#1A237E;font-size:22px;margin-bottom:8px">Welcome to Books, {first_name}!</h2>
  <p style="color:#555;line-height:1.6">
    You've been invited to join <b>{company}</b> on Books with the role <b>{role}</b>.
  </p>
  <div style="background:#F5F7FA;border-radius:10px;padding:20px;margin:20px 0">
    <div style="font-size:13px;color:#666;margin-bottom:6px">Sign in URL</div>
    <div style="font-size:15px;color:#0D1117;margin-bottom:14px"><a href="{site_url}/login" style="color:#3949AB">{site_url}/login</a></div>
    <div style="font-size:13px;color:#666;margin-bottom:6px">Email</div>
    <div style="font-size:15px;color:#0D1117;margin-bottom:14px"><b>{email}</b></div>
    <div style="font-size:13px;color:#666;margin-bottom:6px">Temporary password</div>
    <div style="font-size:18px;color:#1A237E;font-family:monospace;letter-spacing:2px"><b>{temp_password}</b></div>
  </div>
  <p style="color:#555;font-size:14px;line-height:1.6">
    Please sign in and change your password from <b>Profile → Change Password</b> immediately.
  </p>
</div>"""
    send_system_email(
        to=email,
        subject=f"You've been invited to {company} on Books",
        html=html,
        text_fallback=f"You've been invited to {company} on Books. Sign in at {site_url}/login with email {email} and temporary password {temp_password}. Please change your password after signing in.",
    )


@frappe.whitelist(methods=["POST"])
def update_user_role(user, role):
    """Replace all Books roles on a user with the given role.
    Restricted to users in the admin's company."""
    company = _require_company_admin()
    if role not in BOOKS_ROLES:
        frappe.throw(_("Invalid role"))

    member_name = frappe.db.get_value("Books Company Member", {"user": user, "company": company}, "name")
    if not member_name:
        frappe.throw(_("User {0} is not part of your company.").format(user))

    member = frappe.get_doc("Books Company Member", member_name)
    member.books_role = role
    if role == "Books Admin":
        member.is_company_admin = 1
        for f in MODULE_FIELDS:
            member.set(f, 1)
    member.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist(methods=["POST"])
def set_user_permissions(user, modules):
    """Set module-level access toggles for a user in the admin's company.
    `modules` is a dict like {'invoices': 1, 'banking': 0}."""
    company = _require_company_admin()

    if isinstance(modules, str):
        import json
        modules = json.loads(modules)
    modules = modules or {}

    member_name = frappe.db.get_value("Books Company Member", {"user": user, "company": company}, "name")
    if not member_name:
        frappe.throw(_("User {0} is not part of your company.").format(user))

    member = frappe.get_doc("Books Company Member", member_name)
    if member.books_role == "Books Admin":
        frappe.throw(_("Books Admin always has full module access; toggles cannot be set."))

    for f in MODULE_FIELDS:
        key = f.removeprefix("mod_")
        if key in modules:
            member.set(f, 1 if int(modules[key]) else 0)

    member.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist(methods=["POST"])
def toggle_user_active(user, enabled):
    """Enable or disable a user account (must be in admin's company)."""
    company = _require_company_admin()
    if user in ("Administrator", "Guest"):
        frappe.throw(_("Cannot disable this user"))
    if not frappe.db.exists("Books Company Member", {"user": user, "company": company}):
        frappe.throw(_("User {0} is not part of your company.").format(user))
    enabled_int = 1 if str(enabled).lower() in ("1", "true") else 0
    frappe.db.set_value("User", user, "enabled", enabled_int)
    frappe.db.commit()
    return {"success": True}


@frappe.whitelist(methods=["POST"])
def remove_user_from_company(user):
    """Remove a user from the admin's company (deletes the membership row, disables the user)."""
    company = _require_company_admin()
    if user == frappe.session.user:
        frappe.throw(_("You cannot remove yourself."))

    member_name = frappe.db.get_value("Books Company Member", {"user": user, "company": company}, "name")
    if not member_name:
        frappe.throw(_("User {0} is not part of your company.").format(user))

    frappe.delete_doc("Books Company Member", member_name, ignore_permissions=True, force=True)
    frappe.db.set_value("User", user, "enabled", 0)
    frappe.db.commit()
    return {"success": True}


# ─── Backwards-compat aliases (the live SPA was built against earlier names) ──

@frappe.whitelist()
def get_company_members():
    """Alias for get_users_list — kept so the existing Team Members page works."""
    return get_users_list()


@frappe.whitelist(methods=["POST"])
def invite_member(email, first_name, last_name="", role="Books Viewer", password=None, modules=None):
    """Alias for invite_user. The legacy SPA also passes a `password` field, which we ignore
    (we always generate a temp password and email it via system SMTP). All other args pass through."""
    return invite_user(email=email, first_name=first_name, last_name=last_name,
                       role=role, modules=modules)


@frappe.whitelist(methods=["POST"])
def remove_member(user_email):
    """Alias for remove_user_from_company — legacy SPA uses `user_email` arg name."""
    return remove_user_from_company(user=user_email)


# ─── Profile ──────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_profile():
    """Return the current user's profile fields."""
    user = frappe.session.user
    doc = frappe.get_doc("User", user)
    return {
        "email": doc.email,
        "first_name": doc.first_name or "",
        "last_name": doc.last_name or "",
        "full_name": doc.full_name or "",
        "phone": doc.phone or "",
        "mobile_no": doc.mobile_no or "",
        "user_image": doc.user_image or "",
        "language": doc.language or "en",
        "time_zone": doc.time_zone or "",
    }


@frappe.whitelist()
def update_profile(first_name, last_name="", phone="", mobile_no=""):
    """Update the current user's profile."""
    user = frappe.session.user
    doc = frappe.get_doc("User", user)
    doc.first_name = first_name.strip()
    doc.last_name = (last_name or "").strip()
    doc.phone = phone or ""
    doc.mobile_no = mobile_no or ""
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "full_name": doc.full_name}


@frappe.whitelist()
def change_password(old_password, new_password):
    """Change the current user's password after verifying the old one."""
    user = frappe.session.user
    try:
        check_password(user, old_password)
    except Exception:
        frappe.throw(_("Current password is incorrect"))
    if len(new_password) < 8:
        frappe.throw(_("New password must be at least 8 characters"))
    update_password(user, new_password)
    frappe.db.commit()
    return {"success": True}


# ─── Notifications ────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_notifications():
    """Return a list of actionable notifications for the current user."""
    notifs = []

    try:
        company = frappe.db.get_single_value("Books Settings", "default_company") or ""
    except Exception:
        company = ""

    def _f(base):
        return base + ([["company", "=", company]] if company else [])

    # Overdue Sales Invoices
    try:
        for inv in frappe.get_all(
            "Sales Invoice",
            filters=_f([["docstatus","=",1],["outstanding_amount",">",0],["due_date","<",today()]]),
            fields=["name","customer_name","outstanding_amount","due_date"],
            limit=5, ignore_permissions=True,
        ):
            notifs.append({
                "type":"overdue_invoice","icon":"alert","color":"#C92A2A","bg":"#FFF5F5",
                "title":"Overdue Invoice",
                "body":f"{inv['name']} — {inv['customer_name']} — ₹{flt(inv['outstanding_amount']):,.2f}",
                "link":f"#/invoices/{inv['name']}","date":str(inv["due_date"]),
            })
    except Exception:
        pass

    # Bills due today or overdue
    try:
        for bill in frappe.get_all(
            "Purchase Invoice",
            filters=_f([["docstatus","=",1],["outstanding_amount",">",0],["due_date","<=",today()]]),
            fields=["name","supplier_name","outstanding_amount","due_date"],
            limit=5, ignore_permissions=True,
        ):
            notifs.append({
                "type":"bill_due","icon":"purchase","color":"#E67700","bg":"#FFF8F0",
                "title":"Bill Due",
                "body":f"{bill['name']} — {bill['supplier_name']} — ₹{flt(bill['outstanding_amount']):,.2f}",
                "link":"#/purchases","date":str(bill["due_date"]),
            })
    except Exception:
        pass

    # Reorder alerts
    try:
        for r in frappe.db.sql("""
            SELECT b.item_code, b.actual_qty, i.reorder_level
            FROM `tabBin` b JOIN `tabItem` i ON i.name=b.item_code
            WHERE i.reorder_level > 0 AND b.actual_qty <= i.reorder_level LIMIT 3
        """, as_dict=True):
            notifs.append({
                "type":"reorder","icon":"bell","color":"#1971C2","bg":"#E7F5FF",
                "title":"Low Stock Alert",
                "body":f"{r['item_code']} — Qty:{flt(r['actual_qty']):.0f} (Reorder at {flt(r['reorder_level']):.0f})",
                "link":"#/inventory/reorder-alerts","date":today(),
            })
    except Exception:
        pass

    return notifs


# ─── Audit Log ────────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_audit_log(page=0, page_len=50):
    """Return recent document activity from Frappe's Activity Log."""
    _require_admin()
    page = int(page)
    page_len = min(int(page_len), 200)

    logs = frappe.db.sql("""
        SELECT
            al.name, al.user, al.creation,
            al.reference_doctype as doctype,
            al.reference_name as doc_name,
            al.operation,
            al.status
        FROM `tabActivity Log` al
        WHERE al.reference_doctype IN (
            'Sales Invoice','Purchase Invoice','Customer','Supplier',
            'Payment Entry','Journal Entry','Sales Order',
            'Purchase Order','Credit Note','Stock Entry'
        )
        ORDER BY al.creation DESC
        LIMIT %(len)s OFFSET %(off)s
    """, {"len": page_len, "off": page * page_len}, as_dict=True)

    return logs


# ─── Company Settings ─────────────────────────────────────────────────────────

@frappe.whitelist()
def get_company_settings():
    """Return company profile from Books Company + invoice/reminder settings from Books Settings."""
    user = frappe.session.user
    company_name = frappe.db.get_value("Books Company Member", {"user": user}, "company") or ""

    result = {
        "default_company": company_name,
        "default_currency": "INR",
        "fiscal_year_start_month": "April",
        "invoice_prefix": "INV",
        "gstin": "",
        "gst_state": "",
        "logo_url": "",
        "company_address": "",
        "company_city": "",
        "company_state": "",
        "company_pincode": "",
        "company_phone": "",
        "company_email": "",
        "company_website": "",
        "auto_send_invoice": 0,
        "send_payment_reminders": 0,
        "reminder_days_before": 3,
        "reminder_days_after": 7,
        "auto_reconcile": 0,
    }

    # Profile fields come from Books Company
    if company_name and frappe.db.exists("Books Company", company_name):
        try:
            co = frappe.get_doc("Books Company", company_name)
            result["default_currency"] = co.currency or "INR"
            result["fiscal_year_start_month"] = co.fiscal_year_start_month or "April"
            result["gstin"] = co.gstin or ""
            result["gst_state"] = co.gst_state or ""
            result["logo_url"] = co.logo_url or ""
            result["company_address"] = co.address_line or ""
            result["company_city"] = co.city or ""
            result["company_state"] = co.state or ""
            result["company_pincode"] = co.pincode or ""
            result["company_phone"] = co.phone or ""
            result["company_email"] = co.email or ""
            result["company_website"] = co.website or ""
        except Exception:
            pass

    # Invoice / reminder / reconcile settings come from Books Settings
    try:
        settings = frappe.get_doc("Books Settings", "Books Settings")
        result["invoice_prefix"] = settings.get("invoice_prefix") or "INV"
        result["auto_send_invoice"] = settings.get("auto_send_invoice") or 0
        result["send_payment_reminders"] = settings.get("send_payment_reminders") or 0
        result["reminder_days_before"] = settings.get("reminder_days_before") or 3
        result["reminder_days_after"] = settings.get("reminder_days_after") or 7
        result["auto_reconcile"] = settings.get("auto_reconcile") or 0
    except Exception:
        pass

    return result


@frappe.whitelist()
def save_company_settings(**kwargs):
    """Save profile fields to Books Company; invoice/reminder settings to Books Settings."""
    _require_admin()

    user = frappe.session.user
    company_name = frappe.db.get_value("Books Company Member", {"user": user}, "company") or ""

    # Save profile fields to Books Company
    if company_name and frappe.db.exists("Books Company", company_name):
        try:
            co = frappe.get_doc("Books Company", company_name)
            if "default_currency" in kwargs:
                co.currency = kwargs["default_currency"]
            if "fiscal_year_start_month" in kwargs:
                co.fiscal_year_start_month = kwargs["fiscal_year_start_month"]
            if "gstin" in kwargs:
                co.gstin = kwargs["gstin"]
            if "gst_state" in kwargs:
                co.gst_state = kwargs["gst_state"]
            if "logo_url" in kwargs:
                co.logo_url = kwargs["logo_url"]
            if "company_address" in kwargs:
                co.address_line = kwargs["company_address"]
            if "company_city" in kwargs:
                co.city = kwargs["company_city"]
            if "company_state" in kwargs:
                co.state = kwargs["company_state"]
            if "company_pincode" in kwargs:
                co.pincode = kwargs["company_pincode"]
            if "company_phone" in kwargs:
                co.phone = kwargs["company_phone"]
            if "company_email" in kwargs:
                co.email = kwargs["company_email"]
            if "company_website" in kwargs:
                co.website = kwargs["company_website"]
            co.save(ignore_permissions=True)
        except Exception as e:
            frappe.log_error(str(e), "save_company_settings: Books Company")

    # Save invoice / reminder / reconcile settings to Books Settings
    try:
        settings = frappe.get_doc("Books Settings", "Books Settings")
    except Exception:
        settings = frappe.new_doc("Books Settings")
    for f in ["invoice_prefix", "auto_send_invoice", "send_payment_reminders",
              "reminder_days_before", "reminder_days_after", "auto_reconcile"]:
        if f in kwargs:
            settings.set(f, kwargs[f])
    settings.save(ignore_permissions=True)

    frappe.db.commit()
    return {"success": True}


# ─── SMTP / Email Settings (per-company) ──────────────────────────────────────

def _admin_company() -> str:
    """Return the Books Company managed by the current admin. Throws if none."""
    user = frappe.session.user
    company = frappe.db.get_value("Books Company Member", {"user": user}, "company")
    if not company:
        frappe.throw(_("Your user is not linked to any Books Company."))
    return company


@frappe.whitelist()
def get_email_settings():
    """Backwards-compat shim — older admin UI reads `{accounts:[...]}`.
    Wraps the company's SMTP config in the legacy shape so existing pages keep rendering."""
    _require_admin()
    company = _admin_company()
    doc = frappe.get_doc("Books Company", company)
    if not (doc.smtp_enabled and doc.smtp_server and doc.smtp_login):
        return {"accounts": []}
    return {"accounts": [{
        "name": company,
        "email_id": doc.smtp_from_email or doc.smtp_login,
        "smtp_server": doc.smtp_server,
        "smtp_port": int(doc.smtp_port or 587),
        "use_tls": int(doc.smtp_use_tls or 0),
        "use_ssl": int(doc.smtp_use_ssl or 0),
        "login_id": doc.smtp_login,
        "email_account_name": company,
    }]}


@frappe.whitelist()
def get_company_smtp():
    """Return the company's SMTP settings (password redacted) for the admin UI."""
    _require_admin()
    company = _admin_company()
    doc = frappe.get_doc("Books Company", company)
    return {
        "company": company,
        "smtp_enabled": int(doc.smtp_enabled or 0),
        "smtp_server": doc.smtp_server or "",
        "smtp_port": int(doc.smtp_port or 587),
        "smtp_use_tls": int(doc.smtp_use_tls or 0),
        "smtp_use_ssl": int(doc.smtp_use_ssl or 0),
        "smtp_login": doc.smtp_login or "",
        "smtp_password_set": bool(doc.smtp_password),
        "smtp_from_email": doc.smtp_from_email or "",
        "smtp_from_name": doc.smtp_from_name or "",
    }


@frappe.whitelist(methods=["POST"])
def save_company_smtp(
    smtp_enabled=0,
    smtp_server="",
    smtp_port=587,
    smtp_use_tls=1,
    smtp_use_ssl=0,
    smtp_login="",
    smtp_password=None,
    smtp_from_email="",
    smtp_from_name="",
):
    """Persist SMTP credentials on the admin's Books Company.
    smtp_password is only updated when explicitly provided (so re-saving the form
    without re-entering the password leaves the stored one untouched)."""
    _require_admin()
    company = _admin_company()
    doc = frappe.get_doc("Books Company", company)

    doc.smtp_enabled = 1 if int(smtp_enabled or 0) else 0
    doc.smtp_server = (smtp_server or "").strip()
    doc.smtp_port = int(smtp_port or 587)
    doc.smtp_use_tls = 1 if int(smtp_use_tls or 0) else 0
    doc.smtp_use_ssl = 1 if int(smtp_use_ssl or 0) else 0
    doc.smtp_login = (smtp_login or "").strip()
    if smtp_password not in (None, ""):
        doc.smtp_password = smtp_password
    doc.smtp_from_email = (smtp_from_email or "").strip() or doc.smtp_login
    doc.smtp_from_name = (smtp_from_name or "").strip() or company

    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "company": company}


@frappe.whitelist(methods=["POST"])
def send_test_email(to_email, use_overrides=0, **overrides):
    """Send a test email via the company's SMTP.
    If use_overrides=1 is passed (with smtp_* fields), tests those creds without saving them."""
    _require_admin()
    from zoho_books_clone.utils.email_company import test_company_smtp

    company = _admin_company()
    overrides_dict = None
    if int(use_overrides or 0):
        overrides_dict = {
            "smtp_server":     overrides.get("smtp_server", ""),
            "smtp_port":       overrides.get("smtp_port", 587),
            "smtp_use_tls":    overrides.get("smtp_use_tls", 1),
            "smtp_use_ssl":    overrides.get("smtp_use_ssl", 0),
            "smtp_login":      overrides.get("smtp_login", ""),
            "smtp_password":   overrides.get("smtp_password", ""),
            "smtp_from_email": overrides.get("smtp_from_email", ""),
            "smtp_from_name":  overrides.get("smtp_from_name", ""),
        }

    result = test_company_smtp(to=to_email, company=company, overrides=overrides_dict)
    if not result["success"]:
        frappe.throw(result["message"])
    return result


# ─── Number Series ────────────────────────────────────────────────────────────

_NS_DOCTYPE = "Books Number Series"

def _ns_fallback():
    """Return a static list when the custom doctype doesn't exist yet."""
    defaults = [
        ("INV-", "Sales Invoice", 4),
        ("PUR-", "Purchase Invoice", 4),
        ("SO-",  "Sales Order", 4),
        ("PO-",  "Purchase Order", 4),
        ("QTN-", "Quotation", 4),
        ("PAY-", "Payment Entry", 4),
        ("JE-",  "Journal Entry", 4),
        ("EXP-", "Expense Claim", 4),
        ("STE-", "Stock Entry", 4),
    ]
    result = []
    for prefix, doctype, padding in defaults:
        try:
            current = frappe.db.get_value("Series", {"name": prefix}, "current") or 0
        except Exception:
            current = 0
        result.append({"prefix": prefix, "doctype": doctype, "padding": padding, "current": int(current)})
    return result


@frappe.whitelist()
def get_number_series():
    """Return all configured number series."""
    _require_admin()
    try:
        if not frappe.db.table_exists(f"tab{_NS_DOCTYPE}"):
            return _ns_fallback()
        rows = frappe.get_all(
            _NS_DOCTYPE,
            fields=["name", "prefix", "doctype_name as doctype", "padding", "current"],
            limit=100,
        )
        if not rows:
            return _ns_fallback()
        return rows
    except Exception:
        return _ns_fallback()


@frappe.whitelist()
def save_number_series(prefix, doctype="", current=0, padding=4):  # noqa: ARG001 — doctype/padding kept for API compat
    """Save or update a number series entry."""
    _require_admin()
    try:
        # Update Frappe's built-in Series table directly
        existing = frappe.db.get_value("Series", {"name": prefix}, "name")
        if existing:
            frappe.db.set_value("Series", prefix, "current", int(current))
        else:
            doc = frappe.new_doc("Series")
            doc.name = prefix
            doc.current = int(current)
            doc.db_insert()
        frappe.db.commit()
        return {"success": True}
    except Exception as e:
        frappe.throw(str(e))


@frappe.whitelist()
def reset_number_series(prefix, doctype=""):  # noqa: ARG001 — doctype kept for API compat
    """Reset a number series back to 0."""
    _require_admin()
    try:
        frappe.db.set_value("Series", prefix, "current", 0)
        frappe.db.commit()
        return {"success": True}
    except Exception:
        return {"success": True, "note": "Series not found in database"}


# ─── Email Templates ──────────────────────────────────────────────────────────

@frappe.whitelist()
def get_email_templates():
    """List all Email Template documents."""
    try:
        return frappe.get_all(
            "Email Template",
            fields=["name", "subject", "use_html"],
            limit=200,
            ignore_permissions=True,
        )
    except Exception:
        return []


@frappe.whitelist()
def get_email_template(name):
    """Fetch a single Email Template with body."""
    try:
        doc = frappe.get_doc("Email Template", name)
        return {
            "name": doc.name,
            "subject": doc.subject or "",
            "response": doc.response or "",
            "use_html": doc.use_html or 0,
        }
    except Exception:
        return {}


@frappe.whitelist()
def save_email_template(name, subject, response="", use_html=0):
    """Create or update an Email Template."""
    _require_admin()
    use_html = int(use_html) if str(use_html).isdigit() else (1 if use_html in (True, "true", "True") else 0)
    if frappe.db.exists("Email Template", name):
        doc = frappe.get_doc("Email Template", name)
        doc.subject = subject
        doc.response = response
        doc.use_html = use_html
        doc.save(ignore_permissions=True)
    else:
        doc = frappe.new_doc("Email Template")
        doc.name = name
        doc.subject = subject
        doc.response = response
        doc.use_html = use_html
        doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "name": doc.name}


@frappe.whitelist()
def delete_email_template(name):
    """Delete an Email Template."""
    _require_admin()
    frappe.delete_doc("Email Template", name, ignore_permissions=True, force=True)
    frappe.db.commit()
    return {"success": True}


# ─── Payment Terms ────────────────────────────────────────────────────────────

@frappe.whitelist()
def get_payment_terms():
    """List all Payment Term documents."""
    try:
        return frappe.get_all(
            "Payment Term",
            fields=["name", "due_date_based_on", "payment_days",
                    "discount_percentage", "discount_days", "description"],
            limit=200,
            ignore_permissions=True,
        )
    except Exception:
        return []


@frappe.whitelist()
def save_payment_term(name, due_date_based_on="Day(s) after invoice date",
                      payment_days=30, discount_days=0, discount_percentage=0,
                      description=""):
    """Create or update a Payment Term."""
    _require_admin()
    payment_days = int(payment_days or 0)
    discount_days = int(discount_days or 0)
    discount_percentage = float(discount_percentage or 0)
    if frappe.db.exists("Payment Term", name):
        doc = frappe.get_doc("Payment Term", name)
    else:
        doc = frappe.new_doc("Payment Term")
        doc.payment_term_name = name
    doc.due_date_based_on = due_date_based_on
    doc.payment_days = payment_days
    doc.discount_days = discount_days
    doc.discount_percentage = discount_percentage
    doc.description = description or ""
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    return {"success": True, "name": doc.name}


@frappe.whitelist()
def delete_payment_term(name):
    """Delete a Payment Term."""
    _require_admin()
    frappe.delete_doc("Payment Term", name, ignore_permissions=True, force=True)
    frappe.db.commit()
    return {"success": True}
