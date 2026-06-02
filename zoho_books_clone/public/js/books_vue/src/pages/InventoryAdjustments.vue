<template>
  <div class="ia-page">
    <div class="ia-actions">
      <div class="ia-search-wrap"><span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span><input v-model="search" placeholder="Search adjustments…" class="ia-search-input" /></div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="ia-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="ia-btn-ghost" @click="exportCSV" :disabled="!sorted.length"><span v-html="icon('download',14)"></span> Export</button>
        <button class="ia-btn-primary" @click="openNew()"><span v-html="icon('plus',13)"></span> New Adjustment</button>
      </div>
    </div>

    <SummaryStrip v-if="!loading" :cards="[
      { label: 'Total Adjustments', tone: 'default', value: list.length },
      { label: 'Increases', tone: 'success', value: increases, valueClass: 'green' },
      { label: 'Decreases', tone: 'danger', value: decreases, valueClass: 'red' },
      { label: 'Net Value Impact', tone: 'accent', value: fmtCur(netValue), valueClass: netValue>=0?'green':'red' },
    ]" />

    <div class="ia-card">
      <table class="ia-table">
        <thead><tr>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
          <th @click="sort('item_code')" class="sortable">Item <span v-html="sortArrow('item_code')"></span></th>
          <th>Warehouse</th>
          <th>Reason</th>
          <th @click="sort('qty')" class="sortable ta-r">Qty Change <span v-html="sortArrow('qty')"></span></th>
          <th class="ta-r">Value</th>
          <th>Status</th>
        </tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 6" :key="n"><td colspan="7"><div class="ia-shimmer"></div></td></tr></template>
          <template v-else>
            <tr v-for="a in sorted" :key="a.name" class="ia-row" @click="openView(a)">
              <td class="mono-sm text-muted">{{ fmtDate(a.posting_date) }}</td>
              <td class="font-medium">{{ a.item_name||a.item_code }}</td>
              <td class="text-muted">{{ a.warehouse||'—' }}</td>
              <td><span v-if="a.adjustment_reason" class="ia-reason">{{ a.adjustment_reason }}</span><span v-else class="text-muted">—</span></td>
              <td class="ta-r mono-sm" :class="flt(a.qty)>=0?'green':'red'">{{ flt(a.qty)>0?'+':'' }}{{ fmtQty(a.qty) }}</td>
              <td class="ta-r mono-sm" :class="flt(a.value)>=0?'':'red'">{{ fmtCur(a.value) }}</td>
              <td><span class="ia-badge" :class="a.docstatus===1?'badge-green':a.docstatus===2?'badge-grey':'badge-orange'">{{ a.docstatus===1?'Submitted':a.docstatus===2?'Cancelled':'Draft' }}</span></td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="7" class="ia-empty">{{ list.length ? 'No adjustments match your search' : 'No stock adjustments yet' }}</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create Drawer -->
    <div v-if="drawerOpen" class="ia-overlay" @click.self="!saving && (drawerOpen=false)"></div>
    <div class="ia-drawer" :class="{open:drawerOpen}">
      <div class="ia-dheader">
        <button class="ia-dclose ia-dclose-abs" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
        <div class="ia-dh-top">
          <div class="ia-dh-ico"><span v-html="icon('repeat',20)"></span></div>
          <div>
            <div class="ia-dh-title">New Stock Adjustment</div>
            <div class="ia-dh-sub">Correct on-hand quantity after a recount</div>
          </div>
        </div>
      </div>
      <div class="ia-dbody">
        <div class="ia-section-hdr"><span v-html="icon('box',13)"></span> Item & Warehouse</div>
        <div class="ia-fields-grid">
          <div class="ia-field" style="grid-column:1/-1">
            <label class="ia-label">Warehouse <span class="req">*</span></label>
            <SearchableSelect v-model="form.warehouse" :options="warehouses" placeholder="Select warehouse…" @search="fetchWarehouses" />
          </div>
          <div class="ia-field" style="grid-column:1/-1">
            <label class="ia-label">Item <span class="req">*</span></label>
            <SearchableSelect v-model="form.item_code" :options="items" placeholder="Select item…" @search="fetchItems" @select="onItemPick" />
          </div>
        </div>

        <div class="ia-section-hdr"><span v-html="icon('balance',13)"></span> Quantity</div>
        <div class="ia-qty-grid">
          <div class="ia-stat">
            <div class="ia-stat-lbl">Current on hand</div>
            <div class="ia-stat-val">{{ stockLoading ? '…' : fmtQty(currentQty) }}</div>
          </div>
          <div class="ia-field">
            <label class="ia-label">New counted qty <span class="req">*</span></label>
            <input v-model.number="form.new_qty" type="number" min="0" step="0.001" class="ia-input ta-r" :disabled="!form.item_code||!form.warehouse" />
          </div>
          <div class="ia-stat" :class="diff>0?'pos':diff<0?'neg':''">
            <div class="ia-stat-lbl">Difference</div>
            <div class="ia-stat-val">{{ diff>0?'+':'' }}{{ fmtQty(diff) }}</div>
          </div>
        </div>
        <div class="ia-hint">Value impact ≈ {{ fmtCur(diff * currentRate) }} at the current rate of {{ fmtCur(currentRate) }}/unit.</div>

        <div class="ia-section-hdr"><span v-html="icon('file',13)"></span> Reason</div>
        <div class="ia-fields-grid">
          <div class="ia-field" style="grid-column:1/-1">
            <label class="ia-label">Reason <span class="req">*</span></label>
            <select v-model="form.reason" class="ia-input">
              <option value="">Select a reason…</option>
              <option v-for="r in reasons" :key="r" :value="r">{{ r }}</option>
            </select>
          </div>
          <div class="ia-field" style="grid-column:1/-1">
            <label class="ia-label">Notes</label>
            <textarea v-model="form.notes" rows="2" class="ia-input" placeholder="Optional details…"></textarea>
          </div>
          <div class="ia-field" style="grid-column:1/-1">
            <label class="ia-label">Adjustment Account</label>
            <SearchableSelect v-model="form.adjustment_account" :options="accounts" placeholder="Default (Stock Adjustment)" @search="fetchAccounts" />
            <div class="ia-hint">Leave as default unless you want to post the difference elsewhere.</div>
          </div>
        </div>
      </div>
      <div class="ia-dfooter">
        <button class="ia-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="ia-btn-primary" :disabled="saving || !canSave" @click="saveAdjustment"><span v-html="icon('check',13)"></span> {{ saving?'Posting…':'Post Adjustment' }}</button>
      </div>
    </div>

    <!-- View Drawer -->
    <div v-if="viewOpen" class="ia-overlay" @click.self="viewOpen=false"></div>
    <div class="ia-drawer ia-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="ia-dheader">
          <button class="ia-dclose ia-dclose-abs" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
          <div class="ia-dh-top">
            <div class="ia-dh-ico"><span v-html="icon('repeat',20)"></span></div>
            <div>
              <div class="ia-dh-title">{{ viewDoc.item_name||viewDoc.item_code }}</div>
              <div class="ia-dh-sub">{{ viewDoc.warehouse }} · {{ fmtDate(viewDoc.posting_date) }}</div>
            </div>
            <span class="ia-badge" :class="viewDoc.docstatus===1?'badge-green':viewDoc.docstatus===2?'badge-grey':'badge-orange'">{{ viewDoc.docstatus===1?'Submitted':viewDoc.docstatus===2?'Cancelled':'Draft' }}</span>
          </div>
          <div class="ia-dh-amount">
            <div class="ia-dh-amt-lbl">Quantity Change</div>
            <div class="ia-dh-amt-val" :class="flt(viewDoc.qty)>=0?'green':'red'">{{ flt(viewDoc.qty)>0?'+':'' }}{{ fmtQty(viewDoc.qty) }}</div>
          </div>
        </div>
        <div class="ia-dbody">
          <div class="ia-section-hdr"><span v-html="icon('info',13)"></span> Details</div>
          <div class="ia-meta-grid">
            <div><div class="ia-meta-lbl">Entry #</div><div class="mono-sm" style="color:#2563eb">{{ viewDoc.name }}</div></div>
            <div><div class="ia-meta-lbl">Reason</div><div>{{ viewDoc.adjustment_reason||'—' }}</div></div>
            <div><div class="ia-meta-lbl">Value Impact</div><div class="mono-sm" :class="flt(viewDoc.value)>=0?'green':'red'">{{ fmtCur(viewDoc.value) }}</div></div>
            <div><div class="ia-meta-lbl">Rate / unit</div><div class="mono-sm">{{ fmtCur(viewDoc.basic_rate) }}</div></div>
          </div>
          <template v-if="viewDoc.remarks">
            <div class="ia-section-hdr"><span v-html="icon('file',13)"></span> Notes</div>
            <div class="ia-remark">{{ viewDoc.remarks }}</div>
          </template>
        </div>
        <div class="ia-dfooter">
          <button v-if="viewDoc.docstatus===1" class="ia-btn-danger-ghost" @click="cancelAdjustment(viewDoc)" :disabled="actionBusy"><span v-html="icon('cancel',13)"></span> Cancel Adjustment</button>
          <div style="margin-left:auto"><button class="ia-btn-ghost" @click="viewOpen=false">Close</button></div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { useRoute } from "vue-router";
