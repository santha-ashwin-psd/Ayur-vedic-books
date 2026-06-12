<template>
  <div class="db-wrap">

    <!-- ── KPI Row ──────────────────────────────────────────────────── -->
    <div class="kpi-grid">
      <div
        v-for="kpi in kpiCards" :key="kpi.key"
        class="kpi-card"
        :class="{ 'kpi-card--link': kpi.route }"
        @click="kpi.route && navTo(kpi.route)"
      >
        <div class="kpi-top">
          <div class="kpi-icon" :style="{ background: kpi.iconBg, color: kpi.iconColor }">
            <span v-html="kpi.icon"></span>
          </div>
          <span class="kpi-label">{{ kpi.label }}</span>
        </div>
        <div class="kpi-value" :class="kpi.valueClass">
          <template v-if="kpiLoading">
            <div class="shimmer" style="width:72px;height:26px;border-radius:5px"></div>
          </template>
          <template v-else>
            {{ kpi.format === "currency" ? fmt(kpis?.[kpi.key]) : (kpis?.[kpi.key] ?? "0") }}
          </template>
        </div>
        <!-- sparkline -->
        <svg class="kpi-spark" viewBox="0 0 80 28" preserveAspectRatio="none">
          <polyline :points="kpi.spark" fill="none" :stroke="kpi.sparkColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/>
        </svg>
        <div class="kpi-trend" :class="kpi.trendClass">
          <span v-html="kpi.trendIcon"></span> 0% vs last month
        </div>
      </div>
    </div>

    <!-- ── Quick Actions ────────────────────────────────────────────── -->
    <div class="qa-card">
      <span class="qa-title">Quick Actions</span>
      <div class="qa-actions">
        <button class="qa-btn" @click="navTo('/invoices')">
          <div class="qa-icon-wrap" style="background:#e0f7f4">
            <span v-html="iconQaInvoice" style="color:#0bb8a8"></span>
          </div>
          <div class="qa-btn-footer">
            <span class="qa-btn-label">New Invoice</span>
            <svg class="qa-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
        </button>
        <button class="qa-btn" @click="navTo('/payments')">
          <div class="qa-icon-wrap" style="background:#e6f9ee">
            <span v-html="iconQaPayment" style="color:#1db954"></span>
          </div>
          <div class="qa-btn-footer">
            <span class="qa-btn-label">Record Payment</span>
            <svg class="qa-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
        </button>
        <button class="qa-btn" @click="navTo('/customers')">
          <div class="qa-icon-wrap" style="background:#f0eafe">
            <span v-html="iconQaCustomer" style="color:#7c3aed"></span>
          </div>
          <div class="qa-btn-footer">
            <span class="qa-btn-label">Add Customer</span>
            <svg class="qa-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
        </button>
        <button class="qa-btn" @click="navTo('/quotes')">
          <div class="qa-icon-wrap" style="background:#fff8e6">
            <span v-html="iconQaQuote" style="color:#f59e0b"></span>
          </div>
          <div class="qa-btn-footer">
            <span class="qa-btn-label">Create Quote</span>
            <svg class="qa-chevron" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="9 18 15 12 9 6"/></svg>
          </div>
        </button>
      </div>
    </div>

    <!-- ── Middle Row ────────────────────────────────────────────────── -->
    <div class="mid-grid">

      <!-- Revenue Trend -->
      <div class="db-card chart-card">
        <div class="db-card-header">
          <span class="db-card-title">Revenue Trend</span>
          <div class="db-header-right">
            <span class="db-badge db-badge-ghost">
              <span v-html="iconCal"></span> Last 6 months
              <span class="badge-caret">▾</span>
            </span>
            <button class="db-link-btn" @click="navTo('/reports')">Full Report</button>
          </div>
        </div>
        <div v-if="trendLoading" class="shimmer" style="height:200px;border-radius:8px"></div>
        <div v-else-if="!points.length" class="chart-empty-state">
          <div class="ces-icon">
            <svg width="52" height="52" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.4"><rect x="2" y="3" width="20" height="14" rx="2"/><polyline points="8 21 12 17 16 21"/><line x1="12" y1="17" x2="12" y2="21"/><polyline points="5 10 9 6 13 10 17 7"/></svg>
          </div>
          <div class="ces-title">No revenue data yet</div>
          <div class="ces-sub">Create your first invoice to see your revenue trend here.</div>
          <button class="ces-btn" @click="navTo('/invoices')">
            <span v-html="iconPlus"></span> New Invoice
          </button>
        </div>
        <div v-else class="chart-wrap">
          <svg class="revenue-svg" :viewBox="`0 0 ${svgW} ${svgH}`" preserveAspectRatio="none">
            <template v-for="(gl, i) in gridLines" :key="i">
              <line :x1="padL" :x2="svgW - padR" :y1="gl.y" :y2="gl.y"
                stroke="#f1f5f9" stroke-width="1"/>
              <text :x="padL - 6" :y="gl.y + 4" text-anchor="end" class="chart-label">{{ gl.label }}</text>
            </template>
            <path v-if="areaPath" :d="areaPath" fill="url(#rev-grad)" opacity=".18"/>
            <path v-if="linePath" :d="linePath" fill="none" stroke="#2563eb" stroke-width="2.5"
              stroke-linecap="round" stroke-linejoin="round"/>
            <circle v-for="(pt, i) in points" :key="i" :cx="pt.x" :cy="pt.y" r="4.5"
              fill="#2563eb" stroke="#fff" stroke-width="2.5">
              <title>{{ pt.label }}: {{ fmt(pt.revenue) }}</title>
            </circle>
            <text v-for="(pt, i) in points" :key="'l'+i" :x="pt.x" :y="svgH - 4"
              text-anchor="middle" class="chart-label">{{ pt.label }}</text>
            <defs>
              <linearGradient id="rev-grad" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%"   stop-color="#2563eb" stop-opacity=".7"/>
                <stop offset="100%" stop-color="#2563eb" stop-opacity="0"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
      </div>

      <!-- AR + AP Aging -->
      <div class="aging-pair">

        <!-- AR Aging -->
        <div class="db-card aging-card">
          <div class="db-card-header">
            <span class="db-card-title">AR Aging</span>
            <span class="db-badge db-badge-blue">Receivables</span>
          </div>
          <div v-if="agingLoading" class="aging-rows">
            <div v-for="n in 5" :key="n" class="aging-row">
              <div class="shimmer" style="height:11px;width:56px;border-radius:4px"></div>
              <div class="shimmer" style="height:6px;flex:1;border-radius:20px"></div>
              <div class="shimmer" style="height:11px;width:40px;border-radius:4px"></div>
            </div>
          </div>
          <div v-else class="aging-rows">
            <div v-for="bucket in agingRows(aging)" :key="bucket.key" class="aging-row">
              <span class="aging-label">{{ bucket.label }}</span>
              <div class="aging-bar-wrap">
                <div class="aging-bar" :style="{ width: bucket.pct + '%', background: bucket.color }"></div>
              </div>
              <span class="aging-amt" :style="{ color: bucket.color }">{{ fmt(aging?.[bucket.key]) }}</span>
            </div>
            <div class="aging-total-row">
              <span class="aging-total-label">Total</span>
              <div class="aging-total-spacer"></div>
              <span class="aging-total-amt">{{ fmt(agingTotal(aging)) }}</span>
            </div>
          </div>
        </div>

        <!-- AP Aging -->
        <div class="db-card aging-card">
          <div class="db-card-header">
            <span class="db-card-title">AP Aging</span>
            <span class="db-badge db-badge-amber">Payables</span>
          </div>
          <div v-if="apAgingLoading" class="aging-rows">
            <div v-for="n in 5" :key="n" class="aging-row">
              <div class="shimmer" style="height:11px;width:56px;border-radius:4px"></div>
              <div class="shimmer" style="height:6px;flex:1;border-radius:20px"></div>
              <div class="shimmer" style="height:11px;width:40px;border-radius:4px"></div>
            </div>
          </div>
          <div v-else class="aging-rows">
            <div v-for="bucket in agingRows(apAging)" :key="bucket.key" class="aging-row">
              <span class="aging-label">{{ bucket.label }}</span>
              <div class="aging-bar-wrap">
                <div class="aging-bar" :style="{ width: bucket.pct + '%', background: bucket.color }"></div>
              </div>
              <span class="aging-amt" :style="{ color: bucket.color }">{{ fmt(apAging?.[bucket.key]) }}</span>
            </div>
            <div class="aging-total-row">
              <span class="aging-total-label">Total</span>
              <div class="aging-total-spacer"></div>
              <span class="aging-total-amt">{{ fmt(agingTotal(apAging)) }}</span>
            </div>
          </div>
        </div>

      </div>
    </div>

    <!-- ── Bottom Row ────────────────────────────────────────────────── -->
    <div class="bot-grid">

      <!-- Top Customers -->
      <div class="db-card">
        <div class="db-card-header">
          <span class="db-card-title">Top Customers</span>
          <button class="db-link-btn" @click="navTo('/customers')">View all</button>
        </div>
        <div v-if="dashLoading" class="shimmer" style="height:150px;border-radius:8px"></div>
        <template v-else-if="dash?.top_customers?.length">
          <table class="db-table">
            <thead><tr>
              <th>Customer</th>
              <th class="ta-r">Invoices</th>
              <th class="ta-r">Revenue</th>
            </tr></thead>
            <tbody>
              <tr v-for="c in dash.top_customers" :key="c.customer">
                <td>
                  <div class="tc-name">{{ c.customer_name || c.customer }}</div>
                  <div class="tc-sub">{{ c.customer }}</div>
                </td>
                <td class="ta-r mono">{{ c.invoice_count }}</td>
                <td class="ta-r mono tc-green">{{ fmt(c.total_revenue) }}</td>
              </tr>
            </tbody>
          </table>
        </template>
        <div v-else class="bot-empty">
          <div class="bot-empty-icon">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.4"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          </div>
          <div class="bot-empty-title">No customers found</div>
          <div class="bot-empty-sub">Add customers to see your top customers here.</div>
          <button class="ces-btn" @click="navTo('/customers')">
            <span v-html="iconPlus"></span> Add Customer
          </button>
        </div>
      </div>

      <!-- Overdue Invoices -->
      <div class="db-card">
        <div class="db-card-header">
          <span class="db-card-title">Overdue Invoices</span>
          <div class="db-header-right">
            <button class="db-link-btn" @click="navTo('/invoices')">View all</button>
            <span class="db-badge" :class="dash?.overdue_invoices?.length ? 'db-badge-red' : 'db-badge-green'">
              {{ dash?.overdue_invoices?.length || 0 }} overdue
            </span>
          </div>
        </div>
        <div v-if="dashLoading" class="shimmer" style="height:150px;border-radius:8px"></div>
        <template v-else-if="dash?.overdue_invoices?.length">
          <table class="db-table">
            <thead><tr>
              <th>Invoice</th>
              <th>Customer</th>
              <th class="ta-r">Due</th>
              <th class="ta-r">Outstanding</th>
            </tr></thead>
            <tbody>
              <tr v-for="inv in dash.overdue_invoices.slice(0,5)" :key="inv.name">
                <td><span class="db-link">{{ inv.name }}</span></td>
                <td class="tc-sub">{{ inv.customer_name || inv.customer }}</td>
                <td class="ta-r mono tc-red">{{ fmtDate(inv.due_date) }}</td>
                <td class="ta-r mono tc-red">{{ fmt(inv.outstanding_amount) }}</td>
              </tr>
            </tbody>
          </table>
        </template>
        <div v-else class="bot-empty">
          <div class="ov-ok-icon">
            <svg width="38" height="38" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="12" fill="#dcfce7"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>
          </div>
          <div class="ov-ok-title">All caught up!</div>
          <div class="bot-empty-sub">No overdue invoices. Great job!</div>
        </div>
      </div>

      <!-- Recent Activity -->
      <div class="db-card recent-activity-card" style="grid-column:1/-1">
        <div class="db-card-header">
          <span class="db-card-title">Recent Activity</span>
          <span class="db-badge db-badge-ghost">Last 10 transactions</span>
        </div>
        <div v-if="activityLoading" class="shimmer" style="height:130px;border-radius:8px"></div>
        <template v-else-if="activity?.length">
          <table class="db-table">
            <tbody>
              <tr v-for="row in activity" :key="row.name">
                <td style="width:38px;padding-right:0">
                  <div class="act-dot" :class="actDotClass(row.doctype)"></div>
                </td>
                <td>
                  <span class="act-desc">{{ activityDesc(row) }}</span>
                </td>
                <td><span class="db-link">{{ row.name }}</span></td>
                <td class="tc-sub ta-r">{{ fmtDate(row.date) }}</td>
                <td class="ta-r mono act-amt" :class="row.doctype === 'Payment Entry' ? 'tc-green' : ''">
                  {{ fmt(row.amount) }}
                </td>
              </tr>
            </tbody>
          </table>
          <div class="act-footer">
            <button class="db-link-btn" @click="navTo('/reports')">View all activity →</button>
          </div>
        </template>
        <div v-else class="bot-empty" style="padding:28px 0">
          <div class="bot-empty-sub">No recent activity</div>
        </div>
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

