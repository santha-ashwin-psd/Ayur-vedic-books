<template>
  <div class="po-page">

    <!-- ── Toolbar ── -->
    <div class="po-actions">
      <div class="po-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search POs, vendors…" class="po-search-input" />
      </div>
      <div class="po-pills">
        <button v-for="t in tabs" :key="t.key"
          class="po-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">
          {{ t.label }}
          <span v-if="t.key!=='all'" class="po-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div style="    display: flex;
    align-items: center;
    gap: 8px;
    flex-shrink: 0;
    flex-wrap: nowrap;">
        <button class="po-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="po-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="po-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Purchase Order
        </button>
      </div>
    </div>

    <!-- ── Summary strip ── -->
    <SummaryStrip v-if="!loading" :cards="[
      { label: 'Total POs',          tone: 'accent',                                    value: list.length },
      { label: 'To Receive',         tone: counts.toReceive>0 ? 'warn' : 'default',     value: counts.toReceive,          valueClass: counts.toReceive>0 ? 'orange' : '' },
      { label: 'To Bill',            tone: counts.toBill>0 ? 'info' : 'default',        value: counts.toBill,             valueClass: counts.toBill>0 ? 'blue' : '' },
      { label: 'Procurement Value',  tone: 'success',                                   value: fmtCur(summary.totalValue), valueClass: 'green' },
    ]" />

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button class="bab-danger" @click="bulkDelete">Delete</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="po-card">
      <table class="po-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">PO # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('supplier_name')" class="sortable">Vendor <span v-html="sortArrow('supplier_name')"></span></th>
            <th @click="sortBy('transaction_date')" class="sortable">Date <span v-html="sortArrow('transaction_date')"></span></th>
            <th @click="sortBy('expected_delivery_date')" class="sortable">Expected <span v-html="sortArrow('expected_delivery_date')"></span></th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="8"><div class="po-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="o in paged" :key="o.name" class="po-row" :class="{selected:selected.has(o.name)}">
              <td><input type="checkbox" :checked="selected.has(o.name)" @change="toggle(o.name)" /></td>
              <td @click="openView(o)"><span class="po-num">{{ o.name }}</span></td>
              <td @click="openView(o)">{{ o.supplier_name || o.supplier || '—' }}</td>
              <td @click="openView(o)" class="text-muted mono-sm">{{ fmtDate(o.transaction_date) }}</td>
              <td @click="openView(o)" :class="isPastExpected(o)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(o.expected_delivery_date)||'—' }}</td>
              <td @click="openView(o)"><span class="po-badge" :class="badgeClass(o)">{{ displayStatus(o) }}</span></td>
              <td @click="openView(o)" class="ta-r mono-sm">{{ fmtCur(o.grand_total) }}</td>
              <td class="po-act-cell">
                <button class="po-act-btn" @click="openView(o)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button class="po-act-btn" @click="openEdit(o)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button class="po-act-btn po-act-conv" v-if="canBill(o)" @click="openBillModal(o)" title="Bill"><span v-html="icon('arrow-right',13)"></span></button>
                <button class="po-act-btn po-act-del" @click="deletePO(o)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="po-empty">No purchase orders match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Pagination ── -->
    <div v-if="!loading && sorted.length" style="padding:12px 4px 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ── Create / Edit Drawer ── -->
    <div v-if="drawerOpen" class="po-overlay" @click.self="drawerOpen=false"></div>
    <div class="po-drawer" :class="{open:drawerOpen}">
      <div class="po-dheader">
        <div class="po-dheader-title">{{ editingName ? 'Edit Purchase Order' : 'New Purchase Order' }}</div>
        <button class="po-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="po-dbody">
        <div class="po-fields-grid">
          <div class="po-field" style="grid-column:1/-1">
            <label class="po-label">Vendor <span class="req">*</span></label>
            <SearchableSelect v-model="form.supplier" :options="vendors" placeholder="Select vendor…"
              :createable="true" createDoctype="Supplier"
              @search="fetchVendors" />
          </div>
          <div class="po-field">
            <label class="po-label">Order Date <span class="req">*</span></label>
            <input v-model="form.transaction_date" type="date" class="po-input" />
          </div>
          <div class="po-field">
            <label class="po-label">Expected Delivery</label>
            <input v-model="form.expected_delivery_date" type="date" class="po-input" />
          </div>
          <div class="po-field">
            <label class="po-label">Billing Address</label>
            <input v-model="form.billing_address" type="text" class="po-input" placeholder="Optional" />
          </div>
          <div class="po-field">
            <label class="po-label">Delivery Address</label>
            <input v-model="form.delivery_address" type="text" class="po-input" placeholder="Optional" />
          </div>
          <div class="po-field" style="grid-column:1/-1">
            <label class="po-label">Receiving Warehouse <span style="color:#dc2626">*</span></label>
            <SearchableSelect v-model="form.set_warehouse" :options="warehouses" placeholder="Select warehouse where goods will be received…" @search="fetchWarehouses" />
          </div>
        </div>

        <div class="po-section-title">Items</div>
        <div class="po-items-table">
          <div class="po-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="po-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items"
              placeholder="Item…" :createable="true" createDoctype="Item"
              @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="po-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="po-input ta-r" @input="calcLine(line)" /></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="po-input ta-r" @input="calcLine(line)" /></div>
            <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
            <div><button @click="removeLine(line.id)" class="po-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="po-add-line" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <div class="po-totals">
          <div class="po-field" style="max-width:160px">
            <label class="po-label">Tax Rate %</label>
            <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="po-input" />
          </div>
          <div class="po-totals-right">
            <div class="po-total-row"><span>Subtotal</span><span>{{ fmtCur(subtotal) }}</span></div>
            <div class="po-total-row"><span>Tax ({{ form.tax_rate||0 }}%)</span><span>{{ fmtCur(taxAmount) }}</span></div>
            <div class="po-total-row grand"><span>Total</span><span>{{ fmtCur(subtotal+taxAmount) }}</span></div>
          </div>
        </div>

        <div class="po-field">
          <label class="po-label">Terms & Conditions</label>
          <textarea v-model="form.terms" rows="3" class="po-input" placeholder="Optional"></textarea>
        </div>
      </div>
      <div class="po-dfooter">
        <button class="po-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="po-btn-save" :disabled="drawerSaving" @click="savePO('Draft')">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="po-btn-primary" :disabled="drawerSaving" @click="savePO('To Receive')">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Issue PO' }}
        </button>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="po-overlay" @click.self="viewOpen=false"></div>
    <div class="po-drawer po-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="po-view-head" :style="`background:${headerBg(viewDoc)}`">
          <div>
            <div class="po-view-num">{{ viewDoc.name }}</div>
            <div class="po-view-sub">{{ viewDoc.supplier_name||viewDoc.supplier }}</div>
          </div>
          <div style="text-align:right">
            <div class="po-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="po-badge po-badge-white">{{ displayStatus(viewDoc) }}</span>
          </div>
          <button class="po-dclose po-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <TimelineStepper :steps="timelineSteps" />

        <div class="po-tabs">
          <button class="po-tab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="po-tab" :class="{active:viewTab==='fulfill'}" @click="viewTab='fulfill'">Fulfillment</button>
          <button class="po-tab" :class="{active:viewTab==='links'}" @click="viewTab='links'">
            Linked<span v-if="links.bills.length>0" class="po-tab-count">{{ links.bills.length }}</span>
          </button>
        </div>

        <div class="po-dbody">
          <template v-if="viewTab==='details'">
            <div class="po-meta-grid">
              <div><div class="po-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
              <div><div class="po-meta-lbl">Expected Delivery</div>
                <div class="mono-sm" :class="isPastExpected(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.expected_delivery_date)||'—' }}</div>
              </div>
              <div><div class="po-meta-lbl">Billing Address</div><div>{{ viewDoc.billing_address||'—' }}</div></div>
              <div><div class="po-meta-lbl">Delivery Address</div><div>{{ viewDoc.delivery_address||'—' }}</div></div>
            </div>
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="po-section-title">Line Items</div>
              <div class="po-view-items">
                <div class="po-view-items-head"><span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span></div>
                <div v-for="it in viewItems" :key="it.name" class="po-view-items-row">
                  <span><strong>{{ it.item_name||it.item_code }}</strong>
                    <div v-if="it.description" class="text-muted" style="font-size:11px">{{ it.description }}</div></span>
                  <span class="ta-r mono-sm">{{ it.qty }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(it.amount) }}</span>
                </div>
              </div>
            </template>
            <div v-if="viewDoc.terms" class="po-terms">
              <div class="po-meta-lbl">Terms & Conditions</div>
              <div style="white-space:pre-wrap;font-size:12.5px;color:#374151">{{ viewDoc.terms }}</div>
            </div>
          </template>

          <template v-if="viewTab==='fulfill'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="fulfill.lines.length">
              <div style="font-size:12px;color:#6b7280">Status: <strong>{{ fulfill.computed_status }}</strong></div>
              <div class="po-fulfill-tbl">
                <div class="po-fulfill-head">
                  <span>Item</span><span class="ta-r">Ordered</span><span class="ta-r">Received</span>
                  <span class="ta-r">Billed</span><span class="ta-r">Remaining</span>
                </div>
                <div v-for="l in fulfill.lines" :key="l.name" class="po-fulfill-row">
                  <span>{{ l.item_name||l.item_code }}</span>
                  <span class="ta-r mono-sm">{{ l.qty }}</span>
                  <span class="ta-r mono-sm" :class="l.received_qty>=l.qty?'text-success':'text-muted'">{{ l.received_qty }}</span>
                  <span class="ta-r mono-sm" :class="l.billed_qty>=l.qty?'text-success':'text-muted'">{{ l.billed_qty }}</span>
                  <span class="ta-r mono-sm text-danger">{{ l.remaining_to_receive }} / {{ l.remaining_to_bill }}</span>
                </div>
              </div>
              <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px">
                <button v-if="hasUnreceived" class="po-btn-ghost" @click="markAllReceived" :disabled="actionRunning">📦 Mark All Received</button>
              </div>
            </template>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">No line items.</div>
          </template>

          <template v-if="viewTab==='links'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else>
              <div v-if="links.bills.length" class="po-section-title">Vendor Bills</div>
              <div v-for="b in links.bills" :key="b.name" class="po-link-row">
                <span class="po-num">{{ b.name }}</span>
                <span class="text-muted">{{ fmtDate(b.posting_date) }}</span>
                <span class="text-muted">Out: {{ fmtCur(b.outstanding_amount) }}</span>
                <span style="text-align:right;font-weight:600">{{ fmtCur(b.grand_total) }}</span>
              </div>
              <div v-if="!links.bills.length"
                style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
                No linked bills yet.
              </div>
            </template>
          </template>
        </div>

        <div class="po-dfooter">
          <button class="po-btn-ghost" @click="viewOpen=false">Close</button>
          <button class="po-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button class="po-btn-ghost" @click="emailPO(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="po-btn-ghost" @click="printPO(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="canBill(viewDoc)" class="po-btn-primary" @click="openBillModal(viewDoc)">→ Bill</button>
          <button class="po-btn-danger" @click="cancelPO(viewDoc)">Cancel</button>
          <button class="po-btn-danger" @click="deletePO(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Convert-to-Bill modal (partial-qty + 3-way warn) ── -->
    <div v-if="billModal.open" class="po-overlay" @click.self="billModal.open=false" style="z-index:60"></div>
    <div v-if="billModal.open" class="po-apply-dialog">
      <div class="po-dheader" style="background:linear-gradient(135deg,#1e3a5f,#1a6ef7);color:#fff;height:auto;padding:14px 18px">
        <div style="color:#fff;font-weight:700">Convert to Bill — {{ billModal.poName }}</div>
        <button class="po-dclose" style="color:#fff" @click="billModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="po-dbody">
        <div style="font-size:12.5px;color:#374151">Enter the quantity to bill for each line (defaults to remaining):</div>
        <div class="po-inv-tbl">
          <div class="po-inv-head">
            <span>Item</span><span class="ta-r">Recv'd</span><span class="ta-r">Remaining</span><span class="ta-r">Bill</span>
          </div>
          <div v-for="l in billModal.lines" :key="l.name" class="po-inv-row" :class="{warn:l.toBill > (l.received_qty - l.billed_qty)}">
            <span>{{ l.item_name||l.item_code }}</span>
            <span class="ta-r mono-sm text-muted">{{ l.received_qty }}</span>
            <span class="ta-r mono-sm text-muted">{{ l.remaining_to_bill }}</span>
            <input v-model.number="l.toBill" type="number" min="0" :max="l.remaining_to_bill" step="0.001"
              class="po-input ta-r" style="font-family:monospace;width:90px" />
          </div>
        </div>
        <div v-if="threeWayMismatch" class="po-warn">
          ⚠ Billing more than received on at least one line. Three-way match will fail. Proceed only if approved.
        </div>
        <div class="po-fields-grid">
          <div class="po-field">
            <label class="po-label">Vendor Bill #</label>
            <input v-model="billModal.billNo" type="text" class="po-input" />
          </div>
          <div class="po-field">
            <label class="po-label">Vendor Bill Date</label>
            <input v-model="billModal.billDate" type="date" class="po-input" />
          </div>
          <div class="po-field" style="grid-column:1/-1">
            <label class="po-label">Due Date</label>
            <input v-model="billModal.dueDate" type="date" class="po-input" />
          </div>
        </div>
        <div style="text-align:right;font-size:13px;color:#6b7280">
          Bill Total: <strong style="color:#111827">{{ fmtCur(billModalTotal) }}</strong>
        </div>
      </div>
      <div class="po-dfooter">
        <button class="po-btn-ghost" @click="billModal.open=false" :disabled="billModal.saving">Cancel</button>
        <button class="po-btn-primary" :disabled="billModal.saving||billModalTotal<=0" @click="submitBill">
          {{ billModal.saving ? 'Creating…' : `Create Bill ${fmtCur(billModalTotal)}` }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiPOST, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { useConfirm } from "../composables/useConfirm.js";
import { useLivePreview } from "../composables/useLivePreview.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import Pagination from "../components/Pagination.vue";
import { usePagination } from "../composables/usePagination.js";
import BulkActionBar from "../components/BulkActionBar.vue";
import TimelineStepper from "../components/TimelineStepper.vue";

const { toast } = useToast();
const { confirm } = useConfirm();
const { printDoc } = useLivePreview();
function printPO(d) { printDoc(d, { title: "PURCHASE ORDER", partyLabel: "Vendor", partyField: "supplier_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();

const activeTab = ref("all");
const tabs = [
  { key: "all",       label: "All" },
  { key: "draft",     label: "Draft" },
  { key: "toReceive", label: "To Receive" },
  { key: "toBill",    label: "To Bill" },
  { key: "closed",    label: "Closed" },
  { key: "cancelled", label: "Cancelled" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const viewLoading = ref(false), viewItems = ref([]);
const fulfill = reactive({ lines: [], computed_status: "" });
const links = reactive({ bills: [], purchase_receipts: [] });
const vendors = ref([]), items = ref([]), lines = ref([]), taxAccountHead = ref("");
const sortCol = ref("transaction_date"), sortDir = ref("desc");
const actionRunning = ref(false);

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const form = reactive({
  supplier: "", transaction_date: todayStr(), expected_delivery_date: expectedDefault(),
  billing_address: "", delivery_address: "", set_warehouse: "", tax_rate: 0, terms: "",
});
const warehouses = ref([]);
async function fetchWarehouses(q = "") {
  try {
    const co = await resolveCompany();
    const rows = await apiList("Warehouse", { filters: [["company","=",co],["disabled","=",0],["is_group","=",0]], fields: ["name","parent_warehouse"], limit: 50 });
    warehouses.value = (rows || [])
      .filter(r => !q || r.name.toLowerCase().includes(q.toLowerCase()) || (r.parent_warehouse||"").toLowerCase().includes(q.toLowerCase()))
      .map(r => ({ label: r.parent_warehouse ? `${r.parent_warehouse} / ${r.name}` : r.name, value: r.name }));
  } catch { warehouses.value = []; }
}

const billModal = reactive({ open: false, saving: false, poName: "", lines: [],
  billNo: "", billDate: "", dueDate: "" });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function expectedDefault() { const d = new Date(); d.setDate(d.getDate() + 7); return d.toISOString().slice(0, 10); }
function fmtCur(v) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v)); }

function isPastExpected(o) {
  if (!o?.expected_delivery_date) return false;
  const s = (o.status||"").toLowerCase();
  if (s === "closed" || s === "billed" || s === "cancelled" || s === "received") return false;
  return new Date(o.expected_delivery_date) < new Date();
}
function displayStatus(o) { return (o?.status || "Draft").toUpperCase(); }
function badgeClass(o) {
  const s = (o?.status||"").toLowerCase();
  if (!s || s === "draft")  return "po-bdg-grey";
  if (s === "cancelled")    return "po-bdg-red";
  if (s === "closed" || s === "billed") return "po-bdg-green";
  if (s.includes("received") && !s.includes("partially")) return "po-bdg-blue";
  if (s === "to receive" || s.includes("partially") || s === "sent" || s === "confirmed") return "po-bdg-orange";
  return "po-bdg-blue";
}
function headerBg(o) {
  const s = (o?.status||"").toLowerCase();
  if (s === "cancelled") return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  if (s === "closed" || s === "billed") return "linear-gradient(135deg,#064e3b,#059669)";
  if (s === "to receive" || s.includes("partially") || s === "sent" || s === "confirmed") return "linear-gradient(135deg,#78350f,#d97706)";
  if (s === "received") return "linear-gradient(135deg,#1e3a5f,#1a6ef7)";
  return "linear-gradient(135deg,#374151,#6b7280)";
}
function canBill(o) {
  const s = (o?.status||"").toLowerCase();
  return s !== "cancelled" && s !== "closed" && s !== "billed";
}

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    list.value = await apiList("Purchase Order", {
      fields: ["name", "supplier", "supplier_name", "transaction_date", "expected_delivery_date", "status", "grand_total", "billed_amount", "billing_address", "delivery_address"],
      filters: [["company", "=", co]],
      limit: 500,
      order: "transaction_date desc",
    });
  } catch (e) { toast.error(e.message || "Failed to load purchase orders"); }
  finally { loading.value = false; }
}
async function loadTaxAccount() {
  try {
    const r = await apiList("Account", { fields: ["name"], filters: [["account_type", "=", "Tax"], ["is_group", "=", 0]], limit: 1 });
    if (r?.length) taxAccountHead.value = r[0].name;
  } catch {}
}

const counts = computed(() => {
  const c = { draft:0, toReceive:0, toBill:0, closed:0, cancelled:0 };
  for (const o of list.value) {
    const s = (o.status||"draft").toLowerCase();
    if (s === "cancelled") c.cancelled++;
    else if (s === "closed" || s === "billed") c.closed++;
    else if (s === "draft") c.draft++;
    else if (s === "received") c.toBill++;
    else c.toReceive++;
  }
  return c;
});
const summary = computed(() => ({
  totalValue: list.value.filter(o => (o.status||"").toLowerCase() !== "cancelled")
    .reduce((s, o) => s + flt(o.grand_total), 0),
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") {
    r = r.filter(o => {
      const s = (o.status||"draft").toLowerCase();
      if (activeTab.value === "draft")     return s === "draft";
      if (activeTab.value === "cancelled") return s === "cancelled";
      if (activeTab.value === "closed")    return s === "closed" || s === "billed";
      if (activeTab.value === "toBill")    return s === "received";
      if (activeTab.value === "toReceive") return s !== "cancelled" && s !== "closed" && s !== "billed" && s !== "draft" && s !== "received";
      return true;
    });
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.supplier_name || x.supplier || "").toLowerCase().includes(q));
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
const { page, pageSize, paged } = usePagination(sorted, { storageKey: "purchase-orders" });
function sortBy(col) { if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc"; else { sortCol.value = col; sortDir.value = "asc"; } }
function sortArrow(col) { if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value === "asc" ? "↑" : "↓"; }

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(o => selected.value.has(o.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(o => o.name)) : new Set(); }

const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const taxAmount = computed(() => Math.round(subtotal.value * flt(form.tax_rate) / 100 * 100) / 100);

const hasUnreceived = computed(() => fulfill.lines.some(l => l.remaining_to_receive > 0));

const timelineSteps = computed(() => {
  const o = viewDoc.value;
  if (!o) return [];
  const s = (o.status||"").toLowerCase();
  if (s === "cancelled") {
    return [
      { key:"draft", label:"Draft", done:true },
      { key:"sub",   label:"Issued", done:true },
      { key:"end",   label:"Cancelled", danger:true, current:true },
    ];
  }
  const received = s === "received" || s === "billed" || s === "closed";
  const billed   = s === "billed"   || s === "closed";
  const closed   = s === "closed";
  return [
    { key:"draft",    label:"Draft",    done:true },
    { key:"issued",   label:"Issued",   done:s!=="draft", current:s==="to receive"||s==="sent"||s==="confirmed" },
    { key:"received", label:"Received", done:received, current:s==="received" && !billed },
    { key:"billed",   label:"Billed",   done:billed, current:billed && !closed },
    { key:"closed",   label:"Closed",   done:closed, current:closed },
  ];
});

const billModalTotal = computed(() =>
  (billModal.lines || []).reduce((s, l) => s + flt(l.toBill) * flt(l.rate), 0)
);
const threeWayMismatch = computed(() =>
  (billModal.lines || []).some(l => flt(l.toBill) > (flt(l.received_qty) - flt(l.billed_qty)))
);

// ── Create / Edit ─────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { supplier: "", transaction_date: todayStr(), expected_delivery_date: expectedDefault(), billing_address: "", delivery_address: "", set_warehouse: "", tax_rate: 0, terms: "" });
  fetchWarehouses("");
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems("");
  drawerOpen.value = true;
}
async function openEdit(o) {
  editingName.value = o.name;
  Object.assign(form, {
    supplier: o.supplier || "", transaction_date: o.transaction_date || todayStr(),
    expected_delivery_date: o.expected_delivery_date || expectedDefault(),
    billing_address: o.billing_address || "", delivery_address: o.delivery_address || "",
    set_warehouse: "", tax_rate: 0, terms: o.terms || "",
  });
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems(""); fetchWarehouses("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Purchase Order", o.name);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || "",
        qty: i.qty || 1, rate: i.rate || 0, amount: i.amount || 0,
      }));
    }
    if (doc?.set_warehouse) form.set_warehouse = doc.set_warehouse;
    if (doc?.taxes?.[0]?.rate) form.tax_rate = doc.taxes[0].rate;
    if (doc?.taxes?.[0]?.account_head) taxAccountHead.value = doc.taxes[0].account_head;
    if (doc?.terms) form.terms = doc.terms;
  } catch {}
}
async function openView(o) {
  viewDoc.value = o;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  fulfill.lines = []; fulfill.computed_status = "";
  links.bills = []; links.purchase_receipts = [];
  try {
    const [doc, ful, lnk] = await Promise.all([
      apiGet("Purchase Order", o.name),
      apiGET("zoho_books_clone.api.docs.get_purchase_order_fulfillment", { purchase_order: o.name }).catch(() => null),
      apiGET("zoho_books_clone.api.docs.get_purchase_order_links", { purchase_order: o.name }).catch(() => null),
    ]);
    viewItems.value = doc?.items || [];
    viewDoc.value = { ...o, ...doc };
    if (ful) { fulfill.lines = ful.lines || []; fulfill.computed_status = ful.computed_status || ""; }
    if (lnk) { links.bills = lnk.bills || []; }
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
    const r = await apiList("Item", { fields: ["name", "item_name", "description", "standard_rate", "stock_uom"], filters: f, limit: 30, order: "item_name asc" });
    items.value = r.map(x => ({ ...x, label: x.item_name || x.name, value: x.name, rate: x.standard_rate || 0, description: x.description || "" }));
  } catch { items.value = []; }
}
async function onItemSelect(line, opt) {
  line.item_code = opt?.value ?? opt;
  if (opt?.rate)        { line.rate        = Number(opt.rate) || 0; }
  if (opt?.item_name)   { line.item_name   = opt.item_name; }
  if (opt?.description) { line.description = opt.description; }
  else if (opt?.value) {
    // description not in option cache — fetch from Item doc directly
    try {
      const doc = await apiGet("Item", opt.value);
      if (doc?.description) line.description = doc.description;
      if (doc?.item_name)   line.item_name   = doc.item_name;
    } catch {}
  }
  calcLine(line);
}
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }

