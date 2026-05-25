<template>
  <div class="dn-page">

    <!-- ── Toolbar ── -->
    <div class="dn-actions">
      <div class="dn-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search debit notes, vendors…" class="dn-search-input" />
      </div>
      <div class="dn-pills">
        <button v-for="t in tabs" :key="t.key"
          class="dn-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">
          {{ t.label }}
          <span v-if="t.key!=='all'" class="dn-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="dn-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="dn-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="dn-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Debit Note</button>
      </div>
    </div>

    <!-- ── Summary strip ── -->
    <SummaryStrip :cards="[
      { label: 'Total Debit Notes', value: list.length },
      { label: 'Total Issued', value: counts.issued, accent: '#16a34a' },
      { label: 'Open Balance', value: fmtCur(summary.openBalance), accent: '#dc2626' },
      { label: 'Total Value', value: fmtCur(summary.totalValue), accent: '#7c2d12' },
    ]" />

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button class="bab-danger" @click="bulkDelete">Delete Drafts</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="dn-card">
      <table class="dn-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">Debit Note # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('supplier_name')" class="sortable">Vendor <span v-html="sortArrow('supplier_name')"></span></th>
            <th @click="sortBy('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
            <th>Against Bill</th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th class="ta-r">Available</th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="9"><div class="dn-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="d in sorted" :key="d.name" class="dn-row" :class="{selected:selected.has(d.name)}">
              <td><input type="checkbox" :checked="selected.has(d.name)" @change="toggle(d.name)" /></td>
              <td @click="openView(d)"><span class="dn-num">{{ d.name }}</span></td>
              <td @click="openView(d)">{{ d.supplier_name || d.supplier || '—' }}</td>
              <td @click="openView(d)" class="text-muted mono-sm">{{ fmtDate(d.posting_date) }}</td>
              <td @click="openView(d)" class="text-muted mono-sm">{{ d.return_against||'—' }}</td>
              <td @click="openView(d)"><span class="dn-badge" :class="statusCls(d)">{{ statusLabel(d) }}</span></td>
              <td @click="openView(d)" class="ta-r mono-sm" style="color:#7c2d12">{{ fmtCur(Math.abs(d.grand_total||0)) }}</td>
              <td @click="openView(d)" class="ta-r mono-sm">
                <span v-if="d.docstatus===1" :class="balanceFor(d.name)>0?'text-danger':'text-success'">{{ fmtCur(balanceFor(d.name)) }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="dn-act-cell">
                <button class="dn-act-btn" @click="openView(d)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="d.docstatus===0" class="dn-act-btn" @click="openEdit(d)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button v-if="d.docstatus===1 && balanceFor(d.name)>0" class="dn-act-btn dn-act-apply" @click="applyDN(d)" title="Apply to Bill">↳</button>
                <button v-if="d.docstatus===0 || d.docstatus===2" class="dn-act-btn dn-act-del" @click="deleteDN(d)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="9" class="dn-empty">No debit notes match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Create/Edit Drawer ── -->
    <div v-if="drawerOpen" class="dn-overlay" @click.self="drawerOpen=false"></div>
    <div class="dn-drawer" :class="{open:drawerOpen}">
      <div class="dn-dheader">
        <div class="dn-dheader-title">{{ editingName ? 'Edit Debit Note' : 'New Debit Note' }}</div>
        <button class="dn-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="dn-dbody">
        <div class="dn-fields-grid">
          <div class="dn-field" style="grid-column:1/-1">
            <label class="dn-label">Vendor <span class="req">*</span></label>
            <SearchableSelect v-model="form.supplier" :options="vendors" placeholder="Select vendor…"
              :createable="true" createDoctype="Supplier"
              @search="fetchVendors" @select="onVendorSelect" />
          </div>
          <div class="dn-field">
            <label class="dn-label">Date <span class="req">*</span></label>
            <input v-model="form.posting_date" type="date" class="dn-input" />
          </div>
          <div class="dn-field">
            <label class="dn-label">Return Against Bill</label>
            <SearchableSelect v-model="form.return_against" :options="bills"
              placeholder="Select bill (optional)…" @search="fetchBills" @select="onBillSelect" />
          </div>
          <div class="dn-field" style="grid-column:1/-1">
            <label class="dn-label">Reason</label>
            <select v-model="form.reason" class="dn-input">
              <option>Vendor Overcharge</option>
              <option>Goods Returned</option>
              <option>Damaged Goods</option>
              <option>Short Delivery</option>
              <option>Duplicate Invoice</option>
              <option>Other</option>
            </select>
          </div>
        </div>

        <div class="dn-section-title">Items to Debit</div>
        <div class="dn-items-table">
          <div class="dn-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="dn-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items"
              placeholder="Item…" :createable="true" createDoctype="Item"
              @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="dn-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="dn-input ta-r" @input="calcLine(line)" /></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="dn-input ta-r" @input="calcLine(line)" /></div>
            <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
            <div><button @click="removeLine(line.id)" class="dn-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="dn-add-line" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <div class="dn-total-row grand"><span>Total Debit</span><span style="color:#7c2d12">{{ fmtCur(subtotal) }}</span></div>

        <div class="dn-field">
          <label class="dn-label">Notes</label>
          <textarea v-model="form.notes" rows="2" class="dn-input" placeholder="Internal note (optional)…"></textarea>
        </div>
      </div>
      <div class="dn-dfooter">
        <button class="dn-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="dn-btn-save" :disabled="drawerSaving" @click="saveDN(0)"><span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}</button>
        <button class="dn-btn-primary" :disabled="drawerSaving" @click="saveDN(1)"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}</button>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="dn-overlay" @click.self="viewOpen=false"></div>
    <div class="dn-drawer dn-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="dn-view-head" :style="`background:${statusBg(viewDoc)}`">
          <div>
            <div class="dn-view-num">{{ viewDoc.name }}</div>
            <div class="dn-view-sub">{{ viewDoc.supplier_name||viewDoc.supplier }}</div>
          </div>
          <div style="text-align:right">
            <div class="dn-view-amount">{{ fmtCur(Math.abs(viewDoc.grand_total||0)) }}</div>
            <span class="dn-badge dn-badge-white">{{ statusLabel(viewDoc) }}</span>
          </div>
          <button class="dn-dclose dn-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <TimelineStepper :steps="timelineSteps" />

        <div class="dn-tabs">
          <button class="dn-tab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="dn-tab" :class="{active:viewTab==='applied'}" @click="viewTab='applied'">
            Applied To<span v-if="viewApplications.length" class="dn-tab-count">{{ viewApplications.length }}</span>
          </button>
        </div>

        <div class="dn-dbody">
          <template v-if="viewTab==='details'">
            <div class="dn-meta-grid">
              <div><div class="dn-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
              <div><div class="dn-meta-lbl">Return Against</div><div class="mono-sm">{{ viewDoc.return_against||'—' }}</div></div>
              <div><div class="dn-meta-lbl">Total Debit</div><div class="mono-sm" style="color:#7c2d12;font-weight:600">{{ fmtCur(Math.abs(viewDoc.grand_total||0)) }}</div></div>
              <div><div class="dn-meta-lbl">Available Balance</div>
                <div class="mono-sm" :class="viewBalance>0?'text-danger':'text-success'">{{ fmtCur(viewBalance) }}</div>
              </div>
            </div>

            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="dn-section-title">Line Items</div>
              <div class="dn-view-items">
                <div class="dn-view-items-head"><span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span></div>
                <div v-for="it in viewItems" :key="it.name" class="dn-view-items-row">
                  <span>{{ it.item_name||it.item_code }}</span>
                  <span class="ta-r mono-sm">{{ Math.abs(it.qty||0) }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(Math.abs(it.amount||0)) }}</span>
                </div>
              </div>
            </template>
          </template>

          <template v-if="viewTab==='applied'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <div v-else-if="viewApplications.length">
              <div class="dn-app-head"><span>Bill</span><span>Date</span><span>Payment Entry</span><span class="ta-r">Amount Applied</span></div>
              <div v-for="a in viewApplications" :key="a.payment_entry" class="dn-app-row">
                <span class="mono-sm dn-num">{{ a.bill }}</span>
                <span class="mono-sm">{{ fmtDate(a.date) }}</span>
                <span class="mono-sm text-muted">{{ a.payment_entry }}</span>
                <span class="ta-r mono-sm" style="font-weight:600;color:#059669">{{ fmtCur(a.amount) }}</span>
              </div>
            </div>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
              No applications yet.
              <div v-if="viewBalance>0 && viewDoc.docstatus===1" style="margin-top:8px">
                <button class="dn-btn-primary" @click="applyDN(viewDoc)" style="font-size:12px;padding:6px 12px">↳ Apply to Bill</button>
              </div>
            </div>
          </template>
        </div>

        <div class="dn-dfooter">
          <button class="dn-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="dn-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button v-if="viewDoc.docstatus===1" class="dn-btn-ghost" @click="emailDN(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="dn-btn-ghost" @click="printDN(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="viewDoc.docstatus===1 && viewBalance>0" class="dn-btn-primary" @click="applyDN(viewDoc)">↳ Apply to Bill</button>
          <button v-if="viewDoc.docstatus===1" class="dn-btn-danger" @click="cancelDN(viewDoc)">Cancel</button>
          <button v-if="viewDoc.docstatus===0 || viewDoc.docstatus===2" class="dn-btn-danger" @click="deleteDN(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Apply-to-Bill modal ── -->
    <div v-if="applyModal.open" class="dn-overlay" @click.self="applyModal.open=false" style="z-index:60"></div>
    <div v-if="applyModal.open" class="dn-apply-dialog">
      <div class="dn-dheader" style="background:linear-gradient(135deg,#7c2d12,#ea580c);color:#fff;height:auto;padding:14px 18px">
        <div style="color:#fff;font-weight:700">Apply Debit Note — {{ applyModal.dnName }}</div>
        <button class="dn-dclose" style="color:#fff" @click="applyModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="dn-dbody">
        <div style="font-size:12.5px;color:#374151">Available Balance: <strong>{{ fmtCur(applyModal.balance) }}</strong></div>
        <div class="dn-field">
          <label class="dn-label">Target Bill <span class="req">*</span></label>
          <select v-model="applyModal.bill" class="dn-input">
            <option value="">— Select bill —</option>
            <option v-for="b in applyModal.openBills" :key="b.name" :value="b.name">
              {{ b.name }} · {{ fmtCur(b.outstanding_amount) }} due
            </option>
          </select>
        </div>
        <div class="dn-field">
          <label class="dn-label">Amount to Apply <span class="req">*</span></label>
          <input v-model.number="applyModal.amount" type="number" min="0.01" :max="applyModal.balance" step="0.01" class="dn-input ta-r" style="font-family:monospace" />
        </div>
      </div>
      <div class="dn-dfooter">
        <button class="dn-btn-ghost" @click="applyModal.open=false" :disabled="applyModal.saving">Cancel</button>
        <button class="dn-btn-primary" :disabled="applyModal.saving || !applyModal.bill || applyModal.amount<=0" @click="submitApply">
          {{ applyModal.saving ? 'Applying…' : `Apply ${fmtCur(applyModal.amount)}` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiPOST, apiSubmit, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useDocStatus } from "../composables/useDocStatus.js";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { useConfirm } from "../composables/useConfirm.js";
import { useLivePreview } from "../composables/useLivePreview.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import BulkActionBar from "../components/BulkActionBar.vue";
import TimelineStepper from "../components/TimelineStepper.vue";

const { toast } = useToast();
const { confirm } = useConfirm();
const { printDoc } = useLivePreview();
function printDN(d) { printDoc(d, { title: "DEBIT NOTE", partyLabel: "Vendor", partyField: "supplier_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();
const { statusLabel, statusCls, statusBg } = useDocStatus({
  fallbackDraftLabel: "Draft",
  fallbackSubmittedLabel: "Issued",
  paidStatuses: ["return"],
  pendingStatuses: ["return"],
  completedStatuses: ["return"],
  outstandingField: "_unused",
  dueDateField: "_unused",
  overdueCheck: () => false,
});

const activeTab = ref("all");
const tabs = [
  { key: "all",       label: "All" },
  { key: "draft",     label: "Draft" },
  { key: "issued",    label: "Issued" },
  { key: "cancelled", label: "Cancelled" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const viewLoading = ref(false), viewItems = ref([]), viewApplications = ref([]), viewBalance = ref(0);
const vendors = ref([]), items = ref([]), bills = ref([]), lines = ref([]);
const sortCol = ref("posting_date"), sortDir = ref("desc");

// Balance cache by DN name
const _balances = ref({});
function balanceFor(name) { return flt(_balances.value[name] || 0); }

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const form = reactive({ supplier: "", posting_date: todayStr(), return_against: "", reason: "Vendor Overcharge", notes: "" });

// Apply-to-bill modal
const applyModal = reactive({ open: false, saving: false, dnName: "", balance: 0, bill: "", amount: 0, openBills: [] });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function fmtCur(v) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(Math.abs(flt(v))); }

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    list.value = await apiList("Purchase Invoice", {
      fields: ["name", "supplier", "supplier_name", "posting_date", "grand_total", "return_against", "docstatus", "status"],
      filters: [["is_return", "=", 1], ["company", "=", co]],
      limit: 500,
      order: "posting_date desc",
    });
    // Fetch balances for submitted DNs (parallel)
    const submitted = list.value.filter(d => d.docstatus === 1);
    const balances = await Promise.all(submitted.map(d =>
      apiGET("zoho_books_clone.api.docs.get_debit_note_balance", { debit_note_name: d.name }).catch(() => null)
    ));
    const map = {};
    submitted.forEach((d, i) => { if (balances[i]) map[d.name] = balances[i].balance; });
    _balances.value = map;
  } catch (e) { toast.error(e.message || "Failed to load debit notes"); }
  finally { loading.value = false; }
}

const counts = computed(() => ({
  draft:     list.value.filter(d => d.docstatus === 0).length,
  issued:    list.value.filter(d => d.docstatus === 1).length,
  cancelled: list.value.filter(d => d.docstatus === 2).length,
}));
const summary = computed(() => ({
  totalValue:  list.value.filter(d => d.docstatus === 1).reduce((s, d) => s + Math.abs(flt(d.grand_total)), 0),
  openBalance: Object.values(_balances.value).reduce((s, v) => s + flt(v), 0),
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value === "draft")     r = r.filter(d => d.docstatus === 0);
  if (activeTab.value === "issued")    r = r.filter(d => d.docstatus === 1);
  if (activeTab.value === "cancelled") r = r.filter(d => d.docstatus === 2);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.supplier_name || x.supplier || "").toLowerCase().includes(q)
      || (x.return_against || "").toLowerCase().includes(q));
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
function sortBy(col) { if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc"; else { sortCol.value = col; sortDir.value = "asc"; } }
function sortArrow(col) { if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value === "asc" ? "↑" : "↓"; }

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(d => selected.value.has(d.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(d => d.name)) : new Set(); }

const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));

const timelineSteps = computed(() => {
  const d = viewDoc.value;
  if (!d) return [];
  if (d.docstatus === 2) {
    return [
      { key: "draft", label: "Draft", done: true },
      { key: "issued", label: "Issued", done: true },
      { key: "cancelled", label: "Cancelled", danger: true, current: true },
    ];
  }
  const fullyApplied = d.docstatus === 1 && viewBalance.value <= 0;
  return [
    { key: "draft",   label: "Draft",   done: true },
    { key: "issued",  label: "Issued",  done: d.docstatus >= 1, current: d.docstatus === 1 && !fullyApplied },
    { key: "closed",  label: "Closed",  done: fullyApplied, current: fullyApplied },
  ];
});

// ── Create / Edit ─────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { supplier: "", posting_date: todayStr(), return_against: "", reason: "Vendor Overcharge", notes: "" });
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems(""); fetchBills("");
  drawerOpen.value = true;
}
async function openEdit(d) {
  editingName.value = d.name;
  Object.assign(form, { supplier: d.supplier || "", posting_date: d.posting_date || todayStr(), return_against: d.return_against || "", reason: "Vendor Overcharge", notes: "" });
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems(""); fetchBills("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Purchase Invoice", d.name);
    if (doc?.items?.length) {
      // Store positive in form, backend negates on save
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || "",
        qty: Math.abs(i.qty || 0), rate: Math.abs(i.rate || 0),
        amount: Math.abs(i.amount || 0),
      }));
    }
    if (doc?.remarks) form.notes = doc.remarks;
  } catch {}
}
async function openView(d) {
  viewDoc.value = d;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  viewApplications.value = [];
  viewBalance.value = 0;
  try {
    const doc = await apiGet("Purchase Invoice", d.name);
    viewItems.value = doc?.items || [];
    if (d.docstatus === 1) {
      const [bal, apps] = await Promise.all([
        apiGET("zoho_books_clone.api.docs.get_debit_note_balance", { debit_note_name: d.name }).catch(() => null),
        apiGET("zoho_books_clone.api.docs.get_debit_note_applications", { debit_note_name: d.name }).catch(() => []),
      ]);
      if (bal) viewBalance.value = flt(bal.balance);
      viewApplications.value = apps || [];
    }
  } catch {}
  viewLoading.value = false;
}

