<template>
  <div class="cn-page">
    <div class="cn-actions">
      <div class="cn-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search credit notes…" class="cn-search-input" />
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="cn-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="cn-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Credit Note
        </button>
      </div>
    </div>

    <div class="cn-summary" v-if="!loading">
      <div class="cn-sum-card"><div class="cn-sum-lbl">Total Credit Notes</div><div class="cn-sum-val">{{ list.length }}</div></div>
      <div class="cn-sum-card"><div class="cn-sum-lbl">Total Value</div><div class="cn-sum-val red">{{ fmtCur(totalValue) }}</div></div>
      <div class="cn-sum-card"><div class="cn-sum-lbl">Draft</div><div class="cn-sum-val orange">{{ list.filter(c=>c.docstatus===0).length }}</div></div>
      <div class="cn-sum-card"><div class="cn-sum-lbl">Submitted</div><div class="cn-sum-val green">{{ list.filter(c=>c.docstatus===1).length }}</div></div>
    </div>

    <div class="cn-card">
      <table class="cn-table">
        <thead>
          <tr>
            <th @click="sort('name')" class="sortable">Credit Note # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('customer_name')" class="sortable">Customer <span v-html="sortArrow('customer_name')"></span></th>
            <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
            <th>Return Against</th>
            <th>Status</th>
            <th @click="sort('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:50px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="7"><div class="cn-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="c in sorted" :key="c.name" class="cn-row" @click="openView(c)">
              <td><span class="cn-num">{{ c.name }}</span></td>
              <td>{{ c.customer_name||'—' }}</td>
              <td class="text-muted mono-sm">{{ fmtDate(c.posting_date) }}</td>
              <td class="text-muted mono-sm">{{ c.return_against||'—' }}</td>
              <td><span class="cn-badge" :class="c.docstatus===0?'badge-orange':c.docstatus===1?'badge-red':'badge-grey'">
                {{ c.docstatus===0?'Draft':c.docstatus===1?'Issued':'Cancelled' }}
              </span></td>
              <td class="ta-r mono-sm red">{{ fmtCur(c.grand_total) }}</td>
              <td @click.stop>
                <button class="cn-act-btn" @click="openView(c)"><span v-html="icon('eye',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="7" class="cn-empty">No credit notes found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create Drawer -->
    <div v-if="drawerOpen" class="cn-overlay" @click.self="drawerOpen=false"></div>
    <div class="cn-drawer" :class="{open:drawerOpen}">
      <div class="cn-dheader">
        <div class="cn-dheader-title">New Credit Note</div>
        <button class="cn-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="cn-dbody">
        <div class="cn-fields-grid">
          <div class="cn-field" style="grid-column:1/-1">
            <label class="cn-label">Customer <span class="req">*</span></label>
            <SearchableSelect v-model="form.customer" :options="customers" placeholder="Select customer…" :createable="true" createDoctype="Customer" @search="fetchCustomers" />
          </div>
          <div class="cn-field">
            <label class="cn-label">Date <span class="req">*</span></label>
            <input v-model="form.posting_date" type="date" class="cn-input" />
          </div>
          <div class="cn-field">
            <label class="cn-label">Return Against Invoice</label>
            <SearchableSelect v-model="form.return_against" :options="invoices" placeholder="Select invoice…" @search="fetchInvoices" />
          </div>
        </div>

        <div class="cn-section-title">Items to Return</div>
        <div class="cn-items-table">
          <div class="cn-items-head">
            <div>Item</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="cn-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items" placeholder="Select item…" :createable="true" createDoctype="Item" @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model.number="line.qty" type="number" min="1" class="cn-input ta-r" @input="calcLine(line)" /></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="cn-input ta-r" @input="calcLine(line)" /></div>
            <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
            <div><button @click="removeLine(line.id)" class="cn-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="cn-add-line" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <div class="cn-totals-right">
          <div class="cn-total-row grand"><span>Total Credit</span><span class="red">{{ fmtCur(subtotal) }}</span></div>
        </div>

        <div class="cn-field">
          <label class="cn-label">Reason / Notes</label>
          <textarea v-model="form.reason" rows="2" class="cn-input" placeholder="Reason for credit note…"></textarea>
        </div>
      </div>
      <div class="cn-dfooter">
        <button class="cn-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="cn-btn-save" :disabled="drawerSaving" @click="saveCN(0)">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="cn-btn-primary" :disabled="drawerSaving" @click="saveCN(1)">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}
        </button>
      </div>
    </div>

    <!-- View Drawer -->
    <div v-if="viewOpen" class="cn-overlay" @click.self="viewOpen=false"></div>
    <div class="cn-drawer cn-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="cn-view-head">
          <div><div class="cn-view-num">{{ viewDoc.name }}</div><div class="cn-view-sub">{{ viewDoc.customer_name }}</div></div>
          <div style="text-align:right">
            <div class="cn-view-amount red">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="cn-badge" :class="viewDoc.docstatus===0?'badge-orange':viewDoc.docstatus===1?'badge-red':'badge-grey'">
              {{ viewDoc.docstatus===0?'Draft':'Issued' }}
            </span>
          </div>
          <button class="cn-dclose cn-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="cn-dbody">
          <div class="cn-meta-grid">
            <div><div class="cn-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
            <div><div class="cn-meta-lbl">Return Against</div><div class="mono-sm">{{ viewDoc.return_against||'—' }}</div></div>
          </div>
        </div>
        <div class="cn-dfooter">
          <button class="cn-btn-ghost" @click="viewOpen=false">Close</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiSubmit, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const list=ref([]),loading=ref(false),search=ref("");
