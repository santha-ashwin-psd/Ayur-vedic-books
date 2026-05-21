<template>
  <div class="bill-page">

    <!-- ── Toolbar ── -->
    <div class="bill-actions">
      <div class="bill-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search bills, vendors, bill #…" class="bill-search-input" />
      </div>
      <div class="bill-pills">
        <button v-for="t in tabs" :key="t.key"
          class="bill-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">
          {{ t.label }}
          <span v-if="t.key!=='all'" class="bill-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="bill-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="bill-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="bill-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Bill
        </button>
      </div>
    </div>

    <!-- ── Summary strip ── -->
    <SummaryStrip :cards="[
      { label: 'Total Bills', value: list.length },
      { label: 'Unpaid',  value: fmtCur(summary.totalUnpaid), accent: '#d97706' },
      { label: 'Overdue', value: summary.overdueCount,        accent: '#dc2626' },
      { label: 'Total Payable', value: fmtCur(summary.totalDue), accent: '#059669' },
    ]" />

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button @click="bulkCancel">Cancel Submitted</button>
      <button class="bab-danger" @click="bulkDelete">Delete Drafts</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="bill-card">
      <table class="bill-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">Bill # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('supplier_name')" class="sortable">Vendor <span v-html="sortArrow('supplier_name')"></span></th>
            <th @click="sortBy('bill_no')" class="sortable">Vendor Bill # <span v-html="sortArrow('bill_no')"></span></th>
            <th @click="sortBy('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
            <th @click="sortBy('due_date')" class="sortable">Due Date <span v-html="sortArrow('due_date')"></span></th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th @click="sortBy('outstanding_amount')" class="sortable ta-r">Balance <span v-html="sortArrow('outstanding_amount')"></span></th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 7" :key="n"><td colspan="10"><div class="bill-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="b in sorted" :key="b.name" class="bill-row" :class="{selected:selected.has(b.name)}">
              <td><input type="checkbox" :checked="selected.has(b.name)" @change="toggle(b.name)" /></td>
              <td @click="openView(b)"><span class="bill-num">{{ b.name }}</span></td>
              <td @click="openView(b)">{{ b.supplier_name || b.supplier || '—' }}</td>
              <td @click="openView(b)" class="text-muted mono-sm">{{ b.bill_no||'—' }}</td>
              <td @click="openView(b)" class="text-muted mono-sm">{{ fmtDate(b.posting_date) }}</td>
              <td @click="openView(b)" :class="isOverdue(b)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(b.due_date)||'—' }}</td>
              <td @click="openView(b)"><span class="bill-badge" :class="statusCls(b)">{{ statusLabel(b) }}</span></td>
              <td @click="openView(b)" class="ta-r mono-sm">{{ fmtCur(b.grand_total) }}</td>
              <td @click="openView(b)" class="ta-r mono-sm" :class="{'text-danger':flt(b.outstanding_amount)>0,'text-success':flt(b.outstanding_amount)<=0&&b.docstatus===1}">{{ fmtCur(b.outstanding_amount) }}</td>
              <td class="bill-act-cell">
                <button class="bill-act-btn" @click="openView(b)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="b.docstatus===0" class="bill-act-btn" @click="openEdit(b)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button v-if="b.docstatus===1 && flt(b.outstanding_amount)>0" class="bill-act-btn bill-act-pay" @click="payBill(b)" title="Record Payment">₹</button>
                <button v-if="b.docstatus===0 || b.docstatus===2" class="bill-act-btn bill-act-del" @click="deleteBill(b)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="10" class="bill-empty">No bills match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Create / Edit drawer ── -->
    <div v-if="drawerOpen" class="bill-overlay" @click.self="drawerOpen=false"></div>
    <div class="bill-drawer" :class="{open:drawerOpen}">
      <div class="bill-dheader">
        <div class="bill-dheader-title">{{ editingName ? 'Edit Bill' : 'New Bill' }}</div>
        <button class="bill-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="bill-dbody">
        <div class="bill-fields-grid">
          <div class="bill-field" style="grid-column:1/-1">
            <label class="bill-label">Vendor <span class="req">*</span></label>
            <SearchableSelect v-model="form.supplier" :options="vendors"
              placeholder="Select vendor…" :createable="true" createDoctype="Supplier"
              @search="fetchVendors" @select="onVendorSelect" />
          </div>
          <div class="bill-field">
            <label class="bill-label">Bill Date <span class="req">*</span></label>
            <input v-model="form.posting_date" type="date" class="bill-input" />
          </div>
          <div class="bill-field">
            <label class="bill-label">Due Date</label>
            <input v-model="form.due_date" type="date" class="bill-input" />
          </div>
          <div class="bill-field">
            <label class="bill-label">Vendor Bill #</label>
            <input v-model="form.bill_no" type="text" class="bill-input" placeholder="Vendor's invoice number" />
          </div>
          <div class="bill-field">
            <label class="bill-label">Vendor Bill Date</label>
            <input v-model="form.bill_date" type="date" class="bill-input" />
          </div>
          <div class="bill-field">
            <label class="bill-label">Currency</label>
            <select v-model="form.currency" class="bill-input" @change="form.exchange_rate=form.currency==='INR'?1:form.exchange_rate">
              <option v-for="(sym,code) in BILL_CURRENCIES" :key="code" :value="code">{{ code }} {{ sym }}</option>
            </select>
          </div>
          <div v-if="form.currency !== 'INR'" class="bill-field">
            <label class="bill-label">Exchange Rate</label>
            <input v-model.number="form.exchange_rate" type="number" min="0.0001" step="0.0001" class="bill-input"/>
          </div>
        </div>

        <div class="bill-section-row">
          <div class="bill-section-title">Items</div>
          <button v-if="form.supplier" class="bill-copy-btn" @click="copyLastItems" :disabled="copyingLast">
            <span v-html="icon('copy',12)"></span> {{ copyingLast ? 'Loading…' : 'Copy Last' }}
          </button>
        </div>
        <div class="bill-items-table">
          <div class="bill-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="bill-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items"
              placeholder="Select item…" :createable="true" createDoctype="Item"
              @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="bill-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="bill-input ta-r" @input="calcLine(line)" /></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="bill-input ta-r" @input="calcLine(line)" /></div>
            <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
            <div><button @click="removeLine(line.id)" class="bill-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="bill-add-line" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <div class="bill-totals">
          <div class="bill-field" style="max-width:160px">
            <label class="bill-label">Tax Rate %</label>
            <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="bill-input" />
          </div>
          <div class="bill-totals-right">
            <div class="bill-total-row"><span>Subtotal</span><span>{{ fmtCur(subtotal) }}</span></div>
            <div class="bill-total-row"><span>Tax ({{ form.tax_rate||0 }}%)</span><span>{{ fmtCur(taxAmount) }}</span></div>
            <div class="bill-total-row grand"><span>Total</span><span>{{ fmtCur(subtotal+taxAmount) }}</span></div>
          </div>
        </div>

        <div class="bill-field">
          <label class="bill-label">Remarks</label>
          <textarea v-model="form.remarks" rows="2" class="bill-input" placeholder="Optional…"></textarea>
        </div>
      </div>
      <div class="bill-dfooter">
        <button class="bill-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="bill-btn-save" :disabled="drawerSaving" @click="saveBill(0)">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="bill-btn-primary" :disabled="drawerSaving" @click="saveBill(1)">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}
        </button>
      </div>
    </div>

    <!-- ── View drawer ── -->
    <div v-if="viewOpen" class="bill-overlay" @click.self="viewOpen=false"></div>
    <div class="bill-drawer bill-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="bill-view-head" :style="`background:${statusBg(viewDoc)}`">
          <div>
            <div class="bill-view-num">{{ viewDoc.name }}</div>
            <div class="bill-view-sub">{{ viewDoc.supplier_name||viewDoc.supplier }}</div>
          </div>
          <div style="text-align:right">
            <div class="bill-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="bill-badge bill-badge-white">{{ statusLabel(viewDoc) }}</span>
          </div>
          <button class="bill-dclose bill-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <TimelineStepper :steps="timelineSteps" />

        <div class="bill-tabs">
          <button class="bill-tab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="bill-tab" :class="{active:viewTab==='payments'}" @click="viewTab='payments'">
            Payments<span v-if="viewPayments.length" class="bill-tab-count">{{ viewPayments.length }}</span>
          </button>
        </div>

        <div class="bill-dbody">
          <template v-if="viewTab==='details'">
            <div class="bill-meta-grid">
              <div><div class="bill-meta-lbl">Bill Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
              <div><div class="bill-meta-lbl">Due Date</div>
                <div class="mono-sm" :class="isOverdue(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.due_date)||'—' }}</div>
              </div>
              <div><div class="bill-meta-lbl">Vendor Bill #</div><div class="mono-sm">{{ viewDoc.bill_no||'—' }}</div></div>
              <div><div class="bill-meta-lbl">Outstanding</div><div class="mono-sm" :class="flt(viewDoc.outstanding_amount)>0?'text-danger':'text-success'">{{ fmtCur(viewDoc.outstanding_amount) }}</div></div>
            </div>

            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading details…</div>
            <template v-else>
              <div v-if="viewItems.length" class="bill-section-title">Line Items</div>
              <div v-if="viewItems.length" class="bill-view-items">
                <div class="bill-view-items-head">
                  <span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span>
                </div>
                <div v-for="it in viewItems" :key="it.name" class="bill-view-items-row">
                  <span><strong>{{ it.item_name||it.item_code }}</strong>
                    <div v-if="it.description" class="text-muted" style="font-size:11px">{{ it.description }}</div></span>
                  <span class="ta-r mono-sm">{{ it.qty }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(it.amount) }}</span>
                </div>
              </div>
            </template>
          </template>

          <template v-if="viewTab==='payments'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading payments…</div>
            <div v-else-if="viewPayments.length">
              <div class="bill-pay-head">
                <span>Date</span><span>Mode</span><span>Reference</span><span class="ta-r">Amount</span>
              </div>
              <div v-for="p in viewPayments" :key="p.name" class="bill-pay-row">
                <span class="mono-sm">{{ fmtDate(p.payment_date) }}</span>
                <span>{{ p.mode_of_payment || '—' }}</span>
                <span class="mono-sm text-muted">{{ p.reference_no || '—' }}</span>
                <span class="ta-r mono-sm" style="font-weight:600;color:#059669">{{ fmtCur(p.paid_amount) }}</span>
              </div>
            </div>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
              No payments recorded yet.
              <div v-if="flt(viewDoc.outstanding_amount)>0 && viewDoc.docstatus===1" style="margin-top:8px">
                <button class="bill-btn-primary" @click="payBill(viewDoc)" style="font-size:12px;padding:6px 12px">₹ Record Payment</button>
              </div>
            </div>
          </template>
        </div>

        <div class="bill-dfooter">
          <button class="bill-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="bill-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button v-if="viewDoc.docstatus===1" class="bill-btn-ghost" @click="emailBill(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button v-if="viewDoc.docstatus===1 && flt(viewDoc.outstanding_amount)>0" class="bill-btn-primary" @click="payBill(viewDoc)">
            ₹ Record Payment
          </button>
          <button v-if="viewDoc.docstatus===1" class="bill-btn-warn" @click="issueDebitNote(viewDoc)">
            <span v-html="icon('arrow-left',13)"></span> Issue Debit Note
          </button>
          <button v-if="viewDoc.docstatus===1" class="bill-btn-danger" @click="cancelBill(viewDoc)">
            Cancel
          </button>
          <button v-if="viewDoc.docstatus===0 || viewDoc.docstatus===2" class="bill-btn-danger" @click="deleteBill(viewDoc)">
            Delete
          </button>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiSubmit, apiDelete, apiPOST, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useDocStatus } from "../composables/useDocStatus.js";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { usePaymentDialog } from "../composables/usePaymentDialog.js";
