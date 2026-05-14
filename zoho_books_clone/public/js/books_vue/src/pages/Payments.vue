<template>
  <div class="pmt-page">

    <!-- ── Topbar actions ─────────────────────────────────────────── -->
    <div class="pmt-actions">
      <div class="pmt-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search payments…" class="pmt-search-input" />
      </div>
      <div class="pmt-pills">
        <button v-for="t in tabs" :key="t.key"
          class="pmt-pill" :class="{active: activeTab===t.key}"
          @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="pmt-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="pmt-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Payment
        </button>
      </div>
    </div>

    <!-- ── Summary strip ─────────────────────────────────────────── -->
    <div class="pmt-summary" v-if="!loading">
      <div class="pmt-sum-card">
        <div class="pmt-sum-lbl">Total Received</div>
        <div class="pmt-sum-val green">{{ fmtCur(summaryReceived) }}</div>
      </div>
      <div class="pmt-sum-card">
        <div class="pmt-sum-lbl">Total Paid Out</div>
        <div class="pmt-sum-val red">{{ fmtCur(summaryPaid) }}</div>
      </div>
      <div class="pmt-sum-card">
        <div class="pmt-sum-lbl">Net</div>
        <div class="pmt-sum-val" :class="(summaryReceived-summaryPaid)>=0?'green':'red'">
          {{ fmtCur(summaryReceived - summaryPaid) }}
        </div>
      </div>
      <div class="pmt-sum-card">
        <div class="pmt-sum-lbl">Count</div>
        <div class="pmt-sum-val">{{ filtered.length }}</div>
      </div>
    </div>

    <!-- ── Table ─────────────────────────────────────────────────── -->
    <div class="pmt-card">
      <table class="pmt-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sort('name')" class="sortable">Payment # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('party')" class="sortable">Party <span v-html="sortArrow('party')"></span></th>
            <th @click="sort('mode_of_payment')" class="sortable">Mode <span v-html="sortArrow('mode_of_payment')"></span></th>
            <th @click="sort('reference_no')" class="sortable">Reference <span v-html="sortArrow('reference_no')"></span></th>
            <th @click="sort('payment_date')" class="sortable">Date <span v-html="sortArrow('payment_date')"></span></th>
            <th>Type</th>
            <th @click="sort('paid_amount')" class="sortable ta-r">Amount <span v-html="sortArrow('paid_amount')"></span></th>
            <th style="width:60px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n">
              <td colspan="9"><div class="pmt-shimmer"></div></td>
            </tr>
          </template>
          <template v-else>
            <tr v-for="p in sorted" :key="p.name" class="pmt-row" :class="{selected: selected.has(p.name)}">
              <td><input type="checkbox" :checked="selected.has(p.name)" @change="toggle(p.name)" /></td>
              <td @click="openView(p)"><span class="pmt-num">{{ p.name }}</span></td>
              <td @click="openView(p)">{{ p.party || '—' }}</td>
              <td @click="openView(p)" class="text-muted">{{ p.mode_of_payment || '—' }}</td>
              <td @click="openView(p)" class="text-muted mono-sm">{{ p.reference_no || '—' }}</td>
              <td @click="openView(p)" class="text-muted mono-sm">{{ fmtDate(p.payment_date) }}</td>
              <td @click="openView(p)">
                <span class="pmt-badge" :class="p.payment_type==='Receive'?'badge-green':'badge-red'">
                  {{ p.payment_type==='Receive' ? 'Received' : 'Paid Out' }}
                </span>
              </td>
              <td @click="openView(p)" class="ta-r mono-sm" :class="p.payment_type==='Receive'?'green':'red'">
                {{ fmtCur(p.paid_amount) }}
              </td>
              <td class="pmt-act-cell">
                <button class="pmt-act-btn" @click="openView(p)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="p.docstatus===0" class="pmt-act-btn" @click="openEdit(p)" title="Edit"><span v-html="icon('edit',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length">
              <td colspan="9" class="pmt-empty">
                <span v-html="icon('payment',28)" style="color:#d1d5db;display:block;margin:0 auto 8px"></span>
                No payments found
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Create / Edit drawer ──────────────────────────────────── -->
    <div v-if="drawerOpen" class="pmt-overlay" @click.self="drawerOpen=false"></div>
    <div class="pmt-drawer" :class="{open:drawerOpen}">
      <div class="pmt-dheader">
        <div class="pmt-dheader-title">{{ editingName ? 'Edit Payment' : 'New Payment' }}</div>
        <button class="pmt-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="pmt-dbody">
        <!-- Payment type -->
        <div class="pmt-field">
          <label class="pmt-label">Payment Type</label>
          <div class="pmt-radio-group">
            <label class="pmt-radio" :class="{checked: form.payment_type==='Receive'}" @click="setPaymentType('Receive')">
              <span class="pmt-radio-dot" :class="{on: form.payment_type==='Receive'}"></span>
              Received (from customer)
            </label>
            <label class="pmt-radio" :class="{checked: form.payment_type==='Pay'}" @click="setPaymentType('Pay')">
              <span class="pmt-radio-dot" :class="{on: form.payment_type==='Pay'}"></span>
              Paid Out (to vendor)
            </label>
          </div>
        </div>

        <div class="pmt-fields-grid">
          <!-- Party -->
          <div class="pmt-field">
            <label class="pmt-label">{{ form.payment_type==='Receive' ? 'Customer' : 'Vendor' }} <span class="req">*</span></label>
            <SearchableSelect
              v-model="form.party"
              :options="partyOptions"
              :placeholder="form.payment_type==='Receive' ? 'Select customer…' : 'Select vendor…'"
              @search="fetchParties"
              @select="onPartySelect"
            />
          </div>

          <!-- Mode of payment -->
          <div class="pmt-field">
            <label class="pmt-label">Mode of Payment</label>
            <select v-model="form.mode_of_payment" class="pmt-select">
              <option value="">— Select —</option>
              <option v-for="m in paymentModes" :key="m" :value="m">{{ m }}</option>
            </select>
          </div>

          <!-- Amount -->
          <div class="pmt-field">
            <label class="pmt-label">Amount <span class="req">*</span></label>
            <input v-model.number="form.paid_amount" type="number" min="0" step="0.01" class="pmt-input" placeholder="0.00" />
          </div>

          <!-- Payment date -->
          <div class="pmt-field">
            <label class="pmt-label">Payment Date <span class="req">*</span></label>
            <input v-model="form.payment_date" type="date" class="pmt-input" />
          </div>

          <!-- Reference No -->
          <div class="pmt-field">
            <label class="pmt-label">Reference / Cheque No</label>
            <input v-model="form.reference_no" type="text" class="pmt-input" placeholder="e.g. CHQ-001" />
          </div>

          <!-- Reference date -->
          <div class="pmt-field">
            <label class="pmt-label">Reference Date</label>
            <input v-model="form.reference_date" type="date" class="pmt-input" />
          </div>
        </div>

        <!-- Account -->
        <div class="pmt-fields-grid" style="margin-top:0">
          <div class="pmt-field">
            <label class="pmt-label">Paid From Account</label>
            <SearchableSelect
              v-model="form.paid_from"
              :options="accounts"
              placeholder="Select account…"
              @search="fetchAccounts"
            />
          </div>
          <div class="pmt-field">
            <label class="pmt-label">Paid To Account</label>
            <SearchableSelect
              v-model="form.paid_to"
              :options="accounts"
              placeholder="Select account…"
              @search="fetchAccounts"
            />
          </div>
        </div>

        <!-- Remarks -->
        <div class="pmt-field" style="margin-top:4px">
          <label class="pmt-label">Remarks</label>
          <textarea v-model="form.remarks" rows="2" class="pmt-input" placeholder="Optional notes…"></textarea>
        </div>
      </div>

      <div class="pmt-dfooter">
        <button class="pmt-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="pmt-btn-save" :disabled="drawerSaving" @click="savePayment(0)">
          <span v-html="icon('save',13)"></span> {{ drawerSaving ? 'Saving…' : 'Save Draft' }}
        </button>
        <button class="pmt-btn-primary" :disabled="drawerSaving" @click="savePayment(1)">
          <span v-html="icon('check',13)"></span> {{ drawerSaving ? 'Saving…' : 'Submit' }}
        </button>
      </div>
    </div>

    <!-- ── View drawer ───────────────────────────────────────────── -->
    <div v-if="viewOpen" class="pmt-overlay" @click.self="viewOpen=false"></div>
    <div class="pmt-drawer pmt-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewPmt">
        <div class="pmt-view-head" :class="viewPmt.payment_type==='Receive'?'head-green':'head-red'">
          <div>
            <div class="pmt-view-num">{{ viewPmt.name }}</div>
            <div class="pmt-view-party">{{ viewPmt.party || '—' }}</div>
          </div>
          <div style="text-align:right">
            <div class="pmt-view-amount">{{ fmtCur(viewPmt.paid_amount) }}</div>
            <span class="pmt-badge" :class="viewPmt.payment_type==='Receive'?'badge-green':'badge-red'">
              {{ viewPmt.payment_type==='Receive' ? 'Received' : 'Paid Out' }}
            </span>
          </div>
          <button class="pmt-dclose pmt-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <div class="pmt-dbody">
          <div class="pmt-meta-grid">
            <div><div class="pmt-meta-lbl">Payment Date</div><div>{{ fmtDate(viewPmt.payment_date) }}</div></div>
            <div><div class="pmt-meta-lbl">Mode</div><div>{{ viewPmt.mode_of_payment || '—' }}</div></div>
            <div><div class="pmt-meta-lbl">Reference No</div><div class="mono-sm">{{ viewPmt.reference_no || '—' }}</div></div>
            <div><div class="pmt-meta-lbl">Reference Date</div><div class="mono-sm">{{ fmtDate(viewPmt.reference_date) }}</div></div>
            <div><div class="pmt-meta-lbl">Paid From</div><div>{{ viewPmt.paid_from || '—' }}</div></div>
            <div><div class="pmt-meta-lbl">Paid To</div><div>{{ viewPmt.paid_to || '—' }}</div></div>
            <div v-if="viewPmt.remarks" style="grid-column:1/-1">
              <div class="pmt-meta-lbl">Remarks</div><div>{{ viewPmt.remarks }}</div>
            </div>
          </div>
        </div>

        <div class="pmt-dfooter">
          <button class="pmt-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewPmt.docstatus===0" class="pmt-btn-save" @click="openEdit(viewPmt);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { apiList, apiGET, apiSave, resolveCompany, apiLinkValues } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const route     = useRoute();

// Default tab based on which route we're on
const defaultTab = route.path === "/payments-received" ? "Receive" : "Pay";
const activeTab  = ref(defaultTab);

const tabs = [
  { key: "all",     label: "All"       },
  { key: "Receive", label: "Received"  },
  { key: "Pay",     label: "Paid Out"  },
];

// ── Data ─────────────────────────────────────────────────────────
const list         = ref([]);
const loading      = ref(false);
const search       = ref("");
const selected     = ref(new Set());

// Drawer state
const drawerOpen   = ref(false);
const drawerSaving = ref(false);
const editingName  = ref("");

// View drawer
const viewOpen     = ref(false);
const viewPmt      = ref(null);

// Options
const partyOptions = ref([]);
const accounts     = ref([]);
const paymentModes = ref(["Cash", "Bank Transfer", "Cheque", "Credit Card", "UPI", "NEFT", "RTGS"]);

// Sort state
const sortCol = ref("payment_date");
const sortDir = ref("desc");

// Form
const blankForm = () => ({
  doctype:        "Payment Entry",
  payment_type:   defaultTab === "Receive" ? "Receive" : "Pay",
  party_type:     defaultTab === "Receive" ? "Customer" : "Supplier",
  party:          "",
  mode_of_payment:"",
  paid_amount:    "",
  payment_date:   new Date().toISOString().slice(0, 10),
  reference_no:   "",
  reference_date: "",
  paid_from:      "",
  paid_to:        "",
  remarks:        "",
});
const form = reactive(blankForm());

// ── Load ─────────────────────────────────────────────────────────
async function load() {
  loading.value = true;
  try {
    const company = await resolveCompany();
    list.value = await apiList("Payment Entry", {
      fields: ["name","party","party_type","paid_amount","payment_type",
               "payment_date","mode_of_payment","reference_no","reference_date",
               "paid_from","paid_to","remarks","docstatus"],
      limit: 200,
      order: "payment_date desc",
    });
  } catch (e) {
    toast.error(e.message || "Failed to load payments");
  } finally {
    loading.value = false;
  }
}

// ── Filters / sort ────────────────────────────────────────────────
const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") r = r.filter(p => p.payment_type === activeTab.value);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(p =>
      (p.name||"").toLowerCase().includes(q) ||
      (p.party||"").toLowerCase().includes(q) ||
      (p.reference_no||"").toLowerCase().includes(q)
    );
  }
  return r;
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const av = a[col] ?? "", bv = b[col] ?? "";
    const cmp = typeof av === "number"
      ? av - bv
      : String(av).localeCompare(String(bv));
    return sortDir.value === "asc" ? cmp : -cmp;
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

