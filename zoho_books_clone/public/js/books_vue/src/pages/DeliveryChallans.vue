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
    <div v-if="viewOpen" style="position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40" @click.self="viewOpen=false"></div>
    <div :style="'position:fixed;top:0;right:0;bottom:0;width:520px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:transform .22s;transform:'+(viewOpen?'translateX(0)':'translateX(100%)')">
      <template v-if="viewDoc">
        <div style="display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#EDF2FF">
          <div>
            <div style="font-size:15px;font-weight:700;font-family:monospace;color:#1a1a2e">{{viewDoc.name}}</div>
            <div style="font-size:12px;color:#6b7280;margin-top:1px">Delivery Challan · {{viewDoc.posting_date}}</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <span class="b-badge" :class="statusClass(viewDoc)">{{statusLabel(viewDoc)}}</span>
            <button @click="viewOpen=false" style="background:none;border:none;cursor:pointer;padding:4px" v-html="icon('x',16)"></button>
          </div>
        </div>
        <div style="flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px">
          <!-- Meta grid -->
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Customer</div><div style="font-weight:600">{{viewDoc.customer_name||viewDoc.customer||'—'}}</div></div>
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Date</div><div>{{viewDoc.posting_date||'—'}}</div></div>
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">LR / Tracking #</div><div class="mono" style="font-size:12.5px">{{viewDoc.lr_no||'—'}}</div></div>
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Transporter</div><div style="font-size:12.5px">{{viewDoc.transporter_name||'—'}}</div></div>
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Delivery Address</div><div style="font-size:12.5px">{{viewDoc.shipping_address||viewDoc.customer_address||'—'}}</div></div>
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px">Remarks</div><div style="font-size:12.5px">{{viewDoc.remarks||'—'}}</div></div>
          </div>

          <!-- Items -->
          <div>
            <div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em">Items</div>
            <table class="b-table" style="font-size:12px">
              <thead><tr><th>Item</th><th class="ta-r">Qty</th><th>UOM</th></tr></thead>
              <tbody>
                <tr v-for="it in viewDoc.items||[]" :key="it.name">
                  <td>{{it.item_name||it.item_code}}</td>
                  <td class="ta-r mono">{{it.qty}}</td>
                  <td class="c-muted">{{it.uom||'Nos'}}</td>
                </tr>
                <tr v-if="!(viewDoc.items||[]).length">
                  <td colspan="3" class="b-empty">No items</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div style="padding:14px 20px;border-top:1px solid #e5e7eb;display:flex;gap:8px;justify-content:flex-end">
          <button class="b-btn b-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="b-btn b-btn-primary" @click="submitChallan" :disabled="submitting">
            {{submitting?'Submitting…':'Submit Challan'}}
          </button>
        </div>
      </template>
    </div>

    <!-- ===== New Challan Drawer ===== -->
    <div v-if="newOpen" style="position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40" @click.self="newOpen=false"></div>
    <div :style="'position:fixed;top:0;right:0;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:transform .22s;transform:'+(newOpen?'translateX(0)':'translateX(100%)')">
      <div style="display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0">
        <span style="font-size:15px;font-weight:700">New Delivery Challan</span>
        <button @click="newOpen=false" style="background:none;border:none;cursor:pointer;padding:4px" v-html="icon('x',16)"></button>
      </div>
      <div style="flex:1;overflow-y:auto;padding:20px;display:grid;gap:14px;align-content:start">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="nim-field">
            <label class="nim-label">Customer <span style="color:#c92a2a">*</span></label>
            <input class="nim-input" v-model="form.customer" placeholder="Customer ID" @input="onCustInput"/>
            <div v-if="custSuggestions.length" style="position:relative">
              <div style="position:absolute;top:2px;left:0;right:0;background:#fff;border:1px solid #E2E8F0;border-radius:6px;box-shadow:0 4px 12px rgba(0,0,0,.1);z-index:100;max-height:180px;overflow-y:auto">
                <div v-for="s in custSuggestions" :key="s.name"
                  @click="pickCustomer(s)"
                  style="padding:8px 12px;cursor:pointer;font-size:13px;border-bottom:1px solid #F8F9FA"
                  onmouseover="this.style.background='#F8F9FA'" onmouseout="this.style.background=''">
                  {{s.customer_name||s.name}}
                </div>
              </div>
            </div>
          </div>
          <div class="nim-field">
            <label class="nim-label">Date <span style="color:#c92a2a">*</span></label>
            <input class="nim-input" type="date" v-model="form.posting_date"/>
          </div>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="nim-field">
            <label class="nim-label">LR / Tracking #</label>
            <input class="nim-input" v-model="form.lr_no" placeholder="e.g. LR12345"/>
          </div>
          <div class="nim-field">
            <label class="nim-label">Transporter</label>
            <input class="nim-input" v-model="form.transporter_name" placeholder="Transporter name"/>
          </div>
        </div>
        <div class="nim-field">
          <label class="nim-label">Delivery Address</label>
          <input class="nim-input" v-model="form.shipping_address" placeholder="Shipping address"/>
        </div>
        <div class="nim-field">
          <label class="nim-label">Remarks</label>
          <input class="nim-input" v-model="form.remarks" placeholder="Optional remarks"/>
        </div>

        <!-- Items -->
        <div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
            <label class="nim-label" style="margin:0">Items <span style="color:#c92a2a">*</span></label>
            <button class="b-btn b-btn-ghost" style="padding:4px 10px;font-size:12px" @click="addItem">
              <span v-html="icon('plus',11)" style="vertical-align:-1px;margin-right:3px"></span> Add Item
            </button>
          </div>
          <div v-for="(it,i) in form.items" :key="i" style="display:grid;grid-template-columns:2fr 80px 80px 28px;gap:8px;margin-bottom:8px;align-items:center">
            <input class="nim-input" v-model="it.item_code" placeholder="Item code" style="font-size:12px"/>
            <input class="nim-input" type="number" v-model="it.qty" placeholder="Qty" min="0.01" step="0.01" style="font-size:12px"/>
            <input class="nim-input" v-model="it.uom" placeholder="UOM" style="font-size:12px"/>
            <button @click="removeItem(i)" style="background:none;border:none;cursor:pointer;color:#C92A2A;padding:2px" v-html="icon('trash',12)"></button>
          </div>
          <div v-if="!form.items.length" style="font-size:12px;color:#868E96;text-align:center;padding:10px;background:#F8F9FA;border-radius:6px">
            No items yet — click Add Item
          </div>
        </div>
      </div>
      <div style="padding:14px 20px;border-top:1px solid #e5e7eb;display:flex;gap:8px;justify-content:flex-end">
        <button class="b-btn b-btn-ghost" @click="newOpen=false">Cancel</button>
        <button class="b-btn b-btn-primary" @click="saveChallan" :disabled="saving">{{saving?'Saving…':'Save Challan'}}</button>
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

function statusClass(r) {
  if (r.docstatus === 2) return "b-badge-muted";
  if (r.status === "Delivered") return "b-badge-green";
  if (r.docstatus === 1) return "b-badge-blue";
  return "b-badge-orange";
}

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Delivery Note", {
      fields: ["name","customer","customer_name","posting_date","lr_no","transporter_name","status","docstatus","total_qty"],
      limit: 200,
    });
  } catch (e) {
    console.warn("Delivery Note load failed:", e.message);
    list.value = [];
  } finally { loading.value = false; }
}

const filtered = computed(() => {
  let r = list.value;
  if (tab.value !== "all") r = r.filter(x => String(x.docstatus) === tab.value);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name||"").toLowerCase().includes(q) || (x.customer_name||"").toLowerCase().includes(q) || (x.lr_no||"").toLowerCase().includes(q));
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
  try {
    viewDoc.value = await apiGET("Delivery Note", r.name);
  } catch { viewDoc.value = r; }
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
</style>
