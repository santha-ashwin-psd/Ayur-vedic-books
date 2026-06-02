<template>
  <div class="g3-page">
    <div class="g3-topbar">
      <div>
        <div class="g3-title">GSTR-3B</div>
        <div class="g3-subtitle">Monthly Self-Declaration Return</div>
      </div>
      <div class="g3-controls">
        <select v-model="period" class="g3-select">
          <option v-for="p in periods" :key="p.v" :value="p.v">{{ p.l }}</option>
        </select>
        <button class="g3-btn-ghost" @click="load" :disabled="loading"><span v-html="icon('refresh',13)"></span></button>
        <button v-if="data" class="g3-btn-ghost" @click="exportCSV"><span v-html="icon('download',13)"></span> CSV</button>
        <button class="g3-btn-primary" @click="load" :disabled="loading">Compute</button>
      </div>
    </div>

    <!-- Filing deadline -->
    <div class="g3-deadline" :class="dueSoon ? 'due-warn' : 'due-ok'">
      <span v-html="icon('calendar',13)"></span>
      GSTR-3B for <strong>{{ periodLabel }}</strong> is due by
      <strong>{{ dueDate }}</strong>
      <span v-if="dueSoon"> — deadline within 7 days</span>
    </div>

    <div v-if="loading" class="g3-card" style="padding:20px">
      <div v-for="n in 6" :key="n" class="g3-shimmer" style="margin-bottom:10px"></div>
    </div>

    <template v-else-if="data">
      <!-- 3.1 Outward Supplies -->
      <div class="g3-card">
        <div class="g3-card-header">
          3.1 Details of Outward Supplies and Inward Supplies Liable to Reverse Charge
          <span class="g3-meta">Based on {{ data.invoice_count || 0 }} invoices</span>
        </div>
        <table class="g3-table">
          <thead><tr>
            <th>Nature of Supplies</th>
            <th class="ta-r">Total Taxable Value</th>
            <th class="ta-r">IGST</th><th class="ta-r">CGST</th><th class="ta-r">SGST / UTGST</th><th class="ta-r">Cess</th>
          </tr></thead>
          <tbody>
            <tr class="g3-row">
              <td><span class="g3-sec-lbl">(a)</span> Outward taxable supplies (other than zero rated, nil rated and exempted)</td>
              <td class="ta-r mono-sm">{{ fmtCur(data.taxable_value) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(data.out_igst) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(data.out_cgst) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(data.out_sgst) }}</td>
              <td class="ta-r mono-sm text-muted">—</td>
            </tr>
            <tr class="g3-row">
              <td><span class="g3-sec-lbl">(b)</span> Outward taxable supplies — zero rated <span class="g3-note">export / SEZ without payment of tax</span></td>
              <td class="ta-r mono-sm text-muted">0.00</td>
              <td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td>
            </tr>
            <tr class="g3-row">
              <td><span class="g3-sec-lbl">(c)</span> Other outward supplies — nil rated, exempted</td>
              <td class="ta-r mono-sm text-muted">0.00</td>
              <td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td>
            </tr>
            <tr class="g3-row">
              <td><span class="g3-sec-lbl">(d)</span> Inward supplies liable to reverse charge</td>
              <td class="ta-r mono-sm text-muted">0.00</td>
              <td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td>
            </tr>
            <tr class="g3-row g3-total">
              <td><strong>Total Outward Tax Liability</strong></td>
              <td class="ta-r mono-sm"><strong>{{ fmtCur(data.taxable_value) }}</strong></td>
              <td class="ta-r mono-sm red"><strong>{{ fmtCur(data.out_igst) }}</strong></td>
              <td class="ta-r mono-sm red"><strong>{{ fmtCur(data.out_cgst) }}</strong></td>
              <td class="ta-r mono-sm red"><strong>{{ fmtCur(data.out_sgst) }}</strong></td>
              <td class="ta-r mono-sm text-muted">—</td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 4 ITC -->
      <div class="g3-card">
        <div class="g3-card-header">
          4 Eligible ITC (Input Tax Credit)
          <span class="g3-meta">From {{ data.itc_invoice_count || 0 }} purchase invoices</span>
        </div>
        <table class="g3-table">
          <thead><tr><th>Details</th><th class="ta-r">IGST</th><th class="ta-r">CGST</th><th class="ta-r">SGST / UTGST</th></tr></thead>
          <tbody>
            <tr class="g3-row">
              <td>(A) ITC Available — all other ITC (B2B Purchases)</td>
              <td class="ta-r mono-sm">{{ fmtCur(data.itc_igst) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(data.itc_cgst) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(data.itc_sgst) }}</td>
            </tr>
            <tr class="g3-row">
              <td>(B) ITC Reversed — rule 42 &amp; 43 / others <span class="g3-note">enter manually if applicable</span></td>
              <td class="ta-r mono-sm text-muted">0.00</td>
              <td class="ta-r mono-sm text-muted">0.00</td>
              <td class="ta-r mono-sm text-muted">0.00</td>
            </tr>
            <tr class="g3-row g3-total">
              <td><strong>Net ITC Available</strong></td>
              <td class="ta-r mono-sm blue"><strong>{{ fmtCur(data.itc_igst) }}</strong></td>
              <td class="ta-r mono-sm blue"><strong>{{ fmtCur(data.itc_cgst) }}</strong></td>
              <td class="ta-r mono-sm blue"><strong>{{ fmtCur(data.itc_sgst) }}</strong></td>
            </tr>
          </tbody>
        </table>
      </div>

      <!-- 5.1 Net Tax Payable -->
      <div class="g3-card">
        <div class="g3-card-header">5.1 Tax Payable and Paid</div>
        <div class="g3-tax-summary">
          <div class="g3-tax-row"><span>Total Output Tax Liability</span><span class="mono-sm red">{{ fmtCur(data.total_output) }}</span></div>
          <div class="g3-tax-row"><span>Less: Input Tax Credit (ITC)</span><span class="mono-sm green">{{ fmtCur(data.total_itc) }}</span></div>
          <div class="g3-tax-divider"></div>
          <div class="g3-tax-row g3-tax-total">
            <span><strong>Net Tax Payable</strong></span>
            <span class="mono-sm" :class="netTax >= 0 ? 'red' : 'green'"><strong>{{ fmtCur(netTax) }}</strong></span>
          </div>
          <div v-if="netTax < 0" class="g3-refund-note">
            <span v-html="icon('info',12)"></span> Refund eligible — ITC exceeds output tax liability
          </div>
        </div>
      </div>

      <!-- Tax type breakdown -->
      <div v-if="data.net_by_type && data.net_by_type.length" class="g3-card">
        <div class="g3-card-header">Tax Type Breakdown</div>
        <table class="g3-table">
          <thead><tr><th>Tax Type</th><th class="ta-r">Output</th><th class="ta-r">ITC</th><th class="ta-r">Net Payable</th></tr></thead>
          <tbody>
            <tr v-for="row in data.net_by_type" :key="row.tax_type" class="g3-row">
              <td><span class="g3-badge">{{ row.tax_type || '—' }}</span></td>
              <td class="ta-r mono-sm">{{ fmtCur(row.output) }}</td>
              <td class="ta-r mono-sm green">{{ fmtCur(row.itc) }}</td>
              <td class="ta-r mono-sm" :class="row.net >= 0 ? 'red' : 'green'">{{ fmtCur(row.net) }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-else class="g3-placeholder">
      <div class="g3-ph-icon" v-html="icon('gstfile', 40)"></div>
      <div class="g3-ph-text">Select a period and click Compute to view GSTR-3B</div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { apiGET, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt } from "../utils/format.js";

const { toast } = useToast();
const loading = ref(false);
const data = ref(null);

const now = new Date();
function makePeriods() {
  const ps = [];
  for (let i = 0; i < 12; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const v = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
    const l = d.toLocaleString("en-IN", { month: "long", year: "numeric" });
    ps.push({ v, l });
  }
  return ps;
}
const periods = makePeriods();
const period = ref(periods[0].v);

const periodLabel = computed(() => periods.find(p => p.v === period.value)?.l || period.value);
const dueDate = computed(() => {
  const [yr, mo] = period.value.split("-");
  const due = new Date(+yr, +mo, 20); // 20th of next month
  return due.toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" });
});
const dueSoon = computed(() => {
  const [yr, mo] = period.value.split("-");
  const due = new Date(+yr, +mo, 20);
  const diff = (due - now) / (1000 * 60 * 60 * 24);
  return diff >= 0 && diff <= 7;
});

async function load() {
  loading.value = true;
  data.value = null;
  try {
    const co = await resolveCompany();
    const [yr, mo] = period.value.split("-");
    const from = `${yr}-${mo}-01`;
    const last = new Date(+yr, +mo, 0).getDate();
    const to = `${yr}-${mo}-${String(last).padStart(2, "0")}`;

    const summary = await apiGET("zoho_books_clone.db.queries.get_gstr_summary", {
      company: co, from_date: from, to_date: to,
    });

    const byType = (list, type) => flt((list || []).find(r => r.tax_type === type)?.amount);

    data.value = {
      taxable_value: flt(summary?.taxable_value),
      out_igst: byType(summary?.output, "IGST"),
      out_cgst: byType(summary?.output, "CGST"),
      out_sgst: byType(summary?.output, "SGST"),
      itc_igst: byType(summary?.itc, "IGST"),
      itc_cgst: byType(summary?.itc, "CGST"),
      itc_sgst: byType(summary?.itc, "SGST"),
      total_output: flt(summary?.totals?.total_output),
      total_itc: flt(summary?.totals?.total_itc),
      net_by_type: summary?.net_by_type || [],
      invoice_count: (summary?.output || []).reduce((s, r) => s + (r.invoice_count || 0), 0),
      itc_invoice_count: (summary?.itc || []).reduce((s, r) => s + (r.invoice_count || 0), 0),
    };
  } catch (e) {
    toast.error(e.message || "Failed to compute GSTR-3B");
  } finally {
    loading.value = false;
  }
}

const netTax = computed(() => data.value ? flt(data.value.total_output) - flt(data.value.total_itc) : 0);

function exportCSV() {
  if (!data.value) return;
  const d = data.value;
  const rows = [
    ["GSTR-3B Summary", period.value],
    [],
    ["Section", "Description", "IGST", "CGST", "SGST"],
    ["3.1(a)", "Outward Taxable Supplies", d.out_igst, d.out_cgst, d.out_sgst],
    ["3.1(b)", "Zero Rated", 0, 0, 0],
    ["3.1(c)", "Nil/Exempted", 0, 0, 0],
    ["3.1(d)", "Reverse Charge", 0, 0, 0],
    [],
    ["4(A)", "ITC Available", d.itc_igst, d.itc_cgst, d.itc_sgst],
    ["4(B)", "ITC Reversed", 0, 0, 0],
    [],
    ["5.1", "Output Tax", d.total_output, "", ""],
    ["5.1", "Less ITC", d.total_itc, "", ""],
    ["5.1", "Net Tax Payable", netTax.value, "", ""],
  ];
  const csv = rows.map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
  const a = document.createElement("a");
  a.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
  a.download = `GSTR-3B_${period.value}.csv`;
  a.click();
}

function fmtCur(v) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v));
}

