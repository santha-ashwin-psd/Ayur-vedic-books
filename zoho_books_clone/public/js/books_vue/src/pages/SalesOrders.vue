<template>
  <div class="so-page">

    <div class="so-actions">
      <div class="so-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search sales orders…" class="so-search-input" />
      </div>
      <div class="so-pills">
        <button v-for="t in tabs" :key="t.key"
          class="so-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="so-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="so-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Sales Order
        </button>
      </div>
    </div>

    <!-- Summary -->
    <div class="so-summary" v-if="!loading">
      <div class="so-sum-card"><div class="so-sum-lbl">Draft</div><div class="so-sum-val orange">{{ counts.draft }}</div></div>
      <div class="so-sum-card"><div class="so-sum-lbl">To Deliver</div><div class="so-sum-val blue">{{ counts.toDeliver }}</div></div>
      <div class="so-sum-card"><div class="so-sum-lbl">Completed</div><div class="so-sum-val green">{{ counts.completed }}</div></div>
      <div class="so-sum-card"><div class="so-sum-lbl">Total Value</div><div class="so-sum-val">{{ fmtCur(totalValue) }}</div></div>
    </div>

    <!-- Table -->
    <div class="so-card">
      <table class="so-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sort('name')" class="sortable">Order # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('customer_name')" class="sortable">Customer <span v-html="sortArrow('customer_name')"></span></th>
            <th @click="sort('transaction_date')" class="sortable">Date <span v-html="sortArrow('transaction_date')"></span></th>
            <th @click="sort('delivery_date')" class="sortable">Delivery Date <span v-html="sortArrow('delivery_date')"></span></th>
            <th>Status</th>
            <th @click="sort('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:60px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="8"><div class="so-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="o in sorted" :key="o.name" class="so-row" :class="{selected:selected.has(o.name)}">
              <td><input type="checkbox" :checked="selected.has(o.name)" @change="toggle(o.name)" /></td>
              <td @click="openView(o)"><span class="so-num">{{ o.name }}</span></td>
              <td @click="openView(o)">{{ o.customer_name || '—' }}</td>
              <td @click="openView(o)" class="text-muted mono-sm">{{ fmtDate(o.transaction_date) }}</td>
              <td @click="openView(o)" :class="isPastDelivery(o)?'text-danger':'text-muted'" class="mono-sm">
                {{ fmtDate(o.delivery_date)||'—' }}
              </td>
              <td @click="openView(o)"><span class="so-badge" :class="statusClass(o)">{{ statusLabel(o) }}</span></td>
              <td @click="openView(o)" class="ta-r mono-sm">{{ fmtCur(o.grand_total) }}</td>
              <td class="so-act-cell">
                <button class="so-act-btn" @click="openView(o)"><span v-html="icon('eye',13)"></span></button>
                <button v-if="o.docstatus===0" class="so-act-btn" @click="openEdit(o)"><span v-html="icon('edit',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="so-empty">No sales orders found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit Drawer -->
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
            <SearchableSelect v-model="form.customer" :options="customers"
              placeholder="Select customer…" :createable="true" createDoctype="Customer"
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
        </div>

        <div class="so-section-title">Items</div>
        <div class="so-items-table">
          <div class="so-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="so-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items"
              placeholder="Select item…" :createable="true" createDoctype="Item"
              @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="so-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="1" class="so-input ta-r" @input="calcLine(line)" /></div>
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
          <label class="so-label">Terms & Notes</label>
          <textarea v-model="form.terms" rows="2" class="so-input" placeholder="Optional…"></textarea>
        </div>
      </div>
      <div class="so-dfooter">
        <button class="so-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="so-btn-save" :disabled="drawerSaving" @click="saveOrder(0)">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="so-btn-primary" :disabled="drawerSaving" @click="saveOrder(1)">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}
        </button>
      </div>
    </div>

    <!-- View Drawer -->
    <div v-if="viewOpen" class="so-overlay" @click.self="viewOpen=false"></div>
    <div class="so-drawer so-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="so-view-head">
          <div>
            <div class="so-view-num">{{ viewDoc.name }}</div>
            <div class="so-view-sub">{{ viewDoc.customer_name }}</div>
          </div>
          <div style="text-align:right">
            <div class="so-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="so-badge" :class="statusClass(viewDoc)">{{ statusLabel(viewDoc) }}</span>
          </div>
          <button class="so-dclose so-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="so-dbody">
          <div class="so-meta-grid">
            <div><div class="so-meta-lbl">Order Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
            <div><div class="so-meta-lbl">Delivery Date</div>
              <div class="mono-sm" :class="isPastDelivery(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.delivery_date)||'—' }}</div>
            </div>
          </div>
        </div>
        <div class="so-dfooter">
          <button class="so-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="so-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button v-if="viewDoc.docstatus===1" class="so-btn-convert" :disabled="converting" @click="convertToInvoice(viewDoc)">
            <span v-html="icon('plus',13)"></span> {{ converting ? 'Creating…' : 'Convert to Invoice' }}
          </button>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRouter } from "vue-router";
