<template>
  <div class="sv-page">
    <div class="sv-actions">
      <SearchableSelect v-model="filters.warehouse" :options="warehouses" placeholder="All Warehouses" @search="fetchWarehouses" style="min-width:200px" />
      <SearchableSelect v-model="filters.item_group" :options="itemGroups" placeholder="All Item Groups" @search="fetchItemGroups" style="min-width:180px" />
      <button class="sv-btn-primary" @click="load"><span v-html="icon('refresh',13)"></span> Refresh</button>
      <button class="sv-btn-ghost" @click="exportCSV" :disabled="!list.length"><span v-html="icon('download',13)"></span> Export</button>
      <div style="margin-left:auto;color:#6b7280;font-size:12.5px;align-self:center">As of today</div>
    </div>

    <div class="sv-summary" v-if="!loading && list.length">
      <div class="sv-sum-card"><div class="sv-sum-lbl">Total Items</div><div class="sv-sum-val">{{ list.length }}</div></div>
      <div class="sv-sum-card"><div class="sv-sum-lbl">Total Stock Value</div><div class="sv-sum-val blue">{{ fmtCur(totalValue) }}</div></div>
      <div class="sv-sum-card"><div class="sv-sum-lbl">Zero Stock Items</div><div class="sv-sum-val orange">{{ zeroStock }}</div></div>
      <div class="sv-sum-card"><div class="sv-sum-lbl">Total Qty</div><div class="sv-sum-val">{{ fmtQty(totalQty) }}</div></div>
    </div>

    <div class="sv-card">
      <table class="sv-table">
        <thead><tr>
          <th @click="sort('item_code')" class="sortable">Item <span v-html="sortArrow('item_code')"></span></th>
          <th @click="sort('item_name')" class="sortable">Item Name <span v-html="sortArrow('item_name')"></span></th>
          <th @click="sort('item_group')" class="sortable">Group <span v-html="sortArrow('item_group')"></span></th>
          <th>UOM</th>
          <th @click="sort('actual_qty')" class="sortable ta-r">Qty <span v-html="sortArrow('actual_qty')"></span></th>
          <th @click="sort('valuation_rate')" class="sortable ta-r">Rate <span v-html="sortArrow('valuation_rate')"></span></th>
          <th @click="sort('stock_value')" class="sortable ta-r">Stock Value <span v-html="sortArrow('stock_value')"></span></th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 10" :key="n"><td colspan="7"><div class="sv-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="i in sorted" :key="i.item_code+i.warehouse" class="sv-row">
              <td><span class="sv-code">{{ i.item_code }}</span></td>
              <td>{{ i.item_name||i.item_code }}</td>
              <td class="text-muted">{{ i.item_group||'—' }}</td>
              <td class="text-muted">{{ i.stock_uom||'—' }}</td>
              <td class="ta-r mono-sm" :class="flt(i.actual_qty)<=0?'red':''">{{ fmtQty(i.actual_qty) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(i.valuation_rate) }}</td>
              <td class="ta-r mono-sm font-medium">{{ fmtCur(i.stock_value) }}</td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="7" class="sv-empty">No stock data found</td></tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGET, resolveCompany, apiLinkValues } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
const { toast } = useToast();
const list=ref([]),loading=ref(false);
const warehouses=ref([]),itemGroups=ref([]);
const sortCol=ref("stock_value"),sortDir=ref("desc");
const filters=reactive({warehouse:"",item_group:""});
async function load(){
  loading.value=true;
  try{
    // get_stock_summary returns item_name + item_group and honours the
    // item-group filter (raw Bin has neither field).
    const r=await apiGET("zoho_books_clone.api.inventory.get_stock_summary",{
      warehouse: filters.warehouse||undefined,
      item_group: filters.item_group||undefined,
      show_zero_stock: 1,
    });
    const rows=Array.isArray(r)?r:(r?.message||[]);
    list.value=rows.map(x=>({...x,stock_uom:x.uom||x.stock_uom||""}));
  }catch(e){toast.error(e.message||"Failed to load valuation");}finally{loading.value=false;}
}
const sorted=computed(()=>{const col=sortCol.value;return[...list.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const totalValue=computed(()=>list.value.reduce((s,i)=>s+flt(i.stock_value),0));
const totalQty=computed(()=>list.value.reduce((s,i)=>s+flt(i.actual_qty),0));
const zeroStock=computed(()=>list.value.filter(i=>flt(i.actual_qty)<=0).length);
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
function fmtQty(v){return Number(flt(v)).toLocaleString("en-IN",{maximumFractionDigits:3});}
function exportCSV(){
  const rows=sorted.value;
  if(!rows.length)return;
  const esc=v=>{const s=v==null?"":String(v);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  const lines=[["Item","Item Name","Group","Warehouse","UOM","Qty","Rate","Stock Value"].join(",")];
  for(const i of rows){
    lines.push([i.item_code||"",i.item_name||"",i.item_group||"",i.warehouse||"",i.stock_uom||"",flt(i.actual_qty),flt(i.valuation_rate),flt(i.stock_value)].map(esc).join(","));
  }
  const blob=new Blob(["﻿"+lines.join("\r\n")],{type:"text/csv;charset=utf-8;"});
  const url=URL.createObjectURL(blob);
  const a=document.createElement("a");
  a.href=url;a.download=`stock_valuation_${new Date().toISOString().slice(0,10)}.csv`;
  a.click();URL.revokeObjectURL(url);
  toast.success(`Exported ${rows.length} row(s)`);
}
async function fetchWarehouses(q=""){try{const co=await resolveCompany();const r=await apiList("Warehouse",{fields:["name"],filters:[["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:20});warehouses.value=r.map(x=>({label:x.name,value:x.name}));}catch{warehouses.value=[];}}
async function fetchItemGroups(q=""){try{const r=await apiLinkValues("Item Group",q);itemGroups.value=r.map(x=>({label:x.name,value:x.name}));}catch{itemGroups.value=[];}}
onMounted(load);
</script>
<style scoped>
.sv-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.sv-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.sv-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.sv-btn-primary:hover{background:#1d4ed8;}
.sv-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;font-weight:600;color:#334155;cursor:pointer;}
.sv-btn-ghost:hover:not(:disabled){background:#f8fafc;border-color:#cbd5e1;}.sv-btn-ghost:disabled{opacity:.5;cursor:not-allowed;}
.sv-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.sv-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.sv-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.sv-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.blue{color:#2563eb!important;}.orange{color:#ea580c!important;}.red{color:#dc2626!important;}
.sv-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.sv-table{width:100%;border-collapse:collapse;font-size:13px;}
.sv-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.sv-table th.sortable{cursor:pointer;user-select:none;}.sv-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.sv-row td{padding:9px 12px;border-bottom:1px solid #f3f4f6;}
.sv-row:last-child td{border-bottom:none;}.sv-row:hover td{background:#f9fafb;}
.sv-code{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.font-medium{font-weight:600;}.text-muted{color:#6b7280;}
.sv-empty{text-align:center;color:#9ca3af;padding:48px!important;}
.sv-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
