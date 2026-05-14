<template>
  <div class="qt-page">

    <div class="qt-actions">
      <div class="qt-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search quotations…" class="qt-search-input" />
      </div>
      <div class="qt-pills">
        <button v-for="t in tabs" :key="t.key"
          class="qt-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="qt-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="qt-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Quotation
        </button>
      </div>
    </div>

    <!-- Summary -->
    <div class="qt-summary" v-if="!loading">
      <div class="qt-sum-card">
        <div class="qt-sum-lbl">Draft</div>
        <div class="qt-sum-val">{{ counts.draft }}</div>
      </div>
      <div class="qt-sum-card">
        <div class="qt-sum-lbl">Submitted</div>
        <div class="qt-sum-val blue">{{ counts.submitted }}</div>
      </div>
      <div class="qt-sum-card">
        <div class="qt-sum-lbl">Total Value</div>
        <div class="qt-sum-val">{{ fmtCur(totalValue) }}</div>
      </div>
      <div class="qt-sum-card">
        <div class="qt-sum-lbl">Expired</div>
        <div class="qt-sum-val red">{{ counts.expired }}</div>
      </div>
    </div>

    <!-- Table -->
    <div class="qt-card">
      <table class="qt-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sort('name')" class="sortable">Quote # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('customer_name')" class="sortable">Customer <span v-html="sortArrow('customer_name')"></span></th>
            <th @click="sort('transaction_date')" class="sortable">Date <span v-html="sortArrow('transaction_date')"></span></th>
            <th @click="sort('valid_till')" class="sortable">Valid Till <span v-html="sortArrow('valid_till')"></span></th>
            <th>Status</th>
            <th @click="sort('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:60px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="8"><div class="qt-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="q in sorted" :key="q.name" class="qt-row" :class="{selected:selected.has(q.name)}">
              <td><input type="checkbox" :checked="selected.has(q.name)" @change="toggle(q.name)" /></td>
              <td @click="openView(q)"><span class="qt-num">{{ q.name }}</span></td>
              <td @click="openView(q)">{{ q.customer_name || q.party_name || '—' }}</td>
              <td @click="openView(q)" class="text-muted mono-sm">{{ fmtDate(q.transaction_date) }}</td>
              <td @click="openView(q)" :class="isExpired(q)?'text-danger':'text-muted'" class="mono-sm">
                {{ fmtDate(q.valid_till) || '—' }}
              </td>
              <td @click="openView(q)"><span class="qt-badge" :class="statusClass(q)">{{ statusLabel(q) }}</span></td>
              <td @click="openView(q)" class="ta-r mono-sm">{{ fmtCur(q.grand_total) }}</td>
              <td class="qt-act-cell">
                <button class="qt-act-btn" @click="openView(q)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="q.docstatus===0" class="qt-act-btn" @click="openEdit(q)" title="Edit"><span v-html="icon('edit',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length">
              <td colspan="8" class="qt-empty">No quotations found</td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit drawer -->
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
            <SearchableSelect v-model="form.party_name" :options="customers"
              placeholder="Select customer…" @search="fetchCustomers" />
          </div>
          <div class="qt-field">
            <label class="qt-label">Quote Date <span class="req">*</span></label>
            <input v-model="form.transaction_date" type="date" class="qt-input" />
          </div>
          <div class="qt-field">
            <label class="qt-label">Valid Till</label>
            <input v-model="form.valid_till" type="date" class="qt-input" />
          </div>
        </div>

        <!-- Line items -->
        <div class="qt-section-title">Items</div>
        <div class="qt-items-table">
          <div class="qt-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="qt-items-row">
            <div>
              <SearchableSelect v-model="line.item_code" :options="items"
                placeholder="Select item…" @search="fetchItems" @select="v=>onItemSelect(line,v)" />
            </div>
            <div><input v-model="line.description" class="qt-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="1" class="qt-input ta-r" @input="calcLine(line)" /></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="qt-input ta-r" @input="calcLine(line)" /></div>
            <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
            <div><button @click="removeLine(line.id)" class="qt-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="qt-add-line" @click="addLine">
            <span v-html="icon('plus',12)"></span> Add Item
          </button>
        </div>

        <!-- Totals -->
        <div class="qt-totals">
          <div class="qt-field" style="max-width:160px">
            <label class="qt-label">Tax Rate %</label>
            <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="qt-input" />
          </div>
          <div class="qt-totals-right">
            <div class="qt-total-row"><span>Subtotal</span><span>{{ fmtCur(subtotal) }}</span></div>
            <div class="qt-total-row"><span>Tax ({{ form.tax_rate || 0 }}%)</span><span>{{ fmtCur(taxAmount) }}</span></div>
            <div class="qt-total-row grand"><span>Total</span><span>{{ fmtCur(subtotal + taxAmount) }}</span></div>
          </div>
        </div>

        <div class="qt-field">
          <label class="qt-label">Notes</label>
          <textarea v-model="form.terms" rows="2" class="qt-input" placeholder="Terms & conditions…"></textarea>
        </div>
      </div>
      <div class="qt-dfooter">
        <button class="qt-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="qt-btn-save" :disabled="drawerSaving" @click="saveQuote(0)">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="qt-btn-primary" :disabled="drawerSaving" @click="saveQuote(1)">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}
        </button>
      </div>
    </div>

    <!-- View drawer -->
    <div v-if="viewOpen" class="qt-overlay" @click.self="viewOpen=false"></div>
    <div class="qt-drawer qt-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="qt-view-head">
          <div>
            <div class="qt-view-num">{{ viewDoc.name }}</div>
            <div class="qt-view-sub">{{ viewDoc.customer_name || viewDoc.party_name }}</div>
          </div>
          <div style="text-align:right">
            <div class="qt-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="qt-badge" :class="statusClass(viewDoc)">{{ statusLabel(viewDoc) }}</span>
          </div>
          <button class="qt-dclose qt-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="qt-dbody">
          <div class="qt-meta-grid">
            <div><div class="qt-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
            <div><div class="qt-meta-lbl">Valid Till</div>
              <div class="mono-sm" :class="isExpired(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.valid_till)||'—' }}</div>
            </div>
          </div>
        </div>
        <div class="qt-dfooter">
          <button class="qt-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="qt-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, resolveCompany, apiLinkValues } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const activeTab = ref("all");
