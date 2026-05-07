"""
L1 — Currency Exchange / Multi-currency GL posting.

Tests that exchange_rate is applied correctly when invoices are posted in a
foreign currency, and that exchange gain/loss entries are created when a
payment settles at a different rate.

  T1  SI in INR (base) — GL amounts unchanged (rate=1)
  T2  SI in USD at rate=83.5 — GL DR Receivable = grand_total * 83.5
  T3  SI in USD — GL currency field stores "USD"
  T4  SI in USD — GL entries balance (DR == CR in base currency)
  T5  PINV in USD at rate=83.5 — GL CR Payable = grand_total * 83.5
  T6  Cancel USD SI — reversal GL amounts match original base amounts
  T7  Payment at same rate — no exchange gain/loss entry
  T8  Payment at higher rate — exchange gain entry posted (CR gain account)
  T9  Payment at lower rate — exchange loss entry posted (DR gain account)
  T10 Cleanup
"""
import frappe
from frappe.utils import flt, today

COMPANY  = "Eiffele gaming"
CUSTOMER = "CUST-2026-00010"

AR_ACCOUNT      = "Accounts Receivable-Eiffele gaming"
AP_ACCOUNT      = "Accounts Payable-Eiffele gaming"
INCOME_ACCOUNT  = "Other Income-Eiffele gaming"
EXPENSE_ACCOUNT = "Office Supplies-Eiffele gaming"
BANK_ACCOUNT    = "HDFC Current-Eiffele gaming"

GAIN_LOSS_ACCOUNT = "Exchange Gain/Loss"

_docs_to_cancel = []  # (doctype, name)


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _get_or_create_gain_loss_account() -> str:
    """Ensure an Exchange Gain/Loss account exists; return its name."""
    name = f"{GAIN_LOSS_ACCOUNT}-{COMPANY}"
    if not frappe.db.exists("Account", name):
        parent = frappe.db.get_value(
            "Account",
            {"account_type": "Income", "company": COMPANY, "is_group": 1},
            "name",
        ) or frappe.db.get_value(
            "Account",
            {"company": COMPANY, "is_group": 1, "parent_account": ("is", "not set")},
            "name",
        )
        doc = frappe.new_doc("Account")
        doc.account_name   = GAIN_LOSS_ACCOUNT
        doc.account_type   = "Income"
        doc.company        = COMPANY
        doc.is_group       = 0
        doc.parent_account = parent
        doc.flags.ignore_permissions = True
        doc.flags.ignore_mandatory   = True
        doc.insert(ignore_links=True)
        frappe.db.commit()
        return doc.name
    return name


def _make_si(currency="INR", exchange_rate=1.0, amount=10000.0) -> object:
    si = frappe.new_doc("Sales Invoice")
    si.customer       = CUSTOMER
    si.debit_to       = AR_ACCOUNT
    si.income_account = INCOME_ACCOUNT
    si.posting_date   = today()
    si.company        = COMPANY
    si.currency       = currency
    si.exchange_rate  = exchange_rate
    si.append("items", {
        "item_name":      "Test Service",
        "qty":            1,
        "rate":           amount,
        "income_account": INCOME_ACCOUNT,
    })
    si.net_total   = amount
    si.grand_total = amount
    si.flags.ignore_permissions = True
    si.flags.ignore_mandatory   = True
    si.flags.ignore_links       = True
    si.insert(ignore_links=True)
    si.submit()
    _docs_to_cancel.append(("Sales Invoice", si.name))
    frappe.db.commit()
    return si


