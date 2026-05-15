<template>
  <div class="ew-page">
    <div class="ew-actions">
      <div class="ew-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search invoice or transporter…" class="ew-search-input" /></div>
      <div class="ew-tab-pills">
        <button v-for="t in tabs" :key="t.v" class="ew-pill" :class="{active:tab===t.v}" @click="tab=t.v">{{ t.l }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="ew-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
      </div>
    </div>

    <div class="ew-summary" v-if="!loading">
      <div class="ew-sum-card"><div class="ew-sum-lbl">Total Invoices</div><div class="ew-sum-val">{{ list.length }}</div></div>
      <div class="ew-sum-card"><div class="ew-sum-lbl">E-Way Bill Generated</div><div class="ew-sum-val green">{{ withBill.length }}</div></div>
      <div class="ew-sum-card"><div class="ew-sum-lbl">Pending</div><div class="ew-sum-val orange">{{ pending.length }}</div></div>
      <div class="ew-sum-card"><div class="ew-sum-lbl">Total Value</div><div class="ew-sum-val">{{ fmtCur(totalValue) }}</div></div>
    </div>

    <div class="ew-card">
      <table class="ew-table">
        <thead><tr>
          <th @click="sort('name')" class="sortable">Invoice # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
          <th>Customer</th>
          <th>Transporter</th>
          <th>Vehicle No.</th>
          <th class="ta-r">Amount</th>
          <th>E-Way Bill #</th>
          <th>Status</th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 8" :key="n"><td colspan="8"><div class="ew-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="inv in sorted" :key="inv.name" class="ew-row" @click="openView(inv)">
              <td><span class="ew-code">{{ inv.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(inv.posting_date) }}</td>
              <td style="max-width:160px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ inv.customer_name||inv.customer }}</td>
              <td class="text-muted">{{ inv.transporter_name||'—' }}</td>
              <td class="mono-sm text-muted">{{ inv.vehicle_no||'—' }}</td>
              <td class="ta-r mono-sm">{{ fmtCur(inv.grand_total) }}</td>
              <td>
                <span v-if="inv.ewaybill" class="ew-irn mono-sm">{{ inv.ewaybill }}</span>
                <span v-else class="text-muted" style="font-size:12px">—</span>
              </td>
              <td><span class="ew-badge" :class="inv.ewaybill?'badge-green':'badge-orange'">{{ inv.ewaybill?'Generated':'Pending' }}</span></td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="ew-empty">No dispatched invoices found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- View / Edit drawer -->
    <div v-if="viewing" class="ew-overlay" @click.self="viewing=null">
      <div class="ew-drawer">
        <div class="ew-drawer-header">
          <span class="ew-drawer-title">{{ viewing.name }}</span>
          <button class="ew-close" @click="viewing=null">✕</button>
        </div>
        <div class="ew-drawer-body">
          <div class="ew-detail-row"><span>Customer</span><span>{{ viewing.customer_name||viewing.customer }}</span></div>
          <div class="ew-detail-row"><span>Date</span><span>{{ fmtDate(viewing.posting_date) }}</span></div>
          <div class="ew-detail-row"><span>Grand Total</span><span class="font-bold">{{ fmtCur(viewing.grand_total) }}</span></div>
          <div class="ew-detail-row"><span>Transporter</span><span>{{ viewing.transporter_name||'—' }}</span></div>
          <div class="ew-detail-row"><span>Vehicle No.</span><span class="mono-sm">{{ viewing.vehicle_no||'—' }}</span></div>

          <div style="margin-top:16px;border-top:1px solid #e5e7eb;padding-top:16px">
            <div class="ew-field-label">E-Way Bill Number</div>
            <input v-model="editBill" class="ew-input" placeholder="Enter 12-digit EWB number" />
            <div class="ew-field-label" style="margin-top:12px">Transporter Name</div>
            <input v-model="editTransporter" class="ew-input" placeholder="Transporter name" />
            <div class="ew-field-label" style="margin-top:12px">Vehicle Number</div>
            <input v-model="editVehicle" class="ew-input" placeholder="e.g. MH12AB1234" />
          </div>
        </div>
        <div class="ew-drawer-footer">
          <button class="ew-btn-ghost" @click="viewing=null">Cancel</button>
          <button class="ew-btn-primary" @click="saveEwb" :disabled="saving">{{ saving?'Saving…':'Save' }}</button>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, computed, onMounted } from "vue";
