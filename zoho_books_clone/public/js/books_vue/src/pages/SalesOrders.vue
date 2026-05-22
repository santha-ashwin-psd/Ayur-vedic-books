<template>
  <div class="so-page">

    <!-- ── Toolbar ── -->
    <div class="so-actions">
      <div class="so-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search orders, customers…" class="so-search-input" />
      </div>
      <div class="so-pills">
        <button v-for="t in tabs" :key="t.key"
          class="so-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">
          {{ t.label }}
          <span v-if="t.key!=='all'" class="so-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="so-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="so-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="so-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Sales Order
        </button>
      </div>
    </div>

    <!-- ── Summary strip ── -->
    <SummaryStrip :cards="[
      { label: 'Total Orders', value: list.length },
      { label: 'To Deliver', value: counts.toDeliver, accent: '#d97706' },
      { label: 'To Invoice', value: counts.toInvoice, accent: '#1a6ef7' },
      { label: 'Pipeline Value', value: fmtCur(summary.totalValue), accent: '#059669' },
    ]" />

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button class="bab-danger" @click="bulkDelete">Delete</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="so-card">
      <table class="so-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">Order # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('customer_name')" class="sortable">Customer <span v-html="sortArrow('customer_name')"></span></th>
            <th @click="sortBy('transaction_date')" class="sortable">Date <span v-html="sortArrow('transaction_date')"></span></th>
            <th @click="sortBy('delivery_date')" class="sortable">Delivery <span v-html="sortArrow('delivery_date')"></span></th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="8"><div class="so-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="o in sorted" :key="o.name" class="so-row" :class="{selected:selected.has(o.name)}">
              <td><input type="checkbox" :checked="selected.has(o.name)" @change="toggle(o.name)" /></td>
              <td @click="openView(o)"><span class="so-num">{{ o.name }}</span></td>
              <td @click="openView(o)">{{ o.customer_name || o.customer || '—' }}</td>
              <td @click="openView(o)" class="text-muted mono-sm">{{ fmtDate(o.transaction_date) }}</td>
              <td @click="openView(o)" :class="isPastDelivery(o)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(o.delivery_date)||'—' }}</td>
              <td @click="openView(o)"><span class="so-badge" :class="badgeClass(o)">{{ displayStatus(o) }}</span></td>
              <td @click="openView(o)" class="ta-r mono-sm">{{ fmtCur(o.grand_total) }}</td>
              <td class="so-act-cell">
                <button class="so-act-btn" @click="openView(o)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button class="so-act-btn" @click="openEdit(o)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button class="so-act-btn so-act-conv" v-if="canInvoice(o)" @click="openInvoiceModal(o)" title="Invoice"><span v-html="icon('arrow-right',13)"></span></button>
                <button class="so-act-btn so-act-del" @click="deleteSO(o)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="so-empty">No sales orders match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Create / Edit Drawer ── -->
    <div v-if="drawerOpen" class="so-overlay" @click.self="drawerOpen=false"></div>
    <div class="so-drawer" :class="{open:drawerOpen}">
      <div class="so-dheader">
        <div class="so-dheader-title">{{ editingName ? 'Edit Sales Order' : 'New Sales Order' }}</div>
        <button class="so-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="so-dbody">
        <div class="so-fields-grid">
          <div class="so-field" style="grid-column:1/-1">
            <label class="so-label">Customer <span class="req">*</span></label>
            <SearchableSelect v-model="form.customer" :options="customers" placeholder="Select customer…"
              :createable="true" createDoctype="Customer"
              @search="fetchCustomers" />
          </div>
          <div class="so-field">
            <label class="so-label">Order Date <span class="req">*</span></label>
            <input v-model="form.transaction_date" type="date" class="so-input" />
          </div>
          <div class="so-field">
            <label class="so-label">Delivery Date</label>
            <input v-model="form.delivery_date" type="date" class="so-input" />
          </div>
          <div class="so-field">
            <label class="so-label">Customer PO #</label>
            <input v-model="form.po_number" type="text" class="so-input" placeholder="Customer's purchase order #" />
          </div>
          <div class="so-field">
            <label class="so-label">Shipping Address</label>
            <input v-model="form.shipping_address" type="text" class="so-input" placeholder="Optional" />
          </div>
        </div>

        <div class="so-section-title">Items</div>
        <div class="so-items-table">
          <div class="so-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="so-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items"
              placeholder="Item…" :createable="true" createDoctype="Item"
              @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="so-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="so-input ta-r" @input="calcLine(line)" /></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="so-input ta-r" @input="calcLine(line)" /></div>
            <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
            <div><button @click="removeLine(line.id)" class="so-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="so-add-line" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <div class="so-totals">
          <div class="so-field" style="max-width:160px">
            <label class="so-label">Tax Rate %</label>
            <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="so-input" />
          </div>
          <div class="so-totals-right">
            <div class="so-total-row"><span>Subtotal</span><span>{{ fmtCur(subtotal) }}</span></div>
            <div class="so-total-row"><span>Tax ({{ form.tax_rate||0 }}%)</span><span>{{ fmtCur(taxAmount) }}</span></div>
            <div class="so-total-row grand"><span>Total</span><span>{{ fmtCur(subtotal+taxAmount) }}</span></div>
          </div>
        </div>

        <div class="so-field">
          <label class="so-label">Terms & Conditions</label>
          <textarea v-model="form.terms" rows="3" class="so-input" placeholder="Optional"></textarea>
        </div>
      </div>
      <div class="so-dfooter">
        <button class="so-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="so-btn-save" :disabled="drawerSaving" @click="saveSO('Draft')">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="so-btn-primary" :disabled="drawerSaving" @click="saveSO('To Deliver')">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Confirm Order' }}
        </button>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="so-overlay" @click.self="viewOpen=false"></div>
    <div class="so-drawer so-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="so-view-head" :style="`background:${headerBg(viewDoc)}`">
          <div>
            <div class="so-view-num">{{ viewDoc.name }}</div>
            <div class="so-view-sub">{{ viewDoc.customer_name||viewDoc.customer }}</div>
          </div>
          <div style="text-align:right">
            <div class="so-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="so-badge so-badge-white">{{ displayStatus(viewDoc) }}</span>
          </div>
          <button class="so-dclose so-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <TimelineStepper :steps="timelineSteps" />

        <div class="so-tabs">
          <button class="so-tab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="so-tab" :class="{active:viewTab==='fulfill'}" @click="viewTab='fulfill'">Fulfillment</button>
          <button class="so-tab" :class="{active:viewTab==='links'}" @click="viewTab='links'">
            Linked<span v-if="links.sales_invoices.length>0" class="so-tab-count">{{ links.sales_invoices.length }}</span>
          </button>
        </div>

        <div class="so-dbody">
          <template v-if="viewTab==='details'">
            <div class="so-meta-grid">
              <div><div class="so-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
              <div><div class="so-meta-lbl">Delivery Date</div>
                <div class="mono-sm" :class="isPastDelivery(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.delivery_date)||'—' }}</div>
              </div>
              <div><div class="so-meta-lbl">Customer PO</div><div class="mono-sm">{{ viewDoc.po_number||'—' }}</div></div>
              <div><div class="so-meta-lbl">From Quote</div><div class="mono-sm">{{ viewDoc.ref_quote||'—' }}</div></div>
            </div>
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="so-section-title">Line Items</div>
              <div class="so-view-items">
                <div class="so-view-items-head"><span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span></div>
                <div v-for="it in viewItems" :key="it.name" class="so-view-items-row">
                  <span><strong>{{ it.item_name||it.item_code }}</strong>
                    <div v-if="it.description" class="text-muted" style="font-size:11px">{{ it.description }}</div></span>
                  <span class="ta-r mono-sm">{{ it.qty }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(it.amount) }}</span>
                </div>
              </div>
            </template>
            <div v-if="viewDoc.terms" class="so-terms">
              <div class="so-meta-lbl">Terms & Conditions</div>
              <div style="white-space:pre-wrap;font-size:12.5px;color:#374151">{{ viewDoc.terms }}</div>
            </div>
          </template>

          <template v-if="viewTab==='fulfill'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="fulfill.lines.length">
              <div style="font-size:12px;color:#6b7280">Status: <strong>{{ fulfill.computed_status }}</strong></div>
              <div class="so-fulfill-tbl">
                <div class="so-fulfill-head">
                  <span>Item</span>
                  <span class="ta-r">Ordered</span>
                  <span class="ta-r">Delivered</span>
                  <span class="ta-r">Invoiced</span>
                  <span class="ta-r">Remaining</span>
                </div>
                <div v-for="l in fulfill.lines" :key="l.name" class="so-fulfill-row">
                  <span>{{ l.item_name||l.item_code }}</span>
                  <span class="ta-r mono-sm">{{ l.qty }}</span>
                  <span class="ta-r mono-sm" :class="l.delivered_qty>=l.qty?'text-success':'text-muted'">{{ l.delivered_qty }}</span>
                  <span class="ta-r mono-sm" :class="l.billed_qty>=l.qty?'text-success':'text-muted'">{{ l.billed_qty }}</span>
                  <span class="ta-r mono-sm text-danger">{{ l.remaining_to_deliver }} / {{ l.remaining_to_bill }}</span>
                </div>
              </div>
              <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px">
                <button v-if="hasUndelivered" class="so-btn-ghost" @click="markAllDelivered" :disabled="actionRunning">📦 Mark All Delivered</button>
              </div>
            </template>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">No line items.</div>
          </template>

          <template v-if="viewTab==='links'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else>
              <div v-if="viewDoc.ref_quote" class="so-section-title">Originating Quote</div>
              <div v-if="viewDoc.ref_quote" class="so-link-row">
                <span class="so-num">{{ viewDoc.ref_quote }}</span>
                <span class="text-muted">Quotation</span>
              </div>
              <div v-if="links.sales_invoices.length" class="so-section-title">Sales Invoices</div>
              <div v-for="si in links.sales_invoices" :key="si.name" class="so-link-row">
                <span class="so-num">{{ si.name }}</span>
                <span class="text-muted">{{ fmtDate(si.posting_date) }}</span>
                <span class="text-muted">Out: {{ fmtCur(si.outstanding_amount) }}</span>
                <span style="text-align:right;font-weight:600">{{ fmtCur(si.grand_total) }}</span>
              </div>
              <div v-if="!viewDoc.ref_quote && !links.sales_invoices.length"
                style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
                No linked documents yet.
              </div>
            </template>
          </template>
        </div>

        <div class="so-dfooter">
          <button class="so-btn-ghost" @click="viewOpen=false">Close</button>
          <button class="so-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button class="so-btn-ghost" @click="emailSO(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="so-btn-ghost" @click="printSO(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="canInvoice(viewDoc)" class="so-btn-primary" @click="openInvoiceModal(viewDoc)">→ Invoice</button>
          <button class="so-btn-danger" @click="cancelSO(viewDoc)">Cancel</button>
          <button class="so-btn-danger" @click="deleteSO(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Convert-to-Invoice modal (partial-qty) ── -->
    <div v-if="invModal.open" class="so-overlay" @click.self="invModal.open=false" style="z-index:60"></div>
    <div v-if="invModal.open" class="so-apply-dialog">
      <div class="so-dheader" style="background:linear-gradient(135deg,#1e3a5f,#1a6ef7);color:#fff;height:auto;padding:14px 18px">
        <div style="color:#fff;font-weight:700">Convert to Invoice — {{ invModal.soName }}</div>
        <button class="so-dclose" style="color:#fff" @click="invModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="so-dbody">
        <div style="font-size:12.5px;color:#374151">Enter the quantity to invoice for each line (defaults to remaining):</div>
        <div class="so-inv-tbl">
          <div class="so-inv-head">
            <span>Item</span><span class="ta-r">Remaining</span><span class="ta-r">Invoice</span>
          </div>
          <div v-for="l in invModal.lines" :key="l.name" class="so-inv-row">
            <span>{{ l.item_name||l.item_code }}</span>
            <span class="ta-r mono-sm text-muted">{{ l.remaining_to_bill }}</span>
            <input v-model.number="l.toInvoice" type="number" min="0" :max="l.remaining_to_bill" step="0.001"
              class="so-input ta-r" style="font-family:monospace;width:90px" />
          </div>
        </div>
        <div class="so-field">
          <label class="so-label">Due Date</label>
          <input v-model="invModal.dueDate" type="date" class="so-input" />
        </div>
        <div style="text-align:right;font-size:13px;color:#6b7280">
          Invoice Total: <strong style="color:#111827">{{ fmtCur(invModalTotal) }}</strong>
        </div>
      </div>
      <div class="so-dfooter">
        <button class="so-btn-ghost" @click="invModal.open=false" :disabled="invModal.saving">Cancel</button>
        <button class="so-btn-primary" :disabled="invModal.saving||invModalTotal<=0" @click="submitInvoice">
          {{ invModal.saving ? 'Creating…' : `Create Invoice ${fmtCur(invModalTotal)}` }}
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
import BulkActionBar from "../components/BulkActionBar.vue";
import TimelineStepper from "../components/TimelineStepper.vue";

const { toast } = useToast();
const { confirm } = useConfirm();
const { printDoc } = useLivePreview();
function printSO(d) { printDoc(d, { title: "SALES ORDER", partyLabel: "Customer", partyField: "customer_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();

const activeTab = ref("all");
const tabs = [
  { key: "all",       label: "All" },
  { key: "draft",     label: "Draft" },
  { key: "toDeliver", label: "To Deliver" },
  { key: "toInvoice", label: "To Invoice" },
  { key: "closed",    label: "Closed" },
  { key: "cancelled", label: "Cancelled" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const viewLoading = ref(false), viewItems = ref([]);
const fulfill = reactive({ lines: [], computed_status: "" });
const links = reactive({ sales_invoices: [], delivery_challans: [] });
const customers = ref([]), items = ref([]), lines = ref([]), taxAccountHead = ref("");
const sortCol = ref("transaction_date"), sortDir = ref("desc");
const actionRunning = ref(false);

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const form = reactive({
  customer: "", transaction_date: todayStr(), delivery_date: deliveryDefault(),
  po_number: "", shipping_address: "", tax_rate: 0, terms: "",
});

const invModal = reactive({ open: false, saving: false, soName: "", lines: [], dueDate: "" });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function deliveryDefault() { const d = new Date(); d.setDate(d.getDate() + 14); return d.toISOString().slice(0, 10); }
function fmtCur(v) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v)); }

function isPastDelivery(o) {
  if (!o?.delivery_date) return false;
  const s = (o.status||"").toLowerCase();
  if (s === "closed" || s === "invoiced" || s === "cancelled") return false;
  return new Date(o.delivery_date) < new Date();
}
function displayStatus(o) {
  const s = o?.status;
  if (!s) return "DRAFT";
  return s.toUpperCase();
}
function badgeClass(o) {
  const s = (o?.status||"").toLowerCase();
  if (!s || s === "draft")  return "so-bdg-grey";
  if (s === "cancelled")    return "so-bdg-red";
  if (s === "closed" || s === "invoiced") return "so-bdg-green";
  if (s.includes("delivered") && !s.includes("partially")) return "so-bdg-blue";
  if (s === "to deliver" || s.includes("partially"))      return "so-bdg-orange";
  return "so-bdg-blue";
}
function headerBg(o) {
  const s = (o?.status||"").toLowerCase();
  if (s === "cancelled") return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  if (s === "closed" || s === "invoiced") return "linear-gradient(135deg,#064e3b,#059669)";
  if (s === "to deliver" || s.includes("partially"))    return "linear-gradient(135deg,#78350f,#d97706)";
  if (s === "delivered") return "linear-gradient(135deg,#1e3a5f,#1a6ef7)";
  return "linear-gradient(135deg,#374151,#6b7280)";
}
function canInvoice(o) {
  const s = (o?.status||"").toLowerCase();
  return s !== "cancelled" && s !== "closed" && s !== "invoiced";
}

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    list.value = await apiList("Sales Order", {
      fields: ["name", "customer", "customer_name", "transaction_date", "delivery_date", "status", "grand_total", "billed_amount", "ref_quote", "po_number"],
      filters: [["company", "=", co]],
      limit: 500,
      order: "transaction_date desc",
    });
  } catch (e) { toast.error(e.message || "Failed to load sales orders"); }
  finally { loading.value = false; }
}
async function loadTaxAccount() {
  try {
    const r = await apiList("Account", { fields: ["name"], filters: [["account_type", "=", "Tax"], ["is_group", "=", 0]], limit: 1 });
    if (r?.length) taxAccountHead.value = r[0].name;
  } catch {}
}

const counts = computed(() => {
  const c = { draft:0, toDeliver:0, toInvoice:0, closed:0, cancelled:0 };
  for (const o of list.value) {
    const s = (o.status||"draft").toLowerCase();
    if (s === "cancelled") c.cancelled++;
    else if (s === "closed" || s === "invoiced") c.closed++;
    else if (s === "draft") c.draft++;
    else if (s === "delivered") c.toInvoice++;
    else c.toDeliver++;   // To Deliver / Partially Delivered / Submitted
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
      if (activeTab.value === "closed")    return s === "closed" || s === "invoiced";
      if (activeTab.value === "toInvoice") return s === "delivered";
      if (activeTab.value === "toDeliver") return s !== "cancelled" && s !== "closed" && s !== "invoiced" && s !== "draft" && s !== "delivered";
      return true;
    });
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.customer_name || x.customer || "").toLowerCase().includes(q)
      || (x.po_number || "").toLowerCase().includes(q));
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

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(o => selected.value.has(o.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(o => o.name)) : new Set(); }

