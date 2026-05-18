<template>
  <div class="bill-page">

    <div class="bill-actions">
      <div class="bill-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search bills…" class="bill-search-input" />
      </div>
      <div class="bill-pills">
        <button v-for="t in tabs" :key="t.key"
          class="bill-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="bill-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="bill-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Bill
        </button>
      </div>
    </div>

    <!-- Summary -->
    <div class="bill-summary" v-if="!loading">
      <div class="bill-sum-card"><div class="bill-sum-lbl">Draft</div><div class="bill-sum-val orange">{{ counts.draft }}</div></div>
      <div class="bill-sum-card"><div class="bill-sum-lbl">Unpaid</div><div class="bill-sum-val red">{{ fmtCur(totalUnpaid) }}</div></div>
      <div class="bill-sum-card"><div class="bill-sum-lbl">Overdue</div><div class="bill-sum-val red">{{ counts.overdue }}</div></div>
      <div class="bill-sum-card"><div class="bill-sum-lbl">Total Bills</div><div class="bill-sum-val">{{ list.length }}</div></div>
    </div>

    <!-- Table -->
    <div class="bill-card">
      <table class="bill-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sort('name')" class="sortable">Bill # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('supplier_name')" class="sortable">Vendor <span v-html="sortArrow('supplier_name')"></span></th>
            <th @click="sort('bill_no')" class="sortable">Vendor Bill # <span v-html="sortArrow('bill_no')"></span></th>
            <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
            <th @click="sort('due_date')" class="sortable">Due Date <span v-html="sortArrow('due_date')"></span></th>
            <th>Status</th>
            <th @click="sort('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:60px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="9"><div class="bill-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="b in sorted" :key="b.name" class="bill-row" :class="{selected:selected.has(b.name)}">
              <td><input type="checkbox" :checked="selected.has(b.name)" @change="toggle(b.name)" /></td>
              <td @click="openView(b)"><span class="bill-num">{{ b.name }}</span></td>
              <td @click="openView(b)">{{ b.supplier_name || b.supplier || '—' }}</td>
              <td @click="openView(b)" class="text-muted mono-sm">{{ b.bill_no||'—' }}</td>
              <td @click="openView(b)" class="text-muted mono-sm">{{ fmtDate(b.posting_date) }}</td>
              <td @click="openView(b)" :class="isOverdue(b)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(b.due_date)||'—' }}</td>
              <td @click="openView(b)"><span class="bill-badge" :class="statusClass(b)">{{ statusLabel(b) }}</span></td>
              <td @click="openView(b)" class="ta-r mono-sm">{{ fmtCur(b.grand_total) }}</td>
              <td class="bill-act-cell">
                <button class="bill-act-btn" @click="openView(b)"><span v-html="icon('eye',13)"></span></button>
                <button v-if="b.docstatus===0" class="bill-act-btn" @click="openEdit(b)"><span v-html="icon('edit',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="9" class="bill-empty">No bills found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create / Edit Drawer -->
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
              placeholder="Select vendor…" @search="fetchVendors" />
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
        </div>

        <div class="bill-section-title">Items</div>
        <div class="bill-items-table">
          <div class="bill-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="bill-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items"
              placeholder="Select item…" @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="bill-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="1" class="bill-input ta-r" @input="calcLine(line)" /></div>
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

    <!-- View Drawer -->
    <div v-if="viewOpen" class="bill-overlay" @click.self="viewOpen=false"></div>
    <div class="bill-drawer bill-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="bill-view-head">
          <div>
            <div class="bill-view-num">{{ viewDoc.name }}</div>
            <div class="bill-view-sub">{{ viewDoc.supplier_name||viewDoc.supplier }}</div>
          </div>
          <div style="text-align:right">
            <div class="bill-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="bill-badge" :class="statusClass(viewDoc)">{{ statusLabel(viewDoc) }}</span>
          </div>
          <button class="bill-dclose bill-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="bill-dbody">
          <div class="bill-meta-grid">
            <div><div class="bill-meta-lbl">Bill Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
            <div><div class="bill-meta-lbl">Due Date</div>
              <div class="mono-sm" :class="isOverdue(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.due_date)||'—' }}</div>
            </div>
            <div><div class="bill-meta-lbl">Vendor Bill #</div><div class="mono-sm">{{ viewDoc.bill_no||'—' }}</div></div>
            <div><div class="bill-meta-lbl">Outstanding</div><div class="mono-sm red">{{ fmtCur(viewDoc.outstanding_amount) }}</div></div>
          </div>
        </div>
        <div class="bill-dfooter">
          <button class="bill-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="bill-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiSubmit, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const activeTab=ref("all");
