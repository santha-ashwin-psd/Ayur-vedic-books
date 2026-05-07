"""
L1 — E-Way Bill test.

E-Way Bill is a data-entry doctype (no GL posting, no business logic beyond
naming). Tests confirm: doctype fields exist, naming series works, required
data round-trips correctly, and status updates persist.

  T1  All expected fields present on E-Way Bill doctype
  T2  Create EWB with required fields — naming series EWB-.YYYY.-
  T3  Data round-trip: all saved fields match what was set
  T4  EWB can be linked to a Sales Invoice number (invoice_no field)
  T5  Status field persists after update
  T6  valid_upto date stored as a date field
  T7  grand_total stored as a numeric field (not string)
  T8  Cleanup: delete test records
"""
import frappe
from frappe.utils import flt, today, add_days

COMPANY = "Eiffele gaming"

_test_ewbs = []

REQUIRED_FIELDS = [
    "customer", "invoice_no", "invoice_date", "valid_upto",
    "ewb_no", "status", "grand_total", "company",
]


def _pass(label): print(f"  ✓ {label}")
def _fail(label, detail=""): print(f"  ✗ {label}" + (f"  [{detail}]" if detail else ""))


def _make_ewb(**kwargs) -> object:
    ewb = frappe.new_doc("E Way Bill")
    ewb.naming_series  = "EWB-.YYYY.-"
    ewb.customer       = kwargs.get("customer", "Test Customer")
    ewb.customer_name  = kwargs.get("customer_name", "Test Customer")
    ewb.invoice_no     = kwargs.get("invoice_no", "INV-TEST-001")
    ewb.invoice_date   = kwargs.get("invoice_date", today())
    ewb.valid_upto     = kwargs.get("valid_upto", str(add_days(today(), 3)))
    ewb.ewb_no         = kwargs.get("ewb_no", "EWB123456789012")
    ewb.status         = kwargs.get("status", "Generated")
    ewb.grand_total    = kwargs.get("grand_total", 50000.0)
    ewb.company        = COMPANY
    ewb.transporter    = kwargs.get("transporter", "Fast Freight")
    ewb.vehicle_no     = kwargs.get("vehicle_no", "MH01AB1234")
    ewb.supply_type    = kwargs.get("supply_type", "Outward")
    ewb.from_gstin     = kwargs.get("from_gstin", "27AAAAA0000A1Z5")
    ewb.to_gstin       = kwargs.get("to_gstin", "33BBBBB0000B1Z4")
    ewb.flags.ignore_permissions = True
    ewb.flags.ignore_mandatory   = True
    ewb.flags.ignore_links       = True
    ewb.insert(ignore_links=True)
    _test_ewbs.append(ewb.name)
    frappe.db.commit()
    return ewb