def _make_pinv(currency="INR", exchange_rate=1.0, amount=5000.0) -> object:
    sup = frappe.db.get_value("Supplier", {}, "name") or "SUP-2026-00001"
    pinv = frappe.new_doc("Purchase Invoice")
    pinv.supplier        = sup
    pinv.credit_to       = AP_ACCOUNT
    pinv.expense_account = EXPENSE_ACCOUNT
    pinv.bill_date       = today()
    pinv.posting_date    = today()
    pinv.company         = COMPANY
    pinv.currency        = currency
    pinv.exchange_rate   = exchange_rate
    pinv.append("items", {
        "item_name":       "Test Material",
        "qty":             1,
        "rate":            amount,
        "expense_account": EXPENSE_ACCOUNT,
    })
    pinv.net_total   = amount
    pinv.grand_total = amount
    pinv.flags.ignore_permissions = True
    pinv.flags.ignore_mandatory   = True
    pinv.flags.ignore_links       = True
    pinv.insert(ignore_links=True)
    pinv.submit()
    _docs_to_cancel.append(("Purchase Invoice", pinv.name))
    frappe.db.commit()
    return pinv


def _gl(voucher_no) -> list:
    return frappe.db.sql("""
        SELECT account, debit, credit, currency, is_cancelled, is_reversal
        FROM `tabGeneral Ledger Entry`
        WHERE voucher_no = %s AND is_cancelled = 0 AND is_reversal = 0
    """, voucher_no, as_dict=True)