const tabs=[{key:"all",label:"All"},{key:"draft",label:"Draft"},{key:"unpaid",label:"Unpaid"},{key:"overdue",label:"Overdue"},{key:"paid",label:"Paid"}];

const list=ref([]),loading=ref(false),search=ref(""),selected=ref(new Set());
const drawerOpen=ref(false),drawerSaving=ref(false),editingName=ref("");
const viewOpen=ref(false),viewDoc=ref(null);
const vendors=ref([]),items=ref([]),lines=ref([]),taxAccountHead=ref("");
const sortCol=ref("posting_date"),sortDir=ref("desc");

let _id=1;
const blankLine=()=>({id:_id++,item_code:"",description:"",qty:1,rate:0,amount:0});
const form=reactive({supplier:"",posting_date:new Date().toISOString().slice(0,10),due_date:"",bill_no:"",bill_date:"",tax_rate:0,remarks:""});

async function load(){
  loading.value=true;
  try{list.value=await apiList("Purchase Invoice",{fields:["name","supplier","supplier_name","posting_date","due_date","bill_no","grand_total","outstanding_amount","docstatus","status"],limit:200,order:"posting_date desc"});}
  catch(e){toast.error(e.message||"Failed to load bills");}
  finally{loading.value=false;}
}
async function loadTaxAccount(){
  try{
    const r=await apiList("Account",{fields:["name"],filters:[["account_type","=","Tax"],["is_group","=",0]],limit:1});
    if(r?.length) taxAccountHead.value=r[0].name;
  }catch{}
}

const today=new Date().toISOString().slice(0,10);
function isOverdue(b){return b.due_date&&b.due_date<today&&b.docstatus===1&&flt(b.outstanding_amount)>0;}
function statusLabel(b){
  if(b.docstatus===2) return "Cancelled";
  if(b.docstatus===0) return "Draft";
  if(flt(b.outstanding_amount)<=0) return "Paid";
  if(isOverdue(b)) return "Overdue";
  return "Unpaid";
}
function statusClass(b){
  if(b.docstatus===2) return "badge-grey";
  if(b.docstatus===0) return "badge-orange";
  if(statusLabel(b)==="Paid") return "badge-green";
  if(statusLabel(b)==="Overdue") return "badge-red";
  return "badge-yellow";
}

const filtered=computed(()=>{
  let r=list.value;
  if(activeTab.value==="draft")  r=r.filter(b=>b.docstatus===0);
  if(activeTab.value==="unpaid") r=r.filter(b=>b.docstatus===1&&flt(b.outstanding_amount)>0&&!isOverdue(b));
  if(activeTab.value==="overdue") r=r.filter(b=>isOverdue(b));
  if(activeTab.value==="paid")   r=r.filter(b=>b.docstatus===1&&flt(b.outstanding_amount)<=0);
  if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(x=>(x.name||"").toLowerCase().includes(q)||(x.supplier_name||x.supplier||"").toLowerCase().includes(q)||(x.bill_no||"").toLowerCase().includes(q));}
  return r;
});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const counts=computed(()=>({draft:list.value.filter(b=>b.docstatus===0).length,overdue:list.value.filter(b=>isOverdue(b)).length}));
const totalUnpaid=computed(()=>list.value.filter(b=>b.docstatus===1).reduce((s,b)=>s+flt(b.outstanding_amount),0));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
const allChecked=computed(()=>sorted.value.length>0&&sorted.value.every(b=>selected.value.has(b.name)));
function toggle(n){const s=new Set(selected.value);s.has(n)?s.delete(n):s.add(n);selected.value=s;}
function toggleAll(e){selected.value=e.target.checked?new Set(sorted.value.map(b=>b.name)):new Set();}

