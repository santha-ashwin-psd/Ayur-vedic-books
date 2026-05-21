// Shared print-template renderer for all transactional documents.
// Three templates (classic / modern / minimal) driven by a small doc config so
// Invoice, Bill, Quote, SO, PO, CN, DN can all reuse the same HTML.
//
// Branding (template + brand color + logo) is persisted to localStorage per
// company so users only pick once.

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
      _state.template = b.template || "classic";
      _state.brandColor = b.brandColor || "#1a6ef7";
      _state.logo = b.logo || "";
    } else {
      _state.template = "classic";
      _state.brandColor = "#1a6ef7";
      _state.logo = "";
    }
  } catch {}
  _state.company = company;
}

function _saveBranding() {
  if (!_state.company) return;
  localStorage.setItem("books_branding_" + _state.company, JSON.stringify({
    template: _state.template,
    brandColor: _state.brandColor,
    logo: _state.logo,
  }));
}

function _esc(s) {
  return String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
}
function _fmt(v) {
  return "₹" + Number(v || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

// `config` describes the doctype: { title, partyLabel, partyAddrLabel, fields, columns, includeDiscount, includeHsn }
function _renderClassic(doc, cfg) {
  const brand = _state.brandColor;
  const logo = _state.logo;
  const items = (doc.items || []).map((it, i) => `
    <tr>
      <td>${i + 1}. <strong>${_esc(it.item_name || it.item_code)}</strong>${it.description ? `<div style="color:#6b7280;font-size:11px">${_esc(it.description)}</div>` : ""}</td>
      ${cfg.includeHsn ? `<td>${_esc(it.gst_hsn_code || it.hsn || "")}</td>` : ""}
      <td style="text-align:right">${Number(it.qty || 0)}</td>
      <td style="text-align:right">${_fmt(it.rate)}</td>
      ${cfg.includeDiscount ? `<td style="text-align:right">${Number(it.discount_percentage || 0)}%</td>` : ""}
      <td style="text-align:right;font-family:monospace;font-weight:600">${_fmt(it.amount)}</td>
    </tr>`).join("");
  const taxes = (doc.taxes || []).map(t => `
    <tr><td colspan="${cfg.includeHsn ? (cfg.includeDiscount ? 5 : 4) : (cfg.includeDiscount ? 4 : 3)}" style="text-align:right;color:#6b7280">${_esc(t.description || t.account_head)}</td><td style="text-align:right;font-family:monospace">${_fmt(t.tax_amount || 0)}</td></tr>
  `).join("");
  return `<!DOCTYPE html><html><head><meta charset="utf-8"/><title>${cfg.title}</title>
<style>body{font-family:Inter,system-ui,sans-serif;color:#111827;margin:0;padding:36px 48px;background:#fff;font-size:13px}
.head{display:flex;justify-content:space-between;align-items:flex-start;padding-bottom:18px;border-bottom:3px solid ${brand};margin-bottom:22px}
.brand{font-size:22px;font-weight:800;color:${brand}}
.chip{background:${brand};color:#fff;padding:4px 10px;border-radius:999px;font-size:11px;font-weight:600;display:inline-block}
.docnum{font-size:24px;font-weight:800;color:#111827;margin-top:6px}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:14px;margin-bottom:18px;font-size:12px}
.lbl{color:#6b7280;text-transform:uppercase;font-size:10.5px;font-weight:700;letter-spacing:.04em}
.val{color:#111827;font-weight:600;margin-top:2px}
table{width:100%;border-collapse:collapse;font-size:12.5px;margin-bottom:16px}
th{background:#f1f5f9;text-align:left;padding:9px;font-size:10.5px;text-transform:uppercase;color:#475569;font-weight:700;border-bottom:1px solid #cbd5e1}
td{padding:9px;border-bottom:1px solid #f1f5f9}
.totals{margin-left:auto;width:280px;font-size:13px}
.totals tr td{border:none;padding:5px 0}
.totals .grand td{border-top:2px solid ${brand};padding-top:8px;font-weight:700;color:${brand};font-size:15px}
.notes{margin-top:24px;padding:14px;border-radius:8px;background:#f8fafc;font-size:12px;color:#374151;line-height:1.5}
</style></head><body>
<div class="head">
  <div>${logo ? `<img src="${_esc(logo)}" style="max-height:48px;margin-bottom:8px"/>` : ""}<div class="brand">${_esc(doc.company || cfg.companyName || "")}</div></div>
  <div style="text-align:right"><span class="chip">${cfg.title}</span><div class="docnum">${_esc(doc.name || "")}</div></div>
</div>
<div class="grid">
  <div><div class="lbl">${cfg.partyLabel}</div><div class="val">${_esc(doc[cfg.partyField] || "")}</div>${doc.address_display ? `<div style="color:#6b7280;font-size:11px;margin-top:3px;white-space:pre-line">${_esc(doc.address_display)}</div>` : ""}</div>
  <div><div class="lbl">Date</div><div class="val">${_esc(doc.posting_date || doc.transaction_date || "")}</div>${doc.due_date ? `<div class="lbl" style="margin-top:8px">Due Date</div><div class="val">${_esc(doc.due_date)}</div>` : ""}${doc.valid_till ? `<div class="lbl" style="margin-top:8px">Valid Till</div><div class="val">${_esc(doc.valid_till)}</div>` : ""}</div>
  <div>${doc.po_no ? `<div class="lbl">PO Number</div><div class="val">${_esc(doc.po_no)}</div>` : ""}${doc.place_of_supply ? `<div class="lbl" style="margin-top:8px">Place of Supply</div><div class="val">${_esc(doc.place_of_supply)}</div>` : ""}</div>
</div>
<table>
  <thead><tr><th>Item</th>${cfg.includeHsn ? "<th>HSN/SAC</th>" : ""}<th style="text-align:right">Qty</th><th style="text-align:right">Rate</th>${cfg.includeDiscount ? `<th style="text-align:right">Disc</th>` : ""}<th style="text-align:right">Amount</th></tr></thead>
  <tbody>${items || `<tr><td colspan="6" style="text-align:center;color:#9ca3af;padding:24px">No items</td></tr>`}</tbody>
</table>
<table class="totals"><tbody>
  <tr><td>Subtotal</td><td style="text-align:right;font-family:monospace">${_fmt((doc.grand_total || 0) - (doc.total_taxes_and_charges || 0))}</td></tr>
  ${taxes}
  <tr class="grand"><td>Grand Total</td><td style="text-align:right;font-family:monospace">${_fmt(doc.grand_total)}</td></tr>
</tbody></table>
${doc.customer_note || doc.terms ? `<div class="notes"><strong>${doc.customer_note ? "Customer Note" : "Terms & Conditions"}:</strong><br/>${_esc(doc.customer_note || doc.terms)}</div>` : ""}
</body></html>`;
}

function _renderModern(doc, cfg) {
  const brand = _state.brandColor;
  const logo = _state.logo;
  const items = (doc.items || []).map((it) => `
    <tr>
      <td><strong>${_esc(it.item_name || it.item_code)}</strong>${it.description ? `<div style="color:#94a3b8;font-size:11px">${_esc(it.description)}</div>` : ""}</td>
      <td style="text-align:right">${Number(it.qty || 0)}</td>
      <td style="text-align:right">${_fmt(it.rate)}</td>
      <td style="text-align:right;font-family:monospace;font-weight:700">${_fmt(it.amount)}</td>
    </tr>`).join("");
  return `<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>body{font-family:Inter,system-ui,sans-serif;color:#0f172a;margin:0;padding:44px 56px;background:#fff;font-size:13px}
.head{display:flex;justify-content:space-between;border-bottom:1px solid #e2e8f0;padding-bottom:24px;margin-bottom:24px}
.title{font-size:30px;font-weight:300;letter-spacing:.08em;color:${brand};text-transform:uppercase}
.num{font-family:monospace;font-size:15px;color:#475569;margin-top:6px}
.parties{display:grid;grid-template-columns:1fr 1fr;gap:32px;margin-bottom:28px;font-size:13px}
.lbl{color:#94a3b8;text-transform:uppercase;font-size:10px;letter-spacing:.08em;margin-bottom:4px}
.val{font-weight:600;color:#0f172a}
table{width:100%;border-collapse:collapse;font-size:13px}
th{text-align:left;color:#94a3b8;text-transform:uppercase;font-size:10px;letter-spacing:.08em;font-weight:600;padding:10px 8px;border-bottom:1px solid #e2e8f0}
td{padding:12px 8px;border-bottom:1px solid #f1f5f9}
.totals{margin-top:18px;display:flex;justify-content:flex-end}
.totals-tbl td{padding:4px 16px;border:none}
.totals-tbl .grand td{border-top:2px solid ${brand};padding-top:10px;font-size:16px;font-weight:700;color:${brand}}
.notes{margin-top:28px;font-size:12px;color:#64748b;line-height:1.6;border-top:1px solid #e2e8f0;padding-top:14px}
</style></head><body>
<div class="head">
  <div>${logo ? `<img src="${_esc(logo)}" style="max-height:42px;margin-bottom:10px"/>` : ""}<div style="font-size:14px;font-weight:700">${_esc(doc.company || cfg.companyName || "")}</div></div>
  <div style="text-align:right"><div class="title">${cfg.title}</div><div class="num">${_esc(doc.name || "")}</div></div>
</div>
<div class="parties">
  <div><div class="lbl">${cfg.partyLabel}</div><div class="val">${_esc(doc[cfg.partyField] || "")}</div>${doc.address_display ? `<div style="color:#64748b;font-size:12px;margin-top:4px;white-space:pre-line">${_esc(doc.address_display)}</div>` : ""}</div>
  <div style="text-align:right">
    <div class="lbl">Date</div><div class="val">${_esc(doc.posting_date || doc.transaction_date || "")}</div>
    ${doc.due_date ? `<div class="lbl" style="margin-top:10px">Due</div><div class="val">${_esc(doc.due_date)}</div>` : ""}
    ${doc.valid_till ? `<div class="lbl" style="margin-top:10px">Valid Till</div><div class="val">${_esc(doc.valid_till)}</div>` : ""}
  </div>
</div>
<table>
  <thead><tr><th>Item</th><th style="text-align:right">Qty</th><th style="text-align:right">Rate</th><th style="text-align:right">Amount</th></tr></thead>
  <tbody>${items || `<tr><td colspan="4" style="text-align:center;color:#94a3b8;padding:28px">No items</td></tr>`}</tbody>
</table>
<div class="totals">
  <table class="totals-tbl">
    <tr><td>Subtotal</td><td style="text-align:right;font-family:monospace">${_fmt((doc.grand_total || 0) - (doc.total_taxes_and_charges || 0))}</td></tr>
    ${(doc.taxes || []).map(t => `<tr><td>${_esc(t.description || t.account_head)}</td><td style="text-align:right;font-family:monospace">${_fmt(t.tax_amount || 0)}</td></tr>`).join("")}
    <tr class="grand"><td>Total</td><td style="text-align:right;font-family:monospace">${_fmt(doc.grand_total)}</td></tr>
  </table>
</div>
${doc.customer_note || doc.terms ? `<div class="notes">${_esc(doc.customer_note || doc.terms)}</div>` : ""}
</body></html>`;
}

function _renderMinimal(doc, cfg) {
  const brand = _state.brandColor;
  const items = (doc.items || []).map((it) => `
    <tr>
      <td>${_esc(it.item_name || it.item_code)}</td>
      <td style="text-align:right">${Number(it.qty || 0)} × ${_fmt(it.rate)}</td>
      <td style="text-align:right;font-family:Georgia,serif">${_fmt(it.amount)}</td>
    </tr>`).join("");
  return `<!DOCTYPE html><html><head><meta charset="utf-8"/>
<style>body{font-family:Georgia,'Times New Roman',serif;color:#1f2937;margin:0;padding:60px 72px;background:#fff;font-size:13px;line-height:1.7}
.title{text-align:center;font-size:32px;font-weight:400;letter-spacing:.3em;color:${brand};margin-bottom:8px}
.subtitle{text-align:center;color:#9ca3af;font-size:13px;letter-spacing:.1em;margin-bottom:32px}
hr{border:none;border-top:1px solid #e5e7eb;margin:24px 0}
.meta{display:grid;grid-template-columns:1fr 1fr;gap:24px;font-size:13px;margin-bottom:24px}
.lbl{color:#6b7280;font-style:italic}
.val{margin-left:8px;font-weight:600}
table{width:100%;border-collapse:collapse;font-size:13px}
th,td{padding:10px 0;border-bottom:1px solid #f3f4f6;text-align:left}
th{font-style:italic;color:#9ca3af;font-weight:400}
.total-line{display:flex;justify-content:space-between;border-top:2px solid ${brand};padding-top:14px;margin-top:14px;font-size:18px;font-weight:700;color:${brand}}
.notes{margin-top:36px;font-size:13px;color:#374151;font-style:italic;text-align:center}
</style></head><body>
<div class="title">${cfg.title}</div>
<div class="subtitle">${_esc(doc.name || "")}</div>
<hr/>
<div class="meta">
  <div><span class="lbl">${cfg.partyLabel}:</span><span class="val">${_esc(doc[cfg.partyField] || "")}</span></div>
  <div style="text-align:right"><span class="lbl">Date:</span><span class="val">${_esc(doc.posting_date || doc.transaction_date || "")}</span></div>
  ${doc.due_date ? `<div><span class="lbl">Due:</span><span class="val">${_esc(doc.due_date)}</span></div>` : ""}
  ${doc.valid_till ? `<div><span class="lbl">Valid Till:</span><span class="val">${_esc(doc.valid_till)}</span></div>` : ""}
</div>
<table>
  <thead><tr><th>Item</th><th style="text-align:right">Quantity × Rate</th><th style="text-align:right">Amount</th></tr></thead>
  <tbody>${items || `<tr><td colspan="3" style="text-align:center;color:#9ca3af;padding:28px;font-style:italic">No items</td></tr>`}</tbody>
</table>
<div class="total-line"><span>Total Due</span><span style="font-family:Georgia,serif">${_fmt(doc.grand_total)}</span></div>
${doc.customer_note || doc.terms ? `<div class="notes">${_esc(doc.customer_note || doc.terms)}</div>` : ""}
</body></html>`;
}

export function useLivePreview() {
  function setCompany(c) { _loadBranding(c); }
  function setTemplate(t) { _state.template = t; _saveBranding(); }
  function setBrandColor(c) { _state.brandColor = c; _saveBranding(); }
  function setLogo(l) { _state.logo = l; _saveBranding(); }

  function renderDocument(doc, config) {
    const cfg = {
      title: "INVOICE",
      partyLabel: "Bill To",
      partyField: "customer_name",
      companyName: "",
      includeHsn: true,
      includeDiscount: true,
      ...config,
    };
    if (_state.template === "modern") return _renderModern(doc, cfg);
    if (_state.template === "minimal") return _renderMinimal(doc, cfg);
    return _renderClassic(doc, cfg);
  }

  const template = computed({ get: () => _state.template, set: setTemplate });
  const brandColor = computed({ get: () => _state.brandColor, set: setBrandColor });
  const logo = computed({ get: () => _state.logo, set: setLogo });

  return { state: _state, template, brandColor, logo, setCompany, renderDocument };
}
