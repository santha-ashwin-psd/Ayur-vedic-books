app_name        = "zoho_books_clone"
app_title       = "Books"
app_publisher   = "PS Digitise"
app_description = "A full-featured accounting application built on Frappe"
app_email       = "devteam@psdigitise.com"
app_license     = "MIT"
app_version     = "1.0.0"
app_icon        = "octicon octicon-book"
app_color       = "#2563EB"

fixtures = [
    {"dt": "Role", "filters": [["name", "in", [
        "Books Admin", "Accountant", "Books Manager", "Books Viewer"
    ]]]},
    "Custom Field",
    "Property Setter",
]

# Central validation layer (P2/Issue 10) — runs on every financial document
_CV = "zoho_books_clone.accounts.central_validator"
# Stock link layer (Audit-2 / Audit-3) — auto stock entries on invoice submit/cancel
_SL = "zoho_books_clone.inventory.stock_link"
# Multi-tenant data isolation — must be defined before doc_events, permission_query_conditions, and has_permission
_TN = "zoho_books_clone.utils.tenancy"
doc_events = {
    "Sales Invoice": {
        "validate":  f"{_CV}.on_validate",
        "on_submit": [f"{_CV}.on_submit", f"{_SL}.on_sales_invoice_submit"],
        "on_cancel": f"{_SL}.on_sales_invoice_cancel",
    },
    "Purchase Invoice": {
        "validate":  f"{_CV}.on_validate",
        "on_submit": [f"{_CV}.on_submit", f"{_SL}.on_purchase_invoice_submit"],
        "on_cancel": f"{_SL}.on_purchase_invoice_cancel",
    },
    "Payment Entry":    {"validate": f"{_CV}.on_validate", "on_submit": f"{_CV}.on_submit"},
    "Journal Entry":    {"validate": f"{_CV}.on_validate", "on_submit": f"{_CV}.on_submit"},
    "Credit Note":      {"validate": f"{_CV}.on_validate", "on_submit": f"{_CV}.on_submit"},
    "Expense":          {"validate": f"{_CV}.on_validate", "on_submit": f"{_CV}.on_submit"},
    "Expense Claim":    {"validate": f"{_CV}.on_validate", "on_submit": f"{_CV}.on_submit"},
    # Goods documents own the physical stock movement (Delivery Note out / Purchase Receipt in)
    "Delivery Note":    {"on_submit": f"{_SL}.on_delivery_note_submit",    "on_cancel": f"{_SL}.on_delivery_note_cancel"},
    "Purchase Receipt": {"on_submit": f"{_SL}.on_purchase_receipt_submit", "on_cancel": f"{_SL}.on_purchase_receipt_cancel"},
    # Auto-stamp books_company on master records so they're company-isolated
    "Customer":  {"before_insert": f"{_TN}.auto_stamp_books_company"},
    "Supplier":  {"before_insert": f"{_TN}.auto_stamp_books_company"},
    "Item":      {"before_insert": f"{_TN}.auto_stamp_books_company"},
    "Contact":   {"before_insert": f"{_TN}.auto_stamp_books_company"},
}

scheduler_events = {
    "daily": [
        "zoho_books_clone.utils.scheduler.send_payment_reminders",
        "zoho_books_clone.banking.utils.auto_match_bank_transactions",
        "zoho_books_clone.utils.scheduler.send_reorder_alerts",
    ],
    "monthly": [
        "zoho_books_clone.utils.scheduler.generate_monthly_reports",
    ],
}