const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const taxAmount = computed(() => Math.round(subtotal.value * flt(form.tax_rate) / 100 * 100) / 100);

const hasUndelivered = computed(() => fulfill.lines.some(l => l.remaining_to_deliver > 0));

const timelineSteps = computed(() => {
  const o = viewDoc.value;
  if (!o) return [];
  const s = (o.status||"").toLowerCase();
  if (s === "cancelled") {
    return [
      { key:"draft", label:"Draft", done:true },
      { key:"sub",   label:"Submitted", done:true },
      { key:"end",   label:"Cancelled", danger:true, current:true },
    ];
  }
  const delivered = s === "delivered" || s === "invoiced" || s === "closed";
  const invoiced  = s === "invoiced"  || s === "closed";
  const closed    = s === "closed";
  return [
    { key:"draft",     label:"Draft",     done:true },
    { key:"submitted", label:"Submitted", done:s!=="draft", current:s==="to deliver"||s==="submitted" },
    { key:"delivered", label:"Delivered", done:delivered, current:s==="delivered" && !invoiced },
    { key:"invoiced",  label:"Invoiced",  done:invoiced, current:invoiced && !closed },
    { key:"closed",    label:"Closed",    done:closed, current:closed },
  ];
});

const invModalTotal = computed(() =>
  (invModal.lines || []).reduce((s, l) => s + flt(l.toInvoice) * flt(l.rate), 0)
);

