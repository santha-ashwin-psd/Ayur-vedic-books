<template>
  <div class="qt-page">

    <!-- ── Toolbar ── -->
    <div class="qt-actions">
      <div class="qt-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search quotes, customers…" class="qt-search-input" />
      </div>
      <div class="qt-pills">
        <button v-for="t in tabs" :key="t.key"
          class="qt-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">
          {{ t.label }}
          <span v-if="t.key!=='all'" class="qt-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="qt-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="qt-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="qt-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Quotation
        </button>
      </div>
    </div>

    <!-- ── Summary strip ── -->
    <SummaryStrip :cards="[
      { label: 'Total Quotes', value: list.length },
      { label: 'Sent',     value: counts.sent,     accent: '#1a6ef7' },
      { label: 'Accepted', value: counts.accepted, accent: '#16a34a' },
      { label: 'Expired',  value: counts.expired,  accent: '#dc2626' },
    ]" />

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button @click="bulkMarkSent">Mark as Sent</button>
      <button @click="bulkMarkExpired">Mark Expired</button>
      <button class="bab-danger" @click="bulkDelete">Delete Drafts</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="qt-card">
      <table class="qt-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">Quote # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('customer_name')" class="sortable">Customer <span v-html="sortArrow('customer_name')"></span></th>
            <th @click="sortBy('transaction_date')" class="sortable">Date <span v-html="sortArrow('transaction_date')"></span></th>
            <th @click="sortBy('valid_till')" class="sortable">Valid Till <span v-html="sortArrow('valid_till')"></span></th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="8"><div class="qt-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="q in sorted" :key="q.name" class="qt-row" :class="{selected:selected.has(q.name)}">
              <td><input type="checkbox" :checked="selected.has(q.name)" @change="toggle(q.name)" /></td>
              <td @click="openView(q)"><span class="qt-num">{{ q.name }}</span></td>
              <td @click="openView(q)">{{ q.customer_name || q.customer || '—' }}</td>
              <td @click="openView(q)" class="text-muted mono-sm">{{ fmtDate(q.transaction_date) }}</td>
              <td @click="openView(q)" :class="isExpired(q)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(q.valid_till)||'—' }}</td>
              <td @click="openView(q)"><span class="qt-badge" :class="badgeClass(q)">{{ displayStatus(q) }}</span></td>
              <td @click="openView(q)" class="ta-r mono-sm">{{ fmtCur(q.grand_total) }}</td>
              <td class="qt-act-cell">
                <button class="qt-act-btn" @click="openView(q)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button class="qt-act-btn" @click="openEdit(q)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button class="qt-act-btn qt-act-conv" v-if="canConvert(q)" @click="openConvertModal(q)" title="Convert"><span v-html="icon('arrow-right',13)"></span></button>
                <button class="qt-act-btn qt-act-del" @click="deleteQT(q)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="qt-empty">No quotations match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Create / Edit Drawer ── -->
    <div v-if="drawerOpen" class="qt-overlay" @click.self="drawerOpen=false"></div>
    <div class="qt-drawer" :class="{open:drawerOpen}">
      <div class="qt-dheader">
        <div class="qt-dheader-title">{{ editingName ? 'Edit Quotation' : 'New Quotation' }}</div>
        <button class="qt-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="qt-dbody">
        <div class="qt-fields-grid">
          <div class="qt-field" style="grid-column:1/-1">
            <label class="qt-label">Customer <span class="req">*</span></label>
            <SearchableSelect v-model="form.customer" :options="customers" placeholder="Select customer…"
              :createable="true" createDoctype="Customer"
              @search="fetchCustomers" />
          </div>
          <div class="qt-field">
            <label class="qt-label">Date <span class="req">*</span></label>
            <input v-model="form.transaction_date" type="date" class="qt-input" />
          </div>
          <div class="qt-field">
            <label class="qt-label">Valid Till</label>
            <input v-model="form.valid_till" type="date" class="qt-input" />
          </div>
          <div class="qt-field" style="grid-column:1/-1">
            <label class="qt-label">Title</label>
            <input v-model="form.title" type="text" class="qt-input" placeholder="Project name or short description" />
          </div>
        </div>

        <div class="qt-section-title">Items</div>
        <div class="qt-items-table">
          <div class="qt-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="qt-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items"
              placeholder="Item…" :createable="true" createDoctype="Item"
              @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="qt-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="qt-input ta-r" @input="calcLine(line)" /></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="qt-input ta-r" @input="calcLine(line)" /></div>
            <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
            <div><button @click="removeLine(line.id)" class="qt-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="qt-add-line" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <div class="qt-totals">
          <div class="qt-field" style="max-width:160px">
            <label class="qt-label">Tax Rate %</label>
            <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="qt-input" />
          </div>
          <div class="qt-totals-right">
            <div class="qt-total-row"><span>Subtotal</span><span>{{ fmtCur(subtotal) }}</span></div>
            <div class="qt-total-row"><span>Tax ({{ form.tax_rate||0 }}%)</span><span>{{ fmtCur(taxAmount) }}</span></div>
            <div class="qt-total-row grand"><span>Total</span><span>{{ fmtCur(subtotal+taxAmount) }}</span></div>
          </div>
        </div>

        <div class="qt-field">
          <label class="qt-label">Terms & Conditions</label>
          <textarea v-model="form.terms" rows="3" class="qt-input" placeholder="Payment terms, delivery terms, validity, etc."></textarea>
        </div>
      </div>
      <div class="qt-dfooter">
        <button class="qt-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="qt-btn-save" :disabled="drawerSaving" @click="saveQT('Draft')">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="qt-btn-primary" :disabled="drawerSaving" @click="saveQT('Sent')">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Save & Mark Sent' }}
        </button>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="qt-overlay" @click.self="viewOpen=false"></div>
    <div class="qt-drawer qt-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="qt-view-head" :style="`background:${headerBg(viewDoc)}`">
          <div>
            <div class="qt-view-num">{{ viewDoc.name }}</div>
            <div class="qt-view-sub">{{ viewDoc.customer_name||viewDoc.customer }}</div>
          </div>
          <div style="text-align:right">
            <div class="qt-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="qt-badge qt-badge-white">{{ displayStatus(viewDoc) }}</span>
          </div>
          <button class="qt-dclose qt-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <TimelineStepper :steps="timelineSteps" />

        <div class="qt-tabs">
          <button class="qt-tab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="qt-tab" :class="{active:viewTab==='conversions'}" @click="viewTab='conversions'">
            Conversions<span v-if="(conv.sales_orders.length+conv.sales_invoices.length)>0" class="qt-tab-count">{{ conv.sales_orders.length + conv.sales_invoices.length }}</span>
          </button>
        </div>

        <div class="qt-dbody">
          <template v-if="viewTab==='details'">
            <div class="qt-meta-grid">
              <div><div class="qt-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
              <div><div class="qt-meta-lbl">Valid Till</div>
                <div class="mono-sm" :class="isExpired(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.valid_till)||'—' }}</div>
              </div>
              <div><div class="qt-meta-lbl">Status</div><div class="mono-sm">{{ displayStatus(viewDoc) }}</div></div>
              <div><div class="qt-meta-lbl">Title</div><div>{{ viewDoc.title||'—' }}</div></div>
            </div>

            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="qt-section-title">Line Items</div>
              <div class="qt-view-items">
                <div class="qt-view-items-head"><span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span></div>
                <div v-for="it in viewItems" :key="it.name" class="qt-view-items-row">
                  <span><strong>{{ it.item_name||it.item_code }}</strong>
                    <div v-if="it.description" class="text-muted" style="font-size:11px">{{ it.description }}</div></span>
                  <span class="ta-r mono-sm">{{ it.qty }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(it.amount) }}</span>
                </div>
              </div>
            </template>
            <div v-if="viewDoc.terms" class="qt-terms">
              <div class="qt-meta-lbl">Terms & Conditions</div>
              <div style="white-space:pre-wrap;font-size:12.5px;color:#374151">{{ viewDoc.terms }}</div>
            </div>
          </template>

          <template v-if="viewTab==='conversions'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else>
              <div v-if="conv.sales_orders.length" class="qt-section-title">Sales Orders</div>
              <div v-for="so in conv.sales_orders" :key="so.name" class="qt-conv-row">
                <span class="qt-num">{{ so.name }}</span>
                <span class="text-muted">{{ fmtDate(so.transaction_date) }}</span>
                <span style="text-align:right;font-weight:600">{{ fmtCur(so.grand_total) }}</span>
              </div>
              <div v-if="conv.sales_invoices.length" class="qt-section-title">Sales Invoices</div>
              <div v-for="si in conv.sales_invoices" :key="si.name" class="qt-conv-row">
                <span class="qt-num">{{ si.name }}</span>
                <span class="text-muted">{{ fmtDate(si.posting_date) }}</span>
                <span style="text-align:right;font-weight:600">{{ fmtCur(si.grand_total) }}</span>
              </div>
              <div v-if="!conv.sales_orders.length && !conv.sales_invoices.length"
                style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
                Not converted yet.
                <div v-if="canConvert(viewDoc)" style="margin-top:8px">
                  <button class="qt-btn-primary" @click="openConvertModal(viewDoc)" style="font-size:12px;padding:6px 12px">Convert →</button>
                </div>
              </div>
            </template>
          </template>
        </div>

        <div class="qt-dfooter">
          <button class="qt-btn-ghost" @click="viewOpen=false">Close</button>
          <button class="qt-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button class="qt-btn-ghost" @click="emailQT(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="qt-btn-ghost" @click="printQT(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="viewDoc.status!=='Accepted' && viewDoc.status!=='Converted'" class="qt-btn-ghost" @click="markStatus(viewDoc,'Accepted')">✓ Accept</button>
          <button v-if="viewDoc.status!=='Declined' && viewDoc.status!=='Converted'" class="qt-btn-ghost" @click="markStatus(viewDoc,'Declined')">✕ Decline</button>
          <button v-if="canConvert(viewDoc)" class="qt-btn-primary" @click="openConvertModal(viewDoc)">Convert →</button>
          <button class="qt-btn-danger" @click="deleteQT(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Convert modal ── -->
    <div v-if="convertModal.open" class="qt-overlay" @click.self="convertModal.open=false" style="z-index:60"></div>
    <div v-if="convertModal.open" class="qt-apply-dialog">
      <div class="qt-dheader" style="background:linear-gradient(135deg,#1e3a5f,#1a6ef7);color:#fff;height:auto;padding:14px 18px">
        <div style="color:#fff;font-weight:700">Convert Quotation — {{ convertModal.qtName }}</div>
        <button class="qt-dclose" style="color:#fff" @click="convertModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="qt-dbody">
        <div style="font-size:13px;color:#374151;margin-bottom:8px">Choose how to convert this quote:</div>
        <div class="qt-convert-options">
          <button class="qt-convert-card" @click="convertModal.target='SO'" :class="{active:convertModal.target==='SO'}">
            <div class="qt-convert-icon" style="background:#dcfce7;color:#16a34a">SO</div>
            <div>
              <div style="font-weight:700">Sales Order</div>
              <div style="font-size:11.5px;color:#6b7280">Track fulfillment + delivery separately</div>
            </div>
          </button>
          <button class="qt-convert-card" @click="convertModal.target='Invoice'" :class="{active:convertModal.target==='Invoice'}">
            <div class="qt-convert-icon" style="background:#dbeafe;color:#1a6ef7">$</div>
            <div>
              <div style="font-weight:700">Sales Invoice</div>
              <div style="font-size:11.5px;color:#6b7280">Bill the customer immediately</div>
            </div>
          </button>
        </div>
        <div v-if="convertModal.target==='SO'" class="qt-field" style="margin-top:12px">
          <label class="qt-label">Delivery Date</label>
          <input v-model="convertModal.deliveryDate" type="date" class="qt-input" />
        </div>
        <div v-if="convertModal.target==='Invoice'" class="qt-field" style="margin-top:12px">
          <label class="qt-label">Due Date</label>
          <input v-model="convertModal.dueDate" type="date" class="qt-input" />
        </div>
      </div>
      <div class="qt-dfooter">
        <button class="qt-btn-ghost" @click="convertModal.open=false" :disabled="convertModal.saving">Cancel</button>
        <button class="qt-btn-primary" :disabled="convertModal.saving||!convertModal.target" @click="submitConvert">
          {{ convertModal.saving ? 'Converting…' : (convertModal.target ? `Convert to ${convertModal.target==='SO' ? 'Sales Order' : 'Invoice'}` : 'Choose target') }}
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
function printQT(d) { printDoc(d, { title: "QUOTATION", partyLabel: "Customer", partyField: "customer_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();

const activeTab = ref("all");
const tabs = [
  { key: "all",       label: "All" },
  { key: "draft",     label: "Draft" },
  { key: "sent",      label: "Sent" },
  { key: "accepted",  label: "Accepted" },
  { key: "declined",  label: "Declined" },
  { key: "expired",   label: "Expired" },
  { key: "converted", label: "Converted" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const viewLoading = ref(false), viewItems = ref([]);
const conv = reactive({ sales_orders: [], sales_invoices: [] });
const customers = ref([]), items = ref([]), lines = ref([]), taxAccountHead = ref("");
const sortCol = ref("transaction_date"), sortDir = ref("desc");

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const form = reactive({
  customer: "", transaction_date: todayStr(), valid_till: validTillDefault(),
  title: "", tax_rate: 0, terms: "",
});

const convertModal = reactive({ open: false, saving: false, qtName: "", target: "", deliveryDate: "", dueDate: "" });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function validTillDefault() { const d = new Date(); d.setDate(d.getDate() + 30); return d.toISOString().slice(0, 10); }
function fmtCur(v) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v)); }

function isExpired(q) {
  if (!q?.valid_till) return false;
  if (q.status === "Converted" || q.status === "Accepted") return false;
  return new Date(q.valid_till) < new Date();
}
function effectiveStatus(q) {
  if (q?.status === "Converted" || q?.status === "Accepted"
      || q?.status === "Declined" || q?.status === "Lost") return q.status;
  if (isExpired(q)) return "Expired";
  return q?.status || "Draft";
}
function displayStatus(q) { return effectiveStatus(q).toUpperCase(); }
function badgeClass(q) {
  const s = effectiveStatus(q);
  if (s === "Draft")     return "qt-bdg-grey";
  if (s === "Sent")      return "qt-bdg-blue";
  if (s === "Accepted")  return "qt-bdg-green";
  if (s === "Converted") return "qt-bdg-purple";
  if (s === "Declined" || s === "Lost") return "qt-bdg-red";
  if (s === "Expired")   return "qt-bdg-red";
  return "qt-bdg-grey";
}
function headerBg(q) {
  const s = effectiveStatus(q);
  if (s === "Converted") return "linear-gradient(135deg,#581c87,#a855f7)";
  if (s === "Accepted")  return "linear-gradient(135deg,#064e3b,#059669)";
  if (s === "Declined" || s === "Lost" || s === "Expired") return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  if (s === "Sent")      return "linear-gradient(135deg,#1e3a5f,#1a6ef7)";
  return "linear-gradient(135deg,#374151,#6b7280)";
}
function canConvert(q) {
  const s = effectiveStatus(q);
  return s !== "Converted" && s !== "Declined" && s !== "Lost";
}

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    list.value = await apiList("Quotation", {
      fields: ["name", "customer", "customer_name", "transaction_date", "valid_till", "status", "grand_total", "title"],
      filters: [["company", "=", co]],
      limit: 500,
      order: "transaction_date desc",
    });
  } catch (e) { toast.error(e.message || "Failed to load quotations"); }
  finally { loading.value = false; }
}
async function loadTaxAccount() {
  try {
    const r = await apiList("Account", { fields: ["name"], filters: [["account_type", "=", "Tax"], ["is_group", "=", 0]], limit: 1 });
    if (r?.length) taxAccountHead.value = r[0].name;
  } catch {}
}

const counts = computed(() => {
  const c = { draft:0, sent:0, accepted:0, declined:0, expired:0, converted:0 };
  for (const q of list.value) {
    const s = effectiveStatus(q).toLowerCase();
    if (s === "draft")     c.draft++;
    else if (s === "sent") c.sent++;
    else if (s === "accepted") c.accepted++;
    else if (s === "converted") c.converted++;
    else if (s === "declined" || s === "lost") c.declined++;
    else if (s === "expired") c.expired++;
  }
  return c;
});

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") {
    r = r.filter(q => {
      const s = effectiveStatus(q).toLowerCase();
      if (activeTab.value === "declined") return s === "declined" || s === "lost";
      return s === activeTab.value;
    });
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.customer_name || x.customer || "").toLowerCase().includes(q)
      || (x.title || "").toLowerCase().includes(q));
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

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(q => selected.value.has(q.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(q => q.name)) : new Set(); }