// ── Quick-action icons ──
const iconQaInvoice  = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/></svg>`;
const iconQaPayment  = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2" ry="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>`;
const iconQaCustomer = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
const iconQaQuote    = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>`;
const iconQaMore     = `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="5" cy="12" r="1"/><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/></svg>`;
const iconCal        = `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`;
const iconPlus       = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>`;
const iconUp         = `<svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="18 15 12 9 6 15"/></svg>`;

// ── KPI spark paths (static placeholder curves) ──
const SPARKS = {
  blue:  "4,22 16,16 28,18 42,10 56,14 68,8 80,6",
  green: "4,20 16,14 28,16 42,8  56,12 68,6  80,4",
  red:   "4,8  16,14 28,10 42,18 56,12 68,16 80,20",
  amber: "4,18 16,12 28,15 42,9  56,13 68,10 80,8",
};

// ── KPI icons ──
const iconRevenue  = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`;
const iconCollect  = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>`;
const iconOutstand = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;
const iconProfit   = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/><polyline points="17 6 23 6 23 12"/></svg>`;
const iconAssets   = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="2" y="7" width="20" height="14" rx="2"/><path d="M16 7V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v2"/></svg>`;
const iconAlert    = `<svg width="17" height="17" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;

const kpiCards = [
  { key: "month_revenue",     label: "Month Revenue",  format: "currency", icon: iconRevenue,  iconBg: "#eff6ff", iconColor: "#2563eb", valueClass: "kv-blue",  route: "/invoices", spark: SPARKS.blue,  sparkColor: "#2563eb", trendClass: "trend-up",   trendIcon: iconUp },
  { key: "month_collected",   label: "Collected",      format: "currency", icon: iconCollect,  iconBg: "#f0fdf4", iconColor: "#16a34a", valueClass: "kv-green", route: "/payments", spark: SPARKS.green, sparkColor: "#16a34a", trendClass: "trend-up",   trendIcon: iconUp },
  { key: "month_outstanding", label: "Outstanding",    format: "currency", icon: iconOutstand, iconBg: "#fff7ed", iconColor: "#ea580c", valueClass: "kv-amber", route: "/invoices", spark: SPARKS.red,   sparkColor: "#ea580c", trendClass: "trend-down", trendIcon: iconUp },
  { key: "net_profit_mtd",    label: "Net Profit MTD", format: "currency", icon: iconProfit,   iconBg: "#f0fdfa", iconColor: "#0d9488", valueClass: "kv-teal",  route: "/reports",  spark: SPARKS.green, sparkColor: "#0d9488", trendClass: "trend-up",   trendIcon: iconUp },
  { key: "total_assets",      label: "Total Assets",   format: "currency", icon: iconAssets,   iconBg: "#eff6ff", iconColor: "#2563eb", valueClass: "",         route: null,        spark: SPARKS.blue,  sparkColor: "#2563eb", trendClass: "trend-up",   trendIcon: iconUp },
  { key: "overdue_count",     label: "Overdue",        format: "number",   icon: iconAlert,    iconBg: "#fff1f2", iconColor: "#e11d48", valueClass: "kv-red",   route: "/invoices", spark: SPARKS.red,   sparkColor: "#e11d48", trendClass: "trend-down", trendIcon: iconUp },
];

// ── Revenue chart ──
const svgW = 580, svgH = 200, padL = 52, padR = 10, padT = 16, padB = 24;
const maxRevenue = computed(() => Math.max(...(trend.value || []).map(r => r.revenue || 0), 1));
const gridLines = computed(() => {
  const max = maxRevenue.value, chartH = svgH - padT - padB;
  return [
    { y: padT,              label: fmtShort(max) },
    { y: padT + chartH / 2, label: fmtShort(max / 2) },
    { y: svgH - padB,       label: "0" },
  ];
});
const points = computed(() => {
  const rows = trend.value || [];
  if (!rows.length) return [];
  const max = maxRevenue.value, n = rows.length;
  const step = n > 1 ? (svgW - padL - padR) / (n - 1) : 0;
  return rows.map((r, i) => ({
    x: n > 1 ? padL + i * step : svgW / 2,
    y: padT + (1 - (r.revenue || 0) / max) * (svgH - padT - padB),
    label: monthLabel(r.month), revenue: r.revenue || 0,
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
  return pts.map((p, i) => `${i === 0 ? "M" : "L"}${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(" ")
    + ` L${pts.at(-1).x.toFixed(1)},${base} L${pts[0].x.toFixed(1)},${base} Z`;
});

