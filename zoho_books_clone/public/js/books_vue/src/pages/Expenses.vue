<template>
  <div class="exp-page">
    <div class="exp-actions">
      <div class="exp-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search expenses…" class="exp-search-input" />
      </div>
      <div class="exp-pills">
        <button v-for="t in tabs" :key="t.key" class="exp-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="exp-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="exp-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Expense</button>
      </div>
    </div>

    <div class="exp-summary" v-if="!loading">
      <div class="exp-sum-card"><div class="exp-sum-lbl">This Month</div><div class="exp-sum-val">{{ fmtCur(monthTotal) }}</div></div>
      <div class="exp-sum-card"><div class="exp-sum-lbl">Unpaid</div><div class="exp-sum-val red">{{ fmtCur(unpaidTotal) }}</div></div>
      <div class="exp-sum-card"><div class="exp-sum-lbl">Draft</div><div class="exp-sum-val orange">{{ counts.draft }}</div></div>
      <div class="exp-sum-card"><div class="exp-sum-lbl">Total Records</div><div class="exp-sum-val">{{ list.length }}</div></div>
    </div>

    <div class="exp-card">
      <table class="exp-table">
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
            <tr v-for="n in 8" :key="n"><td colspan="8"><div class="exp-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="e in sorted" :key="e.name" class="exp-row" :class="{selected:selected.has(e.name)}">
              <td><input type="checkbox" :checked="selected.has(e.name)" @change="toggle(e.name)" /></td>
              <td @click="openView(e)"><span class="exp-num">{{ e.name }}</span></td>
              <td @click="openView(e)">{{ e.expense_type||'—' }}</td>
              <td @click="openView(e)" class="text-muted mono-sm">{{ fmtDate(e.posting_date) }}</td>
              <td @click="openView(e)">{{ e.employee_name||e.employee||'—' }}</td>
              <td @click="openView(e)"><span class="exp-badge" :class="statusClass(e)">{{ statusLabel(e) }}</span></td>
              <td @click="openView(e)" class="ta-r mono-sm">{{ fmtCur(e.total_claimed_amount||e.grand_total) }}</td>
              <td class="exp-act-cell">
                <button class="exp-act-btn" @click="openView(e)"><span v-html="icon('eye',13)"></span></button>
                <button v-if="e.docstatus===0" class="exp-act-btn" @click="openEdit(e)"><span v-html="icon('edit',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="exp-empty">No expenses found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Drawer -->
    <div v-if="drawerOpen" class="exp-overlay" @click.self="drawerOpen=false"></div>
    <div class="exp-drawer" :class="{open:drawerOpen}">
      <div class="exp-dheader">
        <div class="exp-dheader-title">{{ editingName?'Edit Expense':'New Expense' }}</div>
        <button class="exp-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="exp-dbody">
        <div class="exp-fields-grid">
          <div class="exp-field" style="grid-column:1/-1">
            <label class="exp-label">Vendor / Supplier <span class="req">*</span></label>
            <SearchableSelect v-model="form.employee_name" :options="vendorOptions"
              placeholder="Search supplier…" @search="fetchVendors" @open="fetchVendors('')"
              @select="opt => { form.employee_name = opt?.value ?? opt; form.vendor_display = opt?.label ?? opt?.value ?? ''; }" />
          </div>
          <div class="exp-field">
            <label class="exp-label">Expense Date <span class="req">*</span></label>
            <input v-model="form.posting_date" type="date" class="exp-input" />
          </div>
          <div class="exp-field">
            <label class="exp-label">Category</label>
            <select v-model="form.expense_type" class="exp-select">
              <option value="">— Select —</option>
              <option v-for="c in expenseCategories" :key="c" :value="c">{{ c }}</option>
            </select>
          </div>
          <div class="exp-field">
            <label class="exp-label">Amount <span class="req">*</span></label>
            <input v-model.number="form.total_claimed_amount" type="number" min="0" step="0.01" class="exp-input" placeholder="0.00" />
          </div>
          <!-- <div class="exp-field">
            <label class="exp-label">Currency</label>
            <input v-model="form.currency" type="text" class="exp-input" placeholder="INR" />
          </div> -->
          <div class="exp-field">
            <label class="exp-label">Expense Account <span class="req">*</span></label>
            <SearchableSelect v-model="form.expense_account" :options="expenseAccountOptions"
              placeholder="Search expense account…"
              @search="fetchExpenseAccounts" @open="fetchExpenseAccounts('')" />
          </div>
          <div class="exp-field">
            <label class="exp-label">Paid Through <span class="req">*</span></label>
            <SearchableSelect v-model="form.paid_through" :options="paidThroughOptions"
              placeholder="Search bank / cash account…"
              @search="fetchPaidThroughAccounts" @open="fetchPaidThroughAccounts('')" />
          </div>
          <div class="exp-field" style="grid-column:1/-1">
            <label class="exp-label">Description</label>
            <textarea v-model="form.remark" rows="2" class="exp-input" placeholder="What was this expense for?"></textarea>
          </div>
        </div>

        <!-- Receipt upload -->
        <div class="exp-field" style="margin-top:4px">
          <label class="exp-label">Attach Receipt</label>
          <div v-if="receiptFile" style="display:flex;align-items:center;gap:8px;padding:8px 12px;background:#EBFBEE;border:1px solid #8CE99A;border-radius:8px;font-size:12.5px">
            <span v-html="icon('check',12)" style="color:#2F9E44"></span>
            <span style="flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{receiptFile.name}}</span>
            <button @click="receiptFile=null" style="background:none;border:none;cursor:pointer;color:#C92A2A;padding:2px" v-html="icon('x',12)"></button>
          </div>
          <label v-else style="display:flex;align-items:center;gap:8px;padding:10px 14px;border:2px dashed #BAC8FF;border-radius:8px;cursor:pointer;background:#F8F9FF;font-size:12.5px;color:#4C6EF5">
            <span v-html="icon('fileplus',13)"></span>
            Click to attach receipt (image or PDF)
            <input type="file" accept="image/*,.pdf" style="display:none" @change="onReceiptChange"/>
          </label>
        </div>
      </div>
      <div class="exp-dfooter">
        <button class="exp-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="exp-btn-save" :disabled="drawerSaving" @click="saveExpense(0)"><span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}</button>
        <button class="exp-btn-primary" :disabled="drawerSaving" @click="saveExpense(1)"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}</button>
      </div>
    </div>

    <!-- View -->
    <div v-if="viewOpen" class="exp-overlay" @click.self="viewOpen=false"></div>
    <div class="exp-drawer exp-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="exp-view-head">
          <div><div class="exp-view-num">{{ viewDoc.name }}</div><div class="exp-view-sub">{{ viewDoc.expense_type||'Expense' }}</div></div>
          <div style="text-align:right"><div class="exp-view-amount">{{ fmtCur(viewDoc.total_claimed_amount||viewDoc.grand_total) }}</div><span class="exp-badge" :class="statusClass(viewDoc)">{{ statusLabel(viewDoc) }}</span></div>
          <button class="exp-dclose exp-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="exp-dbody">
          <div class="exp-meta-grid">
            <div><div class="exp-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
            <div><div class="exp-meta-lbl">Vendor / Supplier</div><div>{{ viewDoc.employee_name||viewDoc.vendor||'—' }}</div></div>
            <div><div class="exp-meta-lbl">Category</div><div>{{ viewDoc.expense_type||'—' }}</div></div>
            <!-- <div><div class="exp-meta-lbl">Currency</div><div>{{ viewDoc.currency||'INR' }}</div></div> -->
            <div style="grid-column:1/-1"><div class="exp-meta-lbl">Expense Account</div><div class="mono-sm" style="font-size:12.5px">{{ viewDoc.expense_account||'—' }}</div></div>
            <div style="grid-column:1/-1"><div class="exp-meta-lbl">Paid Through</div><div class="mono-sm" style="font-size:12.5px">{{ viewDoc.paid_through||'—' }}</div></div>
          </div>
          <div v-if="viewDoc.remark||viewDoc.notes||viewDoc.description" style="margin-top:4px">
            <div class="exp-meta-lbl">Description / Notes</div>
            <div style="font-size:13px;color:#374151;margin-top:4px;line-height:1.5">{{ viewDoc.remark||viewDoc.notes||viewDoc.description }}</div>
          </div>
          <!-- Attachment -->
          <div v-if="viewDoc.attach" style="margin-top:4px">
            <div class="exp-meta-lbl">Receipt</div>
            <a :href="viewDoc.attach" target="_blank" class="exp-attach-link">
              <span v-html="icon('paperclip',13)"></span>
              <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{ viewDoc.attach.split('/').pop() }}</span>
              <span v-html="icon('externallink',12)" style="flex-shrink:0;color:#9ca3af"></span>
            </a>
          </div>
        </div>
        <div class="exp-dfooter">
          <button class="exp-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="exp-btn-save" @click="openEdit(viewDoc);viewOpen=false"><span v-html="icon('edit',13)"></span> Edit</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGet, apiSave, apiSubmit, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

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
const form=reactive({posting_date:new Date().toISOString().slice(0,10),employee_name:"",vendor_display:"",expense_type:"",total_claimed_amount:0,currency:"INR",remark:"",expense_account:"",paid_through:""});

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
function fmtCur(v){return new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",minimumFractionDigits:2}).format(flt(v));}
const filtered=computed(()=>{let r=list.value;if(activeTab.value==="draft")r=r.filter(e=>e.docstatus===0);if(activeTab.value==="submitted")r=r.filter(e=>e.docstatus===1&&statusLabel(e)!=="Paid");if(activeTab.value==="paid")r=r.filter(e=>statusLabel(e)==="Paid");if(search.value.trim()){const q=search.value.toLowerCase();r=r.filter(x=>(x.name||"").toLowerCase().includes(q)||(x.employee_name||"").toLowerCase().includes(q)||(x.expense_type||"").toLowerCase().includes(q));}return r;});
const sorted=computed(()=>{const col=sortCol.value;return[...filtered.value].sort((a,b)=>{const av=a[col]??"",bv=b[col]??"";const c=typeof av==="number"?av-bv:String(av).localeCompare(String(bv));return sortDir.value==="asc"?c:-c;});});
function sort(col){if(sortCol.value===col)sortDir.value=sortDir.value==="asc"?"desc":"asc";else{sortCol.value=col;sortDir.value="asc";}}
function sortArrow(col){if(sortCol.value!==col)return'<span style="color:#d1d5db">⇅</span>';return sortDir.value==="asc"?"↑":"↓";}
const allChecked=computed(()=>sorted.value.length>0&&sorted.value.every(e=>selected.value.has(e.name)));
function toggle(n){const s=new Set(selected.value);s.has(n)?s.delete(n):s.add(n);selected.value=s;}
function toggleAll(e){selected.value=e.target.checked?new Set(sorted.value.map(x=>x.name)):new Set();}
function openNew(){editingName.value="";receiptFile.value=null;Object.assign(form,{posting_date:new Date().toISOString().slice(0,10),employee_name:"",vendor_display:"",expense_type:"",total_claimed_amount:0,currency:"INR",remark:"",expense_account:"",paid_through:""});drawerOpen.value=true;}
async function openEdit(e){
  editingName.value=e.name;
  try{
    const doc=await apiGet("Expense",e.name);
    Object.assign(form,{
      posting_date: doc.posting_date||"",
      employee_name: doc.vendor||"",   // template uses "Employee Name" label, we map it to vendor
      expense_account: doc.expense_account||"",
      paid_through:    doc.paid_through||"",
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
  if(!flt(form.total_claimed_amount)){
    return toast.error("Enter an amount");
  }
  drawerSaving.value=true;
  try{
    const company=await resolveCompany();
    const amt=flt(form.total_claimed_amount);
    const doc={
      doctype:"Expense",
      company,
      posting_date:form.posting_date||new Date().toISOString().slice(0,10),
      expense_type:form.expense_type||"Miscellaneous",
      description:form.remark||"",
      amount:amt,
      tax_amount:0,
      total_amount:amt,
      vendor:form.employee_name||"",
      expense_account: form.expense_account||"",
      paid_through:    form.paid_through||"",
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
onMounted(() => { load(); fetchVendors(""); fetchExpenseItems(""); fetchExpenseAccounts(""); fetchPaidThroughAccounts(""); });
</script>

<style scoped>
.exp-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.exp-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.exp-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;}
.exp-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.exp-pills{display:flex;gap:6px;}
.exp-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.exp-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.exp-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.exp-btn-primary:hover{background:#1d4ed8;}.exp-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.exp-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.exp-btn-ghost:hover{background:#f9fafb;}
.exp-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.exp-btn-save:hover{background:#dcfce7;}.exp-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.exp-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.exp-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.exp-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.exp-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
.orange{color:#ea580c!important;}.red{color:#dc2626!important;}
.exp-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.exp-table{width:100%;border-collapse:collapse;font-size:13px;}
.exp-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.exp-table th.sortable{cursor:pointer;user-select:none;}.exp-table th.sortable:hover{color:#2563eb;}
.ta-r{text-align:right!important;}
.exp-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.exp-row:last-child td{border-bottom:none;}.exp-row:hover td{background:#f9fafb;}.exp-row.selected td{background:#eff6ff;}
.exp-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}
.exp-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-blue{background:#dbeafe;color:#2563eb;}.badge-orange{background:#fff7ed;color:#ea580c;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.exp-act-cell{display:flex;gap:4px;justify-content:flex-end;cursor:default!important;}
.exp-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.exp-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.exp-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.exp-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.exp-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.exp-drawer{position:fixed;top:0;right:-520px;bottom:0;width:520px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.exp-drawer.open{right:0;}
.exp-view-drawer{width:420px;right:-420px;}.exp-view-drawer.open{right:0;}
.exp-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.exp-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.exp-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.exp-dclose:hover{background:#f3f4f6;color:#111827;}
.exp-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.exp-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.exp-field{display:flex;flex-direction:column;gap:4px;}
.exp-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.exp-input{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.exp-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
textarea.exp-input{resize:vertical;}
.exp-select{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;cursor:pointer;}
.exp-select:focus{border-color:#2563eb;}
.exp-view-head{position:relative;display:flex;align-items:flex-start;justify-content:space-between;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#f0fdf4;}
.exp-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.exp-view-sub{font-size:13px;color:#6b7280;margin-top:2px;}
.exp-view-amount{font-size:22px;font-weight:800;font-family:monospace;color:#111827;}
.exp-vclose{position:absolute;top:12px;right:12px;}
.exp-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.exp-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.exp-attach-link{display:inline-flex;align-items:center;gap:6px;margin-top:6px;padding:8px 12px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;font-size:12.5px;font-weight:600;color:#2563eb;text-decoration:none;max-width:100%;}
.exp-attach-link:hover{background:#dbeafe;}
.exp-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>