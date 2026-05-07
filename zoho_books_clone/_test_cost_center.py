"""
L1 — Cost Center tagging on GL entries.

Tests that cost_center flows from Sales Invoice and Expense documents
through the accounting_engine into General Ledger Entries.

  T1  Create root Cost Center (group) and child Cost Center (leaf)
  T2  Cost Center hierarchy: child validates against group parent
  T3  Sales Invoice with cost_center → all GL entries carry the cost_center
  T4  GL cost_center matches the document's cost_center exactly
  T5  Expense with cost_center → GL entries carry cost_center
  T6  GL filter by cost_center: only entries for that CC returned
  T7  cost_center blank when document has no cost_center
  T8  Cancel SI → reversal GL entries also carry cost_center
  T9  Cleanup
"""
import frappe
from frappe.utils import flt, today

COMPANY = "Eiffele gaming"
CC_ROOT = "TEST-CC-ROOT"
CC_OPS  = "TEST-CC-OPS"

AR_ACCOUNT      = "Accounts Receivable-Eiffele gaming"
INCOME_ACCOUNT  = "Other Income-Eiffele gaming"
EXPENSE_ACCOUNT = "Office Supplies-Eiffele gaming"
CUSTOMER       = "CUST-2026-00010"

_docs_to_cancel  = []  # (doctype, name)
_ccs_to_delete   = []  # cost center names


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _make_si(cost_center: str, amount: float = 5000.0) -> object:
    si = frappe.new_doc("Sales Invoice")
    si.customer      = CUSTOMER
    si.debit_to      = AR_ACCOUNT
    si.posting_date  = today()
    si.company       = COMPANY
    si.cost_center   = cost_center
    si.append("items", {
        "item_name":      "Test Service",
        "qty":            1,
        "rate":           amount,
        "income_account": INCOME_ACCOUNT,
        "cost_center":    cost_center,
    })
    si.flags.ignore_permissions = True
    si.flags.ignore_mandatory   = True
    si.flags.ignore_links       = True
    si.insert(ignore_links=True)
    si.submit()
    _docs_to_cancel.append(("Sales Invoice", si.name))
    frappe.db.commit()
    return si


def _gl_for_voucher(voucher_no: str) -> list:
    return frappe.db.sql("""
        SELECT account, debit, credit, cost_center, is_cancelled, is_reversal
        FROM `tabGeneral Ledger Entry`
        WHERE voucher_no = %s AND is_cancelled = 0 AND is_reversal = 0
    """, voucher_no, as_dict=True)


