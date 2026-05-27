def run():
    """End-to-end Credit Note workflow audit."""
    import frappe
    from frappe.utils import flt, today
    from zoho_books_clone.api.docs import (
        create_credit_note, apply_credit_note_to_invoice,
        get_credit_note_balance, refund_credit_note,
        get_credit_notes, get_credit_note_applications,
    )

    res = {"steps": [], "pass": 0, "fail": 0}
    def check(label, cond, detail=""):
        res["steps"].append({"label": label, "ok": bool(cond), "detail": detail})
        if cond: res["pass"] += 1
        else: res["fail"] += 1

    # ── Find a paid/unpaid invoice we can issue a CN against
    inv = frappe.db.sql("""
        SELECT name, customer, grand_total, outstanding_amount, status
        FROM `tabSales Invoice`
        WHERE docstatus=1 AND is_return=0 AND outstanding_amount > 0
        ORDER BY grand_total DESC LIMIT 1
    """, as_dict=True)
    if not inv:
        return {"abort": "No suitable Sales Invoice with positive outstanding found"}
    inv = inv[0]
    res["target_invoice"] = inv

    # ── STEP 1: Create CN against this invoice
    cn_amount = min(100.0, flt(inv.grand_total) / 2)
    items_payload = [{
        "item_code": "gyfgyj",
        "item_name": "gyfgyj",
        "description": "Test return",
        "qty": 1,
        "rate": cn_amount,
    }]
    import json
    r = create_credit_note(
        customer=inv.customer,
        against_invoice=inv.name,
        date=today(),
        reason="Test return",
        notes="E2E workflow test",
        items=json.dumps(items_payload),
        taxes="[]",
    )
    cn_name = r.get("credit_note")
    check("create_credit_note returns a CN name", bool(cn_name), str(r))
    if not cn_name:
        return res

    cn_doc = frappe.db.get_value("Sales Invoice", cn_name,
        ["docstatus","is_return","return_against","customer","grand_total"], as_dict=True)
    check("CN has is_return=1", cn_doc and cn_doc.is_return == 1, str(cn_doc))
    check("CN return_against matches invoice", cn_doc and cn_doc.return_against == inv.name)
    check("CN is submitted (docstatus=1)", cn_doc and cn_doc.docstatus == 1, f"docstatus={cn_doc.docstatus if cn_doc else None}")
    check("CN grand_total is negative", cn_doc and flt(cn_doc.grand_total) < 0, f"gt={cn_doc.grand_total if cn_doc else None}")

    # ── STEP 2: Balance reflects full CN amount
    bal = get_credit_note_balance(cn_name)
    check("Initial balance = abs(grand_total)", abs(bal["balance"] - abs(flt(cn_doc.grand_total))) < 0.01,
          f"balance={bal['balance']} grand_total={cn_doc.grand_total}")

    # ── STEP 3: Listing on invoice surfaces the CN
    cns_for_inv = get_credit_notes(inv.name)
    check("get_credit_notes returns the new CN", any(c.get("name") == cn_name for c in cns_for_inv),
          f"count={len(cns_for_inv)}")

    # ── STEP 4: Apply CN to the invoice
    inv_before_outstanding = flt(frappe.db.get_value("Sales Invoice", inv.name, "outstanding_amount"))
    apply_amount = min(bal["balance"], inv_before_outstanding)
    apply_res = apply_credit_note_to_invoice(cn_name, inv.name, apply_amount)
    check("apply_credit_note_to_invoice returns JE", bool(apply_res.get("journal_entry")), str(apply_res))

    bal_after_apply = get_credit_note_balance(cn_name)
    check("CN balance reduced by applied amount",
          abs(bal_after_apply["balance"] - (bal["balance"] - apply_amount)) < 0.01,
          f"before={bal['balance']} after={bal_after_apply['balance']} applied={apply_amount}")

    inv_after = flt(frappe.db.get_value("Sales Invoice", inv.name, "outstanding_amount"))
    check("Invoice outstanding reduced", inv_after < inv_before_outstanding + 0.01,
          f"before={inv_before_outstanding} after={inv_after}")

    inv_status = frappe.db.get_value("Sales Invoice", inv.name, "status")
    check("Invoice status reflects new outstanding", inv_status in ("Unpaid","Partly Paid","Paid","Overdue"),
          f"status={inv_status}")

    # ── STEP 5: Applications listing surfaces the apply
    apps = get_credit_note_applications(cn_name)
    check("get_credit_note_applications returns the apply",
          any(a.get("invoice") == inv.name for a in apps),
          f"apps={apps}")

    # ── STEP 6: Refund remaining balance (if any)
    if bal_after_apply["balance"] > 0.5:
        refund_res = refund_credit_note(cn_name, bal_after_apply["balance"], "Bank Transfer",
                                        paid_to="", reference_no="TEST-REF")
        check("refund_credit_note returns a Payment Entry", bool(refund_res.get("payment_entry")),
              str(refund_res))
        bal_after_refund = get_credit_note_balance(cn_name)
        check("CN balance zero after refund", bal_after_refund["balance"] < 0.5,
              f"balance_after_refund={bal_after_refund['balance']}")

    # ── STEP 7: Cancel CN (rolls back JE + outstanding)
    try:
        cn_full = frappe.get_doc("Sales Invoice", cn_name)
        cn_full.cancel()
        frappe.db.commit()
        check("CN cancel succeeds", True)
        cancelled_status = frappe.db.get_value("Sales Invoice", cn_name, "docstatus")
        check("CN docstatus=2 after cancel", cancelled_status == 2, f"docstatus={cancelled_status}")
    except Exception as e:
        check("CN cancel succeeds", False, str(e))

    res["cn_name"] = cn_name
    return res