async function savePO(newStatus) {
  if (!form.supplier) return toast.error("Vendor is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  if (!form.set_warehouse) return toast.error("Receiving Warehouse is required");
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const taxes = form.tax_rate > 0 && taxAccountHead.value
      ? [{ doctype: "Tax Line", charge_type: "On Net Total", account_head: taxAccountHead.value, description: taxAccountHead.value, rate: form.tax_rate }]
      : [];
    const doc = {
      doctype: "Purchase Order", company,
      supplier: form.supplier, transaction_date: form.transaction_date,
      expected_delivery_date: form.expected_delivery_date || null,
      billing_address: form.billing_address || "",
      delivery_address: form.delivery_address || "",
      set_warehouse: form.set_warehouse || "",
      status: newStatus || "Draft",
      terms: form.terms || "",
      items: lines.value.filter(l => l.item_code).map(l => ({
        doctype: "Purchase Order Item", item_code: l.item_code,
        description: l.description || l.item_code,
        qty: flt(l.qty) || 1, rate: flt(l.rate), amount: flt(l.amount),
      })),
      taxes,
    };
    if (editingName.value) doc.name = editingName.value;
    const saved = await apiSave(doc);
    toast.success(`Purchase Order ${saved?.name || ""} saved`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save PO"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailPO(o) {
  await openEmail({
    doctype: "Purchase Order", name: o.name, docLabel: `Purchase Order ${o.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_purchase_order_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_purchase_order_email",
    paramKey: "purchase_order",
  });
}

function openBillModal(o) {
  apiGET("zoho_books_clone.api.docs.get_purchase_order_fulfillment", { purchase_order: o.name })
    .then(r => {
      const ful = r?.lines || [];
      Object.assign(billModal, {
        open: true, saving: false, poName: o.name,
        lines: ful.filter(l => l.remaining_to_bill > 0)
                  .map(l => ({ ...l, toBill: Math.min(l.remaining_to_bill, Math.max(0, l.received_qty - l.billed_qty)) || l.remaining_to_bill })),
        billNo: "", billDate: todayStr(), dueDate: o.expected_delivery_date || todayStr(),
      });
      if (!billModal.lines.length) { billModal.open = false; toast.info("Nothing left to bill"); }
    })
    .catch(e => toast.error(e.message || "Failed to load fulfillment"));
}
async function submitBill() {
  const lineMap = {};
  for (const l of billModal.lines) {
    if (flt(l.toBill) > 0) lineMap[l.name] = flt(l.toBill);
  }
  if (!Object.keys(lineMap).length) { toast.error("Enter at least one qty to bill"); return; }
  billModal.saving = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.docs.convert_purchase_order_to_bill", {
      purchase_order: billModal.poName,
      line_qtys: JSON.stringify(lineMap),
      bill_no: billModal.billNo || "",
      bill_date: billModal.billDate || "",
      due_date: billModal.dueDate || "",
    });
    toast.success(`Bill created: ${r?.bill}`);
    if (r?.three_way_warnings?.length) {
      toast.warn?.("3-way match: " + r.three_way_warnings.join("; ")) || toast.info("3-way mismatch — check fulfillment");
    }
    billModal.open = false;
    await load();
    if (viewDoc.value?.name === billModal.poName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Convert failed"); }
  billModal.saving = false;
}

async function markAllReceived() {
  actionRunning.value = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.docs.mark_po_received", { purchase_order: viewDoc.value.name });
    toast.success(`Marked ${r?.lines_updated || 0} line(s) received`);
    await load();
    if (viewDoc.value) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Mark received failed"); }
  actionRunning.value = false;
}

async function cancelPO(o) {
  if (!await confirm({ title: "Cancel Purchase Order", body: `Cancel ${o.name}? Linked bills must be cancelled separately.`, okLabel: "Cancel PO" })) return;
  try {
    await apiPOST("zoho_books_clone.api.docs.cancel_purchase_order_safe", { purchase_order: o.name });
    toast.success("Purchase Order cancelled");
    await load(); if (viewDoc.value?.name === o.name) await openView(o);
  } catch (e) { toast.error(e.message || "Cancel failed"); }
}
async function deletePO(o) {
  if (!await confirm({ title: "Delete Purchase Order", body: `Permanently delete ${o.name}?`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Purchase Order", o.name);
    toast.success("Purchase Order deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk actions ──────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(o => selected.value.has(o.name) && (!o.status || o.status === "Draft"));
  if (!drafts.length) { toast.info("Select drafts to delete"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft PO(s)?`, okLabel: "Delete" })) return;
  for (const o of drafts) { try { await apiDelete("Purchase Order", o.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length}`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(o => selected.value.has(o.name));
  if (!subs.length) { toast.info("No POs selected"); return; }
  let sent = 0;
  for (const o of subs) {
    const ok = await openEmail({
      doctype: "Purchase Order", name: o.name, docLabel: `Purchase Order ${o.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_purchase_order_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_purchase_order_email",
      paramKey: "purchase_order",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} PO(s)`);
}

function exportCSV() {
  const rows = selected.value.size
    ? sorted.value.filter(p => selected.value.has(p.name))
    : sorted.value;
  if (!rows.length) return;
  const head = ["PO #","Vendor","Date","Expected","Status","Amount"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const o of rows) {
    out.push([o.name, o.supplier_name || o.supplier, o.transaction_date, o.expected_delivery_date || "",
      o.status || "Draft", Number(o.grand_total || 0).toFixed(2)].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `purchase_orders_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} PO(s)`);
}

onMounted(() => { load(); loadTaxAccount(); });
</script>

<style scoped>
.po-page { display: flex; flex-direction: column; gap: 16px; padding: 24px; }
.po-actions { display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: nowrap;
    padding: 12px 16px;
    background: transparent;
    border-bottom: none; }
.po-search-wrap { display: flex; align-items: center; gap: 8px; background: #ffffff; border-radius: 8px; padding: 6px 12px; min-width: 220px; }
.po-search-input { border: none; background: transparent; outline: none; font: inherit; color: #111827; width: 100%; font-size: 13px; }
.po-pills {display: flex;
    gap: 6px;
    flex-wrap: nowrap;
    overflow-x: auto;
    scrollbar-width: none;
    flex: 1 1 auto;
    min-width: 0; }
.po-pill {     padding: 5px 11px;
    border-radius: 20px;
    font-size: 12px;
    font-weight: 600;
    border: 1px solid #e5e7eb;
    background: #fff;
    color: #6b7280;
    cursor: pointer;
    font-family: inherit;
    display: inline-flex;
    align-items: center;
    gap: 5px;
    white-space: nowrap;
    transition: border-color .15s, color .15s, background .15s;}
.po-pill:hover { color: #2563eb; border-color: #2563eb; }
.po-pill.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.po-pill-count { background: #f3f4f6; color: #6b7280; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.po-pill.active .po-pill-count { background: #2563eb; color: #fff; }
.po-btn-primary { display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.po-btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.po-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.po-btn-ghost { display: inline-flex; align-items: center; gap: 6px; background: #ffffff; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #374151; cursor: pointer; }
.po-btn-ghost:hover { background: #f9fafb; }
.po-btn-save { display: inline-flex; align-items: center; gap: 6px; background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.po-btn-save:hover { background: #dcfce7; }
.po-btn-save:disabled { opacity: .5; cursor: not-allowed; }
.po-btn-danger { display: inline-flex; align-items: center; gap: 6px; background: #fef2f2; border: 1px solid #dc2626; color: #dc2626; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.po-btn-danger:hover { background: #fee2e2; }

.po-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; }
.po-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.po-table th { background: #f9fafb; border-bottom: 1px solid #e5e7eb; padding: 10px 12px; font-size: 11.5px; font-weight: 600; color: #374151; text-align: left; white-space: nowrap; }
.po-table th.sortable { cursor: pointer; user-select: none; }
.po-table th.sortable:hover { color: #2563eb; }
.ta-r { text-align: right !important; }
.po-row td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; cursor: pointer; }
.po-row:last-child td { border-bottom: none; }
.po-row:hover td { background: #f9fafb; }
.po-row.selected td { background: #eff6ff; }
.po-num { font-family: monospace; font-size: 12.5px; color: #2563eb; font-weight: 600; }
.mono-sm { font-family: monospace; font-size: 12.5px; }
.text-muted { color: #6b7280; }
.text-danger { color: #dc2626; }
.text-success { color: #059669; }
.po-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 10px; font-size: 11.5px; font-weight: 600; }
.po-bdg-grey   { background: #f3f4f6; color: #6b7280; }
.po-bdg-blue   { background: #dbeafe; color: #1a6ef7; }
.po-bdg-green  { background: #d1fae5; color: #059669; }
.po-bdg-orange { background: #fef3c7; color: #d97706; }
.po-bdg-red    { background: #fee2e2; color: #dc2626; }
.po-badge-white { background: rgba(255,255,255,.2); color: #fff !important; border: 1px solid rgba(255,255,255,.4); }
.po-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.po-act-btn { background: transparent; border: 1px solid #e5e7eb; border-radius: 6px; width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #6b7280; }
.po-act-btn:hover { background: #f3f4f6; color: #2563eb; }
.po-act-conv { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.po-act-conv:hover { background: #dbeafe; }
.po-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.po-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }
.po-shimmer { height: 13px; background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%); border-radius: 4px; animation: shimmer 1.2s infinite; background-size: 200% 100%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

.po-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.2); z-index: 40; }
.po-drawer { position: fixed; top: 0; right: -600px; bottom: 0; width: 600px; max-width: 96vw; background: #fff; border-left: 1px solid #e5e7eb; box-shadow: -8px 0 24px rgba(0,0,0,.08); z-index: 50; display: flex; flex-direction: column; transition: right .22s ease; }
.po-drawer.open { right: 0; }
.po-view-drawer { width: 540px; right: -540px; }
.po-view-drawer.open { right: 0; }
.po-dheader { display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 60px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0;background: linear-gradient(135deg,#1e3a5f,#1a6ef7); color: #fff; }
.po-dheader-title { font-size: 15px; font-weight: 600; color: #ffffff; }
.po-dclose { background: #ffffff26;
    border: none;
    cursor: pointer;
    width: 30px;
    height: 30px;
    border-radius: 8px;
    color: #fff;
    display: grid;
    place-items: center;}
.po-dclose:hover { background: #f3f4f6; color: #111827; }
.po-dbody { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.po-fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.po-field { display: flex; flex-direction: column; gap: 4px; }
.po-label { font-size: 12px; font-weight: 600; color: #374151; }
.req { color: #dc2626; }
.po-input { width: 100%; box-sizing: border-box; border: 1px solid #e5e7eb; border-radius: 6px; padding: 7px 10px; font: inherit; font-size: 13px; outline: none; background: #fff; color: #111827; }
.po-input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.08); }
textarea.po-input { resize: vertical; }
.po-section-title { font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: .05em; padding-bottom: 4px; border-bottom: 1px solid #f3f4f6; }
.po-items-table { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 8px; }
.po-items-head { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #374151; }
.po-items-row { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; }
.po-add-line { background: transparent; border: none; color: #2563eb; font-size: 12.5px; font-weight: 600; cursor: pointer; padding: 8px 12px; display: inline-flex; align-items: center; gap: 6px; }
.po-add-line:hover { background: #eff6ff; }
.po-rm-line { background: transparent; border: 1px solid #e5e7eb; border-radius: 4px; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #9ca3af; }
.po-rm-line:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.po-totals { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.po-totals-right { display: flex; flex-direction: column; gap: 4px; min-width: 220px; }
.po-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 3px 0; }
.po-total-row.grand { font-weight: 700; font-size: 14px; color: #111827; border-top: 1px solid #e5e7eb; padding-top: 6px; }

.po-view-head { position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 20px; flex-shrink: 0; color: #fff; }
.po-view-num { font-size: 18px; font-weight: 700; font-family: monospace; color: #fff; }
.po-view-sub { font-size: 13px; color: rgba(255,255,255,.8); margin-top: 2px; }
.po-view-amount { font-size: 22px; font-weight: 800; font-family: monospace; color: #fff; }
.po-vclose { position: absolute; top: 12px; right: 12px; color: #fff; }
.po-vclose:hover { background: rgba(255,255,255,.18); color: #fff; }
.po-tabs { display: flex; gap: 4px; padding: 0 20px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; background: #fff; }
.po-tab { background: transparent; border: none; padding: 10px 14px; font: inherit; font-size: 12.5px; font-weight: 600; color: #6b7280; cursor: pointer; border-bottom: 2px solid transparent; display: inline-flex; align-items: center; gap: 6px; }
.po-tab:hover { color: #2563eb; }
.po-tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.po-tab-count { background: #2563eb; color: #fff; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.po-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.po-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }
.po-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px;}
.po-view-items-head { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.po-view-items-row { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.po-terms { padding: 10px 12px; background: #f8fafc; border-radius: 6px; }
.po-link-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 12.5px; align-items: center; }
.po-fulfill-tbl { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.po-fulfill-head { display: grid; grid-template-columns: 2fr 80px 100px 90px 110px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.po-fulfill-row { display: grid; grid-template-columns: 2fr 80px 100px 90px 110px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.po-dfooter { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #e5e7eb; flex-shrink: 0; flex-wrap: wrap; }

.po-apply-dialog { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 560px; max-width: 96vw; background: #fff; border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.2); z-index: 70; display: flex; flex-direction: column; overflow: hidden; }
.po-inv-tbl { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.po-inv-head { display: grid; grid-template-columns: 2fr 80px 90px 110px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.po-inv-row { display: grid; grid-template-columns: 2fr 80px 90px 110px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.po-inv-row.warn { background: #fef3c7; }
.po-warn { background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 10px 12px; font-size: 12.5px; color: #92400e; }
</style>