import { useConfirmCascade } from "../composables/useConfirmCascade.js";
import { useReturnNote } from "../composables/useReturnNote.js";
import { useConfirm } from "../composables/useConfirm.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import BulkActionBar from "../components/BulkActionBar.vue";
import TimelineStepper from "../components/TimelineStepper.vue";

const { toast } = useToast();
const { confirm } = useConfirm();
const { openEmail } = useEmailDialog();
const { openPayment } = usePaymentDialog();
const { confirmCascade } = useConfirmCascade();
const { openReturnNote } = useReturnNote();

// Status helpers tuned for Purchase Invoice
const { statusLabel, statusCls, statusBg, isOverdue } = useDocStatus({
  dueDateField: "due_date",
  outstandingField: "outstanding_amount",
  fallbackDraftLabel: "Draft",
  fallbackSubmittedLabel: "Unpaid",
});

const activeTab = ref("all");
const tabs = [
  { key: "all",     label: "All" },
  { key: "draft",   label: "Draft" },
  { key: "unpaid",  label: "Unpaid" },
  { key: "overdue", label: "Overdue" },
  { key: "paid",    label: "Paid" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const viewLoading = ref(false), viewItems = ref([]), viewPayments = ref([]);
const vendors = ref([]), items = ref([]), lines = ref([]), taxAccountHead = ref("");
const sortCol = ref("posting_date"), sortDir = ref("desc");
const copyingLast = ref(false);

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const BILL_CURRENCIES = { INR:"₹", USD:"$", EUR:"€", GBP:"£", AED:"د.إ", SGD:"S$", JPY:"¥", AUD:"A$", CAD:"C$", CHF:"₣" };
const form = reactive({ supplier: "", posting_date: todayStr(), due_date: "", bill_no: "", bill_date: "", tax_rate: 0, remarks: "", currency: "INR", exchange_rate: 1 });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function fmtCur(v) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(Math.abs(flt(v)));
}

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Purchase Invoice", {
      fields: ["name", "supplier", "supplier_name", "posting_date", "due_date", "bill_no", "grand_total", "outstanding_amount", "docstatus", "status"],
      filters: [["is_return", "=", 0]],
      limit: 500,
      order: "posting_date desc",
    });
  } catch (e) { toast.error(e.message || "Failed to load bills"); }
  finally { loading.value = false; }
}
async function loadTaxAccount() {
  try {
    const r = await apiList("Account", { fields: ["name"], filters: [["account_type", "=", "Tax"], ["is_group", "=", 0]], limit: 1 });
    if (r?.length) taxAccountHead.value = r[0].name;
  } catch {}
}

