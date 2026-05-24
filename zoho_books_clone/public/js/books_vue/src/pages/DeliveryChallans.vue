<template>
<div class="b-page">
  <!-- Toolbar -->
  <div class="b-action-bar">
    <div class="rec-search-wrap" style="min-width:220px">
      <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
      <input v-model="search" placeholder="Search challans…" class="rec-search-input"/>
    </div>
    <div style="display:flex;gap:6px">
      <button v-for="t in TABS" :key="t.k" class="b-pill" :class="{active:tab===t.k}" @click="tab=t.k">{{t.l}}</button>
    </div>
    <div style="margin-left:auto;display:flex;gap:6px">
      <button class="b-btn b-btn-ghost" @click="load"><span v-html="icon('refresh',13)"></span></button>
      <button class="b-btn b-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Challan</button>
    </div>
  </div>

  <!-- Summary -->
  <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px" v-if="!loading">
    <div class="b-card b-card-body" style="padding:14px 16px">
      <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Draft</div>
      <div style="font-size:20px;font-weight:700;font-family:monospace;color:#E67700">{{counts.draft}}</div>
    </div>
    <div class="b-card b-card-body" style="padding:14px 16px">
      <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">To Deliver</div>
      <div style="font-size:20px;font-weight:700;font-family:monospace;color:#1971C2">{{counts.submitted}}</div>
    </div>
    <div class="b-card b-card-body" style="padding:14px 16px">
      <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Delivered</div>
      <div style="font-size:20px;font-weight:700;font-family:monospace;color:#2F9E44">{{counts.delivered}}</div>
    </div>
    <div class="b-card b-card-body" style="padding:14px 16px">
      <div style="font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Total</div>
      <div style="font-size:20px;font-weight:700;font-family:monospace;color:#111827">{{list.length}}</div>
    </div>
  </div>

  <!-- Table -->
  <div class="b-card" style="padding:0;overflow:hidden">
    <table class="b-table">
      <thead>
        <tr>
          <th @click="sort('name')" class="sortable">Challan # <span v-html="sa('name')"></span></th>
          <th @click="sort('customer_name')" class="sortable">Customer <span v-html="sa('customer_name')"></span></th>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sa('posting_date')"></span></th>
          <th @click="sort('lr_no')" class="sortable">LR / Tracking # <span v-html="sa('lr_no')"></span></th>
          <th>Status</th>
          <th class="ta-r">Items</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template v-if="loading">
          <tr v-for="n in 6" :key="n"><td colspan="7" style="padding:14px"><div class="b-shimmer" style="height:12px"></div></td></tr>
        </template>
        <tr v-else-if="!sorted.length">
          <td colspan="7" class="b-empty">{{search?'No challans match your search':'No delivery challans yet'}}</td>
        </tr>
        <tr v-else v-for="r in sorted" :key="r.name" class="clickable" @click="openView(r)">
          <td><span class="mono" style="font-size:12px;color:#3B5BDB">{{r.name}}</span></td>
          <td class="fw-600">{{r.customer_name||r.customer||'—'}}</td>
          <td class="c-muted" style="font-size:12.5px">{{r.posting_date||'—'}}</td>
          <td class="c-muted mono" style="font-size:12.5px">{{r.lr_no||'—'}}</td>
          <td>
            <span class="b-badge" :class="statusClass(r)">{{statusLabel(r)}}</span>
          </td>
          <td class="ta-r c-muted" style="font-size:12.5px">{{r.total_qty||'—'}}</td>
          <td style="text-align:center">
            <button class="b-btn b-btn-ghost" style="padding:4px 8px;font-size:11.5px" @click.stop="openView(r)">
              <span v-html="icon('eye',12)"></span>
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- ===== View Drawer ===== -->
  <Teleport to="body">
    <!-- ============================ VIEW DRAWER -->
    <div v-if="viewOpen" class="dc-overlay" @click.self="viewOpen=false"></div>
    <div class="dc-drawer dc-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="dc-view-head" :class="dcHeadClass(viewDoc)">
          <div class="dc-view-head-row">
            <div>
              <div class="dc-view-num">{{ viewDoc.name }}</div>
              <div class="dc-view-sub">Delivery Challan · {{ viewDoc.posting_date }}</div>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span class="b-badge" :class="statusClass(viewDoc)">{{ statusLabel(viewDoc) }}</span>
              <button class="dc-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
            </div>
          </div>
        </div>

        <div class="dc-dbody">
          <div class="dc-section">
            <div class="dc-section-hdr"><span v-html="icon('user',13)"></span><span>Customer & Date</span></div>
            <div class="dc-meta-grid">
              <div><div class="dc-meta-lbl">Customer</div><div style="font-weight:600">{{ viewDoc.customer_name||viewDoc.customer||'—' }}</div></div>
              <div><div class="dc-meta-lbl">Date</div><div>{{ viewDoc.posting_date||'—' }}</div></div>
              <div><div class="dc-meta-lbl">LR / Tracking #</div><div class="mono">{{ viewDoc.lr_no||'—' }}</div></div>
              <div><div class="dc-meta-lbl">Transporter</div><div>{{ viewDoc.transporter_name||'—' }}</div></div>
              <div style="grid-column:1/-1"><div class="dc-meta-lbl">Delivery Address</div><div>{{ viewDoc.shipping_address||viewDoc.customer_address||'—' }}</div></div>
              <div v-if="viewDoc.remarks" style="grid-column:1/-1"><div class="dc-meta-lbl">Remarks</div><div>{{ viewDoc.remarks }}</div></div>
            </div>
          </div>

          <div class="dc-section">
            <div class="dc-section-hdr">
              <span v-html="icon('box',13)"></span><span>Items</span>
              <span style="margin-left:auto;font-size:11.5px;color:#6b7280;text-transform:none;letter-spacing:0">
                {{ (viewDoc.items||[]).length }} line{{ (viewDoc.items||[]).length!==1?'s':'' }}
              </span>
            </div>
            <table class="b-table" style="font-size:12.5px">
              <thead><tr><th>Item</th><th class="ta-r">Qty</th><th>UOM</th></tr></thead>
              <tbody>
                <tr v-for="it in viewDoc.items||[]" :key="it.name">
                  <td>{{ it.item_name||it.item_code }}</td>
                  <td class="ta-r mono">{{ it.qty }}</td>
                  <td class="c-muted">{{ it.uom||'Nos' }}</td>
                </tr>
                <tr v-if="!(viewDoc.items||[]).length"><td colspan="3" class="b-empty">No items</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="dc-dfooter">
          <button class="b-btn b-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="b-btn b-btn-primary" @click="submitChallan" :disabled="submitting">
            {{ submitting?'Submitting…':'Submit Challan' }}
          </button>
        </div>
      </template>
    </div>

    <!-- ============================ NEW CHALLAN DRAWER -->
    <div v-if="newOpen" class="dc-overlay" @click.self="newOpen=false"></div>
    <div class="dc-drawer" :class="{open:newOpen}">
      <div class="dc-dheader">
        <div class="dc-dheader-left">
          <div class="dc-dheader-ico"><span v-html="icon('warehouse',18)"></span></div>
          <div>
            <div class="dc-dheader-title">New Delivery Challan</div>
            <div class="dc-dheader-sub">Dispatch goods to a customer, with or without an invoice</div>
          </div>
        </div>
        <button class="dc-dclose" @click="newOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="dc-dbody">
        <!-- Section: Customer & Date -->
        <div class="dc-section">
          <div class="dc-section-hdr"><span v-html="icon('user',13)"></span><span>Customer & Date</span></div>
          <div class="dc-grid">
            <div class="dc-field">
              <label class="dc-flbl">Customer <span class="req">*</span></label>
              <div style="position:relative">
                <input class="dc-input" v-model="form.customer" placeholder="Customer ID" @input="onCustInput"/>
                <div v-if="custSuggestions.length" class="dc-suggest">
                  <div v-for="s in custSuggestions" :key="s.name" class="dc-suggest-item" @click="pickCustomer(s)">
                    {{ s.customer_name||s.name }}
                  </div>
                </div>
              </div>
            </div>
            <div class="dc-field">
              <label class="dc-flbl">Date <span class="req">*</span></label>
              <input class="dc-input" type="date" v-model="form.posting_date"/>
            </div>
          </div>
        </div>

        <!-- Section: Transport -->
        <div class="dc-section">
          <div class="dc-section-hdr"><span v-html="icon('warehouse',13)"></span><span>Transport</span></div>
          <div class="dc-grid">
            <div class="dc-field">
              <label class="dc-flbl">LR / Tracking #</label>
              <input class="dc-input" v-model="form.lr_no" placeholder="e.g. LR12345"/>
            </div>
            <div class="dc-field">
              <label class="dc-flbl">Transporter</label>
              <input class="dc-input" v-model="form.transporter_name" placeholder="e.g. BlueDart, VRL"/>
            </div>
            <div class="dc-field" style="grid-column:1/-1">
              <label class="dc-flbl">Delivery Address</label>
              <input class="dc-input" v-model="form.shipping_address" placeholder="Shipping address"/>
            </div>
            <div class="dc-field" style="grid-column:1/-1">
              <label class="dc-flbl">Remarks</label>
              <input class="dc-input" v-model="form.remarks" placeholder="Optional remarks"/>
            </div>
          </div>
        </div>

        <!-- Section: Items -->
        <div class="dc-section">
          <div class="dc-section-hdr">
            <span v-html="icon('box',13)"></span><span>Items <span class="req">*</span></span>
            <button class="b-btn b-btn-ghost" style="margin-left:auto;padding:4px 10px;font-size:12px" @click="addItem">
              <span v-html="icon('plus',11)" style="vertical-align:-1px;margin-right:3px"></span> Add Item
            </button>
          </div>
          <div v-for="(it,i) in form.items" :key="i" class="dc-item-row">
            <input class="dc-input" v-model="it.item_code" placeholder="Item code"/>
            <input class="dc-input ta-r" type="number" v-model="it.qty" placeholder="Qty" min="0.01" step="0.01"/>
            <input class="dc-input" v-model="it.uom" placeholder="UOM"/>
            <button class="dc-rm" @click="removeItem(i)"><span v-html="icon('trash',12)"></span></button>
          </div>
          <div v-if="!form.items.length" class="dc-items-empty">No items yet — click Add Item</div>
        </div>
      </div>

      <div class="dc-dfooter">
        <button class="b-btn b-btn-ghost" @click="newOpen=false" :disabled="saving">Cancel</button>
        <button class="b-btn b-btn-primary" @click="saveChallan" :disabled="saving">
          {{ saving?'Saving…':'Save Challan' }}
        </button>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGET, apiSave, apiSubmit, apiLinkValues, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";

