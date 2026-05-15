<template>
  <div class="br-page">
    <div class="br-actions">
      <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap">
        <select v-model="form.bank_account" class="br-select" style="min-width:220px">
          <option value="">— Select Bank Account —</option>
          <option v-for="a in bankAccounts" :key="a.name" :value="a.name">{{ a.account_name||a.name }}</option>
        </select>
        <input v-model="form.from_date" type="date" class="br-input" />
        <input v-model="form.to_date" type="date" class="br-input" />
        <button class="br-btn-primary" @click="load" :disabled="!form.bank_account">
          <span v-html="icon('refresh',13)"></span> Run
        </button>
      </div>
    </div>

    <div class="br-summary" v-if="!loading && ran">
      <div class="br-sum-card"><div class="br-sum-lbl">Statement Balance</div><div class="br-sum-val">{{ fmtCur(summary.statementBalance) }}</div></div>
      <div class="br-sum-card"><div class="br-sum-lbl">System Balance</div><div class="br-sum-val">{{ fmtCur(summary.systemBalance) }}</div></div>
      <div class="br-sum-card"><div class="br-sum-lbl">Difference</div><div class="br-sum-val" :class="Math.abs(summary.diff)<0.01?'green':'red'">{{ fmtCur(summary.diff) }}</div></div>
      <div class="br-sum-card"><div class="br-sum-lbl">Unmatched</div><div class="br-sum-val orange">{{ summary.unmatched }}</div></div>
    </div>

    <div v-if="ran" class="br-section-title">Bank Transactions (Statement)</div>
    <div v-if="ran" class="br-card">
      <table class="br-table">
        <thead>
          <tr>
            <th>Date</th><th>Description</th><th>Reference</th>
            <th class="ta-r">Deposit</th><th class="ta-r">Withdrawal</th><th>Status</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 5" :key="n"><td colspan="6"><div class="br-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="t in transactions" :key="t.name" class="br-row">
              <td class="mono-sm">{{ fmtDate(t.date) }}</td>
              <td>{{ t.description||'—' }}</td>
              <td class="mono-sm text-muted">{{ t.reference_number||'—' }}</td>
              <td class="ta-r mono-sm green">{{ flt(t.deposit)>0?fmtCur(t.deposit):'—' }}</td>
              <td class="ta-r mono-sm red">{{ flt(t.withdrawal)>0?fmtCur(t.withdrawal):'—' }}</td>
              <td><span class="br-badge" :class="t.status==='Reconciled'?'badge-green':'badge-orange'">{{ t.status||'Unreconciled' }}</span></td>
            </tr>
            <tr v-if="!transactions.length"><td colspan="6" class="br-empty">No transactions in this period</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <div v-if="!ran" class="br-placeholder">
      <span v-html="icon('balance',40)" style="color:#d1d5db;display:block;margin:0 auto 16px"></span>
      <div style="font-weight:600;color:#374151;margin-bottom:6px">Bank Reconciliation</div>
      <div style="color:#9ca3af;font-size:13px">Select a bank account and date range, then click Run to view the reconciliation statement.</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";

const { toast } = useToast();
const bankAccounts=ref([]),transactions=ref([]),loading=ref(false),ran=ref(false);
const systemBalance=ref(0);
const now=new Date();
const firstOfMonth=new Date(now.getFullYear(),now.getMonth(),1).toISOString().slice(0,10);
const form=reactive({bank_account:"",from_date:firstOfMonth,to_date:now.toISOString().slice(0,10)});

async function loadAccounts(){try{const co=await resolveCompany();bankAccounts.value=await apiList("Bank Account",{fields:["name","account_name"],filters:[["company","=",co]],limit:50});}catch{}}
async function load(){
  if(!form.bank_account)return;
  loading.value=true;ran.value=true;systemBalance.value=0;
  try{
    const[txRows,baRows]=await Promise.all([
      apiList("Bank Transaction",{fields:["name","date","description","reference_number","deposit","withdrawal","status"],filters:[["bank_account","=",form.bank_account],["date",">=",form.from_date],["date","<=",form.to_date]],limit:500,order:"date asc"}),
      apiList("Bank Account",{fields:["account"],filters:[["name","=",form.bank_account]],limit:1}),
    ]);
    transactions.value=txRows;
    const linkedAccount=baRows[0]?.account;
    if(linkedAccount){
      const gl=await apiList("GL Entry",{fields:["debit","credit"],filters:[["account","=",linkedAccount],["posting_date","<=",form.to_date],["is_cancelled","=",0]],limit:2000});
      systemBalance.value=gl.reduce((s,e)=>s+flt(e.debit)-flt(e.credit),0);
    }
  }catch(e){toast.error(e.message||"Failed to load");}finally{loading.value=false;}
}
const summary=computed(()=>{
  const dep=transactions.value.reduce((s,t)=>s+flt(t.deposit),0);
  const wd=transactions.value.reduce((s,t)=>s+flt(t.withdrawal),0);
  const stmtBal=dep-wd;
  const unmatched=transactions.value.filter(t=>t.status!=="Reconciled").length;
  return{statementBalance:stmtBal,systemBalance:systemBalance.value,diff:systemBalance.value-stmtBal,unmatched};
});
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
onMounted(loadAccounts);
</script>

<style scoped>
.br-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.br-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.br-select{border:1px solid #e5e7eb;border-radius:8px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;cursor:pointer;}
.br-select:focus{border-color:#2563eb;}
.br-input{border:1px solid #e5e7eb;border-radius:8px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.br-input:focus{border-color:#2563eb;}
.br-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.br-btn-primary:hover{background:#1d4ed8;}.br-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.br-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.br-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.br-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.br-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}.orange{color:#ea580c!important;}
.br-section-title{font-size:12px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.05em;}
.br-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.br-table{width:100%;border-collapse:collapse;font-size:13px;}
.br-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;}
.ta-r{text-align:right!important;}
.br-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;}
.br-row:last-child td{border-bottom:none;}.br-row:hover td{background:#f9fafb;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.br-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}
.br-empty{text-align:center;color:#9ca3af;padding:32px!important;}
.br-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.br-placeholder{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:80px 20px;text-align:center;}
</style>
