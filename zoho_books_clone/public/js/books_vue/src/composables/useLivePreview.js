// Shared print-template renderer — Classic / Modern / Minimal.
// All pages reuse these three templates by calling printDoc(doc, config).

import { reactive, computed } from "vue";

const _state = reactive({
  template: "classic",
  brandColor: "#1a6ef7",
  logo: "",
  company: "",
});

function _loadBranding(company) {
  if (!company) return;
  try {
    const raw = localStorage.getItem("books_branding_" + company);
    if (raw) {
      const b = JSON.parse(raw);
      _state.template   = b.template   || "classic";
      _state.brandColor = b.brandColor || "#1a6ef7";
      _state.logo       = b.logo       || "";
    } else {
      _state.template   = "classic";
      _state.brandColor = "#1a6ef7";
      _state.logo       = "";
    }
  } catch {}
  _state.company = company;
}

function _saveBranding() {
  if (!_state.company) return;
  localStorage.setItem("books_branding_" + _state.company, JSON.stringify({
    template:   _state.template,
    brandColor: _state.brandColor,
    logo:       _state.logo,
  }));
}

function _esc(s) {
  return String(s ?? "").replace(/[&<>"']/g,
    c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}
function _fmt(v, currency) {
  const symbol = (currency && currency !== "INR") ? (currency + " ") : "₹";
  return symbol + Number(v || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function _today() {
  return new Date().toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
}

// ── CLASSIC ──────────────────────────────────────────────────────────────────
function _renderClassic(doc, cfg) {
  const brand    = _state.brandColor;
  const logo     = _state.logo;
  const currency = doc.currency || "INR";
  const netTotal = doc.net_total != null ? doc.net_total
    : (doc.grand_total || 0) - (doc.total_taxes_and_charges || 0);

  const items = (doc.items || []).map((it, i) => `
    <tr>
      <td class="num-cell">${i + 1}</td>
      <td>
        <span class="it-name">${_esc(it.item_name || it.item_code)}</span>
        ${it.item_code && it.item_name && it.item_code !== it.item_name
          ? `<div class="it-code">${_esc(it.item_code)}</div>` : ""}
        ${it.description && it.description !== it.item_name
          ? `<div class="it-desc">${_esc(it.description)}</div>` : ""}
      </td>
      ${cfg.includeHsn ? `<td class="tc">${_esc(it.gst_hsn_code || it.hsn_code || "—")}</td>` : ""}
      <td class="tr">${Number(it.qty || 0)}</td>
      <td class="tc">${_esc(it.uom || "Nos")}</td>
      <td class="tr">${_fmt(it.rate, currency)}</td>
      ${cfg.includeDiscount ? `<td class="tc">${Number(it.discount_percentage || 0)}%</td>` : ""}
      <td class="tr bld">${_fmt(it.amount, currency)}</td>
    </tr>`).join("");

  const taxRows = (doc.taxes || []).map(t =>
    `<tr><td class="tl">${_esc(t.description || t.account_head)}</td>
         <td class="tr mono">${_fmt(t.tax_amount || 0, currency)}</td></tr>`
  ).join("");

  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<title>${_esc(cfg.title)} — ${_esc(doc.name)}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',system-ui,-apple-system,sans-serif;color:#1e293b;background:#fff;font-size:12.5px;line-height:1.5}
  .page{padding:44px 52px;max-width:920px;margin:0 auto}

  /* ─ Header ─ */
  .hdr{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:20px;border-bottom:3.5px solid ${brand};margin-bottom:26px}
  .co-logo{max-height:54px;max-width:160px;object-fit:contain;display:block;margin-bottom:8px}
  .co-name{font-size:24px;font-weight:800;color:${brand};line-height:1.1;letter-spacing:-.01em}
  .co-gst{font-size:10.5px;color:#64748b;margin-top:3px}
  .doc-chip{display:inline-block;background:${brand};color:#fff;padding:4px 13px;border-radius:999px;font-size:10.5px;font-weight:700;letter-spacing:.06em;margin-bottom:8px}
  .doc-num{font-size:26px;font-weight:800;color:#0f172a;line-height:1}
  .doc-status{margin-top:5px;font-size:11px;color:#64748b}
  .doc-status strong{color:#0f172a}

  /* ─ Meta grid ─ */
  .meta{display:grid;grid-template-columns:2.2fr 1fr 1fr;border:1px solid #e8edf2;border-radius:8px;overflow:hidden;margin-bottom:20px}
  .mc{padding:13px 16px;border-right:1px solid #e8edf2}
  .mc:last-child{border-right:none}
  .ml{font-size:9.5px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px}
  .mv{font-weight:600;color:#0f172a;font-size:13px}
  .ms{font-size:11px;color:#64748b;margin-top:2px;white-space:pre-line;line-height:1.4}
  .mr{margin-top:10px}

  /* ─ Ship-to banner ─ */
  .ship-box{background:#f8fafc;border:1px solid #e8edf2;border-radius:6px;padding:10px 14px;margin-bottom:16px;font-size:12px}
  .ship-box .ml{margin-bottom:3px}

  /* ─ Section label ─ */
  .sec-lbl{font-size:9.5px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em;margin:18px 0 8px}

  /* ─ Items table ─ */
  .items-tbl{width:100%;border-collapse:collapse;font-size:12px}
  .items-tbl thead th{background:#f1f5f9;padding:9px 10px;font-size:10px;font-weight:700;color:#475569;text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid #cbd5e1;white-space:nowrap}
  .items-tbl tbody td{padding:10px 10px;border-bottom:1px solid #f1f5f9;vertical-align:top}
  .items-tbl tbody tr:last-child td{border-bottom:none}
  .it-name{font-weight:600;color:#0f172a}
  .it-code{font-size:10.5px;color:#94a3b8;margin-top:1px}
  .it-desc{font-size:11px;color:#64748b;margin-top:2px;line-height:1.4}
  .num-cell{color:#94a3b8;font-size:11px;text-align:center}
  .tc{text-align:center}.tr{text-align:right}.tl{text-align:left}
  .bld{font-weight:700;font-variant-numeric:tabular-nums}
  .mono{font-variant-numeric:tabular-nums}

  /* ─ Totals ─ */
  .totals-wrap{display:flex;justify-content:flex-end;margin-top:10px;padding-top:10px;border-top:2px solid #e2e8f0}
  .totals-tbl{width:300px;border-collapse:collapse}
  .totals-tbl td{padding:5px 0;font-size:12.5px}
  .totals-tbl .tl{color:#475569}
  .totals-tbl .tr{font-variant-numeric:tabular-nums}
  .t-divider td{border-top:1px dashed #e5e7eb;padding-top:8px!important}
  .totals-tbl .grand td{border-top:2.5px solid ${brand};padding-top:10px!important;font-weight:800;font-size:15px;color:${brand}}

  /* ─ Remarks / Terms ─ */
  .bottom-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:24px}
  .bx{background:#f8fafc;border:1px solid #e8edf2;border-radius:8px;padding:14px 16px;font-size:12px;color:#374151;line-height:1.6}
  .bx-ttl{font-weight:700;color:#0f172a;margin-bottom:6px;font-size:10.5px;text-transform:uppercase;letter-spacing:.04em}

  /* ─ Signature ─ */
  .sig-row{display:flex;gap:20px;margin-top:32px}
  .sig-box{flex:1;border-top:1.5px solid #e5e7eb;padding-top:8px;font-size:10.5px;color:#94a3b8;text-align:center}

  /* ─ Footer ─ */
  .foot{margin-top:24px;padding-top:12px;border-top:1px solid #f1f5f9;display:flex;justify-content:space-between;font-size:10.5px;color:#94a3b8}

  @media print{body{background:#fff}.page{padding:28px 36px}}
</style></head><body><div class="page">

<!-- Header -->
<div class="hdr">
  <div>
    ${logo ? `<img src="${_esc(logo)}" class="co-logo"/>` : ""}
    <div class="co-name">${_esc(doc.company || cfg.companyName || "")}</div>
    ${doc.company_gstin || doc.gstin ? `<div class="co-gst">GSTIN: ${_esc(doc.company_gstin || doc.gstin)}</div>` : ""}
  </div>
  <div style="text-align:right">
    <div class="doc-chip">${_esc(cfg.title)}</div>
    <div class="doc-num">${_esc(doc.name || "")}</div>
    ${doc.status ? `<div class="doc-status">Status: <strong>${_esc(doc.status)}</strong></div>` : ""}
  </div>
</div>

<!-- Meta -->
<div class="meta">
  <div class="mc">
    <div class="ml">${_esc(cfg.partyLabel)}</div>
    <div class="mv">${_esc(doc[cfg.partyField] || doc.customer || doc.supplier || "")}</div>
    ${doc.address_display ? `<div class="ms">${_esc(doc.address_display)}</div>` : ""}
    ${doc.contact_display ? `<div style="font-size:11px;color:#64748b;margin-top:3px">${_esc(doc.contact_display)}</div>` : ""}
    ${doc.customer_gstin || doc.supplier_gstin ? `<div style="font-size:10.5px;color:#64748b;margin-top:3px">GSTIN: ${_esc(doc.customer_gstin || doc.supplier_gstin)}</div>` : ""}
  </div>
  <div class="mc">
    <div class="ml">Date</div>
    <div class="mv">${_esc(doc.posting_date || doc.transaction_date || "")}</div>
    ${doc.due_date ? `<div class="mr"><div class="ml">Due Date</div><div class="mv">${_esc(doc.due_date)}</div></div>` : ""}
    ${doc.valid_till ? `<div class="mr"><div class="ml">Valid Till</div><div class="mv">${_esc(doc.valid_till)}</div></div>` : ""}
    ${doc.delivery_date ? `<div class="mr"><div class="ml">Delivery Date</div><div class="mv">${_esc(doc.delivery_date)}</div></div>` : ""}
  </div>
  <div class="mc">
    ${doc.po_no ? `<div class="ml">PO Number</div><div class="mv">${_esc(doc.po_no)}</div>` : ""}
    ${doc.payment_terms_template ? `<div class="mr"><div class="ml">Payment Terms</div><div class="mv">${_esc(doc.payment_terms_template)}</div></div>` : ""}
    ${doc.place_of_supply ? `<div class="mr"><div class="ml">Place of Supply</div><div class="mv">${_esc(doc.place_of_supply)}</div></div>` : ""}
    ${doc.currency && doc.currency !== "INR" ? `<div class="mr"><div class="ml">Currency</div><div class="mv">${_esc(doc.currency)}</div></div>` : ""}
    ${!doc.po_no && !doc.payment_terms_template && !doc.place_of_supply ? `<div class="ml">Reference</div><div class="mv">—</div>` : ""}
  </div>
</div>

${doc.shipping_address ? `
<div class="ship-box">
  <div class="ml">Ship To</div>
  <div style="color:#334155;font-size:12px;white-space:pre-line">${_esc(doc.shipping_address)}</div>
</div>` : ""}

<!-- Items -->
<div class="sec-lbl">Line Items</div>
<table class="items-tbl">
  <thead>
    <tr>
      <th style="width:28px;text-align:center">#</th>
      <th>Item / Description</th>
      ${cfg.includeHsn ? `<th style="text-align:center;width:76px">HSN/SAC</th>` : ""}
      <th style="text-align:right;width:50px">Qty</th>
      <th style="text-align:center;width:52px">UOM</th>
      <th style="text-align:right;width:110px">Rate</th>
      ${cfg.includeDiscount ? `<th style="text-align:center;width:52px">Disc</th>` : ""}
      <th style="text-align:right;width:110px">Amount</th>
    </tr>
  </thead>
  <tbody>
    ${items || `<tr><td colspan="8" style="text-align:center;color:#9ca3af;padding:28px">No items</td></tr>`}
  </tbody>
</table>

<!-- Totals -->
<div class="totals-wrap">
  <table class="totals-tbl">
    <tr><td class="tl">Subtotal</td><td class="tr mono">${_fmt(netTotal, currency)}</td></tr>
    ${taxRows}
    ${doc.discount_amount ? `<tr><td class="tl" style="color:#dc2626">Discount</td><td class="tr mono" style="color:#dc2626">− ${_fmt(doc.discount_amount, currency)}</td></tr>` : ""}
    <tr class="t-divider"><td colspan="2" style="padding:0"></td></tr>
    <tr class="grand"><td>Grand Total</td><td style="text-align:right">${_fmt(doc.grand_total, currency)}</td></tr>
  </table>
</div>

${(doc.remarks || doc.terms || doc.customer_note) ? `
<div class="bottom-grid">
  ${doc.remarks ? `<div class="bx"><div class="bx-ttl">Remarks</div>${_esc(doc.remarks)}</div>` : "<div></div>"}
  ${doc.terms || doc.customer_note ? `<div class="bx"><div class="bx-ttl">${doc.customer_note ? "Note" : "Terms &amp; Conditions"}</div>${_esc(doc.customer_note || doc.terms)}</div>` : ""}
</div>` : ""}

<!-- Signatures -->
<div class="sig-row">
  <div class="sig-box">Prepared By</div>
  <div class="sig-box">Authorised Signatory<br/><span style="font-size:9.5px">${_esc(doc.company || "")}</span></div>
  <div class="sig-box">Receiver's Signature</div>
</div>

<!-- Footer -->
<div class="foot">
  <span>${_esc(doc.company || cfg.companyName || "")}</span>
  <span>${_esc(doc.name)} · Printed ${_today()}</span>
</div>

</div></body></html>`;
}

// ── MODERN ───────────────────────────────────────────────────────────────────
function _renderModern(doc, cfg) {
  const brand    = _state.brandColor;
  const logo     = _state.logo;
  const currency = doc.currency || "INR";
  const netTotal = doc.net_total != null ? doc.net_total
    : (doc.grand_total || 0) - (doc.total_taxes_and_charges || 0);

  // Derive a slightly darker shade for gradients
  const brandDark = brand;

  const items = (doc.items || []).map((it, i) => `
    <tr>
      <td class="num-c">${i + 1}</td>
      <td>
        <div class="it-n">${_esc(it.item_name || it.item_code)}</div>
        ${it.item_code && it.item_name && it.item_code !== it.item_name
          ? `<div class="it-c">${_esc(it.item_code)}</div>` : ""}
        ${it.description && it.description !== it.item_name
          ? `<div class="it-d">${_esc(it.description)}</div>` : ""}
      </td>
      ${cfg.includeHsn ? `<td class="tc muted">${_esc(it.gst_hsn_code || it.hsn_code || "—")}</td>` : ""}
      <td class="tr">${Number(it.qty || 0)} <span class="muted" style="font-size:10px">${_esc(it.uom || "Nos")}</span></td>
      <td class="tr">${_fmt(it.rate, currency)}</td>
      ${cfg.includeDiscount ? `<td class="tc muted">${Number(it.discount_percentage || 0)}%</td>` : ""}
      <td class="tr bld accent">${_fmt(it.amount, currency)}</td>
    </tr>`).join("");

  const taxRows = (doc.taxes || []).map(t =>
    `<tr><td colspan="2" class="tl muted">${_esc(t.description || t.account_head)}</td>
         <td class="tr" colspan="1">${_fmt(t.tax_amount || 0, currency)}</td></tr>`
  ).join("");

  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<title>${_esc(cfg.title)} — ${_esc(doc.name)}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',system-ui,-apple-system,sans-serif;color:#0f172a;background:#fff;font-size:12.5px;line-height:1.5}
  .page{padding:0;max-width:920px;margin:0 auto}

  /* ─ Top band ─ */
  .top-band{background:${brand};color:#fff;padding:32px 48px 28px;display:flex;justify-content:space-between;align-items:flex-end}
  .co-logo{max-height:46px;max-width:140px;object-fit:contain;display:block;margin-bottom:8px;filter:brightness(0) invert(1)}
  .co-name{font-size:20px;font-weight:800;letter-spacing:-.01em;line-height:1}
  .co-sub{font-size:11px;opacity:.75;margin-top:4px}
  .doc-type{font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;opacity:.8;margin-bottom:4px}
  .doc-num{font-size:28px;font-weight:800;line-height:1;letter-spacing:-.02em}
  .doc-meta{font-size:11px;opacity:.8;margin-top:6px}

  /* ─ Body ─ */
  .body{padding:28px 48px 40px}

  /* ─ Info strip ─ */
  .info-strip{display:grid;grid-template-columns:2fr 1.2fr 1.2fr;gap:0;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;margin-bottom:24px}
  .ic{padding:14px 18px;border-right:1px solid #e2e8f0}
  .ic:last-child{border-right:none}
  .il{font-size:9.5px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em;margin-bottom:3px}
  .iv{font-weight:600;color:#0f172a;font-size:13px}
  .is{font-size:11px;color:#64748b;margin-top:2px;white-space:pre-line;line-height:1.4}
  .irow{margin-top:10px}

  /* ─ Ship ─ */
  .ship{background:#f0f9ff;border:1px solid #bae6fd;border-radius:8px;padding:11px 14px;margin-bottom:18px;font-size:12px;color:#0369a1}
  .ship .il{color:#0284c7;margin-bottom:3px}

  /* ─ Items table ─ */
  .sec{font-size:9.5px;font-weight:700;color:#94a3b8;text-transform:uppercase;letter-spacing:.07em;margin:0 0 10px}
  table{width:100%;border-collapse:collapse;font-size:12.5px}
  thead th{padding:10px 12px;font-size:10px;font-weight:700;color:#64748b;text-transform:uppercase;letter-spacing:.04em;border-bottom:2px solid #e2e8f0;text-align:left;background:transparent}
  tbody td{padding:12px 12px;border-bottom:1px solid #f1f5f9;vertical-align:top}
  tbody tr:last-child td{border-bottom:none}
  .num-c{color:#94a3b8;font-size:11px;text-align:center;width:28px}
  .it-n{font-weight:600;color:#0f172a}
  .it-c{font-size:10.5px;color:#94a3b8;margin-top:1px}
  .it-d{font-size:11px;color:#64748b;margin-top:2px}
  .tc{text-align:center}.tr{text-align:right}.tl{text-align:left}
  .bld{font-weight:700;font-variant-numeric:tabular-nums}
  .accent{color:${brand}}
  .muted{color:#64748b}

  /* ─ Totals panel ─ */
  .totals-wrap{display:flex;justify-content:flex-end;margin-top:14px}
  .totals-panel{width:300px;background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;overflow:hidden}
  .tp-row{display:flex;justify-content:space-between;padding:9px 16px;border-bottom:1px solid #e2e8f0;font-size:12.5px}
  .tp-row:last-child{border-bottom:none}
  .tp-lbl{color:#475569}
  .tp-val{font-variant-numeric:tabular-nums;font-weight:500}
  .tp-grand{background:${brand};color:#fff;font-weight:800;font-size:15px}
  .tp-grand .tp-lbl,.tp-grand .tp-val{color:#fff}

  /* ─ Bottom ─ */
  .bottom{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-top:24px}
  .bx{border:1px solid #e2e8f0;border-radius:8px;padding:14px 16px;font-size:12px;color:#374151;line-height:1.6}
  .bx-ttl{font-weight:700;font-size:10px;text-transform:uppercase;letter-spacing:.05em;color:#94a3b8;margin-bottom:6px}

  /* ─ Sig ─ */
  .sig-row{display:flex;gap:20px;margin-top:28px}
  .sig-box{flex:1;border-top:1.5px solid #e5e7eb;padding-top:8px;font-size:10.5px;color:#94a3b8;text-align:center}

  /* ─ Footer ─ */
  .foot{margin-top:20px;display:flex;justify-content:space-between;font-size:10.5px;color:#94a3b8;padding-top:12px;border-top:1px solid #f1f5f9}

  @media print{body{background:#fff}.body{padding:20px 36px}}
</style></head><body><div class="page">

<!-- Top band -->
<div class="top-band">
  <div>
    ${logo ? `<img src="${_esc(logo)}" class="co-logo"/>` : ""}
    <div class="co-name">${_esc(doc.company || cfg.companyName || "")}</div>
    ${doc.company_gstin || doc.gstin ? `<div class="co-sub">GSTIN: ${_esc(doc.company_gstin || doc.gstin)}</div>` : ""}
  </div>
  <div style="text-align:right">
    <div class="doc-type">${_esc(cfg.title)}</div>
    <div class="doc-num">${_esc(doc.name || "")}</div>
    <div class="doc-meta">${_esc(doc.posting_date || doc.transaction_date || "")}
      ${doc.status ? ` · ${_esc(doc.status)}` : ""}
    </div>
  </div>
</div>

<div class="body">

<!-- Info strip -->
<div class="info-strip">
  <div class="ic">
    <div class="il">${_esc(cfg.partyLabel)}</div>
    <div class="iv">${_esc(doc[cfg.partyField] || doc.customer || doc.supplier || "")}</div>
    ${doc.address_display ? `<div class="is">${_esc(doc.address_display)}</div>` : ""}
    ${doc.contact_display ? `<div style="font-size:11px;color:#64748b;margin-top:3px">${_esc(doc.contact_display)}</div>` : ""}
    ${doc.customer_gstin || doc.supplier_gstin ? `<div style="font-size:10.5px;color:#64748b;margin-top:3px">GSTIN: ${_esc(doc.customer_gstin || doc.supplier_gstin)}</div>` : ""}
  </div>
  <div class="ic">
    <div class="il">Date</div>
    <div class="iv">${_esc(doc.posting_date || doc.transaction_date || "")}</div>
    ${doc.due_date ? `<div class="irow"><div class="il">Due Date</div><div class="iv">${_esc(doc.due_date)}</div></div>` : ""}
    ${doc.valid_till ? `<div class="irow"><div class="il">Valid Till</div><div class="iv">${_esc(doc.valid_till)}</div></div>` : ""}
    ${doc.delivery_date ? `<div class="irow"><div class="il">Delivery Date</div><div class="iv">${_esc(doc.delivery_date)}</div></div>` : ""}
  </div>
  <div class="ic">
    ${doc.po_no ? `<div class="il">PO Number</div><div class="iv">${_esc(doc.po_no)}</div>` : ""}
    ${doc.payment_terms_template ? `<div class="irow"><div class="il">Payment Terms</div><div class="iv">${_esc(doc.payment_terms_template)}</div></div>` : ""}
    ${doc.place_of_supply ? `<div class="irow"><div class="il">Place of Supply</div><div class="iv">${_esc(doc.place_of_supply)}</div></div>` : ""}
    ${doc.currency && doc.currency !== "INR" ? `<div class="irow"><div class="il">Currency</div><div class="iv">${_esc(doc.currency)}</div></div>` : ""}
    ${!doc.po_no && !doc.payment_terms_template && !doc.place_of_supply ? `<div class="il">Reference</div><div class="iv">—</div>` : ""}
  </div>
</div>

${doc.shipping_address ? `
<div class="ship">
  <div class="il">Ship To</div>
  <div style="font-size:12px;white-space:pre-line">${_esc(doc.shipping_address)}</div>
</div>` : ""}

<!-- Items -->
<div class="sec">Line Items</div>
<table>
  <thead>
    <tr>
      <th style="width:28px;text-align:center">#</th>
      <th>Item</th>
      ${cfg.includeHsn ? `<th style="text-align:center;width:80px">HSN/SAC</th>` : ""}
      <th style="text-align:right;width:90px">Qty</th>
      <th style="text-align:right;width:110px">Rate</th>
      ${cfg.includeDiscount ? `<th style="text-align:center;width:52px">Disc</th>` : ""}
      <th style="text-align:right;width:120px">Amount</th>
    </tr>
  </thead>
  <tbody>
    ${items || `<tr><td colspan="7" style="text-align:center;color:#94a3b8;padding:32px">No items</td></tr>`}
  </tbody>
</table>

<!-- Totals -->
<div class="totals-wrap">
  <div class="totals-panel">
    <div class="tp-row"><span class="tp-lbl">Subtotal</span><span class="tp-val">${_fmt(netTotal, currency)}</span></div>
    ${(doc.taxes || []).map(t =>
      `<div class="tp-row"><span class="tp-lbl">${_esc(t.description || t.account_head)}</span><span class="tp-val">${_fmt(t.tax_amount || 0, currency)}</span></div>`
    ).join("")}
    ${doc.discount_amount ? `<div class="tp-row"><span class="tp-lbl" style="color:#dc2626">Discount</span><span class="tp-val" style="color:#dc2626">− ${_fmt(doc.discount_amount, currency)}</span></div>` : ""}
    <div class="tp-row tp-grand"><span class="tp-lbl">Grand Total</span><span class="tp-val">${_fmt(doc.grand_total, currency)}</span></div>
  </div>
</div>

${(doc.remarks || doc.terms || doc.customer_note) ? `
<div class="bottom">
  ${doc.remarks ? `<div class="bx"><div class="bx-ttl">Remarks</div>${_esc(doc.remarks)}</div>` : "<div></div>"}
  ${doc.terms || doc.customer_note ? `<div class="bx"><div class="bx-ttl">${doc.customer_note ? "Note" : "Terms &amp; Conditions"}</div>${_esc(doc.customer_note || doc.terms)}</div>` : ""}
</div>` : ""}

<!-- Signatures -->
<div class="sig-row">
  <div class="sig-box">Prepared By</div>
  <div class="sig-box">Authorised Signatory<br/><span style="font-size:9.5px">${_esc(doc.company || "")}</span></div>
  <div class="sig-box">Receiver's Signature</div>
</div>

<!-- Footer -->
<div class="foot">
  <span>${_esc(doc.company || cfg.companyName || "")}</span>
  <span>${_esc(doc.name)} · Printed ${_today()}</span>
</div>

</div></div></body></html>`;
}

// ── MINIMAL ──────────────────────────────────────────────────────────────────
function _renderMinimal(doc, cfg) {
  const brand    = _state.brandColor;
  const logo     = _state.logo;
  const currency = doc.currency || "INR";
  const netTotal = doc.net_total != null ? doc.net_total
    : (doc.grand_total || 0) - (doc.total_taxes_and_charges || 0);

  const items = (doc.items || []).map((it, i) => `
    <tr>
      <td>${i + 1}.</td>
      <td>
        <span class="it-n">${_esc(it.item_name || it.item_code)}</span>
        ${it.item_code && it.item_name && it.item_code !== it.item_name
          ? `<div class="it-c">${_esc(it.item_code)}</div>` : ""}
        ${it.description && it.description !== it.item_name
          ? `<div class="it-d">${_esc(it.description)}</div>` : ""}
      </td>
      ${cfg.includeHsn ? `<td class="tc">${_esc(it.gst_hsn_code || it.hsn_code || "—")}</td>` : ""}
      <td class="tr">${Number(it.qty || 0)} ${_esc(it.uom || "Nos")}</td>
      <td class="tr">${_fmt(it.rate, currency)}</td>
      ${cfg.includeDiscount && Number(it.discount_percentage) > 0 ? `<td class="tc">−${Number(it.discount_percentage)}%</td>` : (cfg.includeDiscount ? `<td class="tc">—</td>` : "")}
      <td class="tr bld">${_fmt(it.amount, currency)}</td>
    </tr>`).join("");

  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<title>${_esc(cfg.title)} — ${_esc(doc.name)}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Georgia','Times New Roman',serif;color:#1f2937;background:#fff;font-size:13px;line-height:1.7}
  .page{padding:52px 72px;max-width:860px;margin:0 auto}

  /* ─ Header ─ */
  .co-logo{max-height:50px;max-width:150px;object-fit:contain;display:block;margin:0 auto 10px}
  .co-name{text-align:center;font-size:22px;font-weight:700;color:${brand};letter-spacing:.04em;font-family:'Inter',system-ui,sans-serif;line-height:1.1}
  .co-sub{text-align:center;font-size:11px;color:#9ca3af;margin-top:4px;font-family:'Inter',system-ui,sans-serif}
  .doc-title{text-align:center;font-size:13px;font-weight:400;letter-spacing:.25em;color:#6b7280;text-transform:uppercase;margin:16px 0 4px;font-family:'Inter',system-ui,sans-serif}
  .doc-num{text-align:center;font-size:13px;color:#374151;font-family:'Inter',system-ui,sans-serif;letter-spacing:.05em}
  hr.thick{border:none;border-top:2px solid ${brand};margin:18px 0}
  hr.thin{border:none;border-top:1px solid #e5e7eb;margin:16px 0}

  /* ─ Meta ─ */
  .meta-row{display:flex;justify-content:space-between;gap:24px;font-size:12.5px;margin:16px 0}
  .mc{flex:1}
  .mc.right{text-align:right}
  .ml{font-size:10px;color:#9ca3af;font-style:italic;letter-spacing:.04em;margin-bottom:2px;font-family:'Inter',system-ui,sans-serif}
  .mv{font-weight:700;color:#111827;font-family:'Inter',system-ui,sans-serif}
  .ms{font-size:11.5px;color:#6b7280;margin-top:2px;white-space:pre-line;line-height:1.4;font-family:'Inter',system-ui,sans-serif}
  .meta-extra{display:flex;justify-content:space-between;flex-wrap:wrap;gap:12px;font-size:12px;color:#374151;margin-bottom:4px;font-family:'Inter',system-ui,sans-serif}
  .me-item .ml{font-size:9.5px}

  /* ─ Items table ─ */
  table.items{width:100%;border-collapse:collapse;font-size:12.5px}
  table.items thead th{padding:9px 6px;border-bottom:1.5px solid #374151;font-style:italic;font-weight:400;color:#6b7280;font-size:12px;text-align:left}
  table.items thead th.tr{text-align:right}
  table.items thead th.tc{text-align:center}
  table.items tbody td{padding:10px 6px;border-bottom:1px solid #f3f4f6;vertical-align:top}
  table.items tbody tr:last-child td{border-bottom:none}
  .num-c{color:#9ca3af;font-style:italic;font-size:12px;width:22px}
  .it-n{font-weight:700}
  .it-c{font-size:10.5px;color:#9ca3af;margin-top:1px;font-family:'Inter',system-ui,sans-serif}
  .it-d{font-size:11.5px;color:#6b7280;margin-top:2px;line-height:1.4}
  .tc{text-align:center}.tr{text-align:right}
  .bld{font-weight:700}

  /* ─ Totals ─ */
  .totals-wrap{display:flex;justify-content:flex-end;margin-top:14px}
  .totals-tbl{width:260px;border-collapse:collapse;font-size:13px;font-family:'Inter',system-ui,sans-serif}
  .totals-tbl td{padding:5px 0}
  .totals-tbl .tl{color:#6b7280;font-style:italic}
  .totals-tbl .tr{text-align:right}
  .grand-row td{border-top:2px solid ${brand};padding-top:12px;font-weight:700;font-size:17px;color:${brand}}

  /* ─ Notes ─ */
  .notes-sec{font-size:12.5px;color:#374151;line-height:1.6;margin-top:4px;font-style:italic}
  .notes-lbl{font-weight:700;font-style:normal;color:#111827;font-size:12px;font-family:'Inter',system-ui,sans-serif;letter-spacing:.03em;text-transform:uppercase;display:block;margin-bottom:4px}

  /* ─ Sig ─ */
  .sig-row{display:flex;gap:24px;margin-top:36px}
  .sig-box{flex:1;border-top:1px solid #374151;padding-top:8px;font-size:10.5px;color:#9ca3af;text-align:center;font-family:'Inter',system-ui,sans-serif}

  /* ─ Footer ─ */
  .foot{margin-top:24px;text-align:center;font-size:10.5px;color:#9ca3af;font-family:'Inter',system-ui,sans-serif}

  @media print{body{background:#fff}.page{padding:32px 48px}}
</style></head><body><div class="page">

<!-- Header -->
${logo ? `<img src="${_esc(logo)}" class="co-logo"/>` : ""}
<div class="co-name">${_esc(doc.company || cfg.companyName || "")}</div>
${doc.company_gstin || doc.gstin ? `<div class="co-sub">GSTIN: ${_esc(doc.company_gstin || doc.gstin)}</div>` : ""}
<div class="doc-title">${_esc(cfg.title)}</div>
<div class="doc-num">${_esc(doc.name || "")}</div>

<hr class="thick"/>

<!-- Meta -->
<div class="meta-row">
  <div class="mc">
    <div class="ml">${_esc(cfg.partyLabel)}</div>
    <div class="mv">${_esc(doc[cfg.partyField] || doc.customer || doc.supplier || "")}</div>
    ${doc.address_display ? `<div class="ms">${_esc(doc.address_display)}</div>` : ""}
    ${doc.customer_gstin || doc.supplier_gstin ? `<div style="font-size:11px;color:#6b7280;margin-top:2px;font-family:Inter,sans-serif">GSTIN: ${_esc(doc.customer_gstin || doc.supplier_gstin)}</div>` : ""}
  </div>
  <div class="mc right">
    <div class="ml">Date</div>
    <div class="mv">${_esc(doc.posting_date || doc.transaction_date || "")}</div>
    ${doc.due_date ? `<div style="margin-top:8px"><div class="ml">Due Date</div><div class="mv">${_esc(doc.due_date)}</div></div>` : ""}
    ${doc.delivery_date ? `<div style="margin-top:8px"><div class="ml">Delivery Date</div><div class="mv">${_esc(doc.delivery_date)}</div></div>` : ""}
    ${doc.valid_till ? `<div style="margin-top:8px"><div class="ml">Valid Till</div><div class="mv">${_esc(doc.valid_till)}</div></div>` : ""}
  </div>
</div>

${(doc.po_no || doc.payment_terms_template || doc.place_of_supply) ? `
<div class="meta-extra">
  ${doc.po_no ? `<div class="me-item"><div class="ml">PO Number</div><div class="mv">${_esc(doc.po_no)}</div></div>` : ""}
  ${doc.payment_terms_template ? `<div class="me-item"><div class="ml">Payment Terms</div><div class="mv">${_esc(doc.payment_terms_template)}</div></div>` : ""}
  ${doc.place_of_supply ? `<div class="me-item"><div class="ml">Place of Supply</div><div class="mv">${_esc(doc.place_of_supply)}</div></div>` : ""}
</div>` : ""}

<hr class="thin"/>

<!-- Items table -->
<table class="items">
  <thead>
    <tr>
      <th></th>
      <th>Item</th>
      ${cfg.includeHsn ? `<th class="tc" style="width:76px">HSN/SAC</th>` : ""}
      <th class="tr" style="width:110px">Quantity &amp; Rate</th>
      ${cfg.includeDiscount ? `<th class="tc" style="width:52px">Disc</th>` : ""}
      <th class="tr" style="width:110px">Amount</th>
    </tr>
  </thead>
  <tbody>
    ${items || `<tr><td colspan="6" style="text-align:center;color:#9ca3af;padding:28px;font-style:italic">No items</td></tr>`}
  </tbody>
</table>

<!-- Totals -->
<hr class="thin" style="margin-top:6px"/>
<div class="totals-wrap">
  <table class="totals-tbl">
    <tr><td class="tl">Subtotal</td><td class="tr">${_fmt(netTotal, currency)}</td></tr>
    ${(doc.taxes || []).map(t =>
      `<tr><td class="tl">${_esc(t.description || t.account_head)}</td><td class="tr">${_fmt(t.tax_amount || 0, currency)}</td></tr>`
    ).join("")}
    ${doc.discount_amount ? `<tr><td class="tl" style="color:#dc2626">Discount</td><td class="tr" style="color:#dc2626">− ${_fmt(doc.discount_amount, currency)}</td></tr>` : ""}
    <tr class="grand-row"><td>Total Due</td><td style="text-align:right">${_fmt(doc.grand_total, currency)}</td></tr>
  </table>
</div>

${doc.remarks ? `<hr class="thin"/><div class="notes-sec"><span class="notes-lbl">Remarks</span>${_esc(doc.remarks)}</div>` : ""}
${doc.terms || doc.customer_note ? `<hr class="thin"/><div class="notes-sec"><span class="notes-lbl">${doc.customer_note ? "Note" : "Terms &amp; Conditions"}</span>${_esc(doc.customer_note || doc.terms)}</div>` : ""}

<!-- Signatures -->
<div class="sig-row">
  <div class="sig-box">Prepared By</div>
  <div class="sig-box">Authorised Signatory</div>
  <div class="sig-box">Receiver's Signature</div>
</div>

<!-- Footer -->
<hr class="thin" style="margin-top:24px"/>
<div class="foot">${_esc(doc.company || "")} · ${_esc(doc.name)} · Printed ${_today()}</div>

</div></body></html>`;
}

// ── Public API ────────────────────────────────────────────────────────────────
export function useLivePreview() {
  function setCompany(c)    { _loadBranding(c); }
  function setTemplate(t)   { _state.template = t; _saveBranding(); }
  function setBrandColor(c) { _state.brandColor = c; _saveBranding(); }
  function setLogo(l)       { _state.logo = l; _saveBranding(); }

  function renderDocument(doc, config) {
    const cfg = {
      title:        "INVOICE",
      partyLabel:   "Bill To",
      partyField:   "customer_name",
      companyName:  "",
      includeHsn:   true,
      includeDiscount: true,
      ...config,
    };
    if (_state.template === "modern")  return _renderModern(doc, cfg);
    if (_state.template === "minimal") return _renderMinimal(doc, cfg);
    return _renderClassic(doc, cfg);
  }

  function printDoc(doc, config) {
    const html = renderDocument(doc, config);
    const safeHtml = html.replace(/"/g, "&quot;");
    const shell = `<!DOCTYPE html><html><head><meta charset="utf-8"/>
<title>Print — ${doc?.name || ""}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',system-ui,sans-serif;background:#e5e7eb;min-height:100vh}
  .toolbar{position:sticky;top:0;z-index:10;background:#fff;padding:10px 18px;
    border-bottom:1px solid #e5e7eb;display:flex;align-items:center;gap:10px;box-shadow:0 1px 4px rgba(0,0,0,.06)}
  .tb-lbl{font-size:11.5px;font-weight:700;color:#374151;letter-spacing:.04em;margin-right:4px}
  .tbtn{font:inherit;font-size:12px;padding:6px 14px;border-radius:6px;border:1px solid #e5e7eb;
    background:#fff;color:#374151;cursor:pointer;font-weight:500;transition:all .15s}
  .tbtn.active{background:#1a6ef7;color:#fff;border-color:#1a6ef7}
  .tbtn:hover:not(.active){background:#f9fafb;border-color:#cbd5e1}
  .sep{width:1px;height:22px;background:#e5e7eb;margin:0 4px}
  .print-btn{margin-left:auto;background:#1a6ef7;color:#fff;border:none;padding:7px 16px;
    border-radius:7px;font-weight:700;cursor:pointer;font:inherit;font-size:12.5px;
    display:flex;align-items:center;gap:6px;transition:background .15s}
  .print-btn:hover{background:#1558d0}
  .doc-wrap{max-width:900px;margin:20px auto;background:#fff;
    box-shadow:0 4px 24px rgba(0,0,0,.1);border-radius:4px;overflow:hidden}
  iframe{border:none;width:100%;min-height:1100px;display:block}
  @media print{.toolbar{display:none!important}.doc-wrap{box-shadow:none;margin:0;max-width:none;border-radius:0}}
</style></head><body>
<div class="toolbar">
  <span class="tb-lbl">PRINT PREVIEW</span>
  <div class="sep"></div>
  <button class="tbtn ${_state.template === "classic" ? "active" : ""}" data-t="classic">Classic</button>
  <button class="tbtn ${_state.template === "modern"  ? "active" : ""}" data-t="modern">Modern</button>
  <button class="tbtn ${_state.template === "minimal" ? "active" : ""}" data-t="minimal">Minimal</button>
  <button class="print-btn" onclick="window.print()">
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
      <polyline points="6 9 6 2 18 2 18 9"/><path d="M6 18H4a2 2 0 0 1-2-2v-5a2 2 0 0 1 2-2h16a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-2"/>
      <rect x="6" y="14" width="12" height="8"/>
    </svg>
    Print
  </button>
</div>
<div class="doc-wrap"><iframe id="frm" srcdoc="${safeHtml}"></iframe></div>
<script>
  document.querySelectorAll('.tbtn').forEach(b => b.onclick = () => {
    document.querySelectorAll('.tbtn').forEach(x => x.classList.remove('active'));
    b.classList.add('active');
    if (window.opener && !window.opener.closed) {
      window.opener.postMessage({
        kind: 'switch-template',
        template: b.dataset.t,
        doc: ${JSON.stringify(doc || {})},
        config: ${JSON.stringify(config || {})}
      }, '*');
    }
  });
  // Auto-resize iframe to content height
  const frm = document.getElementById('frm');
  frm.onload = () => {
    try {
      const h = frm.contentDocument.documentElement.scrollHeight;
      if (h > 400) frm.style.minHeight = h + 'px';
    } catch {}
  };
<\/script>
</body></html>`;
    const w = window.open("", "_blank");
    if (!w) return;
    w.document.open(); w.document.write(shell); w.document.close();
  }

  if (typeof window !== "undefined" && !window.__bvLivePreviewListener) {
    window.__bvLivePreviewListener = true;
    window.addEventListener("message", (ev) => {
      const d = ev.data || {};
      if (d.kind === "switch-template" && d.template) {
        setTemplate(d.template);
        if (d.doc && d.config) printDoc(d.doc, d.config);
      }
    });
  }

  const template   = computed({ get: () => _state.template,   set: setTemplate });
  const brandColor = computed({ get: () => _state.brandColor, set: setBrandColor });
  const logo       = computed({ get: () => _state.logo,       set: setLogo });

  return { state: _state, template, brandColor, logo, setCompany, renderDocument, printDoc };
}
