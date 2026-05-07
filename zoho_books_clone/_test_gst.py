"""
L1 — GST / Tax on Invoices test.

Scenario:
  T1  Sales Invoice: CGST 9% + SGST 9% on 10,000 net
        → 4 GL rows, debit AR=11800, credit Income=10000 + CGST Payable=900 + SGST Payable=900
        → DR = CR = 11800
  T2  Purchase Invoice: CGST 9% + SGST 9% on 5,000 net
        → 4 GL rows, debit Expense=5000 + Input Tax Credits=450 + SGST Input=450
        → credit Payable=5900, DR = CR = 5900
  T3  Sales Invoice: IGST 18% (interstate) on 10,000 net
        → 3 GL rows, debit AR=11800, credit Income=10000 + IGST Payable=1800
  T4  SI with no taxes → 2 GL rows only
  T5  Cancel T1 SI → GL rows reversed (is_cancelled=1 on originals, reversal rows added)
  T6  Cleanup
"""
import frappe
from frappe.utils import flt, today, add_days

COMPANY  = "Eiffele gaming"
DATE     = today()


def _gl(voucher_no, account=None, cancelled=None):
    filters = {"voucher_no": voucher_no}
    if account:
        filters["account"] = account
    if cancelled is not None:
        filters["is_cancelled"] = cancelled
    return frappe.db.get_all(
        "General Ledger Entry", filters=filters,
        fields=["account", "debit", "credit", "is_cancelled"],
    )


def _gl_count(voucher_no, cancelled=0):
    return len(_gl(voucher_no, cancelled=cancelled))


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _lookup(company=COMPANY):
    customer   = frappe.db.get_value("Customer", {}, "name")
    supplier   = frappe.db.get_value("Supplier", {}, "name")
    ar_acct    = frappe.db.get_value("Account", {"account_type": "Receivable", "company": company, "is_group": 0}, "name")
    inc_acct   = frappe.db.get_value("Account", {"account_type": "Income",     "company": company, "is_group": 0}, "name")
    exp_acct   = frappe.db.get_value("Account", {"account_type": "Expense",    "company": company, "is_group": 0}, "name")
    pay_acct   = frappe.db.get_value("Account", {"account_type": "Payable",    "company": company, "is_group": 0}, "name")
    cgst_out   = frappe.db.get_value("Account", {"account_type": "Tax", "company": company,
                                                  "account_name": ["like", "%CGST%Payable%"], "is_group": 0}, "name")
    sgst_out   = frappe.db.get_value("Account", {"account_type": "Tax", "company": company,
                                                  "account_name": ["like", "%SGST%Payable%"], "is_group": 0}, "name")
    igst_out   = frappe.db.get_value("Account", {"account_type": "Tax", "company": company,
                                                  "account_name": ["like", "%IGST%Payable%"], "is_group": 0}, "name")
    cgst_in    = frappe.db.get_value("Account", {"account_type": "Tax", "company": company,
                                                  "account_name": ["like", "%CGST%Input%"], "is_group": 0}, "name")
    sgst_in    = frappe.db.get_value("Account", {"account_type": "Tax", "company": company,
                                                  "account_name": ["like", "%SGST%Input%"], "is_group": 0}, "name")
    igst_in    = frappe.db.get_value("Account", {"account_type": "Tax", "company": company,
                                                  "account_name": ["like", "%IGST%Input%"], "is_group": 0}, "name")
    return {
        "customer": customer, "supplier": supplier,
        "ar": ar_acct, "inc": inc_acct, "exp": exp_acct, "pay": pay_acct,
        "cgst_out": cgst_out, "sgst_out": sgst_out, "igst_out": igst_out,
        "cgst_in": cgst_in, "sgst_in": sgst_in, "igst_in": igst_in,
    }


def _make_si(a, net, taxes, date=None):
    """Create, insert, and submit a Sales Invoice with given taxes list."""
    date = date or DATE
    si = frappe.get_doc({
        "doctype":        "Sales Invoice",
        "customer":       a["customer"],
        "posting_date":   date,
        "due_date":       add_days(date, 30),
        "company":        COMPANY,
        "debit_to":       a["ar"],
        "income_account": a["inc"],
        "items": [{"item_name": "Test Item", "qty": 1, "rate": net, "amount": net}],
        "taxes": taxes,
    })
    si.flags.ignore_permissions = True
    si.insert()
    si.submit()
    frappe.db.commit()
    return si


