<template>
  <div class="g3-page">
    <div class="g3-topbar">
      <div class="g3-title-block">
        <div class="g3-title">GSTR-3B</div>
        <div class="g3-subtitle">Monthly Self-Declaration Return</div>
      </div>
      <div class="g3-controls">
        <select v-model="period" class="g3-select">
          <option v-for="p in periods" :key="p.v" :value="p.v">{{ p.l }}</option>
        </select>
        <button class="g3-btn-primary" @click="load"><span v-html="icon('refresh',13)"></span> Compute</button>
      </div>
    </div>

    <template v-if="!loading && data">
      <!-- 3.1 Outward Supplies -->
      <div class="g3-card">
        <div class="g3-card-header">3.1 Details of Outward Supplies and Inward Supplies Liable to Reverse Charge</div>
        <table class="g3-table">
          <thead><tr><th>Nature of Supplies</th><th class="ta-r">Total Taxable Value</th><th class="ta-r">IGST</th><th class="ta-r">CGST</th><th class="ta-r">SGST/UTGST</th><th class="ta-r">Cess</th></tr></thead>
          <tbody>
            <tr class="g3-row"><td>(a) Outward taxable supplies (other than zero rated, nil rated and exempted)</td><td class="ta-r mono-sm">{{ fmtCur(data.taxable_value) }}</td><td class="ta-r mono-sm">{{ fmtCur(data.igst) }}</td><td class="ta-r mono-sm">{{ fmtCur(data.cgst) }}</td><td class="ta-r mono-sm">{{ fmtCur(data.sgst) }}</td><td class="ta-r mono-sm">—</td></tr>
            <tr class="g3-row"><td>(b) Outward taxable supplies (zero rated)</td><td class="ta-r mono-sm text-muted">0.00</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td></tr>
            <tr class="g3-row"><td>(c) Other outward supplies (nil rated, exempted)</td><td class="ta-r mono-sm text-muted">0.00</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td></tr>
            <tr class="g3-row"><td>(d) Inward supplies (liable to reverse charge)</td><td class="ta-r mono-sm text-muted">0.00</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td></tr>
            <tr class="g3-row g3-total"><td><strong>Total Outward Tax Liability</strong></td><td class="ta-r mono-sm"><strong>{{ fmtCur(data.taxable_value) }}</strong></td><td class="ta-r mono-sm green"><strong>{{ fmtCur(data.total_tax) }}</strong></td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td><td class="ta-r mono-sm text-muted">—</td></tr>
          </tbody>
        </table>
      </div>

      <!-- 4 ITC -->
      <div class="g3-card">
        <div class="g3-card-header">4 Eligible ITC (Input Tax Credit)</div>
        <table class="g3-table">
          <thead><tr><th>Details</th><th class="ta-r">IGST</th><th class="ta-r">CGST</th><th class="ta-r">SGST/UTGST</th></tr></thead>
          <tbody>
            <tr class="g3-row"><td>(A) ITC Available (B2B Purchases)</td><td class="ta-r mono-sm">{{ fmtCur(data.purchase_igst_only) }}</td><td class="ta-r mono-sm">{{ fmtCur(data.purchase_cgst) }}</td><td class="ta-r mono-sm">{{ fmtCur(data.purchase_sgst) }}</td></tr>
            <tr class="g3-row"><td>(B) ITC Reversed</td><td class="ta-r mono-sm text-muted">0.00</td><td class="ta-r mono-sm text-muted">0.00</td><td class="ta-r mono-sm text-muted">0.00</td></tr>
            <tr class="g3-row g3-total"><td><strong>Net ITC Available</strong></td><td class="ta-r mono-sm blue"><strong>{{ fmtCur(data.purchase_igst_only) }}</strong></td><td class="ta-r mono-sm blue"><strong>{{ fmtCur(data.purchase_cgst) }}</strong></td><td class="ta-r mono-sm blue"><strong>{{ fmtCur(data.purchase_sgst) }}</strong></td></tr>
          </tbody>
        </table>
      </div>

      <!-- 5.1 Net Tax Payable -->
      <div class="g3-card">
        <div class="g3-card-header">5.1 Tax Payable and Paid</div>
        <div class="g3-tax-summary">
          <div class="g3-tax-row"><span>Total Output Tax</span><span class="mono-sm red">{{ fmtCur(data.total_tax) }}</span></div>
          <div class="g3-tax-row"><span>Less: ITC</span><span class="mono-sm green">{{ fmtCur(data.purchase_igst) }}</span></div>
          <div class="g3-tax-divider"></div>
          <div class="g3-tax-row g3-tax-total"><span><strong>Net Tax Payable</strong></span><span class="mono-sm" :class="netTax>=0?'red':'green'"><strong>{{ fmtCur(netTax) }}</strong></span></div>
        </div>
      </div>
    </template>

    <div v-else-if="!loading" class="g3-placeholder">
      <div class="g3-ph-icon" v-html="icon('file-text',40)"></div>
      <div class="g3-ph-text">Select a period and click Compute to view GSTR-3B</div>
    </div>

    <div v-if="loading" class="g3-card" style="padding:20px">
      <div v-for="n in 5" :key="n" class="g3-shimmer" style="margin-bottom:10px"></div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed } from "vue";
