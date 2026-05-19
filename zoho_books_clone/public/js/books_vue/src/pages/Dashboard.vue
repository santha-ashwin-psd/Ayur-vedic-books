<template>
  <div class="dashboard">

    <!-- KPI row -->
    <div class="kpi-grid">
      <div v-for="kpi in kpiCards" :key="kpi.key" class="books-card kpi-card" :class="{ 'kpi-card--link': kpi.route }" @click="kpi.route && navTo(kpi.route)">
        <div class="kpi-icon" :style="{ background: kpi.iconBg }">
          <span v-html="kpi.icon"></span>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value" :class="kpi.valueClass">
            <template v-if="kpiLoading">
              <div class="loading-shimmer" style="width:80px;height:22px;margin-top:4px"></div>
            </template>
            <template v-else>
              {{ kpi.format === "currency" ? fmt(kpis?.[kpi.key]) : (kpis?.[kpi.key] ?? "—") }}
            </template>
          </div>
        </div>
      </div>
    </div>

    <!-- Middle row -->
    <div class="mid-grid">
      <!-- Revenue trend chart -->
      <div class="books-card chart-card">
        <div class="card-header">
          <span class="books-card-title">Revenue Trend</span>
          <span class="badge badge-blue">Last 6 months</span>
          <button class="books-btn books-btn-ghost" style="font-size:11px;padding:4px 10px;margin-left:auto" @click="navTo('/reports')">Full Report</button>
        </div>
        <div v-if="trendLoading" class="chart-placeholder">
          <div class="loading-shimmer" style="height:180px;border-radius:8px"></div>
        </div>
        <div v-else-if="!points.length" class="chart-empty">
          No revenue data yet
        </div>
        <div v-else class="chart-wrap">
          <svg class="revenue-svg" :viewBox="`0 0 ${svgW} ${svgH}`" preserveAspectRatio="none">
            <!-- Grid lines + Y-axis labels (pinned to same y) -->
            <template v-for="(gl, i) in gridLines" :key="i">
              <line :x1="padL" :x2="svgW - padR" :y1="gl.y" :y2="gl.y"
                stroke="#e5e7eb" stroke-width="1" stroke-dasharray="4 3"
              />
              <text :x="padL - 6" :y="gl.y + 4"
                text-anchor="end" class="chart-label"
              >{{ gl.label }}</text>
            </template>
            <!-- Area fill (2+ points) -->
            <path v-if="areaPath" :d="areaPath" fill="url(#rev-grad)" opacity=".22" />
            <!-- Line (2+ points) -->
            <path v-if="linePath" :d="linePath"
              fill="none" stroke="#2563eb" stroke-width="2.5"
              stroke-linecap="round" stroke-linejoin="round"
            />
            <!-- Single-point vertical guide -->
            <line v-if="points.length === 1"
              :x1="points[0].x" :x2="points[0].x"
              :y1="svgH - padB" :y2="points[0].y + 6"
              stroke="#2563eb" stroke-width="1.5" stroke-dasharray="4 3"
            />
            <!-- Dots -->
            <circle v-for="(pt, i) in points" :key="i"
              :cx="pt.x" :cy="pt.y" r="5"
              fill="#2563eb" stroke="#ffffff" stroke-width="2.5"
            >
              <title>{{ pt.label }}: {{ fmt(pt.revenue) }}</title>
            </circle>
            <!-- Value label above single dot -->
            <text v-if="points.length === 1"
              :x="points[0].x" :y="points[0].y - 10"
              text-anchor="middle" class="chart-val-label"
            >{{ fmtShort(points[0].revenue) }}</text>
            <!-- X-axis month labels -->
            <text v-for="(pt, i) in points" :key="'l'+i"
              :x="pt.x" :y="svgH - 4"
              text-anchor="middle" class="chart-label"
            >{{ pt.label }}</text>
            <defs>
              <linearGradient id="rev-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stop-color="#2563eb" stop-opacity=".8"/>
                <stop offset="100%" stop-color="#2563eb" stop-opacity="0"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      <!-- AR / AP Aging side by side -->
      <div class="aging-pair">
        <div class="books-card aging-card">
          <div class="card-header">
            <span class="books-card-title">AR Aging</span>
            <span class="badge badge-blue">Receivables</span>
          </div>
          <div v-if="agingLoading" class="aging-bars">
            <div v-for="n in 5" :key="n" class="aging-row">
              <div class="loading-shimmer" style="height:12px;width:60px"></div>
              <div class="loading-shimmer" style="height:12px;width:100px"></div>
            </div>
          </div>
          <div v-else class="aging-bars">
            <div v-for="bucket in agingRows(aging)" :key="bucket.key" class="aging-row">
              <span class="aging-label">{{ bucket.label }}</span>
              <div class="aging-bar-wrap">
                <div class="aging-bar" :style="{ width: bucket.pct + '%', background: bucket.color }"></div>
              </div>
              <span class="aging-amount" :style="{ color: bucket.color }">{{ fmt(aging?.[bucket.key]) }}</span>
            </div>
          </div>
        </div>
        <div class="books-card aging-card">
          <div class="card-header">
            <span class="books-card-title">AP Aging</span>
            <span class="badge badge-amber">Payables</span>
          </div>
          <div v-if="apAgingLoading" class="aging-bars">
            <div v-for="n in 5" :key="n" class="aging-row">
              <div class="loading-shimmer" style="height:12px;width:60px"></div>
              <div class="loading-shimmer" style="height:12px;width:100px"></div>
            </div>
          </div>
          <div v-else class="aging-bars">
            <div v-for="bucket in agingRows(apAging)" :key="bucket.key" class="aging-row">
              <span class="aging-label">{{ bucket.label }}</span>
              <div class="aging-bar-wrap">
                <div class="aging-bar" :style="{ width: bucket.pct + '%', background: bucket.color }"></div>
              </div>
              <span class="aging-amount" :style="{ color: bucket.color }">{{ fmt(apAging?.[bucket.key]) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom row -->
    <div class="bot-grid">
      <!-- Top customers -->
      <div class="books-card">
        <div class="card-header">
          <span class="books-card-title">Top Customers</span>
          <button class="books-btn books-btn-ghost" style="font-size:11px;padding:4px 10px" @click="navTo('/invoices')">View all</button>
        </div>
        <table class="books-table" v-if="!dashLoading">
          <thead>
            <tr>
              <th>Customer</th>
              <th class="ta-r">Invoices</th>
              <th class="ta-r">Revenue</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in (dash?.top_customers || [])" :key="c.customer">
              <td>
                <div class="cust-name">{{ c.customer_name || c.customer }}</div>
                <div class="cust-sub">{{ c.customer }}</div>
              </td>
              <td class="ta-r mono">{{ c.invoice_count }}</td>
              <td class="ta-r mono kv-green">{{ fmt(c.total_revenue) }}</td>
            </tr>
            <tr v-if="!dash?.top_customers?.length">
              <td colspan="3" style="text-align:center;color:#9ca3af;padding:24px">No data</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="loading-shimmer" style="height:140px;border-radius:8px"></div>
      </div>

      <!-- Overdue invoices -->
      <div class="books-card">
        <div class="card-header">
          <span class="books-card-title">Overdue Invoices</span>
          <span class="badge badge-red">{{ dash?.overdue_invoices?.length || 0 }} overdue</span>
        </div>
        <table class="books-table" v-if="!dashLoading">
          <thead>
            <tr>
              <th>Invoice</th>
              <th>Customer</th>
              <th class="ta-r">Due</th>
              <th class="ta-r">Outstanding</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="inv in (dash?.overdue_invoices?.slice(0,5) || [])" :key="inv.name">
              <td><span class="link-accent">{{ inv.name }}</span></td>
              <td class="text-muted">{{ inv.customer_name || inv.customer }}</td>
              <td class="ta-r mono kv-red">{{ fmtDate(inv.due_date) }}</td>
              <td class="ta-r mono kv-red">{{ fmt(inv.outstanding_amount) }}</td>
            </tr>
            <tr v-if="!dash?.overdue_invoices?.length">
              <td colspan="4" style="text-align:center;color:#16a34a;padding:24px">✓ All caught up!</td>
            </tr>
          </tbody>
        </table>
        <div v-else class="loading-shimmer" style="height:140px;border-radius:8px"></div>
      </div>

      <!-- Recent Activity -->
      <div class="books-card" style="grid-column:1/-1">
        <div class="card-header">
          <span class="books-card-title">Recent Activity</span>
          <span class="badge badge-blue">Last 10 transactions</span>
        </div>
        <div v-if="activityLoading" class="loading-shimmer" style="height:120px;border-radius:8px"></div>
        <table v-else class="books-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Reference</th>
              <th>Party</th>
              <th class="ta-r">Amount</th>
              <th class="ta-r">Date</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in (activity || [])" :key="row.name">
              <td>
                <span class="activity-tag" :class="activityTagClass(row.doctype)">{{ activityTypeLabel(row.doctype) }}</span>
              </td>
              <td><span class="link-accent">{{ row.name }}</span></td>
              <td class="text-muted" style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ row.party || '—' }}</td>
              <td class="ta-r mono">{{ fmt(row.amount) }}</td>
              <td class="ta-r mono text-muted">{{ fmtDate(row.date) }}</td>
              <td>
                <span class="activity-status" :class="statusTagClass(row.status)">{{ row.status }}</span>
              </td>
            </tr>
            <tr v-if="!activity?.length">
              <td colspan="6" style="text-align:center;color:#9ca3af;padding:24px">No recent activity</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { useFrappeCall, formatCurrency, formatDate } from "../composables/useFrappe.js";