import { apiList, apiGet, apiSave, apiSubmit, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const router = useRouter();

const { toast } = useToast();
const taxAccountHead=ref("");
async function loadTaxAccount(){try{const co=await resolveCompany();const r=await apiList("Account",{fields:["name"],filters:[["company","=",co],["account_type","=","Tax"],["is_group","=",0]],limit:1});taxAccountHead.value=r[0]?.name||"";}catch{}}
const activeTab = ref("all");
const tabs = [
  {key:"all",label:"All"},{key:"draft",label:"Draft"},
  {key:"to-deliver",label:"To Deliver"},{key:"completed",label:"Completed"},
];

const list=ref([]),loading=ref(false),search=ref(""),selected=ref(new Set());
const drawerOpen=ref(false),drawerSaving=ref(false),editingName=ref("");
const viewOpen=ref(false),viewDoc=ref(null);
const customers=ref([]),items=ref([]),lines=ref([]);
const sortCol=ref("transaction_date"),sortDir=ref("desc");

let _id=1;
const blankLine=()=>({id:_id++,item_code:"",description:"",qty:1,rate:0,amount:0});
const form=reactive({customer:"",transaction_date:new Date().toISOString().slice(0,10),delivery_date:"",tax_rate:0,terms:""});

async function load(){
  loading.value=true;
  try{const co=await resolveCompany();list.value=await apiList("Sales Order",{fields:["name","customer","customer_name","transaction_date","delivery_date","grand_total","docstatus","status"],filters:[["company","=",co]],limit:200,order:"transaction_date desc"});}
  catch(e){toast.error(e.message||"Failed to load sales orders");}
  finally{loading.value=false;}
}

const today=new Date().toISOString().slice(0,10);
function isPastDelivery(o){return o.delivery_date&&o.delivery_date<today&&o.docstatus===1;}
function statusLabel(o){
  if(o.docstatus===2) return "Cancelled";
  if(o.docstatus===0) return "Draft";
  const s=o.status||"";
  if(s==="Completed") return "Completed";
  if(s.includes("Deliver")) return "To Deliver";
  return s||"Submitted";
}
function statusClass(o){
  if(o.docstatus===2) return "badge-grey";
  if(o.docstatus===0) return "badge-orange";
  const s=statusLabel(o);
  if(s==="Completed") return "badge-green";
  return "badge-blue";
}

const filtered=computed(()=>{
  let r=list.value;
  if(activeTab.value==="draft")       r=r.filter(o=>o.docstatus===0);
  if(activeTab.value==="to-deliver")  r=r.filter(o=>o.docstatus===1&&statusLabel(o)==="To Deliver");
  if(activeTab.value==="completed")   r=r.filter(o=>statusLabel(o)==="Completed");
  if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(o=>(o.name||"").toLowerCase().includes(q)||(o.customer_name||"").toLowerCase().includes(q));}
  return r;
});
const sorted=computed(()=>{
  const col=sortCol.value;
  return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});
});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const counts=computed(()=>({draft:list.value.filter(o=>o.docstatus===0).length,toDeliver:list.value.filter(o=>o.docstatus===1&&statusLabel(o)==="To Deliver").length,completed:list.value.filter(o=>statusLabel(o)==="Completed").length}));
const totalValue=computed(()=>list.value.filter(o=>o.docstatus===1).reduce((s,o)=>s+flt(o.grand_total),0));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
const allChecked=computed(()=>sorted.value.length>0&&sorted.value.every(o=>selected.value.has(o.name)));
function toggle(n){const s=new Set(selected.value);s.has(n)?s.delete(n):s.add(n);selected.value=s;}
function toggleAll(e){selected.value=e.target.checked?new Set(sorted.value.map(o=>o.name)):new Set();}

