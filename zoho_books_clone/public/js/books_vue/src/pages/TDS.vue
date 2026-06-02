<template>
  <div class="tds-page">
    <div class="tds-topbar">
      <div>
        <div class="tds-title">TDS</div>
        <div class="tds-subtitle">Tax Deducted at Source — Purchase Invoice Deductions</div>
      </div>
      <div class="tds-controls">
        <div class="tds-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search by party or section…" class="tds-search-input" /></div>
        <select v-model="periodFilter" class="tds-select" @change="load">
          <option value="">All Periods</option>
          <option v-for="p in periods" :key="p.v" :value="p.v">{{ p.l }}</option>
        </select>
        <button class="tds-btn-ghost" @click="load" :disabled="loading"><span v-html="icon('refresh',14)"></span></button>
        <button v-if="list.length" class="tds-btn-ghost" @click="exportCSV"><span v-html="icon('download',13)"></span> CSV</button>
      </div>
    </div>

    <div v-if="!loading && noTdsNote" class="tds-note">
      <span v-html="icon('info',14)"></span>
      No TDS deductions found. TDS transactions appear here when a Purchase Invoice has a tax line with "TDS", "194C", "194J" etc. in the description.
    </div>

    <div class="tds-summary" v-if="!loading">
      <div class="tds-sum-card"><div class="tds-sum-lbl">Total Deductions</div><div class="tds-sum-val">{{ list.length }}</div></div>
      <div class="tds-sum-card"><div class="tds-sum-lbl">Total TDS Deducted</div><div class="tds-sum-val red">{{ fmtCur(totalTds) }}</div></div>
      <div class="tds-sum-card"><div class="tds-sum-lbl">Gross Payment</div><div class="tds-sum-val">{{ fmtCur(totalGross) }}</div></div>
      <div class="tds-sum-card"><div class="tds-sum-lbl">Net Payment</div><div class="tds-sum-val blue">{{ fmtCur(totalNet) }}</div></div>
    </div>

    <!-- Section-wise breakdown -->
    <div v-if="!loading && sectionBreakdown.length > 1" class="tds-sections">
      <div class="tds-sections-title">Section-wise Breakdown</div>
      <div class="tds-sections-grid">
        <div v-for="s in sectionBreakdown" :key="s.section" class="tds-sec-card">
          <div class="tds-sec-label"><span class="tds-sec-badge">{{ s.section }}</span></div>
          <div class="tds-sec-count">{{ s.count }} transaction{{ s.count > 1 ? 's' : '' }}</div>
          <div class="tds-sec-amount">{{ fmtCur(s.amount) }}</div>
        </div>
      </div>
    </div>

    <div class="tds-card">
      <table class="tds-table">
        <thead><tr>
          <th @click="sort('name')" class="sortable">Voucher # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
          <th>Party</th>
          <th>TDS Section</th>
          <th class="ta-r">Gross Amount</th>
          <th class="ta-r">TDS Rate %</th>
          <th class="ta-r">TDS Amount</th>
          <th class="ta-r">Net Payment</th>
        </tr></thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="8"><div class="tds-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="e in sorted" :key="e.name + (e.tds_section||'')" class="tds-row">
              <td><span class="tds-code">{{ e.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(e.posting_date) }}</td>
              <td>{{ e.supplier_name || e.supplier || '—' }}</td>
              <td><span class="tds-section-badge">{{ e.tds_section || e.tax_type || '—' }}</span></td>
              <td class="ta-r mono-sm">{{ fmtCur(e.gross_amount) }}</td>
              <td class="ta-r mono-sm text-muted">{{ e.rate ? `${e.rate}%` : '—' }}</td>
              <td class="ta-r mono-sm red">{{ fmtCur(e.tds_amount) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(e.net_payment) }}</td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="tds-empty">No TDS transactions found</td></tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { apiGET, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";

const { toast } = useToast();
const list = ref([]);
const loading = ref(false);
const search = ref("");
const periodFilter = ref("");
const sortCol = ref("posting_date");
const sortDir = ref("desc");
const noTdsNote = ref(false);

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

async function load() {
  loading.value = true;
  noTdsNote.value = false;
  try {
    const co = await resolveCompany();
    const params = { company: co };
    if (periodFilter.value) {
      const [yr, mo] = periodFilter.value.split("-");
      params.from_date = `${yr}-${mo}-01`;
      params.to_date   = `${yr}-${mo}-${new Date(+yr, +mo, 0).getDate()}`;
    }
    const rows = await apiGET("zoho_books_clone.db.queries.get_tds_transactions", params);
    list.value = Array.isArray(rows) ? rows : (rows?.message || []);
    if (!list.value.length) noTdsNote.value = true;
  } catch (e) {
    toast.error(e.message || "Failed to load TDS data");
  } finally {
    loading.value = false;
  }
}

const totalTds   = computed(() => list.value.reduce((s, e) => s + flt(e.tds_amount), 0));
const totalGross = computed(() => list.value.reduce((s, e) => s + flt(e.gross_amount), 0));
const totalNet   = computed(() => list.value.reduce((s, e) => s + flt(e.net_payment), 0));

const sectionBreakdown = computed(() => {
  const map = {};
  list.value.forEach(e => {
    const sec = e.tds_section || e.tax_type || "Unknown";
    if (!map[sec]) map[sec] = { section: sec, count: 0, amount: 0 };
    map[sec].count++;
    map[sec].amount += flt(e.tds_amount);
  });
  return Object.values(map).sort((a, b) => b.amount - a.amount);
});

const filtered = computed(() => {
  if (!search.value.trim()) return list.value;
  const q = search.value.toLowerCase();
  return list.value.filter(e =>
    (e.supplier_name || e.supplier || "").toLowerCase().includes(q) ||
    (e.tds_section || e.tax_type || "").toLowerCase().includes(q)
  );
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const av = a[col] ?? "", bv = b[col] ?? "";
    const c = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv));
    return sortDir.value === "asc" ? c : -c;
  });
});