const router  = useRouter();
const fmt     = (v) => formatCurrency(v);
const fmtDate = formatDate;
const navTo   = (p) => router.push(p);

const MONTHS = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"];
function monthLabel(m) {
  if (!m) return "";
  const idx = parseInt(m.slice(5, 7)) - 1;
  return MONTHS[idx] ?? m.slice(5);
}
function fmtShort(v) {
  if (!v) return "0";
  if (v >= 1_00_00_000) return "₹" + (v / 1_00_00_000).toFixed(1) + "Cr";
  if (v >= 1_00_000)    return "₹" + (v / 1_00_000).toFixed(1) + "L";
  if (v >= 1_000)       return "₹" + (v / 1_000).toFixed(0) + "K";
  return "₹" + v;
}

// ── API calls ──
const { data: dash,     loading: dashLoading,     execute: loadDash     } = useFrappeCall("zoho_books_clone.api.dashboard.get_home_dashboard");
const { data: kpis,     loading: kpiLoading,      execute: loadKpis     } = useFrappeCall("zoho_books_clone.db.aggregates.get_dashboard_kpis");
const { data: trend,    loading: trendLoading,     execute: loadTrend    } = useFrappeCall("zoho_books_clone.db.aggregates.get_monthly_revenue_trend");
const { data: aging,    loading: agingLoading,     execute: loadAging    } = useFrappeCall("zoho_books_clone.db.aggregates.get_aging_buckets");
const { data: apAging,  loading: apAgingLoading,   execute: loadApAging  } = useFrappeCall("zoho_books_clone.api.dashboard.get_ap_aging_buckets");
const { data: activity, loading: activityLoading,  execute: loadActivity } = useFrappeCall("zoho_books_clone.api.dashboard.get_recent_activity");

