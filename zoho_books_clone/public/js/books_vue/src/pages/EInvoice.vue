<template>
  <div class="ei-page">
    <div class="ei-actions">
      <div class="ei-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search invoices…" class="ei-search-input" /></div>
      <div class="ei-tab-pills">
        <button v-for="t in tabs" :key="t.v" class="ei-pill" :class="{active:tab===t.v}" @click="tab=t.v">{{ t.l }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="ei-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
      </div>
    </div>

    <div class="ei-summary" v-if="!loading">
      <div class="ei-sum-card"><div class="ei-sum-lbl">Total Invoices</div><div class="ei-sum-val">{{ list.length }}</div></div>
      <div class="ei-sum-card"><div class="ei-sum-lbl">IRN Generated</div><div class="ei-sum-val green">{{ irnGenerated.length }}</div></div>
      <div class="ei-sum-card"><div class="ei-sum-lbl">Pending IRN</div><div class="ei-sum-val orange">{{ irnPending.length }}</div></div>
      <div class="ei-sum-card"><div class="ei-sum-lbl">Cancelled</div><div class="ei-sum-val red">{{ irnCancelled.length }}</div></div>
    </div>

    <div class="ei-card">
      <table class="ei-table">
        <thead><tr>
          <th @click="sort('name')" class="sortable">Invoice # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
          <th>Customer</th>
          <th>GSTIN</th>
          <th class="ta-r">Invoice Value</th>
          <th>IRN</th>
          <th>Status</th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 8" :key="n"><td colspan="7"><div class="ei-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="inv in sorted" :key="inv.name" class="ei-row" @click="openView(inv)">
              <td><span class="ei-code">{{ inv.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(inv.posting_date) }}</td>
              <td>{{ inv.customer_name||inv.customer }}</td>
              <td class="mono-sm text-muted">{{ inv.customer_gstin||'—' }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(inv.grand_total) }}</td>
              <td><span v-if="inv.irn" class="ei-irn" :title="inv.irn">{{ inv.irn.slice(0,16)+'…' }}</span><span v-else class="text-muted" style="font-size:12px">Not Generated</span></td>
              <td><span class="ei-badge" :class="irnStatusClass(inv)">{{ irnStatusLabel(inv) }}</span></td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="7" class="ei-empty">No e-invoices found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- View drawer -->
    <div v-if="viewing" class="ei-overlay" @click.self="viewing=null">
      <div class="ei-drawer">
        <div class="ei-drawer-header"><span class="ei-drawer-title">{{ viewing.name }}</span><button class="ei-close" @click="viewing=null">✕</button></div>
        <div class="ei-drawer-body">
          <div class="ei-detail-row"><span>Customer</span><span>{{ viewing.customer_name||viewing.customer }}</span></div>
          <div class="ei-detail-row"><span>GSTIN</span><span class="mono-sm">{{ viewing.customer_gstin||'—' }}</span></div>
          <div class="ei-detail-row"><span>Date</span><span>{{ fmtDate(viewing.posting_date) }}</span></div>
          <div class="ei-detail-row"><span>Grand Total</span><span class="font-bold">{{ fmtCur(viewing.grand_total) }}</span></div>
          <div class="ei-detail-row"><span>Status</span><span class="ei-badge" :class="irnStatusClass(viewing)">{{ irnStatusLabel(viewing) }}</span></div>
          <div v-if="viewing.irn" class="ei-field" style="margin-top:12px">
            <label>IRN</label>
            <div class="ei-irn-block">{{ viewing.irn }}</div>
          </div>
          <div v-if="viewing.ack_no" class="ei-detail-row"><span>Ack No.</span><span class="mono-sm">{{ viewing.ack_no }}</span></div>
          <div v-if="viewing.ack_date" class="ei-detail-row"><span>Ack Date</span><span class="mono-sm">{{ fmtDate(viewing.ack_date) }}</span></div>
        </div>
        <div class="ei-drawer-footer">
          <button class="ei-btn-ghost" @click="viewing=null">Close</button>
          <button v-if="!viewing.irn" class="ei-btn-primary" @click="generateIRN(viewing)">Generate IRN</button>
        </div>
      </div>
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
const list=ref([]),loading=ref(false),search=ref(""),tab=ref("all");
const sortCol=ref("posting_date"),sortDir=ref("desc");
const viewing=ref(null);
const tabs=[{v:"all",l:"All"},{v:"generated",l:"IRN Generated"},{v:"pending",l:"Pending"},{v:"cancelled",l:"Cancelled"}];
async function load(){loading.value=true;try{const co=await resolveCompany();list.value=await apiList("Sales Invoice",{fields:["name","posting_date","customer","customer_name","grand_total"],filters:[["company","=",co],["docstatus","=",1],["is_return","=",0]],limit:500,order:"posting_date desc"});}catch(e){toast.error(e.message||"Failed to load invoices");}finally{loading.value=false;}}
function irnStatusLabel(inv){if(inv.einvoice_status==="Cancelled")return"Cancelled";if(inv.irn)return"IRN Generated";return"Pending";}
function irnStatusClass(inv){if(inv.einvoice_status==="Cancelled")return"badge-grey";if(inv.irn)return"badge-green";return"badge-orange";}
const irnGenerated=computed(()=>list.value.filter(i=>i.irn&&i.einvoice_status!=="Cancelled"));
const irnPending=computed(()=>list.value.filter(i=>!i.irn));
const irnCancelled=computed(()=>list.value.filter(i=>i.einvoice_status==="Cancelled"));
const filtered=computed(()=>{let r=list.value;if(tab.value==="generated")r=irnGenerated.value;else if(tab.value==="pending")r=irnPending.value;else if(tab.value==="cancelled")r=irnCancelled.value;if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(i=>(i.name||"").toLowerCase().includes(q)||(i.customer_name||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
function openView(inv){viewing.value=inv;}
async function generateIRN(inv){toast.info("IRN generation requires GST portal integration. Configure in Settings > Integrations.");}
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
onMounted(load);
</script>
<style scoped>
.ei-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.ei-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.ei-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;}
.ei-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.ei-tab-pills{display:flex;gap:4px;background:#f3f4f6;border-radius:8px;padding:3px;}
.ei-pill{border:none;background:transparent;border-radius:6px;padding:5px 12px;font-size:12.5px;font-weight:600;color:#6b7280;cursor:pointer;}
.ei-pill.active{background:#fff;color:#2563eb;box-shadow:0 1px 3px rgba(0,0,0,.08);}
.ei-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.ei-btn-primary:hover{background:#1d4ed8;}
.ei-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.ei-btn-ghost:hover{background:#f9fafb;}
.ei-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.ei-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.ei-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.ei-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.green{color:#16a34a!important;}.orange{color:#ea580c!important;}.red{color:#dc2626!important;}
.ei-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.ei-table{width:100%;border-collapse:collapse;font-size:13px;}
.ei-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.ei-table th.sortable{cursor:pointer;user-select:none;}.ei-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.ei-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;cursor:pointer;}
.ei-row:last-child td{border-bottom:none;}.ei-row:hover td{background:#f9fafb;}
.ei-code{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.ei-irn{font-family:monospace;font-size:11px;color:#374151;background:#f3f4f6;padding:2px 6px;border-radius:4px;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}.font-bold{font-weight:700;}
.ei-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.ei-empty{text-align:center;color:#9ca3af;padding:48px!important;}
.ei-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.ei-overlay{position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:1000;display:flex;justify-content:flex-end;}
.ei-drawer{width:420px;background:#fff;height:100%;display:flex;flex-direction:column;box-shadow:-4px 0 24px rgba(0,0,0,.12);}
.ei-drawer-header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5e7eb;}
.ei-drawer-title{font-size:15px;font-weight:700;color:#111827;}
.ei-close{background:none;border:none;font-size:16px;color:#6b7280;cursor:pointer;padding:4px;}
.ei-drawer-body{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:0;}
.ei-drawer-footer{padding:16px 20px;border-top:1px solid #e5e7eb;display:flex;gap:8px;justify-content:flex-end;}
.ei-detail-row{display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid #f3f4f6;font-size:13px;}
.ei-detail-row:last-child{border-bottom:none;}
.ei-detail-row span:first-child{color:#6b7280;font-size:12px;}
.ei-field{display:flex;flex-direction:column;gap:5px;}
.ei-field label{font-size:11.5px;font-weight:600;color:#374151;text-transform:uppercase;letter-spacing:.04em;}
.ei-irn-block{font-family:monospace;font-size:11.5px;color:#374151;background:#f3f4f6;padding:10px;border-radius:6px;word-break:break-all;}
</style>