// ── Summary ──────────────────────────────────────────────────────
const summaryReceived = computed(() =>
  list.value.filter(p => p.payment_type === "Receive").reduce((s, p) => s + flt(p.paid_amount), 0)
);
const summaryPaid = computed(() =>
  list.value.filter(p => p.payment_type === "Pay").reduce((s, p) => s + flt(p.paid_amount), 0)
);

function fmtCur(v) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v));
}

// ── Selection ────────────────────────────────────────────────────
const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(p => selected.value.has(p.name)));
function toggle(name) {
  const s = new Set(selected.value);
  s.has(name) ? s.delete(name) : s.add(name);
  selected.value = s;
}
function toggleAll(e) {
  selected.value = e.target.checked ? new Set(sorted.value.map(p => p.name)) : new Set();
}

// ── Drawer helpers ────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, blankForm());
  form.payment_type  = activeTab.value !== "all" ? activeTab.value : "Receive";
  form.party_type    = form.payment_type === "Receive" ? "Customer" : "Supplier";
  fetchParties("");
  fetchAccounts("");
  drawerOpen.value = true;
}

function openEdit(p) {
  editingName.value = p.name;
  Object.assign(form, {
    doctype:         "Payment Entry",
    name:            p.name,
    payment_type:    p.payment_type,
    party_type:      p.party_type,
    party:           p.party       || "",
    mode_of_payment: p.mode_of_payment || "",
    paid_amount:     flt(p.paid_amount),
    payment_date:    p.payment_date || new Date().toISOString().slice(0,10),
    reference_no:    p.reference_no  || "",
    reference_date:  p.reference_date || "",
    paid_from:       p.paid_from || "",
    paid_to:         p.paid_to   || "",
    remarks:         p.remarks   || "",
  });
  fetchParties("");
  fetchAccounts("");
  drawerOpen.value = true;
}