const { toast } = useToast();

const TABS = [{k:"all",l:"All"},{k:"0",l:"Draft"},{k:"1",l:"Submitted"},{k:"2",l:"Cancelled"}];

const list     = ref([]);
const loading  = ref(false);
const search   = ref("");
const tab      = ref("all");
const sortCol  = ref("posting_date");
const sortDir  = ref("desc");

const viewOpen  = ref(false);
const viewDoc   = ref(null);
const submitting = ref(false);

const newOpen   = ref(false);
const saving    = ref(false);
const custSuggestions = ref([]);
let custTimer = null;

const form = reactive({
  customer: "", posting_date: new Date().toISOString().slice(0,10),
  lr_no: "", transporter_name: "", shipping_address: "", remarks: "",
  items: [],
});

const counts = computed(() => ({
  draft:     list.value.filter(r => r.docstatus === 0).length,
  submitted: list.value.filter(r => r.docstatus === 1).length,
  delivered: list.value.filter(r => r.status === "Delivered").length,
}));

function statusLabel(r) {
  if (r.docstatus === 2) return "Cancelled";
  if (r.status === "Delivered") return "Delivered";
  if (r.docstatus === 1) return "To Deliver";
  return "Draft";
}

function dcHeadClass(r) {
  if (r.docstatus === 2) return "cancelled";
  if (r.status === "Delivered") return "delivered";
  return "";
}

