import frappe
from urllib.parse import quote_plus

no_cache = 1
no_sitemap = 1

def get_context(context):
    if not frappe.session.user or frappe.session.user == "Guest":
        redirect_to = frappe.request.path if hasattr(frappe, "request") and frappe.request else "/books"
        frappe.local.flags.redirect_location = f"/login?redirect-to={quote_plus(redirect_to)}"
        raise frappe.Redirect
