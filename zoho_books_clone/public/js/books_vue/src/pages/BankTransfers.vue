<template>
  <div class="btr-page">
    <div class="btr-actions">
      <div class="btr-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search transfers…" class="btr-search-input" />
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="btr-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="btr-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Transfer</button>
      </div>
    </div>

    <div class="btr-summary" v-if="!loading">
      <div class="btr-sum-card"><div class="btr-sum-lbl">Total Transfers</div><div class="btr-sum-val">{{ list.length }}</div></div>
      <div class="btr-sum-card"><div class="btr-sum-lbl">Total Amount</div><div class="btr-sum-val">{{ fmtCur(totalAmount) }}</div></div>
      <div class="btr-sum-card"><div class="btr-sum-lbl">This Month</div><div class="btr-sum-val blue">{{ fmtCur(monthAmount) }}</div></div>
      <div class="btr-sum-card"><div class="btr-sum-lbl">Draft</div><div class="btr-sum-val orange">{{ list.filter(t=>t.docstatus===0).length }}</div></div>
    </div>

    <div class="btr-card">
      <table class="btr-table">
        <thead>
          <tr>
            <th @click="sort('name')" class="sortable">Transfer # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
            <th>From Account</th><th>To Account</th>
            <th>Status</th>
            <th @click="sort('total_debit')" class="sortable ta-r">Amount <span v-html="sortArrow('total_debit')"></span></th>
            <th style="width:50px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="7"><div class="btr-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="t in sorted" :key="t.name" class="btr-row" @click="openView(t)">
              <td><span class="btr-num">{{ t.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(t.posting_date) }}</td>
              <td class="text-muted">{{ t.accounts?.[0]?.account||'—' }}</td>
              <td class="text-muted">{{ t.accounts?.[1]?.account||'—' }}</td>
              <td><span class="btr-badge" :class="t.docstatus===0?'badge-orange':t.docstatus===1?'badge-green':'badge-grey'">{{ t.docstatus===0?'Draft':t.docstatus===1?'Submitted':'Cancelled' }}</span></td>
              <td class="ta-r mono-sm">{{ fmtCur(t.total_debit) }}</td>
              <td @click.stop><button class="btr-act-btn" @click="openView(t)"><span v-html="icon('eye',13)"></span></button></td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="7" class="btr-empty">No transfers found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create Drawer -->
    <div v-if="drawerOpen" class="btr-overlay" @click.self="drawerOpen=false"></div>
    <div class="btr-drawer" :class="{open:drawerOpen}">
      <div class="btr-dheader">
        <div class="btr-dheader-title">New Bank Transfer</div>
        <button class="btr-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="btr-dbody">
        <div class="btr-fields-grid">
          <div class="btr-field">
            <label class="btr-label">Transfer Date <span class="req">*</span></label>
            <input v-model="form.posting_date" type="date" class="btr-input" />
          </div>
          <div class="btr-field">
            <label class="btr-label">Amount <span class="req">*</span></label>
            <input v-model.number="form.amount" type="number" min="0" step="0.01" class="btr-input" placeholder="0.00" />
          </div>
          <div class="btr-field" style="grid-column:1/-1">
            <label class="btr-label">From Account <span class="req">*</span></label>
            <SearchableSelect v-model="form.from_account" :options="accounts" placeholder="Debit account…" @search="fetchAccounts" />
          </div>
          <div class="btr-field" style="grid-column:1/-1">
            <label class="btr-label">To Account <span class="req">*</span></label>
            <SearchableSelect v-model="form.to_account" :options="accounts" placeholder="Credit account…" @search="fetchAccounts" />
          </div>
          <div class="btr-field" style="grid-column:1/-1">
            <label class="btr-label">Remarks</label>
            <textarea v-model="form.remark" rows="2" class="btr-input" placeholder="Optional…"></textarea>
          </div>
        </div>
      </div>
      <div class="btr-dfooter">
        <button class="btr-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="btr-btn-save" :disabled="drawerSaving" @click="saveTransfer(0)"><span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}</button>
        <button class="btr-btn-primary" :disabled="drawerSaving" @click="saveTransfer(1)"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}</button>
      </div>
    </div>

    <!-- View -->
    <div v-if="viewOpen" class="btr-overlay" @click.self="viewOpen=false"></div>
    <div class="btr-drawer btr-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="btr-dheader"><div class="btr-dheader-title">{{ viewDoc.name }}</div><button class="btr-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button></div>
        <div class="btr-dbody">
          <div class="btr-meta-grid">
            <div><div class="btr-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
            <div><div class="btr-meta-lbl">Amount</div><div class="mono-sm">{{ fmtCur(viewDoc.total_debit) }}</div></div>
          </div>
        </div>
        <div class="btr-dfooter"><button class="btr-btn-ghost" @click="viewOpen=false">Close</button></div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiSubmit, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const list=ref([]),loading=ref(false),search=ref("");