const counts = computed(() => ({
  draft:   list.value.filter(b => b.docstatus === 0).length,
  unpaid:  list.value.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) > 0 && !isOverdue(b)).length,
  overdue: list.value.filter(b => isOverdue(b)).length,
  paid:    list.value.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) <= 0).length,
}));
const summary = computed(() => ({
  totalUnpaid:   list.value.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) > 0 && !isOverdue(b)).reduce((s, b) => s + flt(b.outstanding_amount), 0),
  overdueCount:  counts.value.overdue,
  totalDue:      list.value.filter(b => b.docstatus === 1).reduce((s, b) => s + flt(b.outstanding_amount), 0),
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value === "draft")   r = r.filter(b => b.docstatus === 0);
  if (activeTab.value === "unpaid")  r = r.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) > 0 && !isOverdue(b));
  if (activeTab.value === "overdue") r = r.filter(b => isOverdue(b));
  if (activeTab.value === "paid")    r = r.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) <= 0);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.supplier_name || x.supplier || "").toLowerCase().includes(q)
      || (x.bill_no || "").toLowerCase().includes(q));
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
function sortBy(col) {
  if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  else { sortCol.value = col; sortDir.value = "asc"; }
}
function sortArrow(col) {
  if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>';
  return sortDir.value === "asc" ? "↑" : "↓";
}

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(b => selected.value.has(b.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(b => b.name)) : new Set(); }

