<template>
  <div class="ei-page">

    <!-- Top bar -->
    <div class="ei-topbar">
      <div>
        <div class="ei-title">e-Invoice</div>
        <div class="ei-subtitle">IRN generation &amp; management for B2B invoices</div>
      </div>
      <div class="ei-controls">
        <div class="ei-search-wrap">
          <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
          <input v-model="search" placeholder="Search by invoice or customer…" class="ei-search-input" />
        </div>
        <div class="ei-tab-pills">
          <button v-for="t in tabs" :key="t.v" class="ei-pill" :class="{active:tab===t.v}" @click="tab=t.v">{{ t.l }}</button>
        </div>
        <input v-model="fromDate" type="date" class="ei-date-input" @change="load" title="From date" />
        <span style="font-size:12px;color:#9ca3af">to</span>
        <input v-model="toDate" type="date" class="ei-date-input" @change="load" title="To date" />
        <button class="ei-btn-ghost" @click="load" :disabled="loading"><span v-html="icon('refresh',14)"></span></button>
        <button v-if="irnPending.length" class="ei-btn-outline" @click="generateAllPending" :disabled="bulkGenerating">
          <span v-if="bulkGenerating" v-html="icon('refresh',13)" style="animation:spin 1s linear infinite"></span>
          {{ bulkGenerating ? `Generating ${bulkProgress}/${irnPending.length}…` : `Generate All Pending (${irnPending.length})` }}
        </button>
        <button v-if="list.length" class="ei-btn-ghost" @click="exportCSV"><span v-html="icon('download',13)"></span> CSV</button>
      </div>
    </div>

    <!-- Summary cards -->
    <div class="ei-summary" v-if="!loading">
      <div class="ei-sum-card">
        <div class="ei-sum-lbl">Total B2B Invoices</div>
        <div class="ei-sum-val">{{ list.length }}</div>
      </div>
      <div class="ei-sum-card">
        <div class="ei-sum-lbl">IRN Generated</div>
        <div class="ei-sum-val" style="color:#16a34a">{{ irnGenerated.length }}</div>
      </div>
      <div class="ei-sum-card">
        <div class="ei-sum-lbl">Pending IRN</div>
        <div class="ei-sum-val" style="color:#ea580c">{{ irnPending.length }}</div>
      </div>
      <div class="ei-sum-card">
        <div class="ei-sum-lbl">Cancelled</div>
        <div class="ei-sum-val" style="color:#dc2626">{{ irnCancelled.length }}</div>
      </div>
    </div>

    <!-- No B2B invoices note -->
    <div v-if="!loading && noGstinWarning" class="ei-note">
      <span v-html="icon('info',14)"></span>
      No B2B invoices found. e-Invoice applies only when the customer has a GSTIN — set Tax ID on the Customer record.
    </div>

    <!-- Table -->
    <div class="ei-card">
      <table class="ei-table">
        <thead><tr>
          <th @click="sort('name')" class="sortable">Invoice # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
          <th>Customer</th>
          <th>GSTIN</th>
          <th class="ta-r">Invoice Value</th>
          <th>IRN</th>
          <th>Status</th>
        </tr></thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="7"><div class="ei-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="inv in sorted" :key="inv.name" class="ei-row" @click="openView(inv)">
              <td><span class="ei-code">{{ inv.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(inv.posting_date) }}</td>
              <td>{{ inv.customer_name || inv.customer }}</td>
              <td class="mono-sm text-muted" style="font-size:11.5px">{{ inv.customer_gstin || '—' }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(inv.grand_total) }}</td>
              <td>
                <span v-if="inv.irn && inv.einvoice_status !== 'Cancelled'" class="ei-irn-chip" :title="inv.irn">{{ inv.irn.slice(0,16) + '…' }}</span>
                <span v-else-if="inv.einvoice_status === 'Cancelled'" class="text-muted" style="font-size:11.5px">Cancelled</span>
                <span v-else class="text-muted" style="font-size:11.5px">Not Generated</span>
              </td>
              <td><span class="ei-badge" :class="statusClass(inv)">{{ statusLabel(inv) }}</span></td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="7" class="ei-empty">No e-invoices match this filter</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── View Drawer ── -->
    <Teleport to="body">
      <div v-if="viewing" class="ei-overlay" @click.self="closeView"></div>
      <div class="ei-drawer-panel" :class="{open: !!viewing}">
        <template v-if="viewing">
          <!-- Header -->
          <div class="ei-drawer-header" :style="drawerHeaderStyle(viewing)">
            <div>
              <div class="ei-drawer-invoice">{{ viewing.name }}</div>
              <div style="margin-top:5px"><span class="ei-badge" :class="statusClass(viewing)" style="font-size:12px;padding:3px 10px">{{ statusLabel(viewing) }}</span></div>
            </div>
            <button class="ei-close-btn" @click="closeView" v-html="icon('x',16)"></button>
          </div>

          <!-- Meta cards -->
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;padding:16px 20px 0">
            <div class="ei-meta-card">
              <div class="ei-meta-lbl">Customer</div>
              <div class="ei-meta-val">{{ viewing.customer_name || viewing.customer }}</div>
            </div>
            <div class="ei-meta-card">
              <div class="ei-meta-lbl">Date</div>
              <div class="ei-meta-val">{{ fmtDate(viewing.posting_date) }}</div>
            </div>
            <div class="ei-meta-card">
              <div class="ei-meta-lbl">Invoice Value</div>
              <div class="ei-meta-val" style="color:#2563eb">{{ fmtCur(viewing.grand_total) }}</div>
            </div>
          </div>

          <!-- GSTIN block -->
          <div style="padding:12px 20px 0;display:flex;flex-direction:column;gap:6px">
            <div class="ei-gstin-row">
              <span class="ei-gstin-lbl">Customer GSTIN</span>
              <span class="ei-gstin-val" v-if="viewing.customer_gstin">{{ viewing.customer_gstin }}</span>
              <span v-else style="color:#ef4444;font-size:12px;font-weight:600">Not set — add Tax ID on Customer</span>
            </div>
            <div class="ei-gstin-row" v-if="companyGstin">
              <span class="ei-gstin-lbl">Company GSTIN</span>
              <span class="ei-gstin-val">{{ companyGstin }}</span>
            </div>
          </div>

          <!-- Body -->
          <div class="ei-drawer-body">

            <!-- No GSTIN warning -->
            <div v-if="!viewing.customer_gstin" class="ei-warn-block">
              <span v-html="icon('info',13)"></span>
              Customer has no GSTIN. Add Tax ID on the Customer record to enable IRN generation.
            </div>

            <!-- IRN block (when generated) -->
            <template v-if="viewing.irn">
              <div class="ei-section-title">IRN Details</div>
              <div class="ei-irn-block">
                <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:8px">
                  <div class="ei-irn-text">{{ viewing.irn }}</div>
                  <button class="ei-copy-btn" @click="copyIRN" :title="copied ? 'Copied!' : 'Copy IRN'">
                    <span v-html="icon(copied ? 'check' : 'copy', 13)"></span>
                  </button>
                </div>
              </div>
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:8px">
                <div class="ei-meta-card">
                  <div class="ei-meta-lbl">Ack No.</div>
                  <div class="ei-meta-val" style="font-size:12px;">{{ viewing.ack_no || '—' }}</div>
                </div>
                <div class="ei-meta-card">
                  <div class="ei-meta-lbl">Ack Date</div>
                  <div class="ei-meta-val" style="font-size:12px">{{ fmtDate(viewing.ack_date) || '—' }}</div>
                </div>
              </div>

              <!-- QR Code -->
              <div v-if="viewing.einvoice_status !== 'Cancelled'" style="margin-top:16px;display:flex;flex-direction:column;align-items:center;gap:8px">
                <div class="ei-qr-label">QR Code</div>
                <div class="ei-qr-wrap">
                  <IrnQrCode :irn="viewing.irn" :size="160" />
                </div>
              </div>
            </template>

            <!-- Pending state -->
            <div v-else-if="!viewing.irn && viewing.customer_gstin" style="text-align:center;padding:24px 0;color:#9ca3af">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5" style="margin-bottom:10px"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
              <div style="font-size:13px">No IRN generated yet</div>
              <div style="font-size:11.5px;margin-top:4px">Click "Generate IRN" to create one</div>
            </div>

            <!-- Manual IRN entry form -->
            <div v-if="showManualForm" class="ei-manual-form">
              <div class="ei-section-title" style="margin-bottom:8px">Enter IRN Manually</div>
              <label class="ei-lbl">IRN (64-char hex) <span style="color:#ef4444">*</span></label>
              <input v-model="manualForm.irn" class="ei-fi" placeholder="64-character hex string from NIC portal" maxlength="64" style="font-size:12px" />
              <label class="ei-lbl" style="margin-top:8px">Ack No. <span style="color:#ef4444">*</span></label>
              <input v-model="manualForm.ack_no" class="ei-fi" placeholder="Acknowledgement number" />
              <label class="ei-lbl" style="margin-top:8px">Ack Date</label>
              <input v-model="manualForm.ack_date" type="date" class="ei-fi" />
              <div style="display:flex;gap:8px;margin-top:12px">
                <button class="ei-btn-ghost" style="flex:1" @click="showManualForm=false">Cancel</button>
                <button class="ei-btn-primary" style="flex:1" :disabled="manualSaving" @click="saveManualIRN">
                  {{ manualSaving ? 'Saving…' : 'Save IRN' }}
                </button>
              </div>
            </div>

          </div><!-- /ei-drawer-body -->

          <!-- Footer actions -->
          <div class="ei-drawer-footer">
            <button class="ei-btn-ghost" @click="closeView">Close</button>
            <template v-if="viewing.einvoice_status !== 'Cancelled'">
              <button v-if="!viewing.irn && viewing.customer_gstin" class="ei-btn-primary" :disabled="generating" @click="doGenerateIRN(viewing)">
                <span v-if="generating" v-html="icon('refresh',13)" style="animation:spin 1s linear infinite"></span>
                {{ generating ? 'Generating…' : 'Generate IRN' }}
              </button>
              <button v-if="!viewing.irn && viewing.customer_gstin && !showManualForm" class="ei-btn-outline" @click="showManualForm=true">Enter Manually</button>
              <button v-if="viewing.irn" class="ei-btn-danger" :disabled="cancelling" @click="doCancelIRN(viewing)">
                {{ cancelling ? 'Cancelling…' : 'Cancel IRN' }}
              </button>
            </template>
          </div>
        </template>
      </div>
    </Teleport>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { apiList, apiPOST, resolveCompany, apiGET } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import IrnQrCode from "../components/IrnQrCode.vue";