onMounted(() => { loadDash(); loadKpis(); loadTrend(); loadAging(); loadApAging(); loadActivity(); });

// ── Icons ──
const iconRevenue  = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`;
const iconCollect  = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`;
const iconOutstand = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
const iconProfit   = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`;
const iconAssets   = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>`;
const iconAlert    = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;

// ── KPI cards config ──
const kpiCards = [
  { key: "month_revenue",     label: "Month Revenue",  format: "currency", icon: iconRevenue,  iconBg: "rgba(37,99,235,.1)",   valueClass: "kv-blue",  route: "/invoices" },
  { key: "month_collected",   label: "Collected",      format: "currency", icon: iconCollect,  iconBg: "rgba(22,163,74,.1)",   valueClass: "kv-green", route: "/payments" },
  { key: "month_outstanding", label: "Outstanding",    format: "currency", icon: iconOutstand, iconBg: "rgba(220,38,38,.1)",   valueClass: "kv-red",   route: "/invoices" },
  { key: "net_profit_mtd",    label: "Net Profit MTD", format: "currency", icon: iconProfit,   iconBg: "rgba(245,158,11,.1)",  valueClass: "kv-amber", route: "/reports"  },
  { key: "total_assets",      label: "Total Assets",   format: "currency", icon: iconAssets,   iconBg: "rgba(37,99,235,.1)",   valueClass: "",         route: null        },
  { key: "overdue_count",     label: "Overdue",        format: "number",   icon: iconAlert,    iconBg: "rgba(220,38,38,.1)",   valueClass: "kv-red",   route: "/invoices" },
];

