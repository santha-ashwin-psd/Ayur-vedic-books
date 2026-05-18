<template>
  <div class="po-page">
    <div class="po-actions">
      <div class="po-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search purchase orders…" class="po-search-input" />
      </div>
      <div class="po-pills">
        <button v-for="t in tabs" :key="t.key" class="po-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="po-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="po-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Purchase Order</button>
      </div>
    </div>

    <div class="po-summary" v-if="!loading">
      <div class="po-sum-card"><div class="po-sum-lbl">Draft</div><div class="po-sum-val orange">{{ counts.draft }}</div></div>
      <div class="po-sum-card"><div class="po-sum-lbl">To Receive</div><div class="po-sum-val blue">{{ counts.toReceive }}</div></div>
      <div class="po-sum-card"><div class="po-sum-lbl">Completed</div><div class="po-sum-val green">{{ counts.completed }}</div></div>
      <div class="po-sum-card"><div class="po-sum-lbl">Total Value</div><div class="po-sum-val">{{ fmtCur(totalValue) }}</div></div>
    </div>

    <div class="po-card">
      <table class="po-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sort('name')" class="sortable">Order # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('supplier_name')" class="sortable">Vendor <span v-html="sortArrow('supplier_name')"></span></th>
            <th @click="sort('transaction_date')" class="sortable">Date <span v-html="sortArrow('transaction_date')"></span></th>
            <th @click="sort('expected_delivery_date')" class="sortable">Expected By <span v-html="sortArrow('expected_delivery_date')"></span></th>
            <th>Status</th>
            <th @click="sort('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:50px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="8"><div class="po-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="o in sorted" :key="o.name" class="po-row" :class="{selected:selected.has(o.name)}">
              <td><input type="checkbox" :checked="selected.has(o.name)" @change="toggle(o.name)" /></td>
              <td @click="openView(o)"><span class="po-num">{{ o.name }}</span></td>
              <td @click="openView(o)">{{ o.supplier_name||o.supplier||'—' }}</td>
              <td @click="openView(o)" class="text-muted mono-sm">{{ fmtDate(o.transaction_date) }}</td>
              <td @click="openView(o)" class="text-muted mono-sm">{{ fmtDate(o.expected_delivery_date)||'—' }}</td>
              <td @click="openView(o)"><span class="po-badge" :class="statusClass(o)">{{ statusLabel(o) }}</span></td>
              <td @click="openView(o)" class="ta-r mono-sm">{{ fmtCur(o.grand_total) }}</td>
              <td class="po-act-cell">
                <button class="po-act-btn" @click="openView(o)"><span v-html="icon('eye',13)"></span></button>
                <button v-if="o.docstatus===0" class="po-act-btn" @click="openEdit(o)"><span v-html="icon('edit',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="po-empty">No purchase orders found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Drawer -->
    <div v-if="drawerOpen" class="po-overlay" @click.self="drawerOpen=false"></div>
    <div class="po-drawer" :class="{open:drawerOpen}">
      <div class="po-dheader">
        <div class="po-dheader-title">{{ editingName?'Edit Purchase Order':'New Purchase Order' }}</div>
        <button class="po-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="po-dbody">
        <div class="po-fields-grid">
          <div class="po-field" style="grid-column:1/-1">
            <label class="po-label">Vendor <span class="req">*</span></label>
            <SearchableSelect v-model="form.supplier" :options="vendors" placeholder="Select vendor…" @search="fetchVendors" />
          </div>
          <div class="po-field">
            <label class="po-label">Order Date <span class="req">*</span></label>
            <input v-model="form.transaction_date" type="date" class="po-input" />
          </div>
          <div class="po-field">
            <label class="po-label">Expected Delivery</label>
            <input v-model="form.expected_delivery_date" type="date" class="po-input" />
          </div>
        </div>

        <div class="po-section-title">Items</div>
        <div class="po-items-table">
          <div class="po-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="po-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items" placeholder="Item…" @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="po-input" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="1" class="po-input ta-r" @input="calcLine(line)" /></div>
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
          <label class="po-label">Terms</label>
          <textarea v-model="form.terms" rows="2" class="po-input" placeholder="Terms & conditions…"></textarea>
        </div>
      </div>
      <div class="po-dfooter">
        <button class="po-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="po-btn-save" :disabled="drawerSaving" @click="saveOrder(0)"><span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}</button>
        <button class="po-btn-primary" :disabled="drawerSaving" @click="saveOrder(1)"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}</button>
      </div>
    </div>

    <!-- View -->
    <div v-if="viewOpen" class="po-overlay" @click.self="viewOpen=false"></div>
    <div class="po-drawer po-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="po-view-head">
          <div><div class="po-view-num">{{ viewDoc.name }}</div><div class="po-view-sub">{{ viewDoc.supplier_name||viewDoc.supplier }}</div></div>
          <div style="text-align:right"><div class="po-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div><span class="po-badge" :class="statusClass(viewDoc)">{{ statusLabel(viewDoc) }}</span></div>
          <button class="po-dclose po-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="po-dbody">
          <div class="po-meta-grid">
            <div><div class="po-meta-lbl">Order Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
            <div><div class="po-meta-lbl">Expected By</div><div class="mono-sm">{{ fmtDate(viewDoc.expected_delivery_date)||'—' }}</div></div>
          </div>
        </div>
        <div class="po-dfooter">
          <button class="po-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="po-btn-save" @click="openEdit(viewDoc);viewOpen=false"><span v-html="icon('edit',13)"></span> Edit</button>
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
const tabs=[{key:"all",label:"All"},{key:"draft",label:"Draft"},{key:"to-receive",label:"To Receive"},{key:"completed",label:"Completed"}];
const list=ref([]),loading=ref(false),search=ref(""),selected=ref(new Set());
const drawerOpen=ref(false),drawerSaving=ref(false),editingName=ref("");
const viewOpen=ref(false),viewDoc=ref(null);
const vendors=ref([]),items=ref([]),lines=ref([]),taxAccountHead=ref("");
const sortCol=ref("transaction_date"),sortDir=ref("desc");
let _id=1;
const blankLine=()=>({id:_id++,item_code:"",description:"",qty:1,rate:0,amount:0});
const form=reactive({supplier:"",transaction_date:new Date().toISOString().slice(0,10),expected_delivery_date:"",tax_rate:0,terms:""});