const { toast } = useToast();
const list        = ref([]);
const loading     = ref(false);
const search      = ref("");
const tab         = ref("all");
const sortCol     = ref("posting_date");
const sortDir     = ref("desc");
const viewing     = ref(null);
const noGstinWarning = ref(false);
const companyGstin   = ref("");
const copied      = ref(false);

// Date range — default to current month
const now = new Date();
const fromDate = ref(`${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-01`);
const toDate   = ref(new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().slice(0, 10));

// Action states
const generating     = ref(false);
const cancelling     = ref(false);
const bulkGenerating = ref(false);
const bulkProgress   = ref(0);

// Manual form
const showManualForm = ref(false);
const manualSaving   = ref(false);
const manualForm     = ref({ irn: "", ack_no: "", ack_date: "" });

const tabs = [
  { v: "all",       l: "All" },
  { v: "generated", l: "IRN Generated" },
  { v: "pending",   l: "Pending" },
  { v: "cancelled", l: "Cancelled" },
];

async function load() {
  loading.value = true;
  noGstinWarning.value = false;
  try {
    const co = await resolveCompany();
    // Fetch company GSTIN for display
    try {
      const cd = await apiGET("zoho_books_clone.api.docs.get_doc", { doctype: "Books Company", name: co });
      companyGstin.value = cd?.gstin || "";
    } catch { companyGstin.value = ""; }

    const filters = [
      ["company", "=", co],
      ["docstatus", "=", 1],
      ["is_return", "=", 0],
      ["customer_gstin", "!=", ""],
    ];
    if (fromDate.value) filters.push(["posting_date", ">=", fromDate.value]);
    if (toDate.value)   filters.push(["posting_date", "<=", toDate.value]);

    const rows = await apiList("Sales Invoice", {
      fields: ["name", "posting_date", "customer", "customer_name", "customer_gstin",
               "grand_total", "irn", "einvoice_status", "ack_no", "ack_date"],
      filters,
      limit: 500,
      order: "posting_date desc",
    });
    list.value = (rows || []).filter(i => i.customer_gstin);
    if (!list.value.length) noGstinWarning.value = true;
  } catch (e) {
    toast.error(e.message || "Failed to load invoices");
  } finally {
    loading.value = false;
  }
}

