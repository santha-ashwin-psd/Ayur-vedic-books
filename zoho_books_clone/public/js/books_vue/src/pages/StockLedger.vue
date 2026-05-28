<template>
  <div class="sl-page">
    <div class="sl-filters">
      <SearchableSelect v-model="filters.item" :options="items" placeholder="Filter by item…" @search="fetchItems" style="min-width:200px" />
      <SearchableSelect v-model="filters.warehouse" :options="warehouses" placeholder="Filter by warehouse…" @search="fetchWarehouses" style="min-width:200px" />
      <input v-model="filters.from_date" type="date" class="sl-input" />
      <input v-model="filters.to_date" type="date" class="sl-input" />
      <button class="sl-btn-primary" @click="load"><span v-html="icon('refresh',13)"></span> Run</button>
      <button class="sl-btn-ghost" @click="exportCSV" :disabled="!list.length"><span v-html="icon('download',13)"></span> Export</button>
      <div style="margin-left:auto;color:#6b7280;font-size:12.5px;align-self:center">{{ list.length }} entries</div>
    </div>

    <div class="sl-summary" v-if="!loading && list.length">
      <div class="sl-sum-card"><div class="sl-sum-lbl">Inward Qty</div><div class="sl-sum-val green">{{ fmtQty(summaryIn) }}</div></div>
      <div class="sl-sum-card"><div class="sl-sum-lbl">Outward Qty</div><div class="sl-sum-val red">{{ fmtQty(summaryOut) }}</div></div>
      <div class="sl-sum-card"><div class="sl-sum-lbl">Net Qty</div><div class="sl-sum-val" :class="(summaryIn-summaryOut)>=0?'green':'red'">{{ fmtQty(summaryIn-summaryOut) }}</div></div>
      <div class="sl-sum-card"><div class="sl-sum-lbl">Stock Value</div><div class="sl-sum-val">{{ fmtCur(stockValue) }}</div></div>
    </div>

    <div class="sl-card">
      <table class="sl-table">
        <thead><tr>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
          <th @click="sort('item_code')" class="sortable">Item <span v-html="sortArrow('item_code')"></span></th>
          <th @click="sort('warehouse')" class="sortable">Warehouse <span v-html="sortArrow('warehouse')"></span></th>
          <th>Voucher Type</th><th>Voucher #</th>
          <th @click="sort('actual_qty')" class="sortable ta-r">Qty In/Out <span v-html="sortArrow('actual_qty')"></span></th>
          <th @click="sort('qty_after_transaction')" class="sortable ta-r">Balance Qty <span v-html="sortArrow('qty_after_transaction')"></span></th>
          <th class="ta-r">Value</th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 10" :key="n"><td colspan="8"><div class="sl-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="e in sorted" :key="e.name" class="sl-row">
              <td class="mono-sm text-muted">{{ fmtDate(e.posting_date) }}</td>
              <td class="font-medium">{{ e.item_code }}</td>
              <td class="text-muted">{{ e.warehouse }}</td>
              <td class="text-muted" style="font-size:12px">{{ e.voucher_type }}</td>
              <td><span class="sl-voucher">{{ e.voucher_no }}</span></td>
              <td class="ta-r mono-sm" :class="flt(e.actual_qty)>0?'green':'red'">{{ flt(e.actual_qty)>0?'+':'' }}{{ fmtQty(e.actual_qty) }}</td>
              <td class="ta-r mono-sm">{{ fmtQty(e.qty_after_transaction) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(e.stock_value_difference) }}</td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="sl-empty">{{ loaded?'No ledger entries found':'Run to view stock ledger' }}</td></tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, computed } from "vue";