// ── Create / Edit ─────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { customer: "", transaction_date: todayStr(), delivery_date: deliveryDefault(), po_number: "", shipping_address: "", tax_rate: 0, terms: "" });
  lines.value = [blankLine()];
  fetchCustomers(""); fetchItems("");
  drawerOpen.value = true;
}
async function openEdit(o) {
  editingName.value = o.name;
  Object.assign(form, {
    customer: o.customer || "", transaction_date: o.transaction_date || todayStr(),
    delivery_date: o.delivery_date || deliveryDefault(), po_number: o.po_number || "",
    shipping_address: o.shipping_address || "", tax_rate: 0, terms: o.terms || "",
  });
  lines.value = [blankLine()];
  fetchCustomers(""); fetchItems("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Sales Order", o.name);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || "",
        qty: i.qty || 1, rate: i.rate || 0, amount: i.amount || 0,
      }));
    }
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
  links.sales_invoices = []; links.delivery_challans = [];
  try {
    const [doc, ful, lnk] = await Promise.all([
      apiGet("Sales Order", o.name),
      apiGET("zoho_books_clone.api.docs.get_sales_order_fulfillment", { sales_order: o.name }).catch(() => null),
      apiGET("zoho_books_clone.api.docs.get_sales_order_links", { sales_order: o.name }).catch(() => null),
    ]);
    viewItems.value = doc?.items || [];
    viewDoc.value = { ...o, ...doc };
    if (ful) { fulfill.lines = ful.lines || []; fulfill.computed_status = ful.computed_status || ""; }
    if (lnk) { links.sales_invoices = lnk.sales_invoices || []; }
  } catch {}
  viewLoading.value = false;
}