function statusLabel(inv) {
  if (inv.einvoice_status === "Cancelled") return "Cancelled";
  if (inv.irn) return "IRN Generated";
  return "Pending IRN";
}
function statusClass(inv) {
  if (inv.einvoice_status === "Cancelled") return "badge-grey";
  if (inv.irn) return "badge-green";
  return "badge-orange";
}
function drawerHeaderStyle(inv) {
  if (inv.einvoice_status === "Cancelled") return "background:linear-gradient(135deg,#6b7280,#4b5563)";
  if (inv.irn) return "background:linear-gradient(135deg,#16a34a,#15803d)";
  return "background:linear-gradient(135deg,#f59e0b,#d97706)";
}

const irnGenerated = computed(() => list.value.filter(i => i.irn && i.einvoice_status !== "Cancelled"));
const irnPending   = computed(() => list.value.filter(i => !i.irn));
const irnCancelled = computed(() => list.value.filter(i => i.einvoice_status === "Cancelled"));

const filtered = computed(() => {
  let r = list.value;
  if (tab.value === "generated") r = irnGenerated.value;
  else if (tab.value === "pending")   r = irnPending.value;
  else if (tab.value === "cancelled") r = irnCancelled.value;
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(i => (i.name || "").toLowerCase().includes(q) || (i.customer_name || "").toLowerCase().includes(q));
  }
  return r;
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

function openView(inv) {
  viewing.value = { ...inv };
  showManualForm.value = false;
  manualForm.value = { irn: "", ack_no: "", ack_date: new Date().toISOString().slice(0, 10) };
}
function closeView() { viewing.value = null; }

function patchViewing(fields) {
  if (viewing.value) viewing.value = { ...viewing.value, ...fields };
  // Also patch the list row
  const idx = list.value.findIndex(i => i.name === viewing.value?.name);
  if (idx >= 0) list.value[idx] = { ...list.value[idx], ...fields };
}

async function doGenerateIRN(inv) {
  generating.value = true;
  try {
    const res = await apiPOST("zoho_books_clone.api.gst.generate_irn", { invoice_name: inv.name });
    patchViewing(res);
    toast.success("IRN generated successfully");
  } catch (e) {
    toast.error(e.message || "Failed to generate IRN");
  } finally {
    generating.value = false;
  }
}

async function doCancelIRN(inv) {
  cancelling.value = true;
  try {
    const res = await apiPOST("zoho_books_clone.api.gst.cancel_irn", { invoice_name: inv.name });
    patchViewing({ einvoice_status: "Cancelled" });
    toast.success("IRN cancelled");
  } catch (e) {
    toast.error(e.message || "Failed to cancel IRN");
  } finally {
    cancelling.value = false;
  }
}

async function saveManualIRN() {
  if (!manualForm.value.irn || manualForm.value.irn.length !== 64) {
    return toast.error("IRN must be exactly 64 characters");
  }
  if (!manualForm.value.ack_no) return toast.error("Ack No. is required");
  manualSaving.value = true;
  try {
    const res = await apiPOST("zoho_books_clone.api.gst.save_irn_manual", {
      invoice_name: viewing.value.name,
      irn:      manualForm.value.irn,
      ack_no:   manualForm.value.ack_no,
      ack_date: manualForm.value.ack_date,
    });
    patchViewing(res);
    showManualForm.value = false;
    toast.success("IRN saved");
  } catch (e) {
    toast.error(e.message || "Failed to save IRN");
  } finally {
    manualSaving.value = false;
  }
}

async function generateAllPending() {
  bulkGenerating.value = true;
  bulkProgress.value = 0;
  const pending = irnPending.value.filter(i => i.customer_gstin);
  for (const inv of pending) {
    try {
      const res = await apiPOST("zoho_books_clone.api.gst.generate_irn", { invoice_name: inv.name });
      const idx = list.value.findIndex(i => i.name === inv.name);
      if (idx >= 0) list.value[idx] = { ...list.value[idx], ...res };
    } catch { /* skip failed ones */ }
    bulkProgress.value++;
  }
  bulkGenerating.value = false;
  toast.success(`Generated IRN for ${pending.length} invoice(s)`);
}

async function copyIRN() {
  if (!viewing.value?.irn) return;
  try {
    await navigator.clipboard.writeText(viewing.value.irn);
    copied.value = true;
    setTimeout(() => { copied.value = false; }, 1800);
  } catch { toast.error("Copy failed — select the IRN text manually"); }
}

function exportCSV() {
  const rows = [
    ["Invoice #", "Date", "Customer", "GSTIN", "Invoice Value", "IRN", "Status", "Ack No.", "Ack Date"],
    ...sorted.value.map(i => [
      i.name, i.posting_date,
      i.customer_name || i.customer,
      i.customer_gstin || "",
      flt(i.grand_total),
      i.irn || "",
      statusLabel(i),
      i.ack_no || "",
      i.ack_date || "",
    ]),
  ];
  const csv = rows.map(r => r.map(v => `"${String(v ?? "").replace(/"/g, '""')}"`).join(",")).join("\n");
  const a = document.createElement("a");
  a.href = "data:text/csv;charset=utf-8," + encodeURIComponent(csv);
  a.download = `eInvoice_${fromDate.value}_to_${toDate.value}.csv`;
  a.click();
}

function fmtCur(v) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v));
}

