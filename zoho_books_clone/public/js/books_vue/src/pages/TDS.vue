<template>
  <div class="tds-page">
    <div class="tds-actions">
      <div class="tds-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search by party or section…" class="tds-search-input" /></div>
      <div class="tds-controls" style="margin-left:auto;display:flex;gap:8px;align-items:center">
        <select v-model="periodFilter" class="tds-select">
          <option value="">All Periods</option>
          <option v-for="p in periods" :key="p.v" :value="p.v">{{ p.l }}</option>
        </select>
        <button class="tds-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
      </div>
    </div>

    <div class="tds-summary" v-if="!loading">
      <div class="tds-sum-card"><div class="tds-sum-lbl">Total Deductions</div><div class="tds-sum-val">{{ list.length }}</div></div>
      <div class="tds-sum-card"><div class="tds-sum-lbl">Total TDS Deducted</div><div class="tds-sum-val red">{{ fmtCur(totalTds) }}</div></div>
      <div class="tds-sum-card"><div class="tds-sum-lbl">Gross Payment</div><div class="tds-sum-val">{{ fmtCur(totalGross) }}</div></div>
      <div class="tds-sum-card"><div class="tds-sum-lbl">Net Payment</div><div class="tds-sum-val blue">{{ fmtCur(totalNet) }}</div></div>
    </div>

    <div class="tds-card">
      <table class="tds-table">
        <thead><tr>
          <th @click="sort('name')" class="sortable">Voucher # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
          <th>Party</th>
          <th>TDS Section</th>
          <th class="ta-r">Gross Amount</th>
          <th class="ta-r">TDS Rate %</th>
          <th class="ta-r">TDS Amount</th>
          <th class="ta-r">Net Amount</th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 8" :key="n"><td colspan="8"><div class="tds-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="e in sorted" :key="e.name" class="tds-row">
              <td><span class="tds-code">{{ e.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(e.posting_date) }}</td>
              <td>{{ e.party||e.supplier||e.customer||'—' }}</td>
              <td><span class="tds-section-badge">{{ e.tax_withholding_category||e.account||'—' }}</span></td>
              <td class="ta-r mono-sm">{{ fmtCur(e.base_tax_amount+e.tax_amount) }}</td>
              <td class="ta-r mono-sm text-muted">{{ e.rate||0 }}%</td>
              <td class="ta-r mono-sm red">{{ fmtCur(e.tax_amount) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(e.base_tax_amount) }}</td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="tds-empty">No TDS transactions found</td></tr>
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
import { flt, fmtDate } from "../utils/format.js";
const { toast } = useToast();
const list=ref([]),loading=ref(false),search=ref(""),periodFilter=ref("");
const sortCol=ref("posting_date"),sortDir=ref("desc");
const now=new Date();
function makePeriods(){const ps=[];for(let i=0;i<12;i++){const d=new Date(now.getFullYear(),now.getMonth()-i,1);const v=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;const l=d.toLocaleString("en-IN",{month:"long",year:"numeric"});ps.push({v,l});}return ps;}
const periods=makePeriods();
async function load(){loading.value=true;try{const co=await resolveCompany();const f=[["company","=",co]];if(periodFilter.value){const[yr,mo]=periodFilter.value.split("-");f.push(["posting_date",">=",`${yr}-${mo}-01`]);f.push(["posting_date","<=",`${yr}-${mo}-${new Date(+yr,+mo,0).getDate()}`]);}list.value=await apiList("Tax Withholding Account",{fields:["name","posting_date","party","supplier","customer","account","tax_withholding_category","rate","tax_amount","base_tax_amount"],filters:f,limit:500,order:"posting_date desc"});}catch(e){toast.error(e.message||"Failed to load TDS data");}finally{loading.value=false;}}
const totalTds=computed(()=>list.value.reduce((s,e)=>s+flt(e.tax_amount),0));
const totalGross=computed(()=>list.value.reduce((s,e)=>s+flt(e.base_tax_amount)+flt(e.tax_amount),0));
const totalNet=computed(()=>list.value.reduce((s,e)=>s+flt(e.base_tax_amount),0));
const filtered=computed(()=>{if(!search.value.trim())return list.value;const q=search.value.toLowerCase();return list.value.filter(e=>(e.party||e.supplier||e.customer||"").toLowerCase().includes(q)||(e.tax_withholding_category||e.account||"").toLowerCase().includes(q));});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
onMounted(load);
</script>
<style scoped>
.tds-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.tds-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.tds-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:240px;}
.tds-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.tds-select{border:1px solid #e5e7eb;border-radius:8px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.tds-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.tds-btn-ghost:hover{background:#f9fafb;}
.tds-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.tds-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.tds-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.tds-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.blue{color:#2563eb!important;}.red{color:#dc2626!important;}
.tds-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.tds-table{width:100%;border-collapse:collapse;font-size:13px;}
.tds-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.tds-table th.sortable{cursor:pointer;user-select:none;}.tds-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.tds-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;}
.tds-row:last-child td{border-bottom:none;}.tds-row:hover td{background:#f9fafb;}
.tds-code{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.tds-section-badge{background:#eff6ff;color:#2563eb;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.tds-empty{text-align:center;color:#9ca3af;padding:48px!important;}
.tds-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
