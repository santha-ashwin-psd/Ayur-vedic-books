<template>
  <div class="g1-page">
    <div class="g1-topbar">
      <div class="g1-title-block">
        <div class="g1-title">GSTR-1</div>
        <div class="g1-subtitle">Outward Supplies Return</div>
      </div>
      <div class="g1-controls">
        <select v-model="period" class="g1-select">
          <option v-for="p in periods" :key="p.v" :value="p.v">{{ p.l }}</option>
        </select>
        <button class="g1-btn-primary" @click="load"><span v-html="icon('refresh',13)"></span> Generate</button>
      </div>
    </div>

    <div class="g1-summary" v-if="!loading && data">
      <div class="g1-sum-card"><div class="g1-sum-lbl">B2B Invoices</div><div class="g1-sum-val">{{ data.b2b_count||0 }}</div></div>
      <div class="g1-sum-card"><div class="g1-sum-lbl">B2C Invoices</div><div class="g1-sum-val">{{ data.b2c_count||0 }}</div></div>
      <div class="g1-sum-card"><div class="g1-sum-lbl">Total Taxable Value</div><div class="g1-sum-val blue">{{ fmtCur(data.total_taxable) }}</div></div>
      <div class="g1-sum-card"><div class="g1-sum-lbl">Total Tax</div><div class="g1-sum-val green">{{ fmtCur(data.total_tax) }}</div></div>
    </div>

    <template v-if="!loading && data">
      <div class="g1-card">
        <div class="g1-card-header">4A, 4B, 4C, 6B, 6C – B2B Invoices</div>
        <table class="g1-table">
          <thead><tr><th>GSTIN of Recipient</th><th>Invoice #</th><th>Date</th><th class="ta-r">Invoice Value</th><th class="ta-r">Taxable Value</th><th class="ta-r">IGST</th><th class="ta-r">CGST</th><th class="ta-r">SGST</th></tr></thead>
          <tbody>
            <tr v-for="inv in (data.b2b||[])" :key="inv.name" class="g1-row">
              <td class="mono-sm">{{ inv.customer_gstin||'—' }}</td>
              <td><span class="g1-code">{{ inv.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(inv.posting_date) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(inv.grand_total) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(inv.net_total) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(inv.total_taxes_and_charges) }}</td>
              <td class="ta-r mono-sm text-muted">—</td>
              <td class="ta-r mono-sm text-muted">—</td>
            </tr>
            <tr v-if="!(data.b2b||[]).length"><td colspan="8" class="g1-empty">No B2B invoices in this period</td></tr>
          </tbody>
        </table>
      </div>

      <div class="g1-card">
        <div class="g1-card-header">5 – B2C (Large) Invoices</div>
        <table class="g1-table">
          <thead><tr><th>Invoice #</th><th>Date</th><th class="ta-r">Invoice Value</th><th class="ta-r">Taxable Value</th><th class="ta-r">Total Tax</th></tr></thead>
          <tbody>
            <tr v-for="inv in (data.b2c||[])" :key="inv.name" class="g1-row">
              <td><span class="g1-code">{{ inv.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(inv.posting_date) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(inv.grand_total) }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(inv.net_total) }}</td>
              <td class="ta-r mono-sm green">{{ fmtCur(inv.total_taxes_and_charges) }}</td>
            </tr>
            <tr v-if="!(data.b2c||[]).length"><td colspan="5" class="g1-empty">No B2C invoices in this period</td></tr>
          </tbody>
        </table>
      </div>
    </template>

    <div v-else-if="!loading" class="g1-placeholder">
      <div class="g1-ph-icon" v-html="icon('file-text',40)"></div>
      <div class="g1-ph-text">Select a period and click Generate to view GSTR-1 data</div>
    </div>

    <div v-if="loading" class="g1-card">
      <div v-for="n in 6" :key="n" class="g1-shimmer" style="margin-bottom:8px"></div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue";
import { apiList, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
const { toast } = useToast();
const loading=ref(false),data=ref(null);
const now=new Date();
function makePeriods(){const ps=[];for(let i=0;i<12;i++){const d=new Date(now.getFullYear(),now.getMonth()-i,1);const v=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;const l=d.toLocaleString("en-IN",{month:"long",year:"numeric"});ps.push({v,l});}return ps;}
const periods=makePeriods();
const period=ref(periods[0].v);
async function load(){loading.value=true;data.value=null;try{const co=await resolveCompany();const [yr,mo]=period.value.split("-");const from=`${yr}-${mo}-01`;const last=new Date(+yr,+mo,0).getDate();const to=`${yr}-${mo}-${String(last).padStart(2,"0")}`;const all=await apiList("Sales Invoice",{fields:["name","posting_date","customer","customer_gstin","grand_total","net_total","total_taxes_and_charges","is_return"],filters:[["company","=",co],["posting_date",">=",from],["posting_date","<=",to],["docstatus","=",1],["is_return","=",0]],limit:500,order:"posting_date asc"});const b2b=all.filter(i=>i.customer_gstin);const b2c=all.filter(i=>!i.customer_gstin);data.value={b2b,b2c,b2b_count:b2b.length,b2c_count:b2c.length,total_taxable:all.reduce((s,i)=>s+flt(i.net_total),0),total_tax:all.reduce((s,i)=>s+flt(i.total_taxes_and_charges),0)};}catch(e){toast.error(e.message||"Failed to load GSTR-1");}finally{loading.value=false;}}
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
</script>
<style scoped>
.g1-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.g1-topbar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;}
.g1-title{font-size:20px;font-weight:800;color:#111827;}.g1-subtitle{font-size:12px;color:#6b7280;}
.g1-controls{display:flex;align-items:center;gap:10px;}
.g1-select{border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.g1-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.g1-btn-primary:hover{background:#1d4ed8;}
.g1-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.g1-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.g1-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.g1-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.blue{color:#2563eb!important;}.green{color:#16a34a!important;}
.g1-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.g1-card-header{padding:12px 16px;font-size:12.5px;font-weight:700;color:#374151;border-bottom:1px solid #e5e7eb;background:#f9fafb;}
.g1-table{width:100%;border-collapse:collapse;font-size:13px;}
.g1-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:9px 12px;font-size:11px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.ta-r{text-align:right!important;}
.g1-row td{padding:9px 12px;border-bottom:1px solid #f3f4f6;}
.g1-row:last-child td{border-bottom:none;}.g1-row:hover td{background:#f9fafb;}
.g1-code{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.g1-empty{text-align:center;color:#9ca3af;padding:32px!important;}
.g1-placeholder{display:flex;flex-direction:column;align-items:center;gap:12px;padding:60px;color:#9ca3af;}
.g1-ph-icon{opacity:.3;}.g1-ph-text{font-size:13.5px;}
.g1-shimmer{height:14px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