function openNew(){editingName.value="";Object.assign(form,{customer:"",transaction_date:new Date().toISOString().slice(0,10),delivery_date:"",tax_rate:0,terms:""});lines.value=[blankLine()];fetchCustomers("");fetchItems("");drawerOpen.value=true;}
async function openEdit(o){editingName.value=o.name;fetchCustomers("");fetchItems("");try{const doc=await apiGet("Sales Order",o.name);Object.assign(form,{customer:doc.customer||"",transaction_date:doc.transaction_date||"",delivery_date:doc.delivery_date||"",tax_rate:doc.taxes?.[0]?.rate||0,terms:doc.terms||""});lines.value=(doc.items||[]).map(it=>({id:_id++,item_code:it.item_code||"",description:it.description||"",qty:flt(it.qty)||1,rate:flt(it.rate),amount:flt(it.amount)}));if(!lines.value.length)lines.value=[blankLine()];}catch{Object.assign(form,{customer:o.customer||"",transaction_date:o.transaction_date||"",delivery_date:o.delivery_date||"",tax_rate:0,terms:o.terms||""});lines.value=[blankLine()];}drawerOpen.value=true;}
function openView(o){viewDoc.value=o;viewOpen.value=true;}

const converting = ref(false);
async function convertToInvoice(o) {
  converting.value = true;
  try {
    const doc = await apiGet("Sales Order", o.name);
    const company = await resolveCompany();
    const today = new Date().toISOString().slice(0, 10);
    const inv = {
      doctype: "Sales Invoice",
      company,
      customer: doc.customer,
      customer_name: doc.customer_name || doc.customer,
      posting_date: today,
      due_date: today,
      items: (doc.items || []).map(it => ({
        doctype: "Sales Invoice Item",
        item_code: it.item_code,
        item_name: it.item_name || it.item_code,
        description: it.description || it.item_code,
        qty: flt(it.qty) || 1,
        rate: flt(it.rate),
        amount: flt(it.amount),
      })),
      taxes: (doc.taxes || []).map(t => ({ ...t, doctype: "Tax Line", name: undefined, parent: undefined })),
      terms: doc.terms || "",
      remarks: `Created from Sales Order ${doc.name}`,
    };
    const saved = await apiSave(inv);
    toast.success(`Invoice ${saved.name} created from ${doc.name}`);
    viewOpen.value = false;
    router.push("/invoices");
  } catch (e) { toast.error(e.message || "Failed to convert"); }
  finally { converting.value = false; }
}
async function fetchCustomers(q=""){try{const f=[["disabled","=",0]];if(q)f.push(["customer_name","like","%"+q+"%"]);const r=await apiList("Customer",{fields:["name","customer_name"],filters:f,limit:30,order:"customer_name asc"});customers.value=r.map(x=>({label:x.customer_name||x.name,value:x.name}));}catch{customers.value=[];}}
async function fetchItems(q=""){try{const f=[["disabled","=",0]];if(q)f.push(["item_name","like","%"+q+"%"]);const r=await apiList("Item",{fields:["name","item_name","standard_rate","stock_uom"],filters:f,limit:30,order:"item_name asc"});items.value=r.map(x=>({label:x.item_name||x.name,value:x.name,rate:x.standard_rate||0}));}catch{items.value=[];}}
function onItemSelect(line,opt){line.item_code=opt?.value??opt;if(opt?.rate){line.rate=Number(opt.rate)||0;calcLine(line);}}
function addLine(){lines.value.push(blankLine());}
function removeLine(id){if(lines.value.length>1)lines.value=lines.value.filter(l=>l.id!==id);}
function calcLine(l){l.amount=Math.round(flt(l.qty)*flt(l.rate)*100)/100;}
const subtotal=computed(()=>lines.value.reduce((s,l)=>s+flt(l.amount),0));
const taxAmount=computed(()=>Math.round(subtotal.value*flt(form.tax_rate)/100*100)/100);

