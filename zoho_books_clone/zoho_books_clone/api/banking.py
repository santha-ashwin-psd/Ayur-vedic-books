"""
Banking API — whitelisted endpoints for banking workflow operations.

Covers:
  - get_bank_accounts_with_balances: Bank accounts with GL-computed balances
  - get_bank_account: Fetch a single Bank Account document (full fields)
  - save_bank_account: Create or update a Bank Account (bypasses modified conflict)
  - bounce_cheque: GL reversal when a cheque bounces
  - post_bank_transfer: inter-account fund transfer with GL posting
  - create_bank_gl_entry: JE for unmatched bank transactions (charges, interest)
"""
import frappe
from frappe import _
from frappe.utils import flt, today
from zoho_books_clone.api.session import _get_company
from zoho_books_clone.accounts.doctype.general_ledger_entry.general_ledger_entry import (
    make_gl_entries,
)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _bank_gl(bank_account: str) -> str:
    gl = frappe.db.get_value("Bank Account", bank_account, "gl_account")
    if not gl:
        frappe.throw(_("Bank Account {0} has no GL account linked.").format(bank_account))
    return gl


def _company(bank_account: str) -> str:
    co = frappe.db.get_value("Bank Account", bank_account, "company")
    return co or frappe.db.get_default("company") or ""


def _recalc_balance(bank_account: str) -> float:
    """
    Compute the live balance for a Bank Account as:
        opening_balance  +  SUM(credit) - SUM(debit)  from submitted Bank Transactions

    This is always per-account (not per-GL-account) so accounts that share the
    same GL account each get their own correct number.
    Persists the result back to current_balance so the field stays up to date.
    """
    opening = flt(frappe.db.get_value("Bank Account", bank_account, "opening_balance") or 0)
    row = frappe.db.sql("""
        SELECT COALESCE(SUM(credit) - SUM(debit), 0) AS net
        FROM `tabBank Transaction`
        WHERE bank_account = %s AND docstatus = 1
    """, bank_account, as_dict=True)
    net = flt(row[0].net) if row else 0.0
    live = opening + net
    # Persist so the field is always fresh; skip modified-time update to avoid conflicts.
    frappe.db.set_value("Bank Account", bank_account, "current_balance", live, update_modified=False)
    return live


# ─── Endpoints ────────────────────────────────────────────────────────────────