async function load(){loading.value=true;try{list.value=await apiList("Purchase Order",{fields:["name","supplier","supplier_name","transaction_date","expected_delivery_date","grand_total","docstatus","status"],limit:200,order:"transaction_date desc"});}catch(e){toast.error(e.message||"Failed to load purchase orders");}finally{loading.value=false;}}
async function loadTaxAccount(){try{const r=await apiList("Account",{fields:["name"],filters:[["account_type","=","Tax"],["is_group","=",0]],limit:1});if(r?.length)taxAccountHead.value=r[0].name;}catch{}}
function statusLabel(o){if(o.docstatus===2)return"Cancelled";if(o.docstatus===0)return"Draft";const s=o.status||"";if(s==="Completed")return"Completed";if(s.includes("Receive"))return"To Receive";return s||"Submitted";}
function statusClass(o){if(o.docstatus===2)return"badge-grey";if(o.docstatus===0)return"badge-orange";if(statusLabel(o)==="Completed")return"badge-green";return"badge-blue";}
const filtered=computed(()=>{let r=list.value;if(activeTab.value==="draft")r=r.filter(o=>o.docstatus===0);if(activeTab.value==="to-receive")r=r.filter(o=>o.docstatus===1&&statusLabel(o)==="To Receive");if(activeTab.value==="completed")r=r.filter(o=>statusLabel(o)==="Completed");if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(o=>(o.name||"").toLowerCase().includes(q)||(o.supplier_name||o.supplier||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const counts=computed(()=>({draft:list.value.filter(o=>o.docstatus===0).length,toReceive:list.value.filter(o=>o.docstatus===1&&statusLabel(o)==="To Receive").length,completed:list.value.filter(o=>statusLabel(o)==="Completed").length}));
const totalValue=computed(()=>list.value.filter(o=>o.docstatus===1).reduce((s,o)=>s+flt(o.grand_total),0));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
const allChecked=computed(()=>sorted.value.length>0&&sorted.value.every(o=>selected.value.has(o.name)));
function toggle(n){const s=new Set(selected.value);s.has(n)?s.delete(n):s.add(n);selected.value=s;}
function toggleAll(e){selected.value=e.target.checked?new Set(sorted.value.map(o=>o.name)):new Set();}
function openNew(){editingName.value="";Object.assign(form,{supplier:"",transaction_date:new Date().toISOString().slice(0,10),expected_delivery_date:"",tax_rate:0,terms:""});lines.value=[blankLine()];fetchVendors("");fetchItems("");drawerOpen.value=true;}
async function openEdit(o){
  editingName.value=o.name;Object.assign(form,{supplier:o.supplier||"",transaction_date:o.transaction_date||"",expected_delivery_date:o.expected_delivery_date||"",tax_rate:0,terms:o.terms||""});
  lines.value=[blankLine()];fetchVendors("");fetchItems("");drawerOpen.value=true;
  try{const doc=await apiGet("Purchase Order",o.name);
    if(doc?.items?.length)lines.value=doc.items.map(i=>({id:_id++,item_code:i.item_code||"",description:i.description||"",qty:i.qty||1,rate:i.rate||0,amount:i.amount||0}));
    if(doc?.taxes?.[0]?.rate)form.tax_rate=doc.taxes[0].rate;
    if(doc?.taxes?.[0]?.account_head)taxAccountHead.value=doc.taxes[0].account_head;
  }catch{}
}
function openView(o){viewDoc.value=o;viewOpen.value=true;}
async function fetchVendors(q=""){try{const r=await apiList("Supplier",{fields:["name","supplier_name"],filters:q?[["supplier_name","like","%"+q+"%"]]:[],limit:30,order:"supplier_name asc"});vendors.value=r.map(x=>({label:x.supplier_name||x.name,value:x.name}));}catch{vendors.value=[];}}
async function fetchItems(q=""){try{const r=await apiList("Item",{fields:["name","item_name","standard_rate","stock_uom"],filters:q?[["item_name","like","%"+q+"%"]]:[],limit:30,order:"item_name asc"});items.value=r.map(x=>({label:x.item_name||x.name,value:x.name,rate:x.standard_rate||0}));}catch{items.value=[];}}
function onItemSelect(line,opt){line.item_code=opt?.value??opt;if(opt?.rate){line.rate=Number(opt.rate)||0;calcLine(line);}}
function addLine(){lines.value.push(blankLine());}
function removeLine(id){if(lines.value.length>1)lines.value=lines.value.filter(l=>l.id!==id);}
function calcLine(l){l.amount=Math.round(flt(l.qty)*flt(l.rate)*100)/100;}
const subtotal=computed(()=>lines.value.reduce((s,l)=>s+flt(l.amount),0));
const taxAmount=computed(()=>Math.round(subtotal.value*flt(form.tax_rate)/100*100)/100);
async function saveOrder(submit){
  if(!form.supplier)return toast.error("Vendor is required");
  drawerSaving.value=true;
  try{
    const company=await resolveCompany();
    const taxes=form.tax_rate>0&&taxAccountHead.value?[{doctype:"Tax Line",charge_type:"On Net Total",account_head:taxAccountHead.value,description:taxAccountHead.value,rate:form.tax_rate}]:[];
    const doc={doctype:"Purchase Order",company,supplier:form.supplier,transaction_date:form.transaction_date,expected_delivery_date:form.expected_delivery_date||null,terms:form.terms||"",
      items:lines.value.filter(l=>l.item_code).map(l=>({doctype:"Purchase Order Item",item_code:l.item_code,description:l.description||l.item_code,qty:flt(l.qty)||1,rate:flt(l.rate),amount:flt(l.amount),expected_delivery_date:form.expected_delivery_date||null})),taxes};
    if(editingName.value)doc.name=editingName.value;
    const saved=await apiSave(doc);
    if(submit&&saved?.name)await apiSubmit("Purchase Order",saved.name);
    toast.success(`Purchase Order ${saved?.name||""} ${submit?"submitted":"saved"}`);drawerOpen.value=false;await load();
  }catch(e){toast.error(e.message||"Failed to save purchase order");}finally{drawerSaving.value=false;}
}
onMounted(()=>{load();loadTaxAccount();});
</script>

<style scoped>
.po-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.po-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.po-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.po-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.po-pills{display:flex;gap:6px;}
.po-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.po-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.po-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.po-btn-primary:hover{background:#1d4ed8;}.po-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.po-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.po-btn-ghost:hover{background:#f9fafb;}
.po-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.po-btn-save:hover{background:#dcfce7;}.po-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.po-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.po-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.po-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.po-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.orange{color:#ea580c!important;}.blue{color:#2563eb!important;}.green{color:#16a34a!important;}
.po-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.po-table{width:100%;border-collapse:collapse;font-size:13px;}
.po-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.po-table th.sortable{cursor:pointer;user-select:none;}.po-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.po-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.po-row:last-child td{border-bottom:none;}.po-row:hover td{background:#f9fafb;}.po-row.selected td{background:#eff6ff;}
.po-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.po-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-blue{background:#dbeafe;color:#2563eb;}.badge-orange{background:#fff7ed;color:#ea580c;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.po-act-cell{display:flex;gap:4px;justify-content:flex-end;cursor:default!important;}
.po-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.po-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.po-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.po-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.po-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.po-drawer{position:fixed;top:0;right:-560px;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.po-drawer.open{right:0;}
.po-view-drawer{width:440px;right:-440px;}.po-view-drawer.open{right:0;}
.po-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.po-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.po-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.po-dclose:hover{background:#f3f4f6;color:#111827;}
.po-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.po-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.po-field{display:flex;flex-direction:column;gap:4px;}
.po-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.po-input{width:100%;box-sizing:border-box;border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.po-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
textarea.po-input{resize:vertical;}
.po-section-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;padding-bottom:4px;border-bottom:1px solid #f3f4f6;}
.po-items-table{display:flex;flex-direction:column;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;}
.po-items-head{display:grid;grid-template-columns:2fr 2fr 80px 100px 100px 32px;gap:8px;background:#f9fafb;padding:8px 12px;font-size:11.5px;font-weight:600;color:#374151;}
.po-items-row{display:grid;grid-template-columns:2fr 2fr 80px 100px 100px 32px;gap:8px;padding:8px 12px;border-top:1px solid #f3f4f6;align-items:center;}
.po-add-line{background:transparent;border:none;color:#2563eb;font-size:12.5px;font-weight:600;cursor:pointer;padding:8px 12px;display:inline-flex;align-items:center;gap:6px;}
.po-add-line:hover{background:#eff6ff;}
.po-rm-line{background:transparent;border:1px solid #e5e7eb;border-radius:4px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#9ca3af;}
.po-rm-line:hover{background:#fee2e2;color:#dc2626;border-color:#fca5a5;}
.po-totals{display:flex;justify-content:space-between;align-items:flex-start;gap:16px;}
.po-totals-right{display:flex;flex-direction:column;gap:4px;min-width:220px;}
.po-total-row{display:flex;justify-content:space-between;gap:16px;font-size:13px;color:#374151;padding:3px 0;}
.po-total-row.grand{font-weight:700;font-size:14px;color:#111827;border-top:1px solid #e5e7eb;padding-top:6px;margin-top:2px;}
.po-view-head{position:relative;display:flex;align-items:flex-start;justify-content:space-between;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#fefce8;}
.po-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.po-view-sub{font-size:13px;color:#6b7280;margin-top:2px;}
.po-view-amount{font-size:22px;font-weight:800;font-family:monospace;color:#111827;}
.po-vclose{position:absolute;top:12px;right:12px;}
.po-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.po-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.po-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