import { apiGET, apiPOST, apiList, apiLinkValues, apiCancel, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useConfirm } from "../composables/useConfirm.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";

const { toast } = useToast();
const { confirm } = useConfirm();
const route = useRoute();

const list = ref([]), loading = ref(false), search = ref("");
const drawerOpen = ref(false), saving = ref(false), actionBusy = ref(false);
const viewOpen = ref(false), viewDoc = ref(null);
const warehouses = ref([]), items = ref([]), accounts = ref([]);
const currentQty = ref(0), currentRate = ref(0), stockLoading = ref(false);
const sortCol = ref("posting_date"), sortDir = ref("desc");
const reasons = ["Stock count discrepancy", "Damaged", "Expired", "Theft / Loss", "Found / Surplus", "Other"];
const form = reactive({ warehouse: "", item_code: "", new_qty: null, reason: "", notes: "", adjustment_account: "" });

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    const r = await apiGET("zoho_books_clone.api.inventory.get_inventory_adjustments", { company: co });
    list.value = Array.isArray(r) ? r : (r?.message || []);
  } catch (e) { toast.error(e.message || "Failed to load adjustments"); }
  finally { loading.value = false; }
}

const filtered = computed(() => {
  if (!search.value.trim()) return list.value;
  const q = search.value.toLowerCase();
  return list.value.filter(a => (a.item_code||"").toLowerCase().includes(q) || (a.item_name||"").toLowerCase().includes(q) || (a.warehouse||"").toLowerCase().includes(q) || (a.adjustment_reason||"").toLowerCase().includes(q));
});
const sorted = computed(() => { const c = sortCol.value; return [...filtered.value].sort((a,b)=>{const av=a[c]??"",bv=b[c]??"";const r=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?r:-r;}); });
function sort(c){ if(sortCol.value===c)sortDir.value=sortDir.value==="asc"?"desc":"asc"; else {sortCol.value=c;sortDir.value="asc";} }
function sortArrow(c){ if(sortCol.value!==c)return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value==="asc"?"↑":"↓"; }