@frappe.whitelist(allow_guest=False)
def get_bank_account(name: str) -> dict:
    """
    Return the full Bank Account document for a single account.
    Attaches the live per-account balance (opening + Bank Transaction net).
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not permitted"), frappe.PermissionError)
    doc = frappe.get_doc("Bank Account", name)
    d = doc.as_dict()

    # Always use the per-account live formula, not the shared GL aggregate.
    d["current_balance"] = _recalc_balance(name)
    d["balance"]         = d["current_balance"]

    # Reconciliation stats
    total = frappe.db.count("Bank Transaction", {"bank_account": name, "docstatus": 1})
    reconciled = frappe.db.count("Bank Transaction", {"bank_account": name, "docstatus": 1, "status": "Reconciled"})
    d["reconcile_pct"] = round(reconciled / total * 100) if total else 0
    d["txn_count"]     = total

    return d


@frappe.whitelist(allow_guest=False, methods=["POST"])
def save_bank_account(
    account_name: str,
    bank_name: str = "",
    account_number: str = "",
    ifsc_code: str = "",
    branch: str = "",
    account_holder_name: str = "",
    micr_code: str = "",
    currency: str = "INR",
    account_type: str = "Current",
    gl_account: str = "",
    status: str = "Active",
    is_default: int = 0,
    company: str = "",
    existing_name: str = "",   # Frappe document name when editing
    opening_balance: float = 0.0,
    current_balance: float = 0.0,
) -> dict:
    """
    Create or update a Bank Account document.

    Key difference from frappe.client.save:
      - Fetches the latest `modified` from the DB before saving so Frappe's
        optimistic-locking check ("document modified after you opened it") never fires.
      - Uses ignore_permissions=True so the Books Manager role can write.
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if not account_name.strip():
        frappe.throw(_("Account name is required"))

    if not company:
        company = _get_company(frappe.session.user)
    if not company:
        frappe.throw(_("No company configured. Please set a default company in Books Settings."))

    # ── UPDATE existing document ───────────────────────────────────────────────
    if existing_name and frappe.db.exists("Bank Account", existing_name):
        doc = frappe.get_doc("Bank Account", existing_name)

        # Sync the `modified` field to whatever is currently in the DB so
        # Frappe's TimestampMismatch check passes without needing a page refresh.
        db_modified = frappe.db.get_value("Bank Account", existing_name, "modified")
        if db_modified:
            doc.modified = db_modified

        doc.account_name         = account_name
        doc.bank_name            = bank_name
        doc.account_number       = account_number
        doc.ifsc_code            = ifsc_code
        doc.branch               = branch
        doc.account_holder_name  = account_holder_name
        doc.micr_code            = micr_code
        doc.currency             = currency or "INR"
        doc.account_type         = account_type or "Current"
        doc.gl_account           = gl_account
        doc.status               = status or "Active"
        doc.is_default           = int(is_default or 0)
        doc.company              = company
        doc.opening_balance      = flt(opening_balance)
        doc.current_balance      = flt(current_balance)

        doc.save(ignore_permissions=True)
        frappe.db.commit()
        return doc.as_dict()

    # ── CREATE new document ────────────────────────────────────────────────────
    # If the user entered a starting balance in the "Current Balance" field but
    # left Opening Balance at 0, treat it as the opening balance so the recalc
    # formula (opening + transactions) produces the correct result.
    effective_opening = flt(opening_balance) or flt(current_balance)

    doc = frappe.get_doc({
        "doctype":             "Bank Account",
        "account_name":        account_name,
        "bank_name":           bank_name,
        "account_number":      account_number,
        "ifsc_code":           ifsc_code,
        "branch":              branch,
        "account_holder_name": account_holder_name,
        "micr_code":           micr_code,
        "currency":            currency or "INR",
        "account_type":        account_type or "Current",
        "gl_account":          gl_account,
        "status":              status or "Active",
        "is_default":          int(is_default or 0),
        "company":             company,
        "opening_balance":     effective_opening,
        "current_balance":     effective_opening,
    })
    doc.insert(ignore_permissions=True)
    frappe.db.commit()
    return doc.as_dict()


@frappe.whitelist(allow_guest=False)
def get_bank_accounts_with_balances(company: str = None) -> list:
    """
    Return all Bank Accounts for the company with their live GL balance,
    reconciliation stats, and recent transactions count.
    """
    if not company:
        company = _get_company(frappe.session.user)

    # Always include the stored balance fields so we display the per-account value,
    # not a shared GL aggregate.
    _FIELDS = [
        "name", "account_name", "bank_name", "account_number", "ifsc_code",
        "gl_account", "currency", "is_default", "account_type",
        "opening_balance", "current_balance",
    ]

    accounts = frappe.get_all(
        "Bank Account",
        filters={"company": company} if company else {},
        fields=_FIELDS,
        order_by="is_default desc, creation asc",
        limit=100,
        ignore_permissions=True,
    )

    for a in accounts:
        # ── Balance: always compute dynamically as
        #   opening_balance + SUM(credit - debit from submitted Bank Transactions)
        # This is per-account so accounts sharing a GL account get distinct balances.
        # We also persist the result to current_balance so it's always fresh.
        opening = flt(a.get("opening_balance"))
        txn_row = frappe.db.sql("""
            SELECT COALESCE(SUM(credit) - SUM(debit), 0) AS net
            FROM `tabBank Transaction`
            WHERE bank_account = %s AND docstatus = 1
        """, a["name"], as_dict=True)
        net = flt(txn_row[0].net) if txn_row else 0.0
        live = opening + net
        a["balance"] = live
        a["current_balance"] = live
        # Persist silently — no modified-time bump to avoid conflicts.
        frappe.db.set_value("Bank Account", a["name"], "current_balance", live, update_modified=False)

        # Reconciliation percentage
        total = frappe.db.count("Bank Transaction",
            {"bank_account": a["name"], "docstatus": 1})
        reconciled = frappe.db.count("Bank Transaction",
            {"bank_account": a["name"], "docstatus": 1, "status": "Reconciled"})
        a["reconcile_pct"] = round(reconciled / total * 100) if total else 0
        a["txn_count"] = total

    return accounts