function openNew(){editingName.value="";Object.assign(form,{supplier:"",posting_date:new Date().toISOString().slice(0,10),due_date:"",bill_no:"",bill_date:"",tax_rate:0,remarks:""});lines.value=[blankLine()];fetchVendors("");fetchItems("");drawerOpen.value=true;}
async function openEdit(b){
  editingName.value=b.name;
  Object.assign(form,{supplier:b.supplier||"",posting_date:b.posting_date||"",due_date:b.due_date||"",bill_no:b.bill_no||"",bill_date:b.bill_date||"",tax_rate:0,remarks:b.remarks||""});
  lines.value=[blankLine()];
  fetchVendors("");fetchItems("");
  drawerOpen.value=true;
  try{
    const doc=await apiGet("Purchase Invoice",b.name);
    if(doc?.items?.length) lines.value=doc.items.map(i=>({id:_id++,item_code:i.item_code||"",description:i.description||"",qty:i.qty||1,rate:i.rate||0,amount:i.amount||0}));
    if(doc?.taxes?.[0]?.rate) form.tax_rate=doc.taxes[0].rate;
    if(doc?.taxes?.[0]?.account_head) taxAccountHead.value=doc.taxes[0].account_head;
  }catch{}
}
function openView(b){viewDoc.value=b;viewOpen.value=true;}
async function fetchVendors(q=""){try{const r=await apiList("Supplier",{fields:["name","supplier_name"],filters:q?[["supplier_name","like","%"+q+"%"]]:[],limit:30,order:"supplier_name asc"});vendors.value=r.map(x=>({label:x.supplier_name||x.name,value:x.name}));}catch{vendors.value=[];}}
async function fetchItems(q=""){try{const r=await apiList("Item",{fields:["name","item_name","standard_rate","stock_uom"],filters:q?[["item_name","like","%"+q+"%"]]:[],limit:30,order:"item_name asc"});items.value=r.map(x=>({label:x.item_name||x.name,value:x.name,rate:x.standard_rate||0}));}catch{items.value=[];}}
function onItemSelect(line,opt){line.item_code=opt?.value??opt;if(opt?.rate){line.rate=Number(opt.rate)||0;calcLine(line);}}
function addLine(){lines.value.push(blankLine());}
function removeLine(id){if(lines.value.length>1)lines.value=lines.value.filter(l=>l.id!==id);}
function calcLine(l){l.amount=Math.round(flt(l.qty)*flt(l.rate)*100)/100;}
const subtotal=computed(()=>lines.value.reduce((s,l)=>s+flt(l.amount),0));
const taxAmount=computed(()=>Math.round(subtotal.value*flt(form.tax_rate)/100*100)/100);

async function saveBill(submit){
  if(!form.supplier) return toast.error("Vendor is required");
  drawerSaving.value=true;
  try{
    const company=await resolveCompany();
    const taxes=form.tax_rate>0&&taxAccountHead.value?[{doctype:"Tax Line",charge_type:"On Net Total",account_head:taxAccountHead.value,description:taxAccountHead.value,rate:form.tax_rate}]:[];
    const doc={doctype:"Purchase Invoice",company,supplier:form.supplier,posting_date:form.posting_date,due_date:form.due_date||null,bill_no:form.bill_no||"",bill_date:form.bill_date||null,remarks:form.remarks||"",
      items:lines.value.filter(l=>l.item_code).map(l=>({doctype:"Purchase Invoice Item",item_code:l.item_code,description:l.description||l.item_code,qty:flt(l.qty)||1,rate:flt(l.rate),amount:flt(l.amount)})),taxes};
    if(editingName.value) doc.name=editingName.value;
    const saved=await apiSave(doc);
    if(submit&&saved?.name) await apiSubmit("Purchase Invoice",saved.name);
    toast.success(`Bill ${saved?.name||""} ${submit?"submitted":"saved"}`);
    drawerOpen.value=false;await load();
  }catch(e){toast.error(e.message||"Failed to save bill");}
  finally{drawerSaving.value=false;}
}
onMounted(()=>{load();loadTaxAccount();});
</script>

