"""
L1 — GST Payment API + TDS Entry test.

Scenario:
  T1  pay_gst: CGST=1000, SGST=1000 → 3 GL rows, DR CGST Payable + DR SGST Payable, CR Bank 2000
  T2  pay_gst: IGST only 1800 → 2 GL rows, DR IGST Payable 1800, CR Bank 1800
  T3  pay_gst: zero amount → rejected with ValidationError
  T4  pay_gst: all three (CGST+SGST+IGST) together, challan_ref used as voucher_no
  T5  create_tds_entry: gross=10000, tds=1000 → 3 GL rows balanced; DR Expense=10000, CR TDS=1000, CR AP=9000
  T6  create_tds_entry: tds > gross → rejected
  T7  Cleanup GL entries from T1, T2, T4, T5
"""
import frappe
from frappe.utils import flt, today
import importlib

COMPANY = "Eiffele gaming"


def _gl(voucher_no, cancelled=0):
    return frappe.db.get_all(
        "General Ledger Entry",
        filters={"voucher_no": voucher_no, "is_cancelled": cancelled},
        fields=["account", "debit", "credit"],
    )


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def run():
    print("\n=== GST Payment API L1 Test ===")

    COMPANY = "Eiffele gaming"

    # Reload gst module so fixes in api/gst.py take effect in this session
    import zoho_books_clone.api.gst as gst_mod
    importlib.reload(gst_mod)
    from zoho_books_clone.api.gst import pay_gst, create_tds_entry

    bank_gl   = frappe.db.get_value("Account", {"account_type": "Bank", "company": COMPANY, "is_group": 0}, "name")
    exp_acct  = frappe.db.get_value("Account", {"account_type": "Expense", "company": COMPANY, "is_group": 0}, "name")
    ap_acct   = frappe.db.get_value("Account", {"account_type": "Payable", "company": COMPANY, "is_group": 0}, "name")
    print(f"  bank_gl={bank_gl}  exp={exp_acct}  ap={ap_acct}")

    # Use unique challan refs so each test run's GL entries are isolated
    REF1     = f"TEST-CGST-SGST-{today()}-A"
    REF2     = f"TEST-IGST-{today()}-B"
    REF4     = f"TEST-ALL-GST-{today()}-D"
    # TDS voucher_no is deterministic from party name (mirrors create_tds_entry logic)
    TDS_PARTY = "Test Vendor"
    REF5_TDS = f"TDS-{TDS_PARTY[:10].upper().replace(' ', '-')}-{today()}"

    # Clean up any leftover from a prior run
    for ref in [REF1, REF2, REF4, REF5_TDS]:
        frappe.db.sql(
            "UPDATE `tabGeneral Ledger Entry` SET is_cancelled=1 WHERE voucher_no=%s", ref
        )
    frappe.db.commit()

    # ── T1: CGST+SGST payment ────────────────────────────────────────────────────
    print("\n--- T1: pay_gst CGST=1000, SGST=1000 ---")
    try:
        pay_gst(COMPANY, cgst_amount="1000", sgst_amount="1000",
                bank_account=None, challan_ref=REF1)
        frappe.db.commit()

        rows = _gl(REF1)
        total_dr = sum(flt(r.debit)  for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)

        if len(rows) == 3:
            _pass(f"3 GL rows (CGST + SGST + Bank)")
        else:
            _fail("GL row count", f"got {len(rows)}, expect 3")

        if abs(total_dr - 2000) < 0.01:
            _pass("Total debit = 2000")
        else:
            _fail("Total debit wrong", f"{total_dr:.2f}")

        if abs(total_dr - total_cr) < 0.01:
            _pass("DR = CR (balanced)")
        else:
            _fail("DR ≠ CR", f"DR={total_dr:.2f} CR={total_cr:.2f}")

        bank_row  = next((r for r in rows if r.account == bank_gl), None)
        cgst_row  = next((r for r in rows if "CGST" in (r.account or "")), None)
        sgst_row  = next((r for r in rows if "SGST" in (r.account or "")), None)

        if bank_row and abs(flt(bank_row.credit) - 2000) < 0.01:
            _pass(f"Bank credited 2000 ({bank_gl})")
        else:
            _fail("Bank credit wrong", str(bank_row))

        if cgst_row and "Payable" in cgst_row.account and abs(flt(cgst_row.debit) - 1000) < 0.01:
            _pass(f"CGST Payable debited 1000 ({cgst_row.account})")
        else:
            _fail("CGST Payable debit wrong", str(cgst_row))

        if sgst_row and "Payable" in sgst_row.account and abs(flt(sgst_row.debit) - 1000) < 0.01:
            _pass(f"SGST Payable debited 1000 ({sgst_row.account})")
        else:
            _fail("SGST Payable debit wrong", str(sgst_row))

    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    # ── T2: IGST-only payment ────────────────────────────────────────────────────
    print("\n--- T2: pay_gst IGST=1800 ---")
    try:
        pay_gst(COMPANY, igst_amount="1800", challan_ref=REF2)
        frappe.db.commit()

        rows = _gl(REF2)
        total_dr = sum(flt(r.debit)  for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)

        if len(rows) == 2:
            _pass("2 GL rows (IGST + Bank)")
        else:
            _fail("GL row count", f"got {len(rows)}, expect 2")

        igst_row = next((r for r in rows if "IGST" in (r.account or "")), None)
        if igst_row and "Payable" in igst_row.account and abs(flt(igst_row.debit) - 1800) < 0.01:
            _pass(f"IGST Payable debited 1800 ({igst_row.account})")
        else:
            _fail("IGST Payable debit wrong", str(igst_row))

        if abs(total_dr - total_cr) < 0.01:
            _pass("DR = CR (balanced)")
        else:
            _fail("DR ≠ CR", f"{total_dr:.2f} vs {total_cr:.2f}")

    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: Zero amount → rejected ───────────────────────────────────────────────
    print("\n--- T3: pay_gst zero → must be rejected ---")
    try:
        pay_gst(COMPANY, cgst_amount="0", sgst_amount="0", igst_amount="0")
        _fail("Zero amount accepted (should have thrown)")
    except Exception as e:
        msg = str(e)
        if "positive" in msg.lower() or "amount" in msg.lower():
            _pass(f"Zero rejected: {msg[:60]}")
        else:
            _fail("Wrong error for zero amount", msg[:60])

    # ── T4: All three + challan_ref used as voucher_no ───────────────────────────
    print("\n--- T4: pay_gst CGST=500, SGST=500, IGST=200, challan_ref used ---")
    try:
        res4 = pay_gst(COMPANY, cgst_amount="500", sgst_amount="500", igst_amount="200",
                       challan_ref=REF4)
        frappe.db.commit()

        if res4.get("voucher_no") == REF4:
            _pass(f"challan_ref used as voucher_no: {REF4}")
        else:
            _fail("voucher_no mismatch", f"got {res4.get('voucher_no')}")

        rows = _gl(REF4)
        if len(rows) == 4:
            _pass("4 GL rows (CGST + SGST + IGST + Bank)")
        else:
            _fail("GL row count", f"got {len(rows)}, expect 4")

        total_dr = sum(flt(r.debit) for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)
        if abs(total_dr - 1200) < 0.01 and abs(total_dr - total_cr) < 0.01:
            _pass("Total 1200, balanced")
        else:
            _fail("Total or balance wrong", f"DR={total_dr:.2f} CR={total_cr:.2f}")

    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: create_tds_entry gross=10000, tds=1000 ──────────────────────────────
    print("\n--- T5: create_tds_entry gross=10000, tds=1000 (10%) ---")
    try:
        res5 = create_tds_entry(
            company=COMPANY,
            party="Test Vendor",
            expense_account=exp_acct,
            amount="10000",
            tds_amount="1000",
            tds_section="194C",
            remarks="Test TDS",
        )
        # Override voucher_no so we can find GL rows reliably
        actual_vno = res5.get("voucher_no")
        frappe.db.commit()

        rows = _gl(actual_vno)
        total_dr = sum(flt(r.debit)  for r in rows)
        total_cr = sum(flt(r.credit) for r in rows)

        if len(rows) == 3:
            _pass(f"3 GL rows (Expense + TDS + AP) — voucher {actual_vno}")
        else:
            _fail("GL row count", f"got {len(rows)}, expect 3")

        exp_row = next((r for r in rows if r.account == exp_acct), None)
        ap_row  = next((r for r in rows if r.account == ap_acct), None)

        if exp_row and abs(flt(exp_row.debit) - 10000) < 0.01:
            _pass("Expense debited 10000")
        else:
            _fail("Expense debit wrong", str(exp_row))

        if ap_row and abs(flt(ap_row.credit) - 9000) < 0.01:
            _pass("AP credited 9000 (net payable)")
        else:
            _fail("AP credit wrong", str(ap_row))

        if abs(total_dr - total_cr) < 0.01:
            _pass(f"DR = CR = {total_dr:.0f} (balanced)")
        else:
            _fail("DR ≠ CR", f"DR={total_dr:.2f} CR={total_cr:.2f}")

        # Clean up T5 immediately
        frappe.db.sql(
            "UPDATE `tabGeneral Ledger Entry` SET is_cancelled=1 WHERE voucher_no=%s", actual_vno
        )
        frappe.db.commit()

    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: TDS > gross → rejected ───────────────────────────────────────────────
    print("\n--- T6: create_tds_entry tds > gross → must be rejected ---")
    try:
        create_tds_entry(COMPANY, "Test", exp_acct, amount="1000", tds_amount="1500")
        _fail("TDS > gross accepted (should have thrown)")
    except Exception as e:
        msg = str(e)
        if "tds" in msg.lower() or "amount" in msg.lower() or "between" in msg.lower():
            _pass(f"TDS > gross rejected: {msg[:60]}")
        else:
            _fail("Wrong error for TDS > gross", msg[:60])

    # ── T7: Cleanup ──────────────────────────────────────────────────────────────
    print("\n--- T7: Cleanup ---")
    cleaned = 0
    for ref in [REF1, REF2, REF4]:
        frappe.db.sql(
            "UPDATE `tabGeneral Ledger Entry` SET is_cancelled=1 WHERE voucher_no=%s AND is_cancelled=0",
            ref
        )
        cleaned += 1
    frappe.db.commit()
    _pass(f"Cancelled GL entries for {cleaned} vouchers")

    print("\n=== DONE ===")
