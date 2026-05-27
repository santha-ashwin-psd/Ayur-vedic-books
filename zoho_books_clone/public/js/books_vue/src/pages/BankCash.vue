<template>
  <div class="cash-page">
    <div class="cash-actions">
      <div class="cash-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search cash transactions…" class="cash-search-input" /></div>
      <div class="cash-pills"><button v-for="t in tabs" :key="t.key" class="cash-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">{{ t.label }}</button></div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="cash-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="cash-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Cash Entry</button>
      </div>
    </div>
    <div class="cash-summary" v-if="!loading">
      <div class="cash-sum-card"><div class="cash-sum-lbl">Cash In</div><div class="cash-sum-val green">{{ fmtCur(cashIn) }}</div></div>
      <div class="cash-sum-card"><div class="cash-sum-lbl">Cash Out</div><div class="cash-sum-val red">{{ fmtCur(cashOut) }}</div></div>
      <div class="cash-sum-card"><div class="cash-sum-lbl">Net Cash</div><div class="cash-sum-val" :class="(cashIn-cashOut)>=0?'green':'red'">{{ fmtCur(cashIn-cashOut) }}</div></div>
      <div class="cash-sum-card"><div class="cash-sum-lbl">Entries</div><div class="cash-sum-val">{{ filtered.length }}</div></div>
    </div>
    <div class="cash-card">
      <table class="cash-table">
        <thead><tr>
          <th @click="sort('name')" class="sortable">Entry # <span v-html="sortArrow('name')"></span></th>
          <th @click="sort('party')" class="sortable">Party <span v-html="sortArrow('party')"></span></th>
          <th @click="sort('payment_date')" class="sortable">Date <span v-html="sortArrow('payment_date')"></span></th>
          <th>Type</th>
          <th @click="sort('paid_amount')" class="sortable ta-r">Amount <span v-html="sortArrow('paid_amount')"></span></th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 6" :key="n"><td colspan="5"><div class="cash-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="p in sorted" :key="p.name" class="cash-row" @click="openView(p)">
              <td><span class="cash-num">{{ p.name }}</span></td>
              <td>{{ p.party||'—' }}</td>
              <td class="mono-sm text-muted">{{ fmtDate(p.payment_date) }}</td>
              <td><span class="cash-badge" :class="p.payment_type==='Receive'?'badge-green':'badge-red'">{{ p.payment_type==='Receive'?'Cash In':'Cash Out' }}</span></td>
              <td class="ta-r mono-sm">{{ fmtCur(p.paid_amount) }}</td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="5" class="cash-empty">No cash entries found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- New Entry Drawer -->
    <div v-if="drawerOpen" class="cash-overlay" @click.self="drawerOpen=false"></div>
    <div class="cash-drawer" :class="{open:drawerOpen}">
      <div class="cash-dheader"><div class="cash-dheader-title">New Cash Entry</div><button class="cash-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button></div>
      <div class="cash-dbody">
        <div class="cash-fields-grid">
          <div class="cash-field" style="grid-column:1/-1">
            <label class="cash-label">Type <span class="req">*</span></label>
            <div class="cash-radio-group">
              <label class="cash-radio" :class="{checked:form.payment_type==='Receive'}" @click="form.payment_type='Receive'"><span class="cash-radio-dot" :class="{on:form.payment_type==='Receive'}"></span> Cash In (Received)</label>
              <label class="cash-radio" :class="{checked:form.payment_type==='Pay'}" @click="form.payment_type='Pay'"><span class="cash-radio-dot" :class="{on:form.payment_type==='Pay'}"></span> Cash Out (Paid)</label>
            </div>
          </div>
          <div class="cash-field"><label class="cash-label">Date <span class="req">*</span></label><input v-model="form.payment_date" type="date" class="cash-input" /></div>
          <div class="cash-field"><label class="cash-label">Amount <span class="req">*</span></label><input v-model.number="form.paid_amount" type="number" min="0" step="0.01" class="cash-input" /></div>
          <div class="cash-field" style="grid-column:1/-1"><label class="cash-label">Party <span class="req">*</span></label><input v-model="form.party" type="text" class="cash-input" :placeholder="form.payment_type==='Receive'?'Customer name':'Vendor / supplier name'" /></div>
          <div class="cash-field" style="grid-column:1/-1"><label class="cash-label">Remarks</label><textarea v-model="form.remarks" rows="2" class="cash-input" placeholder="Optional…"></textarea></div>
        </div>
      </div>
      <div class="cash-dfooter">
        <button class="cash-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="cash-btn-primary" :disabled="drawerSaving" @click="saveCash"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}</button>
      </div>
    </div>

    <div v-if="viewOpen" class="cash-overlay" @click.self="viewOpen=false"></div>
    <div class="cash-drawer" :class="{open:viewOpen}" style="width:360px;right:-360px">
      <template v-if="viewDoc">
        <div class="cash-dheader"><div class="cash-dheader-title">{{ viewDoc.name }}</div><button class="cash-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button></div>
        <div class="cash-dbody">
          <div class="cash-meta-grid">
            <div><div class="cash-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.payment_date) }}</div></div>
            <div><div class="cash-meta-lbl">Amount</div><div class="mono-sm">{{ fmtCur(viewDoc.paid_amount) }}</div></div>
            <div><div class="cash-meta-lbl">Party</div><div>{{ viewDoc.party||'—' }}</div></div>
            <div><div class="cash-meta-lbl">Type</div><div><span class="cash-badge" :class="viewDoc.payment_type==='Receive'?'badge-green':'badge-red'">{{ viewDoc.payment_type==='Receive'?'Cash In':'Cash Out' }}</span></div></div>
          </div>
        </div>
        <div class="cash-dfooter"><button class="cash-btn-ghost" @click="viewOpen=false">Close</button></div>
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
const { toast } = useToast();
const cashAccount=ref(""),receivableAccount=ref(""),payableAccount=ref(""),companyCurrency=ref("INR");
async function loadAccounts(){try{const co=await resolveCompany();const[cashAcc,recvAcc,payAcc,comp]=await Promise.all([apiList("Account",{fields:["name"],filters:[["company","=",co],["account_type","=","Cash"],["is_group","=",0]],limit:1}),apiList("Account",{fields:["name"],filters:[["company","=",co],["account_type","=","Receivable"],["is_group","=",0]],limit:1}),apiList("Account",{fields:["name"],filters:[["company","=",co],["account_type","=","Payable"],["is_group","=",0]],limit:1}),apiList("Books Company",{fields:["currency"],filters:[["name","=",co]],limit:1})]);cashAccount.value=cashAcc[0]?.name||"";receivableAccount.value=recvAcc[0]?.name||"";payableAccount.value=payAcc[0]?.name||"";companyCurrency.value=comp[0]?.currency||"INR";}catch(e){console.error("Failed to load accounts",e);}}
const activeTab=ref("all");
const tabs=[{key:"all",label:"All"},{key:"Receive",label:"Cash In"},{key:"Pay",label:"Cash Out"}];
const list=ref([]),loading=ref(false),search=ref("");
const drawerOpen=ref(false),drawerSaving=ref(false);
const viewOpen=ref(false),viewDoc=ref(null);
const sortCol=ref("payment_date"),sortDir=ref("desc");
const form=reactive({payment_type:"Receive",payment_date:new Date().toISOString().slice(0,10),paid_amount:0,party:"",remarks:""});
async function load(){loading.value=true;try{const co=await resolveCompany();list.value=await apiList("Payment Entry",{fields:["name","party","payment_type","payment_date","paid_amount","remarks","docstatus"],filters:[["company","=",co],["mode_of_payment","=","Cash"],["docstatus","=",1]],limit:200,order:"payment_date desc"});}catch(e){toast.error(e.message||"Failed to load cash entries");}finally{loading.value=false;}}
const filtered=computed(()=>{let r=list.value;if(activeTab.value!=="all")r=r.filter(p=>p.payment_type===activeTab.value);if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(p=>(p.party||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const cashIn=computed(()=>list.value.filter(p=>p.payment_type==="Receive").reduce((s,p)=>s+flt(p.paid_amount),0));
const cashOut=computed(()=>list.value.filter(p=>p.payment_type==="Pay").reduce((s,p)=>s+flt(p.paid_amount),0));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
function openNew(){Object.assign(form,{payment_type:"Receive",payment_date:new Date().toISOString().slice(0,10),paid_amount:0,party:"",remarks:""});drawerOpen.value=true;}
function openView(p){viewDoc.value=p;viewOpen.value=true;}
async function saveCash(){if(!flt(form.paid_amount))return toast.error("Amount is required");if(!form.party.trim())return toast.error("Party name is required");if(!cashAccount.value)return toast.error("Cash account not configured — check chart of accounts");drawerSaving.value=true;try{const company=await resolveCompany();const isCashIn=form.payment_type==="Receive";const doc={doctype:"Payment Entry",company,payment_type:form.payment_type,party_type:isCashIn?"Customer":"Supplier",party:form.party,mode_of_payment:"Cash",paid_from:isCashIn?(receivableAccount.value||cashAccount.value):cashAccount.value,paid_to:isCashIn?cashAccount.value:(payableAccount.value||cashAccount.value),paid_from_account_currency:companyCurrency.value,paid_to_account_currency:companyCurrency.value,source_exchange_rate:1,target_exchange_rate:1,paid_amount:flt(form.paid_amount),received_amount:flt(form.paid_amount),payment_date:form.payment_date,remarks:form.remarks||""};const saved=await apiSave(doc);await apiSubmit("Payment Entry",saved.name);toast.success(`Cash entry ${saved?.name||""} created`);drawerOpen.value=false;await load();}catch(e){toast.error(e.message||"Failed to save");}finally{drawerSaving.value=false;}}
onMounted(()=>{load();loadAccounts();});
</script>
<style scoped>
.cash-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.cash-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.cash-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;}
.cash-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.cash-pills{display:flex;gap:6px;}
.cash-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.cash-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.cash-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.cash-btn-primary:hover{background:#1d4ed8;}.cash-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.cash-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.cash-btn-ghost:hover{background:#f9fafb;}
.cash-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.cash-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.cash-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.cash-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}
.cash-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.cash-table{width:100%;border-collapse:collapse;font-size:13px;}
.cash-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.cash-table th.sortable{cursor:pointer;user-select:none;}.cash-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.cash-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;cursor:pointer;}
.cash-row:last-child td{border-bottom:none;}.cash-row:hover td{background:#f9fafb;}
.cash-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.cash-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-red{background:#fee2e2;color:#dc2626;}
.cash-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.cash-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.cash-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.cash-drawer{position:fixed;top:0;right:-440px;bottom:0;width:440px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.cash-drawer.open{right:0;}
.cash-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.cash-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.cash-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.cash-dclose:hover{background:#f3f4f6;}
.cash-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.cash-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.cash-field{display:flex;flex-direction:column;gap:4px;}
.cash-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.cash-input{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.cash-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
textarea.cash-input{resize:vertical;}
.cash-radio-group{display:flex;gap:10px;}
.cash-radio{display:flex;align-items:center;gap:8px;padding:8px 14px;border:1px solid #e5e7eb;border-radius:8px;cursor:pointer;font-size:13px;color:#374151;user-select:none;}
.cash-radio.checked{border-color:#2563eb;background:#eff6ff;color:#2563eb;}
.cash-radio-dot{width:14px;height:14px;border-radius:50%;border:2px solid #d1d5db;display:inline-block;flex-shrink:0;}
.cash-radio-dot.on{border-color:#2563eb;background:#2563eb;box-shadow:inset 0 0 0 3px #fff;}
.cash-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.cash-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.cash-dfooter{display:flex;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
