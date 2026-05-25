<template>
  <div class="pmt-page">

    <div class="pmt-actions">
      <div class="pmt-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search payments…" class="pmt-search-input" />
      </div>
      <div class="pmt-pills">
        <button v-for="t in tabs" :key="t.key" class="pmt-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="pmt-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="pmt-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Payment</button>
      </div>
    </div>

    <div class="pmt-summary" v-if="!loading">
      <div class="pmt-sum-card"><div class="pmt-sum-lbl">Total Received</div><div class="pmt-sum-val green">{{ fmtCur(summaryReceived) }}</div></div>
      <div class="pmt-sum-card"><div class="pmt-sum-lbl">Total Paid Out</div><div class="pmt-sum-val red">{{ fmtCur(summaryPaid) }}</div></div>
      <div class="pmt-sum-card"><div class="pmt-sum-lbl">Net</div><div class="pmt-sum-val" :class="(summaryReceived-summaryPaid)>=0?'green':'red'">{{ fmtCur(summaryReceived-summaryPaid) }}</div></div>
      <div class="pmt-sum-card"><div class="pmt-sum-lbl">Count</div><div class="pmt-sum-val">{{ filtered.length }}</div></div>
    </div>

    <!-- Bulk action bar (light style, matching Sales Orders/Quotes/Invoices) -->
    <div v-if="selected.size" class="inv-bulk-bar">
      <span class="inv-bulk-count">{{ selected.size }} selected</span>
      <button class="inv-bulk-btn" @click="bulkCancel" :disabled="bulkBusy">Cancel Submitted</button>
      <button class="inv-bulk-btn inv-bulk-danger" @click="bulkDelete" :disabled="bulkBusy">Delete Drafts</button>
      <button class="inv-bulk-btn" @click="bulkExport" :disabled="bulkBusy">
        <span v-html="icon('download',13)"></span> Export CSV
      </button>
      <button class="inv-bulk-clear" @click="selected = new Set()">✕ Clear</button>
    </div>

    <div class="pmt-card">
      <table class="pmt-table">
        <thead><tr>
          <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
          <th @click="sort('name')" class="sortable">Payment # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('party')" class="sortable">Party <span v-html="sortArrow('party')"></span></th>
          <th @click="sort('mode_of_payment')" class="sortable">Mode <span v-html="sortArrow('mode_of_payment')"></span></th>
          <th @click="sort('reference_no')" class="sortable">Reference <span v-html="sortArrow('reference_no')"></span></th>
          <th @click="sort('payment_date')" class="sortable">Date <span v-html="sortArrow('payment_date')"></span></th>
          <th>Type</th>
          <th @click="sort('paid_amount')" class="sortable ta-r">Amount <span v-html="sortArrow('paid_amount')"></span></th>
          <th style="width:60px"></th>
        </tr></thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="9"><div class="pmt-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="p in sorted" :key="p.name" class="pmt-row" :class="{selected:selected.has(p.name)}">
              <td><input type="checkbox" :checked="selected.has(p.name)" @change="toggle(p.name)" /></td>
              <td @click="openView(p)"><span class="pmt-num">{{ p.name }}</span></td>
              <td @click="openView(p)">{{ p.party_name||p.party||'—' }}</td>
              <td @click="openView(p)" class="text-muted">{{ p.mode_of_payment||'—' }}</td>
              <td @click="openView(p)" class="text-muted mono-sm">{{ p.reference_no||'—' }}</td>
              <td @click="openView(p)" class="text-muted mono-sm">{{ fmtDate(p.payment_date) }}</td>
              <td @click="openView(p)">
                <span class="pmt-badge" :class="p.payment_type==='Receive'?'badge-green':'badge-red'">
                  {{ p.payment_type==='Receive'?'Received':'Paid Out' }}
                </span>
              </td>
              <td @click="openView(p)" class="ta-r mono-sm" :class="p.payment_type==='Receive'?'green':'red'">{{ fmtCur(p.paid_amount) }}</td>
              <td class="pmt-act-cell">
                <button class="pmt-act-btn" @click="openView(p)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="p.docstatus===0" class="pmt-act-btn" @click="openEdit(p)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button v-if="p.docstatus===1" class="pmt-act-btn" style="border-color:#fee2e2;color:#dc2626" @click="cancelPmt(p)" title="Cancel">✕</button>
                <button v-if="p.docstatus===0 || p.docstatus===2" class="pmt-act-btn" style="border-color:#fee2e2;color:#dc2626" @click="deletePmt(p)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="9" class="pmt-empty">No payments found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit drawer -->
    <div v-if="drawerOpen" class="pmt-overlay" @click.self="drawerOpen=false"></div>
    <div class="pmt-drawer" :class="{open:drawerOpen}">
      <div class="pmt-dheader" :class="form.payment_type==='Pay'?'pay':'recv'">
        <div class="pmt-dheader-left">
          <div class="pmt-dheader-ico" :class="form.payment_type==='Pay'?'pay':'recv'">
            <span v-html="icon(form.payment_type==='Pay'?'expense':'invoices',18)"></span>
          </div>
          <div>
            <div class="pmt-dheader-title">{{ editingName?'Edit Payment':'New Payment' }}</div>
            <div class="pmt-dheader-sub">
              {{ editingName ? editingName : (form.payment_type==='Pay'?'Record an outgoing payment to a vendor':'Record a payment received from a customer') }}
            </div>
          </div>
        </div>
        <button class="pmt-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="pmt-dbody">
        <!-- Section: Payment Type -->
        <div class="pmt-section">
          <div class="pmt-section-hdr-bar">
            <span v-html="icon('refresh',13)"></span>
            <span>Payment Type</span>
          </div>
          <div class="pmt-radio-group">
            <label class="pmt-radio" :class="{checked:form.payment_type==='Receive'}" @click="setPaymentType('Receive')">
              <span class="pmt-radio-dot" :class="{on:form.payment_type==='Receive'}"></span>
              <div>
                <div class="pmt-radio-title">Received</div>
                <div class="pmt-radio-sub">from a customer</div>
              </div>
            </label>
            <label class="pmt-radio" :class="{checked:form.payment_type==='Pay'}" @click="setPaymentType('Pay')">
              <span class="pmt-radio-dot" :class="{on:form.payment_type==='Pay'}"></span>
              <div>
                <div class="pmt-radio-title">Paid Out</div>
                <div class="pmt-radio-sub">to a vendor</div>
              </div>
            </label>
          </div>
        </div>

        <!-- Section: Party & Amount -->
        <div class="pmt-section">
          <div class="pmt-section-hdr-bar">
            <span v-html="icon('user',13)"></span>
            <span>{{ form.payment_type==='Receive'?'Customer & Amount':'Vendor & Amount' }}</span>
          </div>
          <div class="pmt-fields-grid">
            <div class="pmt-field" style="grid-column:1/-1">
              <label class="pmt-label">{{ form.payment_type==='Receive'?'Customer':'Vendor' }} <span class="req">*</span></label>
              <SearchableSelect v-model="form.party" :options="partyOptions"
                :placeholder="form.payment_type==='Receive'?'Select customer…':'Select vendor…'"
                @search="fetchParties" @select="onPartySelect" />
            </div>
            <div class="pmt-field">
              <label class="pmt-label">Amount <span class="req">*</span></label>
              <input v-model.number="form.paid_amount" type="number" min="0" step="0.01" class="pmt-input" placeholder="0.00" @input="syncUnallocated" />
            </div>
            <div class="pmt-field">
              <label class="pmt-label">Mode of Payment</label>
              <select v-model="form.mode_of_payment" class="pmt-select">
                <option value="">— Select —</option>
                <option v-for="m in paymentModes" :key="m" :value="m">{{ m }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Section: Reference & Dates -->
        <div class="pmt-section">
          <div class="pmt-section-hdr-bar">
            <span v-html="icon('hash',13)"></span>
            <span>Reference & Dates</span>
          </div>
          <div class="pmt-fields-grid">
            <div class="pmt-field">
              <label class="pmt-label">Payment Date <span class="req">*</span></label>
              <input v-model="form.payment_date" type="date" class="pmt-input" />
            </div>
            <div class="pmt-field">
              <label class="pmt-label">Reference Date</label>
              <input v-model="form.reference_date" type="date" class="pmt-input" />
            </div>
            <div class="pmt-field" style="grid-column:1/-1">
              <label class="pmt-label">Reference / Cheque No</label>
              <input v-model="form.reference_no" type="text" class="pmt-input" placeholder="e.g. CHQ-001, NEFT-78902" />
            </div>
          </div>
        </div>

        <!-- Section: Accounts -->
        <div class="pmt-section">
          <div class="pmt-section-hdr-bar">
            <span v-html="icon('ledger',13)"></span>
            <span>Accounts</span>
          </div>
          <div class="pmt-fields-grid">
            <div class="pmt-field">
              <label class="pmt-label">Paid From</label>
              <SearchableSelect v-model="form.paid_from" :options="accounts" placeholder="Select account…" @search="fetchAccounts" />
            </div>
            <div class="pmt-field">
              <label class="pmt-label">Paid To</label>
              <SearchableSelect v-model="form.paid_to" :options="accounts" placeholder="Select account…" @search="fetchAccounts" />
            </div>
          </div>
        </div>

        <!-- Section: Allocation -->
        <div class="pmt-section">
          <div class="pmt-section-hdr-bar">
            <span v-html="icon('check',13)"></span>
            <span>Outstanding {{ form.payment_type==='Receive'?'Invoices':'Bills' }}</span>
            <span class="pmt-unalloc" :class="unallocated<-0.01?'red':unallocated>0.01?'orange':''">
              Unallocated: {{ fmtCur(unallocated) }}
            </span>
          </div>
          <div v-if="!form.party" class="pmt-inv-empty">Select a party to load outstanding invoices</div>
          <div v-else-if="invLoading" class="pmt-inv-empty"><span style="color:#9ca3af">Loading invoices…</span></div>
          <div v-else-if="!outstandingInvoices.length" class="pmt-inv-empty">No outstanding {{ form.payment_type==='Receive'?'invoices':'bills' }} for this party</div>
          <div v-else class="pmt-inv-table">
            <div class="pmt-inv-head">
              <div></div><div>Document</div><div>Date</div>
              <div class="ta-r">Outstanding</div><div class="ta-r">Allocate</div>
            </div>
            <div v-for="ref in invoiceRefs" :key="ref.reference_name" class="pmt-inv-row">
              <div><input type="checkbox" v-model="ref.checked" @change="onRefCheck(ref)" /></div>
              <div><span class="pmt-inv-name">{{ ref.reference_name }}</span></div>
              <div class="mono-sm text-muted">{{ fmtDate(ref.due_date) }}</div>
              <div class="ta-r mono-sm">{{ fmtCur(ref.outstanding_amount) }}</div>
              <div>
                <input v-if="ref.checked" v-model.number="ref.allocated_amount" type="number" min="0" :max="ref.outstanding_amount" step="0.01" class="pmt-alloc-input" @input="syncUnallocated" />
                <span v-else class="mono-sm text-muted">—</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Section: Notes -->
        <div class="pmt-section">
          <div class="pmt-section-hdr-bar">
            <span v-html="icon('mail',13)"></span>
            <span>Notes</span>
          </div>
          <textarea v-model="form.remarks" rows="3" class="pmt-input" placeholder="Optional notes about this payment…"></textarea>
        </div>
      </div>

      <div class="pmt-dfooter">
        <button class="pmt-btn-ghost" @click="drawerOpen=false" :disabled="drawerSaving">Cancel</button>
        <button class="pmt-btn-save" :disabled="drawerSaving" @click="savePayment(0)">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="pmt-btn-primary" :disabled="drawerSaving" @click="savePayment(1)">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}
        </button>
      </div>
    </div>

    <!-- View drawer -->
    <div v-if="viewOpen" class="pmt-overlay" @click.self="viewOpen=false"></div>
    <div class="pmt-drawer pmt-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewPmt">
        <div class="pmt-view-head" :class="viewPmt.payment_type==='Receive'?'head-green':'head-red'">
          <div>
            <div class="pmt-view-num">{{ viewPmt.name }}</div>
            <div class="pmt-view-party">
              <DocLink :doctype="viewPmt.party_type || (viewPmt.payment_type==='Receive'?'Customer':'Supplier')" :name="viewPmt.party" :mono-style="false">
                {{ viewPmt.party_name || viewPmt.party || '—' }}
              </DocLink>
            </div>
          </div>
          <div style="text-align:right">
            <div class="pmt-view-amount">{{ fmtCur(viewPmt.paid_amount) }}</div>
            <span class="pmt-badge" :class="viewPmt.payment_type==='Receive'?'badge-green':'badge-red'">
              {{ viewPmt.payment_type==='Receive'?'Received':'Paid Out' }}
            </span>
          </div>
          <button class="pmt-dclose pmt-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="pmt-dbody">
          <div class="pmt-meta-grid">
            <div><div class="pmt-meta-lbl">Payment Date</div><div>{{ fmtDate(viewPmt.payment_date) }}</div></div>
            <div><div class="pmt-meta-lbl">Mode</div><div>{{ viewPmt.mode_of_payment||'—' }}</div></div>
            <div><div class="pmt-meta-lbl">Reference No</div><div class="mono-sm">{{ viewPmt.reference_no||'—' }}</div></div>
            <div><div class="pmt-meta-lbl">Reference Date</div><div class="mono-sm">{{ fmtDate(viewPmt.reference_date) }}</div></div>
            <div><div class="pmt-meta-lbl">Paid From</div><div>{{ viewPmt.paid_from||'—' }}</div></div>
            <div><div class="pmt-meta-lbl">Paid To</div><div>{{ viewPmt.paid_to||'—' }}</div></div>
          </div>
          <!-- Linked references -->
          <div v-if="viewPmt.references&&viewPmt.references.length">
            <div class="pmt-section-hdr" style="margin-bottom:8px">Linked Documents</div>
            <div class="pmt-inv-table">
              <div class="pmt-inv-head"><div></div><div>Document</div><div class="ta-r">Outstanding</div><div class="ta-r">Allocated</div></div>
              <div v-for="r in viewPmt.references" :key="r.reference_name" class="pmt-inv-row">
                <div></div>
                <div><DocLink :doctype="r.reference_doctype || (viewPmt.payment_type==='Receive'?'Sales Invoice':'Purchase Invoice')" :name="r.reference_name" /></div>
                <div class="ta-r mono-sm">{{ fmtCur(r.outstanding_amount) }}</div>
                <div class="ta-r mono-sm green">{{ fmtCur(r.allocated_amount) }}</div>
              </div>
            </div>
          </div>
          <div v-if="viewPmt.remarks" style="grid-column:1/-1">
            <div class="pmt-meta-lbl">Remarks</div><div>{{ viewPmt.remarks }}</div>
          </div>
        </div>
        <div class="pmt-dfooter">
          <button class="pmt-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewPmt.docstatus===0" class="pmt-btn-save" @click="openEdit(viewPmt);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button v-if="viewPmt.docstatus===1" class="pmt-btn-ghost" style="border-color:#dc2626;color:#dc2626" @click="cancelPmt(viewPmt)">
            Cancel Payment
          </button>
          <button v-if="viewPmt.docstatus===0 || viewPmt.docstatus===2" class="pmt-btn-ghost" style="border-color:#dc2626;color:#dc2626" @click="deletePmt(viewPmt)">
            <span v-html="icon('trash',13)"></span> Delete
          </button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { useRoute } from "vue-router";