@frappe.whitelist(allow_guest=False, methods=["POST"])
def bounce_cheque(payment_entry: str) -> dict:
    """
    Reverse GL entries when a cheque bounces.
    The original Payment Entry GL (DR Bank / CR Payable or DR Receivable / CR Bank)
    is unwound by creating reversing GL entries.
    """
    from zoho_books_clone.accounts.accounting_engine import reverse_voucher

    doc = frappe.get_doc("Payment Entry", payment_entry)
    if doc.docstatus != 1:
        frappe.throw(_("Payment Entry {0} is not submitted — cannot reverse.").format(payment_entry))

    reverse_voucher("Payment Entry", payment_entry)
    return {"payment_entry": payment_entry, "status": "GL Reversed"}


@frappe.whitelist(allow_guest=False, methods=["POST"])
def post_bank_transfer(
    from_account: str,
    to_account: str,
    amount: str,
    date: str = None,
    description: str = "",
) -> dict:
    """
    Transfer funds between two bank accounts.

    GL impact:
      DR  to_account.gl_account   (funds arrive)
      CR  from_account.gl_account (funds leave)

    Creates a Bank Transaction record on each account for reconciliation.
    No income/expense impact — pure asset swap.
    """
    amount_f = flt(amount)
    if amount_f <= 0:
        frappe.throw(_("Transfer amount must be positive."))
    if from_account == to_account:
        frappe.throw(_("Source and destination account must be different."))

    date = date or today()
    from_gl = _bank_gl(from_account)
    to_gl   = _bank_gl(to_account)
    company = _company(from_account)
    remark  = description or f"Transfer from {from_account} to {to_account}"

    # Bank Transaction — source account (withdrawal / debit).
    # skip_gl_posting flag: this API posts a single combined GL set below,
    # so the per-transaction _post_gl must not run (would double-post).
    bt_from = frappe.get_doc({
        "doctype": "Bank Transaction",
        "bank_account": from_account,
        "date": date,
        "description": f"Transfer to {to_account}" + (f" — {description}" if description else ""),
        "debit": amount_f,
        "credit": 0,
        "transaction_type": "Transfer",
        "status": "Reconciled",
    })
    bt_from.flags.ignore_permissions = True
    bt_from.flags.skip_gl_posting = True
    bt_from.insert()
    bt_from.submit()

    # Bank Transaction — destination account (deposit / credit)
    bt_to = frappe.get_doc({
        "doctype": "Bank Transaction",
        "bank_account": to_account,
        "date": date,
        "description": f"Transfer from {from_account}" + (f" — {description}" if description else ""),
        "debit": 0,
        "credit": amount_f,
        "transaction_type": "Transfer",
        "status": "Reconciled",
    })
    bt_to.flags.ignore_permissions = True
    bt_to.flags.skip_gl_posting = True
    bt_to.insert()
    bt_to.submit()

    # GL: DR to_gl / CR from_gl
    make_gl_entries([
        {
            "account": to_gl,
            "debit": amount_f,
            "credit": 0,
            "posting_date": date,
            "voucher_type": "Bank Transaction",
            "voucher_no": bt_from.name,
            "company": company,
            "remarks": remark,
        },
        {
            "account": from_gl,
            "debit": 0,
            "credit": amount_f,
            "posting_date": date,
            "voucher_type": "Bank Transaction",
            "voucher_no": bt_from.name,
            "company": company,
            "remarks": remark,
        },
    ])

    # Recalculate and persist the live balance for both accounts immediately
    # so the Bank Accounts page shows the correct number without a manual refresh.
    from_balance = _recalc_balance(from_account)
    to_balance   = _recalc_balance(to_account)
    frappe.db.commit()

    return {
        "from_transaction": bt_from.name,
        "to_transaction":   bt_to.name,
        "amount":           amount_f,
        "from_account":     from_account,
        "to_account":       to_account,
        "from_balance":     from_balance,
        "to_balance":       to_balance,
    }


