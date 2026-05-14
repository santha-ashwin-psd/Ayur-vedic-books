<template>
  <div class="chq-page">
    <div class="chq-actions">
      <div class="chq-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search cheques…" class="chq-search-input" /></div>
      <div class="chq-pills"><button v-for="t in tabs" :key="t.key" class="chq-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">{{ t.label }}</button></div>
      <div style="display:flex;gap:8px;margin-left:auto"><button class="chq-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button></div>
    </div>
    <div class="chq-summary" v-if="!loading">
      <div class="chq-sum-card"><div class="chq-sum-lbl">Total Cheques</div><div class="chq-sum-val">{{ list.length }}</div></div>
      <div class="chq-sum-card"><div class="chq-sum-lbl">Total Amount</div><div class="chq-sum-val">{{ fmtCur(totalAmount) }}</div></div>
      <div class="chq-sum-card"><div class="chq-sum-lbl">Received</div><div class="chq-sum-val green">{{ counts.receive }}</div></div>
      <div class="chq-sum-card"><div class="chq-sum-lbl">Paid Out</div><div class="chq-sum-val red">{{ counts.pay }}</div></div>
    </div>
    <div class="chq-card">
      <table class="chq-table">
        <thead><tr>
          <th @click="sort('name')" class="sortable">Payment # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('party')" class="sortable">Party <span v-html="sortArrow('party')"></span></th>
          <th @click="sort('reference_no')" class="sortable">Cheque No <span v-html="sortArrow('reference_no')"></span></th>
          <th @click="sort('payment_date')" class="sortable">Date <span v-html="sortArrow('payment_date')"></span></th>
          <th>Type</th>
          <th @click="sort('paid_amount')" class="sortable ta-r">Amount <span v-html="sortArrow('paid_amount')"></span></th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 6" :key="n"><td colspan="6"><div class="chq-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="p in sorted" :key="p.name" class="chq-row" @click="openView(p)">
              <td><span class="chq-num">{{ p.name }}</span></td>
              <td>{{ p.party||'—' }}</td>
              <td class="mono-sm text-muted">{{ p.reference_no||'—' }}</td>
              <td class="mono-sm text-muted">{{ fmtDate(p.payment_date) }}</td>
              <td><span class="chq-badge" :class="p.payment_type==='Receive'?'badge-green':'badge-red'">{{ p.payment_type==='Receive'?'Received':'Paid Out' }}</span></td>
              <td class="ta-r mono-sm">{{ fmtCur(p.paid_amount) }}</td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="6" class="chq-empty">No cheque payments found</td></tr>
          </template>
        </tbody>
      </table>
    </div>
    <div v-if="viewOpen" class="chq-overlay" @click.self="viewOpen=false"></div>
    <div class="chq-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="chq-dheader"><div class="chq-dheader-title">{{ viewDoc.name }}</div><button class="chq-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button></div>
        <div class="chq-dbody">
          <div class="chq-meta-grid">
            <div><div class="chq-meta-lbl">Party</div><div>{{ viewDoc.party||'—' }}</div></div>
            <div><div class="chq-meta-lbl">Cheque No</div><div class="mono-sm">{{ viewDoc.reference_no||'—' }}</div></div>
            <div><div class="chq-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.payment_date) }}</div></div>
            <div><div class="chq-meta-lbl">Amount</div><div class="mono-sm">{{ fmtCur(viewDoc.paid_amount) }}</div></div>
          </div>
        </div>
        <div class="chq-dfooter"><button class="chq-btn-ghost" @click="viewOpen=false">Close</button></div>
      </template>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from "vue";
import { apiList } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
const { toast } = useToast();
const activeTab=ref("all");
const tabs=[{key:"all",label:"All"},{key:"Receive",label:"Received"},{key:"Pay",label:"Paid Out"}];
const list=ref([]),loading=ref(false),search=ref("");
const viewOpen=ref(false),viewDoc=ref(null);
const sortCol=ref("payment_date"),sortDir=ref("desc");
async function load(){loading.value=true;try{list.value=await apiList("Payment Entry",{fields:["name","party","payment_type","reference_no","reference_date","payment_date","paid_amount","docstatus"],filters:[["mode_of_payment","=","Cheque"]],limit:200,order:"payment_date desc"});}catch(e){toast.error(e.message||"Failed to load cheques");}finally{loading.value=false;}}
const filtered=computed(()=>{let r=list.value;if(activeTab.value!=="all")r=r.filter(p=>p.payment_type===activeTab.value);if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(p=>(p.party||"").toLowerCase().includes(q)||(p.reference_no||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const totalAmount=computed(()=>list.value.reduce((s,p)=>s+flt(p.paid_amount),0));
const counts=computed(()=>({receive:list.value.filter(p=>p.payment_type==="Receive").length,pay:list.value.filter(p=>p.payment_type==="Pay").length}));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
function openView(p){viewDoc.value=p;viewOpen.value=true;}
onMounted(load);
</script>
<style scoped>
.chq-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.chq-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.chq-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.chq-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.chq-pills{display:flex;gap:6px;}
.chq-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.chq-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.chq-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.chq-btn-ghost:hover{background:#f9fafb;}
.chq-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.chq-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.chq-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.chq-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}
.chq-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.chq-table{width:100%;border-collapse:collapse;font-size:13px;}
.chq-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.chq-table th.sortable{cursor:pointer;user-select:none;}.chq-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.chq-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;cursor:pointer;}
.chq-row:last-child td{border-bottom:none;}.chq-row:hover td{background:#f9fafb;}
.chq-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.chq-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-red{background:#fee2e2;color:#dc2626;}
.chq-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.chq-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.chq-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.chq-drawer{position:fixed;top:0;right:-380px;bottom:0;width:380px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.chq-drawer.open{right:0;}
.chq-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.chq-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.chq-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.chq-dclose:hover{background:#f3f4f6;}
.chq-dbody{flex:1;overflow-y:auto;padding:20px;}
.chq-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.chq-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.chq-dfooter{display:flex;justify-content:flex-end;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