import { apiList, apiGET, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt } from "../utils/format.js";
const { toast } = useToast();
const loading=ref(false),data=ref(null);
const now=new Date();
function makePeriods(){const ps=[];for(let i=0;i<12;i++){const d=new Date(now.getFullYear(),now.getMonth()-i,1);const v=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,"0")}`;const l=d.toLocaleString("en-IN",{month:"long",year:"numeric"});ps.push({v,l});}return ps;}
const periods=makePeriods();
const period=ref(periods[0].v);
async function load(){loading.value=true;data.value=null;try{const co=await resolveCompany();const [yr,mo]=period.value.split("-");const from=`${yr}-${mo}-01`;const last=new Date(+yr,+mo,0).getDate();const to=`${yr}-${mo}-${String(last).padStart(2,"0")}`;const [summary,sales]=await Promise.all([apiGET("zoho_books_clone.db.queries.get_gstr_summary",{company:co,from_date:from,to_date:to}),apiList("Sales Invoice",{fields:["name","net_total"],filters:[["company","=",co],["posting_date",">=",from],["posting_date","<=",to],["docstatus","=",1],["is_return","=",0]],limit:500})]);const byType=o=>({igst:flt((o||[]).find(r=>r.tax_type==="IGST")?.amount),cgst:flt((o||[]).find(r=>r.tax_type==="CGST")?.amount),sgst:flt((o||[]).find(r=>r.tax_type==="SGST")?.amount)});const out=byType(summary?.output||[]);const itc=byType(summary?.itc||[]);const taxable_value=sales.reduce((s,i)=>s+flt(i.net_total),0);const total_tax=(summary?.totals?.total_output)||0;const purchase_igst=(summary?.totals?.total_itc)||0;data.value={taxable_value,total_tax,igst:out.igst,cgst:out.cgst,sgst:out.sgst,purchase_igst,purchase_igst_only:itc.igst,purchase_cgst:itc.cgst,purchase_sgst:itc.sgst};}catch(e){toast.error(e.message||"Failed to compute GSTR-3B");}finally{loading.value=false;}}
const netTax=computed(()=>data.value?flt(data.value.total_tax)-flt(data.value.purchase_igst):0);
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
</script>
<style scoped>
.g3-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.g3-topbar{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;}
.g3-title{font-size:20px;font-weight:800;color:#111827;}.g3-subtitle{font-size:12px;color:#6b7280;}
.g3-controls{display:flex;align-items:center;gap:10px;}
.g3-select{border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.g3-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.g3-btn-primary:hover{background:#1d4ed8;}
.g3-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.g3-card-header{padding:12px 16px;font-size:12.5px;font-weight:700;color:#374151;border-bottom:1px solid #e5e7eb;background:#f9fafb;}
.g3-table{width:100%;border-collapse:collapse;font-size:12.5px;}
.g3-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:9px 12px;font-size:11px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.ta-r{text-align:right!important;}
.g3-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;}
.g3-row:last-child td{border-bottom:none;}
.g3-row.g3-total td{background:#f9fafb;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}.blue{color:#2563eb!important;}
.g3-tax-summary{display:flex;flex-direction:column;padding:0 16px;}
.g3-tax-row{display:flex;justify-content:space-between;padding:12px 0;border-bottom:1px solid #f3f4f6;font-size:13.5px;}
.g3-tax-divider{height:2px;background:#e5e7eb;margin:4px 0;}
.g3-tax-total{font-size:15px;}
.g3-placeholder{display:flex;flex-direction:column;align-items:center;gap:12px;padding:60px;color:#9ca3af;}
.g3-ph-icon{opacity:.3;}.g3-ph-text{font-size:13.5px;}
.g3-shimmer{height:14px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
</style>