function statusClass(r) {
  if (r.docstatus === 2) return "b-badge-muted";
  if (r.status === "Delivered") return "b-badge-green";
  if (r.docstatus === 1) return "b-badge-blue";
  return "b-badge-orange";
}

async function load() {
  loading.value = true;
  try {
    // No standalone Delivery Note doctype in this build. We synthesise the
    // list from Sales Order lines that have been marked delivered.
    const rows = await apiGET("zoho_books_clone.api.docs.get_delivery_challan_list", { limit: 500 }) || [];
    // Compat shape so the existing template binds without changes
    list.value = rows.map(r => ({
      name: r.sales_order,
      customer: r.customer,
      customer_name: r.customer_name,
      posting_date: r.delivery_date || r.transaction_date,
      lr_no: "",
      transporter_name: "",
      status: r.challan_status,
      docstatus: r.status === "Cancelled" ? 2 : 1,
      total_qty: r.qty_delivered,
      qty_ordered: r.qty_ordered,
      qty_delivered: r.qty_delivered,
      qty_billed: r.qty_billed,
      pct_delivered: r.pct_delivered,
      grand_total: r.grand_total,
    }));
  } catch (e) {
    console.warn("Delivery challan load failed:", e.message);
    list.value = [];
  } finally { loading.value = false; }
}