const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const taxAmount = computed(() => Math.round(subtotal.value * flt(form.tax_rate) / 100 * 100) / 100);

const timelineSteps = computed(() => {
  const q = viewDoc.value;
  if (!q) return [];
  const s = effectiveStatus(q);
  if (s === "Declined" || s === "Lost") {
    return [
      { key:"draft", label:"Draft", done:true },
      { key:"sent",  label:"Sent",  done:true },
      { key:"end",   label:"Declined", danger:true, current:true },
    ];
  }
  if (s === "Expired") {
    return [
      { key:"draft", label:"Draft", done:true },
      { key:"sent",  label:"Sent",  done:true },
      { key:"end",   label:"Expired", danger:true, current:true },
    ];
  }
  return [
    { key:"draft",     label:"Draft",     done:true },
    { key:"sent",      label:"Sent",      done: s !== "Draft", current: s === "Sent" },
    { key:"accepted",  label:"Accepted",  done: s === "Accepted" || s === "Converted", current: s === "Accepted" },
    { key:"converted", label:"Converted", done: s === "Converted", current: s === "Converted" },
  ];
});

// ── Create / Edit ─────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { customer: "", transaction_date: todayStr(), valid_till: validTillDefault(), title: "", tax_rate: 0, terms: "" });
  lines.value = [blankLine()];
  fetchCustomers(""); fetchItems("");
  drawerOpen.value = true;
}
async function openEdit(q) {
  editingName.value = q.name;
  Object.assign(form, {
    customer: q.customer || "", transaction_date: q.transaction_date || todayStr(),
    valid_till: q.valid_till || validTillDefault(), title: q.title || "",
    tax_rate: 0, terms: q.terms || "",
  });
  lines.value = [blankLine()];
  fetchCustomers(""); fetchItems("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Quotation", q.name);
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
async function openView(q) {
  viewDoc.value = q;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  conv.sales_orders = [];
  conv.sales_invoices = [];
  try {
    const [doc, convData] = await Promise.all([
      apiGet("Quotation", q.name),
      apiGET("zoho_books_clone.api.docs.get_quote_conversions", { quotation_name: q.name }).catch(() => null),
    ]);
    viewItems.value = doc?.items || [];
    viewDoc.value = { ...q, ...doc };
    if (convData) {
      conv.sales_orders = convData.sales_orders || [];
      conv.sales_invoices = convData.sales_invoices || [];
    }
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

async function saveQT(newStatus) {
  if (!form.customer) return toast.error("Customer is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const taxes = form.tax_rate > 0 && taxAccountHead.value
      ? [{ doctype: "Tax Line", charge_type: "On Net Total", account_head: taxAccountHead.value, description: taxAccountHead.value, rate: form.tax_rate }]
      : [];
    const doc = {
      doctype: "Quotation", company,
      customer: form.customer, transaction_date: form.transaction_date,
      valid_till: form.valid_till || null, title: form.title || "",
      status: newStatus || "Draft", terms: form.terms || "",
      items: lines.value.filter(l => l.item_code).map(l => ({
        doctype: "Quotation Item", item_code: l.item_code,
        description: l.description || l.item_code,
        qty: flt(l.qty) || 1, rate: flt(l.rate), amount: flt(l.amount),
      })),
      taxes,
    };
    if (editingName.value) doc.name = editingName.value;
    const saved = await apiSave(doc);
    toast.success(`Quotation ${saved?.name || ""} saved`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save quotation"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailQT(q) {
  const ok = await openEmail({
    doctype: "Quotation", name: q.name, docLabel: `Quotation ${q.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_quote_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_quote_email",
    paramKey: "quotation_name",
  });
  if (ok) await load();
}

async function markStatus(q, status) {
  const epMap = { "Sent":"mark_quote_sent", "Accepted":"mark_quote_accepted", "Declined":"mark_quote_declined" };
  const ep = epMap[status];
  if (!ep) return;
  try {
    await apiPOST(`zoho_books_clone.api.docs.${ep}`, { quotation_name: q.name });
    toast.success(`Marked ${status}`);
    await load();
    if (viewDoc.value?.name === q.name) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Update failed"); }
}

function openConvertModal(q) {
  Object.assign(convertModal, {
    open: true, saving: false, qtName: q.name,
    target: "", deliveryDate: q.valid_till || todayStr(), dueDate: todayStr(),
  });
}
async function submitConvert() {
  if (!convertModal.target) return;
  convertModal.saving = true;
  try {
    const ep = convertModal.target === "SO"
      ? "zoho_books_clone.api.docs.convert_quote_to_sales_order"
      : "zoho_books_clone.api.docs.convert_quote_to_invoice";
    const payload = { quotation_name: convertModal.qtName };
    if (convertModal.target === "SO" && convertModal.deliveryDate) payload.delivery_date = convertModal.deliveryDate;
    if (convertModal.target === "Invoice" && convertModal.dueDate)  payload.due_date = convertModal.dueDate;
    const r = await apiPOST(ep, payload);
    const created = r?.sales_order || r?.sales_invoice;
    toast.success(`Converted → ${convertModal.target === "SO" ? "Sales Order" : "Invoice"}: ${created}`);
    convertModal.open = false;
    await load();
    if (viewDoc.value?.name === convertModal.qtName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Convert failed"); }
  convertModal.saving = false;
}

async function deleteQT(q) {
  if (!await confirm({ title: "Delete Quotation", body: `Permanently delete ${q.name}?`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Quotation", q.name);
    toast.success("Quotation deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk actions ──────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(q => selected.value.has(q.name) && (q.status === "Draft" || !q.status));
  if (!drafts.length) { toast.info("No draft quotations selected"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft quotation(s)?`, okLabel: "Delete" })) return;
  for (const q of drafts) { try { await apiDelete("Quotation", q.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length} draft(s)`);
  await load();
}
async function bulkMarkSent() {
  const targets = sorted.value.filter(q => selected.value.has(q.name) && effectiveStatus(q) === "Draft");
  if (!targets.length) { toast.info("Select drafts to mark as sent"); return; }
  let done = 0;
  for (const q of targets) {
    try { await apiPOST("zoho_books_clone.api.docs.mark_quote_sent", { quotation_name: q.name }); done++; } catch {}
  }
  selected.value = new Set();
  toast.success(`Marked ${done} quote(s) as Sent`);
  await load();
}
async function bulkMarkExpired() {
  const targets = sorted.value.filter(q => selected.value.has(q.name));
  if (!targets.length) { toast.info("No quotes selected"); return; }
  try {
    await apiPOST("zoho_books_clone.api.docs.mark_quote_expired_bulk",
      { quotation_names: JSON.stringify(targets.map(q => q.name)) });
    selected.value = new Set();
    toast.success(`Marked ${targets.length} quote(s) as Expired`);
    await load();
  } catch (e) { toast.error(e.message || "Bulk expire failed"); }
}
async function bulkEmail() {
  const subs = sorted.value.filter(q => selected.value.has(q.name));
  if (!subs.length) { toast.info("No quotes selected"); return; }
  let sent = 0;
  for (const q of subs) {
    const ok = await openEmail({
      doctype: "Quotation", name: q.name, docLabel: `Quotation ${q.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_quote_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_quote_email",
      paramKey: "quotation_name",
    });
    if (ok) sent++;
  }
  if (sent) { toast.success(`Emailed ${sent} quote(s)`); await load(); }
}

function exportCSV() {
  const rows = sorted.value;
  const head = ["Quote #","Customer","Date","Valid Till","Status","Amount"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const q of rows) {
    out.push([q.name, q.customer_name || q.customer, q.transaction_date, q.valid_till || "",
      effectiveStatus(q), Number(q.grand_total || 0).toFixed(2)].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `quotations_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} quote(s)`);
}

onMounted(() => { load(); loadTaxAccount(); });
</script>

<style scoped>
.qt-page { display: flex; flex-direction: column; gap: 16px; padding: 24px; }
.qt-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.qt-search-wrap { display: flex; align-items: center; gap: 8px; background: #f3f4f6; border-radius: 8px; padding: 6px 12px; min-width: 220px; }
.qt-search-input { border: none; background: transparent; outline: none; font: inherit; color: #111827; width: 100%; font-size: 13px; }
.qt-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.qt-pill { padding: 6px 14px; border-radius: 20px; font-size: 12.5px; font-weight: 600; border: 1px solid #e5e7eb; background: #fff; color: #6b7280; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 6px; }
.qt-pill:hover { color: #2563eb; border-color: #2563eb; }
.qt-pill.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.qt-pill-count { background: #f3f4f6; color: #6b7280; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.qt-pill.active .qt-pill-count { background: #2563eb; color: #fff; }
.qt-btn-primary { display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.qt-btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.qt-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.qt-btn-ghost { display: inline-flex; align-items: center; gap: 6px; background: transparent; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #374151; cursor: pointer; }
.qt-btn-ghost:hover { background: #f9fafb; }
.qt-btn-save { display: inline-flex; align-items: center; gap: 6px; background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.qt-btn-save:hover { background: #dcfce7; }
.qt-btn-save:disabled { opacity: .5; cursor: not-allowed; }
.qt-btn-danger { display: inline-flex; align-items: center; gap: 6px; background: #fef2f2; border: 1px solid #dc2626; color: #dc2626; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.qt-btn-danger:hover { background: #fee2e2; }

.qt-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; }
.qt-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.qt-table th { background: #f9fafb; border-bottom: 1px solid #e5e7eb; padding: 10px 12px; font-size: 11.5px; font-weight: 600; color: #374151; text-align: left; white-space: nowrap; }
.qt-table th.sortable { cursor: pointer; user-select: none; }
.qt-table th.sortable:hover { color: #2563eb; }
.ta-r { text-align: right !important; }
.qt-row td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; cursor: pointer; }
.qt-row:last-child td { border-bottom: none; }
.qt-row:hover td { background: #f9fafb; }
.qt-row.selected td { background: #eff6ff; }
.qt-num { font-family: monospace; font-size: 12.5px; color: #2563eb; font-weight: 600; }
.mono-sm { font-family: monospace; font-size: 12.5px; }
.text-muted { color: #6b7280; }
.text-danger { color: #dc2626; }
.qt-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 10px; font-size: 11.5px; font-weight: 600; }
.qt-bdg-grey   { background: #f3f4f6; color: #6b7280; }
.qt-bdg-blue   { background: #dbeafe; color: #1a6ef7; }
.qt-bdg-green  { background: #d1fae5; color: #059669; }
.qt-bdg-purple { background: #ede9fe; color: #7c3aed; }
.qt-bdg-red    { background: #fee2e2; color: #dc2626; }
.qt-badge-white { background: rgba(255,255,255,.2); color: #fff !important; border: 1px solid rgba(255,255,255,.4); }
.qt-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.qt-act-btn { background: transparent; border: 1px solid #e5e7eb; border-radius: 6px; width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #6b7280; }
.qt-act-btn:hover { background: #f3f4f6; color: #2563eb; }
.qt-act-conv { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.qt-act-conv:hover { background: #dbeafe; }
.qt-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.qt-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }
.qt-shimmer { height: 13px; background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%); border-radius: 4px; animation: shimmer 1.2s infinite; background-size: 200% 100%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

.qt-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.2); z-index: 40; }
.qt-drawer { position: fixed; top: 0; right: -600px; bottom: 0; width: 600px; max-width: 96vw; background: #fff; border-left: 1px solid #e5e7eb; box-shadow: -8px 0 24px rgba(0,0,0,.08); z-index: 50; display: flex; flex-direction: column; transition: right .22s ease; }
.qt-drawer.open { right: 0; }
.qt-view-drawer { width: 540px; right: -540px; }
.qt-view-drawer.open { right: 0; }
.qt-dheader { display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 60px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; }
.qt-dheader-title { font-size: 15px; font-weight: 600; color: #111827; }
.qt-dclose { background: transparent; border: none; cursor: pointer; color: #6b7280; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; }
.qt-dclose:hover { background: #f3f4f6; color: #111827; }
.qt-dbody { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.qt-fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.qt-field { display: flex; flex-direction: column; gap: 4px; }
.qt-label { font-size: 12px; font-weight: 600; color: #374151; }
.req { color: #dc2626; }
.qt-input { width: 100%; box-sizing: border-box; border: 1px solid #e5e7eb; border-radius: 6px; padding: 7px 10px; font: inherit; font-size: 13px; outline: none; background: #fff; color: #111827; }
.qt-input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.08); }
textarea.qt-input { resize: vertical; }
.qt-section-title { font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: .05em; padding-bottom: 4px; border-bottom: 1px solid #f3f4f6; }
.qt-items-table { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.qt-items-head { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #374151; }
.qt-items-row { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; }
.qt-add-line { background: transparent; border: none; color: #2563eb; font-size: 12.5px; font-weight: 600; cursor: pointer; padding: 8px 12px; display: inline-flex; align-items: center; gap: 6px; }
.qt-add-line:hover { background: #eff6ff; }
.qt-rm-line { background: transparent; border: 1px solid #e5e7eb; border-radius: 4px; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #9ca3af; }
.qt-rm-line:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.qt-totals { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.qt-totals-right { display: flex; flex-direction: column; gap: 4px; min-width: 220px; }
.qt-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 3px 0; }
.qt-total-row.grand { font-weight: 700; font-size: 14px; color: #111827; border-top: 1px solid #e5e7eb; padding-top: 6px; }

.qt-view-head { position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 20px; flex-shrink: 0; color: #fff; }
.qt-view-num { font-size: 18px; font-weight: 700; font-family: monospace; color: #fff; }
.qt-view-sub { font-size: 13px; color: rgba(255,255,255,.8); margin-top: 2px; }
.qt-view-amount { font-size: 22px; font-weight: 800; font-family: monospace; color: #fff; }
.qt-vclose { position: absolute; top: 12px; right: 12px; color: #fff; }
.qt-vclose:hover { background: rgba(255,255,255,.18); color: #fff; }
.qt-tabs { display: flex; gap: 4px; padding: 0 20px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; background: #fff; }
.qt-tab { background: transparent; border: none; padding: 10px 14px; font: inherit; font-size: 12.5px; font-weight: 600; color: #6b7280; cursor: pointer; border-bottom: 2px solid transparent; display: inline-flex; align-items: center; gap: 6px; }
.qt-tab:hover { color: #2563eb; }
.qt-tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.qt-tab-count { background: #2563eb; color: #fff; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.qt-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.qt-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }
.qt-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.qt-view-items-head { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.qt-view-items-row { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.qt-terms { padding: 10px 12px; background: #f8fafc; border-radius: 6px; }
.qt-conv-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 12.5px; align-items: center; }
.qt-dfooter { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #e5e7eb; flex-shrink: 0; flex-wrap: wrap; }

.qt-apply-dialog { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 520px; max-width: 96vw; background: #fff; border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.2); z-index: 70; display: flex; flex-direction: column; overflow: hidden; }
.qt-convert-options { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.qt-convert-card { background: #fff; border: 2px solid #e5e7eb; border-radius: 10px; padding: 14px; display: flex; align-items: center; gap: 12px; cursor: pointer; font: inherit; text-align: left; transition: all .15s; }
.qt-convert-card:hover { border-color: #1a6ef7; background: #f0f9ff; }
.qt-convert-card.active { border-color: #1a6ef7; background: #eff6ff; box-shadow: 0 0 0 4px rgba(26,110,247,.1); }
.qt-convert-icon { width: 40px; height: 40px; border-radius: 8px; display: grid; place-items: center; font-weight: 800; font-size: 14px; flex-shrink: 0; }
</style>