const drawerOpen=ref(false),drawerSaving=ref(false);
const viewOpen=ref(false),viewDoc=ref(null);
const accounts=ref([]);
const sortCol=ref("posting_date"),sortDir=ref("desc");
const form=reactive({posting_date:new Date().toISOString().slice(0,10),amount:0,from_account:"",to_account:"",remark:""});
const now=new Date();
const monthStart=new Date(now.getFullYear(),now.getMonth(),1).toISOString().slice(0,10);

async function load(){loading.value=true;try{const co=await resolveCompany();const rows=await apiList("Journal Entry",{fields:["name","posting_date","voucher_type","total_debit","docstatus","remark"],filters:[["company","=",co],["voucher_type","=","Bank Entry"]],limit:200,order:"posting_date desc"});if(rows.length){const names=rows.map(r=>r.name);const accs=await apiList("Journal Entry Account",{fields:["parent","account","debit","credit"],filters:[["parent","in",names]],limit:rows.length*3});for(const je of rows){je.accounts=accs.filter(a=>a.parent===je.name);}}list.value=rows;}catch(e){toast.error(e.message||"Failed to load transfers");}finally{loading.value=false;}}
const filtered=computed(()=>{if(!search.value.trim())return list.value;const q=search.value.toLowerCase();return list.value.filter(t=>(t.name||"").toLowerCase().includes(q)||(t.remark||"").toLowerCase().includes(q));});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const totalAmount=computed(()=>list.value.filter(t=>t.docstatus===1).reduce((s,t)=>s+flt(t.total_debit),0));
const monthAmount=computed(()=>list.value.filter(t=>t.posting_date>=monthStart&&t.docstatus===1).reduce((s,t)=>s+flt(t.total_debit),0));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
function openNew(){Object.assign(form,{posting_date:new Date().toISOString().slice(0,10),amount:0,from_account:"",to_account:"",remark:""});accounts.value=[];fetchAccounts("");drawerOpen.value=true;}
function openView(t){viewDoc.value=t;viewOpen.value=true;}
async function fetchAccounts(q=""){try{const co=await resolveCompany();const r=await apiList("Account",{fields:["name"],filters:[["account_type","in",["Bank","Cash"]],["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:20});accounts.value=r.map(x=>({label:x.name,value:x.name}));}catch{accounts.value=[];}}
async function saveTransfer(submit){
  if(!form.from_account||!form.to_account)return toast.error("Both accounts are required");
  if(!flt(form.amount))return toast.error("Amount is required");
  drawerSaving.value=true;
  try{const company=await resolveCompany();const doc={doctype:"Journal Entry",company,posting_date:form.posting_date,voucher_type:"Bank Entry",remark:form.remark||"",accounts:[{doctype:"Journal Entry Account",account:form.from_account,credit:flt(form.amount),debit:0},{doctype:"Journal Entry Account",account:form.to_account,debit:flt(form.amount),credit:0}]};const saved=await apiSave(doc);if(submit)await apiSubmit("Journal Entry",saved.name);toast.success(`Transfer ${saved?.name||""} ${submit?"submitted":"saved"}`);drawerOpen.value=false;await load();}
  catch(e){toast.error(e.message||"Failed to save transfer");}finally{drawerSaving.value=false;}
}
onMounted(load);
</script>

<style scoped>
.btr-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.btr-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.btr-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;}
.btr-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.btr-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.btr-btn-primary:hover{background:#1d4ed8;}.btr-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.btr-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.btr-btn-ghost:hover{background:#f9fafb;}
.btr-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.btr-btn-save:hover{background:#dcfce7;}.btr-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.btr-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.btr-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.btr-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.btr-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.blue{color:#2563eb!important;}.orange{color:#ea580c!important;}
.btr-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.btr-table{width:100%;border-collapse:collapse;font-size:13px;}
.btr-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.btr-table th.sortable{cursor:pointer;user-select:none;}.btr-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.btr-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.btr-row:last-child td{border-bottom:none;}.btr-row:hover td{background:#f9fafb;}
.btr-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.btr-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.btr-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.btr-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.btr-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.btr-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.btr-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.btr-drawer{position:fixed;top:0;right:-480px;bottom:0;width:480px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.btr-drawer.open{right:0;}
.btr-view-drawer{width:380px;right:-380px;}.btr-view-drawer.open{right:0;}
.btr-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.btr-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.btr-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.btr-dclose:hover{background:#f3f4f6;color:#111827;}
.btr-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.btr-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.btr-field{display:flex;flex-direction:column;gap:4px;}
.btr-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.btr-input{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.btr-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
textarea.btr-input{resize:vertical;}
.btr-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.btr-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.btr-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