import { apiList, apiGet, apiGET, apiSave, apiSubmit, apiPOST, apiDelete, resolveCompany, apiLinkValues } from "../api/client.js";
import { useConfirm } from "../composables/useConfirm.js";
import { useOpenFromQuery } from "../composables/useOpenFromQuery.js";
import DocLink from "../components/DocLink.vue";
const { confirm } = useConfirm();

async function cancelPmt(p) {
  if (!await confirm({ title: "Cancel Payment", body: `Cancel ${p.name}? Linked invoices/bills will reflect the reversal.`, okLabel: "Cancel Payment" })) return;
  try {
    await apiPOST("zoho_books_clone.api.docs.cancel_payment_entry_safe",
      { payment_entry_name: p.name });
    toast.success(`Payment ${p.name} cancelled`);
    viewOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Cancel failed"); }
}
async function deletePmt(p) {
  if (!await confirm({ title: "Delete Payment", body: `Permanently delete ${p.name}? This cannot be undone.`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Payment Entry", p.name);
    toast.success(`Payment ${p.name} deleted`);
    viewOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ─── Bulk actions ──────────────────────────────────────────────────────
const bulkBusy = ref(false);
function selectedRows() {
  return sorted.value.filter(p => selected.value.has(p.name));
}
async function bulkCancel() {
  const rows = selectedRows().filter(p => p.docstatus === 1);
  if (!rows.length) { toast.info?.("No submitted payments selected") || toast.error("No submitted payments selected"); return; }
  if (!await confirm({ title: `Cancel ${rows.length} payment(s)?`, body: "Linked invoices/bills will reflect the reversal.", okLabel: "Cancel All", okStyle: "danger" })) return;
  bulkBusy.value = true;
  let ok = 0, fail = 0;
  for (const p of rows) {
    try { await apiPOST("zoho_books_clone.api.docs.cancel_payment_entry_safe", { payment_entry_name: p.name }); ok++; }
    catch { fail++; }
  }
  bulkBusy.value = false;
  toast.success(`${ok} cancelled${fail?`, ${fail} failed`:''}`);
  selected.value = new Set();
  await load();
}
async function bulkDelete() {
  const rows = selectedRows().filter(p => p.docstatus === 0 || p.docstatus === 2);
  if (!rows.length) { toast.error("No draft/cancelled payments selected"); return; }
  if (!await confirm({ title: `Delete ${rows.length} payment(s)?`, body: "Only drafts and cancelled records can be deleted. This cannot be undone.", okLabel: "Delete All", okStyle: "danger" })) return;
  bulkBusy.value = true;
  let ok = 0, fail = 0;
  for (const p of rows) {
    try { await apiDelete("Payment Entry", p.name); ok++; }
    catch { fail++; }
  }
  bulkBusy.value = false;
  toast.success(`${ok} deleted${fail?`, ${fail} failed`:''}`);
  selected.value = new Set();
  await load();
}
function bulkExport() {
  const rows = selectedRows();
  if (!rows.length) return;
  const headers = ["Payment #","Party","Mode","Reference","Reference Date","Payment Date","Type","Amount","Status"];
  const lines = rows.map(p => [
    p.name, p.party_name || p.party || "", p.mode_of_payment || "",
    p.reference_no || "", p.reference_date || "", p.payment_date || "",
    p.payment_type === "Receive" ? "Received" : "Paid Out",
    p.paid_amount,
    p.docstatus === 1 ? "Submitted" : p.docstatus === 2 ? "Cancelled" : "Draft",
  ]);
  const esc = (v) => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const csv = "﻿" + [headers, ...lines].map(r => r.map(esc).join(",")).join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `payments-${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  toast.success(`${rows.length} row(s) exported`);
}
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const route = useRoute();
const defaultTab = route.path === "/payments-received" ? "Receive" : "Pay";
const activeTab = ref(defaultTab);
const tabs = [{key:"all",label:"All"},{key:"Receive",label:"Received"},{key:"Pay",label:"Paid Out"}];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewPmt = ref(null);
const partyOptions = ref([]), accounts = ref([]);
const paymentModes = ref(["Cash","Bank Transfer","Cheque","Credit Card","UPI","NEFT","RTGS"]);
const sortCol = ref("payment_date"), sortDir = ref("desc");

// Invoice linking state
const outstandingInvoices = ref([]);
const invoiceRefs = ref([]);
const invLoading = ref(false);

const blankForm = () => ({
  doctype: "Payment Entry",
  payment_type: defaultTab === "Receive" ? "Receive" : "Pay",
  party_type: defaultTab === "Receive" ? "Customer" : "Supplier",
  party: "", mode_of_payment: "", paid_amount: "",
  payment_date: new Date().toISOString().slice(0,10),
  reference_no: "", reference_date: "", paid_from: "", paid_to: "", remarks: "",
});
const form = reactive(blankForm());

const unallocated = computed(() => {
  const alloc = invoiceRefs.value.filter(r => r.checked).reduce((s, r) => s + flt(r.allocated_amount), 0);
  return flt(form.paid_amount) - alloc;
});

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Payment Entry", {
      fields: ["name","party","party_name","party_type","paid_amount","payment_type","payment_date",
               "mode_of_payment","reference_no","reference_date","paid_from","paid_to","remarks","docstatus"],
      limit: 200, order: "payment_date desc",
    });
  } catch (e) { toast.error(e.message || "Failed to load payments"); }
  finally { loading.value = false; }
}

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") r = r.filter(p => p.payment_type === activeTab.value);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(p => (p.name||"").toLowerCase().includes(q) || (p.party_name||p.party||"").toLowerCase().includes(q) || (p.reference_no||"").toLowerCase().includes(q));
  }
  return r;
});
const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const av = a[col] ?? "", bv = b[col] ?? "";
    const cmp = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv));
    return sortDir.value === "asc" ? cmp : -cmp;
  });
});
function sort(col) { if (sortCol.value===col) sortDir.value=sortDir.value==="asc"?"desc":"asc"; else{sortCol.value=col;sortDir.value="asc";} }
function sortArrow(col) { if (sortCol.value!==col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value==="asc"?"↑":"↓"; }

const summaryReceived = computed(() => list.value.filter(p=>p.payment_type==="Receive").reduce((s,p)=>s+flt(p.paid_amount),0));
const summaryPaid = computed(() => list.value.filter(p=>p.payment_type==="Pay").reduce((s,p)=>s+flt(p.paid_amount),0));
function fmtCur(v) { return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v)); }

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(p => selected.value.has(p.name)));
function toggle(name) { const s = new Set(selected.value); s.has(name)?s.delete(name):s.add(name); selected.value=s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(p=>p.name)) : new Set(); }

function openNew() {
  editingName.value = "";
  Object.assign(form, blankForm());
  form.payment_type = activeTab.value !== "all" ? activeTab.value : "Receive";
  form.party_type = form.payment_type === "Receive" ? "Customer" : "Supplier";
  outstandingInvoices.value = [];
  invoiceRefs.value = [];
  fetchParties(""); fetchAccounts("");
  drawerOpen.value = true;
}

async function openEdit(p) {
  editingName.value = p.name;
  Object.assign(form, {
    doctype: "Payment Entry", name: p.name, payment_type: p.payment_type,
    party_type: p.party_type, party: p.party||"", mode_of_payment: p.mode_of_payment||"",
    paid_amount: flt(p.paid_amount), payment_date: p.payment_date||new Date().toISOString().slice(0,10),
    reference_no: p.reference_no||"", reference_date: p.reference_date||"",
    paid_from: p.paid_from||"", paid_to: p.paid_to||"", remarks: p.remarks||"",
  });
  outstandingInvoices.value = []; invoiceRefs.value = [];
  fetchParties(""); fetchAccounts("");
  drawerOpen.value = true;
  if (p.party) await fetchOutstandingInvoices(p.party, p.payment_type);
}

async function openView(p) {
  viewPmt.value = p;
  viewOpen.value = true;
  // Fetch full doc to get references child table
  try {
    const doc = await apiGet("Payment Entry", p.name);
    viewPmt.value = { ...p, references: doc.references || [] };
  } catch {}
}

function setPaymentType(type) {
  form.payment_type = type;
  form.party_type = type === "Receive" ? "Customer" : "Supplier";
  form.party = "";
  outstandingInvoices.value = []; invoiceRefs.value = [];
  fetchParties("");
}

async function fetchParties(q = "") {
  const dt = form.payment_type === "Receive" ? "Customer" : "Supplier";
  const nameField = dt === "Customer" ? "customer_name" : "supplier_name";
  try {
    const filters = [["disabled", "=", 0]];
    if (q) filters.push([nameField, "like", "%" + q + "%"]);
    const rows = await apiList(dt, { fields: ["name", nameField], filters, limit: 30, order: nameField + " asc" });
    partyOptions.value = rows.map(r => ({ label: r[nameField] || r.name, value: r.name }));
  } catch { partyOptions.value = []; }
}

async function onPartySelect(opt) {
  // SearchableSelect's @select emits the full {label, value} option object;
  // v-model="form.party" already updates form.party via update:modelValue.
  // Outstanding-invoice loading is handled by the watch() below, so this
  // handler is now a no-op kept for backwards compatibility.
  const party = (opt && typeof opt === "object") ? opt.value : opt;
  if (party && typeof party === "string" && party !== form.party) form.party = party;
}

// Reload outstanding invoices/bills whenever the party OR payment type changes,
// regardless of which UI control mutated them.
watch(() => [form.party, form.payment_type], async ([p, t], [oldP, oldT]) => {
  if (!p) {
    outstandingInvoices.value = [];
    invoiceRefs.value = [];
    return;
  }
  if (p === oldP && t === oldT) return;
  await fetchOutstandingInvoices(p, t);
});

async function fetchOutstandingInvoices(party, pmtType) {
  if (!party) return;
  invLoading.value = true;
  try {
    const dt = pmtType === "Receive" ? "Sales Invoice" : "Purchase Invoice";
    const partyField = pmtType === "Receive" ? "customer" : "supplier";
    const co = await resolveCompany();
    const rows = await apiList(dt, {
      fields: ["name", "posting_date", "due_date", "grand_total", "outstanding_amount"],
      filters: [["company","=",co],[partyField,"=",party],["docstatus","=",1],["outstanding_amount",">",0]],
      limit: 50, order: "posting_date asc",
    });
    outstandingInvoices.value = rows;
    invoiceRefs.value = rows.map(r => ({
      reference_doctype: dt,
      reference_name: r.name,
      outstanding_amount: flt(r.outstanding_amount),
      due_date: r.due_date || r.posting_date,
      allocated_amount: 0,
      checked: false,
    }));
  } catch { outstandingInvoices.value = []; invoiceRefs.value = []; }
  finally { invLoading.value = false; }
}

function onRefCheck(ref) {
  if (ref.checked && ref.allocated_amount === 0) {
    // Auto-fill with min(outstanding, remaining unallocated)
    const used = invoiceRefs.value.filter(r => r.checked && r !== ref).reduce((s,r) => s+flt(r.allocated_amount), 0);
    const remaining = flt(form.paid_amount) - used;
    ref.allocated_amount = Math.min(flt(ref.outstanding_amount), Math.max(0, remaining));
  }
}

function syncUnallocated() {} // triggers computed

async function fetchAccounts(q = "") {
  try {
    const company = await resolveCompany();
    const rows = await apiList("Account", {
      fields: ["name","account_type"],
      filters: [["is_group","=",0],["company","=",company],...(q?[["name","like",`%${q}%`]]:[])],
      limit: 20,
    });
    accounts.value = rows.map(r=>({label:r.name,value:r.name}));
  } catch { accounts.value = []; }
}

async function savePayment(submit) {
  if (!form.party) return toast.error("Party is required");
  if (!form.paid_amount || flt(form.paid_amount) <= 0) return toast.error("Amount must be greater than 0");
  if (!form.payment_date) return toast.error("Payment date is required");
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const checkedRefs = invoiceRefs.value.filter(r => r.checked && flt(r.allocated_amount) > 0);
    const references = checkedRefs.map(r => ({
      doctype: "Payment Entry Reference",
      reference_doctype: r.reference_doctype,
      reference_name: r.reference_name,
      outstanding_amount: flt(r.outstanding_amount),
      allocated_amount: flt(r.allocated_amount),
    }));
    // Resolve party_name from the selected option so Frappe stores it on the record
    const selectedPartyOpt = partyOptions.value.find(o => o.value === form.party);
    const partyName = selectedPartyOpt?.label || form.party;
    const doc = {
      doctype: "Payment Entry", company,
      payment_type: form.payment_type, party_type: form.party_type, party: form.party, party_name: partyName,
      mode_of_payment: form.mode_of_payment || "Cash",
      paid_amount: flt(form.paid_amount), received_amount: flt(form.paid_amount),
      payment_date: form.payment_date,
      reference_no: form.reference_no || "", reference_date: form.reference_date || null,
      paid_from: form.paid_from || "", paid_to: form.paid_to || "",
      remarks: form.remarks || "",
      references,
    };
    if (editingName.value) doc.name = editingName.value;
    const saved = await apiSave(doc);
    if (submit) await apiSubmit("Payment Entry", saved.name);
    toast.success(`Payment ${saved?.name||""} ${submit?"submitted":"saved"}`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save payment"); }
  finally { drawerSaving.value = false; }
}

onMounted(async () => {
  await load();
  useOpenFromQuery({
    list: () => sorted.value,
    openByName: (n) => { const r = sorted.value.find(x => x.name === n); if (r) openView(r); },
  });
});
</script>

<style scoped>
.pmt-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.pmt-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.pmt-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.pmt-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.pmt-pills{display:flex;gap:6px;}
.pmt-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.pmt-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.pmt-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.pmt-btn-primary:hover{background:#1d4ed8;}.pmt-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.pmt-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.pmt-btn-ghost:hover{background:#f9fafb;}
.pmt-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.pmt-btn-save:hover{background:#dcfce7;}.pmt-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.pmt-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.pmt-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.pmt-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.pmt-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}.orange{color:#ea580c!important;}
.inv-bulk-bar{display:flex;align-items:center;gap:8px;padding:10px 16px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;flex-wrap:wrap;}
.inv-bulk-count{font-size:13px;font-weight:700;color:#1a6ef7;margin-right:4px;}
.inv-bulk-btn{display:inline-flex;align-items:center;gap:5px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:5px 12px;font-size:12.5px;font-weight:600;color:#374151;cursor:pointer;font-family:inherit;transition:border-color .15s,background .15s,color .15s;}
.inv-bulk-btn:hover:not(:disabled){background:#f8fafc;border-color:#1a6ef7;color:#1a6ef7;}
.inv-bulk-btn:disabled{opacity:.5;cursor:not-allowed;}
.inv-bulk-danger{border-color:rgba(220,38,38,.3);color:#dc2626;}
.inv-bulk-danger:hover:not(:disabled){background:#fee2e2;border-color:#dc2626;color:#dc2626;}
.inv-bulk-clear{background:none;border:none;font-size:12.5px;color:#6b7280;cursor:pointer;font-family:inherit;padding:4px 8px;border-radius:4px;}
.inv-bulk-clear:hover{background:#e0e7ff;color:#1a6ef7;}

.pmt-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.pmt-table{width:100%;border-collapse:collapse;font-size:13px;}
.pmt-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.pmt-table th.sortable{cursor:pointer;user-select:none;}.pmt-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.pmt-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.pmt-row:last-child td{border-bottom:none;}.pmt-row:hover td{background:#f9fafb;}.pmt-row.selected td{background:#eff6ff;}
.pmt-act-cell{cursor:default!important;display:flex;gap:4px;justify-content:flex-end;}
.pmt-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.pmt-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-red{background:#fee2e2;color:#dc2626;}
.pmt-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.pmt-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.pmt-empty{text-align:center;color:#9ca3af;padding:48px 20px!important;font-size:13px;cursor:default!important;}
.pmt-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.pmt-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);backdrop-filter:blur(2px);z-index:40;}
.pmt-drawer{position:fixed;top:0;right:-580px;bottom:0;width:580px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-12px 0 32px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s cubic-bezier(.32,.72,0,1);}
.pmt-drawer.open{right:0;}
.pmt-view-drawer{width:520px;right:-520px;}.pmt-view-drawer.open{right:0;}

.pmt-dheader{display:flex;align-items:flex-start;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.pmt-dheader.recv{background:linear-gradient(135deg,#f0fdf4 0%,#bbf7d0 100%);}
.pmt-dheader.pay{background:linear-gradient(135deg,#fff1f2 0%,#fecaca 100%);}
.pmt-dheader-left{display:flex;align-items:flex-start;gap:12px;}
.pmt-dheader-ico{width:38px;height:38px;border-radius:10px;background:#fff;border:1px solid rgba(37,99,235,.18);display:inline-flex;align-items:center;justify-content:center;color:#2563eb;box-shadow:0 1px 3px rgba(15,23,42,.06);flex-shrink:0;}
.pmt-dheader-ico.recv{color:#16a34a;border-color:rgba(22,163,74,.22);}
.pmt-dheader-ico.pay{color:#dc2626;border-color:rgba(220,38,38,.25);}
.pmt-dheader-title{font-size:15px;font-weight:700;color:#111827;letter-spacing:-0.01em;}
.pmt-dheader-sub{font-size:12px;color:#475569;margin-top:3px;font-weight:500;}
.pmt-dclose{background:rgba(255,255,255,.6);border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;transition:background .15s;}
.pmt-dclose:hover{background:#fff;color:#111827;}

.pmt-dbody{flex:1;overflow-y:auto;padding:18px 20px;display:flex;flex-direction:column;gap:14px;background:#f8fafc;}

/* Section cards */
.pmt-section{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:12px;box-shadow:0 1px 2px rgba(15,23,42,.03);}
.pmt-section-hdr-bar{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#0f172a;}
.pmt-section-hdr-bar svg{color:#2563eb;}
.pmt-section-hdr-bar .pmt-unalloc{margin-left:auto;text-transform:none;font-size:11.5px;font-weight:700;color:#16a34a;}
.pmt-section-hdr-bar .pmt-unalloc.red{color:#dc2626;}
.pmt-section-hdr-bar .pmt-unalloc.orange{color:#ea580c;}
.pmt-view-head{position:relative;display:flex;align-items:flex-start;justify-content:space-between;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.head-green{background:#f0fdf4;}.head-red{background:#fff1f2;}
.pmt-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.pmt-view-party{font-size:13px;color:#6b7280;margin-top:2px;}
.pmt-view-amount{font-size:22px;font-weight:800;font-family:monospace;color:#111827;}
.pmt-vclose{position:absolute;top:12px;right:12px;}
.pmt-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.pmt-field{display:flex;flex-direction:column;gap:4px;}
.pmt-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.pmt-input,.pmt-select{border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;transition:border-color .15s, box-shadow .15s;}
.pmt-input:hover:not(:disabled),.pmt-select:hover:not(:disabled){border-color:#cbd5e1;}
.pmt-input:focus,.pmt-select:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12);}
.pmt-input:disabled,.pmt-select:disabled{background:#f1f5f9;color:#94a3b8;cursor:not-allowed;border-color:#e2e8f0;}
textarea.pmt-input{resize:vertical;font-family:inherit;}
.pmt-select{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;cursor:pointer;}
.pmt-select:focus{border-color:#2563eb;}
.pmt-radio-group{display:grid;grid-template-columns:1fr 1fr;gap:10px;}
.pmt-radio{display:flex;align-items:center;gap:10px;padding:10px 14px;border:1px solid #e5e7eb;border-radius:10px;cursor:pointer;font-size:13px;color:#374151;user-select:none;transition:border-color .15s,background .15s,box-shadow .15s;}
.pmt-radio:hover{border-color:#cbd5e1;}
.pmt-radio.checked{border-color:#2563eb;background:#eff6ff;box-shadow:0 0 0 3px rgba(37,99,235,.10);}
.pmt-radio-dot{width:16px;height:16px;border-radius:50%;border:2px solid #d1d5db;display:inline-block;flex-shrink:0;transition:border-color .15s, background .15s;}
.pmt-radio-dot.on{border-color:#2563eb;background:#2563eb;box-shadow:inset 0 0 0 3px #fff;}
.pmt-radio-title{font-weight:600;color:#0f172a;font-size:13px;line-height:1.2;}
.pmt-radio.checked .pmt-radio-title{color:#1d4ed8;}
.pmt-radio-sub{font-size:11.5px;color:#6b7280;margin-top:2px;}
.pmt-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.pmt-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
/* Invoice section */
.pmt-section-hdr{display:flex;align-items:center;justify-content:space-between;font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;padding-bottom:6px;border-bottom:1px solid #f3f4f6;}
.pmt-unalloc{font-family:monospace;font-size:12px;font-weight:600;color:#6b7280;}
.pmt-inv-empty{font-size:12.5px;color:#9ca3af;padding:18px 0;text-align:center;background:#f9fafb;border:1px dashed #e5e7eb;border-radius:8px;}
.pmt-inv-table{border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;font-size:12.5px;background:#fff;}
.pmt-inv-head{display:grid;grid-template-columns:24px 1fr 90px 90px 90px;gap:8px;background:#f9fafb;padding:8px 10px;font-size:11px;font-weight:600;color:#6b7280;text-transform:uppercase;letter-spacing:.04em;}
.pmt-inv-row{display:grid;grid-template-columns:24px 1fr 90px 90px 90px;gap:8px;padding:8px 10px;border-top:1px solid #f3f4f6;align-items:center;}
.pmt-inv-row:hover{background:#f9fafb;}
.pmt-inv-name{font-family:monospace;color:#2563eb;font-weight:600;}
.pmt-alloc-input{width:80px;border:1px solid #e2e8f0;border-radius:6px;padding:4px 8px;font:inherit;font-size:12px;text-align:right;outline:none;}
.pmt-alloc-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.10);}
.pmt-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;background:#fff;flex-shrink:0;}
</style>