const drawerOpen=ref(false),drawerSaving=ref(false);
const viewOpen=ref(false),viewDoc=ref(null);
const customers=ref([]),items=ref([]),invoices=ref([]),lines=ref([]);
const sortCol=ref("posting_date"),sortDir=ref("desc");

let _id=1;
const blankLine=()=>({id:_id++,item_code:"",qty:1,rate:0,amount:0});
const form=reactive({customer:"",posting_date:new Date().toISOString().slice(0,10),return_against:"",reason:""});

async function load(){
  loading.value=true;
  try{const co=await resolveCompany();list.value=await apiList("Sales Invoice",{fields:["name","customer","customer_name","posting_date","grand_total","return_against","docstatus"],filters:[["company","=",co],["is_return","=",1]],limit:200,order:"posting_date desc"});}
  catch(e){toast.error(e.message||"Failed to load credit notes");}
  finally{loading.value=false;}
}

const filtered=computed(()=>{
  if(!search.value.trim()) return list.value;
  const q=search.value.toLowerCase();
  return list.value.filter(c=>(c.name||"").toLowerCase().includes(q)||(c.customer_name||"").toLowerCase().includes(q));
});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const totalValue=computed(()=>list.value.filter(c=>c.docstatus===1).reduce((s,c)=>s+Math.abs(flt(c.grand_total)),0));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(Math.abs(flt(v)));}

function openNew(){Object.assign(form,{customer:"",posting_date:new Date().toISOString().slice(0,10),return_against:"",reason:""});lines.value=[blankLine()];fetchCustomers("");fetchItems("");drawerOpen.value=true;}
function openView(c){viewDoc.value=c;viewOpen.value=true;}
async function fetchCustomers(q=""){try{const f=[["disabled","=",0]];if(q)f.push(["customer_name","like","%"+q+"%"]);const r=await apiList("Customer",{fields:["name","customer_name"],filters:f,limit:30,order:"customer_name asc"});customers.value=r.map(x=>({label:x.customer_name||x.name,value:x.name}));}catch{customers.value=[];}}
async function fetchItems(q=""){try{const f=[["disabled","=",0]];if(q)f.push(["item_name","like","%"+q+"%"]);const r=await apiList("Item",{fields:["name","item_name","standard_rate","stock_uom"],filters:f,limit:30,order:"item_name asc"});items.value=r.map(x=>({label:x.item_name||x.name,value:x.name,rate:x.standard_rate||0}));}catch{items.value=[];}}
async function fetchInvoices(q=""){try{const f=[["is_return","=",0],["docstatus","=",1]];if(form.customer)f.push(["customer","=",form.customer]);if(q)f.push(["name","like",`%${q}%`]);const r=await apiList("Sales Invoice",{fields:["name"],filters:f,limit:20});invoices.value=r.map(x=>({label:x.name,value:x.name}));}catch{invoices.value=[];}}
function onItemSelect(line,opt){line.item_code=opt?.value??opt;if(opt?.rate){line.rate=Number(opt.rate)||0;calcLine(line);}}
function addLine(){lines.value.push(blankLine());}
function removeLine(id){if(lines.value.length>1)lines.value=lines.value.filter(l=>l.id!==id);}
function calcLine(l){l.amount=Math.round(flt(l.qty)*flt(l.rate)*100)/100;}
const subtotal=computed(()=>lines.value.reduce((s,l)=>s+flt(l.amount),0));