function sort(col) {
  if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  else { sortCol.value = col; sortDir.value = "asc"; }
}
function sortArrow(col) {
  if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>';
  return sortDir.value === "asc" ? "↑" : "↓";
}

function exportCSV() {
  const rows = [
    ["Voucher #", "Date", "Party", "TDS Section", "Gross Amount", "TDS Rate %", "TDS Amount", "Net Payment"],
    ...sorted.value.map(e => [
      e.name, e.posting_date,
      e.supplier_name || e.supplier || "",
      e.tds_section || e.tax_type || "",
      flt(e.gross_amount), e.rate || "",
      flt(e.tds_amount), flt(e.net_payment),
    ]),
  ];
  const csv = rows.map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
  const a = document.createElement("a");
  a.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
  a.download = `TDS_${periodFilter.value || "all"}.csv`;
  a.click();
}

function fmtCur(v) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v));
}

onMounted(load);
</script>

<style scoped>
.tds-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.tds-topbar{display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:12px;}
.tds-title{font-size:20px;font-weight:800;color:#111827;}.tds-subtitle{font-size:12px;color:#6b7280;}
.tds-controls{display:flex;align-items:center;gap:8px;flex-wrap:wrap;}
.tds-search-wrap{display:flex;align-items:center;gap:6px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:6px 10px;min-width:200px;}
.tds-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.tds-select{border:1px solid #e5e7eb;border-radius:8px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.tds-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.tds-btn-ghost:hover:not(:disabled){background:#f9fafb;}.tds-btn-ghost:disabled{opacity:.5;cursor:not-allowed;}
.tds-note{display:flex;align-items:flex-start;gap:8px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:12px 16px;font-size:12.5px;color:#1e40af;line-height:1.55;}
.tds-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.tds-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.tds-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.tds-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.blue{color:#2563eb!important;}.red{color:#dc2626!important;}
.tds-sections{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.tds-sections-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;margin-bottom:10px;}
.tds-sections-grid{display:flex;gap:10px;flex-wrap:wrap;}
.tds-sec-card{background:#f9fafb;border:1px solid #e5e7eb;border-radius:8px;padding:10px 14px;min-width:140px;}
.tds-sec-label{margin-bottom:4px;}
.tds-sec-badge{background:#eff6ff;color:#2563eb;border-radius:10px;padding:2px 10px;font-size:11.5px;font-weight:700;}
.tds-sec-count{font-size:11.5px;color:#6b7280;margin-top:4px;}
.tds-sec-amount{font-size:14px;font-weight:700;color:#dc2626;font-family:monospace;margin-top:2px;}
.tds-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.tds-table{width:100%;border-collapse:collapse;font-size:13px;}
.tds-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;text-transform:uppercase;}
.tds-table th.sortable{cursor:pointer;user-select:none;}.tds-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.tds-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;}
.tds-row:last-child td{border-bottom:none;}.tds-row:hover td{background:#f9fafb;}
.tds-code{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.tds-section-badge{background:#eff6ff;color:#2563eb;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.tds-empty{text-align:center;color:#9ca3af;padding:48px!important;}
.tds-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