async function fetchVendors(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["supplier_name", "like", "%" + q + "%"]);
    const r = await apiList("Supplier", { fields: ["name", "supplier_name"], filters: f, limit: 30, order: "supplier_name asc" });
    vendors.value = r.map(x => ({ ...x, label: x.supplier_name || x.name, value: x.name }));
  } catch { vendors.value = []; }
}
async function fetchItems(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["item_name", "like", "%" + q + "%"]);
    const r = await apiList("Item", { fields: ["name", "item_name", "standard_rate", "stock_uom"], filters: f, limit: 30, order: "item_name asc" });
    items.value = r.map(x => ({ ...x, label: x.item_name || x.name, value: x.name, rate: x.standard_rate || 0 }));
  } catch { items.value = []; }
}
async function fetchBills(q = "") {
  try {
    const f = [["is_return", "=", 0], ["docstatus", "=", 1]];
    if (form.supplier) f.push(["supplier", "=", form.supplier]);
    if (q) f.push(["name", "like", "%" + q + "%"]);
    const r = await apiList("Purchase Invoice", { fields: ["name", "supplier", "supplier_name", "outstanding_amount"], filters: f, limit: 30 });
    bills.value = r.map(x => ({ ...x, label: x.name + (x.supplier_name ? ` · ${x.supplier_name}` : ""), value: x.name }));
  } catch { bills.value = []; }
}
function onVendorSelect(opt) {
  // refresh bills filter when vendor changes
  form.return_against = "";
  fetchBills("");
}
async function onBillSelect(opt) {
  const billName = opt?.value ?? opt;
  if (!billName) return;
  // Auto-populate items from the bill
  try {
    const doc = await apiGet("Purchase Invoice", billName);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || i.item_name || "",
        qty: Math.abs(i.qty || 1), rate: Math.abs(i.rate || 0),
        amount: Math.round(Math.abs(i.qty || 1) * Math.abs(i.rate || 0) * 100) / 100,
      }));
      toast.success(`Loaded ${doc.items.length} item(s) from ${billName}`);
    }
    if (!form.supplier && doc?.supplier) form.supplier = doc.supplier;
  } catch {}
}
function onItemSelect(line, opt) { line.item_code = opt?.value ?? opt; if (opt?.rate) { line.rate = Number(opt.rate) || 0; calcLine(line); } }
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }

async function saveDN(submit) {
  if (!form.supplier) return toast.error("Vendor is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  drawerSaving.value = true;
  try {
    // Use the high-level create_debit_note endpoint (negates qty on backend)
    if (!editingName.value) {
      const itemsPayload = lines.value
        .filter(l => l.item_code)
        .map(l => ({ item_code: l.item_code, item_name: l.item_code, description: l.description, qty: flt(l.qty), rate: flt(l.rate) }));
      const r = await apiPOST("zoho_books_clone.api.docs.create_debit_note", {
        vendor: form.supplier,
        against_bill: form.return_against || "",
        date: form.posting_date,
        reason: form.reason,
        notes: form.notes || "",
        items: JSON.stringify(itemsPayload),
      });
      // create_debit_note already submits. If user clicked Save Draft we can't really;
      // it's intentional that DNs are issued immediately. Reflect that in the toast.
      toast.success(`Debit Note ${r?.debit_note || ""} ${submit ? "submitted" : "issued"}`);
    } else {
      // Edit path — direct save
      const company = await resolveCompany();
      const doc = {
        doctype: "Purchase Invoice", name: editingName.value,
        company, supplier: form.supplier,
        posting_date: form.posting_date,
        is_return: 1, return_against: form.return_against || null,
        remarks: (form.reason || "") + (form.notes ? " — " + form.notes : ""),
        items: lines.value.filter(l => l.item_code).map(l => ({
          doctype: "Purchase Invoice Item",
          item_code: l.item_code,
          description: l.description || l.item_code,
          qty: -Math.abs(flt(l.qty)),
          rate: flt(l.rate),
          amount: -Math.abs(flt(l.amount)),
        })),
      };
      const saved = await apiSave(doc);
      if (submit) await apiSubmit("Purchase Invoice", saved.name);
      toast.success(`Debit Note ${saved?.name || ""} ${submit ? "submitted" : "saved"}`);
    }
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save debit note"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailDN(d) {
  // Reuse bill email defaults — supplier-side, same shape
  await openEmail({
    doctype: "Purchase Invoice", name: d.name, docLabel: `Debit Note ${d.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_bill_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_bill_email",
    paramKey: "bill_name",
  });
}
async function applyDN(d) {
  // Load open bills for the same vendor
  try {
    const r = await apiList("Purchase Invoice", {
      fields: ["name", "outstanding_amount", "grand_total"],
      filters: [["is_return", "=", 0], ["docstatus", "=", 1], ["supplier", "=", d.supplier], ["outstanding_amount", ">", 0]],
      limit: 50, order: "posting_date desc",
    });
    if (!r.length) { toast.info("No open bills for this vendor"); return; }
    const balance = balanceFor(d.name) || viewBalance.value || Math.abs(flt(d.grand_total));
    Object.assign(applyModal, {
      open: true, saving: false, dnName: d.name, balance, bill: "",
      amount: Math.min(balance, flt(r[0].outstanding_amount)), openBills: r,
    });
  } catch (e) { toast.error(e.message || "Failed to load bills"); }
}
async function submitApply() {
  if (!applyModal.bill || applyModal.amount <= 0) return;
  applyModal.saving = true;
  try {
    await apiPOST("zoho_books_clone.api.docs.apply_debit_note_to_bill", {
      debit_note: applyModal.dnName,
      bill: applyModal.bill,
      amount: applyModal.amount,
    });
    toast.success(`Applied ${fmtCur(applyModal.amount)} to ${applyModal.bill}`);
    applyModal.open = false;
    await load();
    if (viewDoc.value?.name === applyModal.dnName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Apply failed"); }
  applyModal.saving = false;
}
async function cancelDN(d) {
  if (!await confirm({ title: "Cancel Debit Note", body: `Cancel ${d.name}? Any applications must be cancelled separately.`, okLabel: "Cancel DN" })) return;
  try {
    await apiPOST("zoho_books_clone.api.docs.cancel_doc", { doctype: "Purchase Invoice", name: d.name });
    toast.success("Debit Note cancelled");
    await load(); if (viewDoc.value?.name === d.name) await openView(d);
  } catch (e) { toast.error(e.message || "Cancel failed"); }
}
async function deleteDN(d) {
  if (!await confirm({ title: "Delete Debit Note", body: `Permanently delete ${d.name}? This cannot be undone.`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Purchase Invoice", d.name);
    toast.success("Debit Note deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk ──────────────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(d => selected.value.has(d.name) && d.docstatus === 0);
  if (!drafts.length) { toast.info("No draft debit notes selected"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft debit note(s)?`, okLabel: "Delete" })) return;
  for (const d of drafts) { try { await apiDelete("Purchase Invoice", d.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length} draft(s)`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(d => selected.value.has(d.name) && d.docstatus === 1);
  if (!subs.length) { toast.info("No submitted debit notes selected"); return; }
  let sent = 0;
  for (const d of subs) {
    const ok = await openEmail({
      doctype: "Purchase Invoice", name: d.name, docLabel: `Debit Note ${d.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_bill_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_bill_email",
      paramKey: "bill_name",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} debit note(s)`);
}

function exportCSV() {
  const rows = selected.value.size
    ? sorted.value.filter(d => selected.value.has(d.name))
    : sorted.value;
  if (!rows.length) return;
  const head = ["Debit Note","Vendor","Date","Against Bill","Status","Amount","Available Balance"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const d of rows) {
    out.push([d.name, d.supplier_name || d.supplier, d.posting_date, d.return_against || "",
      statusLabel(d), Math.abs(flt(d.grand_total)).toFixed(2), balanceFor(d.name).toFixed(2)
    ].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `debit_notes_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} note(s)`);
}

onMounted(load);
</script>

<style scoped>
.dn-page { display: flex; flex-direction: column; gap: 16px; padding: 24px; }
.dn-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.dn-search-wrap { display: flex; align-items: center; gap: 8px; background: #ffffff; border-radius: 8px; padding: 6px 12px; min-width: 220px; }
.dn-search-input { border: none; background: transparent; outline: none; font: inherit; color: #111827; width: 100%; font-size: 13px; }
.dn-pills { display: flex; gap: 6px; }
.dn-pill { padding: 6px 14px; border-radius: 20px; font-size: 12.5px; font-weight: 600; border: 1px solid #e5e7eb; background: #fff; color: #6b7280; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 6px; }
.dn-pill:hover { color: #2563eb; border-color: #2563eb; }
.dn-pill.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.dn-pill-count { background: #f3f4f6; color: #6b7280; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.dn-pill.active .dn-pill-count { background: #2563eb; color: #fff; }
.dn-btn-primary { display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.dn-btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.dn-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.dn-btn-ghost { display: inline-flex; align-items: center; gap: 6px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #374151; cursor: pointer; }
.dn-btn-ghost:hover { background: #f9fafb; }
.dn-btn-save { display: inline-flex; align-items: center; gap: 6px; background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.dn-btn-save:hover { background: #dcfce7; }
.dn-btn-save:disabled { opacity: .5; cursor: not-allowed; }
.dn-btn-danger { display: inline-flex; align-items: center; gap: 6px; background: #fef2f2; border: 1px solid #dc2626; color: #dc2626; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.dn-btn-danger:hover { background: #fee2e2; }

.dn-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; }
.dn-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.dn-table th { background: #f9fafb; border-bottom: 1px solid #e5e7eb; padding: 10px 12px; font-size: 11.5px; font-weight: 600; color: #374151; text-align: left; white-space: nowrap; }
.dn-table th.sortable { cursor: pointer; user-select: none; }
.dn-table th.sortable:hover { color: #2563eb; }
.ta-r { text-align: right !important; }
.dn-row td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; cursor: pointer; }
.dn-row:last-child td { border-bottom: none; }
.dn-row:hover td { background: #f9fafb; }
.dn-row.selected td { background: #eff6ff; }
.dn-num { font-family: monospace; font-size: 12.5px; color: #2563eb; font-weight: 600; }
.mono-sm { font-family: monospace; font-size: 12.5px; }
.text-muted { color: #6b7280; }
.text-danger { color: #dc2626; }
.text-success { color: #059669; }
.dn-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 10px; font-size: 11.5px; font-weight: 600; }
.dn-badge.status-paid { background: #d1fae5; color: #059669; }
.dn-badge.status-unpaid { background: #fef3c7; color: #92400e; }
.dn-badge.status-draft { background: #f3f4f6; color: #6b7280; }
.dn-badge.status-cancelled { background: #fee2e2; color: #7f1d1d; }
.dn-badge-white { background: rgba(255,255,255,.2); color: #fff !important; border: 1px solid rgba(255,255,255,.4); }

.dn-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.dn-act-btn { background: transparent; border: 1px solid #e5e7eb; border-radius: 6px; width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #6b7280; font: inherit; font-size: 14px; }
.dn-act-btn:hover { background: #f3f4f6; color: #2563eb; }
.dn-act-apply { background: #fff7ed; border-color: #ea580c; color: #ea580c; }
.dn-act-apply:hover { background: #ffedd5; color: #c2410c; }
.dn-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.dn-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }
.dn-shimmer { height: 13px; background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%); border-radius: 4px; animation: shimmer 1.2s infinite; background-size: 200% 100%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

.dn-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.2); z-index: 40; }
.dn-drawer { position: fixed; top: 0; right: -580px; bottom: 0; width: 580px; max-width: 96vw; background: #fff; border-left: 1px solid #e5e7eb; box-shadow: -8px 0 24px rgba(0,0,0,.08); z-index: 50; display: flex; flex-direction: column; transition: right .22s ease; }
.dn-drawer.open { right: 0; }
.dn-view-drawer { width: 520px; right: -520px; }
.dn-view-drawer.open { right: 0; }
.dn-dheader { display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 60px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; }
.dn-dheader-title { font-size: 15px; font-weight: 600; color: #111827; }
.dn-dclose { background: transparent; border: none; cursor: pointer; color: #6b7280; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; }
.dn-dclose:hover { background: #f3f4f6; color: #111827; }
.dn-dbody { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.dn-fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.dn-field { display: flex; flex-direction: column; gap: 4px; }
.dn-label { font-size: 12px; font-weight: 600; color: #374151; }
.req { color: #dc2626; }
.dn-input { width: 100%; box-sizing: border-box; border: 1px solid #e5e7eb; border-radius: 6px; padding: 7px 10px; font: inherit; font-size: 13px; outline: none; background: #fff; color: #111827; }
.dn-input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.08); }
textarea.dn-input { resize: vertical; }
.dn-section-title { font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: .05em; padding-bottom: 4px; border-bottom: 1px solid #f3f4f6; }
.dn-items-table { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 8px; }
.dn-items-head { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #374151; }
.dn-items-row { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; }
.dn-add-line { background: transparent; border: none; color: #2563eb; font-size: 12.5px; font-weight: 600; cursor: pointer; padding: 8px 12px; display: inline-flex; align-items: center; gap: 6px; }
.dn-add-line:hover { background: #eff6ff; }
.dn-rm-line { background: transparent; border: 1px solid #e5e7eb; border-radius: 4px; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #9ca3af; }
.dn-rm-line:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.dn-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 8px 0; }
.dn-total-row.grand { font-weight: 700; font-size: 15px; color: #111827; border-top: 2px solid #e5e7eb; padding-top: 10px; }

.dn-view-head { position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 20px; flex-shrink: 0; color: #fff; }
.dn-view-num { font-size: 18px; font-weight: 700; font-family: monospace; color: #fff; }
.dn-view-sub { font-size: 13px; color: rgba(255,255,255,.8); margin-top: 2px; }
.dn-view-amount { font-size: 22px; font-weight: 800; font-family: monospace; color: #fff; }
.dn-vclose { position: absolute; top: 12px; right: 12px; color: #fff; }
.dn-vclose:hover { background: rgba(255,255,255,.18); color: #fff; }
.dn-tabs { display: flex; gap: 4px; padding: 0 20px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; background: #fff; }
.dn-tab { background: transparent; border: none; padding: 10px 14px; font: inherit; font-size: 12.5px; font-weight: 600; color: #6b7280; cursor: pointer; border-bottom: 2px solid transparent; display: inline-flex; align-items: center; gap: 6px; }
.dn-tab:hover { color: #2563eb; }
.dn-tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.dn-tab-count { background: #2563eb; color: #fff; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.dn-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.dn-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }
.dn-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.dn-view-items-head { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.dn-view-items-row { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.dn-app-head { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; border-radius: 6px 6px 0 0; border: 1px solid #e5e7eb; border-bottom: none; }
.dn-app-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; align-items: center; font-size: 12.5px; }
.dn-app-row:last-child { border-bottom: 1px solid #e5e7eb; border-radius: 0 0 6px 6px; }
.dn-dfooter { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #e5e7eb; flex-shrink: 0; flex-wrap: wrap; }

.dn-apply-dialog { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 480px; max-width: 96vw; background: #fff; border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.2); z-index: 70; display: flex; flex-direction: column; overflow: hidden; }
</style>