global_search_doctypes = {
    "Accounts":  [
        {"doctype": "Account"},
        {"doctype": "Cost Center"},
    ],
    "Invoicing": [
        {"doctype": "Sales Invoice"},
        {"doctype": "Purchase Invoice"},
        {"doctype": "Customer"},
        {"doctype": "Supplier"},
        {"doctype": "Item"},
    ],
    "Payments": [
        {"doctype": "Payment Entry"},
    ],
    "Expenses": [
        {"doctype": "Expense"},
        {"doctype": "Expense Claim"},
    ],
    "Inventory": [
        {"doctype": "Warehouse"},
        {"doctype": "Stock Entry"},
        {"doctype": "Item Price"},
        {"doctype": "Price List"},
    ],
    "Books Setup": [
        {"doctype": "Currency"},
        {"doctype": "Currency Exchange"},
        {"doctype": "UOM"},
        {"doctype": "Books Payment Mode"},
        {"doctype": "Payment Terms"},
    ],
}

app_include_css = ["/assets/zoho_books_clone/css/books.css"]
app_include_js  = ["/assets/zoho_books_clone/js/books.js"]

after_install = "zoho_books_clone.books_setup.install.after_install"
after_migrate = "zoho_books_clone.books_setup.install.after_migrate"


# ─── Multi-tenant data isolation ─────────────────────────────────────────────
# Every transactional doctype with a `company` field is filtered to the user's
# company at query time AND validated at save time (via central_validator).
# System Manager / Administrator bypass these filters.
# (_TN is defined near the top of this file, alongside _CV and _SL)

permission_query_conditions = {
    "Sales Invoice":     f"{_TN}.qc_sales_invoice",
    "Purchase Invoice":  f"{_TN}.qc_purchase_invoice",
    "Payment Entry":     f"{_TN}.qc_payment_entry",
    "Journal Entry":     f"{_TN}.qc_journal_entry",
    "Credit Note":       f"{_TN}.qc_credit_note",
    "Sales Order":       f"{_TN}.qc_sales_order",
    "Purchase Order":    f"{_TN}.qc_purchase_order",
    "Quotation":         f"{_TN}.qc_quotation",
    "Account":           f"{_TN}.qc_account",
    "Cost Center":       f"{_TN}.qc_cost_center",
    "Warehouse":         f"{_TN}.qc_warehouse",
    "Stock Entry":       f"{_TN}.qc_stock_entry",
    "Bank Account":      f"{_TN}.qc_bank_account",
    "Bank Transaction":  f"{_TN}.qc_bank_transaction",
    "Expense":           f"{_TN}.qc_expense",
    "Expense Claim":     f"{_TN}.qc_expense_claim",
    # Master types — scoped by books_company custom field
    "Customer":          f"{_TN}.qc_customer",
    "Supplier":          f"{_TN}.qc_supplier",
    "Item":              f"{_TN}.qc_item",
    "Contact":           f"{_TN}.qc_contact",
}

has_permission = {
    "Sales Invoice":     f"{_TN}.hp_sales_invoice",
    "Purchase Invoice":  f"{_TN}.hp_purchase_invoice",
    "Payment Entry":     f"{_TN}.hp_payment_entry",
    "Journal Entry":     f"{_TN}.hp_journal_entry",
    "Credit Note":       f"{_TN}.hp_credit_note",
    "Sales Order":       f"{_TN}.hp_sales_order",
    "Purchase Order":    f"{_TN}.hp_purchase_order",
    "Quotation":         f"{_TN}.hp_quotation",
    "Account":           f"{_TN}.hp_account",
    "Cost Center":       f"{_TN}.hp_cost_center",
    "Warehouse":         f"{_TN}.hp_warehouse",
    "Stock Entry":       f"{_TN}.hp_stock_entry",
    "Bank Account":      f"{_TN}.hp_bank_account",
    "Bank Transaction":  f"{_TN}.hp_bank_transaction",
    "Expense":           f"{_TN}.hp_expense",
    "Expense Claim":     f"{_TN}.hp_expense_claim",
    # Master types — scoped by books_company custom field
    "Customer":          f"{_TN}.hp_customer",
    "Supplier":          f"{_TN}.hp_supplier",
    "Item":              f"{_TN}.hp_item",
    "Contact":           f"{_TN}.hp_contact",
}
