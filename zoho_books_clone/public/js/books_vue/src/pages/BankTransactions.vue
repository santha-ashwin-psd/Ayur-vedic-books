<template>
  <div class="bt-page">
    <div class="bt-actions">
      <div class="bt-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search transactions…" class="bt-search-input" />
      </div>
      <div class="bt-pills">
        <button v-for="t in tabs" :key="t.key" class="bt-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto;align-items:center">
        <select v-model="selectedAccount" class="bt-select" @change="load">
          <option value="">All Accounts</option>
          <option v-for="a in bankAccounts" :key="a.name" :value="a.name">{{ a.account_name||a.name }}</option>
        </select>
        <label class="bt-import-btn" :class="{disabled:!selectedAccount||importing}">
          📥 Import CSV
          <input type="file" accept=".csv,text/csv" style="display:none" :disabled="!selectedAccount||importing" @change="onCsvSelected"/>
        </label>
        <button class="bt-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
      </div>
    </div>

    <div v-if="importResult" class="bt-import-result" :class="importResult.ok?'ok':'err'">
      <span v-if="importResult.ok">✓ Imported {{ importResult.count }} transaction(s). Skipped {{ importResult.skipped }}.</span>
      <span v-else>✗ {{ importResult.error }}</span>
      <button class="bt-import-close" @click="importResult=null">×</button>
    </div>

    <SummaryStrip v-if="!loading" :cards="[
      { label: 'Deposits', tone: 'success', value: fmtCur(summaryDeposit), valueClass: 'green' },
      { label: 'Withdrawals', tone: 'danger', value: fmtCur(summaryWithdrawal), valueClass: 'red' },
      { label: 'Unreconciled', tone: counts.unreconciled>0?'warn':'default', value: counts.unreconciled, valueClass: counts.unreconciled>0?'orange':'' },
      { label: 'Total', tone: 'default', value: filtered.length },
    ]" />

    <div class="bt-card">
      <table class="bt-table">
        <thead>
          <tr>
            <th @click="sort('date')" class="sortable">Date <span v-html="sortArrow('date')"></span></th>
            <th @click="sort('bank_account')" class="sortable">Account <span v-html="sortArrow('bank_account')"></span></th>
            <th @click="sort('description')" class="sortable">Description <span v-html="sortArrow('description')"></span></th>
            <th @click="sort('reference_number')" class="sortable">Reference <span v-html="sortArrow('reference_number')"></span></th>
            <th>Status</th>
            <th @click="sort('deposit')" class="sortable ta-r">Deposit <span v-html="sortArrow('deposit')"></span></th>
            <th @click="sort('withdrawal')" class="sortable ta-r">Withdrawal <span v-html="sortArrow('withdrawal')"></span></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="7"><div class="bt-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="t in sorted" :key="t.name" class="bt-row" @click="openView(t)">
              <td class="mono-sm">{{ fmtDate(t.date) }}</td>
              <td class="text-muted">{{ t.bank_account||'—' }}</td>
              <td>{{ t.description||'—' }}</td>
              <td class="mono-sm text-muted">{{ t.reference_number||'—' }}</td>
              <td><span class="bt-badge" :class="t.status==='Reconciled'?'badge-green':t.status==='Unreconciled'?'badge-orange':'badge-grey'">{{ t.status||'Unreconciled' }}</span></td>
              <td class="ta-r mono-sm green">{{ flt(t.deposit)>0 ? fmtCur(t.deposit) : '—' }}</td>
              <td class="ta-r mono-sm red">{{ flt(t.withdrawal)>0 ? fmtCur(t.withdrawal) : '—' }}</td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="7" class="bt-empty">No transactions found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- View -->
    <div v-if="viewOpen" class="bt-overlay" @click.self="viewOpen=false"></div>
    <div class="bt-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="bt-dheader">
          <button class="bt-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
          <div class="bt-dh-top">
            <div class="bt-dh-ico"><span v-html="icon('ledger',20)"></span></div>
            <div>
              <div class="bt-dh-title">Transaction Details</div>
              <div class="bt-dh-sub">{{ viewDoc.bank_account||'—' }} · {{ fmtDate(viewDoc.date) }}</div>
            </div>
            <span class="bt-badge" :class="viewDoc.status==='Reconciled'?'badge-green':'badge-orange'">{{ viewDoc.status||'Unreconciled' }}</span>
          </div>
          <div class="bt-dh-amount">
            <div class="bt-dh-amt-lbl">{{ flt(viewDoc.deposit)>0 ? 'Deposit' : 'Withdrawal' }}</div>
            <div class="bt-dh-amt-val" :class="flt(viewDoc.deposit)>0?'pos':'neg'">
              {{ flt(viewDoc.deposit)>0 ? fmtCur(viewDoc.deposit) : '-'+fmtCur(viewDoc.withdrawal) }}
            </div>
          </div>
        </div>
        <div class="bt-dbody">
          <div class="bt-section-hdr"><span v-html="icon('info',13)"></span> Details</div>
          <div class="bt-meta-grid">
            <div><div class="bt-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.date) }}</div></div>
            <div><div class="bt-meta-lbl">Bank Account</div><div>{{ viewDoc.bank_account||'—' }}</div></div>
            <div><div class="bt-meta-lbl">Deposit</div><div class="mono-sm green">{{ flt(viewDoc.deposit)>0?fmtCur(viewDoc.deposit):'—' }}</div></div>
            <div><div class="bt-meta-lbl">Withdrawal</div><div class="mono-sm red">{{ flt(viewDoc.withdrawal)>0?fmtCur(viewDoc.withdrawal):'—' }}</div></div>
            <div><div class="bt-meta-lbl">Reference</div><div class="mono-sm">{{ viewDoc.reference_number||'—' }}</div></div>
            <div><div class="bt-meta-lbl">Status</div><div><span class="bt-badge" :class="viewDoc.status==='Reconciled'?'badge-green':'badge-orange'">{{ viewDoc.status||'Unreconciled' }}</span></div></div>
          </div>
          <div class="bt-section-hdr"><span v-html="icon('file',13)"></span> Description</div>
          <div class="bt-desc">{{ viewDoc.description||'—' }}</div>
        </div>
        <div class="bt-dfooter"><button class="bt-btn-ghost" @click="viewOpen=false">Close</button></div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import { apiList, apiPOST, resolveCompany } from "../api/client.js";