const increases = computed(()=>list.value.filter(a=>flt(a.qty)>0).length);
const decreases = computed(()=>list.value.filter(a=>flt(a.qty)<0).length);
const netValue = computed(()=>list.value.filter(a=>a.docstatus===1).reduce((s,a)=>s+flt(a.value),0));
const diff = computed(()=> (form.new_qty===null||form.new_qty==="") ? 0 : flt(form.new_qty) - flt(currentQty.value));
const canSave = computed(()=> form.warehouse && form.item_code && form.reason && form.new_qty!==null && form.new_qty!=="" && flt(form.new_qty)>=0 && Math.abs(diff.value)>0.0000001);

function fmtCur(v){ return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v)); }
function fmtQty(v){ return Number(flt(v)).toLocaleString("en-IN",{maximumFractionDigits:3}); }

async function fetchWarehouses(q=""){ try{ const co=await resolveCompany(); const r=await apiList("Warehouse",{fields:["name"],filters:[["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:30}); warehouses.value=r.map(x=>({label:x.name,value:x.name})); }catch{warehouses.value=[];} }
async function fetchItems(q=""){ try{ const r=await apiLinkValues("Item",q); items.value=r.map(x=>({label:x.name,value:x.name})); }catch{items.value=[];} }
async function fetchAccounts(q=""){ try{ const co=await resolveCompany(); const r=await apiList("Account",{fields:["name"],filters:[["company","=",co],["is_group","=",0],["account_type","in",["Stock Adjustment","Expense","Temporary"]],...(q?[["name","like",`%${q}%`]]:[])],limit:30}); accounts.value=r.map(x=>({label:x.name,value:x.name})); }catch{accounts.value=[];} }

async function loadCurrentStock(){
  if(!form.item_code||!form.warehouse){ currentQty.value=0; currentRate.value=0; return; }
  stockLoading.value=true;
  try{
    const r = await apiGET("zoho_books_clone.api.inventory.get_item_stock_detail", { item_code: form.item_code, warehouse: form.warehouse });
    const wh = (r?.warehouses||r?.message?.warehouses||[]).find(w=>w.warehouse===form.warehouse);
    currentQty.value = flt(wh?.actual_qty);
    currentRate.value = flt(wh?.valuation_rate);
  }catch{ currentQty.value=0; currentRate.value=0; }
  finally{ stockLoading.value=false; }
}
function onItemPick(opt){ form.item_code = opt?.value ?? opt; loadCurrentStock(); }

async function openNew(prefill){
  Object.assign(form, { warehouse:"", item_code:"", new_qty:null, reason:"", notes:"", adjustment_account:"" });
  currentQty.value=0; currentRate.value=0;
  await Promise.all([fetchWarehouses(""), fetchItems(""), fetchAccounts(""), loadDefaultAccount()]);
  if(prefill){ form.warehouse=prefill.warehouse||""; form.item_code=prefill.item||""; if(form.item_code&&form.warehouse) await loadCurrentStock(); }
  drawerOpen.value=true;
}
function openView(a){ viewDoc.value=a; viewOpen.value=true; }

async function loadDefaultAccount(){
  try{ const co=await resolveCompany(); const r=await apiGET("zoho_books_clone.api.inventory.get_default_adjustment_account",{company:co}); const acc=r?.account||r?.message?.account||""; if(acc){ form.adjustment_account=acc; if(!accounts.value.find(o=>o.value===acc)) accounts.value.unshift({label:acc,value:acc}); } }catch{}
}

async function saveAdjustment(){
  if(!canSave.value) return;
  saving.value=true;
  try{
    const res = await apiPOST("zoho_books_clone.api.inventory.create_inventory_adjustment", {
      item_code: form.item_code, warehouse: form.warehouse, new_qty: flt(form.new_qty),
      reason: form.reason, notes: form.notes||"", adjustment_account: form.adjustment_account||"",
    });
    const d = res?.message?.delta ?? res?.delta;
    toast.success(`Adjustment posted (${d>0?'+':''}${fmtQty(d)})`);
    drawerOpen.value=false;
    await load();
  }catch(e){ toast.error(e.message||"Failed to post adjustment"); }
  finally{ saving.value=false; }
}

async function cancelAdjustment(a){
  const ok = await confirm({ title:"Cancel this adjustment?", body:`Cancelling ${a.name} reverses the stock change and its ledger entries.`, okLabel:"Cancel Adjustment", okStyle:"danger" });
  if(!ok) return;
  actionBusy.value=true;
  try{ await apiCancel("Stock Entry", a.name); toast.success(`${a.name} cancelled`); viewOpen.value=false; await load(); }
  catch(e){ toast.error(e.message||"Failed to cancel"); }
  finally{ actionBusy.value=false; }
}

function exportCSV(){
  const rows=sorted.value; if(!rows.length)return;
  const esc=v=>{const s=v==null?"":String(v);return /[",\n]/.test(s)?'"'+s.replace(/"/g,'""')+'"':s;};
  const statusOf=d=>d===1?"Submitted":d===2?"Cancelled":"Draft";
  const lines=[["Entry #","Date","Item","Warehouse","Reason","Qty Change","Value","Status"].join(",")];
  for(const a of rows) lines.push([a.name,fmtDate(a.posting_date),a.item_name||a.item_code,a.warehouse||"",a.adjustment_reason||"",flt(a.qty),flt(a.value),statusOf(a.docstatus)].map(esc).join(","));
  const blob=new Blob(["﻿"+lines.join("\r\n")],{type:"text/csv;charset=utf-8;"});
  const url=URL.createObjectURL(blob); const el=document.createElement("a");
  el.href=url; el.download=`stock_adjustments_${new Date().toISOString().slice(0,10)}.csv`; el.click(); URL.revokeObjectURL(url);
  toast.success(`Exported ${rows.length} row(s)`);
}

onMounted(async()=>{
  await load();
  if(route.query.item || route.query.warehouse){
    openNew({ item: route.query.item ? String(route.query.item) : "", warehouse: route.query.warehouse ? String(route.query.warehouse) : "" });
  }
});
</script>

<style scoped>
.ia-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.ia-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.ia-search-wrap{display:flex;align-items:center;gap:8px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:6px 12px;min-width:240px;}
.ia-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.ia-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.ia-btn-primary:hover{background:#1d4ed8;}.ia-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.ia-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font-size:13px;font-weight:600;color:#334155;cursor:pointer;}
.ia-btn-ghost:hover:not(:disabled){background:#f8fafc;border-color:#cbd5e1;}.ia-btn-ghost:disabled{opacity:.5;cursor:not-allowed;}
.ia-btn-danger-ghost{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid #fecaca;border-radius:8px;padding:8px 12px;font-size:13px;color:#dc2626;cursor:pointer;}
.ia-btn-danger-ghost:hover:not(:disabled){background:#fef2f2;}.ia-btn-danger-ghost:disabled{opacity:.5;cursor:not-allowed;}

.ia-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.ia-table{width:100%;border-collapse:collapse;font-size:13px;}
.ia-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;text-transform:uppercase;}
.ia-table th.sortable{cursor:pointer;user-select:none;}.ia-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.ia-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;cursor:pointer;}
.ia-row:last-child td{border-bottom:none;}.ia-row:hover td{background:#f9fafb;}
.font-medium{font-weight:600;}.mono-sm{font-family:'JetBrains Mono',ui-monospace,monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.green{color:#16a34a!important;}.red{color:#dc2626!important;}
.ia-reason{display:inline-flex;padding:2px 8px;border-radius:10px;background:#f1f5f9;color:#475569;font-size:11.5px;font-weight:600;}
.ia-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.ia-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.ia-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* drawer */
.ia-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);z-index:40;}
.ia-drawer{position:fixed;top:0;right:-480px;bottom:0;width:480px;max-width:96vw;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 28px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s ease;}
.ia-drawer.open{right:0;}
.ia-view-drawer{width:420px;right:-420px;}.ia-view-drawer.open{right:0;}
.ia-dheader{position:relative;flex-shrink:0;padding:20px;border-bottom:1px solid #e5e7eb;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.ia-dclose{background:transparent;border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;}
.ia-dclose:hover{background:rgba(255,255,255,.6);color:#0f172a;}
.ia-dclose-abs{position:absolute;top:12px;right:12px;}
.ia-dh-top{display:flex;align-items:center;gap:13px;padding-right:36px;}
.ia-dh-ico{width:42px;height:42px;background:#fff;border-radius:11px;display:flex;align-items:center;justify-content:center;color:#2563eb;flex-shrink:0;box-shadow:0 1px 3px rgba(15,23,42,.08);}
.ia-dh-title{font-size:15px;font-weight:700;color:#0f172a;}
.ia-dh-sub{font-size:12px;color:#475569;margin-top:1px;}
.ia-dh-top .ia-badge{margin-left:auto;}
.ia-dh-amount{margin-top:16px;}
.ia-dh-amt-lbl{font-size:10.5px;color:#64748b;text-transform:uppercase;letter-spacing:.05em;font-weight:600;}
.ia-dh-amt-val{font-size:26px;font-weight:800;font-family:'JetBrains Mono',ui-monospace,monospace;letter-spacing:-.01em;margin-top:2px;}
.ia-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:12px;}
.ia-section-hdr{display:flex;align-items:center;gap:8px;font-size:11.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#0f172a;margin-top:4px;}
.ia-section-hdr span{color:#2563eb;display:inline-flex;}
.ia-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.ia-field{display:flex;flex-direction:column;gap:4px;}
.ia-label{font-size:12px;font-weight:600;color:#334155;}.req{color:#dc2626;}
.ia-hint{font-size:11.5px;color:#94a3b8;}
.ia-input{border:1px solid #e2e8f0;border-radius:8px;padding:8px 11px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;transition:border-color .15s,box-shadow .15s;}
.ia-input:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.1);}
.ia-input:disabled{background:#f8fafc;color:#94a3b8;cursor:not-allowed;}
textarea.ia-input{resize:vertical;}
.ia-qty-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:end;}
.ia-stat{background:#f8fafc;border:1px solid #eef2f7;border-radius:10px;padding:10px 12px;}
.ia-stat.pos{background:#f0fdf4;border-color:#bbf7d0;}.ia-stat.neg{background:#fef2f2;border-color:#fecaca;}
.ia-stat-lbl{font-size:10px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;font-weight:600;margin-bottom:2px;}
.ia-stat-val{font-size:18px;font-weight:800;font-family:'JetBrains Mono',ui-monospace,monospace;color:#0f172a;}
.ia-stat.pos .ia-stat-val{color:#16a34a;}.ia-stat.neg .ia-stat-val{color:#dc2626;}
.ia-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.ia-meta-lbl{font-size:10.5px;color:#94a3b8;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;font-weight:600;}
.ia-remark{font-size:13px;color:#334155;line-height:1.5;background:#f8fafc;border:1px solid #eef2f7;border-radius:10px;padding:12px 14px;}
.ia-dfooter{display:flex;align-items:center;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