// ── Revenue chart ──
const svgW = 580, svgH = 170, padL = 52, padR = 10, padT = 16, padB = 22;

const maxRevenue = computed(() => {
  const rows = trend.value || [];
  return Math.max(...rows.map(r => r.revenue || 0), 1);
});

const gridLines = computed(() => {
  const max = maxRevenue.value;
  const chartH = svgH - padT - padB;
  return [
    { y: padT,              label: fmtShort(max) },
    { y: padT + chartH / 2, label: fmtShort(max / 2) },
    { y: svgH - padB,       label: "0" },
  ];
});

const points = computed(() => {
  const rows = trend.value || [];
  if (!rows.length) return [];
  const max  = maxRevenue.value;
  const n    = rows.length;
  const step = n > 1 ? (svgW - padL - padR) / (n - 1) : 0;
  return rows.map((r, i) => ({
    x:       n > 1 ? padL + i * step : svgW / 2,
    y:       padT + (1 - (r.revenue || 0) / max) * (svgH - padT - padB),
    label:   monthLabel(r.month),
    revenue: r.revenue || 0,
  }));
});

const linePath = computed(() => {
  const pts = points.value;
  if (pts.length < 2) return "";
  return pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
});

const areaPath = computed(() => {
  const pts = points.value;
  if (pts.length < 2) return "";
  const base = svgH - padB;
  const line = pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ");
  return `${line} L${pts.at(-1).x.toFixed(1)},${base} L${pts[0].x.toFixed(1)},${base} Z`;
});

// ── Aging config ──
const AGING_BUCKETS = [
  { key: "current", label: "Current",    color: "#16a34a" },
  { key: "1_30",    label: "1–30 days",  color: "#2563eb" },
  { key: "31_60",   label: "31–60 days", color: "#f59e0b" },
  { key: "61_90",   label: "61–90 days", color: "#fb923c" },
  { key: "over_90", label: ">90 days",   color: "#dc2626" },
];
function agingRows(data) {
  const d     = data?.value || data || {};
  const total = Object.values(d).reduce((a, v) => a + (v || 0), 0) || 1;
  return AGING_BUCKETS.map(b => ({ ...b, pct: Math.min(100, ((d[b.key] || 0) / total) * 100) }));
}

// ── Recent activity helpers ──
function activityTypeLabel(dt) {
  if (dt === "Sales Invoice")    return "Invoice";
  if (dt === "Purchase Invoice") return "Bill";
  if (dt === "Payment Entry")    return "Payment";
  return dt;
}
function activityTagClass(dt) {
  if (dt === "Sales Invoice")    return "tag-invoice";
  if (dt === "Purchase Invoice") return "tag-bill";
  return "tag-payment";
}
function statusTagClass(status) {
  const s = (status || "").toLowerCase();
  if (s === "paid" || s === "receive") return "status-paid";
  if (s === "unpaid" || s === "overdue") return "status-unpaid";
  if (s === "draft") return "status-draft";
  return "status-other";
}
</script>

<style scoped>
.dashboard { display: flex; flex-direction: column; gap: 20px; padding: 24px; }