// CSV import
const importing = ref(false);
const importResult = ref(null);
function onCsvSelected(e) {
  const f = e.target.files?.[0];
  if (!f) return;
  if (!selectedAccount.value) {
    importResult.value = { ok: false, error: "Pick a Bank Account first" };
    return;
  }
  const reader = new FileReader();
  reader.onload = async (evt) => {
    importing.value = true;
    importResult.value = null;
    try {
      const r = await apiPOST("zoho_books_clone.api.docs.import_bank_statement_csv", {
        bank_account: selectedAccount.value,
        csv_data: evt.target.result,
      });
      importResult.value = { ok: true, count: r?.count || 0, skipped: r?.skipped || 0 };
      await load();
    } catch (err) {
      importResult.value = { ok: false, error: err.message || "Import failed" };
    } finally {
      importing.value = false;
      e.target.value = ""; // reset input so the same file can be re-selected
    }
  };
  reader.readAsText(f);
}
import { useToast } from "../composables/useToast.js";
import { useRoute } from "vue-router";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SummaryStrip from "../components/SummaryStrip.vue";

const { toast } = useToast();
const route = useRoute();
const activeTab=ref("all");
const tabs=[{key:"all",label:"All"},{key:"Unreconciled",label:"Unreconciled"},{key:"Reconciled",label:"Reconciled"}];
const list=ref([]),loading=ref(false),search=ref(""),selectedAccount=ref("");
const bankAccounts=ref([]),viewOpen=ref(false),viewDoc=ref(null);
const sortCol=ref("date"),sortDir=ref("desc");

async function load(){
  loading.value=true;
  try{
    const co=await resolveCompany();
    if(!bankAccounts.value.length){bankAccounts.value=await apiList("Bank Account",{fields:["name","account_name"],filters:[["company","=",co]],limit:50});}
    const whNames=bankAccounts.value.map(a=>a.name);
    if(!whNames.length&&!selectedAccount.value){list.value=[];loading.value=false;return;}
    const filters=whNames.length?[["bank_account","in",whNames]]:[];
    if(selectedAccount.value)filters.push(["bank_account","=",selectedAccount.value]);
    // Bank Transaction uses `debit`/`credit` columns (not deposit/withdrawal).
    // Pull both then alias for the legacy template.
    const raw=await apiList("Bank Transaction",{
      fields:["name","date","bank_account","description","reference_number","debit","credit","status","currency"],
      filters, limit:300, order:"date desc"
    });
    list.value = raw.map(t => ({
      ...t,
      deposit:    flt(t.debit  || 0),   // money INTO bank → debit on bank ledger
      withdrawal: flt(t.credit || 0),
    }));
  }catch(e){toast.error(e.message||"Failed to load transactions");}
  finally{loading.value=false;}
}