async function saveOrder(submit){
  if(!form.customer) return toast.error("Customer is required");
  drawerSaving.value=true;
  try{
    const company=await resolveCompany();
    const taxes=form.tax_rate>0?[{doctype:"Tax Line",charge_type:"On Net Total",rate:form.tax_rate,account_head:taxAccountHead.value,description:`Tax @ ${form.tax_rate}%`}]:[];
    const doc={doctype:"Sales Order",company,customer:form.customer,transaction_date:form.transaction_date,delivery_date:form.delivery_date||null,terms:form.terms||"",
      items:lines.value.filter(l=>l.item_code).map(l=>({doctype:"Sales Order Item",item_code:l.item_code,description:l.description||l.item_code,qty:flt(l.qty)||1,rate:flt(l.rate),amount:flt(l.amount),delivery_date:form.delivery_date||null})),taxes};
    if(editingName.value) doc.name=editingName.value;
    const saved=await apiSave(doc);
    if(submit) await apiSubmit("Sales Order",saved.name);
    toast.success(`Sales Order ${saved?.name||""} ${submit?"submitted":"saved"}`);
    drawerOpen.value=false;await load();
  }catch(e){toast.error(e.message||"Failed to save sales order");}
  finally{drawerSaving.value=false;}
}
onMounted(()=>{load();loadTaxAccount();});
</script>

<style scoped>
.so-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.so-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.so-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.so-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.so-pills{display:flex;gap:6px;}
.so-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.so-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.so-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.so-btn-primary:hover{background:#1d4ed8;}.so-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.so-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.so-btn-ghost:hover{background:#f9fafb;}
.so-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.so-btn-save:hover{background:#dcfce7;}.so-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.so-btn-convert{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.so-btn-convert:hover{background:#1d4ed8;}.so-btn-convert:disabled{opacity:.5;cursor:not-allowed;}
.so-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.so-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.so-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.so-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.orange{color:#ea580c!important;}.blue{color:#2563eb!important;}.green{color:#16a34a!important;}
.so-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.so-table{width:100%;border-collapse:collapse;font-size:13px;}
.so-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.so-table th.sortable{cursor:pointer;user-select:none;}.so-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.so-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.so-row:last-child td{border-bottom:none;}.so-row:hover td{background:#f9fafb;}.so-row.selected td{background:#eff6ff;}
.so-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}.text-danger{color:#dc2626;}
.so-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-blue{background:#dbeafe;color:#2563eb;}.badge-orange{background:#fff7ed;color:#ea580c;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.so-act-cell{display:flex;gap:4px;justify-content:flex-end;cursor:default!important;}
.so-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.so-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.so-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.so-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.so-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.so-drawer{position:fixed;top:0;right:-560px;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.so-drawer.open{right:0;}
.so-view-drawer{width:440px;right:-440px;}.so-view-drawer.open{right:0;}
.so-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.so-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.so-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.so-dclose:hover{background:#f3f4f6;color:#111827;}
.so-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.so-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.so-field{display:flex;flex-direction:column;gap:4px;}
.so-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.so-input{width:100%;box-sizing:border-box;border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.so-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
textarea.so-input{resize:vertical;}
.so-section-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;padding-bottom:4px;border-bottom:1px solid #f3f4f6;}
.so-items-table{display:flex;flex-direction:column;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;}
.so-items-head{display:grid;grid-template-columns:2fr 2fr 80px 100px 100px 32px;gap:8px;background:#f9fafb;padding:8px 12px;font-size:11.5px;font-weight:600;color:#374151;}
.so-items-row{display:grid;grid-template-columns:2fr 2fr 80px 100px 100px 32px;gap:8px;padding:8px 12px;border-top:1px solid #f3f4f6;align-items:center;}
.so-add-line{background:transparent;border:none;color:#2563eb;font-size:12.5px;font-weight:600;cursor:pointer;padding:8px 12px;display:inline-flex;align-items:center;gap:6px;}
.so-add-line:hover{background:#eff6ff;}
.so-rm-line{background:transparent;border:1px solid #e5e7eb;border-radius:4px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#9ca3af;}
.so-rm-line:hover{background:#fee2e2;color:#dc2626;border-color:#fca5a5;}
.so-totals{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;}
.so-totals-right{display:flex;flex-direction:column;gap:4px;min-width:220px;}
.so-total-row{display:flex;justify-content:space-between;gap:16px;font-size:13px;color:#374151;padding:3px 0;}
.so-total-row.grand{font-weight:700;font-size:14px;color:#111827;border-top:1px solid #e5e7eb;padding-top:6px;margin-top:2px;}
.so-view-head{position:relative;display:flex;align-items:flex-start;justify-content:space-between;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#f0f9ff;}
.so-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.so-view-sub{font-size:13px;color:#6b7280;margin-top:2px;}
.so-view-amount{font-size:22px;font-weight:800;font-family:monospace;color:#111827;}
.so-vclose{position:absolute;top:12px;right:12px;}
.so-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.so-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.so-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