const tabs = [
  { key:"all",       label:"All"       },
  { key:"draft",     label:"Draft"     },
  { key:"submitted", label:"Submitted" },
  { key:"expired",   label:"Expired"   },
];

const list      = ref([]);
const loading   = ref(false);
const search    = ref("");
const selected  = ref(new Set());
const drawerOpen   = ref(false);
const drawerSaving = ref(false);
const editingName  = ref("");
const viewOpen  = ref(false);
const viewDoc   = ref(null);
const customers = ref([]);
const items     = ref([]);
const lines     = ref([]);
const sortCol   = ref("transaction_date");
const sortDir   = ref("desc");

let _lineId = 1;
const blankLine = () => ({ id:_lineId++, item_code:"", description:"", qty:1, rate:0, amount:0 });

const form = reactive({
  party_name: "", transaction_date: new Date().toISOString().slice(0,10),
  valid_till: "", tax_rate: 0, terms: "",
});

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Quotation", {
      fields:["name","party_name","customer_name","transaction_date","valid_till","grand_total","docstatus","status"],
      limit:200, order:"transaction_date desc",
    });
  } catch(e) { toast.error(e.message||"Failed to load quotations"); }
  finally { loading.value = false; }
}

const today = new Date().toISOString().slice(0,10);
function isExpired(q) { return q.valid_till && q.valid_till < today && q.docstatus !== 2; }
function statusLabel(q) {
  if (q.docstatus===2) return "Cancelled";
  if (q.docstatus===0) return "Draft";
  if (isExpired(q))    return "Expired";
  return q.status || "Submitted";
}
function statusClass(q) {
  if (q.docstatus===2) return "badge-grey";
  if (q.docstatus===0) return "badge-orange";
  if (isExpired(q))    return "badge-red";
  return "badge-blue";
}

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value === "draft")     r = r.filter(q => q.docstatus===0);
  if (activeTab.value === "submitted") r = r.filter(q => q.docstatus===1 && !isExpired(q));
  if (activeTab.value === "expired")   r = r.filter(q => isExpired(q));
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name||"").toLowerCase().includes(q) || (x.party_name||x.customer_name||"").toLowerCase().includes(q));
  }
  return r;
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a,b) => {
    const av=a[col]??"", bv=b[col]??"";
    const c = typeof av==="number" ? av-bv : String(av).localeCompare(String(bv));
    return sortDir.value==="asc" ? c : -c;
  });
});
function sort(col) {
  if (sortCol.value===col) sortDir.value = sortDir.value==="asc"?"desc":"asc";
  else { sortCol.value=col; sortDir.value="asc"; }
}
function sortArrow(col) {
  if (sortCol.value!==col) return '<span style="color:#d1d5db">⇅</span>';
  return sortDir.value==="asc"?"↑":"↓";
}