// ── Timeline ──────────────────────────────────────────────────────────────
const timelineSteps = computed(() => {
  const b = viewDoc.value;
  if (!b) return [];
  if (b.docstatus === 2) {
    return [
      { key: "draft", label: "Draft", done: true },
      { key: "submitted", label: "Submitted", done: true },
      { key: "cancelled", label: "Cancelled", danger: true, current: true },
    ];
  }
  const paid = b.docstatus === 1 && flt(b.outstanding_amount) <= 0;
  const overdue = isOverdue(b);
  return [
    { key: "draft",     label: "Draft", done: true },
    { key: "submitted", label: "Submitted", done: b.docstatus >= 1, current: b.docstatus === 1 && !paid },
    { key: "paid",      label: overdue ? "Overdue" : "Paid", done: paid, danger: overdue && !paid, current: paid },
  ];
});

// ── Create/Edit ───────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { supplier: "", posting_date: todayStr(), due_date: "", bill_no: "", bill_date: "", tax_rate: 0, remarks: "", currency: "INR", exchange_rate: 1 });
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems("");
  drawerOpen.value = true;
}
async function openEdit(b) {
  editingName.value = b.name;
  Object.assign(form, { supplier: b.supplier || "", posting_date: b.posting_date || todayStr(), due_date: b.due_date || "", bill_no: b.bill_no || "", bill_date: b.bill_date || "", tax_rate: 0, remarks: b.remarks || "", currency: "INR", exchange_rate: 1 });
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Purchase Invoice", b.name);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || "",
        qty: i.qty || 1, rate: i.rate || 0, amount: i.amount || 0,
      }));
    }
    if (doc?.currency) form.currency = doc.currency;
    if (doc?.conversion_rate) form.exchange_rate = doc.conversion_rate;
    if (doc?.taxes?.[0]?.rate) form.tax_rate = doc.taxes[0].rate;
    if (doc?.taxes?.[0]?.account_head) taxAccountHead.value = doc.taxes[0].account_head;
  } catch {}
}
async function openView(b) {
  viewDoc.value = b;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  viewPayments.value = [];
  try {
    const [doc, payments] = await Promise.all([
      apiGet("Purchase Invoice", b.name),
      b.docstatus === 1 ? apiGET("zoho_books_clone.api.docs.get_bill_payments", { bill_name: b.name }) : Promise.resolve([]),
    ]);
    viewItems.value = doc?.items || [];
    viewPayments.value = (payments || []).filter(p => p.docstatus === 1);
  } catch (e) { /* keep dialog open */ }
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
function onVendorSelect(_opt) { /* could auto-fill terms in future */ }
function onItemSelect(line, opt) {
  line.item_code = opt?.value ?? opt;
  if (opt?.rate) { line.rate = Number(opt.rate) || 0; calcLine(line); }
}
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }
const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const taxAmount = computed(() => Math.round(subtotal.value * flt(form.tax_rate) / 100 * 100) / 100);

