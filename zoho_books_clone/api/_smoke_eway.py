def run():
    from zoho_books_clone.api.eway import (
        generate_eway_bill, get_eway_bill, get_eway_json,
        update_vehicle, extend_validity, cancel_eway_bill,
        get_pending_invoices, get_eway_bills,
    )
    pend = get_pending_invoices(limit=1)
    if not pend:
        return {"err": "no pending invoices"}
    inv = pend[0]['name']
    res = generate_eway_bill(inv, "BlueDart Express", "MH12 AB 1234", 350)
    name = res['name']
    d = get_eway_bill(name)
    j = get_eway_json(name)
    u = update_vehicle(name, "DL1AB9999", "VRL")
    e = extend_validity(name, 2)
    c = cancel_eway_bill(name)
    return {
        "generated": res, "detail_ui_status": d['ui_status'], "days_left": d['days_left'],
        "json_chars": len(j['content']), "filename": j['filename'],
        "updated_vehicle": u['vehicle_no'], "extended_to": e['valid_upto'], "cancelled": c['message'],
    }
