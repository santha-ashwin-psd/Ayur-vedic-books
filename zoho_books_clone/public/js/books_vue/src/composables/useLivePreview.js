// Shared print-template renderer — Classic / Modern / Minimal.
// All pages reuse these three templates by calling printDoc(doc, config).

import { reactive, computed } from "vue";

const _state = reactive({
  template: "classic",
  brandColor: "#1a6ef7",
  logo: "",
  company: "",
});

async function _loadBranding(company) {
  _state.company = company || "";
  try {
    const csrf = window.frappe?.csrf_token || "";
    const res = await fetch("/api/method/zoho_books_clone.api.admin.get_company_settings", {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded", "X-Frappe-CSRF-Token": csrf },
      credentials: "same-origin",
      body: new URLSearchParams({}),
    });
    const data = await res.json();
    const d = data.message || {};
    if (d.pdf_template) _state.template   = d.pdf_template;
    if (d.brand_color)  _state.brandColor = d.brand_color;
    if (d.company_logo) _state.logo       = d.company_logo;
  } catch {}
}

function _saveBranding() {
  // no-op: branding is managed centrally in Settings > Branding & Template
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
function _logoSrc(url) {
  if (!url) return "";
  if (url.startsWith("data:") || url.startsWith("http")) return url;
  return (window.frappe?.boot?.site_url || window.location.origin).replace(/\/$/, "") + url;
}

// ── TEMPLATE 1: "Executive" (key: classic) ───────────────────────────────────
function _renderClassic(doc, cfg) {
  const brand    = _state.brandColor;
  const logo     = _logoSrc(_state.logo);
  const currency = doc.currency || "INR";
  const netTotal = doc.net_total != null ? doc.net_total
    : (doc.grand_total || 0) - (doc.total_taxes_and_charges || 0);
  const party    = doc[cfg.partyField] || doc.customer || doc.supplier || "";
  const docDate  = doc.posting_date || doc.transaction_date || "";

  const items = (doc.items || []).map((it, i) => `
    <tr>
      <td class="n">${i + 1}</td>
      <td>
        <div class="inm">${_esc(it.item_name || it.item_code)}</div>
        ${it.item_code && it.item_name && it.item_code !== it.item_name ? `<div class="ic">${_esc(it.item_code)}</div>` : ""}
        ${it.description && it.description !== it.item_name ? `<div class="ids">${_esc(it.description)}</div>` : ""}
      </td>
      ${cfg.includeHsn ? `<td class="c">${_esc(it.gst_hsn_code || it.hsn_code || "—")}</td>` : ""}
      <td class="r">${Number(it.qty || 0)}</td>
      <td class="c">${_esc(it.uom || "Nos")}</td>
      <td class="r">${_fmt(it.rate, currency)}</td>
      ${cfg.includeDiscount ? `<td class="c">${Number(it.discount_percentage || 0)}%</td>` : ""}
      <td class="r b">${_fmt(it.amount, currency)}</td>
    </tr>`).join("");

  const taxRows = (doc.taxes || []).map(t =>
    `<tr><td class="tl">${_esc(t.description || t.account_head)}</td><td class="r">${_fmt(t.tax_amount || 0, currency)}</td></tr>`
  ).join("");

  const colspan = 6 + (cfg.includeHsn ? 1 : 0) + (cfg.includeDiscount ? 1 : 0);

  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<title>${_esc(cfg.title)} — ${_esc(doc.name)}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',system-ui,-apple-system,sans-serif;color:#1e293b;background:#fff;font-size:12.5px;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .page{max-width:920px;margin:0 auto}
  /* Header band */
  .hd{background:${brand};color:#fff;display:flex;justify-content:space-between;align-items:center;padding:26px 40px}
  .hd-l{display:flex;align-items:center;gap:16px}
  .hd-logo{max-height:52px;max-width:120px;object-fit:contain;background:#fff;border-radius:8px;padding:6px}
  .hd-co{font-size:21px;font-weight:800;letter-spacing:-.01em;line-height:1.15}
  .hd-gst{font-size:10.5px;opacity:.85;margin-top:3px}
  .hd-badge{background:rgba(255,255,255,.16);border:1px solid rgba(255,255,255,.35);border-radius:10px;padding:12px 18px;text-align:right;min-width:190px}
  .hd-badge .t{font-size:10.5px;font-weight:700;letter-spacing:.14em;text-transform:uppercase;opacity:.9}
  .hd-badge .num{font-size:19px;font-weight:800;margin-top:2px}
  .hd-badge .dt{font-size:10.5px;opacity:.85;margin-top:4px}
  .body{padding:28px 40px 36px}
  /* Party cards */
  .parties{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px}
  .pc{border:1px solid #e6ebf1;border-radius:10px;padding:14px 16px}
  .pc .lbl{font-size:9.5px;font-weight:700;letter-spacing:.08em;text-transform:uppercase;color:${brand};margin-bottom:5px}
  .pc .nm{font-weight:700;color:#0f172a;font-size:13.5px}
  .pc .sub{font-size:11px;color:#64748b;margin-top:3px;white-space:pre-line;line-height:1.45}
  /* Meta pills */
  .meta{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:18px}
  .pill{background:#f4f7fb;border:1px solid #e6ebf1;border-radius:7px;padding:6px 12px;font-size:11px}
  .pill b{color:#94a3b8;font-weight:700;text-transform:uppercase;letter-spacing:.05em;font-size:9.5px;display:block;margin-bottom:1px}
  .pill span{color:#0f172a;font-weight:600}
  /* Items */
  table.it{width:100%;border-collapse:collapse;font-size:12px;border:1px solid #e6ebf1;border-radius:10px;overflow:hidden}
  table.it thead th{background:${brand}14;color:${brand};padding:10px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.04em;text-align:left;border-bottom:2px solid ${brand}40}
  table.it thead th.r{text-align:right}table.it thead th.c{text-align:center}
  table.it tbody td{padding:11px 10px;border-bottom:1px solid #f0f3f7;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
  table.it tbody tr:nth-child(even){background:#fafbfd}
  table.it tbody tr:last-child td{border-bottom:none}
  .it .n{color:#94a3b8;text-align:center;width:26px}
  .it .inm{font-weight:600;color:#0f172a}.it .ic{font-size:10px;color:#94a3b8;margin-top:1px}.it .ids{font-size:10.5px;color:#64748b;margin-top:2px}
  .it .r{text-align:right}.it .c{text-align:center}.it .b{font-weight:700;font-variant-numeric:tabular-nums}
  /* Totals */
  .tw{display:flex;justify-content:flex-end;margin-top:16px}
  .tt{width:300px;border:1px solid #e6ebf1;border-radius:10px;overflow:hidden}
  .tt .row{display:flex;justify-content:space-between;padding:9px 16px;font-size:12.5px;border-bottom:1px solid #f0f3f7}
  .tt .row .tl{color:#64748b}.tt .row span:last-child{font-variant-numeric:tabular-nums}
  .tt .grand{background:${brand};color:#fff;font-weight:800;font-size:15px;padding:12px 16px;display:flex;justify-content:space-between}
  /* Bottom */
  .notes{margin-top:22px;display:grid;grid-template-columns:1fr 1fr;gap:14px}
  .bx{border:1px solid #e6ebf1;border-radius:10px;padding:13px 16px;font-size:11.5px;color:#374151;line-height:1.6}
  .bx .h{font-size:9.5px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:${brand};margin-bottom:5px}
  .sig{display:flex;gap:18px;margin-top:30px}
  .sig div{flex:1;border-top:1.5px solid #cbd5e1;padding-top:7px;font-size:10px;color:#94a3b8;text-align:center}
  .ft{margin-top:22px;padding:12px 40px;border-top:1px solid #eef2f6;display:flex;justify-content:space-between;font-size:10px;color:#94a3b8}
  @media print{.page{max-width:none}}
</style></head><body><div class="page">
  <div class="hd">
    <div class="hd-l">
      ${logo ? `<img src="${_esc(logo)}" class="hd-logo"/>` : ""}
      <div>
        <div class="hd-co">${_esc(doc.company || cfg.companyName || "")}</div>
        ${doc.company_gstin || doc.gstin ? `<div class="hd-gst">GSTIN: ${_esc(doc.company_gstin || doc.gstin)}</div>` : ""}
      </div>
    </div>
    <div class="hd-badge">
      <div class="t">${_esc(cfg.title)}</div>
      <div class="num">${_esc(doc.name || "")}</div>
      <div class="dt">${_esc(docDate)}${doc.status ? " · " + _esc(doc.status) : ""}</div>
    </div>
  </div>
  <div class="body">
    <div class="parties">
      <div class="pc">
        <div class="lbl">From</div>
        <div class="nm">${_esc(doc.company || cfg.companyName || "")}</div>
        ${doc.company_gstin || doc.gstin ? `<div class="sub">GSTIN: ${_esc(doc.company_gstin || doc.gstin)}</div>` : ""}
      </div>
      <div class="pc">
        <div class="lbl">${_esc(cfg.partyLabel)}</div>
        <div class="nm">${_esc(party)}</div>
        ${doc.address_display ? `<div class="sub">${_esc(doc.address_display)}</div>` : ""}
        ${doc.customer_gstin || doc.supplier_gstin ? `<div class="sub">GSTIN: ${_esc(doc.customer_gstin || doc.supplier_gstin)}</div>` : ""}
      </div>
    </div>
    <div class="meta">
      <div class="pill"><b>Date</b><span>${_esc(docDate)}</span></div>
      ${doc.due_date ? `<div class="pill"><b>Due Date</b><span>${_esc(doc.due_date)}</span></div>` : ""}
      ${doc.valid_till ? `<div class="pill"><b>Valid Till</b><span>${_esc(doc.valid_till)}</span></div>` : ""}
      ${doc.delivery_date ? `<div class="pill"><b>Delivery</b><span>${_esc(doc.delivery_date)}</span></div>` : ""}
      ${doc.po_no ? `<div class="pill"><b>PO Number</b><span>${_esc(doc.po_no)}</span></div>` : ""}
      ${doc.place_of_supply ? `<div class="pill"><b>Place of Supply</b><span>${_esc(doc.place_of_supply)}</span></div>` : ""}
      ${doc.currency && doc.currency !== "INR" ? `<div class="pill"><b>Currency</b><span>${_esc(doc.currency)}</span></div>` : ""}
    </div>
    ${doc.shipping_address ? `<div class="pc" style="margin-bottom:16px"><div class="lbl">Ship To</div><div class="sub" style="margin-top:2px">${_esc(doc.shipping_address)}</div></div>` : ""}
    <table class="it">
      <thead><tr>
        <th class="c" style="width:26px">#</th><th>Item / Description</th>
        ${cfg.includeHsn ? `<th class="c" style="width:74px">HSN/SAC</th>` : ""}
        <th class="r" style="width:48px">Qty</th><th class="c" style="width:50px">UOM</th>
        <th class="r" style="width:104px">Rate</th>
        ${cfg.includeDiscount ? `<th class="c" style="width:50px">Disc</th>` : ""}
        <th class="r" style="width:110px">Amount</th>
      </tr></thead>
      <tbody>${items || `<tr><td colspan="${colspan}" style="text-align:center;color:#9ca3af;padding:26px">No items</td></tr>`}</tbody>
    </table>
    <div class="tw"><div class="tt">
      <div class="row"><span class="tl">Subtotal</span><span>${_fmt(netTotal, currency)}</span></div>
      ${taxRows}
      ${doc.discount_amount ? `<div class="row"><span class="tl" style="color:#dc2626">Discount</span><span style="color:#dc2626">− ${_fmt(doc.discount_amount, currency)}</span></div>` : ""}
      <div class="grand"><span>Grand Total</span><span>${_fmt(doc.grand_total, currency)}</span></div>
    </div></div>
    ${(doc.remarks || doc.terms || doc.customer_note) ? `
    <div class="notes">
      ${doc.remarks ? `<div class="bx"><div class="h">Remarks</div>${_esc(doc.remarks)}</div>` : "<div></div>"}
      ${doc.terms || doc.customer_note ? `<div class="bx"><div class="h">${doc.customer_note ? "Note" : "Terms & Conditions"}</div>${_esc(doc.customer_note || doc.terms)}</div>` : ""}
    </div>` : ""}
    <div class="sig"><div>Prepared By</div><div>Authorised Signatory</div><div>Receiver's Signature</div></div>
  </div>
  <div class="ft"><span>${_esc(doc.company || cfg.companyName || "")}</span><span>${_esc(doc.name)} · Printed ${_today()}</span></div>
</div></body></html>`;
}

// ── TEMPLATE 2: "Sidebar" (key: modern) ──────────────────────────────────────
function _renderModern(doc, cfg) {
  const brand    = _state.brandColor;
  const logo     = _logoSrc(_state.logo);
  const currency = doc.currency || "INR";
  const netTotal = doc.net_total != null ? doc.net_total
    : (doc.grand_total || 0) - (doc.total_taxes_and_charges || 0);
  const party    = doc[cfg.partyField] || doc.customer || doc.supplier || "";
  const docDate  = doc.posting_date || doc.transaction_date || "";

  const items = (doc.items || []).map((it, i) => `
    <tr>
      <td>
        <div class="inm">${_esc(it.item_name || it.item_code)}</div>
        ${it.description && it.description !== it.item_name ? `<div class="ids">${_esc(it.description)}</div>` : ""}
        ${cfg.includeHsn && (it.gst_hsn_code || it.hsn_code) ? `<div class="ihs">HSN ${_esc(it.gst_hsn_code || it.hsn_code)}</div>` : ""}
      </td>
      <td class="r">${Number(it.qty || 0)} <span class="mut">${_esc(it.uom || "")}</span></td>
      <td class="r">${_fmt(it.rate, currency)}</td>
      ${cfg.includeDiscount ? `<td class="c mut">${Number(it.discount_percentage || 0)}%</td>` : ""}
      <td class="r b">${_fmt(it.amount, currency)}</td>
    </tr>`).join("");

  const colspan = 4 + (cfg.includeDiscount ? 1 : 0);

  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<title>${_esc(cfg.title)} — ${_esc(doc.name)}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',system-ui,-apple-system,sans-serif;color:#0f172a;background:#fff;font-size:12.5px;line-height:1.5;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .wrap{display:flex;min-height:100%;max-width:920px;margin:0 auto}
  /* Sidebar */
  .side{width:232px;flex-shrink:0;background:${brand};color:#fff;padding:30px 22px;display:flex;flex-direction:column}
  .side-logo{max-height:50px;max-width:150px;object-fit:contain;background:#fff;border-radius:8px;padding:6px;margin-bottom:16px}
  .side-co{font-size:18px;font-weight:800;line-height:1.2}
  .side-blk{margin-top:16px}
  .side-blk .l{font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;opacity:.7;margin-bottom:3px}
  .side-blk .v{font-size:11.5px;opacity:.95;white-space:pre-line;line-height:1.5}
  .side-doc{margin-top:auto;padding-top:24px}
  .side-doc .t{font-size:13px;font-weight:700;letter-spacing:.18em;text-transform:uppercase;opacity:.85}
  .side-doc .num{font-size:24px;font-weight:800;margin-top:4px;line-height:1}
  /* Main */
  .main{flex:1;padding:34px 36px}
  .billto .l{font-size:9.5px;font-weight:800;letter-spacing:.08em;text-transform:uppercase;color:${brand};margin-bottom:4px}
  .billto .nm{font-size:16px;font-weight:800;color:#0f172a}
  .billto .sub{font-size:11px;color:#64748b;margin-top:3px;white-space:pre-line;line-height:1.45}
  .meta{display:flex;flex-wrap:wrap;gap:22px;margin:20px 0 22px;padding:14px 0;border-top:1px solid #eef2f6;border-bottom:1px solid #eef2f6}
  .meta .m .l{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:.06em;color:#94a3b8}
  .meta .m .v{font-size:12.5px;font-weight:700;color:#0f172a;margin-top:2px}
  table{width:100%;border-collapse:collapse;font-size:12.5px}
  thead th{text-align:left;padding:0 8px 10px;font-size:10px;font-weight:800;text-transform:uppercase;letter-spacing:.05em;color:#94a3b8;border-bottom:2px solid ${brand}}
  thead th.r{text-align:right}thead th.c{text-align:center}
  tbody td{padding:12px 8px;border-bottom:1px solid #f0f3f7;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
  .inm{font-weight:600}.ids{font-size:10.5px;color:#64748b;margin-top:2px}.ihs{font-size:10px;color:#94a3b8;margin-top:2px}
  .r{text-align:right}.c{text-align:center}.b{font-weight:700;font-variant-numeric:tabular-nums}.mut{color:#94a3b8;font-size:10.5px}
  .tw{display:flex;justify-content:flex-end;margin-top:18px}
  .tt{width:290px}
  .tt .row{display:flex;justify-content:space-between;padding:7px 0;font-size:12.5px;color:#475569}
  .tt .row span:last-child{font-variant-numeric:tabular-nums;color:#0f172a}
  .tt .grand{margin-top:8px;background:${brand};color:#fff;border-radius:10px;padding:13px 18px;display:flex;justify-content:space-between;font-weight:800;font-size:15px}
  .notes{margin-top:24px;font-size:11.5px;color:#374151;line-height:1.6}
  .notes .h{font-size:9.5px;font-weight:800;text-transform:uppercase;letter-spacing:.06em;color:${brand};margin-bottom:4px}
  .sig{display:flex;gap:18px;margin-top:32px}
  .sig div{flex:1;border-top:1.5px solid #cbd5e1;padding-top:7px;font-size:10px;color:#94a3b8;text-align:center}
  .ft{margin-top:26px;font-size:10px;color:#b6c0cc;text-align:right}
  @media print{.wrap{max-width:none}.side{min-height:100vh}}
</style></head><body><div class="wrap">
  <aside class="side">
    ${logo ? `<img src="${_esc(logo)}" class="side-logo"/>` : ""}
    <div class="side-co">${_esc(doc.company || cfg.companyName || "")}</div>
    ${doc.company_gstin || doc.gstin ? `<div class="side-blk"><div class="l">GSTIN</div><div class="v">${_esc(doc.company_gstin || doc.gstin)}</div></div>` : ""}
    ${doc.shipping_address ? `<div class="side-blk"><div class="l">Ship To</div><div class="v">${_esc(doc.shipping_address)}</div></div>` : ""}
    <div class="side-doc"><div class="t">${_esc(cfg.title)}</div><div class="num">${_esc(doc.name || "")}</div></div>
  </aside>
  <main class="main">
    <div class="billto">
      <div class="l">${_esc(cfg.partyLabel)}</div>
      <div class="nm">${_esc(party)}</div>
      ${doc.address_display ? `<div class="sub">${_esc(doc.address_display)}</div>` : ""}
      ${doc.customer_gstin || doc.supplier_gstin ? `<div class="sub">GSTIN: ${_esc(doc.customer_gstin || doc.supplier_gstin)}</div>` : ""}
    </div>
    <div class="meta">
      <div class="m"><div class="l">Date</div><div class="v">${_esc(docDate)}</div></div>
      ${doc.due_date ? `<div class="m"><div class="l">Due Date</div><div class="v">${_esc(doc.due_date)}</div></div>` : ""}
      ${doc.valid_till ? `<div class="m"><div class="l">Valid Till</div><div class="v">${_esc(doc.valid_till)}</div></div>` : ""}
      ${doc.delivery_date ? `<div class="m"><div class="l">Delivery</div><div class="v">${_esc(doc.delivery_date)}</div></div>` : ""}
      ${doc.po_no ? `<div class="m"><div class="l">PO Number</div><div class="v">${_esc(doc.po_no)}</div></div>` : ""}
      ${doc.place_of_supply ? `<div class="m"><div class="l">Place of Supply</div><div class="v">${_esc(doc.place_of_supply)}</div></div>` : ""}
      ${doc.status ? `<div class="m"><div class="l">Status</div><div class="v">${_esc(doc.status)}</div></div>` : ""}
    </div>
    <table>
      <thead><tr>
        <th>Item</th><th class="r" style="width:100px">Qty</th><th class="r" style="width:110px">Rate</th>
        ${cfg.includeDiscount ? `<th class="c" style="width:54px">Disc</th>` : ""}
        <th class="r" style="width:120px">Amount</th>
      </tr></thead>
      <tbody>${items || `<tr><td colspan="${colspan}" style="text-align:center;color:#9ca3af;padding:28px">No items</td></tr>`}</tbody>
    </table>
    <div class="tw"><div class="tt">
      <div class="row"><span>Subtotal</span><span>${_fmt(netTotal, currency)}</span></div>
      ${(doc.taxes || []).map(t => `<div class="row"><span>${_esc(t.description || t.account_head)}</span><span>${_fmt(t.tax_amount || 0, currency)}</span></div>`).join("")}
      ${doc.discount_amount ? `<div class="row"><span style="color:#dc2626">Discount</span><span style="color:#dc2626">− ${_fmt(doc.discount_amount, currency)}</span></div>` : ""}
      <div class="grand"><span>Grand Total</span><span>${_fmt(doc.grand_total, currency)}</span></div>
    </div></div>
    ${doc.terms || doc.customer_note ? `<div class="notes"><div class="h">${doc.customer_note ? "Note" : "Terms & Conditions"}</div>${_esc(doc.customer_note || doc.terms)}</div>` : ""}
    ${doc.remarks ? `<div class="notes"><div class="h">Remarks</div>${_esc(doc.remarks)}</div>` : ""}
    <div class="sig"><div>Prepared By</div><div>Authorised Signatory</div><div>Receiver's Signature</div></div>
    <div class="ft">${_esc(doc.name)} · Printed ${_today()}</div>
  </main>
</div></body></html>`;
}

// ── TEMPLATE 3: "Editorial" (key: minimal) ───────────────────────────────────
function _renderMinimal(doc, cfg) {
  const brand    = _state.brandColor;
  const logo     = _logoSrc(_state.logo);
  const currency = doc.currency || "INR";
  const netTotal = doc.net_total != null ? doc.net_total
    : (doc.grand_total || 0) - (doc.total_taxes_and_charges || 0);
  const party    = doc[cfg.partyField] || doc.customer || doc.supplier || "";
  const docDate  = doc.posting_date || doc.transaction_date || "";

  const items = (doc.items || []).map((it, i) => `
    <tr>
      <td class="n">${i + 1}</td>
      <td>
        <span class="inm">${_esc(it.item_name || it.item_code)}</span>
        ${it.description && it.description !== it.item_name ? `<div class="ids">${_esc(it.description)}</div>` : ""}
      </td>
      ${cfg.includeHsn ? `<td class="c">${_esc(it.gst_hsn_code || it.hsn_code || "—")}</td>` : ""}
      <td class="r">${Number(it.qty || 0)} ${_esc(it.uom || "")}</td>
      <td class="r">${_fmt(it.rate, currency)}</td>
      ${cfg.includeDiscount ? `<td class="c">${Number(it.discount_percentage || 0) ? "−" + Number(it.discount_percentage) + "%" : "—"}</td>` : ""}
      <td class="r b">${_fmt(it.amount, currency)}</td>
    </tr>`).join("");

  const colspan = 5 + (cfg.includeHsn ? 1 : 0) + (cfg.includeDiscount ? 1 : 0);

  return `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"/>
<title>${_esc(cfg.title)} — ${_esc(doc.name)}</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:'Inter',system-ui,sans-serif;color:#111827;background:#fff;font-size:12.5px;line-height:1.65;-webkit-print-color-adjust:exact;print-color-adjust:exact}
  .page{max-width:800px;margin:0 auto;padding:56px 64px}
  .top{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:6px}
  .top-l{display:flex;align-items:center;gap:12px}
  .logo{max-height:44px;max-width:120px;object-fit:contain}
  .co{font-size:17px;font-weight:800;letter-spacing:-.01em}
  .co-gst{font-size:10px;color:#9ca3af;margin-top:2px}
  .doc{text-align:right}
  .doc .t{font-size:11px;font-weight:600;letter-spacing:.28em;text-transform:uppercase;color:#9ca3af}
  .doc .num{font-size:15px;font-weight:800;margin-top:3px;color:#111827}
  .rule{height:2px;background:${brand};margin:14px 0 22px}
  .meta{display:flex;justify-content:space-between;gap:30px;margin-bottom:24px}
  .meta .blk{flex:1}
  .meta .blk.r{text-align:right}
  .meta .l{font-size:9px;font-weight:700;letter-spacing:.1em;text-transform:uppercase;color:#9ca3af;margin-bottom:3px}
  .meta .v{font-size:13px;font-weight:700;color:#111827}
  .meta .sub{font-size:11px;color:#6b7280;margin-top:2px;white-space:pre-line;line-height:1.45}
  .meta .row2{margin-top:10px}
  table{width:100%;border-collapse:collapse;font-size:12.5px}
  thead th{text-align:left;padding:8px 6px;border-bottom:1px solid #111827;font-size:9.5px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:#6b7280}
  thead th.r{text-align:right}thead th.c{text-align:center}
  tbody td{padding:11px 6px;border-bottom:1px solid #f0f0f1;vertical-align:top;word-break:break-word;overflow-wrap:anywhere}
  tbody tr:last-child td{border-bottom:none}
  .n{color:#cbd5e1;width:22px;font-variant-numeric:tabular-nums}
  .inm{font-weight:700}.ids{font-size:11px;color:#6b7280;margin-top:2px}
  .r{text-align:right;font-variant-numeric:tabular-nums}.c{text-align:center}.b{font-weight:700}
  .tw{display:flex;justify-content:flex-end;margin-top:6px}
  .tt{width:260px}
  .tt .row{display:flex;justify-content:space-between;padding:6px 0;font-size:12.5px;color:#6b7280}
  .tt .row span:last-child{color:#111827;font-variant-numeric:tabular-nums}
  .tt .grand{display:flex;justify-content:space-between;margin-top:6px;padding-top:11px;border-top:2px solid ${brand};font-size:16px;font-weight:800;color:${brand}}
  .notes{margin-top:26px;border-top:1px solid #f0f0f1;padding-top:14px;font-size:12px;color:#374151;line-height:1.6}
  .notes .h{font-size:9.5px;font-weight:800;letter-spacing:.07em;text-transform:uppercase;color:#111827;margin-bottom:4px}
  .sig{display:flex;gap:24px;margin-top:38px}
  .sig div{flex:1;border-top:1px solid #111827;padding-top:7px;font-size:10px;color:#9ca3af;text-align:center}
  .ft{margin-top:28px;text-align:center;font-size:10px;color:#cbd5e1;letter-spacing:.04em}
  @media print{.page{padding:40px 48px;max-width:none}}
</style></head><body><div class="page">
  <div class="top">
    <div class="top-l">
      ${logo ? `<img src="${_esc(logo)}" class="logo"/>` : ""}
      <div>
        <div class="co">${_esc(doc.company || cfg.companyName || "")}</div>
        ${doc.company_gstin || doc.gstin ? `<div class="co-gst">GSTIN: ${_esc(doc.company_gstin || doc.gstin)}</div>` : ""}
      </div>
    </div>
    <div class="doc"><div class="t">${_esc(cfg.title)}</div><div class="num">${_esc(doc.name || "")}</div></div>
  </div>
  <div class="rule"></div>
  <div class="meta">
    <div class="blk">
      <div class="l">${_esc(cfg.partyLabel)}</div>
      <div class="v">${_esc(party)}</div>
      ${doc.address_display ? `<div class="sub">${_esc(doc.address_display)}</div>` : ""}
      ${doc.customer_gstin || doc.supplier_gstin ? `<div class="sub">GSTIN: ${_esc(doc.customer_gstin || doc.supplier_gstin)}</div>` : ""}
    </div>
    <div class="blk r">
      <div class="l">Date</div><div class="v">${_esc(docDate)}</div>
      ${doc.due_date ? `<div class="row2"><div class="l">Due Date</div><div class="v">${_esc(doc.due_date)}</div></div>` : ""}
      ${doc.valid_till ? `<div class="row2"><div class="l">Valid Till</div><div class="v">${_esc(doc.valid_till)}</div></div>` : ""}
      ${doc.delivery_date ? `<div class="row2"><div class="l">Delivery</div><div class="v">${_esc(doc.delivery_date)}</div></div>` : ""}
      ${doc.po_no ? `<div class="row2"><div class="l">PO Number</div><div class="v">${_esc(doc.po_no)}</div></div>` : ""}
    </div>
  </div>
  <table>
    <thead><tr>
      <th style="width:22px"></th><th>Item</th>
      ${cfg.includeHsn ? `<th class="c" style="width:72px">HSN/SAC</th>` : ""}
      <th class="r" style="width:100px">Qty</th><th class="r" style="width:104px">Rate</th>
      ${cfg.includeDiscount ? `<th class="c" style="width:54px">Disc</th>` : ""}
      <th class="r" style="width:110px">Amount</th>
    </tr></thead>
    <tbody>${items || `<tr><td colspan="${colspan}" style="text-align:center;color:#9ca3af;padding:26px">No items</td></tr>`}</tbody>
  </table>
  <div class="tw"><div class="tt">
    <div class="row"><span>Subtotal</span><span>${_fmt(netTotal, currency)}</span></div>
    ${(doc.taxes || []).map(t => `<div class="row"><span>${_esc(t.description || t.account_head)}</span><span>${_fmt(t.tax_amount || 0, currency)}</span></div>`).join("")}
    ${doc.discount_amount ? `<div class="row"><span style="color:#dc2626">Discount</span><span style="color:#dc2626">− ${_fmt(doc.discount_amount, currency)}</span></div>` : ""}
    <div class="grand"><span>Total Due</span><span>${_fmt(doc.grand_total, currency)}</span></div>
  </div></div>
  ${doc.remarks ? `<div class="notes"><div class="h">Remarks</div>${_esc(doc.remarks)}</div>` : ""}
  ${doc.terms || doc.customer_note ? `<div class="notes"><div class="h">${doc.customer_note ? "Note" : "Terms & Conditions"}</div>${_esc(doc.customer_note || doc.terms)}</div>` : ""}
  <div class="sig"><div>Prepared By</div><div>Authorised Signatory</div><div>Receiver's Signature</div></div>
  <div class="ft">${_esc(doc.company || "")} · ${_esc(doc.name)} · Printed ${_today()}</div>
</div></body></html>`;
}


// ── Public API ────────────────────────────────────────────────────────────────
export function useLivePreview() {
  function setCompany(c)    { return _loadBranding(c); }
  function refreshBranding() { return _loadBranding(_state.company); }
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

  return { state: _state, template, brandColor, logo, setCompany, refreshBranding, renderDocument, printDoc };
}