// ── Aging ──
const AGING_BUCKETS = [
  { key: "current", label: "Current",    color: "#16a34a" },
  { key: "1_30",    label: "1-30 days",  color: "#2563eb" },
  { key: "31_60",   label: "31-60 days", color: "#f59e0b" },
  { key: "61_90",   label: "61-90 days", color: "#fb923c" },
  { key: "over_90", label: ">90 days",   color: "#dc2626" },
];
function agingRows(data) {
  const d = data?.value || data || {};
  const total = Object.values(d).reduce((a, v) => a + (v || 0), 0) || 1;
  return AGING_BUCKETS.map(b => ({ ...b, pct: Math.min(100, ((d[b.key] || 0) / total) * 100) }));
}
function agingTotal(data) {
  const d = data?.value || data || {};
  return Object.values(d).reduce((a, v) => a + (v || 0), 0);
}

// ── Activity helpers ──
function activityDesc(row) {
  if (row.doctype === "Payment Entry") return `Payment received from ${row.party || ""}`;
  if (row.doctype === "Sales Invoice") return `Invoice created for ${row.party || ""}`;
  if (row.doctype === "Purchase Invoice") return `Bill created from ${row.party || ""}`;
  return row.party || row.name;
}
function actDotClass(dt) {
  if (dt === "Sales Invoice") return "dot-invoice";
  if (dt === "Purchase Invoice") return "dot-bill";
  return "dot-payment";
}
</script>

