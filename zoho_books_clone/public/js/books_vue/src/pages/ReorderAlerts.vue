<template>
  <div class="ra-page">
    <div class="ra-actions">
      <div class="ra-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search items…" class="ra-search-input" /></div>
      <div style="display:flex;gap:8px;margin-left:auto"><button class="ra-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button></div>
    </div>

    <div class="ra-summary" v-if="!loading">
      <div class="ra-sum-card"><div class="ra-sum-lbl">Items to Reorder</div><div class="ra-sum-val red">{{ belowReorder.length }}</div></div>
      <div class="ra-sum-card"><div class="ra-sum-lbl">Critical (0 stock)</div><div class="ra-sum-val red">{{ zeroStock.length }}</div></div>
      <div class="ra-sum-card"><div class="ra-sum-lbl">Low Stock</div><div class="ra-sum-val orange">{{ lowStock.length }}</div></div>
      <div class="ra-sum-card"><div class="ra-sum-lbl">Total Monitored</div><div class="ra-sum-val">{{ list.length }}</div></div>
    </div>

    <div class="ra-card">
      <table class="ra-table">
        <thead><tr>
          <th @click="sort('item_code')" class="sortable">Item <span v-html="sortArrow('item_code')"></span></th>
          <th>Item Name</th>
          <th @click="sort('warehouse')" class="sortable">Warehouse <span v-html="sortArrow('warehouse')"></span></th>
          <th @click="sort('actual_qty')" class="sortable ta-r">Current Qty <span v-html="sortArrow('actual_qty')"></span></th>
          <th @click="sort('re_order_level')" class="sortable ta-r">Reorder Level <span v-html="sortArrow('re_order_level')"></span></th>
          <th @click="sort('re_order_qty')" class="sortable ta-r">Reorder Qty <span v-html="sortArrow('re_order_qty')"></span></th>
          <th>Status</th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 8" :key="n"><td colspan="7"><div class="ra-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="item in sorted" :key="item.item_code+item.warehouse" class="ra-row" :class="{critical:flt(item.actual_qty)<=0}">
              <td><span class="ra-code">{{ item.item_code }}</span></td>
              <td>{{ item.item_name||item.item_code }}</td>
              <td class="text-muted">{{ item.warehouse||'—' }}</td>
              <td class="ta-r mono-sm" :class="flt(item.actual_qty)<=0?'red':flt(item.actual_qty)<=flt(item.re_order_level)?'orange':''">
                {{ fmtQty(item.actual_qty) }}
              </td>
              <td class="ta-r mono-sm text-muted">{{ fmtQty(item.re_order_level) }}</td>
              <td class="ta-r mono-sm">{{ fmtQty(item.re_order_qty) }}</td>
              <td>
                <span class="ra-badge" :class="flt(item.actual_qty)<=0?'badge-red':flt(item.actual_qty)<=flt(item.re_order_level)?'badge-orange':'badge-green'">
                  {{ flt(item.actual_qty)<=0?'Critical':flt(item.actual_qty)<=flt(item.re_order_level)?'Low Stock':'OK' }}
                </span>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="7" class="ra-empty">No reorder alerts</td></tr>
          </template>
        </tbody>
      </table>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from "vue";
import { apiList, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt } from "../utils/format.js";
const { toast } = useToast();
const list=ref([]),loading=ref(false),search=ref("");
const sortCol=ref("actual_qty"),sortDir=ref("asc");
async function load(){
  loading.value=true;
  try{
    const co=await resolveCompany();
    const whs=await apiList("Warehouse",{fields:["name"],filters:[["company","=",co],["is_group","=",0]],limit:200});
    const whNames=whs.map(w=>w.name);
    if(!whNames.length){list.value=[];return;}
    // Reorder thresholds + on-hand qty both live on Bin in this app.
    const bins=await apiList("Bin",{
      fields:["item_code","warehouse","actual_qty","reorder_level","reorder_qty"],
      filters:[["warehouse","in",whNames],["reorder_level",">",0]],
      limit:5000,
    });
    let rows=bins
      .map(b=>({item_code:b.item_code,item_name:b.item_code,warehouse:b.warehouse,actual_qty:flt(b.actual_qty),re_order_level:flt(b.reorder_level),re_order_qty:flt(b.reorder_qty)}))
      .filter(i=>i.actual_qty<=i.re_order_level);
    // Resolve readable item names.
    const codes=[...new Set(rows.map(r=>r.item_code).filter(Boolean))];
    if(codes.length){
      const items=await apiList("Item",{fields:["name","item_name"],filters:[["name","in",codes]],limit:codes.length});
      const nameMap={};for(const it of items)nameMap[it.name]=it.item_name;
      rows=rows.map(r=>({...r,item_name:nameMap[r.item_code]||r.item_code}));
    }
    list.value=rows;
  }catch(e){toast.error(e.message||"Failed to load reorder alerts");}finally{loading.value=false;}
}
const filtered=computed(()=>{if(!search.value.trim())return list.value;const q=search.value.toLowerCase();return list.value.filter(i=>(i.item_code||"").toLowerCase().includes(q)||(i.item_name||"").toLowerCase().includes(q));});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const belowReorder=computed(()=>list.value.filter(i=>flt(i.actual_qty)<=flt(i.re_order_level)));
const zeroStock=computed(()=>list.value.filter(i=>flt(i.actual_qty)<=0));
const lowStock=computed(()=>list.value.filter(i=>flt(i.actual_qty)>0&&flt(i.actual_qty)<=flt(i.re_order_level)));
function fmtQty(v){return Number(flt(v)).toLocaleString("en-IN",{maximumFractionDigits:3});}
onMounted(load);
</script>
<style scoped>
.ra-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.ra-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.ra-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.ra-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.ra-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.ra-btn-ghost:hover{background:#f9fafb;}
.ra-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.ra-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.ra-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.ra-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.orange{color:#ea580c!important;}.red{color:#dc2626!important;}
.ra-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.ra-table{width:100%;border-collapse:collapse;font-size:13px;}
.ra-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.ra-table th.sortable{cursor:pointer;user-select:none;}.ra-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.ra-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;}
.ra-row:last-child td{border-bottom:none;}.ra-row:hover td{background:#f9fafb;}
.ra-row.critical td{background:#fff5f5;}
.ra-code{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.ra-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-red{background:#fee2e2;color:#dc2626;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-green{background:#dcfce7;color:#16a34a;}
.ra-empty{text-align:center;color:#9ca3af;padding:48px!important;}
.ra-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