async function fetchCustomers(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["customer_name", "like", "%" + q + "%"]);
    const r = await apiList("Customer", { fields: ["name", "customer_name"], filters: f, limit: 30, order: "customer_name asc" });
    customers.value = r.map(x => ({ ...x, label: x.customer_name || x.name, value: x.name }));
  } catch { customers.value = []; }
}
async function fetchItems(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["item_name", "like", "%" + q + "%"]);
    const r = await apiList("Item", { fields: ["name", "item_name", "standard_rate", "stock_uom"], filters: f, limit: 30, order: "item_name asc" });
    items.value = r.map(x => ({ ...x, label: x.item_name || x.name, value: x.name, rate: x.standard_rate || 0 }));
  } catch { items.value = []; }
}
function onItemSelect(line, opt) { line.item_code = opt?.value ?? opt; if (opt?.rate) { line.rate = Number(opt.rate) || 0; calcLine(line); } }
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }

async function saveSO(newStatus) {
  if (!form.customer) return toast.error("Customer is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const taxes = form.tax_rate > 0 && taxAccountHead.value
      ? [{ doctype: "Tax Line", charge_type: "On Net Total", account_head: taxAccountHead.value, description: taxAccountHead.value, rate: form.tax_rate }]
      : [];
    const doc = {
      doctype: "Sales Order", company,
      customer: form.customer, transaction_date: form.transaction_date,
      delivery_date: form.delivery_date || null,
      po_number: form.po_number || "",
      shipping_address: form.shipping_address || "",
      status: newStatus || "Draft",
      terms: form.terms || "",
      items: lines.value.filter(l => l.item_code).map(l => ({
        doctype: "Sales Order Item", item_code: l.item_code,
        description: l.description || l.item_code,
        qty: flt(l.qty) || 1, rate: flt(l.rate), amount: flt(l.amount),
      })),
      taxes,
    };
    if (editingName.value) doc.name = editingName.value;
    const saved = await apiSave(doc);
    toast.success(`Sales Order ${saved?.name || ""} saved`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save order"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailSO(o) {
  await openEmail({
    doctype: "Sales Order", name: o.name, docLabel: `Sales Order ${o.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_sales_order_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_sales_order_email",
    paramKey: "sales_order",
  });
}

function openInvoiceModal(o) {
  // Fetch fresh fulfillment to ensure we have remaining_to_bill
  apiGET("zoho_books_clone.api.docs.get_sales_order_fulfillment", { sales_order: o.name })
    .then(r => {
      const ful = r?.lines || [];
      Object.assign(invModal, {
        open: true, saving: false, soName: o.name,
        lines: ful.filter(l => l.remaining_to_bill > 0)
                  .map(l => ({ ...l, toInvoice: l.remaining_to_bill })),
        dueDate: o.delivery_date || todayStr(),
      });
      if (!invModal.lines.length) { invModal.open = false; toast.info("Nothing left to invoice"); }
    })
    .catch(e => toast.error(e.message || "Failed to load fulfillment"));
}
async function submitInvoice() {
  const lineMap = {};
  for (const l of invModal.lines) {
    if (flt(l.toInvoice) > 0) lineMap[l.name] = flt(l.toInvoice);
  }
  if (!Object.keys(lineMap).length) { toast.error("Enter at least one qty to invoice"); return; }
  invModal.saving = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.docs.convert_sales_order_to_invoice", {
      sales_order: invModal.soName,
      line_qtys: JSON.stringify(lineMap),
      due_date: invModal.dueDate || "",
    });
    toast.success(`Invoice created: ${r?.sales_invoice}`);
    invModal.open = false;
    await load();
    if (viewDoc.value?.name === invModal.soName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Convert failed"); }
  invModal.saving = false;
}

async function markAllDelivered() {
  actionRunning.value = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.docs.mark_so_delivered", { sales_order: viewDoc.value.name });
    toast.success(`Marked ${r?.lines_updated || 0} line(s) delivered`);
    await load();
    if (viewDoc.value) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Mark delivered failed"); }
  actionRunning.value = false;
}

async function cancelSO(o) {
  if (!await confirm({ title: "Cancel Sales Order", body: `Cancel ${o.name}? Linked invoices must be cancelled separately.`, okLabel: "Cancel SO" })) return;
  try {
    await apiPOST("zoho_books_clone.api.docs.cancel_sales_order_safe", { sales_order: o.name });
    toast.success("Sales Order cancelled");
    await load(); if (viewDoc.value?.name === o.name) await openView(o);
  } catch (e) { toast.error(e.message || "Cancel failed"); }
}
async function deleteSO(o) {
  if (!await confirm({ title: "Delete Sales Order", body: `Permanently delete ${o.name}?`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Sales Order", o.name);
    toast.success("Sales Order deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk actions ──────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(o => selected.value.has(o.name) && (!o.status || o.status === "Draft"));
  if (!drafts.length) { toast.info("Select drafts to delete"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft order(s)?`, okLabel: "Delete" })) return;
  for (const o of drafts) { try { await apiDelete("Sales Order", o.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length}`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(o => selected.value.has(o.name));
  if (!subs.length) { toast.info("No orders selected"); return; }
  let sent = 0;
  for (const o of subs) {
    const ok = await openEmail({
      doctype: "Sales Order", name: o.name, docLabel: `Sales Order ${o.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_sales_order_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_sales_order_email",
      paramKey: "sales_order",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} order(s)`);
}

function exportCSV() {
  const rows = sorted.value;
  const head = ["Order #","Customer","Date","Delivery","Status","PO #","Amount"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const o of rows) {
    out.push([o.name, o.customer_name || o.customer, o.transaction_date, o.delivery_date || "",
      o.status || "Draft", o.po_number || "", Number(o.grand_total || 0).toFixed(2)].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `sales_orders_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} order(s)`);
}

onMounted(() => { load(); loadTaxAccount(); });
</script>

<style scoped>
.so-page { display: flex; flex-direction: column; gap: 16px; padding: 24px; }
.so-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.so-search-wrap { display: flex; align-items: center; gap: 8px; background: #f3f4f6; border-radius: 8px; padding: 6px 12px; min-width: 220px; }
.so-search-input { border: none; background: transparent; outline: none; font: inherit; color: #111827; width: 100%; font-size: 13px; }
.so-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.so-pill { padding: 6px 14px; border-radius: 20px; font-size: 12.5px; font-weight: 600; border: 1px solid #e5e7eb; background: #fff; color: #6b7280; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 6px; }
.so-pill:hover { color: #2563eb; border-color: #2563eb; }
.so-pill.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.so-pill-count { background: #f3f4f6; color: #6b7280; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.so-pill.active .so-pill-count { background: #2563eb; color: #fff; }
.so-btn-primary { display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.so-btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.so-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.so-btn-ghost { display: inline-flex; align-items: center; gap: 6px; background: transparent; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #374151; cursor: pointer; }
.so-btn-ghost:hover { background: #f9fafb; }
.so-btn-save { display: inline-flex; align-items: center; gap: 6px; background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.so-btn-save:hover { background: #dcfce7; }
.so-btn-save:disabled { opacity: .5; cursor: not-allowed; }
.so-btn-danger { display: inline-flex; align-items: center; gap: 6px; background: #fef2f2; border: 1px solid #dc2626; color: #dc2626; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.so-btn-danger:hover { background: #fee2e2; }

.so-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; }
.so-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.so-table th { background: #f9fafb; border-bottom: 1px solid #e5e7eb; padding: 10px 12px; font-size: 11.5px; font-weight: 600; color: #374151; text-align: left; white-space: nowrap; }
.so-table th.sortable { cursor: pointer; user-select: none; }
.so-table th.sortable:hover { color: #2563eb; }
.ta-r { text-align: right !important; }
.so-row td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; cursor: pointer; }
.so-row:last-child td { border-bottom: none; }
.so-row:hover td { background: #f9fafb; }
.so-row.selected td { background: #eff6ff; }
.so-num { font-family: monospace; font-size: 12.5px; color: #2563eb; font-weight: 600; }
.mono-sm { font-family: monospace; font-size: 12.5px; }
.text-muted { color: #6b7280; }
.text-danger { color: #dc2626; }
.text-success { color: #059669; }
.so-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 10px; font-size: 11.5px; font-weight: 600; }
.so-bdg-grey   { background: #f3f4f6; color: #6b7280; }
.so-bdg-blue   { background: #dbeafe; color: #1a6ef7; }
.so-bdg-green  { background: #d1fae5; color: #059669; }
.so-bdg-orange { background: #fef3c7; color: #d97706; }
.so-bdg-red    { background: #fee2e2; color: #dc2626; }
.so-badge-white { background: rgba(255,255,255,.2); color: #fff !important; border: 1px solid rgba(255,255,255,.4); }
.so-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.so-act-btn { background: transparent; border: 1px solid #e5e7eb; border-radius: 6px; width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #6b7280; }
.so-act-btn:hover { background: #f3f4f6; color: #2563eb; }
.so-act-conv { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.so-act-conv:hover { background: #dbeafe; }
.so-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.so-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }
.so-shimmer { height: 13px; background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%); border-radius: 4px; animation: shimmer 1.2s infinite; background-size: 200% 100%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

.so-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.2); z-index: 40; }
.so-drawer { position: fixed; top: 0; right: -600px; bottom: 0; width: 600px; max-width: 96vw; background: #fff; border-left: 1px solid #e5e7eb; box-shadow: -8px 0 24px rgba(0,0,0,.08); z-index: 50; display: flex; flex-direction: column; transition: right .22s ease; }
.so-drawer.open { right: 0; }
.so-view-drawer { width: 540px; right: -540px; }
.so-view-drawer.open { right: 0; }
.so-dheader { display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 60px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; }
.so-dheader-title { font-size: 15px; font-weight: 600; color: #111827; }
.so-dclose { background: transparent; border: none; cursor: pointer; color: #6b7280; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; }
.so-dclose:hover { background: #f3f4f6; color: #111827; }
.so-dbody { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.so-fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.so-field { display: flex; flex-direction: column; gap: 4px; }
.so-label { font-size: 12px; font-weight: 600; color: #374151; }
.req { color: #dc2626; }
.so-input { width: 100%; box-sizing: border-box; border: 1px solid #e5e7eb; border-radius: 6px; padding: 7px 10px; font: inherit; font-size: 13px; outline: none; background: #fff; color: #111827; }
.so-input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.08); }
textarea.so-input { resize: vertical; }
.so-section-title { font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: .05em; padding-bottom: 4px; border-bottom: 1px solid #f3f4f6; }
.so-items-table { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.so-items-head { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #374151; }
.so-items-row { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; }
.so-add-line { background: transparent; border: none; color: #2563eb; font-size: 12.5px; font-weight: 600; cursor: pointer; padding: 8px 12px; display: inline-flex; align-items: center; gap: 6px; }
.so-add-line:hover { background: #eff6ff; }
.so-rm-line { background: transparent; border: 1px solid #e5e7eb; border-radius: 4px; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #9ca3af; }
.so-rm-line:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.so-totals { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.so-totals-right { display: flex; flex-direction: column; gap: 4px; min-width: 220px; }
.so-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 3px 0; }
.so-total-row.grand { font-weight: 700; font-size: 14px; color: #111827; border-top: 1px solid #e5e7eb; padding-top: 6px; }

.so-view-head { position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 20px; flex-shrink: 0; color: #fff; }
.so-view-num { font-size: 18px; font-weight: 700; font-family: monospace; color: #fff; }
.so-view-sub { font-size: 13px; color: rgba(255,255,255,.8); margin-top: 2px; }
.so-view-amount { font-size: 22px; font-weight: 800; font-family: monospace; color: #fff; }
.so-vclose { position: absolute; top: 12px; right: 12px; color: #fff; }
.so-vclose:hover { background: rgba(255,255,255,.18); color: #fff; }
.so-tabs { display: flex; gap: 4px; padding: 0 20px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; background: #fff; }
.so-tab { background: transparent; border: none; padding: 10px 14px; font: inherit; font-size: 12.5px; font-weight: 600; color: #6b7280; cursor: pointer; border-bottom: 2px solid transparent; display: inline-flex; align-items: center; gap: 6px; }
.so-tab:hover { color: #2563eb; }
.so-tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.so-tab-count { background: #2563eb; color: #fff; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.so-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.so-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }
.so-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.so-view-items-head { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.so-view-items-row { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.so-terms { padding: 10px 12px; background: #f8fafc; border-radius: 6px; }
.so-link-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 12.5px; align-items: center; }
.so-fulfill-tbl { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.so-fulfill-head { display: grid; grid-template-columns: 2fr 80px 100px 90px 110px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.so-fulfill-row { display: grid; grid-template-columns: 2fr 80px 100px 90px 110px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.so-dfooter { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #e5e7eb; flex-shrink: 0; flex-wrap: wrap; }

.so-apply-dialog { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 540px; max-width: 96vw; background: #fff; border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.2); z-index: 70; display: flex; flex-direction: column; overflow: hidden; }
.so-inv-tbl { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.so-inv-head { display: grid; grid-template-columns: 2fr 100px 110px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.so-inv-row { display: grid; grid-template-columns: 2fr 100px 110px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
</style>