const filtered=computed(()=>{let r=list.value;if(activeTab.value!=="all")r=r.filter(t=>t.status===activeTab.value);if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(t=>(t.description||"").toLowerCase().includes(q)||(t.reference_number||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const summaryDeposit=computed(()=>filtered.value.reduce((s,t)=>s+flt(t.deposit),0));
const summaryWithdrawal=computed(()=>filtered.value.reduce((s,t)=>s+flt(t.withdrawal),0));
const counts=computed(()=>({unreconciled:list.value.filter(t=>t.status!=="Reconciled").length}));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
function openView(t){viewDoc.value=t;viewOpen.value=true;}
onMounted(()=>{if(route.query.account)selectedAccount.value=String(route.query.account);load();});
</script>

<style scoped>
.bt-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.bt-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.bt-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;}
.bt-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.bt-pills{display:flex;gap:6px;}
.bt-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.bt-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.bt-select{border:1px solid #e5e7eb;border-radius:8px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;cursor:pointer;}
.bt-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.bt-btn-ghost:hover{background:#f9fafb;}
.bt-import-btn{display:inline-flex;align-items:center;gap:6px;background:#eff6ff;border:1px solid #93c5fd;color:#1d4ed8;border-radius:8px;padding:7px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.bt-import-btn:hover:not(.disabled){background:#dbeafe;}
.bt-import-btn.disabled{opacity:.5;cursor:not-allowed;}
.bt-import-result{display:flex;align-items:center;justify-content:space-between;padding:10px 14px;border-radius:8px;font-size:12.5px;font-weight:600;margin-top:-4px;}
.bt-import-result.ok{background:#dcfce7;color:#16a34a;border:1px solid #86efac;}
.bt-import-result.err{background:#fee2e2;color:#dc2626;border:1px solid #fca5a5;}
.bt-import-close{background:transparent;border:none;color:inherit;cursor:pointer;font-size:18px;line-height:1;padding:0 4px;}
.bt-import-close:hover{opacity:.7;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}.orange{color:#ea580c!important;}
.bt-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.bt-table{width:100%;border-collapse:collapse;font-size:13px;}
.bt-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;text-transform:uppercase;}
.bt-table th.sortable{cursor:pointer;user-select:none;}.bt-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.bt-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.bt-row:last-child td{border-bottom:none;}.bt-row:hover td{background:#f9fafb;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.bt-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.bt-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.bt-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.bt-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);z-index:40;}
.bt-drawer{position:fixed;top:0;right:-440px;bottom:0;width:440px;max-width:96vw;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 28px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s ease;}
.bt-drawer.open{right:0;}
.bt-dheader{position:relative;flex-shrink:0;padding:20px;border-bottom:1px solid #e5e7eb;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.bt-dclose{position:absolute;top:12px;right:12px;background:transparent;border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;}
.bt-dclose:hover{background:rgba(255,255,255,.6);color:#0f172a;}
.bt-dh-top{display:flex;align-items:center;gap:13px;padding-right:36px;}
.bt-dh-ico{width:42px;height:42px;background:#fff;border-radius:11px;display:flex;align-items:center;justify-content:center;color:#2563eb;flex-shrink:0;box-shadow:0 1px 3px rgba(15,23,42,.08);}
.bt-dh-title{font-size:15px;font-weight:700;color:#0f172a;}
.bt-dh-sub{font-size:12px;color:#475569;margin-top:1px;}
.bt-dh-top .bt-badge{margin-left:auto;}
.bt-dh-amount{margin-top:16px;}
.bt-dh-amt-lbl{font-size:10.5px;color:#64748b;text-transform:uppercase;letter-spacing:.05em;font-weight:600;}
.bt-dh-amt-val{font-size:26px;font-weight:800;letter-spacing:-.01em;margin-top:2px;}
.bt-dh-amt-val.pos{color:#16a34a;}.bt-dh-amt-val.neg{color:#dc2626;}
.bt-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:12px;}
.bt-section-hdr{display:flex;align-items:center;gap:8px;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#0f172a;margin-top:4px;}
.bt-section-hdr span{color:#2563eb;display:inline-flex;}
.bt-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.bt-meta-lbl{font-size:10.5px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;font-weight:600;}
.bt-desc{font-size:13px;color:#334155;line-height:1.5;background:#f8fafc;border:1px solid #eef2f7;border-radius:10px;padding:12px 14px;}
.bt-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