const filtered = computed(() => {
  let r = list.value;
  if (tab.value === "1")      r = r.filter(x => x.status === "Fully Delivered");
  else if (tab.value === "0") r = r.filter(x => x.status === "Partially Delivered");
  else if (tab.value === "2") r = r.filter(x => x.docstatus === 2);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name||"").toLowerCase().includes(q) || (x.customer_name||"").toLowerCase().includes(q));
  }
  return r;
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const c = String(a[col]??"").localeCompare(String(b[col]??""));
    return sortDir.value === "asc" ? c : -c;
  });
});

function sort(col) { if (sortCol.value===col) sortDir.value=sortDir.value==="asc"?"desc":"asc"; else { sortCol.value=col; sortDir.value="asc"; } }
function sa(col) { if (sortCol.value!==col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value==="asc"?"↑":"↓"; }

async function openView(r) {
  viewOpen.value = true;
  // r.name is the underlying Sales Order; pull per-line delivery rows.
  try {
    const lines = await apiGET("zoho_books_clone.api.docs.get_delivery_challan_lines", { sales_order: r.name }) || [];
    viewDoc.value = { ...r, items: lines };
  } catch (e) {
    console.warn("DC lines load failed:", e.message);
    viewDoc.value = r;
  }
}

async function submitChallan() {
  if (!viewDoc.value) return;
  submitting.value = true;
  try {
    await apiSubmit("Delivery Note", viewDoc.value.name);
    toast.success("Challan submitted");
    viewOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Submit failed"); }
  finally { submitting.value = false; }
}

function openNew() {
  Object.assign(form, {
    customer: "", posting_date: new Date().toISOString().slice(0,10),
    lr_no: "", transporter_name: "", shipping_address: "", remarks: "",
    items: [],
  });
  custSuggestions.value = [];
  newOpen.value = true;
}

function addItem() {
  form.items.push({ item_code: "", qty: 1, uom: "Nos" });
}

function removeItem(i) {
  form.items.splice(i, 1);
}

function onCustInput() {
  clearTimeout(custTimer);
  const txt = form.customer.trim();
  if (txt.length < 2) { custSuggestions.value = []; return; }
  custTimer = setTimeout(async () => {
    try {
      const res = await apiLinkValues("Customer", txt);
      custSuggestions.value = res;
    } catch { custSuggestions.value = []; }
  }, 250);
}

function pickCustomer(s) {
  form.customer = s.name;
  custSuggestions.value = [];
}

async function saveChallan() {
  if (!form.customer.trim()) { toast.error("Customer is required"); return; }
  if (!form.items.length || !form.items[0].item_code) { toast.error("Add at least one item"); return; }
  saving.value = true;
  try {
    const company = await resolveCompany();
    const doc = {
      doctype: "Delivery Note",
      customer: form.customer,
      posting_date: form.posting_date,
      company,
      lr_no: form.lr_no || "",
      transporter_name: form.transporter_name || "",
      shipping_address: form.shipping_address || "",
      remarks: form.remarks || "",
      items: form.items.filter(it => it.item_code.trim()).map(it => ({
        doctype: "Delivery Note Item",
        item_code: it.item_code,
        item_name: it.item_code,
        qty: parseFloat(it.qty) || 1,
        uom: it.uom || "Nos",
        stock_uom: it.uom || "Nos",
        conversion_factor: 1,
      })),
    };
    const saved = await apiSave(doc);
    toast.success(`Challan ${saved.name} saved`);
    newOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save"); }
  finally { saving.value = false; }
}

onMounted(load);
</script>

<style scoped>
.rec-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;}
.rec-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.sortable{cursor:pointer;user-select:none;}.sortable:hover{color:#2563eb;}

/* DC Drawer */
.dc-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);backdrop-filter:blur(2px);z-index:40;}
.dc-drawer{position:fixed;top:0;right:-580px;bottom:0;width:580px;max-width:96vw;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-12px 0 32px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s cubic-bezier(.32,.72,0,1);}
.dc-drawer.open{right:0;}
.dc-view-drawer{width:560px;right:-560px;}.dc-view-drawer.open{right:0;}

.dc-dheader{display:flex;align-items:flex-start;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.dc-dheader-left{display:flex;align-items:flex-start;gap:12px;}
.dc-dheader-ico{width:38px;height:38px;border-radius:10px;background:#fff;border:1px solid rgba(37,99,235,.18);display:inline-flex;align-items:center;justify-content:center;color:#2563eb;box-shadow:0 1px 3px rgba(15,23,42,.06);flex-shrink:0;}
.dc-dheader-title{font-size:15px;font-weight:700;color:#111827;letter-spacing:-0.01em;}
.dc-dheader-sub{font-size:12px;color:#475569;margin-top:3px;font-weight:500;}
.dc-dclose{background:rgba(255,255,255,.6);border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;transition:background .15s;}
.dc-dclose:hover{background:#fff;color:#111827;}

.dc-view-head{padding:18px 20px;border-bottom:1px solid #e5e7eb;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);flex-shrink:0;}
.dc-view-head.delivered{background:linear-gradient(135deg,#f0fdf4 0%,#bbf7d0 100%);}
.dc-view-head.cancelled{background:linear-gradient(135deg,#f3f4f6 0%,#e5e7eb 100%);}
.dc-view-head-row{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;}
.dc-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.dc-view-sub{font-size:12.5px;color:#475569;margin-top:2px;}

.dc-dbody{flex:1;overflow-y:auto;padding:18px 20px;display:flex;flex-direction:column;gap:14px;background:#f8fafc;}
.dc-section{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:12px;box-shadow:0 1px 2px rgba(15,23,42,.03);}
.dc-section-hdr{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#0f172a;}
.dc-section-hdr svg{color:#2563eb;}
.dc-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.dc-field{display:flex;flex-direction:column;gap:4px;}
.dc-flbl{font-size:12px;font-weight:600;color:#374151;}
.dc-input{border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;transition:border-color .15s, box-shadow .15s;width:100%;box-sizing:border-box;}
.dc-input:hover:not(:disabled){border-color:#cbd5e1;}
.dc-input:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12);}
.req{color:#dc2626;}

.dc-suggest{position:absolute;top:calc(100% + 4px);left:0;right:0;background:#fff;border:1px solid #e5e7eb;border-radius:8px;box-shadow:0 8px 24px rgba(15,23,42,.10);z-index:100;max-height:200px;overflow-y:auto;}
.dc-suggest-item{padding:8px 12px;cursor:pointer;font-size:13px;border-bottom:1px solid #f3f4f6;}
.dc-suggest-item:hover{background:#f9fafb;}
.dc-suggest-item:last-child{border-bottom:none;}

.dc-item-row{display:grid;grid-template-columns:2fr 90px 90px 32px;gap:8px;align-items:center;}
.dc-rm{background:#fef2f2;border:1px solid #fecaca;border-radius:6px;cursor:pointer;color:#dc2626;height:32px;display:inline-flex;align-items:center;justify-content:center;}
.dc-rm:hover{background:#fee2e2;}
.dc-items-empty{font-size:12px;color:#868E96;text-align:center;padding:14px;background:#f9fafb;border:1px dashed #e5e7eb;border-radius:8px;}

.dc-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.dc-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px;font-weight:600;}

.dc-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;background:#fff;flex-shrink:0;}
.mono{font-family:monospace;}
</style>