import { apiList, apiSave, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
const { toast } = useToast();
const list=ref([]),loading=ref(false),search=ref(""),tab=ref("all");
const sortCol=ref("posting_date"),sortDir=ref("desc");
const viewing=ref(null),saving=ref(false);
const editBill=ref(""),editTransporter=ref(""),editVehicle=ref("");
const tabs=[{v:"all",l:"All"},{v:"generated",l:"Generated"},{v:"pending",l:"Pending"}];
async function load(){loading.value=true;try{const co=await resolveCompany();list.value=await apiList("Sales Invoice",{fields:["name","posting_date","customer","customer_name","grand_total","status"],filters:[["company","=",co],["docstatus","=",1],["is_return","=",0]],limit:500,order:"posting_date desc"});}catch(e){toast.error(e.message||"Failed to load e-way bills");}finally{loading.value=false;}}
const withBill=computed(()=>list.value.filter(i=>i.ewaybill));
const pending=computed(()=>list.value.filter(i=>!i.ewaybill));
const totalValue=computed(()=>list.value.reduce((s,i)=>s+flt(i.grand_total),0));
const filtered=computed(()=>{let r=list.value;if(tab.value==="generated")r=withBill.value;else if(tab.value==="pending")r=pending.value;if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(i=>(i.name||"").toLowerCase().includes(q)||(i.customer_name||"").toLowerCase().includes(q)||(i.transporter_name||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
function openView(inv){viewing.value=inv;editBill.value=inv.ewaybill||"";editTransporter.value=inv.transporter_name||"";editVehicle.value=inv.vehicle_no||"";}
async function saveEwb(){saving.value=true;try{const patch={doctype:"Sales Invoice",name:viewing.value.name};if(editBill.value)patch.ewaybill=editBill.value;if(editTransporter.value)patch.transporter_name=editTransporter.value;if(editVehicle.value)patch.vehicle_no=editVehicle.value;await apiSave(patch);toast.success("E-Way Bill updated");viewing.value=null;await load();}catch(e){toast.error(e.message||"Save failed — extended e-Way Bill fields may require India Compliance app");}finally{saving.value=false;}}
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
onMounted(load);
</script>
<style scoped>
.ew-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.ew-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.ew-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:220px;}
.ew-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.ew-tab-pills{display:flex;gap:4px;background:#f3f4f6;border-radius:8px;padding:3px;}
.ew-pill{border:none;background:transparent;border-radius:6px;padding:5px 12px;font-size:12.5px;font-weight:600;color:#6b7280;cursor:pointer;}
.ew-pill.active{background:#fff;color:#2563eb;box-shadow:0 1px 3px rgba(0,0,0,.08);}
.ew-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.ew-btn-primary:hover{background:#1d4ed8;}.ew-btn-primary:disabled{opacity:.6;cursor:not-allowed;}
.ew-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.ew-btn-ghost:hover{background:#f9fafb;}
.ew-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.ew-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.ew-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.ew-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.green{color:#16a34a!important;}.orange{color:#ea580c!important;}
.ew-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.ew-table{width:100%;border-collapse:collapse;font-size:13px;}
.ew-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.ew-table th.sortable{cursor:pointer;user-select:none;}.ew-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.ew-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;cursor:pointer;}
.ew-row:last-child td{border-bottom:none;}.ew-row:hover td{background:#f9fafb;}
.ew-code{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.ew-irn{background:#f3f4f6;padding:2px 6px;border-radius:4px;color:#374151;font-size:11px;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}.font-bold{font-weight:700;}
.ew-badge{display:inline-flex;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}
.ew-empty{text-align:center;color:#9ca3af;padding:48px!important;}
.ew-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.ew-overlay{position:fixed;inset:0;background:rgba(0,0,0,.35);z-index:1000;display:flex;justify-content:flex-end;}
.ew-drawer{width:420px;background:#fff;height:100%;display:flex;flex-direction:column;box-shadow:-4px 0 24px rgba(0,0,0,.12);}
.ew-drawer-header{display:flex;align-items:center;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5e7eb;}
.ew-drawer-title{font-size:15px;font-weight:700;color:#111827;}
.ew-close{background:none;border:none;font-size:16px;color:#6b7280;cursor:pointer;padding:4px;}
.ew-drawer-body{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:0;}
.ew-drawer-footer{padding:16px 20px;border-top:1px solid #e5e7eb;display:flex;gap:8px;justify-content:flex-end;}
.ew-detail-row{display:flex;justify-content:space-between;padding:9px 0;border-bottom:1px solid #f3f4f6;font-size:13px;}
.ew-detail-row span:first-child{color:#6b7280;font-size:12px;}
.ew-field-label{font-size:11.5px;font-weight:600;color:#374151;text-transform:uppercase;letter-spacing:.04em;margin-bottom:5px;}
.ew-input{border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;font:inherit;font-size:13px;outline:none;width:100%;color:#111827;}
.ew-input:focus{border-color:#2563eb;}
</style>