import { apiList, resolveCompany, apiLinkValues } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
const { toast } = useToast();
const list=ref([]),loading=ref(false),loaded=ref(false);
const items=ref([]),warehouses=ref([]);
const sortCol=ref("posting_date"),sortDir=ref("desc");
const now=new Date();
const firstOfMonth=new Date(now.getFullYear(),now.getMonth(),1).toISOString().slice(0,10);
const filters=reactive({item:"",warehouse:"",from_date:firstOfMonth,to_date:now.toISOString().slice(0,10)});
async function load(){loading.value=true;loaded.value=true;try{const co=await resolveCompany();const f=[["company","=",co]];if(filters.item)f.push(["item_code","=",filters.item]);if(filters.warehouse)f.push(["warehouse","=",filters.warehouse]);if(filters.from_date)f.push(["posting_date",">=",filters.from_date]);if(filters.to_date)f.push(["posting_date","<=",filters.to_date]);list.value=await apiList("Stock Ledger Entry",{fields:["name","posting_date","item_code","warehouse","voucher_type","voucher_no","actual_qty","qty_after_transaction","stock_value_difference","valuation_rate"],filters:f,limit:500,order:"posting_date asc"});}catch(e){toast.error(e.message||"Failed to load stock ledger");}finally{loading.value=false;}}
const sorted=computed(()=>{const col=sortCol.value;return[...list.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const summaryIn=computed(()=>list.value.filter(e=>flt(e.actual_qty)>0).reduce((s,e)=>s+flt(e.actual_qty),0));
const summaryOut=computed(()=>list.value.filter(e=>flt(e.actual_qty)<0).reduce((s,e)=>s+Math.abs(flt(e.actual_qty)),0));
const stockValue=computed(()=>list.value.reduce((s,e)=>s+flt(e.stock_value_difference),0));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
function fmtQty(v){return Number(flt(v)).toLocaleString("en-IN",{maximumFractionDigits:3});}
function exportCSV(){
  const rows=sorted.value;
  if(!rows.length)return;
  const esc=v=>{const s=v==null?"":String(v);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  const lines=[["Date","Item","Warehouse","Voucher Type","Voucher #","Qty In/Out","Balance Qty","Value Change","Valuation Rate"].join(",")];
  for(const e of rows){
    lines.push([fmtDate(e.posting_date),e.item_code||"",e.warehouse||"",e.voucher_type||"",e.voucher_no||"",flt(e.actual_qty),flt(e.qty_after_transaction),flt(e.stock_value_difference),flt(e.valuation_rate)].map(esc).join(","));
  }
  const blob=new Blob(["﻿"+lines.join("\r\n")],{type:"text/csv;charset=utf-8;"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a");
  a.href=url;a.download=`stock_ledger_${filters.from_date}_to_${filters.to_date}.csv`;
  a.click();URL.revokeObjectURL(url);
  toast.success(`Exported ${rows.length} row(s)`);
}
async function fetchItems(q=""){try{const r=await apiLinkValues("Item",q);items.value=r.map(x=>({label:x.name,value:x.name}));}catch{items.value=[];}}
async function fetchWarehouses(q=""){try{const co=await resolveCompany();const r=await apiList("Warehouse",{fields:["name"],filters:[["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:20});warehouses.value=r.map(x=>({label:x.name,value:x.name}));}catch{warehouses.value=[];}}
</script>
<style scoped>
.sl-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.sl-filters{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.sl-input{border:1px solid #e5e7eb;border-radius:8px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.sl-input:focus{border-color:#2563eb;}
.sl-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.sl-btn-primary:hover{background:#1d4ed8;}
.sl-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;font-weight:600;color:#334155;cursor:pointer;}
.sl-btn-ghost:hover:not(:disabled){background:#f8fafc;border-color:#cbd5e1;}.sl-btn-ghost:disabled{opacity:.5;cursor:not-allowed;}
.sl-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.sl-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.sl-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.sl-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}
.sl-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.sl-table{width:100%;border-collapse:collapse;font-size:13px;}
.sl-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.sl-table th.sortable{cursor:pointer;user-select:none;}.sl-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.sl-row td{padding:9px 12px;border-bottom:1px solid #f3f4f6;}
.sl-row:last-child td{border-bottom:none;}.sl-row:hover td{background:#f9fafb;}
.sl-voucher{font-family:monospace;font-size:12px;color:#2563eb;}
.font-medium{font-weight:600;}.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.sl-empty{text-align:center;color:#9ca3af;padding:48px!important;}
.sl-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