const counts = computed(()=>({
  draft:     list.value.filter(q=>q.docstatus===0).length,
  submitted: list.value.filter(q=>q.docstatus===1&&!isExpired(q)).length,
  expired:   list.value.filter(q=>isExpired(q)).length,
}));
const totalValue = computed(()=>list.value.filter(q=>q.docstatus===1).reduce((s,q)=>s+flt(q.grand_total),0));

function fmtCur(v) {
  return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));
}

const allChecked = computed(()=>sorted.value.length>0&&sorted.value.every(q=>selected.value.has(q.name)));
function toggle(n){const s=new Set(selected.value);s.has(n)?s.delete(n):s.add(n);selected.value=s;}
function toggleAll(e){selected.value=e.target.checked?new Set(sorted.value.map(q=>q.name)):new Set();}

function openNew() {
  editingName.value="";
  Object.assign(form,{party_name:"",transaction_date:new Date().toISOString().slice(0,10),valid_till:"",tax_rate:0,terms:""});
  lines.value=[blankLine()];
  fetchCustomers(""); fetchItems("");
  drawerOpen.value=true;
}
function openEdit(q) {
  editingName.value=q.name;
  Object.assign(form,{party_name:q.party_name||q.customer_name||"",transaction_date:q.transaction_date||"",valid_till:q.valid_till||"",tax_rate:0,terms:q.terms||""});
  lines.value=[blankLine()];
  fetchCustomers(""); fetchItems("");
  drawerOpen.value=true;
}
function openView(q){viewDoc.value=q;viewOpen.value=true;}

async function fetchCustomers(q="") {
  try { const r=await apiLinkValues("Customer",q); customers.value=r.map(x=>({label:x.name,value:x.name})); }
  catch { customers.value=[]; }
}
async function fetchItems(q="") {
  try { const r=await apiLinkValues("Item",q); items.value=r.map(x=>({label:x.name,value:x.name})); }
  catch { items.value=[]; }
}
function onItemSelect(line,val) {
  line.item_code=val;
  const it=items.value.find(x=>x.value===val);
  if (it?.rate) { line.rate=flt(it.rate); calcLine(line); }
}
function addLine(){lines.value.push(blankLine());}
function removeLine(id){if(lines.value.length>1)lines.value=lines.value.filter(l=>l.id!==id);}
function calcLine(l){l.amount=Math.round(flt(l.qty)*flt(l.rate)*100)/100;}

const subtotal  = computed(()=>lines.value.reduce((s,l)=>s+flt(l.amount),0));
const taxAmount = computed(()=>Math.round(subtotal.value*flt(form.tax_rate)/100*100)/100);

async function saveQuote(docstatus) {
  if (!form.party_name) return toast.error("Customer is required");
  if (!form.transaction_date) return toast.error("Date is required");
  drawerSaving.value=true;
  try {
    const company=await resolveCompany();
    const taxes=form.tax_rate>0?[{doctype:"Sales Taxes and Charges",charge_type:"On Net Total",rate:form.tax_rate,tax_amount:taxAmount.value,total:subtotal.value+taxAmount.value}]:[];
    const doc={
      doctype:"Quotation", company,
      quotation_to:"Customer", party_name:form.party_name,
      transaction_date:form.transaction_date, valid_till:form.valid_till||null,
      terms:form.terms||"", docstatus,
      items:lines.value.filter(l=>l.item_code).map(l=>({doctype:"Quotation Item",item_code:l.item_code,description:l.description||l.item_code,qty:flt(l.qty)||1,rate:flt(l.rate),amount:flt(l.amount)})),
      taxes,
    };
    if (editingName.value) doc.name=editingName.value;
    const saved=await apiSave(doc);
    toast.success(`Quotation ${saved?.name||""} ${docstatus?"submitted":"saved"}`);
    drawerOpen.value=false;
    await load();
  } catch(e) { toast.error(e.message||"Failed to save quotation"); }
  finally { drawerSaving.value=false; }
}

