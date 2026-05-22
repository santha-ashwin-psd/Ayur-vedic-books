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
            <th style="width:32px"><input type="checkbox" :checked="allUnreconciledSelected" @change="toggleSelectAll" /></th>
            <th>Date</th><th>Description</th><th>Reference</th>
            <th class="ta-r">Deposit</th><th class="ta-r">Withdrawal</th><th>Status</th>
            <th style="width:130px">Match</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 5" :key="n"><td colspan="8"><div class="br-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <template v-for="t in transactions" :key="t.name">
              <tr class="br-row">
                <td @click.stop><input v-if="t.status!=='Reconciled'" type="checkbox" :checked="selected.has(t.name)" @change="toggleSelect(t.name)" /></td>
                <td class="mono-sm">{{ fmtDate(t.date) }}</td>
                <td>{{ t.description||'—' }}</td>
                <td class="mono-sm text-muted">{{ t.reference_number||'—' }}</td>
                <td class="ta-r mono-sm green">{{ flt(t.deposit)>0?fmtCur(t.deposit):'—' }}</td>
                <td class="ta-r mono-sm red">{{ flt(t.withdrawal)>0?fmtCur(t.withdrawal):'—' }}</td>
                <td><span class="br-badge" :class="t.status==='Reconciled'?'badge-green':'badge-orange'">{{ t.status||'Unreconciled' }}</span></td>
                <td>
                  <button v-if="t.status!=='Reconciled'"
                    class="br-match-btn"
                    @click.stop="suggestMatches(t)"
                    :disabled="matchingFor===t.name">
                    {{ matchingFor===t.name ? '…' : '🔍 Suggest' }}
                  </button>
                </td>
              </tr>
              <tr v-if="suggestions[t.name]" class="br-suggest-row">
                <td colspan="8" style="padding:0">
                  <div class="br-suggest-panel">
                    <div style="font-size:12px;font-weight:600;color:#1e40af;margin-bottom:8px">
                      🤖 {{ suggestions[t.name].matches.length }} candidate payment{{ suggestions[t.name].matches.length===1?'':'s' }} for ₹{{ fmtCur(suggestions[t.name].bt_amount) }} ({{ suggestions[t.name].bt_direction==='in'?'received':'paid out' }})
                    </div>
                    <div v-if="!suggestions[t.name].matches.length" style="font-size:12.5px;color:#6b7280;padding:8px">No Payment Entries matched on amount + date. You can mark this row Reconciled manually if you reviewed it.</div>
                    <div v-for="m in suggestions[t.name].matches" :key="m.name" class="br-suggest-card">
                      <div class="br-suggest-meta">
                        <span class="br-num">{{ m.name }}</span>
                        <span class="br-score" :style="`background:${m.score>=80?'#dcfce7':m.score>=50?'#fef3c7':'#fee2e2'};color:${m.score>=80?'#16a34a':m.score>=50?'#d97706':'#dc2626'}`">{{ m.score.toFixed(0) }}% confidence</span>
                      </div>
                      <div class="br-suggest-info">
                        <span>{{ m.party_name || m.party }} · {{ fmtDate(m.payment_date) }} · {{ m.mode_of_payment||'—' }}</span>
                      </div>
                      <div class="br-suggest-amt">{{ fmtCur(m.paid_amount) }}</div>
                      <button class="br-match-confirm" @click="confirmMatch(t, m)" :disabled="matchingFor===m.name">
                        {{ matchingFor===m.name ? '…' : '✓ Match' }}
                      </button>
                    </div>
                    <button class="br-suggest-close" @click="suggestions[t.name]=null">close</button>
                  </div>
                </td>
              </tr>
            </template>
            <tr v-if="!transactions.length"><td colspan="8" class="br-empty">No transactions in this period</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <div v-if="ran && selected.size>0" class="br-reconcile-bar">
      <span style="font-size:13px;color:#374151;font-weight:600">{{ selected.size }} transaction{{ selected.size>1?'s':'' }} selected</span>
      <label style="font-size:13px;color:#374151">Clearance Date</label>
      <input v-model="clearanceDate" type="date" class="br-input" style="width:150px" />
      <button class="br-btn-primary" :disabled="reconciling||!clearanceDate" @click="markReconciled">
        <span v-html="icon('check',13)"></span> {{ reconciling?'Saving…':'Mark Reconciled' }}
      </button>
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
import { apiList, apiGET, apiPOST, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";

const { toast } = useToast();
const bankAccounts=ref([]),transactions=ref([]),loading=ref(false),ran=ref(false);
const systemBalance=ref(0);
const selected=ref(new Set());
const clearanceDate=ref(new Date().toISOString().slice(0,10));
const reconciling=ref(false);
const now=new Date();
const firstOfMonth=new Date(now.getFullYear(),now.getMonth(),1).toISOString().slice(0,10);
const form=reactive({bank_account:"",from_date:firstOfMonth,to_date:now.toISOString().slice(0,10)});

async function loadAccounts(){try{const co=await resolveCompany();bankAccounts.value=await apiList("Bank Account",{fields:["name","account_name"],filters:[["company","=",co]],limit:50});}catch{}}
async function load(){
  if(!form.bank_account)return;
  loading.value=true;ran.value=true;systemBalance.value=0;
  selected.value=new Set();
  try{
    // Use the consolidated backend endpoint — handles the GL Entry → General
    // Ledger Entry rename + the Bank Transaction debit/credit column naming.
    const res = await apiGET("zoho_books_clone.api.docs.get_bank_reconciliation", {
      bank_account: form.bank_account,
      from_date:    form.from_date,
      to_date:      form.to_date,
    });
    // Backend returns rows with debit/credit; alias for legacy template.
    transactions.value = (res?.bank_transactions || []).map(t => ({
      ...t,
      deposit:    flt(t.debit  || 0),
      withdrawal: flt(t.credit || 0),
    }));
    systemBalance.value = flt(res?.gl_balance || 0);
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
function toggleSelect(name){const s=new Set(selected.value);if(s.has(name))s.delete(name);else s.add(name);selected.value=s;}
const allUnreconciledSelected=computed(()=>{const unreconciled=transactions.value.filter(t=>t.status!=="Reconciled");return unreconciled.length>0&&unreconciled.every(t=>selected.value.has(t.name));});
function toggleSelectAll(){const unreconciled=transactions.value.filter(t=>t.status!=="Reconciled");if(allUnreconciledSelected.value){selected.value=new Set();}else{selected.value=new Set(unreconciled.map(t=>t.name));}}
async function markReconciled(){
  if(!selected.value.size||!clearanceDate.value)return;
  reconciling.value=true;
  let ok=0;
  try{
    for(const name of selected.value){
      try{
        await apiPOST("zoho_books_clone.api.docs.reconcile_bank_transaction",{bank_transaction_name:name});
        ok++;
      }catch{}
    }
    toast.success(`${ok} transaction(s) marked as reconciled`);
    await load();
  }catch(e){toast.error(e.message||"Failed to reconcile transactions");}
  finally{reconciling.value=false;}
}
// ── Auto-match suggestions ───────────────────────────────────────────────
const suggestions = reactive({});   // { bt_name: { matches, bt_amount, bt_direction } | null }
const matchingFor = ref("");

async function suggestMatches(t) {
  if (suggestions[t.name]) { suggestions[t.name] = null; return; } // toggle close
  matchingFor.value = t.name;
  try {
    suggestions[t.name] = await apiGET("zoho_books_clone.api.docs.suggest_payment_matches",
      { bank_transaction_name: t.name });
  } catch (e) { toast.error(e.message || "Failed to suggest matches"); }
  matchingFor.value = "";
}

async function confirmMatch(t, m) {
  matchingFor.value = m.name;
  try {
    await apiPOST("zoho_books_clone.api.docs.reconcile_bank_transaction",
      { bank_transaction_name: t.name, payment_entry_name: m.name });
    toast.success(`${t.name} matched to ${m.name}`);
    suggestions[t.name] = null;
    await load();
  } catch (e) { toast.error(e.message || "Match failed"); }
  matchingFor.value = "";
}

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
.br-reconcile-bar{display:flex;align-items:center;gap:12px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;padding:12px 16px;flex-wrap:wrap;}
.br-match-btn{background:#eff6ff;border:1px solid #93c5fd;color:#1d4ed8;padding:4px 10px;border-radius:6px;font-size:11.5px;font-weight:600;cursor:pointer;font-family:inherit;}
.br-match-btn:hover:not(:disabled){background:#dbeafe;}
.br-match-btn:disabled{opacity:.5;cursor:not-allowed;}
.br-suggest-row{background:#f8fafc;}
.br-suggest-panel{position:relative;padding:14px 18px;background:#f0f9ff;border-left:3px solid #1a6ef7;}
.br-suggest-card{display:grid;grid-template-columns:1.5fr 2fr 100px 80px;gap:10px;align-items:center;padding:8px 10px;background:#fff;border:1px solid #e0e7ff;border-radius:6px;margin-bottom:6px;font-size:12.5px;}
.br-suggest-meta{display:flex;align-items:center;gap:8px;}
.br-num{font-family:monospace;color:#1d4ed8;font-weight:700;font-size:12px;}
.br-score{padding:2px 8px;border-radius:10px;font-size:10.5px;font-weight:700;}
.br-suggest-info{color:#6b7280;font-size:12px;}
.br-suggest-amt{text-align:right;font-family:monospace;font-weight:700;color:#111827;}
.br-match-confirm{background:#1a6ef7;color:#fff;border:none;padding:5px 10px;border-radius:6px;font-size:12px;font-weight:600;cursor:pointer;font-family:inherit;}
.br-match-confirm:hover:not(:disabled){background:#1d4ed8;}
.br-match-confirm:disabled{opacity:.5;cursor:not-allowed;}
.br-suggest-close{position:absolute;top:8px;right:10px;background:transparent;border:none;color:#6b7280;font-size:11px;cursor:pointer;}
.br-suggest-close:hover{color:#1d4ed8;text-decoration:underline;}
</style>