onMounted(load);
</script>

<style scoped>
.g3-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.g3-topbar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;}
.g3-title{font-size:20px;font-weight:800;color:#111827;}.g3-subtitle{font-size:12px;color:#6b7280;}
.g3-controls{display:flex;align-items:center;gap:8px;}
.g3-select{border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.g3-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.g3-btn-primary:hover{background:#1d4ed8;}.g3-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.g3-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;font-weight:600;color:#374151;cursor:pointer;}
.g3-btn-ghost:hover:not(:disabled){background:#f9fafb;}.g3-btn-ghost:disabled{opacity:.5;}
.g3-deadline{display:flex;align-items:center;gap:8px;border-radius:8px;padding:10px 14px;font-size:12.5px;}
.due-ok{background:#f0fdf4;border:1px solid #bbf7d0;color:#166534;}
.due-warn{background:#fffbeb;border:1px solid #fde68a;color:#92400e;}
.g3-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.g3-card-header{padding:12px 16px;font-size:12.5px;font-weight:700;color:#374151;border-bottom:1px solid #e5e7eb;background:#f9fafb;display:flex;align-items:center;gap:8px;}
.g3-meta{font-size:11px;color:#9ca3af;font-weight:400;margin-left:auto;}
.g3-table{width:100%;border-collapse:collapse;font-size:12.5px;}
.g3-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:9px 12px;font-size:11px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.ta-r{text-align:right!important;}
.g3-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;}
.g3-row:last-child td{border-bottom:none;}
.g3-row.g3-total td{background:#f9fafb;}
.g3-sec-lbl{font-weight:700;color:#374151;margin-right:6px;}
.g3-note{font-size:11px;color:#9ca3af;font-weight:400;margin-left:4px;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}.blue{color:#2563eb!important;}
.g3-badge{background:#eff6ff;color:#2563eb;border-radius:10px;padding:2px 8px;font-size:11.5px;font-weight:600;}
.g3-tax-summary{display:flex;flex-direction:column;padding:0 16px;}
.g3-tax-row{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #f3f4f6;font-size:13.5px;}
.g3-tax-divider{height:2px;background:#e5e7eb;margin:4px 0;}
.g3-tax-total{font-size:15px;}
.g3-refund-note{display:flex;align-items:center;gap:6px;font-size:12px;color:#16a34a;padding:8px 0;}
.g3-placeholder{display:flex;flex-direction:column;align-items:center;gap:12px;padding:60px;color:#9ca3af;}
.g3-ph-icon{opacity:.3;}.g3-ph-text{font-size:13.5px;}
.g3-shimmer{height:14px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