async function copyLastItems() {
  if (!form.supplier) return;
  copyingLast.value = true;
  try {
    const r = await apiGET("zoho_books_clone.api.docs.get_party_last_items", { party_type: "Supplier", party: form.supplier, limit: 20 });
    if (r?.items?.length) {
      lines.value = r.items.map(it => ({
        id: _id++, item_code: it.item_code || "", description: it.description || it.item_name || "",
        qty: flt(it.qty) || 1, rate: flt(it.rate) || 0,
        amount: Math.round(flt(it.qty || 1) * flt(it.rate || 0) * 100) / 100,
      }));
      toast.success(`Copied ${r.items.length} item(s) from ${r.source || "last bill"}`);
    } else { toast.info("No previous items found for this vendor"); }
  } catch (e) { toast.error("Failed to copy items"); }
  copyingLast.value = false;
}

async function saveBill(submit) {
  if (!form.supplier) return toast.error("Vendor is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const taxes = form.tax_rate > 0 && taxAccountHead.value
      ? [{ doctype: "Tax Line", charge_type: "On Net Total", account_head: taxAccountHead.value, description: taxAccountHead.value, rate: form.tax_rate }]
      : [];
    const doc = {
      doctype: "Purchase Invoice", company,
      supplier: form.supplier, posting_date: form.posting_date,
      due_date: form.due_date || null, bill_no: form.bill_no || "",
      bill_date: form.bill_date || null, remarks: form.remarks || "",
      currency: form.currency || "INR",
      conversion_rate: form.currency === "INR" ? 1 : (form.exchange_rate || 1),
      items: lines.value.filter(l => l.item_code).map(l => ({
        doctype: "Purchase Invoice Item", item_code: l.item_code,
        description: l.description || l.item_code,
        qty: flt(l.qty) || 1, rate: flt(l.rate), amount: flt(l.amount),
      })),
      taxes,
    };
    if (editingName.value) doc.name = editingName.value;
    const saved = await apiSave(doc);
    if (submit && saved?.name) await apiSubmit("Purchase Invoice", saved.name);
    toast.success(`Bill ${saved?.name || ""} ${submit ? "submitted" : "saved"}`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save bill"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailBill(b) {
  await openEmail({
    doctype: "Purchase Invoice", name: b.name,
    docLabel: `Bill ${b.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_bill_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_bill_email",
    paramKey: "bill_name",
  });
}
async function payBill(b) {
  const paid = await openPayment({
    direction: "pay", doctype: "Purchase Invoice", name: b.name,
    party: b.supplier, partyLabel: b.supplier_name || b.supplier,
    balance: flt(b.outstanding_amount),
    sendEndpoint: "zoho_books_clone.api.docs.record_vendor_payment",
    paramKey: "bill_name",
  });
  if (paid) { await load(); if (viewDoc.value?.name === b.name) await openView(b); }
}
async function issueDebitNote(b) {
  // Pre-fill items from the bill
  let billItems = viewItems.value;
  if (!billItems.length) {
    try { const doc = await apiGet("Purchase Invoice", b.name); billItems = doc?.items || []; }
    catch { billItems = []; }
  }
  const result = await openReturnNote({
    kind: "debit", parentName: b.name, party: b.supplier,
    items: billItems.map(i => ({ item_code: i.item_code, item_name: i.item_name, description: i.description, qty: i.qty, rate: i.rate })),
    existingEndpoint: "zoho_books_clone.api.docs.get_debit_notes",
    createEndpoint: "zoho_books_clone.api.docs.create_debit_note",
    paramKey: "bill_name",
    partyKey: "vendor",
    parentKey: "against_bill",
  });
  if (result) { await load(); if (viewDoc.value?.name === b.name) await openView(b); }
}

async function cancelBill(b) {
  let payments = [];
  try { payments = await apiGET("zoho_books_clone.api.docs.get_bill_payments", { bill_name: b.name }) || []; } catch {}
  const submittedPays = payments.filter(p => p.docstatus === 1);
  if (submittedPays.length) {
    const ok = await confirmCascade({
      title: "Cancel Bill & Payments",
      message: `${b.name} has ${submittedPays.length} linked payment(s). Both must be cancelled together.`,
      actionLabel: "Cancel Both",
      links: submittedPays.map(p => ({ name: p.name, mode: p.mode_of_payment, date: p.payment_date, amount: p.paid_amount })),
    });
    if (!ok) return;
    try {
      await apiPOST("zoho_books_clone.api.docs.cancel_bill_with_payments", { bill_name: b.name });
      toast.success("Bill and payment(s) cancelled");
      await load(); if (viewDoc.value?.name === b.name) await openView(b);
    } catch (e) { toast.error(e.message || "Cancel failed"); }
  } else {
    if (!await confirm({ title: "Cancel Bill", body: `Cancel ${b.name}? This cannot be undone.`, okLabel: "Cancel Bill" })) return;
    try {
      await apiPOST("zoho_books_clone.api.docs.cancel_doc", { doctype: "Purchase Invoice", name: b.name });
      toast.success("Bill cancelled");
      await load(); if (viewDoc.value?.name === b.name) await openView(b);
    } catch (e) { toast.error(e.message || "Cancel failed"); }
  }
}
async function deleteBill(b) {
  if (!await confirm({ title: "Delete Bill", body: `Permanently delete ${b.name}? This cannot be undone.`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Purchase Invoice", b.name);
    toast.success("Bill deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk actions ──────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(b => selected.value.has(b.name) && b.docstatus === 0);
  if (!drafts.length) { toast.info("No draft bills selected"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft bill(s)?`, okLabel: "Delete" })) return;
  for (const b of drafts) { try { await apiDelete("Purchase Invoice", b.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length} draft bill(s)`);
  await load();
}
async function bulkCancel() {
  const submitted = sorted.value.filter(b => selected.value.has(b.name) && b.docstatus === 1);
  if (!submitted.length) { toast.info("No submitted bills selected"); return; }
  let done = 0, failed = 0;
  for (const b of submitted) {
    try { await apiPOST("zoho_books_clone.api.docs.cancel_bill_with_payments", { bill_name: b.name }); done++; }
    catch (e) { failed++; }
  }
  selected.value = new Set();
  toast.success(`Cancelled ${done} bill(s)${failed ? `; ${failed} failed` : ""}`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(b => selected.value.has(b.name) && b.docstatus === 1);
  if (!subs.length) { toast.info("No submitted bills selected"); return; }
  let sent = 0;
  for (const b of subs) {
    const ok = await openEmail({
      doctype: "Purchase Invoice", name: b.name, docLabel: `Bill ${b.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_bill_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_bill_email",
      paramKey: "bill_name",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} bill(s)`);
}

function exportCSV() {
  const rows = sorted.value;
  const head = ["Bill #","Vendor","Vendor Bill #","Date","Due Date","Status","Amount","Balance"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lines = [head.map(esc).join(",")];
  for (const b of rows) {
    lines.push([b.name, b.supplier_name || b.supplier, b.bill_no || "", b.posting_date || "", b.due_date || "",
      statusLabel(b), Number(b.grand_total || 0).toFixed(2), Number(b.outstanding_amount || 0).toFixed(2)
    ].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `bills_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} bill(s)`);
}

onMounted(() => { load(); loadTaxAccount(); });
</script>

<style scoped>
.bill-page { display: flex; flex-direction: column; gap: 16px; padding: 24px; }
.bill-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.bill-search-wrap { display: flex; align-items: center; gap: 8px; background: #f3f4f6; border-radius: 8px; padding: 6px 12px; min-width: 220px; }
.bill-search-input { border: none; background: transparent; outline: none; font: inherit; color: #111827; width: 100%; font-size: 13px; }
.bill-pills { display: flex; gap: 6px; }
.bill-pill { padding: 6px 14px; border-radius: 20px; font-size: 12.5px; font-weight: 600; border: 1px solid #e5e7eb; background: #fff; color: #6b7280; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 6px; }
.bill-pill:hover { color: #2563eb; border-color: #2563eb; }
.bill-pill.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.bill-pill-count { background: #f3f4f6; color: #6b7280; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.bill-pill.active .bill-pill-count { background: #2563eb; color: #fff; }
.bill-btn-primary { display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.bill-btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.bill-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.bill-btn-ghost { display: inline-flex; align-items: center; gap: 6px; background: transparent; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #374151; cursor: pointer; }
.bill-btn-ghost:hover { background: #f9fafb; }
.bill-btn-save { display: inline-flex; align-items: center; gap: 6px; background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.bill-btn-save:hover { background: #dcfce7; }
.bill-btn-save:disabled { opacity: .5; cursor: not-allowed; }
.bill-btn-warn { display: inline-flex; align-items: center; gap: 6px; background: #fff7ed; border: 1px solid #ea580c; color: #ea580c; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.bill-btn-warn:hover { background: #ffedd5; }
.bill-btn-danger { display: inline-flex; align-items: center; gap: 6px; background: #fef2f2; border: 1px solid #dc2626; color: #dc2626; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.bill-btn-danger:hover { background: #fee2e2; }

.bill-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; }
.bill-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.bill-table th { background: #f9fafb; border-bottom: 1px solid #e5e7eb; padding: 10px 12px; font-size: 11.5px; font-weight: 600; color: #374151; text-align: left; white-space: nowrap; }
.bill-table th.sortable { cursor: pointer; user-select: none; }
.bill-table th.sortable:hover { color: #2563eb; }
.ta-r { text-align: right !important; }
.bill-row td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; cursor: pointer; }
.bill-row:last-child td { border-bottom: none; }
.bill-row:hover td { background: #f9fafb; }
.bill-row.selected td { background: #eff6ff; }
.bill-num { font-family: monospace; font-size: 12.5px; color: #2563eb; font-weight: 600; }
.mono-sm { font-family: monospace; font-size: 12.5px; }
.text-muted { color: #6b7280; }
.text-danger { color: #dc2626; }
.text-success { color: #059669; }
.bill-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 10px; font-size: 11.5px; font-weight: 600; }
.bill-badge.status-paid { background: #d1fae5; color: #059669; }
.bill-badge.status-unpaid { background: #fef3c7; color: #92400e; }
.bill-badge.status-overdue { background: transparent; color: #dc2626; font-weight: 700; }
.bill-badge.status-cancelled { background: #fee2e2; color: #7f1d1d; }
.bill-badge.status-draft { background: #f3f4f6; color: #6b7280; }
.bill-badge-white { background: rgba(255,255,255,.2); color: #fff !important; border: 1px solid rgba(255,255,255,.4); }

.bill-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.bill-act-btn { background: transparent; border: 1px solid #e5e7eb; border-radius: 6px; width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #6b7280; font: inherit; font-size: 13px; font-weight: 600; }
.bill-act-btn:hover { background: #f3f4f6; color: #2563eb; }
.bill-act-pay { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.bill-act-pay:hover { background: #dbeafe; }
.bill-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.bill-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }
.bill-shimmer { height: 13px; background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%); border-radius: 4px; animation: shimmer 1.2s infinite; background-size: 200% 100%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

.bill-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.2); z-index: 40; }
.bill-drawer { position: fixed; top: 0; right: -600px; bottom: 0; width: 600px; max-width: 96vw; background: #fff; border-left: 1px solid #e5e7eb; box-shadow: -8px 0 24px rgba(0,0,0,.08); z-index: 50; display: flex; flex-direction: column; transition: right .22s ease; }
.bill-drawer.open { right: 0; }
.bill-view-drawer { width: 540px; right: -540px; }
.bill-view-drawer.open { right: 0; }
.bill-dheader { display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 60px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; }
.bill-dheader-title { font-size: 15px; font-weight: 600; color: #111827; }
.bill-dclose { background: transparent; border: none; cursor: pointer; color: #6b7280; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; }
.bill-dclose:hover { background: #f3f4f6; color: #111827; }
.bill-dbody { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.bill-fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.bill-field { display: flex; flex-direction: column; gap: 4px; }
.bill-label { font-size: 12px; font-weight: 600; color: #374151; }
.req { color: #dc2626; }
.bill-input { width: 100%; box-sizing: border-box; border: 1px solid #e5e7eb; border-radius: 6px; padding: 7px 10px; font: inherit; font-size: 13px; outline: none; background: #fff; color: #111827; }
.bill-input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.08); }
textarea.bill-input { resize: vertical; }
.bill-section-row { display: flex; align-items: center; justify-content: space-between; }
.bill-section-title { font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: .05em; padding-bottom: 4px; border-bottom: 1px solid #f3f4f6; flex: 1; }
.bill-copy-btn { background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; padding: 4px 10px; border-radius: 6px; font: inherit; font-size: 11.5px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; margin-left: 8px; }
.bill-copy-btn:hover { background: #dcfce7; }
.bill-copy-btn:disabled { opacity: .5; cursor: not-allowed; }
.bill-items-table { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.bill-items-head { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #374151; }
.bill-items-row { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; }
.bill-add-line { background: transparent; border: none; color: #2563eb; font-size: 12.5px; font-weight: 600; cursor: pointer; padding: 8px 12px; display: inline-flex; align-items: center; gap: 6px; }
.bill-add-line:hover { background: #eff6ff; }
.bill-rm-line { background: transparent; border: 1px solid #e5e7eb; border-radius: 4px; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #9ca3af; }
.bill-rm-line:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.bill-totals { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.bill-totals-right { display: flex; flex-direction: column; gap: 4px; min-width: 220px; }
.bill-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 3px 0; }
.bill-total-row.grand { font-weight: 700; font-size: 14px; color: #111827; border-top: 1px solid #e5e7eb; padding-top: 6px; margin-top: 2px; }

.bill-view-head { position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 20px; flex-shrink: 0; color: #fff; }
.bill-view-num { font-size: 18px; font-weight: 700; font-family: monospace; color: #fff; }
.bill-view-sub { font-size: 13px; color: rgba(255,255,255,.8); margin-top: 2px; }
.bill-view-amount { font-size: 22px; font-weight: 800; font-family: monospace; color: #fff; }
.bill-vclose { position: absolute; top: 12px; right: 12px; color: #fff; }
.bill-vclose:hover { background: rgba(255,255,255,.18); color: #fff; }

.bill-tabs { display: flex; gap: 4px; padding: 0 20px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; background: #fff; }
.bill-tab { background: transparent; border: none; padding: 10px 14px; font: inherit; font-size: 12.5px; font-weight: 600; color: #6b7280; cursor: pointer; border-bottom: 2px solid transparent; display: inline-flex; align-items: center; gap: 6px; }
.bill-tab:hover { color: #2563eb; }
.bill-tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.bill-tab-count { background: #2563eb; color: #fff; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }

.bill-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.bill-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }

.bill-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.bill-view-items-head { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.bill-view-items-row { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }

.bill-pay-head { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; border-radius: 6px 6px 0 0; border: 1px solid #e5e7eb; border-bottom: none; }
.bill-pay-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; align-items: center; font-size: 12.5px; }
.bill-pay-row:last-child { border-bottom: 1px solid #e5e7eb; border-radius: 0 0 6px 6px; }

.bill-dfooter { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #e5e7eb; flex-shrink: 0; flex-wrap: wrap; }
</style>