def _make_pinv(a, net, taxes, date=None):
    """Create, insert, and submit a Purchase Invoice with given taxes list."""
    date = date or DATE
    pi = frappe.get_doc({
        "doctype":          "Purchase Invoice",
        "supplier":         a["supplier"],
        "posting_date":     date,
        "company":          COMPANY,
        "credit_to":        a["pay"],
        "expense_account":  a["exp"],
        "items": [{"item_name": "Test Item", "qty": 1, "rate": net, "amount": net}],
        "taxes": taxes,
    })
    pi.flags.ignore_permissions = True
    pi.insert()
    pi.submit()
    frappe.db.commit()
    return pi


def run():
    print("\n=== GST / Tax on Invoices L1 Test ===")

    a = _lookup()
    print(f"  customer={a['customer']}  supplier={a['supplier']}")
    print(f"  AR={a['ar']}  Inc={a['inc']}  Exp={a['exp']}  Pay={a['pay']}")
    print(f"  CGST_out={a['cgst_out']}  SGST_out={a['sgst_out']}  IGST_out={a['igst_out']}")
    print(f"  CGST_in={a['cgst_in']}  SGST_in={a['sgst_in']}  IGST_in={a['igst_in']}")

    missing = [k for k, v in a.items() if not v]
    if missing:
        print(f"  ABORT: missing {missing}")
        return

    si1 = si3 = si4 = pi2 = None

    # ── T1: SI with CGST 9% + SGST 9% ──────────────────────────────────────────
    print("\n--- T1: Sales Invoice CGST+SGST (net=10000, each 9%) ---")
    try:
        si1 = _make_si(a, 10000, [
            {"description": "CGST @ 9%",  "rate": 9, "tax_amount": 900,  "account_head": a["cgst_out"]},
            {"description": "SGST @ 9%",  "rate": 9, "tax_amount": 900,  "account_head": a["sgst_out"]},
        ])
        rows = _gl(si1.name, cancelled=0)
        total_dr = sum(flt(r.debit)  for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)

        if len(rows) == 4:
            _pass(f"SI {si1.name}: 4 GL rows")
        else:
            _fail("GL row count", f"got {len(rows)}, expect 4")

        if abs(total_dr - 11800) < 0.01:
            _pass(f"Total debit = 11800")
        else:
            _fail("Total debit wrong", f"{total_dr:.2f}")

        if abs(total_dr - total_cr) < 0.01:
            _pass("DR = CR (balanced)")
        else:
            _fail("DR ≠ CR", f"DR={total_dr:.2f} CR={total_cr:.2f}")

        cgst_row = next((r for r in rows if r.account == a["cgst_out"]), None)
        sgst_row = next((r for r in rows if r.account == a["sgst_out"]), None)
        if cgst_row and abs(flt(cgst_row.credit) - 900) < 0.01:
            _pass("CGST Payable credited 900")
        else:
            _fail("CGST Payable credit wrong", str(cgst_row))
        if sgst_row and abs(flt(sgst_row.credit) - 900) < 0.01:
            _pass("SGST Payable credited 900")
        else:
            _fail("SGST Payable credit wrong", str(sgst_row))

    except Exception as e:
        _fail("T1 crashed", str(e)[:100])

    # ── T2: PINV with CGST 9% + SGST 9% ────────────────────────────────────────
    print("\n--- T2: Purchase Invoice CGST+SGST (net=5000, each 9%) ---")
    try:
        pi2 = _make_pinv(a, 5000, [
            {"description": "CGST Input @ 9%", "rate": 9, "tax_amount": 450, "account_head": a["cgst_in"]},
            {"description": "SGST Input @ 9%", "rate": 9, "tax_amount": 450, "account_head": a["sgst_in"]},
        ])
        rows = _gl(pi2.name, cancelled=0)
        total_dr = sum(flt(r.debit)  for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)

        if len(rows) == 4:
            _pass(f"PINV {pi2.name}: 4 GL rows")
        else:
            _fail("GL row count", f"got {len(rows)}, expect 4")

        if abs(total_cr - 5900) < 0.01:
            _pass("Total credit = 5900 (Payable)")
        else:
            _fail("Total credit wrong", f"{total_cr:.2f}")

        if abs(total_dr - total_cr) < 0.01:
            _pass("DR = CR (balanced)")
        else:
            _fail("DR ≠ CR", f"DR={total_dr:.2f} CR={total_cr:.2f}")

        cgst_in_row = next((r for r in rows if r.account == a["cgst_in"]), None)
        sgst_in_row = next((r for r in rows if r.account == a["sgst_in"]), None)
        if cgst_in_row and abs(flt(cgst_in_row.debit) - 450) < 0.01:
            _pass("Input Tax Credits (CGST) debited 450")
        else:
            _fail("CGST input debit wrong", str(cgst_in_row))
        if sgst_in_row and abs(flt(sgst_in_row.debit) - 450) < 0.01:
            _pass("SGST Input debited 450")
        else:
            _fail("SGST input debit wrong", str(sgst_in_row))

    except Exception as e:
        _fail("T2 crashed", str(e)[:100])

    # ── T3: SI with IGST 18% (interstate) ───────────────────────────────────────
    print("\n--- T3: Sales Invoice IGST only (net=10000, 18%) ---")
    try:
        si3 = _make_si(a, 10000, [
            {"description": "IGST @ 18%", "rate": 18, "tax_amount": 1800, "account_head": a["igst_out"]},
        ])
        rows = _gl(si3.name, cancelled=0)
        total_dr = sum(flt(r.debit)  for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)

        if len(rows) == 3:
            _pass(f"SI {si3.name}: 3 GL rows (1 income + 1 tax + 1 AR)")
        else:
            _fail("GL row count", f"got {len(rows)}, expect 3")

        igst_row = next((r for r in rows if r.account == a["igst_out"]), None)
        if igst_row and abs(flt(igst_row.credit) - 1800) < 0.01:
            _pass("IGST Payable credited 1800")
        else:
            _fail("IGST Payable credit wrong", str(igst_row))

        if abs(total_dr - total_cr) < 0.01:
            _pass("DR = CR (balanced)")
        else:
            _fail("DR ≠ CR", f"DR={total_dr:.2f} CR={total_cr:.2f}")

    except Exception as e:
        _fail("T3 crashed", str(e)[:100])

    # ── T4: SI with no taxes → 2 GL rows only ───────────────────────────────────
    print("\n--- T4: Sales Invoice with no taxes → 2 GL rows ---")
    try:
        si4 = _make_si(a, 8000, [])
        rows = _gl(si4.name, cancelled=0)
        if len(rows) == 2:
            _pass(f"SI {si4.name}: 2 GL rows (no tax)")
        else:
            _fail("GL row count", f"got {len(rows)}, expect 2")
        total_dr = sum(flt(r.debit) for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)
        if abs(total_dr - total_cr) < 0.01:
            _pass("DR = CR (balanced, no tax)")
        else:
            _fail("DR ≠ CR", f"DR={total_dr:.2f} CR={total_cr:.2f}")

    except Exception as e:
        _fail("T4 crashed", str(e)[:100])

    # ── T5: Cancel T1 SI → GL originals cancelled, reversals posted ─────────────
    print("\n--- T5: Cancel SI from T1 → GL reversed ---")
    if si1:
        try:
            si1.cancel()
            frappe.db.commit()
            orig_cancelled = _gl_count(si1.name, cancelled=1)
            if orig_cancelled >= 4:
                _pass(f"Original GL rows marked cancelled ({orig_cancelled} rows)")
            else:
                _fail("Not all originals cancelled", f"got {orig_cancelled}")
            # Reversal rows are is_reversal=1; they are also marked is_cancelled=1 by design
            reversal = frappe.db.get_all(
                "General Ledger Entry",
                {"voucher_no": si1.name, "is_reversal": 1},
                pluck="name",
            )
            if len(reversal) >= 4:
                _pass(f"Reversal GL rows exist ({len(reversal)} rows)")
            else:
                _fail("Reversal rows missing", f"got {len(reversal)}")
        except Exception as e:
            _fail("T5 cancel crashed", str(e)[:100])
    else:
        _fail("T5 skipped — T1 SI not available")

    # ── T6: Cleanup ──────────────────────────────────────────────────────────────
    print("\n--- T6: Cleanup ---")
    cleaned = 0
    for doc_name, doctype in [
        (si3.name if si3 else None, "Sales Invoice"),
        (si4.name if si4 else None, "Sales Invoice"),
        (pi2.name if pi2 else None, "Purchase Invoice"),
    ]:
        if not doc_name:
            continue
        try:
            doc = frappe.get_doc(doctype, doc_name)
            doc.cancel()
            frappe.db.commit()
            cleaned += 1
        except Exception:
            pass
    _pass(f"Cancelled {cleaned} test documents")

    print("\n=== DONE ===")
