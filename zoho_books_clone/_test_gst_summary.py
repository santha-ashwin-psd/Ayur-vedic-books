"""
L1 — GST Summary Report test.

Scenario:
  T1  get_gst_summary() → list, required fields present (tax_type, invoice_count, total_tax)
  T2  get_gstr_summary() → all 4 sections (output, itc, net_by_type, totals)
  T3  get_gstr_summary().totals net_tax_liability == output - ITC (even when both zero)
  T4  Create SI with CGST 9% + SGST 9% (net=10000) → both Tax Lines with correct tax_type
  T5  Tax Line amounts for SI match GL credits to CGST Payable + SGST Payable
  T6  get_gst_summary() → CGST and SGST rows appear with correct amounts
  T7  Create PINV with CGST 9% + SGST 9% ITC (net=5000)
  T8  ITC Tax Line amounts match GL debits to CGST Input + SGST Input
  T9  Create SI with IGST 18% (net=10000) → IGST Tax Line
  T10 get_gstr_summary() output == CGST+SGST+IGST from SIs; ITC from PINV
  T11 net_tax_liability == total_output - total_ITC
  T12 get_gst_summary() invoice_count accurate per tax_type
  T13 Cancelled SI tax excluded from summary
  T14 Cleanup
"""
import frappe
from frappe.utils import flt, today, add_days, get_first_day, get_last_day

COMPANY = "Eiffele gaming"
DATE    = today()
SOM     = str(get_first_day(DATE))
EOM     = str(get_last_day(DATE))


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _lookup():
    customer = frappe.db.get_value("Customer", {}, "name")
    supplier = frappe.db.get_value("Supplier", {}, "name")
    ar    = frappe.db.get_value("Account", {"account_type": "Receivable", "company": COMPANY, "is_group": 0}, "name")
    inc   = frappe.db.get_value("Account", {"account_type": "Income",     "company": COMPANY, "is_group": 0}, "name")
    exp   = frappe.db.get_value("Account", {"account_type": "Expense",    "company": COMPANY, "is_group": 0}, "name")
    pay   = frappe.db.get_value("Account", {"account_type": "Payable",    "company": COMPANY, "is_group": 0}, "name")
    # Output (liability) accounts — like match for company-suffixed names
    cgst_out = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY,
                                                "account_name": ["like", "%CGST%Payable%"], "is_group": 0}, "name")
    sgst_out = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY,
                                                "account_name": ["like", "%SGST%Payable%"], "is_group": 0}, "name")
    igst_out = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY,
                                                "account_name": ["like", "%IGST%Payable%"], "is_group": 0}, "name")
    # Input (ITC asset) accounts
    cgst_in  = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY,
                                                "account_name": ["like", "%CGST%Input%"], "is_group": 0}, "name")
    sgst_in  = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY,
                                                "account_name": ["like", "%SGST%Input%"], "is_group": 0}, "name")
    igst_in  = frappe.db.get_value("Account", {"account_type": "Tax", "company": COMPANY,
                                                "account_name": ["like", "%IGST%Input%"], "is_group": 0}, "name")
    return dict(customer=customer, supplier=supplier,
                ar=ar, inc=inc, exp=exp, pay=pay,
                cgst_out=cgst_out, sgst_out=sgst_out, igst_out=igst_out,
                cgst_in=cgst_in,   sgst_in=sgst_in,   igst_in=igst_in)


def _make_si(a, net, taxes):
    doc = frappe.get_doc({
        "doctype": "Sales Invoice", "customer": a["customer"],
        "posting_date": DATE, "due_date": add_days(DATE, 30),
        "company": COMPANY, "debit_to": a["ar"], "income_account": a["inc"],
        "items": [{"item_name": "Test GST Item", "qty": 1, "rate": net, "amount": net}],
        "taxes": taxes,
    })
    doc.flags.ignore_permissions = True
    doc.insert()
    doc.submit()
    frappe.db.commit()
    return doc


def _make_pinv(a, net, taxes):
    doc = frappe.get_doc({
        "doctype": "Purchase Invoice", "supplier": a["supplier"],
        "posting_date": DATE, "company": COMPANY,
        "credit_to": a["pay"], "expense_account": a["exp"],
        "items": [{"item_name": "Test GST Item", "qty": 1, "rate": net, "amount": net}],
        "taxes": taxes,
    })
    doc.flags.ignore_permissions = True
    doc.insert()
    doc.submit()
    frappe.db.commit()
    return doc