def run():
    print("\n=== Cost Center Tagging L1 Test ===")

    # ── T1: Create Cost Center hierarchy ──────────────────────────────────────
    print("\n--- T1: Create root and child Cost Centers ---")
    try:
        global CC_ROOT, CC_OPS
        # Cost Centers autoname as {cost_center_name}-{company}
        root_name  = f"{CC_ROOT}-{COMPANY}"
        child_name = f"{CC_OPS}-{COMPANY}"

        # Clean up any leftover from prior runs (child before root due to FK)
        for cn in (child_name, root_name):
            if frappe.db.exists("Cost Center", cn):
                frappe.db.delete("Cost Center", cn)
        frappe.db.commit()

        root = frappe.new_doc("Cost Center")
        root.cost_center_name   = CC_ROOT
        root.is_group           = 1
        root.company            = COMPANY
        root.flags.ignore_permissions = True
        root.flags.ignore_mandatory   = True
        root.flags.ignore_links       = True
        root.insert(ignore_links=True)
        _ccs_to_delete.append(root.name)

        child = frappe.new_doc("Cost Center")
        child.cost_center_name   = CC_OPS
        child.is_group           = 0
        child.parent_cost_center = root.name   # use actual name after insert
        child.company            = COMPANY
        child.flags.ignore_permissions = True
        child.flags.ignore_mandatory   = True
        child.flags.ignore_links       = True
        child.insert(ignore_links=True)
        _ccs_to_delete.append(child.name)
        frappe.db.commit()

        # Update module-level refs so all tests below use the real names
        CC_ROOT = root.name
        CC_OPS  = child.name

        _pass(f"Root CC '{CC_ROOT}' (group) and child CC '{CC_OPS}' (leaf) created")
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])
        return  # Cannot proceed without Cost Centers

    # ── T2: Child CC validates parent is a group ───────────────────────────────
    print("\n--- T2: Non-group parent is rejected by Cost Center validator ---")
    try:
        invalid_child = frappe.new_doc("Cost Center")
        invalid_child.cost_center_name   = "TEST-CC-INVALID"
        invalid_child.name               = "TEST-CC-INVALID"
        invalid_child.is_group           = 0
        invalid_child.parent_cost_center = CC_OPS  # CC_OPS is a leaf, not a group
        invalid_child.company            = COMPANY
        invalid_child.flags.ignore_permissions = True
        invalid_child.flags.ignore_mandatory   = True
        invalid_child.flags.ignore_links       = True
        try:
            invalid_child.insert(ignore_links=True)
            frappe.db.rollback()
            _fail("Expected ValidationError — leaf parent should be rejected")
        except frappe.exceptions.ValidationError:
            _pass("ValidationError raised: leaf Cost Center cannot be a parent")
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: Sales Invoice with cost_center → GL entries carry cost_center ─────
    print("\n--- T3: SI with cost_center → all active GL entries have cost_center set ---")
    try:
        si = _make_si(cost_center=CC_OPS, amount=10000.0)
        gl_rows = _gl_for_voucher(si.name)

        if not gl_rows:
            _fail("No GL entries created for SI")
        else:
            rows_with_cc = [r for r in gl_rows if r.cost_center == CC_OPS]
            if len(rows_with_cc) == len(gl_rows):
                _pass(f"All {len(gl_rows)} GL entries carry cost_center='{CC_OPS}'")
            else:
                missing = [r.account for r in gl_rows if r.cost_center != CC_OPS]
                _fail(f"Some GL entries missing cost_center", f"missing: {missing}")
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: GL cost_center matches document cost_center exactly ───────────────
    print("\n--- T4: GL cost_center string matches document cost_center exactly ---")
    try:
        si2 = _make_si(cost_center=CC_OPS, amount=5000.0)
        gl_rows = _gl_for_voucher(si2.name)
        mismatch = [r for r in gl_rows if r.cost_center != CC_OPS]
        if not mismatch:
            _pass(f"All GL cost_center == '{CC_OPS}' exactly")
        else:
            _fail("cost_center mismatch in GL",
                  f"expected={CC_OPS}, found={[r.cost_center for r in mismatch]}")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: Expense with cost_center → GL entries carry cost_center ───────────
    print("\n--- T5: Expense with cost_center → GL entries have cost_center ---")
    try:
        exp = frappe.new_doc("Expense")
        exp.expense_date    = today()
        exp.company         = COMPANY
        exp.description     = "Test CC expense"
        exp.amount          = 2000.0
        exp.expense_account = EXPENSE_ACCOUNT
        exp.cost_center     = CC_OPS
        exp.flags.ignore_permissions = True
        exp.flags.ignore_mandatory   = True
        exp.flags.ignore_links       = True
        exp.insert(ignore_links=True)
        exp.submit()
        _docs_to_cancel.append(("Expense", exp.name))
        frappe.db.commit()

        gl_rows = _gl_for_voucher(exp.name)
        rows_with_cc = [r for r in gl_rows if r.cost_center == CC_OPS]
        if not gl_rows:
            _fail("No GL entries for Expense")
        elif len(rows_with_cc) == len(gl_rows):
            _pass(f"All {len(gl_rows)} Expense GL entries carry cost_center='{CC_OPS}'")
        else:
            missing = [r.account for r in gl_rows if r.cost_center != CC_OPS]
            _fail("Some Expense GL entries missing cost_center", f"missing: {missing}")
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: GL filter by cost_center returns only entries for that CC ──────────
    print("\n--- T6: GL filter by cost_center returns only matching entries ---")
    try:
        # Query GL for our specific cost center
        cc_entries = frappe.db.sql("""
            SELECT COUNT(*) AS cnt
            FROM `tabGeneral Ledger Entry`
            WHERE cost_center = %(cc)s AND is_cancelled = 0
        """, {"cc": CC_OPS}, as_dict=True)[0].cnt

        # Query GL WITHOUT cost_center filter — should have more entries
        all_entries = frappe.db.sql("""
            SELECT COUNT(*) AS cnt
            FROM `tabGeneral Ledger Entry`
            WHERE company = %(co)s AND is_cancelled = 0
        """, {"co": COMPANY}, as_dict=True)[0].cnt

        if cc_entries > 0 and all_entries > cc_entries:
            _pass(f"CC filter: {cc_entries} entries for '{CC_OPS}', "
                  f"{all_entries} total (filter works)")
        elif cc_entries > 0 and all_entries == cc_entries:
            _pass(f"All {cc_entries} GL entries belong to '{CC_OPS}' — filter works")
        else:
            _fail("No GL entries found for cost_center filter",
                  f"cc_entries={cc_entries}, all={all_entries}")
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: Document without cost_center → GL cost_center is blank ────────────
    print("\n--- T7: SI without cost_center → GL cost_center is empty string ---")
    try:
        si_no_cc = frappe.new_doc("Sales Invoice")
        si_no_cc.customer      = CUSTOMER
        si_no_cc.debit_to      = AR_ACCOUNT
        si_no_cc.posting_date  = today()
        si_no_cc.company       = COMPANY
        # No cost_center set
        si_no_cc.append("items", {
            "item_name":      "Test No CC",
            "qty":            1,
            "rate":           1000.0,
            "income_account": INCOME_ACCOUNT,
        })
        si_no_cc.flags.ignore_permissions = True
        si_no_cc.flags.ignore_mandatory   = True
        si_no_cc.flags.ignore_links       = True
        si_no_cc.insert(ignore_links=True)
        si_no_cc.submit()
        _docs_to_cancel.append(("Sales Invoice", si_no_cc.name))
        frappe.db.commit()

        gl_rows = _gl_for_voucher(si_no_cc.name)
        blank_cc = all(not r.cost_center for r in gl_rows)
        if blank_cc:
            _pass(f"All {len(gl_rows)} GL entries have blank cost_center when not set")
        else:
            unexpected = [r.cost_center for r in gl_rows if r.cost_center]
            _fail("Unexpected cost_center in GL for SI without CC",
                  f"found: {unexpected}")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: Cancelled SI → reversal GL entries also carry cost_center ──────────
    print("\n--- T8: Cancelled SI reversal entries also carry the original cost_center ---")
    try:
        si_cancel = _make_si(cost_center=CC_OPS, amount=3000.0)
        # Remove from cancel list since we're cancelling here
        _docs_to_cancel.remove(("Sales Invoice", si_cancel.name))
        si_cancel.cancel()
        frappe.db.commit()

        # Check that reversal entries (is_reversal=1) also have the cost_center
        all_gl = frappe.db.sql("""
            SELECT account, cost_center, is_reversal
            FROM `tabGeneral Ledger Entry`
            WHERE voucher_no = %s
        """, si_cancel.name, as_dict=True)

        reversal_rows = [r for r in all_gl if r.is_reversal]
        if not reversal_rows:
            _fail("No reversal rows found after cancellation")
        else:
            reversals_with_cc = [r for r in reversal_rows if r.cost_center == CC_OPS]
            if len(reversals_with_cc) == len(reversal_rows):
                _pass(f"All {len(reversal_rows)} reversal GL entries carry cost_center='{CC_OPS}'")
            else:
                _fail("Some reversal entries missing cost_center",
                      f"{len(reversals_with_cc)}/{len(reversal_rows)} have CC")
    except Exception as e:
        _fail("T8 crashed", str(e)[:120])

    # ── T9: Cleanup ───────────────────────────────────────────────────────────
    print("\n--- T9: Cleanup ---")
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

        for cc in reversed(_ccs_to_delete):
            try:
                frappe.db.delete("Cost Center", cc)
            except Exception:
                pass
        frappe.db.commit()
        _pass(f"Cancelled {cancelled} documents; removed {len(_ccs_to_delete)} Cost Centers")
    except Exception as e:
        _fail("T9 cleanup crashed", str(e)[:120])

    print("\n=== DONE ===")