def run():
    print("\n=== Currency Exchange L1 Test ===")

    gain_loss_acct = _get_or_create_gain_loss_account()

    # ── T1: SI in INR — GL amounts unchanged ─────────────────────────────────
    print("\n--- T1: SI in INR (base currency) — GL amounts = grand_total (rate=1) ---")
    try:
        si = _make_si(currency="INR", exchange_rate=1.0, amount=10000.0)
        rows = _gl(si.name)
        ar_row = next((r for r in rows if r.account == AR_ACCOUNT), None)
        if not ar_row:
            _fail("No AR GL row found")
        elif abs(flt(ar_row.debit) - 10000.0) < 0.01:
            _pass(f"INR SI: AR debit = {flt(ar_row.debit):.2f} (no exchange applied)")
        else:
            _fail("INR SI AR debit wrong", f"expected=10000, got={flt(ar_row.debit)}")
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    # ── T2: SI in USD — GL amounts = grand_total * exchange_rate ─────────────
    print("\n--- T2: SI in USD at rate=83.5 — GL DR Receivable = 1000 * 83.5 = 83,500 ---")
    try:
        si_usd = _make_si(currency="USD", exchange_rate=83.5, amount=1000.0)
        rows = _gl(si_usd.name)
        ar_row = next((r for r in rows if r.account == AR_ACCOUNT), None)
        expected = 1000.0 * 83.5
        if not ar_row:
            _fail("No AR GL row for USD SI")
        elif abs(flt(ar_row.debit) - expected) < 1.0:
            _pass(f"USD SI: AR debit = {flt(ar_row.debit):.2f} = 1000 * 83.5")
        else:
            _fail("USD SI AR debit wrong", f"expected={expected}, got={flt(ar_row.debit)}")
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: SI in USD — GL currency field stores "USD" ────────────────────────
    print("\n--- T3: SI in USD — GL currency field stores 'USD' ---")
    try:
        rows = _gl(si_usd.name)
        currencies = {r.currency for r in rows}
        if "USD" in currencies:
            _pass(f"GL currency field contains 'USD': {currencies}")
        else:
            _fail("GL currency field not 'USD'", f"found: {currencies}")
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: SI in USD — GL entries balance (total DR == total CR) ────────────
    print("\n--- T4: SI in USD — GL entries balance in base currency ---")
    try:
        rows = _gl(si_usd.name)
        total_dr = sum(flt(r.debit) for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)
        if abs(total_dr - total_cr) < 0.01:
            _pass(f"GL balanced: DR={total_dr:.2f} CR={total_cr:.2f}")
        else:
            _fail("GL unbalanced", f"DR={total_dr:.2f} CR={total_cr:.2f}")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: PINV in USD — GL CR Payable = grand_total * exchange_rate ────────
    print("\n--- T5: PINV in USD at rate=83.5 — GL CR Payable = 500 * 83.5 = 41,750 ---")
    try:
        pinv_usd = _make_pinv(currency="USD", exchange_rate=83.5, amount=500.0)
        rows = _gl(pinv_usd.name)
        ap_row = next((r for r in rows if r.account == AP_ACCOUNT), None)
        expected = 500.0 * 83.5
        if not ap_row:
            _fail("No AP GL row for USD PINV")
        elif abs(flt(ap_row.credit) - expected) < 1.0:
            _pass(f"USD PINV: AP credit = {flt(ap_row.credit):.2f} = 500 * 83.5")
        else:
            _fail("USD PINV AP credit wrong", f"expected={expected}, got={flt(ap_row.credit)}")
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: Cancel USD SI — reversal GL amounts match original ───────────────
    print("\n--- T6: Cancel USD SI — reversal entries carry same base amounts ---")
    try:
        si_cancel = _make_si(currency="USD", exchange_rate=83.5, amount=2000.0)
        _docs_to_cancel.remove(("Sales Invoice", si_cancel.name))
        si_cancel.cancel()
        frappe.db.commit()

        all_gl = frappe.db.sql("""
            SELECT account, debit, credit, is_reversal
            FROM `tabGeneral Ledger Entry`
            WHERE voucher_no = %s
        """, si_cancel.name, as_dict=True)

        reversal = [r for r in all_gl if r.is_reversal]

        if not reversal:
            _fail("No reversal entries found after cancel")
        else:
            rev_ar = next((r for r in reversal if r.account == AR_ACCOUNT), None)
            expected_base = 2000.0 * 83.5
            if rev_ar and abs(flt(rev_ar.credit) - expected_base) < 1.0:
                _pass(f"Reversal AR credit = {flt(rev_ar.credit):.2f} matches original base amount")
            else:
                got = flt(rev_ar.credit) if rev_ar else "no row"
                _fail("Reversal AR amount wrong", f"expected={expected_base}, got={got}")
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: Payment at same rate — no exchange gain/loss ─────────────────────
    print("\n--- T7: Payment at same rate as SI — no exchange gain/loss GL entry ---")
    try:
        si7 = _make_si(currency="USD", exchange_rate=83.5, amount=1000.0)
        pe = frappe.new_doc("Payment Entry")
        pe.payment_type  = "Receive"
        pe.payment_date  = today()
        pe.company       = COMPANY
        pe.currency      = "USD"
        pe.exchange_rate = 83.5          # same as SI
        pe.paid_from     = AR_ACCOUNT
        pe.paid_to       = BANK_ACCOUNT
        pe.paid_amount   = 1000.0
        pe.party_type    = "Customer"
        pe.party         = CUSTOMER
        pe.exchange_gain_loss_account = gain_loss_acct
        pe.reference_name = si7.name
        pe.reference_type = "Sales Invoice"
        pe.flags.ignore_permissions = True
        pe.flags.ignore_mandatory   = True
        pe.flags.ignore_links       = True
        pe.insert(ignore_links=True)
        pe.submit()
        _docs_to_cancel.append(("Payment Entry", pe.name))
        frappe.db.commit()

        rows = _gl(pe.name)
        gain_rows = [r for r in rows if r.account == gain_loss_acct]
        if not gain_rows:
            _pass("No exchange gain/loss entry when rate matches invoice rate")
        else:
            _fail("Unexpected gain/loss entry at same rate", f"{gain_rows}")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: Payment at higher rate — exchange gain (CR) ───────────────────────
    print("\n--- T8: Payment at rate=84.0 > SI rate=83.5 — exchange gain CR entry ---")
    try:
        si8 = _make_si(currency="USD", exchange_rate=83.5, amount=1000.0)
        pe8 = frappe.new_doc("Payment Entry")
        pe8.payment_type  = "Receive"
        pe8.payment_date  = today()
        pe8.company       = COMPANY
        pe8.currency      = "USD"
        pe8.exchange_rate = 84.0         # higher than SI rate=83.5 → gain
        pe8.paid_from     = AR_ACCOUNT
        pe8.paid_to       = BANK_ACCOUNT
        pe8.paid_amount   = 1000.0
        pe8.party_type    = "Customer"
        pe8.party         = CUSTOMER
        pe8.exchange_gain_loss_account = gain_loss_acct
        pe8.reference_name = si8.name
        pe8.reference_type = "Sales Invoice"
        pe8.flags.ignore_permissions = True
        pe8.flags.ignore_mandatory   = True
        pe8.flags.ignore_links       = True
        pe8.insert(ignore_links=True)
        pe8.submit()
        _docs_to_cancel.append(("Payment Entry", pe8.name))
        frappe.db.commit()

        rows = _gl(pe8.name)
        gain_rows = [r for r in rows if r.account == gain_loss_acct]
        if gain_rows:
            gain_cr = sum(flt(r.credit) for r in gain_rows)
            expected_gain = (84.0 - 83.5) * 1000.0  # = 500
            if abs(gain_cr - expected_gain) < 1.0:
                _pass(f"Exchange gain CR = {gain_cr:.2f} (rate diff {84.0-83.5} * 1000)")
            else:
                _fail("Exchange gain amount wrong", f"expected={expected_gain}, got={gain_cr}")
        else:
            _fail("No exchange gain entry found at higher rate")
    except Exception as e:
        _fail("T8 crashed", str(e)[:120])

    # ── T9: Payment at lower rate — exchange loss (DR) ────────────────────────
    print("\n--- T9: Payment at rate=83.0 < SI rate=83.5 — exchange loss DR entry ---")
    try:
        si9 = _make_si(currency="USD", exchange_rate=83.5, amount=1000.0)
        pe9 = frappe.new_doc("Payment Entry")
        pe9.payment_type  = "Receive"
        pe9.payment_date  = today()
        pe9.company       = COMPANY
        pe9.currency      = "USD"
        pe9.exchange_rate = 83.0         # lower than SI rate=83.5 → loss
        pe9.paid_from     = AR_ACCOUNT
        pe9.paid_to       = BANK_ACCOUNT
        pe9.paid_amount   = 1000.0
        pe9.party_type    = "Customer"
        pe9.party         = CUSTOMER
        pe9.exchange_gain_loss_account = gain_loss_acct
        pe9.reference_name = si9.name
        pe9.reference_type = "Sales Invoice"
        pe9.flags.ignore_permissions = True
        pe9.flags.ignore_mandatory   = True
        pe9.flags.ignore_links       = True
        pe9.insert(ignore_links=True)
        pe9.submit()
        _docs_to_cancel.append(("Payment Entry", pe9.name))
        frappe.db.commit()

        rows = _gl(pe9.name)
        loss_rows = [r for r in rows if r.account == gain_loss_acct]
        if loss_rows:
            loss_dr = sum(flt(r.debit) for r in loss_rows)
            expected_loss = (83.5 - 83.0) * 1000.0  # = 500
            if abs(loss_dr - expected_loss) < 1.0:
                _pass(f"Exchange loss DR = {loss_dr:.2f} (rate diff {83.5-83.0} * 1000)")
            else:
                _fail("Exchange loss amount wrong", f"expected={expected_loss}, got={loss_dr}")
        else:
            _fail("No exchange loss entry found at lower rate")
    except Exception as e:
        _fail("T9 crashed", str(e)[:120])

    # ── T10: Cleanup ──────────────────────────────────────────────────────────
    print("\n--- T10: Cleanup ---")
    try:
        cancelled = 0
        for doctype, name in reversed(_docs_to_cancel):
            try:
                doc = frappe.get_doc(doctype, name)
                if doc.docstatus == 1:
                    doc.cancel()
                    cancelled += 1
            except Exception:
                pass
        frappe.db.commit()
        _pass(f"Cancelled {cancelled} documents")
    except Exception as e:
        _fail("T10 cleanup crashed", str(e)[:120])

    print("\n=== DONE ===")
