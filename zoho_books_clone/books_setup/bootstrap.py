"""
Per-company bootstrap — runs on signup to seed a fresh company with the data
required for the golden flow (Customer → Item → Sales Invoice → Payment) to
work without manual setup.

Idempotent: every step checks for existence before inserting.

Account naming convention: "{account_name} - {company}"
  (matches the DocType autoname rule: format:{account_name} - {company})
"""
import datetime

import frappe


COA = [
    # (account_name, account_type, parent_name, is_group)
    # Parent is the account_name (not the full doc name) — we build the full
    # name as "{parent} - {company}" at runtime.
    ("Assets",                "Asset",      None,                  1),
    ("Current Assets",        "Asset",      "Assets",              1),
    ("Cash",                  "Cash",       "Current Assets",      0),
    ("Bank Accounts",         "Bank",       "Current Assets",      1),
    ("Accounts Receivable",   "Receivable", "Current Assets",      0),
    ("Stock In Hand",         "Stock",      "Current Assets",      0),
    ("Input Tax Credits",     "Tax",        "Current Assets",      1),
    ("CGST Input",            "Tax",        "Input Tax Credits",   0),
    ("SGST Input",            "Tax",        "Input Tax Credits",   0),
    ("IGST Input",            "Tax",        "Input Tax Credits",   0),
    ("Liabilities",           "Liability",  None,                  1),
    ("Current Liabilities",   "Liability",  "Liabilities",         1),
    ("Accounts Payable",      "Payable",    "Current Liabilities", 0),
    ("CGST Payable",          "Tax",        "Current Liabilities", 0),
    ("SGST Payable",          "Tax",        "Current Liabilities", 0),
    ("IGST Payable",          "Tax",        "Current Liabilities", 0),
    ("Equity",                "Equity",     None,                  1),
    ("Retained Earnings",     "Equity",     "Equity",              0),
    ("Income",                "Income",     None,                  1),
    ("Sales Revenue",         "Income",     "Income",              0),
    ("Other Income",          "Income",     "Income",              0),
    ("Expenses",              "Expense",    None,                  1),
    ("Cost of Goods Sold",    "Cost of Goods Sold", "Expenses",    0),
    ("Stock Adjustment",      "Stock Adjustment",   "Expenses",    0),
    ("Operating Expenses",    "Expense",    "Expenses",            1),
    ("Salaries & Wages",      "Expense",    "Operating Expenses",  0),
    ("Rent",                  "Expense",    "Operating Expenses",  0),
    ("Office Supplies",       "Expense",    "Operating Expenses",  0),
]


def _acc_name(account_name: str, company: str) -> str:
    """Return the full document name for an account."""
    return f"{account_name} - {company}"


def bootstrap_company_data(company: str, fy_start: str = "04-01") -> None:
    """Seed a fresh company with the minimum data needed for invoicing."""
    if not company:
        return
    _seed_coa(company)
    _seed_fiscal_year(company, fy_start)


def _seed_coa(company: str) -> None:
    """Create the default Chart of Accounts for this company if absent.

    The full document name for each account is "{account_name} - {company}".
    We check by that full name first so the idempotency guard works even when
    the account was created in a previous call.
    """
    for name, atype, parent, is_group in COA:
        full_name = _acc_name(name, company)

        # Idempotency: skip if already present (check by PK, which is the full name)
        if frappe.db.exists("Account", full_name):
            continue

        parent_full = _acc_name(parent, company) if parent else ""

        try:
            doc = frappe.get_doc({
                "doctype":        "Account",
                "account_name":   name,
                "account_type":   atype,
                "parent_account": parent_full,
                "is_group":       is_group,
                "company":        company,
                "currency":       "INR",
            })
            doc.insert(ignore_permissions=True)
        except Exception as exc:
            frappe.log_error(
                f"Bootstrap COA — {company}/{name}: {exc}", "Books Bootstrap"
            )


def _seed_fiscal_year(company: str, fy_start: str = "04-01") -> None:
    """Create a Fiscal Year for `company` covering today, if absent.

    Each tenant gets its own FY document named "{year_label} - {company}".
    The validate_overlap check in FiscalYear.py is company-scoped, so
    we must check existence before inserting to stay idempotent.
    """
    try:
        today = datetime.date.today()
        month, day = (int(x) for x in (fy_start or "04-01").split("-"))

        start = datetime.date(today.year, month, day)
        if today < start:
            start = datetime.date(today.year - 1, month, day)
        end = datetime.date(start.year + 1, month, day) - datetime.timedelta(days=1)

        if start.year == end.year:
            year_label = str(start.year)
        else:
            year_label = f"{start.year}-{str(end.year)[-2:]}"

        # Idempotency: skip if a FY already covers this period for this company
        existing = frappe.db.sql("""
            SELECT name FROM `tabFiscal Year`
            WHERE company = %s
              AND year_start_date <= %s
              AND year_end_date   >= %s
            LIMIT 1
        """, (company, end.strftime("%Y-%m-%d"), start.strftime("%Y-%m-%d")), as_dict=True)

        if existing:
            return

        fy = frappe.new_doc("Fiscal Year")
        fy.year            = year_label
        fy.year_start_date = start.strftime("%Y-%m-%d")
        fy.year_end_date   = end.strftime("%Y-%m-%d")
        fy.company         = company
        # flags.ignore_validate skips the overlap check in FiscalYear.validate()
        # which would otherwise trigger because fy.name is not yet persisted
        fy.flags.ignore_validate = True
        fy.insert(ignore_permissions=True)

    except Exception as exc:
        frappe.log_error(f"Bootstrap FY — {company}: {exc}", "Books Bootstrap")