def run():
    print("\n=== E-Way Bill L1 Test ===")

    # ── T1: All expected fields present ──────────────────────────────────────
    print("\n--- T1: E-Way Bill doctype has all expected fields ---")
    try:
        meta = frappe.get_meta("E Way Bill")
        field_names = {f.fieldname for f in meta.fields}
        missing = [f for f in REQUIRED_FIELDS if f not in field_names]
        if not missing:
            _pass(f"All {len(REQUIRED_FIELDS)} required fields present on E Way Bill")
        else:
            _fail("Missing fields on E Way Bill doctype", str(missing))
    except Exception as e:
        _fail("T1 crashed", str(e)[:120])

    # ── T2: Create EWB — naming series EWB-.YYYY.- ────────────────────────────
    print("\n--- T2: Create EWB and verify naming series (EWB-.YYYY.-) ---")
    try:
        ewb = _make_ewb()
        if ewb.name and ewb.name.startswith("EWB-"):
            _pass(f"EWB created with naming series: {ewb.name}")
        else:
            _fail("Naming series wrong or not applied", f"name={ewb.name}")
    except Exception as e:
        _fail("T2 crashed", str(e)[:120])

    # ── T3: Data round-trip ───────────────────────────────────────────────────
    print("\n--- T3: Data round-trip — all fields match after save ---")
    try:
        ewb = _make_ewb(
            customer="CUST-TEST-ROUNDTRIP",
            invoice_no="INV-2026-99999",
            ewb_no="EWB999000888777",
            grand_total=75000.0,
            vehicle_no="KA05XY9876",
        )
        saved = frappe.db.get_value("E Way Bill", ewb.name, [
            "customer", "invoice_no", "ewb_no", "grand_total", "vehicle_no"
        ], as_dict=True)
        checks = [
            ("customer",   "CUST-TEST-ROUNDTRIP"),
            ("invoice_no", "INV-2026-99999"),
            ("ewb_no",     "EWB999000888777"),
            ("vehicle_no", "KA05XY9876"),
        ]
        errors = []
        for field, expected in checks:
            actual = saved.get(field)
            if actual != expected:
                errors.append(f"{field}: expected={expected!r}, got={actual!r}")
        if not errors:
            _pass(f"All fields round-trip correctly for {ewb.name}")
        else:
            for e in errors:
                _fail("Field mismatch", e)
    except Exception as e:
        _fail("T3 crashed", str(e)[:120])

    # ── T4: EWB linked to SI via invoice_no field ─────────────────────────────
    print("\n--- T4: invoice_no field stores Sales Invoice reference ---")
    try:
        si_name = "INV-2026-00023"  # existing submitted SI
        ewb = _make_ewb(invoice_no=si_name, grand_total=1000.0)
        stored = frappe.db.get_value("E Way Bill", ewb.name, "invoice_no")
        if stored == si_name:
            _pass(f"invoice_no stored correctly: {stored}")
        else:
            _fail("invoice_no mismatch", f"expected={si_name}, got={stored}")
    except Exception as e:
        _fail("T4 crashed", str(e)[:120])

    # ── T5: Status update persists ────────────────────────────────────────────
    print("\n--- T5: Status field persists after update ---")
    try:
        ewb = _make_ewb(status="Generated")
        frappe.db.set_value("E Way Bill", ewb.name, "status", "Cancelled")
        frappe.db.commit()
        refreshed = frappe.db.get_value("E Way Bill", ewb.name, "status")
        if refreshed == "Cancelled":
            _pass("Status updated to 'Cancelled' and persisted")
        else:
            _fail("Status not persisted", f"got={refreshed}")
    except Exception as e:
        _fail("T5 crashed", str(e)[:120])

    # ── T6: valid_upto stored as date ─────────────────────────────────────────
    print("\n--- T6: valid_upto stored as a date ---")
    try:
        target_date = str(add_days(today(), 5))
        ewb = _make_ewb(valid_upto=target_date)
        stored = str(frappe.db.get_value("E Way Bill", ewb.name, "valid_upto"))
        if stored == target_date:
            _pass(f"valid_upto stored correctly as date: {stored}")
        else:
            _fail("valid_upto mismatch", f"expected={target_date}, got={stored}")
    except Exception as e:
        _fail("T6 crashed", str(e)[:120])

    # ── T7: grand_total stored as numeric ─────────────────────────────────────
    print("\n--- T7: grand_total stored as numeric (float), not string ---")
    try:
        ewb = _make_ewb(grand_total=123456.78)
        stored = frappe.db.get_value("E Way Bill", ewb.name, "grand_total")
        if isinstance(stored, (int, float)) and abs(flt(stored) - 123456.78) < 0.01:
            _pass(f"grand_total stored as numeric: {flt(stored):.2f}")
        else:
            _fail("grand_total not numeric or wrong value",
                  f"type={type(stored).__name__}, value={stored}")
    except Exception as e:
        _fail("T7 crashed", str(e)[:120])

    # ── T8: Cleanup ───────────────────────────────────────────────────────────
    print("\n--- T8: Cleanup ---")
    try:
        for name in _test_ewbs:
            frappe.db.delete("E Way Bill", name)
        frappe.db.commit()
        _pass(f"Deleted {len(_test_ewbs)} E Way Bill records")
    except Exception as e:
        _fail("T8 cleanup crashed", str(e)[:120])

    print("\n=== DONE ===")
