<template>
  <div class="list-page">
    <div class="sales-toolbar">
      <div class="sales-search">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search expenses…" class="sales-search-input" />
      </div>
      <div class="sales-pills">
        <button v-for="t in tabs" :key="t.key" class="sales-pill" :class="{active:activeTab===t.key, ['pill-'+t.key]: t.key!=='all'}" @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="sales-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="sales-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Expense</button>
      </div>
    </div>

    <!-- ── KPI Cards ── -->
    <div class="bk-kpi-grid bk-kpi-grid-4">
      <div class="bk-kpi-card bk-kpi-accent clickable" @click="activeTab='all'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total Records</div><div class="bk-kpi-value">{{ list.length }}</div><div class="bk-kpi-trend" :class="expTrends.total.up?'bk-trend-up':'bk-trend-down'">{{ expTrends.total.up?'↑':'↓' }} {{ expTrends.total.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dcfce7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="1.8"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">This Month</div><div class="bk-kpi-value bk-kpi-green" style="font-size:18px">{{ fmtCur(monthTotal) }}</div><div class="bk-kpi-trend" :class="expTrends.month.up?'bk-trend-up':'bk-trend-down'">{{ expTrends.month.up?'↑':'↓' }} {{ expTrends.month.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-info clickable" @click="activeTab='submitted'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#cffafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#0891b2" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#0891b2" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Submitted</div><div class="bk-kpi-value bk-kpi-blue">{{ list.filter(e=>e.docstatus===1&&statusLabel(e)!=='Paid').length }}</div><div class="bk-kpi-trend" :class="expTrends.submitted.up?'bk-trend-up':'bk-trend-down'">{{ expTrends.submitted.up?'↑':'↓' }} {{ expTrends.submitted.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-warn clickable" @click="activeTab='draft'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#f1f5f9"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Draft</div><div class="bk-kpi-value bk-kpi-amber">{{ counts.draft }}</div><div class="bk-kpi-trend" :class="expTrends.draft.up?'bk-trend-up':'bk-trend-down'">{{ expTrends.draft.up?'↑':'↓' }} {{ expTrends.draft.pct }}% vs last month</div></div></div></div>
    </div>
    <div class="bk-stat-grid">
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month Count</div><div class="bk-stat-value">{{ expThisMonth.count }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Submitted</div><div class="bk-stat-value bk-kpi-green">{{ list.filter(e=>e.docstatus===1).length }}</div></div><div class="bk-stat-icon" style="background:#dcfce7;color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#16a34a" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Avg Expense</div><div class="bk-stat-value" style="font-size:16px">{{ fmtCur(expAvg) }}</div></div><div class="bk-stat-icon" style="background:#e5e7eb;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Paid</div><div class="bk-stat-value bk-kpi-green">{{ list.filter(e=>statusLabel(e)==='Paid').length }}</div></div><div class="bk-stat-icon" style="background:#dcfce7;color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg></div></div></div>
    </div>

    <div class="inv-table-wrap">
      <table class="inv-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sort('name')" class="sortable">Expense # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('expense_type')" class="sortable">Category <span v-html="sortArrow('expense_type')"></span></th>
            <th @click="sort('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
            <th @click="sort('employee_name')" class="sortable">Employee <span v-html="sortArrow('employee_name')"></span></th>
            <th>Status</th>
            <th @click="sort('total_claimed_amount')" class="sortable ta-r">Amount <span v-html="sortArrow('total_claimed_amount')"></span></th>
            <th style="width:50px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 8" :key="n"><td colspan="8"><div class="shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="e in paged" :key="e.name" class="inv-row" :class="{selected:selected.has(e.name)}">
              <td><input type="checkbox" :checked="selected.has(e.name)" @change="toggle(e.name)" /></td>
              <td @click="openView(e)"><span class="inv-link">{{ e.name }}</span></td>
              <td @click="openView(e)">{{ e.expense_type||'—' }}</td>
              <td @click="openView(e)" class="text-muted mono-sm">{{ fmtDate(e.posting_date) }}</td>
              <td @click="openView(e)">{{ e.employee_name||e.employee||'—' }}</td>
              <td @click="openView(e)"><span class="inv-status-badge" :class="statusClass(e)">{{ statusLabel(e) }}</span></td>
              <td @click="openView(e)" class="ta-r mono-sm">{{ fmtCur(e.total_claimed_amount||e.grand_total) }}</td>
              <td style="display:flex;gap:4px;justify-content:flex-end">
                <button class="inv-act-btn" @click="openView(e)"><span v-html="icon('eye',13)"></span></button>
                <button v-if="e.docstatus===0" class="inv-act-btn" @click="openEdit(e)"><span v-html="icon('edit',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="exp-empty">No expenses found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Pagination ── -->
    <div v-if="!loading && sorted.length" style="padding:12px 4px 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- Drawer -->
    <div v-if="drawerOpen" class="inv-drawer-bg" @click.self="drawerOpen=false"></div>
    <div class="inv-drawer-panel" :class="{open:drawerOpen}">

      <!-- Header -->
      <div class="inv-dh">
        <div>
          <div class="inv-dh-title">{{ editingName ? 'Edit Expense' : 'New Expense' }}</div>
          <div class="inv-dh-sub">{{ editingName ? editingName : 'Fill in the details below' }}</div>
        </div>
        <button class="inv-dclose" @click="drawerOpen=false"><span v-html="icon('x',15)"></span></button>
      </div>

      <div class="inv-dbody">

        <!-- Section: Vendor & Date -->
        <div class="exp-section">
          <div class="inv-sec-lbl">Basic Details</div>
          <div class="inv-fg inv-fg2">
            <div style="grid-column:1/-1">
              <label class="inv-lbl">Vendor / Supplier <span class="req">*</span></label>
              <SearchableSelect v-model="form.employee_name" :options="vendorOptions"
                placeholder="Search supplier…" @search="fetchVendors" @open="fetchVendors('')"
                @select="opt => { form.employee_name = opt?.value ?? opt; form.vendor_display = opt?.label ?? opt?.value ?? ''; }" />
            </div>
            <div>
              <label class="inv-lbl">Expense Date <span class="req">*</span></label>
              <input v-model="form.posting_date" type="date" class="inv-fi" />
            </div>
            <div>
              <label class="inv-lbl">Category <span class="req">*</span></label>
              <select v-model="form.expense_type" class="inv-fi" :class="!form.expense_type ? 'exp-select-empty' : ''">
                <option value="">— Select —</option>
                <option v-for="c in expenseCategories" :key="c" :value="c">{{ c }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Section: Amount & Accounts -->
        <div class="exp-section">
          <div class="inv-sec-lbl">Payment Details</div>
          <div class="inv-fg inv-fg2">
            <div>
              <label class="inv-lbl">Amount <span class="req">*</span></label>
              <div class="exp-amount-wrap">
                <span class="exp-amount-prefix">₹</span>
                <input v-model.number="form.total_claimed_amount" type="number" min="0" step="0.01" class="inv-fi exp-amount-input" placeholder="0.00" />
              </div>
            </div>
            <div>
              <label class="inv-lbl">Expense Account <span class="req">*</span></label>
              <SearchableSelect v-model="form.expense_account" :options="expenseAccountOptions"
                placeholder="Search expense account…"
                @search="fetchExpenseAccounts" @open="fetchExpenseAccounts('')" />
            </div>
            <div style="grid-column:1/-1">
              <label class="inv-lbl">Paid Through <span class="req">*</span></label>
              <SearchableSelect v-model="form.paid_through" :options="paidThroughOptions"
                placeholder="Search bank / cash account…"
                @search="fetchPaidThroughAccounts" @open="fetchPaidThroughAccounts('')" />
            </div>
            <div style="grid-column:1/-1">
              <label class="inv-lbl">Cost Center</label>
              <select v-model="form.cost_center" class="inv-fi">
                <option value="">— None —</option>
                <option v-for="cc in costCenters" :key="cc" :value="cc">{{ cc }}</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Section: Notes & Receipt -->
        <div class="exp-section">
          <div class="inv-sec-lbl">Additional Info</div>
          <div style="margin-bottom:12px">
            <label class="inv-lbl">Description <span class="req">*</span></label>
            <textarea v-model="form.remark" rows="3" class="inv-fi exp-textarea" placeholder="What was this expense for?"></textarea>
          </div>
          <div>
            <label class="inv-lbl">Attach Receipt</label>
            <div v-if="receiptFile" class="exp-receipt-attached">
              <div class="exp-receipt-attached-icon"><span v-html="icon('check',13)"></span></div>
              <span class="exp-receipt-filename">{{receiptFile.name}}</span>
              <button @click="receiptFile=null" class="exp-receipt-remove" v-html="icon('x',12)"></button>
            </div>
            <label v-else class="exp-receipt-drop">
              <div class="exp-receipt-drop-icon"><span v-html="icon('fileplus',16)"></span></div>
              <div>
                <div class="exp-receipt-drop-text">Click to attach receipt</div>
                <div class="exp-receipt-drop-hint">Supports image or PDF</div>
              </div>
              <input type="file" accept="image/*,.pdf" style="display:none" @change="onReceiptChange"/>
            </label>
          </div>
        </div>

      </div>

      <!-- Footer -->
      <div class="inv-dfooter">
        <button class="form-btn form-btn-outline" @click="drawerOpen=false">Cancel</button>
        <div style="display:flex;gap:8px">
          <button class="form-btn form-btn-success" :disabled="drawerSaving" @click="saveExpense(0)">
            <span v-html="icon('save',13)"></span> {{ drawerSaving ? 'Saving…' : 'Save Draft' }}
          </button>
          <button class="form-btn form-btn-primary" :disabled="drawerSaving" @click="saveExpense(1)">
            <span v-html="icon('check',13)"></span> {{ drawerSaving ? 'Saving…' : 'Submit' }}
          </button>
        </div>
      </div>
    </div>

    <!-- View Drawer -->
    <div v-if="viewOpen" class="inv-drawer-bg" @click.self="viewOpen=false"></div>
    <div class="inv-drawer-panel exp-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">

        <!-- View Header -->
        <div class="inv-view-header">
          <div>
            <div class="inv-view-number">{{ viewDoc.name }}</div>
            <div class="inv-view-subtitle">{{ viewDoc.expense_type||'Expense' }} · {{ fmtCur(viewDoc.total_claimed_amount||viewDoc.grand_total) }}</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <span class="inv-hdr-badge" :class="statusClass(viewDoc)">{{ statusLabel(viewDoc) }}</span>
            <button class="inv-dclose" @click="viewOpen=false"><span v-html="icon('x',15)"></span></button>
          </div>
        </div>

        <!-- View Body -->
        <div class="exp-vbody">

          <div class="exp-vsection">
            <div class="exp-vgrid-2">
              <div class="exp-vmeta">
                <div class="exp-vmeta-lbl">Date</div>
                <div class="exp-vmeta-val">{{ fmtDate(viewDoc.posting_date) }}</div>
              </div>
              <div class="exp-vmeta">
                <div class="exp-vmeta-lbl">Vendor / Supplier</div>
                <div class="exp-vmeta-val">{{ viewDoc.employee_name||viewDoc.vendor||'—' }}</div>
              </div>
            </div>
          </div>

          <div class="exp-vsection">
            <div class="exp-vmeta">
              <div class="exp-vmeta-lbl">Category</div>
              <div class="exp-vmeta-val">{{ viewDoc.expense_type||'—' }}</div>
            </div>
          </div>

          <div class="exp-vsection">
            <div class="exp-vmeta">
              <div class="exp-vmeta-lbl">Expense Account</div>
              <div class="exp-vmeta-val exp-vmeta-mono">{{ viewDoc.expense_account||'—' }}</div>
            </div>
          </div>

          <div class="exp-vsection">
            <div class="exp-vmeta">
              <div class="exp-vmeta-lbl">Paid Through</div>
              <div class="exp-vmeta-val exp-vmeta-mono">{{ viewDoc.paid_through||'—' }}</div>
            </div>
          </div>

          <div v-if="viewDoc.remark||viewDoc.notes||viewDoc.description" class="exp-vsection">
            <div class="exp-vmeta">
              <div class="exp-vmeta-lbl">Description / Notes</div>
              <div class="exp-vmeta-val exp-vmeta-desc">{{ viewDoc.remark||viewDoc.notes||viewDoc.description }}</div>
            </div>
          </div>

          <div v-if="viewDoc.attach" class="exp-vsection">
            <div class="exp-vmeta">
              <div class="exp-vmeta-lbl">Receipt</div>
              <a :href="viewDoc.attach" target="_blank" class="exp-vattach-link">
                <div class="exp-vattach-icon"><span v-html="icon('paperclip',13)"></span></div>
                <span class="exp-vattach-name">{{ viewDoc.attach.split('/').pop() }}</span>
                <span v-html="icon('externallink',11)" style="flex-shrink:0;color:#93c5fd;margin-left:auto"></span>
              </a>
            </div>
          </div>

        </div>

        <!-- View Footer -->
        <div class="inv-dfooter">
          <button class="form-btn form-btn-outline" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="form-btn form-btn-success" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
        </div>

      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGet, apiGET, apiSave, apiSubmit, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import Pagination from "../components/Pagination.vue";
import { usePagination } from "../composables/usePagination.js";

const { toast } = useToast();
const activeTab=ref("all");
const tabs=[{key:"all",label:"All"},{key:"draft",label:"Draft"},{key:"submitted",label:"Submitted"},{key:"paid",label:"Paid"}];
const expenseCategories=["Travel","Food & Meals","Accommodation","Office Supplies","Utilities","Marketing","Software","Hardware","Training","Miscellaneous"];

const list=ref([]),loading=ref(false),search=ref(""),selected=ref(new Set());
const drawerOpen=ref(false),drawerSaving=ref(false),editingName=ref("");
const viewOpen=ref(false),viewDoc=ref(null);
const receiptFile=ref(null);
function onReceiptChange(e){const f=e.target.files[0];if(f)receiptFile.value=f;e.target.value="";}
const sortCol=ref("posting_date"),sortDir=ref("desc");
let _id=1;
const vendorOptions          = ref([]);
const itemOptions            = ref([]);
const expenseAccountOptions  = ref([]);
const paidThroughOptions     = ref([]);

async function fetchVendors(q = "") {
  try {
    const filters = [["disabled", "=", 0]];
    if (q) filters.push(["supplier_name", "like", `%${q}%`]);
    const rows = await apiList("Supplier", { fields: ["name", "supplier_name"], filters, limit: 30, order: "supplier_name asc" });
    vendorOptions.value = rows.map(r => ({ label: r.supplier_name || r.name, value: r.name }));
  } catch { vendorOptions.value = []; }
}
async function fetchExpenseItems(q = "") {
  try {
    const filters = [["disabled", "=", 0]];
    if (q) filters.push(["item_name", "like", `%${q}%`]);
    const rows = await apiList("Item", { fields: ["name", "item_name", "description", "standard_rate"], filters, limit: 30, order: "item_name asc" });
    itemOptions.value = rows.map(r => ({ label: r.item_name || r.name, value: r.item_name || r.name, description: r.description || "", rate: r.standard_rate || 0 }));
  } catch { itemOptions.value = []; }
}
async function fetchExpenseAccounts(q = "") {
  try {
    const company = await resolveCompany();
    const filters = [["is_group","=",0],["disabled","=",0],["company","=",company],["account_type","=","Expense"]];
    if (q) filters.push(["name","like",`%${q}%`]);
    const rows = await apiList("Account", { fields:["name"], filters, limit:30, order:"name asc" });
    expenseAccountOptions.value = rows.map(r => ({ label: r.name, value: r.name }));
  } catch { expenseAccountOptions.value = []; }
}
async function fetchPaidThroughAccounts(q = "") {
  try {
    const company = await resolveCompany();
    const filters = [["is_group","=",0],["disabled","=",0],["company","=",company],["account_type","in",["Bank","Cash"]]];
    if (q) filters.push(["name","like",`%${q}%`]);
    const rows = await apiList("Account", { fields:["name","account_type"], filters, limit:30, order:"name asc" });
    paidThroughOptions.value = rows.map(r => ({ label: r.name, value: r.name }));
  } catch { paidThroughOptions.value = []; }
}
function onExpItemSelect(line, opt) {
  line.description = opt?.label || opt?.value || "";
  if (opt?.rate) line.amount = opt.rate;
}
const form=reactive({posting_date:new Date().toISOString().slice(0,10),employee_name:"",vendor_display:"",expense_type:"",total_claimed_amount:0,currency:"INR",remark:"",expense_account:"",paid_through:"",cost_center:""});
const costCenters=ref([]);
async function fetchCostCenters(){try{const co=await resolveCompany();const r=await apiGET("frappe.client.get_list",{doctype:"Cost Center",fields:JSON.stringify(["name"]),filters:JSON.stringify([["disabled","=",0],["company","=",co],["is_group","=",0]]),order_by:"name asc",limit_page_length:100})||[];costCenters.value=r.map(c=>c.name);}catch{costCenters.value=[];}}

async function load(){
  loading.value=true;
  try{
    const co=await resolveCompany();
    const raw=await apiList("Expense",{
      fields:["name","posting_date","expense_type","description","amount","tax_amount",
              "total_amount","vendor","status","docstatus","expense_account","paid_through","attach","notes"],
      filters:[["company","=",co]],
      limit:200,
      order:"posting_date desc",
    });
    // Map to legacy shape so the rest of the template doesn't need to change.
    list.value=raw.map(e=>({
      ...e,
      // template uses these field names — provide compatibility aliases:
      employee_name: e.vendor||"",   // resolved below
      total_claimed_amount: e.total_amount||e.amount||0,
    }));
    // Resolve vendor display names client-side (Expense doctype has no vendor_name column)
    const missingVendors = [...new Set(list.value.filter(e => e.employee_name && !e._vendor_name).map(e => e.employee_name))];
    if (missingVendors.length) {
      const sups = await apiList("Supplier", { fields: ["name","supplier_name"], filters: [["name","in",missingVendors]], limit: missingVendors.length }).catch(()=>[]);
      const nameMap = Object.fromEntries(sups.map(s => [s.name, s.supplier_name || s.name]));
      list.value = list.value.map(e => ({ ...e, employee_name: nameMap[e.employee_name] || e.employee_name }));
    }
  }catch(e){toast.error(e.message||"Failed to load expenses");}
  finally{loading.value=false;}
}

function statusLabel(e){if(e.docstatus===2)return"Cancelled";if(e.docstatus===0)return"Draft";const s=e.status||"";if(s==="Paid")return"Paid";return"Submitted";}
function statusClass(e){if(e.docstatus===2)return"badge-grey";if(e.docstatus===0)return"badge-orange";if(statusLabel(e)==="Paid")return"badge-green";return"badge-blue";}
const now=new Date();
const monthStart=new Date(now.getFullYear(),now.getMonth(),1).toISOString().slice(0,10);
const monthTotal=computed(()=>list.value.filter(e=>e.posting_date>=monthStart).reduce((s,e)=>s+flt(e.total_claimed_amount||e.grand_total),0));
const unpaidTotal=computed(()=>list.value.filter(e=>e.docstatus===1&&statusLabel(e)!=="Paid").reduce((s,e)=>s+flt(e.total_claimed_amount||e.grand_total),0));
const counts=computed(()=>({draft:list.value.filter(e=>e.docstatus===0).length}));
const _exYM  = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _exLYM = () => { const d=new Date(); d.setMonth(d.getMonth()-1); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _exTr  = (a,b) => { if(!b&&!a) return {pct:0,up:true}; if(!b) return {pct:100,up:true}; const p=Math.round((a-b)/b*100); return {pct:Math.abs(p),up:p>=0}; };
const expThisMonth = computed(()=>{ const ym=_exYM(); const r=list.value.filter(e=>(e.posting_date||'').startsWith(ym)); return {count:r.length,total:r.reduce((s,e)=>s+flt(e.total_claimed_amount||e.grand_total),0)}; });
const expAvg = computed(()=>{ const p=list.value.filter(e=>(e.total_claimed_amount||e.grand_total)>0); return p.length?p.reduce((s,e)=>s+flt(e.total_claimed_amount||e.grand_total),0)/p.length:0; });
const expTrends = computed(()=>({
  total:     _exTr(expThisMonth.value.count, list.value.filter(e=>(e.posting_date||'').startsWith(_exLYM())).length),
  month:     _exTr(expThisMonth.value.total, list.value.filter(e=>(e.posting_date||'').startsWith(_exLYM())).reduce((s,e)=>s+flt(e.total_claimed_amount||e.grand_total),0)),
  submitted: _exTr(list.value.filter(e=>e.docstatus===1&&statusLabel(e)!=='Paid').length, list.value.filter(e=>(e.posting_date||'').startsWith(_exLYM())&&e.docstatus===1&&statusLabel(e)!=='Paid').length),
  draft:     _exTr(list.value.filter(e=>e.docstatus===0).length, list.value.filter(e=>(e.posting_date||'').startsWith(_exLYM())&&e.docstatus===0).length),
}));
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
const filtered=computed(()=>{let r=list.value;if(activeTab.value==="draft")r=r.filter(e=>e.docstatus===0);if(activeTab.value==="submitted")r=r.filter(e=>e.docstatus===1&&statusLabel(e)!=="Paid");if(activeTab.value==="paid")r=r.filter(e=>statusLabel(e)==="Paid");if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(x=>(x.name||"").toLowerCase().includes(q)||(x.employee_name||"").toLowerCase().includes(q)||(x.expense_type||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
const { page, pageSize, paged } = usePagination(sorted, { storageKey: "expenses" });
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const allChecked=computed(()=>sorted.value.length>0&&sorted.value.every(e=>selected.value.has(e.name)));
function toggle(n){const s=new Set(selected.value);s.has(n)?s.delete(n):s.add(n);selected.value=s;}
function toggleAll(e){selected.value=e.target.checked?new Set(sorted.value.map(x=>x.name)):new Set();}
function openNew(){editingName.value="";receiptFile.value=null;Object.assign(form,{posting_date:new Date().toISOString().slice(0,10),employee_name:"",vendor_display:"",expense_type:"",total_claimed_amount:0,currency:"INR",remark:"",expense_account:"",paid_through:"",cost_center:""});drawerOpen.value=true;}
async function openEdit(e){
  editingName.value=e.name;
  try{
    const doc=await apiGet("Expense",e.name);
    Object.assign(form,{
      posting_date: doc.posting_date||"",
      employee_name: doc.vendor||"",   // template uses "Employee Name" label, we map it to vendor
      expense_account: doc.expense_account||"",
      paid_through:    doc.paid_through||"",
      cost_center:     doc.cost_center||"",
      expense_type: doc.expense_type||"",
      total_claimed_amount: flt(doc.total_amount||doc.amount),
      currency: "INR",
      remark: doc.description||doc.notes||"",
    });
    // Expense is FLAT (one row = one expense), so seed a single line for editing
  }catch{
    Object.assign(form,{
      posting_date:e.posting_date||"",
      employee_name:e.vendor||e.employee_name||"",
      expense_type:e.expense_type||"",
      total_claimed_amount:flt(e.total_amount||e.total_claimed_amount),
      currency:"INR",
      remark:e.description||"",
    });
  }
  drawerOpen.value=true;
}
async function openView(e) {
  viewDoc.value = e;
  viewOpen.value = true;
  // Fetch full doc to get expense_account, paid_through, attach, notes
  try {
    const full = await apiGet("Expense", e.name);
    if (full) viewDoc.value = { ...e, ...full, employee_name: e.employee_name || full.vendor || "" };
  } catch {}
}

async function saveExpense(submit){
  if(!flt(form.total_claimed_amount)) return toast.error("Enter an amount");
  if(!form.expense_type)              return toast.error("Category is required");
  if(!form.expense_account)           return toast.error("Expense Account is required");
  if(!form.paid_through)              return toast.error("Paid Through is required");
  if(!form.remark)                    return toast.error("Description is required");
  drawerSaving.value=true;
  try{
    const company=await resolveCompany();
    const amt=flt(form.total_claimed_amount);
    const doc={
      doctype:"Expense",
      company,
      posting_date:form.posting_date||new Date().toISOString().slice(0,10),
      expense_type:form.expense_type,
      description:form.remark,
      amount:amt,
      tax_amount:0,
      total_amount:amt,
      vendor:form.employee_name||"",
      expense_account: form.expense_account,
      paid_through:    form.paid_through,
      cost_center:     form.cost_center||"",
      notes:form.remark||"",
    };
    if(editingName.value) doc.name=editingName.value;
    const saved=await apiSave(doc);
    // Upload attachment to Frappe and save the file URL in the `attach` field
    if(receiptFile.value && saved?.name){
      try{
        const url = await uploadAttachment(receiptFile.value, "Expense", saved.name);
        if(url){
          await apiSave({ doctype:"Expense", name:saved.name, attach: url });
        }
      }catch(uploadErr){
        // Non-fatal — expense saved, just warn about the attachment
        toast.warning("Expense saved but attachment upload failed: " + (uploadErr.message||""));
      }
    }
    if(submit && saved?.name) await apiSubmit("Expense",saved.name);
    toast.success(`Expense ${saved?.name} ${submit?"submitted":"saved"}`);
    drawerOpen.value=false;
    await load();
  }catch(e){toast.error(e.message||"Failed to save expense");}
  finally{drawerSaving.value=false;}
}

async function uploadAttachment(file, doctype, docname) {
  const fd = new FormData();
  fd.append("file", file, file.name);
  fd.append("doctype", doctype);
  fd.append("docname", docname);
  fd.append("fieldname", "attach");
  fd.append("is_private", "0");
  const res = await fetch("/api/method/upload_file", {
    method: "POST",
    headers: { "X-Frappe-CSRF-Token": window.csrf_token || frappe?.csrf_token || "" },
    body: fd,
  });
  if(!res.ok) throw new Error(`Upload failed: ${res.status}`);
  const data = await res.json();
  return data?.message?.file_url || data?.file_url || null;
}
onMounted(() => { load(); fetchVendors(""); fetchExpenseItems(""); fetchExpenseAccounts(""); fetchPaidThroughAccounts(""); fetchCostCenters(); });
</script>

<style scoped>
/* ── Drawer slide-in ── */
.inv-drawer-panel { position:fixed;top:0;right:-540px;bottom:0;width:540px;background:#fff;box-shadow:-12px 0 40px rgba(0,0,0,.12);z-index:8000;display:flex;flex-direction:column;transition:right .24s cubic-bezier(.4,0,.2,1); }
.inv-drawer-panel.open { right:0; }
.exp-view-drawer { width:440px;right:-440px; }
.exp-view-drawer.open { right:0; }

/* ── Section wrappers ── */
.exp-section { background:#fff; border-bottom:1px solid #f1f5f9; padding:18px 22px; }

/* ── Amount field with prefix ── */
.exp-amount-wrap { position:relative; display:flex; align-items:center; }
.exp-amount-prefix { position:absolute; left:11px; font-size:13px; font-weight:600; color:#6b7280; pointer-events:none; }
.exp-amount-input { padding-left:24px !important; font-weight:600; font-size:14px !important; }

/* ── Receipt Upload ── */
.exp-receipt-drop { display:flex; align-items:center; gap:12px; padding:14px 16px; border:2px dashed #bfdbfe; border-radius:10px; cursor:pointer; background:#f0f7ff; transition:border-color .15s,background .15s; }
.exp-receipt-drop:hover { border-color:#2563eb; background:#eff6ff; }
.exp-receipt-drop-icon { width:36px; height:36px; border-radius:8px; background:#dbeafe; display:flex; align-items:center; justify-content:center; color:#2563eb; flex-shrink:0; }
.exp-receipt-drop-text { font-size:13px; font-weight:600; color:#1d4ed8; }
.exp-receipt-drop-hint { font-size:11.5px; color:#93c5fd; margin-top:1px; }
.exp-receipt-attached { display:flex; align-items:center; gap:10px; padding:10px 14px; background:#f0fdf4; border:1px solid #bbf7d0; border-radius:10px; font-size:12.5px; }
.exp-receipt-attached-icon { width:28px; height:28px; border-radius:50%; background:#dcfce7; display:flex; align-items:center; justify-content:center; color:#16a34a; flex-shrink:0; }
.exp-receipt-filename { flex:1; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#15803d; font-weight:500; }
.exp-receipt-remove { background:none; border:none; cursor:pointer; color:#dc2626; padding:2px; display:flex; align-items:center; border-radius:4px; }
.exp-receipt-remove:hover { background:#fef2f2; }

/* ── View body sections ── */
.exp-vbody { flex:1; overflow-y:auto; background:#f8fafc; display:flex; flex-direction:column; }
.exp-vsection { background:#fff; border-bottom:1px solid #f1f5f9; padding:14px 22px; }
.exp-vgrid-2 { display:grid; grid-template-columns:1fr 1fr; gap:16px; }
.exp-vmeta { display:flex; flex-direction:column; gap:4px; }
.exp-vmeta-lbl { font-size:10.5px; font-weight:700; color:#94a3b8; text-transform:uppercase; letter-spacing:.07em; }
.exp-vmeta-val { font-size:13.5px; font-weight:500; color:#111827; line-height:1.4; }
.exp-vmeta-mono { font-family:'SF Mono','Fira Code',monospace; font-size:12.5px; color:#374151; }
.exp-vmeta-desc { font-size:13px; color:#374151; line-height:1.6; font-weight:400; }

/* ── Receipt link in view ── */
.exp-vattach-link { display:inline-flex; align-items:center; gap:10px; margin-top:6px; padding:10px 14px; background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; text-decoration:none; max-width:100%; transition:background .15s; }
.exp-vattach-link:hover { background:#dbeafe; }
.exp-vattach-icon { width:30px; height:30px; border-radius:8px; background:#dbeafe; display:flex; align-items:center; justify-content:center; color:#2563eb; flex-shrink:0; }
.exp-vattach-name { font-size:12.5px; font-weight:600; color:#1d4ed8; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; flex:1; }

/* ── Misc ── */
.exp-empty { text-align:center; color:#9ca3af; padding:48px!important; cursor:default!important; }
.exp-textarea { resize:vertical; min-height:80px; line-height:1.5; }
.req { color:#dc2626; }
.ta-r { text-align:right!important; }
.text-muted { color:#6b7280; }
.mono-sm { font-family:monospace; font-size:12.5px; }
</style>