/* KPI grid */
.kpi-grid { display: grid; grid-template-columns: repeat(6, 1fr); gap: 14px; }
@media (max-width: 1400px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px)  { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

.kpi-card { display: flex; align-items: center; gap: 14px; padding: 16px 18px; cursor: default; }
.kpi-card--link { cursor: pointer; transition: box-shadow .15s, transform .15s; }
.kpi-card--link:hover { box-shadow: 0 4px 16px rgba(0,0,0,.1); transform: translateY(-1px); }
.kpi-icon { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; color: #374151; }
.kpi-label { font-size: 11px; color: #6b7280; letter-spacing: .06em; text-transform: uppercase; }
.kpi-value { font-size: 19px; font-weight: 700; margin-top: 3px; letter-spacing: -.02em; color: #111827; }
.kv-green { color: #16a34a; }
.kv-red   { color: #dc2626; }
.kv-amber { color: #f59e0b; }
.kv-blue  { color: #2563eb; }

/* Mid grid */
.mid-grid { display: grid; grid-template-columns: 1fr 620px; gap: 14px; }
@media (max-width: 1300px) { .mid-grid { grid-template-columns: 1fr 480px; } }
@media (max-width: 1100px) { .mid-grid { grid-template-columns: 1fr; } }

/* Aging pair */
.aging-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 900px)  { .aging-pair { grid-template-columns: 1fr; } }

.card-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 16px; }

/* Chart */
.chart-wrap { width: 100%; }
.revenue-svg { width: 100%; height: 170px; display: block; overflow: visible; }
.chart-label { font-size: 10.5px; fill: #9ca3af; font-family: inherit; }
.chart-val-label { font-size: 11px; fill: #2563eb; font-weight: 600; font-family: inherit; }
.chart-placeholder { padding: 10px 0; }
.chart-empty { height: 170px; display: flex; align-items: center; justify-content: center; color: #9ca3af; font-size: 13px; }

/* Aging */
.aging-bars  { display: flex; flex-direction: column; gap: 14px; }
.aging-row   { display: grid; grid-template-columns: 72px 1fr 72px; align-items: center; gap: 10px; }
.aging-label { font-size: 11.5px; color: #6b7280; }
.aging-bar-wrap { background: #f3f4f6; border-radius: 20px; height: 6px; overflow: hidden; }
.aging-bar   { height: 100%; border-radius: 20px; transition: width .6s ease; }
.aging-amount{ font-size: 12px; font-weight: 600; text-align: right; }

/* Bottom grid */
.bot-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 1000px) { .bot-grid { grid-template-columns: 1fr; } }
.bot-grid > *:last-child { grid-column: 1 / -1; }

/* Table helpers */
.ta-r      { text-align: right; }
.mono      { font-family: monospace; font-size: 12.5px; }
.kv-green  { color: #16a34a; }
.kv-red    { color: #dc2626; }
.cust-name { font-weight: 600; font-size: 13px; color: #111827; }
.cust-sub  { font-size: 11px; color: #9ca3af; }
.text-muted{ color: #6b7280; font-size: 12.5px; }
.link-accent { color: #2563eb; font-weight: 600; cursor: pointer; }
.link-accent:hover { text-decoration: underline; }

/* Activity tags */
.activity-tag  { display:inline-block;padding:2px 7px;border-radius:4px;font-size:10.5px;font-weight:600;letter-spacing:.04em; }
.tag-invoice   { background:#eff6ff;color:#1d4ed8; }
.tag-bill      { background:#fff7ed;color:#c2410c; }
.tag-payment   { background:#f0fdf4;color:#15803d; }

.activity-status { display:inline-block;padding:2px 7px;border-radius:4px;font-size:10.5px;font-weight:500; }
.status-paid    { background:#f0fdf4;color:#15803d; }
.status-unpaid  { background:#fef2f2;color:#b91c1c; }
.status-draft   { background:#f9fafb;color:#6b7280; }
.status-other   { background:#f3f4f6;color:#374151; }

/* Badge variants */
.badge-amber { background:#fff7ed;color:#c2410c; }
</style>