onMounted(load);
</script>

<style scoped>
.qt-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.qt-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.qt-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.qt-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.qt-pills{display:flex;gap:6px;}
.qt-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.qt-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.qt-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.qt-btn-primary:hover{background:#1d4ed8;}
.qt-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.qt-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.qt-btn-ghost:hover{background:#f9fafb;}
.qt-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.qt-btn-save:hover{background:#dcfce7;}
.qt-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.qt-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.qt-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.qt-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.qt-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.blue{color:#2563eb!important;}.red{color:#dc2626!important;}
.qt-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.qt-table{width:100%;border-collapse:collapse;font-size:13px;}
.qt-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.qt-table th.sortable{cursor:pointer;user-select:none;}
.qt-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.qt-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.qt-row:last-child td{border-bottom:none;}
.qt-row:hover td{background:#f9fafb;}
.qt-row.selected td{background:#eff6ff;}
.qt-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}
.text-muted{color:#6b7280;}.text-danger{color:#dc2626;}
.qt-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-blue{background:#dbeafe;color:#2563eb;}
.badge-orange{background:#fff7ed;color:#ea580c;}
.badge-red{background:#fee2e2;color:#dc2626;}
.badge-grey{background:#f3f4f6;color:#6b7280;}
.qt-act-cell{display:flex;gap:4px;justify-content:flex-end;cursor:default!important;}
.qt-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.qt-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.qt-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.qt-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.qt-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.qt-drawer{position:fixed;top:0;right:-560px;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.qt-drawer.open{right:0;}
.qt-view-drawer{width:440px;right:-440px;}
.qt-view-drawer.open{right:0;}
.qt-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.qt-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.qt-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.qt-dclose:hover{background:#f3f4f6;color:#111827;}
.qt-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.qt-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.qt-field{display:flex;flex-direction:column;gap:4px;}
.qt-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.qt-input{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.qt-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
textarea.qt-input{resize:vertical;}
.qt-section-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;padding-bottom:4px;border-bottom:1px solid #f3f4f6;}
.qt-items-table{display:flex;flex-direction:column;gap:0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;}
.qt-items-head{display:grid;grid-template-columns:2fr 2fr 80px 100px 100px 32px;gap:8px;background:#f9fafb;padding:8px 12px;font-size:11.5px;font-weight:600;color:#374151;}
.qt-items-row{display:grid;grid-template-columns:2fr 2fr 80px 100px 100px 32px;gap:8px;padding:8px 12px;border-top:1px solid #f3f4f6;align-items:center;}
.qt-add-line{background:transparent;border:none;color:#2563eb;font-size:12.5px;font-weight:600;cursor:pointer;padding:8px 12px;display:inline-flex;align-items:center;gap:6px;text-align:left;}
.qt-add-line:hover{background:#eff6ff;}
.qt-rm-line{background:transparent;border:1px solid #e5e7eb;border-radius:4px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#9ca3af;}
.qt-rm-line:hover{background:#fee2e2;color:#dc2626;border-color:#fca5a5;}
.qt-totals{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;}
.qt-totals-right{display:flex;flex-direction:column;gap:4px;min-width:220px;}
.qt-total-row{display:flex;justify-content:space-between;gap:16px;font-size:13px;color:#374151;padding:3px 0;}
.qt-total-row.grand{font-weight:700;font-size:14px;color:#111827;border-top:1px solid #e5e7eb;padding-top:6px;margin-top:2px;}
.qt-view-head{position:relative;display:flex;align-items:flex-start;justify-content:space-between;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#f0f9ff;}
.qt-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.qt-view-sub{font-size:13px;color:#6b7280;margin-top:2px;}
.qt-view-amount{font-size:22px;font-weight:800;font-family:monospace;color:#111827;}
.qt-vclose{position:absolute;top:12px;right:12px;}
.qt-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.qt-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.qt-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
