from __future__ import annotations
"""
Multi-tenant data isolation.

Wires into Frappe's permission system so every list/get for a transactional
doctype is filtered by the user's company, and every save is rejected if the
document's company doesn't match the user's.

The permission_query_conditions hook injects a SQL WHERE clause into every
query Frappe runs against a doctype. has_permission is checked on individual
docs (the latter is the safety net for doc.get(), which doesn't go through
permission_query_conditions).
"""
import frappe


# Roles that bypass tenancy entirely (system-level admins).
_BYPASS_ROLES = {"Administrator", "System Manager"}


def _is_bypass(user: str) -> bool:
    if user == "Administrator":
        return True
    roles = set(frappe.get_roles(user))
    return bool(roles & _BYPASS_ROLES)


def get_user_company(user: str | None = None) -> str | None:
    """Return the Books Company name the user belongs to, or None."""
    user = user or frappe.session.user
    if not user or user in ("Guest", ""):
        return None
    if _is_bypass(user):
        return None  # bypass = no filter applied
    return frappe.db.get_value("Books Company Member", {"user": user}, "company")


def _meta_has_company(doctype: str) -> bool:
    """True if the doctype has a `company` field (Link or Data)."""
    try:
        meta = frappe.get_meta(doctype)
    except Exception:
        return False
    return bool(meta.has_field("company"))


def permission_query_conditions(user: str | None = None, doctype: str | None = None) -> str:
    """Inject a SQL WHERE fragment so users only see rows for their own company.

    Returns an empty string when:
      - The user is a system bypass role
      - The user has no company membership (defensive: see nothing rather than everything)
      - The doctype has no `company` field (nothing to filter on)

    Frappe calls this with (user) only — but we accept doctype for direct testing.
    """
    user = user or frappe.session.user
    if _is_bypass(user):
        return ""

    company = get_user_company(user)
    if not company:
        # Defensive default: an unmapped session-user sees nothing.
        return "1=0"

    # When called without `doctype`, Frappe injects this fragment via callback;
    # the actual doctype is determined by the call site. We can't resolve it
    # here, so return the generic fragment — Frappe wraps it in the right table alias.
    safe_company = frappe.db.escape(company)
    return f"`company` = {safe_company}"


def has_permission(doc, ptype: str = "read", user: str | None = None) -> bool | None:
    """Per-document tenancy check. Returning None means "no opinion" (let other
    permission hooks decide); True/False is decisive."""
    user = user or frappe.session.user
    if _is_bypass(user):
        return None

    company = get_user_company(user)
    if not company:
        return False

    doc_company = getattr(doc, "company", None)
    if doc_company is None:
        return None  # doctype has no company field — no opinion
    return doc_company == company


def assert_doc_in_user_company(doc):
    """Raise PermissionError if the doc's company isn't the user's company.
    Called from the central validator on save/submit. No-op for bypass roles."""
    user = frappe.session.user
    if _is_bypass(user):
        return

    doc_company = getattr(doc, "company", None)
    if not doc_company:
        return  # _check_company in central_validator already enforces presence

    user_company = get_user_company(user)
    if not user_company:
        frappe.throw(
            "Your user is not linked to any Books Company. Contact your administrator.",
            frappe.PermissionError,
        )
    if doc_company != user_company:
        frappe.throw(
            f"You cannot save this {doc.doctype} for company '{doc_company}' — "
            f"your account belongs to '{user_company}'.",
            frappe.PermissionError,
        )


# ── Per-doctype query condition builders (for hooks.py wiring) ──────────────
# Frappe's permission_query_conditions hook is keyed by doctype, so we register
# a thin wrapper per doctype that calls the generic implementation.

def _make_qc(doctype: str):
    def _qc(user=None):
        if not _meta_has_company(doctype):
            return ""
        return permission_query_conditions(user=user)
    _qc.__name__ = f"qc_{doctype.lower().replace(' ', '_')}"
    return _qc


qc_sales_invoice    = _make_qc("Sales Invoice")
qc_purchase_invoice = _make_qc("Purchase Invoice")
qc_payment_entry    = _make_qc("Payment Entry")
qc_journal_entry    = _make_qc("Journal Entry")
qc_credit_note      = _make_qc("Credit Note")
qc_sales_order      = _make_qc("Sales Order")
qc_purchase_order   = _make_qc("Purchase Order")
qc_quotation        = _make_qc("Quotation")
qc_account          = _make_qc("Account")
qc_cost_center      = _make_qc("Cost Center")
qc_warehouse        = _make_qc("Warehouse")
qc_stock_entry      = _make_qc("Stock Entry")
qc_bank_account     = _make_qc("Bank Account")
qc_bank_transaction = _make_qc("Bank Transaction")
qc_expense          = _make_qc("Expense")
qc_expense_claim    = _make_qc("Expense Claim")


# ── Per-doctype has_permission wrappers ─────────────────────────────────────

def _make_hp(_doctype: str):
    def _hp(doc, ptype="read", user=None):
        return has_permission(doc, ptype=ptype, user=user)
    return _hp


hp_sales_invoice    = _make_hp("Sales Invoice")
hp_purchase_invoice = _make_hp("Purchase Invoice")
hp_payment_entry    = _make_hp("Payment Entry")
hp_journal_entry    = _make_hp("Journal Entry")
hp_credit_note      = _make_hp("Credit Note")
hp_sales_order      = _make_hp("Sales Order")
hp_purchase_order   = _make_hp("Purchase Order")
hp_quotation        = _make_hp("Quotation")
hp_account          = _make_hp("Account")
hp_cost_center      = _make_hp("Cost Center")
hp_warehouse        = _make_hp("Warehouse")
hp_stock_entry      = _make_hp("Stock Entry")
hp_bank_account     = _make_hp("Bank Account")
hp_bank_transaction = _make_hp("Bank Transaction")
hp_expense          = _make_hp("Expense")
hp_expense_claim    = _make_hp("Expense Claim")
