<template>
  <div class="se-page">
    <div class="se-actions">
      <div class="se-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search stock entries…" class="se-search-input" /></div>
      <div class="se-pills"><button v-for="t in tabs" :key="t.key" class="se-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">{{ t.label }}</button></div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="se-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="se-btn-ghost" @click="exportCSV" :disabled="!sorted.length"><span v-html="icon('download',14)"></span> Export</button>
        <button class="se-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Entry</button>
      </div>
    </div>
    <div class="se-card">
      <table class="se-table">
        <thead><tr>
          <th @click="sort('name')" class="sortable">Entry # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('stock_entry_type')" class="sortable">Type <span v-html="sortArrow('stock_entry_type')"></span></th>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
          <th>From Warehouse</th><th>To Warehouse</th>
          <th>Status</th>
          <th @click="sort('value_difference')" class="sortable ta-r">Value <span v-html="sortArrow('value_difference')"></span></th>
          <th style="width:40px"></th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 8" :key="n"><td colspan="8"><div class="se-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="e in sorted" :key="e.name" class="se-row" @click="openView(e)">
              <td><span class="se-num">{{ e.name }}</span></td>
              <td><span class="se-type-badge">{{ e.stock_entry_type||'—' }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(e.posting_date) }}</td>
              <td class="text-muted">{{ e.from_warehouse||'—' }}</td>
              <td class="text-muted">{{ e.to_warehouse||'—' }}</td>
              <td><span class="se-badge" :class="e.docstatus===0?'badge-orange':e.docstatus===1?'badge-green':'badge-grey'">{{ e.docstatus===0?'Draft':e.docstatus===1?'Submitted':'Cancelled' }}</span></td>
              <td class="ta-r mono-sm">{{ fmtCur(e.value_difference) }}</td>
              <td @click.stop><button class="se-act-btn" @click="openView(e)"><span v-html="icon('eye',13)"></span></button></td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="se-empty">No stock entries found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create Drawer -->
    <div v-if="drawerOpen" class="se-overlay" @click.self="drawerOpen=false"></div>
    <div class="se-drawer" :class="{open:drawerOpen}">
      <div class="se-dheader">
        <button class="se-dclose se-dclose-abs" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
        <div class="se-dh-top">
          <div class="se-dh-ico"><span v-html="icon('stack',20)"></span></div>
          <div>
            <div class="se-dh-title">New Stock Entry</div>
            <div class="se-dh-sub">Record a stock movement</div>
          </div>
        </div>
      </div>
      <div class="se-dbody">
        <div class="se-fields-grid">
          <div class="se-field" style="grid-column:1/-1">
            <label class="se-label">Entry Type <span class="req">*</span></label>
            <select v-model="form.stock_entry_type" class="se-select">
              <option value="Material Issue">Material Issue</option>
              <option value="Material Receipt">Material Receipt</option>
              <option value="Material Transfer">Material Transfer</option>
              <option value="Manufacture">Manufacture</option>
              <option value="Repack">Repack</option>
            </select>
          </div>
          <div class="se-field">
            <label class="se-label">Date <span class="req">*</span></label>
            <input v-model="form.posting_date" type="date" class="se-input" />
          </div>
          <div class="se-field">
            <label class="se-label">From Warehouse</label>
            <SearchableSelect v-model="form.from_warehouse" :options="warehouses" placeholder="Source…" @search="fetchWarehouses" />
          </div>
          <div class="se-field" style="grid-column:1/-1">
            <label class="se-label">To Warehouse</label>
            <SearchableSelect v-model="form.to_warehouse" :options="warehouses" placeholder="Destination…" @search="fetchWarehouses" />
          </div>
        </div>
        <div class="se-section-title">Items</div>
        <div class="se-items-table">
          <div class="se-items-head"><div>Item</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div></div></div>
          <div v-for="line in lines" :key="line.id" class="se-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items" placeholder="Item…" @search="fetchItems" @select="opt=>onItemSelect(line,opt)" /></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="se-input ta-r" /></div>
            <div><input v-model.number="line.basic_rate" type="number" min="0" step="0.01" class="se-input ta-r" /></div>
            <div><button @click="removeLine(line.id)" class="se-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="se-add-line" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>
        <div class="se-field"><label class="se-label">Remarks</label><textarea v-model="form.remarks" rows="2" class="se-input" placeholder="Optional…"></textarea></div>
      </div>
      <div class="se-dfooter">
        <button class="se-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="se-btn-save" :disabled="drawerSaving" @click="saveEntry(0)"><span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}</button>
        <button class="se-btn-primary" :disabled="drawerSaving" @click="saveEntry(1)"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}</button>
      </div>
    </div>

    <!-- View -->
    <div v-if="viewOpen" class="se-overlay" @click.self="viewOpen=false"></div>
    <div class="se-drawer se-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="se-dheader">
          <button class="se-dclose se-dclose-abs" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
          <div class="se-dh-top">
            <div class="se-dh-ico"><span v-html="icon('stack',20)"></span></div>
            <div>
              <div class="se-dh-title">{{ viewDoc.name }}</div>
              <div class="se-dh-sub">{{ viewDoc.stock_entry_type }} · {{ fmtDate(viewDoc.posting_date) }}</div>
            </div>
            <span class="se-badge" :class="viewDoc.docstatus===0?'badge-orange':viewDoc.docstatus===1?'badge-green':'badge-grey'" style="margin-left:auto">{{ viewDoc.docstatus===0?'Draft':viewDoc.docstatus===1?'Submitted':'Cancelled' }}</span>
          </div>
        </div>
        <div class="se-dbody">
          <div class="se-meta-grid">
            <div><div class="se-meta-lbl">Type</div><div>{{ viewDoc.stock_entry_type }}</div></div>
            <div><div class="se-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
            <div><div class="se-meta-lbl">From</div><div>{{ viewDoc.from_warehouse||'—' }}</div></div>
            <div><div class="se-meta-lbl">To</div><div>{{ viewDoc.to_warehouse||'—' }}</div></div>
          </div>
          <div v-if="viewDoc.remarks" style="font-size:13px;color:#374151;padding:10px 0;border-top:1px solid #f3f4f6;"><span style="font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;display:block;margin-bottom:4px">Remarks</span>{{ viewDoc.remarks }}</div>
          <div v-if="viewDoc.items && viewDoc.items.length">
            <div class="se-section-title" style="margin-bottom:8px">Items</div>
            <table class="se-view-items-tbl">
              <thead><tr><th>Item</th><th class="ta-r">Qty</th><th class="ta-r">Rate</th><th class="ta-r">Amount</th></tr></thead>
              <tbody>
                <tr v-for="it in viewDoc.items" :key="it.name||it.idx">
                  <td>{{ it.item_code }}</td>
                  <td class="ta-r mono-sm">{{ it.qty }}</td>
                  <td class="ta-r mono-sm">{{ fmtCur(it.basic_rate) }}</td>
                  <td class="ta-r mono-sm">{{ fmtCur(flt(it.qty)*flt(it.basic_rate)) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="se-dfooter"><button class="se-btn-ghost" @click="viewOpen=false">Close</button></div>
      </template>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { apiList, apiGet, apiSave, apiSubmit, resolveCompany, apiLinkValues } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
const { toast } = useToast();
const route = useRoute();
const activeTab=ref("all");
const tabs=[{key:"all",label:"All"},{key:"Material Receipt",label:"Receipt"},{key:"Material Issue",label:"Issue"},{key:"Material Transfer",label:"Transfer"}];
const list=ref([]),loading=ref(false),search=ref("");
const drawerOpen=ref(false),drawerSaving=ref(false);
const viewOpen=ref(false),viewDoc=ref(null);
const warehouses=ref([]),items=ref([]),lines=ref([]);
const sortCol=ref("posting_date"),sortDir=ref("desc");
let _id=1;
const blankLine=()=>({id:_id++,item_code:"",qty:1,basic_rate:0});
const form=reactive({stock_entry_type:"Material Receipt",posting_date:new Date().toISOString().slice(0,10),from_warehouse:"",to_warehouse:"",remarks:""});

async function load(){loading.value=true;try{const co=await resolveCompany();list.value=await apiList("Stock Entry",{fields:["name","stock_entry_type","posting_date","from_warehouse","to_warehouse","value_difference","docstatus"],filters:[["company","=",co]],limit:200,order:"posting_date desc"});}catch(e){toast.error(e.message||"Failed to load stock entries");}finally{loading.value=false;}}
const filtered=computed(()=>{let r=list.value;if(activeTab.value!=="all")r=r.filter(e=>e.stock_entry_type===activeTab.value);if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(e=>(e.name||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
function exportCSV(){
  const rows=sorted.value;
  if(!rows.length)return;
  const esc=v=>{const s=v==null?"":String(v);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  const statusOf=d=>d===0?"Draft":d===1?"Submitted":"Cancelled";
  const lines2=[["Entry #","Type","Date","From Warehouse","To Warehouse","Status","Value"].join(",")];
  for(const e of rows){
    lines2.push([e.name,e.stock_entry_type||"",fmtDate(e.posting_date),e.from_warehouse||"",e.to_warehouse||"",statusOf(e.docstatus),flt(e.value_difference)].map(esc).join(","));
  }
  const blob=new Blob(["﻿"+lines2.join("\r\n")],{type:"text/csv;charset=utf-8;"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a");
  a.href=url;a.download=`stock_entries_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();URL.revokeObjectURL(url);
  toast.success(`Exported ${rows.length} row(s)`);
}
function openNew(){Object.assign(form,{stock_entry_type:"Material Receipt",posting_date:new Date().toISOString().slice(0,10),from_warehouse:"",to_warehouse:"",remarks:""});lines.value=[blankLine()];fetchWarehouses("");fetchItems("");drawerOpen.value=true;}
async function openView(e){viewDoc.value=e;viewOpen.value=true;try{const full=await apiGet("Stock Entry",e.name);viewDoc.value=full;}catch{/* keep list-row data */}}
async function fetchWarehouses(q=""){try{const co=await resolveCompany();const r=await apiList("Warehouse",{fields:["name"],filters:[["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:20});warehouses.value=r.map(x=>({label:x.name,value:x.name}));}catch{warehouses.value=[];}}
async function fetchItems(q=""){try{const r=await apiLinkValues("Item",q);items.value=r.map(x=>({label:x.name,value:x.name}));}catch{items.value=[];}}
async function onItemSelect(line,opt){
  line.item_code = opt?.value ?? opt;
  if(!line.item_code)return;
  // Auto-fill rate from the item's buying/standard rate (if rate not set yet).
  try{
    const r=await apiList("Item",{fields:["name","standard_buying_rate","standard_rate"],filters:[["name","=",line.item_code]],limit:1});
    const it=r&&r[0];
    if(it&&!flt(line.basic_rate))line.basic_rate=flt(it.standard_buying_rate)||flt(it.standard_rate)||0;
  }catch{}
}
function addLine(){lines.value.push(blankLine());}
function removeLine(id){if(lines.value.length>1)lines.value=lines.value.filter(l=>l.id!==id);}
async function saveEntry(submit){
  if(!lines.value.some(l=>l.item_code))return toast.error("At least one item is required");
  drawerSaving.value=true;
  try{const company=await resolveCompany();const doc={doctype:"Stock Entry",company,stock_entry_type:form.stock_entry_type,posting_date:form.posting_date,from_warehouse:form.from_warehouse||null,to_warehouse:form.to_warehouse||null,remarks:form.remarks||"",items:lines.value.filter(l=>l.item_code).map(l=>({doctype:"Stock Entry Detail",item_code:l.item_code,qty:flt(l.qty),basic_rate:flt(l.basic_rate),s_warehouse:form.from_warehouse||null,t_warehouse:form.to_warehouse||null}))};const saved=await apiSave(doc);if(submit)await apiSubmit("Stock Entry",saved.name);toast.success(`Stock Entry ${saved?.name||""} ${submit?"submitted":"saved"}`);drawerOpen.value=false;await load();}
  catch(e){toast.error(e.message||"Failed to save stock entry");}finally{drawerSaving.value=false;}
}
onMounted(async()=>{await load();if(route.query.open)openView({name:String(route.query.open)});});
</script>
<style scoped>
.se-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.se-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.se-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.se-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.se-pills{display:flex;gap:6px;}
.se-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.se-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.se-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.se-btn-primary:hover{background:#1d4ed8;}.se-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.se-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.se-btn-ghost:hover{background:#f9fafb;}
.se-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.se-btn-save:hover{background:#dcfce7;}.se-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.se-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.se-table{width:100%;border-collapse:collapse;font-size:13px;}
.se-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.se-table th.sortable{cursor:pointer;user-select:none;}.se-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.se-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.se-row:last-child td{border-bottom:none;}.se-row:hover td{background:#f9fafb;}
.se-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.se-type-badge{display:inline-flex;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;background:#f3f4f6;color:#374151;}
.se-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.se-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.se-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.se-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.se-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.se-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);z-index:40;}
.se-drawer{position:fixed;top:0;right:-500px;bottom:0;width:500px;max-width:96vw;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 28px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s ease;}
.se-drawer.open{right:0;}
.se-view-drawer{width:420px;right:-420px;}.se-view-drawer.open{right:0;}
.se-dheader{position:relative;flex-shrink:0;padding:20px;border-bottom:1px solid #e5e7eb;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.se-dh-top{display:flex;align-items:center;gap:13px;padding-right:36px;}
.se-dh-ico{width:42px;height:42px;background:#fff;border-radius:11px;display:flex;align-items:center;justify-content:center;color:#2563eb;flex-shrink:0;box-shadow:0 1px 3px rgba(15,23,42,.08);}
.se-dh-title{font-size:15px;font-weight:700;color:#0f172a;}
.se-dh-sub{font-size:12px;color:#475569;margin-top:1px;}
.se-dclose{background:transparent;border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;}
.se-dclose:hover{background:rgba(255,255,255,.6);color:#0f172a;}
.se-dclose-abs{position:absolute;top:12px;right:12px;}
.se-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.se-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.se-field{display:flex;flex-direction:column;gap:4px;}
.se-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.se-input{border:1px solid #e2e8f0;border-radius:8px;padding:8px 11px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;transition:border-color .15s,box-shadow .15s;}
.se-input:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.1);}
textarea.se-input{resize:vertical;}
.se-select{border:1px solid #e2e8f0;border-radius:8px;padding:8px 11px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;cursor:pointer;transition:border-color .15s,box-shadow .15s;}
.se-select:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.1);}
.se-section-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;padding-bottom:4px;border-bottom:1px solid #f3f4f6;}
.se-items-table{display:flex;flex-direction:column;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;}
.se-items-head{display:grid;grid-template-columns:3fr 80px 100px 32px;gap:8px;background:#f9fafb;padding:8px 12px;font-size:11.5px;font-weight:600;color:#374151;}
.se-items-row{display:grid;grid-template-columns:3fr 80px 100px 32px;gap:8px;padding:8px 12px;border-top:1px solid #f3f4f6;align-items:center;}
.se-add-line{background:transparent;border:none;color:#2563eb;font-size:12.5px;font-weight:600;cursor:pointer;padding:8px 12px;display:inline-flex;align-items:center;gap:6px;}
.se-add-line:hover{background:#eff6ff;}
.se-rm-line{background:transparent;border:1px solid #e5e7eb;border-radius:4px;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#9ca3af;}
.se-rm-line:hover{background:#fee2e2;color:#dc2626;border-color:#fca5a5;}
.se-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.se-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.se-view-items-tbl{width:100%;border-collapse:collapse;font-size:12.5px;border:1px solid #e5e7eb;border-radius:6px;overflow:hidden;}
.se-view-items-tbl th{background:#f9fafb;padding:7px 10px;font-size:11px;font-weight:600;color:#374151;text-align:left;border-bottom:1px solid #e5e7eb;}
.se-view-items-tbl td{padding:7px 10px;border-bottom:1px solid #f3f4f6;color:#111827;}
.se-view-items-tbl tr:last-child td{border-bottom:none;}
.se-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