def _gl_for(voucher_no):
    return frappe.db.get_all(
        "General Ledger Entry",
        filters={"voucher_no": voucher_no, "is_cancelled": 0, "is_reversal": 0},
        fields=["account", "debit", "credit"],
    )


def run():
    print("\n=== GST Summary Report L1 Test ===")

    import importlib
    import zoho_books_clone.db.queries as q_mod
    importlib.reload(q_mod)
    from zoho_books_clone.db.queries import get_gst_summary, get_gstr_summary

    a = _lookup()
    print(f"  CGST_out={a['cgst_out']}  SGST_out={a['sgst_out']}  IGST_out={a['igst_out']}")
    print(f"  CGST_in={a['cgst_in']}   SGST_in={a['sgst_in']}    IGST_in={a['igst_in']}")

    missing = [k for k, v in a.items() if not v]
    if missing:
        print(f"  ABORT: missing accounts/parties: {missing}")
        return

    si_cgst_sgst = si_igst = pi_itc = None

    # ── T1: get_gst_summary structure ─────────────────────────────────────────
    print("\n--- T1: get_gst_summary() → list with required fields ---")
    try:
        summary = get_gst_summary(COMPANY, SOM, EOM)
        if isinstance(summary, list):
            _pass(f"get_gst_summary returns list ({len(summary)} rows)")
        else:
            _fail("Non-list result", type(summary).__name__)

        if summary:
            row = summary[0]
            gst_keys = {"tax_type", "invoice_count", "total_tax"}
            missing_keys = gst_keys - set(row.keys())
            if not missing_keys:
                _pass("All gst_summary keys present")
            else:
                _fail("Missing gst_summary keys", str(missing_keys))
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    # ── T2: get_gstr_summary() → all 4 sections ───────────────────────────────
    print("\n--- T2: get_gstr_summary() → 4 sections present ---")
    try:
        gstr = get_gstr_summary(COMPANY, SOM, EOM)
        gstr_sections = {"output", "itc", "net_by_type", "totals"}
        missing_sec = gstr_sections - set(gstr.keys())
        if not missing_sec:
            _pass("All 4 GSTR sections present")
        else:
            _fail("Missing sections", str(missing_sec))

        totals_keys = {"total_output", "total_itc", "net_tax_liability"}
        missing_tot = totals_keys - set(gstr.get("totals", {}).keys())
        if not missing_tot:
            _pass("All totals keys present")
        else:
            _fail("Missing totals keys", str(missing_tot))
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: net_tax_liability == output - ITC (baseline, may be zero) ─────────
    print("\n--- T3: net_tax_liability == total_output - total_itc ---")
    try:
        gstr = get_gstr_summary(COMPANY, SOM, EOM)
        t = gstr.get("totals", {})
        expected = flt(t.get("total_output")) - flt(t.get("total_itc"))
        actual   = flt(t.get("net_tax_liability"))
        if abs(expected - actual) < 0.01:
            _pass(f"net_tax_liability = {actual:.2f} (output={flt(t.get('total_output')):.2f} - ITC={flt(t.get('total_itc')):.2f})")
        else:
            _fail("net_tax_liability formula wrong", f"expected={expected:.2f}, got={actual:.2f}")
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: Create SI with CGST+SGST, correct tax_type fields ─────────────────
    print("\n--- T4: Create SI with CGST 9% + SGST 9% (net=10000) ---")
    try:
        si_cgst_sgst = _make_si(a, 10000, [
            {"tax_type": "CGST", "description": "CGST @ 9%", "rate": 9, "tax_amount": 900, "account_head": a["cgst_out"]},
            {"tax_type": "SGST", "description": "SGST @ 9%", "rate": 9, "tax_amount": 900, "account_head": a["sgst_out"]},
        ])
        _pass(f"SI created and submitted: {si_cgst_sgst.name}")

        # Verify Tax Lines were saved with correct tax_type
        tl_rows = frappe.db.get_all(
            "Tax Line",
            filters={"parent": si_cgst_sgst.name},
            fields=["tax_type", "tax_amount", "account_head"],
        )
        cgst_tl = next((r for r in tl_rows if r.tax_type == "CGST"), None)
        sgst_tl = next((r for r in tl_rows if r.tax_type == "SGST"), None)
        if cgst_tl:
            _pass(f"Tax Line: tax_type=CGST, amount={flt(cgst_tl.tax_amount):.0f}")
        else:
            _fail("CGST Tax Line with tax_type='CGST' not found", str(tl_rows))
        if sgst_tl:
            _pass(f"Tax Line: tax_type=SGST, amount={flt(sgst_tl.tax_amount):.0f}")
        else:
            _fail("SGST Tax Line with tax_type='SGST' not found", str(tl_rows))
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: GL credits to CGST/SGST Payable == Tax Line amounts ──────────────
    print("\n--- T5: GL credits to tax accounts == Tax Line amounts ---")
    try:
        if si_cgst_sgst:
            gl_rows = _gl_for(si_cgst_sgst.name)
            cgst_gl = next((r for r in gl_rows if r.account == a["cgst_out"]), None)
            sgst_gl = next((r for r in gl_rows if r.account == a["sgst_out"]), None)

            if cgst_gl and abs(flt(cgst_gl.credit) - 900) < 0.01:
                _pass(f"GL credit to CGST Payable = 900 (matches Tax Line)")
            else:
                _fail("CGST GL credit mismatch", str(cgst_gl))
            if sgst_gl and abs(flt(sgst_gl.credit) - 900) < 0.01:
                _pass(f"GL credit to SGST Payable = 900 (matches Tax Line)")
            else:
                _fail("SGST GL credit mismatch", str(sgst_gl))

            # Total GL is balanced
            total_dr = sum(flt(r.debit) for r in gl_rows)
            total_cr = sum(flt(r.credit) for r in gl_rows)
            if abs(total_dr - total_cr) < 0.01:
                _pass(f"GL balanced: DR=CR={total_dr:.2f}")
            else:
                _fail("GL not balanced", f"DR={total_dr:.2f} CR={total_cr:.2f}")
        else:
            _fail("Skipped (T4 failed)")
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: get_gst_summary now shows CGST and SGST rows ─────────────────────
    print("\n--- T6: get_gst_summary() shows CGST and SGST rows ---")
    try:
        summary = get_gst_summary(COMPANY, SOM, EOM)
        by_type = {r.get("tax_type"): r for r in summary}

        cgst_row = by_type.get("CGST")
        sgst_row = by_type.get("SGST")

        if cgst_row and flt(cgst_row.get("total_tax")) >= 900:
            _pass(f"CGST row: total_tax={flt(cgst_row['total_tax']):.2f}, "
                  f"invoice_count={cgst_row['invoice_count']}")
        else:
            _fail("CGST row missing or wrong amount", str(cgst_row))

        if sgst_row and flt(sgst_row.get("total_tax")) >= 900:
            _pass(f"SGST row: total_tax={flt(sgst_row['total_tax']):.2f}, "
                  f"invoice_count={sgst_row['invoice_count']}")
        else:
            _fail("SGST row missing or wrong amount", str(sgst_row))
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: Create PINV with CGST+SGST ITC ────────────────────────────────────
    print("\n--- T7: Create PINV with CGST 9% + SGST 9% ITC (net=5000) ---")
    try:
        pi_itc = _make_pinv(a, 5000, [
            {"tax_type": "CGST", "description": "ITC CGST @ 9%", "rate": 9, "tax_amount": 450, "account_head": a["cgst_in"]},
            {"tax_type": "SGST", "description": "ITC SGST @ 9%", "rate": 9, "tax_amount": 450, "account_head": a["sgst_in"]},
        ])
        _pass(f"PINV created and submitted: {pi_itc.name}")

        tl_rows = frappe.db.get_all(
            "Tax Line",
            filters={"parent": pi_itc.name},
            fields=["tax_type", "tax_amount", "account_head"],
        )
        cgst_tl = next((r for r in tl_rows if r.tax_type == "CGST"), None)
        sgst_tl = next((r for r in tl_rows if r.tax_type == "SGST"), None)
        if cgst_tl and abs(flt(cgst_tl.tax_amount) - 450) < 0.01:
            _pass(f"PINV CGST Tax Line saved: amount={flt(cgst_tl.tax_amount):.0f}")
        else:
            _fail("PINV CGST Tax Line wrong", str(cgst_tl))
        if sgst_tl and abs(flt(sgst_tl.tax_amount) - 450) < 0.01:
            _pass(f"PINV SGST Tax Line saved: amount={flt(sgst_tl.tax_amount):.0f}")
        else:
            _fail("PINV SGST Tax Line wrong", str(sgst_tl))
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: GL debits to ITC accounts == Tax Line amounts ────────────────────
    print("\n--- T8: GL debits to ITC accounts == Tax Line amounts ---")
    try:
        if pi_itc:
            gl_rows = _gl_for(pi_itc.name)
            cgst_gl = next((r for r in gl_rows if r.account == a["cgst_in"]), None)
            sgst_gl = next((r for r in gl_rows if r.account == a["sgst_in"]), None)

            if cgst_gl and abs(flt(cgst_gl.debit) - 450) < 0.01:
                _pass(f"GL debit to CGST Input = 450 (matches Tax Line)")
            else:
                _fail("CGST Input GL debit mismatch", str(cgst_gl))
            if sgst_gl and abs(flt(sgst_gl.debit) - 450) < 0.01:
                _pass(f"GL debit to SGST Input = 450 (matches Tax Line)")
            else:
                _fail("SGST Input GL debit mismatch", str(sgst_gl))

            total_dr = sum(flt(r.debit)  for r in gl_rows)
            total_cr = sum(flt(r.credit) for r in gl_rows)
            if abs(total_dr - total_cr) < 0.01:
                _pass(f"PINV GL balanced: DR=CR={total_dr:.2f}")
            else:
                _fail("PINV GL not balanced", f"DR={total_dr:.2f} CR={total_cr:.2f}")
        else:
            _fail("Skipped (T7 failed)")
    except Exception as e:
        _fail("T8 crashed", str(e)[:120])

    # ── T9: Create SI with IGST 18% ───────────────────────────────────────────
    print("\n--- T9: Create SI with IGST 18% (net=10000) ---")
    try:
        si_igst = _make_si(a, 10000, [
            {"tax_type": "IGST", "description": "IGST @ 18%", "rate": 18, "tax_amount": 1800, "account_head": a["igst_out"]},
        ])
        _pass(f"IGST SI created: {si_igst.name}")

        tl_rows = frappe.db.get_all(
            "Tax Line",
            filters={"parent": si_igst.name},
            fields=["tax_type", "tax_amount", "account_head"],
        )
        igst_tl = next((r for r in tl_rows if r.tax_type == "IGST"), None)
        if igst_tl and abs(flt(igst_tl.tax_amount) - 1800) < 0.01:
            _pass(f"IGST Tax Line: amount={flt(igst_tl.tax_amount):.0f}")
        else:
            _fail("IGST Tax Line wrong", str(tl_rows))

        # GL check
        gl_rows = _gl_for(si_igst.name)
        igst_gl = next((r for r in gl_rows if r.account == a["igst_out"]), None)
        if igst_gl and abs(flt(igst_gl.credit) - 1800) < 0.01:
            _pass(f"GL credit to IGST Payable = 1800")
        else:
            _fail("IGST GL credit wrong", str(igst_gl))
    except Exception as e:
        _fail("T9 crashed", str(e)[:120])
        si_igst = None

    # ── T10: get_gstr_summary output matches sum of SI Tax Lines ──────────────
    print("\n--- T10: get_gstr_summary() output == sum of SI Tax Lines ---")
    try:
        gstr = get_gstr_summary(COMPANY, SOM, EOM)
        t = gstr.get("totals", {})

        # Expected: CGST 900 + SGST 900 + IGST 1800 = 3600 from our 2 SIs
        # (there may be other SIs in the period, so check >= expected minimum)
        expected_output_min = 900 + 900 + 1800   # our 3 tax lines
        expected_itc_min    = 450 + 450            # our 2 ITC lines

        total_output = flt(t.get("total_output"))
        total_itc    = flt(t.get("total_itc"))

        if total_output >= expected_output_min - 0.01:
            _pass(f"total_output={total_output:.2f} >= expected {expected_output_min} (our SI taxes)")
        else:
            _fail("total_output too low", f"got={total_output:.2f}, expected>={expected_output_min}")

        if total_itc >= expected_itc_min - 0.01:
            _pass(f"total_itc={total_itc:.2f} >= expected {expected_itc_min} (our PINV ITC)")
        else:
            _fail("total_itc too low", f"got={total_itc:.2f}, expected>={expected_itc_min}")

        # Cross-check output against direct Tax Line sum on submitted SIs
        tl_total = flt(frappe.db.sql("""
            SELECT COALESCE(SUM(tl.tax_amount), 0) AS total
            FROM `tabTax Line` tl
            JOIN `tabSales Invoice` si ON si.name = tl.parent
            WHERE si.company = %(co)s AND si.docstatus = 1
              AND si.posting_date BETWEEN %(s)s AND %(e)s
              AND tl.tax_type IN ('CGST','SGST','IGST')
        """, {"co": COMPANY, "s": SOM, "e": EOM}, as_dict=True)[0].total)

        if abs(total_output - tl_total) < 0.01:
            _pass(f"gstr output ({total_output:.2f}) == direct Tax Line sum ({tl_total:.2f})")
        else:
            _fail("gstr output != Tax Line sum",
                  f"gstr={total_output:.2f}, tl_sum={tl_total:.2f}")
    except Exception as e:
        _fail("T10 crashed", str(e)[:120])

    # ── T11: net_tax_liability == total_output - total_ITC ────────────────────
    print("\n--- T11: net_tax_liability == total_output - total_ITC ---")
    try:
        gstr = get_gstr_summary(COMPANY, SOM, EOM)
        t = gstr.get("totals", {})
        expected_net = flt(t.get("total_output")) - flt(t.get("total_itc"))
        actual_net   = flt(t.get("net_tax_liability"))
        if abs(expected_net - actual_net) < 0.01:
            _pass(f"net_tax_liability={actual_net:.2f} = {flt(t['total_output']):.2f} - {flt(t['total_itc']):.2f}")
        else:
            _fail("net_tax_liability formula wrong",
                  f"expected={expected_net:.2f}, got={actual_net:.2f}")
    except Exception as e:
        _fail("T11 crashed", str(e)[:120])

    # ── T12: invoice_count accurate per tax_type ──────────────────────────────
    print("\n--- T12: get_gst_summary invoice_count accurate ---")
    try:
        summary = get_gst_summary(COMPANY, SOM, EOM)
        by_type = {r.get("tax_type"): r for r in summary}

        # Count distinct SI parents per tax_type directly
        for tax_t in ("CGST", "SGST", "IGST"):
            expected_count = frappe.db.sql("""
                SELECT COUNT(DISTINCT tl.parent) AS cnt
                FROM `tabTax Line` tl
                JOIN `tabSales Invoice` si ON si.name = tl.parent
                WHERE si.company = %(co)s AND si.docstatus = 1
                  AND si.posting_date BETWEEN %(s)s AND %(e)s
                  AND tl.tax_type = %(tt)s
            """, {"co": COMPANY, "s": SOM, "e": EOM, "tt": tax_t}, as_dict=True)
            exp = expected_count[0].cnt if expected_count else 0
            got_row = by_type.get(tax_t, {})
            got_cnt = got_row.get("invoice_count", 0) if got_row else 0

            if abs(int(got_cnt) - int(exp)) <= 0:
                _pass(f"{tax_t}: invoice_count={got_cnt} (matches direct count={exp})")
            else:
                _fail(f"{tax_t} invoice_count wrong", f"got={got_cnt}, expected={exp}")
    except Exception as e:
        _fail("T12 crashed", str(e)[:120])

    # ── T13: Cancelled SI tax excluded from summary ───────────────────────────
    print("\n--- T13: Cancelled SI tax excluded from get_gst_summary ---")
    try:
        # Create and immediately cancel an SI with CGST
        si_cancel = _make_si(a, 5000, [
            {"tax_type": "CGST", "description": "CGST @ 9%", "rate": 9,
             "tax_amount": 450, "account_head": a["cgst_out"]},
        ])
        # Capture summary BEFORE cancel
        summary_before = get_gst_summary(COMPANY, SOM, EOM)
        cgst_before = flt(next((r for r in summary_before if r.get("tax_type") == "CGST"), {}).get("total_tax", 0))

        si_cancel.cancel()
        frappe.db.commit()

        # Capture summary AFTER cancel
        summary_after = get_gst_summary(COMPANY, SOM, EOM)
        cgst_after = flt(next((r for r in summary_after if r.get("tax_type") == "CGST"), {}).get("total_tax", 0))

        if abs(cgst_before - cgst_after - 450) < 0.01:
            _pass(f"Cancelled SI tax excluded: CGST dropped from {cgst_before:.0f} to {cgst_after:.0f} (-450)")
        else:
            _fail("Cancel did not reduce CGST summary",
                  f"before={cgst_before:.0f}, after={cgst_after:.0f}, expected diff=450")
    except Exception as e:
        _fail("T13 crashed", str(e)[:120])
        si_cancel = None

    # ── T14: Cleanup ──────────────────────────────────────────────────────────
    print("\n--- T14: Cleanup ---")
    cleaned = 0
    to_cancel = [
        (si_cgst_sgst, "Sales Invoice"),
        (si_igst,      "Sales Invoice"),
        (pi_itc,       "Purchase Invoice"),
    ]
    for doc, dt in to_cancel:
        if not doc:
            continue
        try:
            d = frappe.get_doc(dt, doc.name)
            if d.docstatus == 1:
                d.cancel()
                frappe.db.commit()
            cleaned += 1
        except Exception as ex:
            print(f"    warn: could not cancel {doc.name}: {str(ex)[:60]}")
    _pass(f"Cancelled {cleaned} test documents")

    print("\n=== DONE ===")