<style scoped>
.bill-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.bill-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.bill-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.bill-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.bill-pills{display:flex;gap:6px;}
.bill-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.bill-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.bill-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.bill-btn-primary:hover{background:#1d4ed8;}.bill-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.bill-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.bill-btn-ghost:hover{background:#f9fafb;}
.bill-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.bill-btn-save:hover{background:#dcfce7;}.bill-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.bill-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.bill-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.bill-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.bill-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.orange{color:#ea580c!important;}.red{color:#dc2626!important;}.green{color:#16a34a!important;}
.bill-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.bill-table{width:100%;border-collapse:collapse;font-size:13px;}
.bill-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.bill-table th.sortable{cursor:pointer;user-select:none;}.bill-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.bill-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.bill-row:last-child td{border-bottom:none;}.bill-row:hover td{background:#f9fafb;}.bill-row.selected td{background:#eff6ff;}
.bill-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}.text-danger{color:#dc2626;}
.bill-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-yellow{background:#fefce8;color:#ca8a04;}
.badge-orange{background:#fff7ed;color:#ea580c;}.badge-red{background:#fee2e2;color:#dc2626;}
.badge-grey{background:#f3f4f6;color:#6b7280;}
.bill-act-cell{display:flex;gap:4px;justify-content:flex-end;cursor:default!important;}
.bill-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.bill-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.bill-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.bill-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.bill-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.bill-drawer{position:fixed;top:0;right:-560px;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.bill-drawer.open{right:0;}
.bill-view-drawer{width:440px;right:-440px;}.bill-view-drawer.open{right:0;}
.bill-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.bill-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.bill-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.bill-dclose:hover{background:#f3f4f6;color:#111827;}
.bill-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.bill-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.bill-field{display:flex;flex-direction:column;gap:4px;}
.bill-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.bill-input{width:100%;box-sizing:border-box;border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.bill-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
textarea.bill-input{resize:vertical;}
.bill-section-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;padding-bottom:4px;border-bottom:1px solid #f3f4f6;}
.bill-items-table{display:flex;flex-direction:column;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;}
.bill-items-head{display:grid;grid-template-columns:2fr 2fr 80px 100px 100px 32px;gap:8px;background:#f9fafb;padding:8px 12px;font-size:11.5px;font-weight:600;color:#374151;}
.bill-items-row{display:grid;grid-template-columns:2fr 2fr 80px 100px 100px 32px;gap:8px;padding:8px 12px;border-top:1px solid #f3f4f6;align-items:center;}
.bill-add-line{background:transparent;border:none;color:#2563eb;font-size:12.5px;font-weight:600;cursor:pointer;padding:8px 12px;display:inline-flex;align-items:center;gap:6px;}
.bill-add-line:hover{background:#eff6ff;}
.bill-rm-line{background:transparent;border:1px solid #e5e7eb;border-radius:4px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#9ca3af;}
.bill-rm-line:hover{background:#fee2e2;color:#dc2626;border-color:#fca5a5;}
.bill-totals{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;}
.bill-totals-right{display:flex;flex-direction:column;gap:4px;min-width:220px;}
.bill-total-row{display:flex;justify-content:space-between;gap:16px;font-size:13px;color:#374151;padding:3px 0;}
.bill-total-row.grand{font-weight:700;font-size:14px;color:#111827;border-top:1px solid #e5e7eb;padding-top:6px;margin-top:2px;}
.bill-view-head{position:relative;display:flex;align-items:flex-start;justify-content:space-between;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#fff7ed;}
.bill-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.bill-view-sub{font-size:13px;color:#6b7280;margin-top:2px;}
.bill-view-amount{font-size:22px;font-weight:800;font-family:monospace;color:#111827;}
.bill-vclose{position:absolute;top:12px;right:12px;}
.bill-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.bill-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.bill-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