async function saveCN(submit){
  if(!form.customer) return toast.error("Customer is required");
  drawerSaving.value=true;
  try{
    const company=await resolveCompany();
    const doc={doctype:"Sales Invoice",company,customer:form.customer,posting_date:form.posting_date,is_return:1,return_against:form.return_against||null,remarks:form.reason||"",
      items:lines.value.filter(l=>l.item_code).map(l=>({doctype:"Sales Invoice Item",item_code:l.item_code,description:l.item_code,qty:-flt(l.qty),rate:flt(l.rate),amount:-flt(l.amount)}))};
    const saved=await apiSave(doc);
    if(submit) await apiSubmit("Sales Invoice",saved.name);
    toast.success(`Credit Note ${saved?.name||""} ${submit?"submitted":"saved"}`);
    drawerOpen.value=false;await load();
  }catch(e){toast.error(e.message||"Failed to save credit note");}
  finally{drawerSaving.value=false;}
}
onMounted(load);
</script>

<style scoped>
.cn-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.cn-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.cn-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.cn-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.cn-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.cn-btn-primary:hover{background:#1d4ed8;}.cn-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.cn-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.cn-btn-ghost:hover{background:#f9fafb;}
.cn-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.cn-btn-save:hover{background:#dcfce7;}.cn-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.cn-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.cn-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.cn-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.cn-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.orange{color:#ea580c!important;}.red{color:#dc2626!important;}.green{color:#16a34a!important;}
.cn-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.cn-table{width:100%;border-collapse:collapse;font-size:13px;}
.cn-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.cn-table th.sortable{cursor:pointer;user-select:none;}.cn-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.cn-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.cn-row:last-child td{border-bottom:none;}.cn-row:hover td{background:#f9fafb;}
.cn-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.cn-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-red{background:#fee2e2;color:#dc2626;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.cn-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.cn-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.cn-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.cn-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.cn-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.cn-drawer{position:fixed;top:0;right:-540px;bottom:0;width:540px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.cn-drawer.open{right:0;}
.cn-view-drawer{width:420px;right:-420px;}.cn-view-drawer.open{right:0;}
.cn-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.cn-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.cn-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.cn-dclose:hover{background:#f3f4f6;color:#111827;}
.cn-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.cn-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.cn-field{display:flex;flex-direction:column;gap:4px;}
.cn-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.cn-input{width:100%;box-sizing:border-box;border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.cn-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
textarea.cn-input{resize:vertical;}
.cn-section-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;padding-bottom:4px;border-bottom:1px solid #f3f4f6;}
.cn-items-table{display:flex;flex-direction:column;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;}
.cn-items-head{display:grid;grid-template-columns:2fr 80px 100px 100px 32px;gap:8px;background:#f9fafb;padding:8px 12px;font-size:11.5px;font-weight:600;color:#374151;}
.cn-items-row{display:grid;grid-template-columns:2fr 80px 100px 100px 32px;gap:8px;padding:8px 12px;border-top:1px solid #f3f4f6;align-items:center;}
.cn-add-line{background:transparent;border:none;color:#2563eb;font-size:12.5px;font-weight:600;cursor:pointer;padding:8px 12px;display:inline-flex;align-items:center;gap:6px;}
.cn-add-line:hover{background:#eff6ff;}
.cn-rm-line{background:transparent;border:1px solid #e5e7eb;border-radius:4px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#9ca3af;}
.cn-rm-line:hover{background:#fee2e2;color:#dc2626;border-color:#fca5a5;}
.cn-totals-right{display:flex;flex-direction:column;gap:4px;align-self:flex-end;min-width:200px;}
.cn-total-row{display:flex;justify-content:space-between;gap:16px;font-size:13px;color:#374151;padding:3px 0;}
.cn-total-row.grand{font-weight:700;font-size:14px;color:#111827;border-top:1px solid #e5e7eb;padding-top:6px;margin-top:2px;}
.cn-view-head{position:relative;display:flex;align-items:flex-start;justify-content:space-between;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#fff1f2;}
.cn-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.cn-view-sub{font-size:13px;color:#6b7280;margin-top:2px;}
.cn-view-amount{font-size:22px;font-weight:800;font-family:monospace;}
.cn-vclose{position:absolute;top:12px;right:12px;}
.cn-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.cn-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.cn-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