@frappe.whitelist(allow_guest=False, methods=["POST"])
def create_bank_gl_entry(
    bank_account: str,
    bank_transaction: str,
    gl_account: str,
    amount: str,
    txn_type: str,
    date: str = None,
    description: str = "",
) -> dict:
    """
    Create a GL Journal Entry for an unmatched bank transaction, then mark
    the transaction as Reconciled.

    txn_type "Debit"  (withdrawal / charge):
      DR  gl_account   (expense)
      CR  bank_gl      (bank decreases)

    txn_type "Credit" (deposit / interest):
      DR  bank_gl      (bank increases)
      CR  gl_account   (income)
    """
    amount_f = flt(amount)
    date = date or today()
    bank_gl  = _bank_gl(bank_account)
    company  = _company(bank_account)
    remark   = description or f"Bank entry: {bank_transaction}"

    if txn_type == "Debit":
        entries = [
            {"account": gl_account, "debit": amount_f, "credit": 0},
            {"account": bank_gl,    "debit": 0,        "credit": amount_f},
        ]
    else:
        entries = [
            {"account": bank_gl,    "debit": amount_f, "credit": 0},
            {"account": gl_account, "debit": 0,        "credit": amount_f},
        ]

    for e in entries:
        e.update({
            "posting_date": date,
            "voucher_type": "Bank Transaction",
            "voucher_no": bank_transaction,
            "company": company,
            "remarks": remark,
        })

    make_gl_entries(entries)

    # Mark Bank Transaction as Reconciled
    try:
        doc = frappe.get_doc("Bank Transaction", bank_transaction)
        if doc.docstatus == 1:
            doc.status = "Reconciled"
            doc.clearance_date = date
            doc.save(ignore_permissions=True)
        frappe.db.commit()
    except Exception:
        pass

    return {
        "bank_transaction": bank_transaction,
        "gl_account": gl_account,
        "amount": amount_f,
        "txn_type": txn_type,
    }
@frappe.whitelist(allow_guest=False, methods=["POST"])
def reconcile_transactions(bank_account: str, transaction_names: str, clearance_date: str = None) -> dict:
    """
    Mark a list of Bank Transactions as Reconciled.
    transaction_names: JSON-encoded list of Bank Transaction names.
    """
    import json
    names = json.loads(transaction_names or "[]")
    if not names:
        frappe.throw(_("No transactions provided."))

    date = clearance_date or today()
    ok = 0; fail = 0
    for name in names:
        try:
            doc = frappe.get_doc("Bank Transaction", name)
            if doc.docstatus == 1 and doc.status != "Reconciled":
                doc.status = "Reconciled"
                doc.clearance_date = date
                doc.save(ignore_permissions=True)
                ok += 1
        except Exception:
            fail += 1

    frappe.db.commit()
    # Refresh current_balance for the account
    live = _recalc_balance(bank_account)
    return {"ok": ok, "fail": fail, "current_balance": live}


@frappe.whitelist(allow_guest=False, methods=["POST"])
def mark_transaction_reconciled(bank_transaction: str, clearance_date: str = None) -> dict:
    """
    Mark a single Bank Transaction as Reconciled.
    """
    date = clearance_date or today()
    doc = frappe.get_doc("Bank Transaction", bank_transaction)
    if doc.docstatus != 1:
        frappe.throw(_("Transaction {0} is not submitted.").format(bank_transaction))
    doc.status = "Reconciled"
    doc.clearance_date = date
    doc.save(ignore_permissions=True)
    frappe.db.commit()
    live = _recalc_balance(doc.bank_account)
    return {"bank_transaction": bank_transaction, "status": "Reconciled", "current_balance": live}


