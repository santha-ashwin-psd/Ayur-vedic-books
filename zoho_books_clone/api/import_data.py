import csv
import io
import frappe
from frappe import _
from frappe.utils import flt, cint


CUSTOMER_FIELDS = [
    "customer_name", "customer_type", "email_id", "mobile_no",
    "phone", "tax_id", "city", "state", "country", "payment_terms",
]

ITEM_FIELDS = [
    "item_code", "item_name", "item_group", "item_type",
    "stock_uom", "standard_rate", "gst_rate", "hsn_code",
    "description", "is_sales_item", "is_purchase_item",
]

VENDOR_FIELDS = [
    "supplier_name", "supplier_type", "email_id", "mobile_no",
    "phone", "tax_id", "city", "state", "country", "payment_terms",
]


@frappe.whitelist()
def bulk_import(doctype, rows_json):
    """
    Import a list of dicts into the given doctype.
    Returns {"created": N, "skipped": N, "errors": [...]}
    """
    import json

    allowed = {"Customer", "Item", "Supplier"}
    if doctype not in allowed:
        frappe.throw(_("Unsupported doctype for import: {}").format(doctype))

    rows = json.loads(rows_json)
    if not isinstance(rows, list):
        frappe.throw(_("rows_json must be a JSON array"))

    created = 0
    skipped = 0
    errors = []

    from zoho_books_clone.utils.tenancy import get_user_company, _is_bypass

    user = frappe.session.user
    company = "" if _is_bypass(user) else get_user_company(user)

    for i, row in enumerate(rows, start=1):
        try:
            doc = _build_doc(doctype, row, company)
            if not doc:
                skipped += 1
                continue
            frappe.get_doc(doc).insert(ignore_permissions=False)
            created += 1
        except Exception as e:
            errors.append({"row": i, "data": row, "error": str(e)})

    frappe.db.commit()
    return {"created": created, "skipped": skipped, "errors": errors}


def _build_doc(doctype, row, company):
    if doctype == "Customer":
        name = (row.get("customer_name") or "").strip()
        if not name:
            return None
        doc = {
            "doctype": "Customer",
            "customer_name": name,
            "customer_type": row.get("customer_type") or "Individual",
            "email_id": row.get("email_id") or "",
            "mobile_no": row.get("mobile_no") or "",
            "phone": row.get("phone") or "",
            "tax_id": row.get("tax_id") or "",
            "city": row.get("city") or "",
            "state": row.get("state") or "",
            "country": row.get("country") or "India",
            "payment_terms": row.get("payment_terms") or "",
        }
        if company:
            doc["books_company"] = company
        return doc

    if doctype == "Supplier":
        name = (row.get("supplier_name") or "").strip()
        if not name:
            return None
        doc = {
            "doctype": "Supplier",
            "supplier_name": name,
            "supplier_type": row.get("supplier_type") or "Individual",
            "email_id": row.get("email_id") or "",
            "mobile_no": row.get("mobile_no") or "",
            "phone": row.get("phone") or "",
            "tax_id": row.get("tax_id") or "",
            "city": row.get("city") or "",
            "state": row.get("state") or "",
            "country": row.get("country") or "India",
            "payment_terms": row.get("payment_terms") or "",
        }
        if company:
            doc["books_company"] = company
        return doc

    if doctype == "Item":
        iname = (row.get("item_name") or "").strip()
        if not iname:
            return None
        doc = {
            "doctype": "Item",
            "item_name": iname,
            "item_code": (row.get("item_code") or iname).strip(),
            "item_group": row.get("item_group") or "All Item Groups",
            "item_type": row.get("item_type") or "Service",
            "stock_uom": row.get("stock_uom") or "Nos",
            "standard_rate": flt(row.get("standard_rate") or 0),
            "gst_rate": flt(row.get("gst_rate") or 0),
            "hsn_code": row.get("hsn_code") or "",
            "description": row.get("description") or iname,
            "is_sales_item": cint(row.get("is_sales_item") if row.get("is_sales_item") is not None else 1),
            "is_purchase_item": cint(row.get("is_purchase_item") if row.get("is_purchase_item") is not None else 1),
        }
        if company:
            doc["books_company"] = company
        return doc

    return None


@frappe.whitelist()
def get_sample_csv(doctype):
    """Return a CSV string with headers for the given doctype."""
    headers = {
        "Customer": ["customer_name","customer_type","email_id","mobile_no","phone","tax_id","city","state","country","payment_terms"],
        "Supplier": ["supplier_name","supplier_type","email_id","mobile_no","phone","tax_id","city","state","country","payment_terms"],
        "Item":     ["item_code","item_name","item_group","item_type","stock_uom","standard_rate","gst_rate","hsn_code","description","is_sales_item","is_purchase_item"],
    }
    samples = {
        "Customer": [["Acme Corp","Company","acme@example.com","9876543210","","27AAACR5055K1Z5","Mumbai","Maharashtra","India","Net 30"]],
        "Supplier": [["Global Supplies","Company","supplier@example.com","9876543210","","27AAACR5055K1Z5","Delhi","Delhi","India",""]],
        "Item":     [["ITEM-001","Widget A","All Item Groups","Stock Item","Nos","100","18","8471","Standard Widget","1","1"]],
    }
    if doctype not in headers:
        frappe.throw(_("Unsupported doctype: {}").format(doctype))

    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow(headers[doctype])
    for row in samples[doctype]:
        w.writerow(row)
    return buf.getvalue()