function openView(p) {
  viewPmt.value  = p;
  viewOpen.value = true;
}

function setPaymentType(type) {
  form.payment_type = type;
  form.party_type   = type === "Receive" ? "Customer" : "Supplier";
  form.party        = "";
  fetchParties("");
}

// ── Party / account lookups ───────────────────────────────────────
async function fetchParties(q = "") {
  const dt = form.payment_type === "Receive" ? "Customer" : "Supplier";
  try {
    const rows = await apiLinkValues(dt, q || "");
    partyOptions.value = rows.map(r => ({ label: r.name, value: r.name }));
  } catch { partyOptions.value = []; }
}

function onPartySelect(val) { form.party = val; }

async function fetchAccounts(q = "") {
  try {
    const company = await resolveCompany();
    const rows = await apiList("Account", {
      fields: ["name", "account_type"],
      filters: [
        ["is_group", "=", 0],
        ["company", "=", company],
        ...(q ? [["name", "like", `%${q}%`]] : []),
      ],
      limit: 20,
    });
    accounts.value = rows.map(r => ({ label: r.name, value: r.name }));
  } catch { accounts.value = []; }
}

// ── Save ─────────────────────────────────────────────────────────
async function savePayment(docstatus) {
  if (!form.party) return toast.error("Party is required");
  if (!form.paid_amount || flt(form.paid_amount) <= 0) return toast.error("Amount must be greater than 0");
  if (!form.payment_date) return toast.error("Payment date is required");

  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const doc = {
      doctype:         "Payment Entry",
      company,
      payment_type:    form.payment_type,
      party_type:      form.party_type,
      party:           form.party,
      mode_of_payment: form.mode_of_payment || "Cash",
      paid_amount:     flt(form.paid_amount),
      received_amount: flt(form.paid_amount),
      payment_date:    form.payment_date,
      reference_no:    form.reference_no   || "",
      reference_date:  form.reference_date || null,
      paid_from:       form.paid_from  || "",
      paid_to:         form.paid_to    || "",
      remarks:         form.remarks    || "",
      docstatus,
    };
    if (editingName.value) doc.name = editingName.value;

    const saved = await apiSave(doc);
    const name = saved?.name || doc.name;
    toast.success(`Payment ${name} ${docstatus ? "submitted" : "saved"}`);
    drawerOpen.value = false;

    await load();
    if (name && !list.value.find(p => p.name === name)) {
      list.value.unshift({ ...doc, name, docstatus });
    }
  } catch (e) {
    toast.error(e.message || "Failed to save payment");
  } finally {
    drawerSaving.value = false;
  }
}