@frappe.whitelist(allow_guest=False, methods=["POST"])
def delete_bank_account(name: str) -> dict:
    """
    Fully delete a Bank Account and all its linked Bank Transactions / GL entries.

    Steps:
      1. Cancel + delete all submitted Bank Transactions for this account.
      2. Delete draft Bank Transactions.
      3. Delete GL Entries whose voucher_no was one of those transactions.
      4. Delete the Bank Account document itself.

    Uses ignore_permissions=True throughout so the Books Manager role
    can perform the deletion without a native Frappe delete permission.
    """
    if frappe.session.user == "Guest":
        frappe.throw(_("Not permitted"), frappe.PermissionError)

    if not frappe.db.exists("Bank Account", name):
        frappe.throw(_("Bank Account {0} does not exist.").format(name))

    # 1. Collect all linked Bank Transactions
    txn_names = frappe.db.get_all(
        "Bank Transaction",
        filters={"bank_account": name},
        pluck="name",
    )

    deleted_txns = []
    for txn_name in txn_names:
        try:
            doc = frappe.get_doc("Bank Transaction", txn_name)
            if doc.docstatus == 1:
                doc.flags.ignore_permissions = True
                doc.cancel()
            frappe.delete_doc(
                "Bank Transaction", txn_name,
                ignore_permissions=True,
                force=True,
            )
            deleted_txns.append(txn_name)
        except Exception as e:
            frappe.log_error("Could not delete Bank Transaction {0}: {1}".format(txn_name, e))

    # 2. Delete GL entries for those transactions
    if deleted_txns:
        frappe.db.delete(
            "General Ledger Entry",
            {"voucher_type": "Bank Transaction", "voucher_no": ["in", deleted_txns]},
        )

    # 3. Delete the Bank Account
    frappe.delete_doc("Bank Account", name, ignore_permissions=True, force=True)
    frappe.db.commit()

    return {"deleted": name, "transactions_removed": len(deleted_txns)}


@frappe.whitelist(allow_guest=False, methods=["POST"])
def save_cheque(data):
    """
    Dedicated endpoint to safely create or update a Cheque (Payment Entry).
    Accepts simple parameters from the frontend and resolves the complex GL
    account requirements (paid_from, paid_to) automatically.
    """
    import json
    if isinstance(data, str):
        data = json.loads(data)

    name = data.get("name")
    payment_type = data.get("payment_type") # "Receive" or "Pay"
    bank_account_name = data.get("bank_account")
    party = data.get("party")
    party_type = data.get("party_type")
    company = _get_company(frappe.session.user)

    if not company:
        frappe.throw("Company is required")

    # Resolve the Bank GL Account
    bank_gl = _bank_gl(bank_account_name)

    # Resolve AR/AP Account
    if payment_type == "Receive":
        ar_ap_gl = frappe.db.get_value("Account", {"account_type": "Receivable", "company": company, "is_group": 0}, "name")
        paid_from = ar_ap_gl
        paid_to = bank_gl
    else:
        ar_ap_gl = frappe.db.get_value("Account", {"account_type": "Payable", "company": company, "is_group": 0}, "name")
        paid_from = bank_gl
        paid_to = ar_ap_gl

    if not ar_ap_gl:
        frappe.throw(f"No default {'Receivable' if payment_type == 'Receive' else 'Payable'} account found for company {company}")

    doc = {
        "doctype": "Payment Entry",
        "payment_type": payment_type,
        "mode_of_payment": "Cheque",
        "party_type": party_type,
        "party": party,
        "company": company,
        "paid_from": paid_from,
        "paid_to": paid_to,
        "paid_amount": flt(data.get("paid_amount")),
        "payment_date": data.get("payment_date"),
        "reference_no": data.get("reference_no"),
        "reference_date": data.get("reference_date"),
        "remarks": data.get("remarks"),
        "status": data.get("status", "Issued")
    }

    if name and frappe.db.exists("Payment Entry", name):
        d = frappe.get_doc("Payment Entry", name)
        is_submitted = d.docstatus == 1
        d.update(doc)
        if is_submitted:
            d.flags.ignore_validate_update_after_submit = True
        d.save(ignore_permissions=True)
    else:
        d = frappe.get_doc(doc)
        d.insert(ignore_permissions=True)
    
    frappe.db.commit()
    return d.as_dict()