onMounted(load);
</script>

<style scoped>
@keyframes spin { to { transform: rotate(360deg); } }
.ei-page { display:flex; flex-direction:column; gap:16px; padding:24px; }
.ei-topbar { display:flex; align-items:flex-start; justify-content:space-between; flex-wrap:wrap; gap:12px; }
.ei-title { font-size:20px; font-weight:800; color:#111827; }
.ei-subtitle { font-size:12px; color:#6b7280; }
.ei-controls { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.ei-search-wrap { display:flex; align-items:center; gap:8px; background:#fff; border-radius:8px; padding:6px 12px; border:1px solid #e5e7eb; min-width:220px; }
.ei-search-input { border:none; background:transparent; outline:none; font:inherit; color:#111827; width:100%; font-size:13px; }
.ei-tab-pills { display:flex; gap:3px; background:#f3f4f6; border-radius:8px; padding:3px; }
.ei-pill { border:none; background:transparent; border-radius:6px; padding:5px 11px; font-size:12px; font-weight:600; color:#6b7280; cursor:pointer; }
.ei-pill.active { background:#fff; color:#2563eb; box-shadow:0 1px 3px rgba(0,0,0,.08); }
.ei-date-input { border:1px solid #e5e7eb; border-radius:7px; padding:6px 10px; font:inherit; font-size:12.5px; outline:none; color:#374151; background:#fff; }
.ei-btn-primary { display:inline-flex; align-items:center; gap:6px; background:#2563eb; color:#fff; border:none; border-radius:8px; padding:8px 14px; font-size:13px; font-weight:600; cursor:pointer; }
.ei-btn-primary:hover { background:#1d4ed8; }
.ei-btn-primary:disabled { opacity:.6; cursor:not-allowed; }
.ei-btn-ghost { display:inline-flex; align-items:center; gap:6px; background:#fff; border:1px solid #e5e7eb; border-radius:8px; padding:8px 12px; font-size:13px; color:#374151; cursor:pointer; }
.ei-btn-ghost:hover { background:#f9fafb; }
.ei-btn-ghost:disabled { opacity:.6; cursor:not-allowed; }
.ei-btn-outline { display:inline-flex; align-items:center; gap:6px; background:#fff; border:1.5px solid #2563eb; border-radius:8px; padding:8px 13px; font-size:13px; color:#2563eb; font-weight:600; cursor:pointer; }
.ei-btn-outline:hover { background:#eff6ff; }
.ei-btn-outline:disabled { opacity:.6; cursor:not-allowed; }
.ei-btn-danger { display:inline-flex; align-items:center; gap:6px; background:#fff; border:1.5px solid #dc2626; border-radius:8px; padding:8px 13px; font-size:13px; color:#dc2626; font-weight:600; cursor:pointer; }
.ei-btn-danger:hover { background:#fef2f2; }
.ei-btn-danger:disabled { opacity:.6; cursor:not-allowed; }
.ei-summary { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.ei-sum-card { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:14px 16px; }
.ei-sum-lbl { font-size:11px; color:#6b7280; text-transform:uppercase; letter-spacing:.05em; margin-bottom:4px; }
.ei-sum-val { font-size:20px; font-weight:800; color:#111827;  }
.ei-note { background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:12px 16px; font-size:12.5px; color:#92400e; display:flex; align-items:center; gap:8px; }
.ei-card { background:#fff; border:1px solid #e5e7eb; border-radius:10px; overflow:hidden; }
.ei-table { width:100%; border-collapse:collapse; font-size:13px; }
.ei-table th { background:#f9fafb; border-bottom:1px solid #e5e7eb; padding:10px 12px; font-size:11px; font-weight:700; color:#374151; text-align:left; white-space:nowrap; text-transform:uppercase; letter-spacing:.04em; }
.ei-table th.sortable { cursor:pointer; user-select:none; }
.ei-table th.sortable:hover { color:#2563eb; }
.ta-r { text-align:right !important; }
.ei-row td { padding:10px 12px; border-bottom:1px solid #f3f4f6; cursor:pointer; }
.ei-row:last-child td { border-bottom:none; }
.ei-row:hover td { background:#f9fafb; }
.ei-code {  font-size:12.5px; color:#2563eb; font-weight:600; }
.ei-irn-chip {  font-size:11px; color:#374151; background:#f3f4f6; padding:2px 6px; border-radius:4px; }
.mono-sm {  font-size:13px; }
.text-muted { color:#9ca3af; }
.ei-badge { display:inline-flex; align-items:center; padding:3px 9px; border-radius:10px; font-size:11.5px; font-weight:600; }
.badge-green  { background:#dcfce7; color:#16a34a; }
.badge-orange { background:#fff7ed; color:#ea580c; }
.badge-grey   { background:#f3f4f6; color:#6b7280; }
.ei-empty { text-align:center; color:#9ca3af; padding:48px !important; }
.ei-shimmer { height:13px; background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%); border-radius:4px; animation:shimmer 1.2s infinite; background-size:200% 100%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* Drawer */
.ei-overlay { position:fixed; inset:0; background:rgba(0,0,0,.35); z-index:1000; }
.ei-drawer-panel { position:fixed; top:0; right:-500px; width:480px; height:100vh; background:#fff; z-index:1001; display:flex; flex-direction:column; box-shadow:-4px 0 32px rgba(0,0,0,.12); transition:right .24s cubic-bezier(.32,.72,0,1); }
.ei-drawer-panel.open { right:0; }
.ei-drawer-header { display:flex; align-items:flex-start; justify-content:space-between; padding:20px 20px 16px; color:#fff; flex-shrink:0; }
.ei-drawer-invoice { font-size:16px; font-weight:800; }
.ei-close-btn { background:rgba(255,255,255,.2); border:none; border-radius:6px; width:30px; height:30px; display:flex; align-items:center; justify-content:center; cursor:pointer; color:#fff; flex-shrink:0; }
.ei-close-btn:hover { background:rgba(255,255,255,.35); }
.ei-meta-card { background:#f8f9fc; border:1px solid #e8ecf0; border-radius:8px; padding:10px 14px; }
.ei-meta-lbl { font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:#868e96; }
.ei-meta-val { font-size:13.5px; font-weight:600; color:#1a1d23; margin-top:3px; }
.ei-gstin-row { display:flex; justify-content:space-between; align-items:center; padding:6px 0; border-bottom:1px solid #f3f4f6; }
.ei-gstin-lbl { font-size:12px; color:#6b7280; }
.ei-gstin-val {  font-size:12px; color:#374151; font-weight:600; }
.ei-drawer-body { flex:1; overflow-y:auto; padding:16px 20px; display:flex; flex-direction:column; gap:0; }
.ei-drawer-footer { padding:14px 20px; border-top:1px solid #f3f4f6; display:flex; gap:8px; justify-content:flex-end; flex-shrink:0; }
.ei-section-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#6b7280; margin-top:16px; margin-bottom:8px; }
.ei-irn-block { background:#f8faff; border:1px solid #dbeafe; border-radius:8px; padding:12px 14px; }
.ei-irn-text {  font-size:11px; color:#1e40af; word-break:break-all; line-height:1.6; flex:1; }
.ei-copy-btn { background:none; border:1px solid #dbeafe; border-radius:6px; padding:4px 7px; cursor:pointer; color:#2563eb; flex-shrink:0; display:flex; align-items:center; }
.ei-copy-btn:hover { background:#eff6ff; }
.ei-qr-label { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#6b7280; }
.ei-qr-wrap { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:12px; display:inline-flex; }
.ei-warn-block { background:#fffbeb; border:1px solid #fde68a; border-radius:8px; padding:12px 14px; font-size:12.5px; color:#92400e; display:flex; align-items:flex-start; gap:8px; line-height:1.5; margin-top:8px; }
.ei-manual-form { background:#f8f9fc; border:1px solid #e8ecf0; border-radius:10px; padding:14px; margin-top:16px; }
.ei-lbl { font-size:11.5px; font-weight:600; color:#374151; display:block; margin-bottom:4px; }
.ei-fi { width:100%; border:1px solid #e5e7eb; border-radius:7px; padding:8px 10px; font:inherit; font-size:13px; outline:none; color:#111827; background:#fff; box-sizing:border-box; }
.ei-fi:focus { border-color:#2563eb; box-shadow:0 0 0 3px rgba(37,99,235,.08); }
</style>