onMounted(() => { load(); });
</script>

<style scoped>
.pmt-page { display:flex; flex-direction:column; gap:16px; padding:24px; }
.pmt-actions { display:flex; align-items:center; gap:10px; flex-wrap:wrap; }

.pmt-search-wrap {
  display:flex; align-items:center; gap:8px;
  background:#f3f4f6; border-radius:8px; padding:6px 12px;
  min-width:220px;
}
.pmt-search-input { border:none; background:transparent; outline:none; font:inherit; color:#111827; width:100%; font-size:13px; }

.pmt-pills { display:flex; gap:6px; }
.pmt-pill {
  padding:6px 14px; border-radius:20px; font-size:12.5px; font-weight:600;
  border:1px solid #e5e7eb; background:#fff; color:#6b7280; cursor:pointer; font-family:inherit;
}
.pmt-pill.active { background:#eff6ff; border-color:#2563eb; color:#2563eb; }

.pmt-btn-primary {
  display:inline-flex; align-items:center; gap:6px;
  background:#2563eb; color:#fff; border:none; border-radius:8px;
  padding:8px 14px; font-size:13px; font-weight:600; cursor:pointer;
}
.pmt-btn-primary:hover { background:#1d4ed8; }
.pmt-btn-primary:disabled { opacity:.5; cursor:not-allowed; }

.pmt-btn-ghost {
  display:inline-flex; align-items:center; gap:6px;
  background:transparent; border:1px solid #e5e7eb; border-radius:8px;
  padding:8px 12px; font-size:13px; color:#374151; cursor:pointer;
}
.pmt-btn-ghost:hover { background:#f9fafb; }

.pmt-btn-save {
  display:inline-flex; align-items:center; gap:6px;
  background:#f0fdf4; border:1px solid #16a34a; color:#16a34a;
  border-radius:8px; padding:8px 14px; font-size:13px; font-weight:600; cursor:pointer;
}
.pmt-btn-save:hover { background:#dcfce7; }
.pmt-btn-save:disabled { opacity:.5; cursor:not-allowed; }

/* ── Summary ──────────────────────────────────────────────────── */
.pmt-summary { display:grid; grid-template-columns:repeat(4,1fr); gap:12px; }
.pmt-sum-card {
  background:#fff; border:1px solid #e5e7eb; border-radius:10px;
  padding:14px 16px;
}
.pmt-sum-lbl { font-size:11px; color:#6b7280; text-transform:uppercase; letter-spacing:.05em; margin-bottom:4px; }
.pmt-sum-val { font-size:18px; font-weight:700; color:#111827; font-family:monospace; }
.green { color:#16a34a !important; }
.red   { color:#dc2626 !important; }

/* ── Table ────────────────────────────────────────────────────── */
.pmt-card { background:#fff; border:1px solid #e5e7eb; border-radius:10px; overflow:hidden; }
.pmt-table { width:100%; border-collapse:collapse; font-size:13px; }
.pmt-table th {
  background:#f9fafb; border-bottom:1px solid #e5e7eb;
  padding:10px 12px; font-size:11.5px; font-weight:600; color:#374151;
  text-align:left; white-space:nowrap;
}
.pmt-table th.sortable { cursor:pointer; user-select:none; }
.pmt-table th.sortable:hover { color:#2563eb; }
.ta-r { text-align:right !important; }

.pmt-row td { padding:10px 12px; border-bottom:1px solid #f3f4f6; vertical-align:middle; }
.pmt-row:last-child td { border-bottom:none; }
.pmt-row:hover td { background:#f9fafb; }
.pmt-row.selected td { background:#eff6ff; }
.pmt-row td { cursor:pointer; }
.pmt-act-cell { cursor:default !important; }

.pmt-num { font-family:monospace; font-size:12.5px; color:#2563eb; font-weight:600; }
.mono-sm { font-family:monospace; font-size:12.5px; }
.text-muted { color:#6b7280; }
.text-danger { color:#dc2626; }

.pmt-badge {
  display:inline-flex; align-items:center; padding:2px 8px;
  border-radius:10px; font-size:11.5px; font-weight:600;
}
.badge-green { background:#dcfce7; color:#16a34a; }
.badge-red   { background:#fee2e2; color:#dc2626; }

.pmt-act-cell { display:flex; gap:4px; justify-content:flex-end; }
.pmt-act-btn {
  background:transparent; border:1px solid #e5e7eb; border-radius:6px;
  width:26px; height:26px; display:inline-flex; align-items:center; justify-content:center;
  cursor:pointer; color:#6b7280;
}
.pmt-act-btn:hover { background:#f3f4f6; color:#2563eb; }
.pmt-empty { text-align:center; color:#9ca3af; padding:48px 20px !important; font-size:13px; cursor:default !important; }
.pmt-shimmer { height:13px; background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%); border-radius:4px; animation:shimmer 1.2s infinite; background-size:200% 100%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ── Overlay ─────────────────────────────────────────────────── */
.pmt-overlay { position:fixed; inset:0; background:rgba(0,0,0,.2); z-index:40; }

/* ── Drawer ──────────────────────────────────────────────────── */
.pmt-drawer {
  position:fixed; top:0; right:-520px; bottom:0; width:520px;
  background:#fff; border-left:1px solid #e5e7eb;
  box-shadow:-8px 0 24px rgba(0,0,0,.08);
  z-index:50; display:flex; flex-direction:column;
  transition:right .22s ease;
}
.pmt-drawer.open { right:0; }

.pmt-view-drawer { width:440px; right:-440px; }
.pmt-view-drawer.open { right:0; }

.pmt-dheader {
  display:flex; align-items:center; justify-content:space-between;
  padding:0 20px; height:60px; border-bottom:1px solid #e5e7eb;
  flex-shrink:0;
}
.pmt-dheader-title { font-size:15px; font-weight:600; color:#111827; }
.pmt-dclose {
  background:transparent; border:none; cursor:pointer;
  color:#6b7280; display:inline-flex; align-items:center; justify-content:center;
  width:32px; height:32px; border-radius:6px;
}
.pmt-dclose:hover { background:#f3f4f6; color:#111827; }

.pmt-dbody { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:14px; }

/* View head */
.pmt-view-head {
  position:relative; display:flex; align-items:flex-start; justify-content:space-between;
  padding:20px; border-bottom:1px solid #e5e7eb; flex-shrink:0;
}
.head-green { background:#f0fdf4; }
.head-red   { background:#fff1f2; }
.pmt-view-num  { font-size:18px; font-weight:700; font-family:monospace; color:#111827; }
.pmt-view-party{ font-size:13px; color:#6b7280; margin-top:2px; }
.pmt-view-amount{ font-size:22px; font-weight:800; font-family:monospace; color:#111827; }
.pmt-vclose { position:absolute; top:12px; right:12px; }

/* Fields */
.pmt-fields-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.pmt-field { display:flex; flex-direction:column; gap:4px; }
.pmt-label { font-size:12px; font-weight:600; color:#374151; }
.req { color:#dc2626; }
.pmt-input {
  border:1px solid #e5e7eb; border-radius:6px; padding:7px 10px;
  font:inherit; font-size:13px; outline:none; background:#fff; color:#111827;
}
.pmt-input:focus { border-color:#2563eb; box-shadow:0 0 0 2px rgba(37,99,235,.08); }
textarea.pmt-input { resize:vertical; }
.pmt-select {
  border:1px solid #e5e7eb; border-radius:6px; padding:7px 10px;
  font:inherit; font-size:13px; outline:none; background:#fff; color:#111827; cursor:pointer;
}
.pmt-select:focus { border-color:#2563eb; }

/* Radio group */
.pmt-radio-group { display:flex; gap:10px; flex-wrap:wrap; }
.pmt-radio {
  display:flex; align-items:center; gap:8px;
  padding:8px 14px; border:1px solid #e5e7eb; border-radius:8px;
  cursor:pointer; font-size:13px; color:#374151; user-select:none;
}
.pmt-radio.checked { border-color:#2563eb; background:#eff6ff; color:#2563eb; }
.pmt-radio-dot {
  width:14px; height:14px; border-radius:50%; border:2px solid #d1d5db;
  display:inline-block; flex-shrink:0;
}
.pmt-radio-dot.on { border-color:#2563eb; background:#2563eb; box-shadow:inset 0 0 0 3px #fff; }

/* Meta grid */
.pmt-meta-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.pmt-meta-lbl { font-size:11px; color:#9ca3af; text-transform:uppercase; letter-spacing:.05em; margin-bottom:2px; }

/* Footer */
.pmt-dfooter {
  display:flex; align-items:center; justify-content:flex-end; gap:8px;
  padding:14px 20px; border-top:1px solid #e5e7eb; flex-shrink:0;
}
</style>
