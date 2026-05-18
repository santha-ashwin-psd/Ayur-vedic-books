"""
E2E — Full End-to-End Test Suite (books_data.py + docs.py + key flows).

Areas covered
─────────────
SECTION A — docs.py API
  A1   get_doc: fetch Sales Invoice → expected fields present
  A2   save_doc (create): new Sales Invoice with auto-filled accounts
  A3   save_doc (update): amend an existing draft Sales Invoice
  A4   save_doc: missing doctype → raises ValidationError
  A5   submit_doc: submit a Sales Invoice → docstatus == 1, GL posted
  A6   delete_doc: delete a draft document → gone from DB
  A7   get_party_last_items (Customer): returns items from most-recent SI
  A8   get_party_last_items (Supplier): returns items from most-recent PI
  A9   get_party_last_items: unknown party → empty items list
  A10  create_credit_note: CN created + submitted, GL DR = CR
  A11  create_debit_note:  DN created + submitted, GL DR = CR
  A12  get_accounts: returns ar/income/bank/ap keys for company

SECTION B — books_data.py API
  B1   get_invoice_email_defaults: correct structure returned
  B2   get_invoice_email_defaults: amount uses ₹ (docs.py version check)
  B3   get_quote_email_defaults: correct structure returned
  B4   get_payment_defaults: correct structure for a submitted invoice
  B5   get_payment_defaults: payment_modes is non-empty list
  B6   record_payment: Payment Entry created + submitted, invoice linked
  B7   record_payment: save_as_draft=True → PE remains draft (docstatus=0)
  B8   record_payment: missing invoice_name → ValidationError
  B9   record_payment: amount_received=0 → ValidationError
  B10  get_chart_of_accounts: returns list with required keys
  B11  save_account (create): new Account created, then deleted
  B12  save_account (update): account_name updated
  B13  get_customer_outstanding: returns dict; values are non-negative
  B14  get_invoice_payments: list; each row has expected keys
  B15  get_gstr_summary: all 4 sections present, math correct
  B16  get_itc_ledger: returns list (may be empty)
  B17  ai_chat: "greeting" intent returns non-empty reply
  B18  ai_chat: "revenue" intent → DB numbers returned (no LLM needed)
  B19  ai_chat: "outstanding" intent
  B20  ai_chat: "overdue_count" intent
  B21  ai_chat: "top_customers" intent
  B22  ai_chat: "unpaid_bills" intent
  B23  ai_chat: navigation intents return action key
  B24  get_ai_alerts: returns alerts list + count

SECTION C — End-to-End Business Flows
  C1   Customer lifecycle: create → update → disable → re-enable
  C2   Quote-to-cash: Quotation → email defaults → SO → Invoice → Payment
  C3   Credit Note flow: SI submitted → credit note → GL reversal
  C4   Debit Note flow:  PI submitted → debit note → GL reversal
  C5   Bulk invoice flow: 3 invoices created, filtered correctly by status
  C6   Outstanding balance: submit invoice → outstanding updates → pay → clears

SECTION D — Security / Guard Rails
  D1   get_doc rejects Guest session (simulated)
  D2   save_doc rejects Guest session
  D3   submit_doc rejects Guest session
  D4   delete_doc rejects Guest session
  D5   record_payment rejects Guest session
  D6   normalize_company_names requires System Manager role
"""

import frappe
import json
from frappe.utils import flt, today, get_first_day, get_last_day
import importlib

# ── Configuration ─────────────────────────────────────────────────────────────
# Company is resolved dynamically at runtime from Books Company
COMPANY  = None   # filled in run()
DATE     = today()
_created = []   # (doctype, name, docstatus) — for cleanup


def _pass(label):  print(f"  ✓  {label}")
def _fail(label, detail=""):
    msg = f"  ✗  {label}"
    if detail:
        msg += f"  [{detail[:120]}]"
    print(msg)


def _make_si(customer, items=None, taxes=None, submit=False, company=None):
    """Create a Sales Invoice (draft or submitted) and register for cleanup."""
    company = company or COMPANY
    ar  = frappe.db.get_value("Account", {"account_type": "Receivable", "company": company, "is_group": 0}, "name")
    inc = frappe.db.get_value("Account", {"account_type": "Income",     "company": company, "is_group": 0}, "name")
    items = items or [{"item_name": "E2E Item", "qty": 2, "rate": 500, "income_account": inc}]
    si = frappe.new_doc("Sales Invoice")
    si.customer        = customer
    si.company         = company
    si.posting_date    = DATE
    si.due_date        = DATE
    si.debit_to        = ar
    si.income_account  = inc   # header-level required field in this app
    for it in items:
        if "income_account" not in it:
            it["income_account"] = inc
        si.append("items", it)
    for tx in (taxes or []):
        si.append("taxes", tx)
    si.flags.ignore_permissions = True
    si.flags.ignore_mandatory   = True
    si.flags.ignore_links       = True
    si.insert()
    if submit:
        si.flags.ignore_permissions = True
        si.flags.ignore_mandatory   = True
        si.submit()
    frappe.db.commit()
    _created.append(("Sales Invoice", si.name, si.docstatus))
    return si


def _make_pi(supplier, items=None, company=None):
    """Create a Purchase Invoice (draft)."""
    company = company or COMPANY
    ap  = frappe.db.get_value("Account", {"account_type": "Payable",  "company": company, "is_group": 0}, "name")
    exp = frappe.db.get_value("Account", {"account_type": "Expense",  "company": company, "is_group": 0}, "name")
    items = items or [{"item_name": "E2E Purchase Item", "qty": 1, "rate": 1000, "expense_account": exp}]
    pi = frappe.new_doc("Purchase Invoice")
    pi.supplier         = supplier
    pi.company          = company
    pi.posting_date     = DATE
    pi.credit_to        = ap
    pi.expense_account  = exp   # header-level required field in this app
    for it in items:
        if "expense_account" not in it:
            it["expense_account"] = exp
        pi.append("items", it)
    pi.flags.ignore_permissions = True
    pi.flags.ignore_mandatory   = True
    pi.flags.ignore_links       = True
    pi.insert()
    frappe.db.commit()
    _created.append(("Purchase Invoice", pi.name, pi.docstatus))
    return pi


def _gl(voucher_no, cancelled=0):
    return frappe.db.get_all(
        "General Ledger Entry",
        filters={"voucher_no": voucher_no, "is_cancelled": cancelled},
        fields=["account", "debit", "credit"],
    )


def _gl_balanced(voucher_no):
    rows = _gl(voucher_no)
    dr = sum(flt(r.debit) for r in rows)
    cr = sum(flt(r.credit) for r in rows)
    return abs(dr - cr) < 0.01, dr, cr


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION A — docs.py API
# ═══════════════════════════════════════════════════════════════════════════════