<style scoped>
/* ── Base ──────────────────────────────────────────────────────────── */
.db-wrap {
  display: flex; flex-direction: column; gap: 18px;
  padding: 24px 28px;
  font-family: Plus Jakarta Sans, Lato, system-ui, sans-serif;
  background: #f8fafc; min-height: 100%;
}

/* ── KPI grid ──────────────────────────────────────────────────────── */
.kpi-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
}
@media (max-width: 1400px) { .kpi-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 900px)  { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }

.kpi-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px 18px 12px;
  display: flex; flex-direction: column; gap: 4px;
  cursor: default;
  transition: box-shadow .15s, transform .15s;
}
.kpi-card--link { cursor: pointer; }
.kpi-card--link:hover { box-shadow: 0 4px 18px rgba(0,0,0,.08); transform: translateY(-1px); }

.kpi-top { display: flex; align-items: center; gap: 10px; margin-bottom: 2px; }
.kpi-icon {
  width: 36px; height: 36px; border-radius: 9px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.kpi-label { font-size: 11px; font-weight: 600; color: #6b7280; text-transform: uppercase; letter-spacing: .06em; }
.kpi-value { font-size: 22px; font-weight: 700; color: #111827; letter-spacing: -.03em; line-height: 1.1; padding: 2px 0; }
.kv-blue  { color: #1d4ed8; }
.kv-green { color: #16a34a; }
.kv-red   { color: #dc2626; }
.kv-amber { color: #d97706; }
.kv-teal  { color: #0d9488; }

.kpi-spark { width: 100%; height: 28px; margin: 2px 0; }

.kpi-trend {
  font-size: 11px; font-weight: 500; color: #6b7280;
  display: flex; align-items: center; gap: 3px;
}
.trend-up   { color: #16a34a; }
.trend-down { color: #dc2626; }

/* ── Quick Actions ─────────────────────────────────────────────────── */
.qa-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 18px 20px 16px;
}
.qa-title {
  font-size: 15px; font-weight: 700; color: #111827;
  display: block; margin-bottom: 14px;
}
.qa-actions {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}
.qa-btn {
  display: flex; flex-direction: column; align-items: flex-start; gap: 12px;
  background: #fff; border: 1.5px solid #e5e7eb;
  border-radius: 10px; padding: 14px;
  cursor: pointer; font-family: inherit;
  transition: all .18s;
  width: 100%; text-align: left;
  box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
.qa-btn:hover { border-color: #2563eb; box-shadow: 0 4px 12px rgba(37,99,235,.1); transform: translateY(-1px); }
.qa-btn:active { transform: translateY(0); }
.qa-icon-wrap {
  width: 46px; height: 46px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.qa-btn-footer {
  display: flex; align-items: center; justify-content: space-between; width: 100%;
}
.qa-btn-label {
  font-size: 13.5px; font-weight: 600; color: #111827;
}
.qa-chevron { color: #9ca3af; flex-shrink: 0; }
.qa-btn-more { color: #6b7280; }

/* ── Responsive: 768px ── */
@media (max-width: 768px) {
  .db-wrap { padding: 16px; gap: 14px; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr) !important; }
  .mid-grid { grid-template-columns: 1fr !important; }
  .aging-pair { grid-template-columns: 1fr !important; }
  .bot-grid { grid-template-columns: 1fr !important; }
}

/* ── Responsive: 480px ── */
@media (max-width: 480px) {
  .db-wrap { padding: 14px 12px; gap: 12px; }
  .kpi-grid { grid-template-columns: repeat(2, 1fr) !important; gap: 10px; }
  .kpi-card { padding: 12px 14px 10px; }
  .kpi-value { font-size: 18px; }
}

/* ── Responsive: 425px ── */
@media (max-width: 425px) {
  .db-wrap { padding: 12px 10px; gap: 10px; }
  .qa-card { padding: 14px 14px 12px; border-radius: 10px; }
  .qa-title { font-size: 14px; margin-bottom: 10px; }
  .qa-actions { grid-template-columns: 1fr 1fr !important; gap: 10px; }
  .qa-btn { padding: 12px 10px; gap: 10px; border-radius: 8px; }
  .qa-icon-wrap { width: 40px; height: 40px; border-radius: 8px; }
  .qa-btn-label { font-size: 12.5px; }
  .qa-chevron { width: 12px; height: 12px; }
  .recent-activity-card { display: none !important; }
}

/* ── Responsive: 375px ── */
@media (max-width: 375px) {
  .db-wrap { padding: 10px 8px; gap: 8px; }
  .qa-card { padding: 12px 12px 10px; border-radius: 8px; }
  .qa-title { font-size: 13.5px; margin-bottom: 8px; }
  .qa-actions { grid-template-columns: 1fr 1fr !important; gap: 8px; }
  .qa-btn { padding: 10px 8px; gap: 8px; border-radius: 8px; }
  .qa-icon-wrap { width: 36px; height: 36px; border-radius: 7px; }
  .qa-btn-label { font-size: 11.5px; }
  .qa-chevron { width: 11px; height: 11px; }
  .kpi-grid { grid-template-columns: 1fr 1fr !important; gap: 8px; }
  .kpi-card { padding: 10px 12px 8px; }
  .kpi-value { font-size: 16px; }
  .recent-activity-card { display: none !important; }
}

/* ── Cards ─────────────────────────────────────────────────────────── */
.db-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 20px 22px;
}
.db-card-header {
  display: flex; align-items: center; justify-content: space-between;
  margin-bottom: 18px;
}
.db-card-title {
  font-size: 14px; font-weight: 700; color: #111827;
}
.db-header-right { display: flex; align-items: center; gap: 10px; }

.db-badge {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 3px 9px; border-radius: 20px;
  font-size: 11.5px; font-weight: 600;
}
.db-badge-ghost  { background: #f1f5f9; color: #475569; }
.db-badge-blue   { background: #eff6ff; color: #1d4ed8; }
.db-badge-amber  { background: #fff7ed; color: #c2410c; }
.db-badge-red    { background: #fef2f2; color: #b91c1c; }
.db-badge-green  { background: #f0fdf4; color: #15803d; }
.badge-caret     { font-size: 9px; }

.db-link-btn {
  background: none; border: none; cursor: pointer;
  font-size: 12.5px; font-weight: 600; color: #2563eb;
  font-family: inherit; padding: 0;
}
.db-link-btn:hover { text-decoration: underline; }
.db-link { color: #2563eb; font-weight: 600; font-size: 13px; cursor: pointer; }
.db-link:hover { text-decoration: underline; }

/* ── Middle grid ───────────────────────────────────────────────────── */
.mid-grid {
  display: grid;
  grid-template-columns: 1fr 460px;
  gap: 14px;
}
@media (max-width: 1300px) { .mid-grid { grid-template-columns: 1fr 380px; } }
@media (max-width: 1100px) { .mid-grid { grid-template-columns: 1fr; } }

.chart-card { min-height: 280px; }
.chart-wrap { width: 100%; }
.revenue-svg { width: 100%; height: 200px; display: block; overflow: visible; }
.chart-label { font-size: 10.5px; fill: #9ca3af; font-family: inherit; }

.chart-empty-state {
  display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 10px; min-height: 200px; padding: 20px;
}
.ces-icon { opacity: .6; }
.ces-title { font-size: 14px; font-weight: 700; color: #374151; }
.ces-sub   { font-size: 12.5px; color: #9ca3af; text-align: center; max-width: 260px; line-height: 1.5; }
.ces-btn {
  display: flex; align-items: center; gap: 6px;
  background: #2563eb; color: #fff; border: none; border-radius: 8px;
  padding: 8px 18px; font-size: 13px; font-weight: 600;
  cursor: pointer; font-family: inherit; transition: background .12s;
  margin-top: 4px;
}
.ces-btn:hover { background: #1d4ed8; }

/* ── Aging pair ────────────────────────────────────────────────────── */
.aging-pair { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
@media (max-width: 900px) { .aging-pair { grid-template-columns: 1fr; } }

.aging-card { display: flex; flex-direction: column; }
.aging-rows { display: flex; flex-direction: column; gap: 13px; }
.aging-row  {
  display: grid; grid-template-columns: 68px 1fr 60px;
  align-items: center; gap: 10px;
}
.aging-label  { font-size: 12px; color: #6b7280; }
.aging-bar-wrap { background: #f1f5f9; border-radius: 20px; height: 6px; overflow: hidden; }
.aging-bar    { height: 100%; border-radius: 20px; transition: width .6s ease; }
.aging-amt    { font-size: 12px; font-weight: 600; text-align: right; }

.aging-total-row {
  display: grid; grid-template-columns: 68px 1fr 60px;
  align-items: center; gap: 10px;
  border-top: 1px solid #f1f5f9; padding-top: 10px; margin-top: 2px;
}
.aging-total-label { font-size: 12px; font-weight: 700; color: #374151; }
.aging-total-spacer {}
.aging-total-amt   { font-size: 12.5px; font-weight: 700; color: #111827; text-align: right; }

/* ── Bottom grid ───────────────────────────────────────────────────── */
.bot-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
@media (max-width: 1000px) { .bot-grid { grid-template-columns: 1fr; } }

/* ── Tables ────────────────────────────────────────────────────────── */
.db-table {
  width: 100%; border-collapse: collapse; font-size: 13px;
}
.db-table th {
  background: #f9fafb; border-bottom: 1px solid #e5e7eb;
  padding: 9px 12px; font-size: 11px; font-weight: 700;
  color: #6b7280; text-align: left; text-transform: uppercase;
  letter-spacing: .04em;
}
.db-table td {
  padding: 10px 12px; border-bottom: 1px solid #f3f4f6;
  color: #374151; vertical-align: middle;
}
.db-table tbody tr:last-child td { border-bottom: none; }
.db-table tbody tr:hover { background: #fafafa; }

.ta-r    { text-align: right; }
.mono    { font-size: 12.5px; }
.tc-name { font-weight: 600; font-size: 13px; color: #111827; }
.tc-sub  { font-size: 11.5px; color: #9ca3af; }
.tc-green{ color: #16a34a; font-weight: 600; }
.tc-red  { color: #dc2626; }

/* ── Empty states ──────────────────────────────────────────────────── */
.bot-empty {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; gap: 8px; padding: 36px 20px;
  text-align: center;
}
.bot-empty-icon { opacity: .7; }
.bot-empty-title { font-size: 14px; font-weight: 700; color: #374151; }
.bot-empty-sub   { font-size: 12.5px; color: #9ca3af; line-height: 1.5; max-width: 240px; }
.ov-ok-icon  { margin-bottom: 2px; }
.ov-ok-title { font-size: 15px; font-weight: 700; color: #16a34a; }

/* ── Recent Activity ───────────────────────────────────────────────── */
.act-dot {
  width: 10px; height: 10px; border-radius: 50%;
  flex-shrink: 0; margin: 0 auto;
}
.dot-invoice { background: #2563eb; }
.dot-bill    { background: #f59e0b; }
.dot-payment { background: #16a34a; }
.act-desc    { font-size: 13px; color: #374151; font-weight: 500; }
.act-amt     { font-weight: 600; }
.act-footer  { padding: 12px 0 0; text-align: center; }

/* ── Shimmer ───────────────────────────────────────────────────────── */
.shimmer {
  background: linear-gradient(90deg, #f1f5f9 25%, #e2e8f0 50%, #f1f5f9 75%);
  background-size: 200% 100%;
  animation: shimmer 1.4s infinite;
}
@keyframes shimmer { 0% { background-position: 200% 0 } 100% { background-position: -200% 0 } }

@media (max-width: 480px) {
.db-table td {
border-bottom: none !important;
text-align: left !important;
padding: 4px 0px !important;
}
}
</style>