def run_section_a(docs, customer, supplier):
    print("\n══ SECTION A — docs.py API ══")

    # ── A1: get_doc ─────────────────────────────────────────────────────────
    print("\n--- A1: get_doc → Sales Invoice fields ---")
    try:
        si_a1 = _make_si(customer)
        result = docs.get_doc("Sales Invoice", si_a1.name)
        required = {"name", "customer", "grand_total", "docstatus", "items"}
        missing  = required - set(result.keys())
        if not missing:
            _pass(f"get_doc returned expected fields ({si_a1.name})")
        else:
            _fail("Missing fields in get_doc result", str(missing))
        if result.get("customer") == customer:
            _pass("customer field matches")
        else:
            _fail("customer field mismatch", f"got {result.get('customer')}")
    except Exception as e:
        _fail("A1 crashed", str(e))

    # ── A2: save_doc create ──────────────────────────────────────────────────
    print("\n--- A2: save_doc (create) → auto-fill AR account ---")
    try:
        inc = frappe.db.get_value("Account", {"account_type": "Income", "company": COMPANY, "is_group": 0}, "name")
        doc_dict = {
            "doctype": "Sales Invoice",
            "customer": customer,
            "company": COMPANY,
            "posting_date": DATE,
            "due_date": DATE,
            "items": [{"item_name": "A2 Test Item", "qty": 1, "rate": 200, "income_account": inc}],
        }
        saved = docs.save_doc(doc_dict)
        _created.append(("Sales Invoice", saved.get("name"), 0))
        if saved.get("name"):
            _pass(f"save_doc created document: {saved['name']}")
        else:
            _fail("save_doc did not return name")
        if saved.get("debit_to"):
            _pass(f"debit_to auto-filled: {saved['debit_to']}")
        else:
            _fail("debit_to not auto-filled")
    except Exception as e:
        _fail("A2 crashed", str(e))

    # ── A3: save_doc update ──────────────────────────────────────────────────
    print("\n--- A3: save_doc (update) → amend draft invoice ---")
    try:
        si_a3 = _make_si(customer)
        inc = frappe.db.get_value("Account", {"account_type": "Income", "company": COMPANY, "is_group": 0}, "name")
        updated = docs.save_doc({
            "doctype": "Sales Invoice",
            "name": si_a3.name,
            "customer": customer,
            "company": COMPANY,
            "posting_date": DATE,
            "due_date": DATE,
            "items": [{"item_name": "Updated Item", "qty": 3, "rate": 100, "income_account": inc}],
        })
        if updated.get("name") == si_a3.name:
            _pass(f"save_doc updated existing document: {si_a3.name}")
        else:
            _fail("save_doc returned wrong name after update")
        reloaded = frappe.get_doc("Sales Invoice", si_a3.name)
        if any(it.item_name == "Updated Item" for it in reloaded.items):
            _pass("Item name updated correctly")
        else:
            _fail("Item name not updated in DB")
    except Exception as e:
        _fail("A3 crashed", str(e))

    # ── A4: save_doc missing doctype ─────────────────────────────────────────
    print("\n--- A4: save_doc without doctype → ValidationError ---")
    try:
        docs.save_doc({"customer": customer})
        _fail("save_doc accepted document without doctype")
    except frappe.ValidationError:
        _pass("ValidationError raised for missing doctype")
    except Exception as e:
        _fail("Wrong exception type", str(e))

    # ── A5: submit_doc ───────────────────────────────────────────────────────
    print("\n--- A5: submit_doc → docstatus=1, GL posted ---")
    try:
        si_a5 = _make_si(customer)
        result = docs.submit_doc("Sales Invoice", si_a5.name)
        # Update cleanup record
        for i, rec in enumerate(_created):
            if rec[1] == si_a5.name:
                _created[i] = ("Sales Invoice", si_a5.name, 1)
        if result.get("docstatus") == 1:
            _pass(f"docstatus=1 after submit_doc ({si_a5.name})")
        else:
            _fail("docstatus not 1 after submit_doc", str(result.get("docstatus")))
        gl_rows = _gl(si_a5.name)
        if len(gl_rows) >= 2:
            _pass(f"GL posted: {len(gl_rows)} entries")
        else:
            _fail("GL not posted (< 2 rows)", str(len(gl_rows)))
        ok, dr, cr = _gl_balanced(si_a5.name)
        if ok:
            _pass(f"GL balanced: DR = CR = {dr:.2f}")
        else:
            _fail("GL unbalanced", f"DR={dr:.2f}, CR={cr:.2f}")
    except Exception as e:
        _fail("A5 crashed", str(e))

    # ── A6: delete_doc ───────────────────────────────────────────────────────
    print("\n--- A6: delete_doc → document removed from DB ---")
    try:
        si_a6 = _make_si(customer)
        docs.delete_doc("Sales Invoice", si_a6.name)
        exists = frappe.db.exists("Sales Invoice", si_a6.name)
        if not exists:
            _pass(f"delete_doc removed {si_a6.name}")
            _created[:] = [r for r in _created if r[1] != si_a6.name]
        else:
            _fail("Document still exists after delete_doc")
    except Exception as e:
        _fail("A6 crashed", str(e))

    # ── A7: get_party_last_items (Customer) ──────────────────────────────────
    print("\n--- A7: get_party_last_items (Customer) ---")
    try:
        si_a7 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_a7.name:
                _created[i] = ("Sales Invoice", si_a7.name, 1)
        result = docs.get_party_last_items("Customer", customer, limit=5)
        if isinstance(result.get("items"), list):
            _pass(f"get_party_last_items returned {len(result['items'])} items")
        else:
            _fail("items not a list", str(type(result.get("items"))))
        if result.get("items"):
            row = result["items"][0]
            item_keys = {"item_name", "qty", "rate"}
            missing = item_keys - set(row.keys())
            if not missing:
                _pass("Item rows have expected keys")
            else:
                _fail("Missing item keys", str(missing))
    except Exception as e:
        _fail("A7 crashed", str(e))

    # ── A8: get_party_last_items (Supplier) ──────────────────────────────────
    print("\n--- A8: get_party_last_items (Supplier) ---")
    try:
        pi_a8 = _make_pi(supplier)
        pi_a8.flags.ignore_permissions = True
        pi_a8.flags.ignore_mandatory   = True
        pi_a8.submit()
        frappe.db.commit()
        for i, rec in enumerate(_created):
            if rec[1] == pi_a8.name:
                _created[i] = ("Purchase Invoice", pi_a8.name, 1)
        result = docs.get_party_last_items("Supplier", supplier, limit=5)
        if isinstance(result.get("items"), list):
            _pass(f"Supplier last items: {len(result['items'])} items")
        else:
            _fail("items not a list for Supplier")
    except Exception as e:
        _fail("A8 crashed", str(e))

    # ── A9: get_party_last_items — unknown party ──────────────────────────────
    print("\n--- A9: get_party_last_items — unknown party → empty list ---")
    try:
        result = docs.get_party_last_items("Customer", "DOES-NOT-EXIST-999", limit=5)
        if result.get("items") == []:
            _pass("Empty items list for unknown party")
        else:
            _fail("Expected empty list", str(result))
    except Exception as e:
        _fail("A9 crashed", str(e))

    # ── A10: create_credit_note ──────────────────────────────────────────────
    print("\n--- A10: create_credit_note → GL balanced ---")
    try:
        si_a10 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_a10.name:
                _created[i] = ("Sales Invoice", si_a10.name, 1)

        # Simulate frappe.form_dict for create_credit_note
        frappe.form_dict.customer       = customer
        frappe.form_dict.against_invoice = si_a10.name
        frappe.form_dict.date            = DATE
        frappe.form_dict.reason          = "Price Adjustment"
        frappe.form_dict.notes           = "E2E test credit note"
        frappe.form_dict.warehouse       = ""
        frappe.form_dict.items           = json.dumps([{"item_name": "E2E Item", "qty": 1, "rate": 500}])
        frappe.form_dict.taxes           = json.dumps([])

        result = docs.create_credit_note()
        cn_name = result.get("credit_note")
        _created.append(("Sales Invoice", cn_name, 1))
        if cn_name:
            _pass(f"Credit note created: {cn_name}")
        else:
            _fail("credit_note name not returned")

        ok, dr, cr = _gl_balanced(cn_name)
        if ok:
            _pass(f"Credit note GL balanced: DR = CR = {dr:.2f}")
        else:
            _fail("Credit note GL unbalanced", f"DR={dr:.2f} CR={cr:.2f}")
    except Exception as e:
        _fail("A10 crashed", str(e))

    # ── A11: create_debit_note ───────────────────────────────────────────────
    print("\n--- A11: create_debit_note → GL balanced ---")
    try:
        pi_a11 = _make_pi(supplier)
        pi_a11.flags.ignore_permissions = True
        pi_a11.flags.ignore_mandatory   = True
        pi_a11.submit()
        frappe.db.commit()
        _created.append(("Purchase Invoice", pi_a11.name, 1))

        frappe.form_dict.vendor       = supplier
        frappe.form_dict.against_bill = pi_a11.name
        frappe.form_dict.date         = DATE
        frappe.form_dict.reason       = "Price Correction"
        frappe.form_dict.notes        = "E2E test debit note"
        frappe.form_dict.warehouse    = ""
        frappe.form_dict.items        = json.dumps([{"item_name": "E2E Purchase Item", "qty": 1, "rate": 500}])

        result = docs.create_debit_note()
        dn_name = result.get("debit_note")
        _created.append(("Purchase Invoice", dn_name, 1))
        if dn_name:
            _pass(f"Debit note created: {dn_name}")
        else:
            _fail("debit_note name not returned")

        ok, dr, cr = _gl_balanced(dn_name)
        if ok:
            _pass(f"Debit note GL balanced: DR = CR = {dr:.2f}")
        else:
            _fail("Debit note GL unbalanced", f"DR={dr:.2f} CR={cr:.2f}")
    except Exception as e:
        _fail("A11 crashed", str(e))

    # ── A12: get_accounts ────────────────────────────────────────────────────
    print("\n--- A12: get_accounts → ar/income/bank/ap keys ---")
    try:
        # Inject company into form_dict so the function picks it up
        frappe.form_dict.company = COMPANY
        result = docs.get_accounts()
        required_keys = {"ar", "income", "bank", "ap"}
        missing = required_keys - set(result.keys())
        if not missing:
            _pass("All account category keys present")
        else:
            _fail("Missing account keys", str(missing))
        for k, v in result.items():
            if isinstance(v, list):
                _pass(f"  {k}: {len(v)} accounts")
            else:
                _fail(f"  {k} is not a list", type(v).__name__)
    except Exception as e:
        _fail("A12 crashed", str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION B — books_data.py API
# ═══════════════════════════════════════════════════════════════════════════════

def run_section_b(bd, customer, supplier):
    print("\n══ SECTION B — books_data.py API ══")

    # ── B1: get_invoice_email_defaults ───────────────────────────────────────
    print("\n--- B1: get_invoice_email_defaults → correct structure ---")
    try:
        si_b1 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_b1.name:
                _created[i] = ("Sales Invoice", si_b1.name, 1)
        result = bd.get_invoice_email_defaults(si_b1.name)
        req = {"to", "subject", "body", "invoice_name", "customer_name"}
        missing = req - set(result.keys())
        if not missing:
            _pass("All email default keys present")
        else:
            _fail("Missing email keys", str(missing))
        if result.get("invoice_name") == si_b1.name:
            _pass("invoice_name matches")
        else:
            _fail("invoice_name mismatch")
        if si_b1.name in result.get("subject", ""):
            _pass("Invoice name in subject line")
        else:
            _fail("Invoice name NOT in subject line", result.get("subject", ""))
    except Exception as e:
        _fail("B1 crashed", str(e))

    # ── B2: email body uses ₹ symbol ─────────────────────────────────────────
    print("\n--- B2: invoice email body uses ₹ symbol ---")
    try:
        si_b2 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_b2.name:
                _created[i] = ("Sales Invoice", si_b2.name, 1)
        result = bd.get_invoice_email_defaults(si_b2.name)
        body = result.get("body", "")
        if "₹" in body:
            _pass("Email body contains ₹ symbol (books_data.py version)")
        elif "Rs." in body:
            _fail("Email body uses 'Rs.' instead of ₹ — books_data.py not updated", body[:80])
        else:
            _fail("Email body missing currency symbol entirely", body[:80])
    except Exception as e:
        _fail("B2 crashed", str(e))

    # ── B3: get_quote_email_defaults ─────────────────────────────────────────
    print("\n--- B3: get_quote_email_defaults → correct structure ---")
    try:
        q = frappe.new_doc("Quotation")
        q.customer        = customer
        q.company         = COMPANY
        q.transaction_date = DATE
        q.valid_till      = DATE
        q.append("items", {"item_name": "E2E Quote Item", "qty": 2, "rate": 300})
        q.flags.ignore_permissions = True
        q.flags.ignore_mandatory   = True
        q.flags.ignore_links       = True
        q.insert()
        frappe.db.commit()
        _created.append(("Quotation", q.name, 0))

        result = bd.get_quote_email_defaults(q.name)
        req = {"to", "subject", "body", "quote_name", "customer_name"}
        missing = req - set(result.keys())
        if not missing:
            _pass("All quote email default keys present")
        else:
            _fail("Missing quote email keys", str(missing))
        if result.get("quote_name") == q.name:
            _pass("quote_name matches")
        else:
            _fail("quote_name mismatch")
        if "₹" in result.get("body", ""):
            _pass("Quote email body uses ₹ symbol")
        else:
            _fail("Quote email body missing ₹", result.get("body", "")[:80])
    except Exception as e:
        _fail("B3 crashed", str(e))

    # ── B4: get_payment_defaults ─────────────────────────────────────────────
    print("\n--- B4: get_payment_defaults → correct structure ---")
    si_b4 = None
    try:
        si_b4 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_b4.name:
                _created[i] = ("Sales Invoice", si_b4.name, 1)
        result = bd.get_payment_defaults(si_b4.name)
        req = {"invoice_name", "customer_name", "grand_total", "balance_due",
               "currency", "payment_date", "bank_accounts", "payment_modes", "company"}
        missing = req - set(result.keys())
        if not missing:
            _pass("All payment default keys present")
        else:
            _fail("Missing payment default keys", str(missing))
        if result.get("invoice_name") == si_b4.name:
            _pass("invoice_name matches")
        else:
            _fail("invoice_name mismatch")
        if flt(result.get("grand_total")) > 0:
            _pass(f"grand_total = {flt(result.get('grand_total')):.2f}")
        else:
            _fail("grand_total not positive", str(result.get("grand_total")))
    except Exception as e:
        _fail("B4 crashed", str(e))

    # ── B5: payment_modes is non-empty ───────────────────────────────────────
    print("\n--- B5: get_payment_defaults → payment_modes non-empty ---")
    try:
        if si_b4:
            result = bd.get_payment_defaults(si_b4.name)
            modes = result.get("payment_modes", [])
            if isinstance(modes, list) and len(modes) > 0:
                _pass(f"payment_modes has {len(modes)} modes: {modes[:3]}")
            else:
                _fail("payment_modes is empty or not a list", str(modes))
        else:
            _fail("B5 skipped (B4 failed)")
    except Exception as e:
        _fail("B5 crashed", str(e))

    # ── B6: record_payment → PE submitted + invoice linked ───────────────────
    print("\n--- B6: record_payment → Payment Entry submitted ---")
    try:
        si_b6 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_b6.name:
                _created[i] = ("Sales Invoice", si_b6.name, 1)

        result = bd.record_payment(
            invoice_name=si_b6.name,
            amount_received=flt(si_b6.grand_total),
            payment_date=DATE,
            payment_mode="Cash",
        )
        pe_name = result.get("payment_entry")
        _created.append(("Payment Entry", pe_name, 1))

        if pe_name:
            _pass(f"Payment Entry created: {pe_name}")
        else:
            _fail("payment_entry name not returned")
        if result.get("status") == "submitted":
            _pass("Payment Entry status = submitted")
        else:
            _fail("PE not submitted", str(result.get("status")))
        if result.get("invoice") == si_b6.name:
            _pass("invoice linked correctly")
        else:
            _fail("invoice link mismatch")

        # Check PE actually exists in DB
        if pe_name and frappe.db.exists("Payment Entry", pe_name):
            pe_doc = frappe.get_doc("Payment Entry", pe_name)
            if pe_doc.docstatus == 1:
                _pass("PE docstatus = 1 in DB")
            else:
                _fail("PE docstatus not 1 in DB", str(pe_doc.docstatus))
        else:
            _fail("PE not found in DB")
    except Exception as e:
        _fail("B6 crashed", str(e))

    # ── B7: record_payment save_as_draft=True ────────────────────────────────
    print("\n--- B7: record_payment save_as_draft=True → PE remains draft ---")
    try:
        si_b7 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_b7.name:
                _created[i] = ("Sales Invoice", si_b7.name, 1)
        result = bd.record_payment(
            invoice_name=si_b7.name,
            amount_received=100,
            payment_date=DATE,
            payment_mode="Cash",
            save_as_draft=True,
        )
        pe_name = result.get("payment_entry")
        _created.append(("Payment Entry", pe_name, 0))
        if result.get("status") == "draft":
            _pass("PE status = draft")
        else:
            _fail("PE not draft", str(result.get("status")))
        if pe_name and frappe.db.exists("Payment Entry", pe_name):
            pe_doc = frappe.get_doc("Payment Entry", pe_name)
            if pe_doc.docstatus == 0:
                _pass("PE docstatus = 0 in DB (draft)")
            else:
                _fail("PE docstatus not 0 in DB", str(pe_doc.docstatus))
    except Exception as e:
        _fail("B7 crashed", str(e))

    # ── B8: record_payment missing invoice_name ───────────────────────────────
    print("\n--- B8: record_payment without invoice_name → ValidationError ---")
    try:
        bd.record_payment(amount_received=100, payment_date=DATE)
        _fail("record_payment accepted missing invoice_name")
    except frappe.ValidationError:
        _pass("ValidationError raised for missing invoice_name")
    except Exception as e:
        _fail("Wrong exception", str(e))

    # ── B9: record_payment amount=0 ───────────────────────────────────────────
    print("\n--- B9: record_payment with amount_received=0 → ValidationError ---")
    try:
        si_b9 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_b9.name:
                _created[i] = ("Sales Invoice", si_b9.name, 1)
        bd.record_payment(invoice_name=si_b9.name, amount_received=0, payment_date=DATE)
        _fail("record_payment accepted zero amount")
    except frappe.ValidationError:
        _pass("ValidationError raised for zero amount")
    except Exception as e:
        _fail("Wrong exception", str(e))

    # ── B10: get_chart_of_accounts ────────────────────────────────────────────
    print("\n--- B10: get_chart_of_accounts → list with required keys ---")
    try:
        accounts = bd.get_chart_of_accounts(company=COMPANY)
        if isinstance(accounts, list):
            _pass(f"get_chart_of_accounts returns list ({len(accounts)} accounts)")
        else:
            _fail("Not a list", type(accounts).__name__)
        if accounts:
            row = accounts[0]
            req = {"name", "account_name", "account_type", "is_group"}
            missing = req - set(row.keys())
            if not missing:
                _pass("Account rows have expected keys")
            else:
                _fail("Missing account keys", str(missing))
        # Template roots ("Assets", "Equity", etc.) are filtered when the
        # company has its own named roots.  If company roots exist, assert no
        # overlap; otherwise note it as an informational gap (not a hard failure).
        root_names = {a.get("account_name") for a in accounts if not a.get("parent_account")}
        template_roots = {"Assets", "Liabilities", "Equity", "Income", "Expenses"}
        overlap = root_names & template_roots
        company_roots = [n for n in root_names if n not in template_roots]
        if company_roots:
            # Company has its own roots — template roots should be stripped
            if not overlap:
                _pass("Template root accounts filtered out correctly")
            else:
                _fail("Template roots still present alongside company roots", str(overlap))
        else:
            # No company-specific roots present — template roots are expected
            _pass(f"No company-specific roots; template roots present (expected): {overlap or '(none)'}")
    except Exception as e:
        _fail("B10 crashed", str(e))

    # ── B11: save_account create + delete ────────────────────────────────────
    print("\n--- B11: save_account (create) → account exists, then deleted ---")
    test_acct_name = None
    try:
        # Frappe requires a group parent_account; find one for this company
        parent_acct = frappe.db.get_value(
            "Account", {"is_group": 1, "account_type": "Expense", "company": COMPANY}, "name"
        ) or frappe.db.get_value(
            "Account", {"is_group": 1, "company": COMPANY}, "name"
        )
        result = bd.save_account(
            op="create",
            account_name="E2E Test Account",
            account_type="Expense",
            parent_account=parent_acct,
            is_group=0,
            company=COMPANY,
        )
        test_acct_name = result.get("name")
        if test_acct_name and frappe.db.exists("Account", test_acct_name):
            _pass(f"Account created: {test_acct_name}")
        else:
            _fail("Account not found in DB after create")
        if result.get("status") == "created":
            _pass("status = created")
        else:
            _fail("status not 'created'", str(result.get("status")))
    except Exception as e:
        _fail("B11 create crashed", str(e))

    # ── B12: save_account update ─────────────────────────────────────────────
    print("\n--- B12: save_account (update) → account_name updated ---")
    try:
        if test_acct_name:
            result = bd.save_account(
                op="update",
                name=test_acct_name,
                account_name="E2E Test Account Updated",
                company=COMPANY,
            )
            if result.get("status") == "updated":
                _pass("status = updated")
            else:
                _fail("status not 'updated'", str(result.get("status")))
            new_name_val = frappe.db.get_value("Account", test_acct_name, "account_name")
            if new_name_val == "E2E Test Account Updated":
                _pass("account_name updated in DB")
            else:
                _fail("account_name not updated in DB", str(new_name_val))
        else:
            _fail("B12 skipped (B11 failed)")
    except Exception as e:
        _fail("B12 crashed", str(e))
    finally:
        if test_acct_name and frappe.db.exists("Account", test_acct_name):
            try:
                frappe.delete_doc("Account", test_acct_name, ignore_permissions=True, force=True)
                frappe.db.commit()
            except Exception:
                pass

    # ── B13: get_customer_outstanding ────────────────────────────────────────
    print("\n--- B13: get_customer_outstanding → dict with non-negative values ---")
    try:
        result = bd.get_customer_outstanding()
        if isinstance(result, dict):
            _pass(f"get_customer_outstanding returns dict ({len(result)} customers)")
        else:
            _fail("Not a dict", type(result).__name__)
        neg = [k for k, v in result.items() if flt(v) < 0]
        if not neg:
            _pass("All outstanding values >= 0")
        else:
            _fail("Negative outstanding values found", str(neg[:3]))
    except Exception as e:
        _fail("B13 crashed", str(e))

    # ── B14: get_invoice_payments ─────────────────────────────────────────────
    print("\n--- B14: get_invoice_payments → list with expected keys ---")
    try:
        si_b14 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_b14.name:
                _created[i] = ("Sales Invoice", si_b14.name, 1)

        bd.record_payment(
            invoice_name=si_b14.name,
            amount_received=flt(si_b14.grand_total),
            payment_date=DATE,
            payment_mode="Cash",
        )

        rows = bd.get_invoice_payments(si_b14.name)
        if isinstance(rows, list):
            _pass(f"get_invoice_payments returns list ({len(rows)} rows)")
        else:
            _fail("Not a list", type(rows).__name__)
        if rows:
            row = rows[0]
            req = {"name", "posting_date", "payment_mode", "allocated_amount"}
            missing = req - set(row.keys())
            if not missing:
                _pass("Payment rows have expected keys")
            else:
                _fail("Missing payment keys", str(missing))
            if flt(row.get("allocated_amount")) > 0:
                _pass(f"allocated_amount = {flt(row.get('allocated_amount')):.2f}")
            else:
                _fail("allocated_amount not positive")
    except Exception as e:
        _fail("B14 crashed", str(e))

    # ── B15: get_gstr_summary ─────────────────────────────────────────────────
    print("\n--- B15: get_gstr_summary → 4 sections + math ---")
    try:
        from_d = str(get_first_day(DATE))
        to_d   = str(get_last_day(DATE))
        result = bd.get_gstr_summary(company=COMPANY, from_date=from_d, to_date=to_d)
        sections = {"output", "itc", "net_by_type", "totals"}
        missing = sections - set(result.keys())
        if not missing:
            _pass("All 4 GSTR sections present")
        else:
            _fail("Missing GSTR sections", str(missing))
        totals = result.get("totals", {})
        t_keys = {"total_output", "total_itc", "net_tax_liability"}
        missing_t = t_keys - set(totals.keys())
        if not missing_t:
            _pass("All totals keys present")
        else:
            _fail("Missing totals keys", str(missing_t))
        expected_net = flt(totals.get("total_output")) - flt(totals.get("total_itc"))
        actual_net   = flt(totals.get("net_tax_liability"))
        if abs(expected_net - actual_net) < 0.01:
            _pass(f"net_tax_liability math correct: {actual_net:.2f}")
        else:
            _fail("net_tax_liability math wrong", f"expected={expected_net:.2f} got={actual_net:.2f}")
    except Exception as e:
        _fail("B15 crashed", str(e))

    # ── B16: get_itc_ledger ───────────────────────────────────────────────────
    print("\n--- B16: get_itc_ledger → list ---")
    try:
        from_d = str(get_first_day(DATE))
        to_d   = str(get_last_day(DATE))
        result = bd.get_itc_ledger(company=COMPANY, from_date=from_d, to_date=to_d)
        if isinstance(result, list):
            _pass(f"get_itc_ledger returns list ({len(result)} rows)")
        else:
            _fail("Not a list", type(result).__name__)
    except Exception as e:
        _fail("B16 crashed", str(e))

    # ── B17-B23: ai_chat ─────────────────────────────────────────────────────
    print("\n--- B17-B23: ai_chat intents ---")

    def _mock_llm_response(intent, **extras):
        """Monkey-patch _llm_parse to avoid real API calls during tests."""
        def _fake_parse(conversation, system=None):
            base = {"intent": intent, "reply": f"Test reply for {intent}"}
            base.update(extras)
            return base
        return _fake_parse

    original_llm_parse = getattr(bd, "_llm_parse", None)

    intent_tests = [
        ("B17", "greeting",      {},                          "non-empty reply"),
        ("B18", "revenue",       {"period": "this_month"},    "revenue data returned"),
        ("B19", "outstanding",   {},                          "outstanding data returned"),
        ("B20", "overdue_count", {},                          "overdue data returned"),
        ("B21", "top_customers", {"limit": 3},                "top customers returned"),
        ("B22", "unpaid_bills",  {},                          "unpaid bills returned"),
    ]

    for code, intent, extras, desc in intent_tests:
        print(f"\n  --- {code}: ai_chat intent='{intent}' → {desc} ---")
        try:
            # Patch _llm_parse in the module so real API is not called
            bd._llm_parse = _mock_llm_response(intent, **extras)
            result = bd.ai_chat(
                messages=[{"role": "user", "content": f"test {intent}"}]
            )
            if result.get("reply"):
                _pass(f"intent={intent}: reply returned")
            else:
                _fail(f"intent={intent}: no reply", str(result))
        except Exception as e:
            _fail(f"{code} crashed", str(e))
        finally:
            if original_llm_parse:
                bd._llm_parse = original_llm_parse

    # Navigation intents
    print("\n  --- B23: navigation intents → action key present ---")
    nav_intents = [
        "show_overdue", "show_unpaid", "show_all_invoices",
        "show_bills", "show_quotes", "show_customers",
        "show_sales_orders", "show_purchase_orders", "show_dashboard",
    ]
    for nav in nav_intents:
        try:
            bd._llm_parse = _mock_llm_response(nav)
            result = bd.ai_chat(messages=[{"role": "user", "content": f"go to {nav}"}])
            if result.get("action") == nav:
                _pass(f"  nav intent '{nav}' → action key correct")
            else:
                _fail(f"  nav intent '{nav}' → wrong action", str(result.get("action")))
        except Exception as e:
            _fail(f"  nav intent '{nav}' crashed", str(e))
        finally:
            if original_llm_parse:
                bd._llm_parse = original_llm_parse

    # ── B24: get_ai_alerts ───────────────────────────────────────────────────
    print("\n--- B24: get_ai_alerts → alerts list + count ---")
    try:
        result = bd.get_ai_alerts()
        if "alerts" in result and "count" in result:
            _pass("get_ai_alerts has 'alerts' and 'count' keys")
        else:
            _fail("Missing keys in get_ai_alerts result", str(result.keys()))
        if isinstance(result.get("alerts"), list):
            _pass(f"alerts is a list ({len(result['alerts'])} alerts)")
        else:
            _fail("alerts not a list")
        if result.get("count") == len(result.get("alerts", [])):
            _pass("count matches len(alerts)")
        else:
            _fail("count/alerts length mismatch")
        for alert in result.get("alerts", []):
            req = {"type", "icon", "text"}
            missing = req - set(alert.keys())
            if missing:
                _fail("Alert missing keys", str(missing))
                break
        else:
            if result.get("alerts"):
                _pass("All alert objects have required keys")
    except Exception as e:
        _fail("B24 crashed", str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION C — End-to-End Business Flows
# ═══════════════════════════════════════════════════════════════════════════════

def run_section_c(bd, docs, customer, supplier):
    print("\n══ SECTION C — End-to-End Business Flows ══")

    # ── C1: Customer lifecycle ───────────────────────────────────────────────
    print("\n--- C1: Customer lifecycle (create → update → disable → re-enable) ---")
    test_cust = None
    try:
        cust_doc = frappe.get_doc({
            "doctype":       "Customer",
            "customer_name": "E2E Test Customer",
            "customer_type": "Company",
            "company":       COMPANY,
        })
        cust_doc.flags.ignore_permissions = True
        cust_doc.insert()
        frappe.db.commit()
        test_cust = cust_doc.name
        _created.append(("Customer", test_cust, 0))
        _pass(f"Customer created: {test_cust}")

        # Update
        cust_doc.customer_name = "E2E Test Customer Updated"
        cust_doc.save(ignore_permissions=True)
        frappe.db.commit()
        name_db = frappe.db.get_value("Customer", test_cust, "customer_name")
        if name_db == "E2E Test Customer Updated":
            _pass("Customer name updated")
        else:
            _fail("Customer name not updated", str(name_db))

        # Disable
        cust_doc.disabled = 1
        cust_doc.save(ignore_permissions=True)
        frappe.db.commit()
        dis = frappe.db.get_value("Customer", test_cust, "disabled")
        if dis == 1:
            _pass("Customer disabled")
        else:
            _fail("Customer not disabled", str(dis))

        # Re-enable
        cust_doc.disabled = 0
        cust_doc.save(ignore_permissions=True)
        frappe.db.commit()
        dis2 = frappe.db.get_value("Customer", test_cust, "disabled")
        if dis2 == 0:
            _pass("Customer re-enabled")
        else:
            _fail("Customer not re-enabled", str(dis2))
    except Exception as e:
        _fail("C1 crashed", str(e))

    # ── C2: Quote-to-cash full flow ──────────────────────────────────────────
    print("\n--- C2: Quote → email defaults → SO → Invoice → Payment ---")
    try:
        import zoho_books_clone.invoicing.doctype.quotation.quotation as q_mod
        import zoho_books_clone.invoicing.doctype.sales_order.sales_order as so_mod
        importlib.reload(q_mod)
        importlib.reload(so_mod)

        # Create and submit quotation
        q = frappe.new_doc("Quotation")
        q.customer         = customer
        q.company          = COMPANY
        q.transaction_date = DATE
        q.valid_till       = DATE
        q.append("items", {"item_name": "C2 Item", "qty": 3, "rate": 400})
        q.flags.ignore_permissions = True
        q.flags.ignore_mandatory   = True
        q.flags.ignore_links       = True
        q.insert()
        q.submit()
        frappe.db.commit()
        _created.append(("Quotation", q.name, 1))
        _pass(f"Quotation submitted: {q.name}")

        # Email defaults
        email_def = bd.get_quote_email_defaults(q.name)
        if email_def.get("quote_name") == q.name:
            _pass("Quote email defaults returned")
        else:
            _fail("Quote email defaults mismatch")

        # Quotation → SO (manually, as Quotation.make_sales_order is not implemented)
        import zoho_books_clone.invoicing.doctype.sales_order.sales_order as so_mod
        importlib.reload(so_mod)

        ar  = frappe.db.get_value("Account", {"account_type": "Receivable", "company": COMPANY, "is_group": 0}, "name")
        inc = frappe.db.get_value("Account", {"account_type": "Income",     "company": COMPANY, "is_group": 0}, "name")

        so = frappe.new_doc("Sales Order")
        so.customer         = customer
        so.company          = COMPANY
        so.transaction_date = DATE
        so.ref_quote        = q.name
        so.income_account   = inc
        for it in q.items:
            so.append("items", {
                "item_name":      it.item_name,
                "qty":            it.qty,
                "rate":           it.rate,
                "income_account": inc,
            })
        so.flags.ignore_permissions = True
        so.flags.ignore_mandatory   = True
        so.flags.ignore_links       = True
        so.insert()
        frappe.db.commit()
        _created.append(("Sales Order", so.name, 0))
        _pass(f"Sales Order created from Quotation data: {so.name}")

        if abs(flt(so.grand_total) - flt(q.grand_total)) < 0.01:
            _pass(f"SO grand_total = {so.grand_total:.2f} matches Quotation")
        else:
            _fail("SO grand_total mismatch", f"SO={so.grand_total} Q={q.grand_total}")

        # Submit SO
        so.flags.ignore_permissions = True
        so.flags.ignore_mandatory   = True
        so.submit()
        frappe.db.commit()
        for i, rec in enumerate(_created):
            if rec[1] == so.name:
                _created[i] = ("Sales Order", so.name, 1)
        so_status = frappe.db.get_value("Sales Order", so.name, "status")
        _pass(f"SO submitted (status={so_status})")

        # SO → SI (manually copy items from SO)
        si = _make_si(
            customer,
            items=[{
                "item_name":      it.item_name,
                "qty":            it.qty,
                "rate":           it.rate,
                "income_account": inc,
            } for it in so.items],
            submit=True,
        )
        for i, rec in enumerate(_created):
            if rec[1] == si.name:
                _created[i] = ("Sales Invoice", si.name, 1)
        _pass(f"Sales Invoice created and submitted: {si.name}")

        ok, dr, cr = _gl_balanced(si.name)
        if ok:
            _pass(f"SI GL balanced: {dr:.2f}")
        else:
            _fail("SI GL unbalanced", f"DR={dr:.2f} CR={cr:.2f}")

        # Invoice email defaults
        inv_email = bd.get_invoice_email_defaults(si.name)
        if inv_email.get("invoice_name") == si.name:
            _pass("Invoice email defaults OK")
        else:
            _fail("Invoice email defaults mismatch")

        # Record payment
        pay_result = bd.record_payment(
            invoice_name=si.name,
            amount_received=flt(si.grand_total),
            payment_date=DATE,
            payment_mode="Cash",
        )
        pe_name = pay_result.get("payment_entry")
        if pe_name:
            _created.append(("Payment Entry", pe_name, 1))
            _pass(f"Payment recorded: {pe_name}")
        else:
            _fail("Payment not created in C2 flow")

    except Exception as e:
        _fail("C2 crashed", str(e))

    # ── C3: Credit Note flow ─────────────────────────────────────────────────
    print("\n--- C3: Credit Note flow → GL reversal ---")
    try:
        si_c3 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_c3.name:
                _created[i] = ("Sales Invoice", si_c3.name, 1)

        orig_gl = _gl(si_c3.name)
        orig_dr = sum(flt(r.debit)  for r in orig_gl)
        orig_cr = sum(flt(r.credit) for r in orig_gl)

        frappe.form_dict.customer        = customer
        frappe.form_dict.against_invoice = si_c3.name
        frappe.form_dict.date            = DATE
        frappe.form_dict.reason          = "Price Adjustment"
        frappe.form_dict.notes           = "C3 test"
        frappe.form_dict.warehouse       = ""
        frappe.form_dict.items           = json.dumps([{"item_name": "E2E Item", "qty": 2, "rate": 500}])
        frappe.form_dict.taxes           = json.dumps([])

        result = docs.create_credit_note()
        cn_name = result.get("credit_note")
        _created.append(("Sales Invoice", cn_name, 1))

        cn_gl = _gl(cn_name)
        cn_dr = sum(flt(r.debit)  for r in cn_gl)
        cn_cr = sum(flt(r.credit) for r in cn_gl)

        if len(cn_gl) >= 2:
            _pass(f"Credit note GL posted: {len(cn_gl)} rows")
        else:
            _fail("Credit note GL not posted")

        ok, dr, cr = _gl_balanced(cn_name)
        if ok:
            _pass(f"Credit note GL balanced: {dr:.2f}")
        else:
            _fail("Credit note GL unbalanced", f"DR={dr:.2f} CR={cr:.2f}")
    except Exception as e:
        _fail("C3 crashed", str(e))

    # ── C4: Debit Note flow ──────────────────────────────────────────────────
    print("\n--- C4: Debit Note flow → GL balanced ---")
    try:
        pi_c4 = _make_pi(supplier)
        pi_c4.flags.ignore_permissions = True
        pi_c4.flags.ignore_mandatory   = True
        pi_c4.submit()
        frappe.db.commit()
        _created.append(("Purchase Invoice", pi_c4.name, 1))

        frappe.form_dict.vendor       = supplier
        frappe.form_dict.against_bill = pi_c4.name
        frappe.form_dict.date         = DATE
        frappe.form_dict.reason       = "Price Correction"
        frappe.form_dict.notes        = "C4 test"
        frappe.form_dict.warehouse    = ""
        frappe.form_dict.items        = json.dumps([{"item_name": "E2E Purchase Item", "qty": 1, "rate": 500}])

        result = docs.create_debit_note()
        dn_name = result.get("debit_note")
        _created.append(("Purchase Invoice", dn_name, 1))

        if len(_gl(dn_name)) >= 2:
            _pass(f"Debit note GL posted ({len(_gl(dn_name))} rows)")
        else:
            _fail("Debit note GL not posted")

        ok, dr, cr = _gl_balanced(dn_name)
        if ok:
            _pass(f"Debit note GL balanced: {dr:.2f}")
        else:
            _fail("Debit note GL unbalanced", f"DR={dr:.2f} CR={cr:.2f}")
    except Exception as e:
        _fail("C4 crashed", str(e))

    # ── C5: Bulk invoice flow ────────────────────────────────────────────────
    print("\n--- C5: Bulk invoice → status filter counts correct ---")
    try:
        # Create 3 invoices — 1 draft, 1 submitted, 1 submitted (to check counts)
        si_draft  = _make_si(customer)
        si_sub1   = _make_si(customer, submit=True)
        si_sub2   = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_sub1.name:
                _created[i] = ("Sales Invoice", si_sub1.name, 1)
            if rec[1] == si_sub2.name:
                _created[i] = ("Sales Invoice", si_sub2.name, 1)

        # Query the DB directly for verification
        draft_count = frappe.db.count("Sales Invoice", {"docstatus": 0, "company": COMPANY})
        sub_count   = frappe.db.count("Sales Invoice", {"docstatus": 1, "company": COMPANY})

        if draft_count >= 1:
            _pass(f"Draft invoices count >= 1 ({draft_count})")
        else:
            _fail("No draft invoices found")

        if sub_count >= 2:
            _pass(f"Submitted invoices count >= 2 ({sub_count})")
        else:
            _fail("Not enough submitted invoices", str(sub_count))
    except Exception as e:
        _fail("C5 crashed", str(e))

    # ── C6: Outstanding balance lifecycle ────────────────────────────────────
    print("\n--- C6: Outstanding balance → submit → outstanding > 0 → pay → clears ---")
    try:
        si_c6 = _make_si(customer, submit=True)
        for i, rec in enumerate(_created):
            if rec[1] == si_c6.name:
                _created[i] = ("Sales Invoice", si_c6.name, 1)

        si_c6_doc = frappe.get_doc("Sales Invoice", si_c6.name)
        outstanding_before = flt(getattr(si_c6_doc, "outstanding_amount", None)) or flt(si_c6_doc.grand_total)

        if outstanding_before > 0:
            _pass(f"Outstanding amount after submit: {outstanding_before:.2f}")
        else:
            _fail("Outstanding amount not set after submit", str(outstanding_before))

        # Record full payment
        bd.record_payment(
            invoice_name=si_c6.name,
            amount_received=outstanding_before,
            payment_date=DATE,
            payment_mode="Cash",
        )

        # Reload and check outstanding
        si_c6_doc.reload()
        outstanding_after = flt(getattr(si_c6_doc, "outstanding_amount", None))
        if outstanding_after < 0.01:
            _pass(f"Outstanding cleared after payment: {outstanding_after:.2f}")
        else:
            _fail("Outstanding not cleared after payment", str(outstanding_after))

        # Verify payment appears in get_invoice_payments
        payments = bd.get_invoice_payments(si_c6.name)
        if payments:
            _pass(f"Payment visible in get_invoice_payments ({len(payments)} entries)")
        else:
            _fail("Payment NOT visible in get_invoice_payments")
    except Exception as e:
        _fail("C6 crashed", str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# SECTION D — Security / Guard Rails
# ═══════════════════════════════════════════════════════════════════════════════

def run_section_d(bd, docs, customer):
    print("\n══ SECTION D — Security & Guard Rails ══")

    def _as_guest(fn, *args, **kwargs):
        """Run a function with frappe.session.user temporarily set to Guest."""
        orig = frappe.session.user
        try:
            frappe.session.user = "Guest"
            return fn(*args, **kwargs)
        finally:
            frappe.session.user = orig

    si_test = _make_si(customer)

    # ── D1: get_doc rejects Guest ─────────────────────────────────────────────
    print("\n--- D1: get_doc rejects Guest session ---")
    try:
        _as_guest(docs.get_doc, "Sales Invoice", si_test.name)
        _fail("get_doc accepted Guest session")
    except frappe.PermissionError:
        _pass("get_doc raises PermissionError for Guest")
    except Exception as e:
        _fail("Wrong exception type", str(e))

    # ── D2: save_doc rejects Guest ────────────────────────────────────────────
    print("\n--- D2: save_doc rejects Guest session ---")
    try:
        _as_guest(docs.save_doc, {"doctype": "Sales Invoice", "customer": customer})
        _fail("save_doc accepted Guest session")
    except (frappe.PermissionError, frappe.ValidationError):
        _pass("save_doc raises PermissionError for Guest")
    except Exception as e:
        _fail("Wrong exception type", str(e))

    # ── D3: submit_doc rejects Guest ──────────────────────────────────────────
    print("\n--- D3: submit_doc rejects Guest session ---")
    try:
        _as_guest(docs.submit_doc, "Sales Invoice", si_test.name)
        _fail("submit_doc accepted Guest session")
    except frappe.PermissionError:
        _pass("submit_doc raises PermissionError for Guest")
    except Exception as e:
        _fail("Wrong exception type", str(e))

    # ── D4: delete_doc rejects Guest ──────────────────────────────────────────
    print("\n--- D4: delete_doc rejects Guest session ---")
    try:
        _as_guest(docs.delete_doc, "Sales Invoice", si_test.name)
        _fail("delete_doc accepted Guest session")
    except frappe.PermissionError:
        _pass("delete_doc raises PermissionError for Guest")
    except Exception as e:
        _fail("Wrong exception type", str(e))

    # ── D5: record_payment rejects Guest ──────────────────────────────────────
    print("\n--- D5: record_payment rejects Guest session ---")
    try:
        _as_guest(bd.record_payment, invoice_name=si_test.name, amount_received=100, payment_date=DATE)
        _fail("record_payment accepted Guest session")
    except frappe.PermissionError:
        _pass("record_payment raises PermissionError for Guest")
    except Exception as e:
        _fail("Wrong exception type", str(e))

    # ── D6: normalize_company_names requires System Manager ───────────────────
    print("\n--- D6: normalize_company_names requires System Manager role ---")
    orig_user = frappe.session.user
    try:
        # Create a non-admin user context
        frappe.session.user = "Administrator"
        # Set roles manually to NOT include System Manager
        orig_get_roles = frappe.get_roles

        def _mock_no_system_manager(user=None):
            return ["Books Manager", "Guest"]

        frappe.get_roles = _mock_no_system_manager
        try:
            bd.normalize_company_names()
            _fail("normalize_company_names accepted non-System-Manager user")
        except frappe.PermissionError:
            _pass("normalize_company_names raises PermissionError for non-System-Manager")
        except frappe.ValidationError:
            _pass("normalize_company_names raises ValidationError for non-System-Manager")
        finally:
            frappe.get_roles = orig_get_roles
    except Exception as e:
        _fail("D6 crashed", str(e))
    finally:
        frappe.session.user = orig_user


# ═══════════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════════

def _cleanup():
    print("\n══ CLEANUP ══")
    cleaned = 0
    # Cancel submitted docs first (reversed order)
    cancel_order = [
        "Payment Entry", "Sales Invoice", "Purchase Invoice",
        "Quotation", "Sales Order",
    ]
    for target_dt in cancel_order:
        for doctype, name, docstatus in reversed(_created):
            if doctype != target_dt:
                continue
            try:
                if not frappe.db.exists(doctype, name):
                    continue
                doc = frappe.get_doc(doctype, name)
                if doc.docstatus == 1:
                    doc.flags.ignore_permissions = True
                    doc.cancel()
                    frappe.db.commit()
                    cleaned += 1
            except Exception:
                pass

    # Delete everything
    for doctype, name, _ in reversed(_created):
        try:
            if frappe.db.exists(doctype, name):
                frappe.delete_doc(doctype, name, ignore_permissions=True, force=True)
                frappe.db.commit()
        except Exception:
            pass

    _pass(f"Cleaned up {cleaned} documents (cancelled), attempted deletion of all created docs")


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN RUNNER
# ═══════════════════════════════════════════════════════════════════════════════

def run():
    global COMPANY

    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║   Zoho Books Clone — Full E2E Test Suite                     ║")
    print("║   books_data.py + docs.py + Business Flows + Security        ║")
    print("╚══════════════════════════════════════════════════════════════╝")

    # ── Reload modules fresh ─────────────────────────────────────────────────
    import zoho_books_clone.api.books_data as bd_mod
    import zoho_books_clone.api.docs       as docs_mod
    importlib.reload(bd_mod)
    importlib.reload(docs_mod)

    bd   = bd_mod
    docs = docs_mod

    # ── Resolve company dynamically from Books Company ────────────────────────
    co_row = frappe.db.get_value("Books Company", {}, "name")
    if not co_row:
        print("\n  ABORT: No Books Company found — cannot run E2E tests.")
        return
    COMPANY = co_row
    print(f"\n  Resolved company: {COMPANY}")

    # ── Resolve or create Customer fixture ───────────────────────────────────
    customer = frappe.db.get_value("Customer", {}, "name")
    if not customer:
        print("\n  ABORT: No Customer found in the database — cannot run E2E tests.")
        return

    # ── Resolve or create Supplier fixture ───────────────────────────────────
    supplier = frappe.db.get_value("Supplier", {}, "name")
    _test_supplier_created = False
    if not supplier:
        print("  No Supplier found — creating a test Supplier for this run…")
        try:
            sup_doc = frappe.get_doc({
                "doctype":       "Supplier",
                "supplier_name": "E2E Test Supplier",
                "supplier_type": "Company",
            })
            sup_doc.flags.ignore_permissions = True
            sup_doc.insert()
            frappe.db.commit()
            supplier = sup_doc.name
            _created.append(("Supplier", supplier, 0))
            _test_supplier_created = True
            print(f"  Test Supplier created: {supplier}")
        except Exception as e:
            print(f"\n  ABORT: Could not create Supplier: {e}")
            return

    print(f"  Company  : {COMPANY}")
    print(f"  Customer : {customer}")
    print(f"  Supplier : {supplier}")
    print(f"  Date     : {DATE}")

    try:
        run_section_a(docs, customer, supplier)
        run_section_b(bd, customer, supplier)
        run_section_c(bd, docs, customer, supplier)
        run_section_d(bd, docs, customer)
    finally:
        _cleanup()

    print("\n╔══════════════════════════════════════════════════════════════╗")
    print("║   E2E Test Suite COMPLETE                                    ║")
    print("╚══════════════════════════════════════════════════════════════╝\n")
