<template>
<div class="b-page">
  <!-- Toolbar -->
  <div class="b-action-bar">
    <div style="display:flex;align-items:center;gap:6px;background:#fff;border:1px solid #E2E8F0;border-radius:20px;padding:5px 14px;flex:1;max-width:280px">
      <span v-html="icon('search',13)" style="color:#868E96;flex-shrink:0"></span>
      <input v-model="search" placeholder="Search proforma invoices…" style="border:none;outline:none;font-size:13px;width:100%;background:transparent;font-family:inherit"/>
    </div>
    <div style="display:flex;gap:6px;margin-left:auto">
      <button class="b-btn b-btn-ghost" @click="load"><span v-html="icon('refresh',13)"></span></button>
      <button class="b-btn b-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Proforma</button>
    </div>
  </div>

  <!-- Info banner -->
  <div style="background:linear-gradient(135deg,#FFF9DB,#FFF3BF);border:1px solid #FFD43B;border-radius:10px;padding:12px 18px;display:flex;gap:12px;align-items:center">
    <span style="font-size:18px">📋</span>
    <div style="font-size:12.5px;color:#876800">
      <b>Proforma Invoices</b> are pre-invoices sent to customers for advance payment or customs. They are kept as drafts and can be converted to real invoices once accepted.
    </div>
  </div>

  <!-- Table -->
  <div class="b-card" style="padding:0;overflow:hidden">
    <table class="b-table">
      <thead>
        <tr>
          <th>Proforma #</th>
          <th>Customer</th>
          <th>Date</th>
          <th class="ta-r">Amount</th>
          <th>Status</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <template v-if="loading">
          <tr v-for="n in 5" :key="n"><td colspan="6" style="padding:14px"><div class="b-shimmer" style="height:12px"></div></td></tr>
        </template>
        <tr v-else-if="!filtered.length">
          <td colspan="6" class="b-empty">{{ search ? 'No proforma invoices match your search' : 'No proforma invoices yet' }}</td>
        </tr>
        <tr v-else v-for="p in filtered" :key="p.name" class="clickable" @click="openView(p)">
          <td><span class="mono" style="font-size:12px;color:#3B5BDB">{{p.name}}</span></td>
          <td class="fw-600">{{p.customer_name||p.customer||'—'}}</td>
          <td class="c-muted" style="font-size:12.5px">{{p.posting_date||'—'}}</td>
          <td class="ta-r mono" style="font-weight:600;color:#2F9E44">₹{{fmtAmt(p.grand_total)}}</td>
          <td><span class="b-badge b-badge-orange">Draft / Proforma</span></td>
          <td style="text-align:center">
            <button @click.stop="confirmDel(p)" style="background:none;border:none;cursor:pointer;color:#C92A2A;padding:4px" v-html="icon('trash',13)"></button>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <!-- View / Convert drawer -->
  <Teleport to="body">
    <div v-if="viewOpen" style="position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40" @click.self="viewOpen=false"></div>
    <div :style="'position:fixed;top:0;right:0;bottom:0;width:520px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:transform .22s;transform:'+(viewOpen?'translateX(0)':'translateX(100%)')">
      <template v-if="viewDoc">
        <div style="display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#FFF9DB">
          <div>
            <div style="font-size:15px;font-weight:700;font-family:monospace;color:#1a1a2e">{{viewDoc.name}}</div>
            <div style="font-size:12px;color:#876800;margin-top:1px">Proforma Invoice · {{viewDoc.posting_date}}</div>
          </div>
          <button @click="viewOpen=false" style="background:none;border:none;cursor:pointer;padding:4px" v-html="icon('x',16)"></button>
        </div>
        <div style="flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:16px">
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;margin-bottom:3px">Customer</div><div style="font-weight:600">{{viewDoc.customer_name||viewDoc.customer}}</div></div>
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;margin-bottom:3px">Date</div><div>{{viewDoc.posting_date}}</div></div>
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;margin-bottom:3px">Grand Total</div><div style="font-weight:700;color:#2F9E44;font-family:monospace">₹{{fmtAmt(viewDoc.grand_total)}}</div></div>
            <div><div style="font-size:11px;color:#9ca3af;text-transform:uppercase;margin-bottom:3px">Remarks</div><div style="font-size:12.5px">{{viewDoc.remarks||'—'}}</div></div>
          </div>
          <div v-if="(viewDoc.items||[]).length">
            <div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em">Items</div>
            <table class="b-table" style="font-size:12px">
              <thead><tr><th>Item</th><th class="ta-r">Qty</th><th class="ta-r">Rate</th><th class="ta-r">Amount</th></tr></thead>
              <tbody>
                <tr v-for="it in viewDoc.items" :key="it.name||it.item_code">
                  <td>{{it.item_name||it.item_code}}</td>
                  <td class="ta-r">{{it.qty}}</td>
                  <td class="ta-r mono">₹{{fmtAmt(it.rate)}}</td>
                  <td class="ta-r mono fw-700">₹{{fmtAmt(it.amount)}}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div style="padding:14px 20px;border-top:1px solid #e5e7eb;display:flex;gap:8px;justify-content:flex-end">
          <button class="b-btn b-btn-ghost" @click="viewOpen=false">Close</button>
          <button class="b-btn" style="background:#FFF9DB;color:#E67700;border-color:#FFD43B" @click="printProforma">
            <span v-html="icon('print',13)" style="vertical-align:-1px;margin-right:4px"></span> Print
          </button>
          <button class="b-btn b-btn-primary" @click="convertToInvoice" :disabled="converting">
            {{converting ? 'Converting…' : '→ Convert to Invoice'}}
          </button>
        </div>
      </template>
    </div>

    <!-- New Proforma drawer -->
    <div v-if="newOpen" style="position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40" @click.self="newOpen=false"></div>
    <div :style="'position:fixed;top:0;right:0;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:transform .22s;transform:'+(newOpen?'translateX(0)':'translateX(100%)')">
      <div style="display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0">
        <span style="font-size:15px;font-weight:700">New Proforma Invoice</span>
        <button @click="newOpen=false" style="background:none;border:none;cursor:pointer;padding:4px" v-html="icon('x',16)"></button>
      </div>
      <div style="flex:1;overflow-y:auto;padding:20px;display:grid;gap:14px;align-content:start">
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="nim-field" style="grid-column:1/-1">
            <label class="nim-label">Customer <span style="color:#c92a2a">*</span></label>
            <input class="nim-input" v-model="form.customer" placeholder="Customer ID" @input="onCustInput"/>
            <div v-if="custSugg.length" style="position:relative">
              <div style="position:absolute;top:2px;left:0;right:0;background:#fff;border:1px solid #E2E8F0;border-radius:6px;box-shadow:0 4px 12px rgba(0,0,0,.1);z-index:100;max-height:180px;overflow-y:auto">
                <div v-for="s in custSugg" :key="s.name" @click="pickCust(s)"
                  style="padding:8px 12px;cursor:pointer;font-size:13px;border-bottom:1px solid #F8F9FA"
                  onmouseover="this.style.background='#F8F9FA'" onmouseout="this.style.background=''">
                  {{s.customer_name||s.name}}
                </div>
              </div>
            </div>
          </div>
          <div class="nim-field">
            <label class="nim-label">Date <span style="color:#c92a2a">*</span></label>
            <input class="nim-input" type="date" v-model="form.posting_date"/>
          </div>
          <div class="nim-field">
            <label class="nim-label">Valid Until</label>
            <input class="nim-input" type="date" v-model="form.due_date"/>
          </div>
        </div>
        <div class="nim-field">
          <label class="nim-label">Remarks</label>
          <input class="nim-input" v-model="form.remarks" placeholder="e.g. Proforma Invoice for advance payment"/>
        </div>

        <!-- Items -->
        <div>
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
            <label class="nim-label" style="margin:0">Items <span style="color:#c92a2a">*</span></label>
            <button class="b-btn b-btn-ghost" style="padding:4px 10px;font-size:12px" @click="addItem">
              <span v-html="icon('plus',11)" style="vertical-align:-1px;margin-right:3px"></span> Add Item
            </button>
          </div>
          <div v-for="(it,i) in form.items" :key="i" style="display:grid;grid-template-columns:2fr 70px 90px 28px;gap:8px;margin-bottom:8px;align-items:center">
            <input class="nim-input" v-model="it.item_code" placeholder="Item code" style="font-size:12px" @change="onItemChange(it)"/>
            <input class="nim-input" type="number" v-model="it.qty" placeholder="Qty" min="0.01" style="font-size:12px" @input="calcAmount(it)"/>
            <input class="nim-input" type="number" v-model="it.rate" placeholder="Rate" min="0" style="font-size:12px" @input="calcAmount(it)"/>
            <button @click="removeItem(i)" style="background:none;border:none;cursor:pointer;color:#C92A2A;padding:2px" v-html="icon('trash',12)"></button>
          </div>
          <div style="text-align:right;font-size:13px;font-weight:700;color:#2F9E44;margin-top:8px;font-family:monospace">
            Total: ₹{{fmtAmt(itemTotal)}}
          </div>
        </div>
      </div>
      <div style="padding:14px 20px;border-top:1px solid #e5e7eb;display:flex;gap:8px;justify-content:flex-end">
        <button class="b-btn b-btn-ghost" @click="newOpen=false">Cancel</button>
        <button class="b-btn b-btn-primary" @click="saveProforma" :disabled="saving">{{saving?'Saving…':'Save Proforma'}}</button>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="showDel" style="position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:1000;display:flex;align-items:center;justify-content:center" @click.self="showDel=false">
      <div class="b-card b-card-body" style="max-width:400px;width:90%">
        <div style="font-size:15px;font-weight:700;margin-bottom:8px;color:#C92A2A">Delete Proforma?</div>
        <div style="font-size:13px;color:#374151;margin-bottom:20px">Delete <strong>{{delTarget?.name}}</strong>? This cannot be undone.</div>
        <div style="display:flex;gap:8px;justify-content:flex-end">
          <button class="b-btn b-btn-ghost" @click="showDel=false">Cancel</button>
          <button class="b-btn" style="background:#C92A2A;color:#fff;border-color:#C92A2A" @click="doDelete">Delete</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed } from "vue";
import { useRouter } from "vue-router";
import { apiList, apiGET, apiSave, apiDelete, apiSubmit, apiLinkValues, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";

const { toast } = useToast();
const router = useRouter();

const list      = ref([]);
const loading   = ref(false);
const search    = ref("");
const viewOpen  = ref(false);
const viewDoc   = ref(null);
const newOpen   = ref(false);
const saving    = ref(false);
const converting = ref(false);
const showDel   = ref(false);
const delTarget = ref(null);
const custSugg  = ref([]);
let custTimer   = null;

const form = reactive({
  customer: "", posting_date: new Date().toISOString().slice(0,10),
  due_date: "", remarks: "Proforma Invoice", items: [],
});

const fmtAmt = (v) => Number(v||0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

const itemTotal = computed(() => form.items.reduce((s,it) => s + (parseFloat(it.amount)||0), 0));

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return list.value;
  return list.value.filter(p =>
    (p.name||"").toLowerCase().includes(q) ||
    (p.customer_name||"").toLowerCase().includes(q)
  );
});

async function load() {
  loading.value = true;
  try {
    // Proforma invoices = draft Sales Invoices with remarks containing 'Proforma'
    list.value = await apiList("Sales Invoice", {
      fields: ["name","customer","customer_name","posting_date","grand_total","remarks","docstatus"],
      filters: [["docstatus","=",0],["remarks","like","%Proforma%"]],
      limit: 200,
    });
  } catch (e) {
    console.warn("Proforma load failed:", e.message);
    list.value = [];
  } finally { loading.value = false; }
}

async function openView(p) {
  viewOpen.value = true;
  try { viewDoc.value = await apiGET("Sales Invoice", p.name); }
  catch { viewDoc.value = p; }
}

function printProforma() {
  if (!viewDoc.value) return;
  window.open(`/printview?doctype=Sales%20Invoice&name=${viewDoc.value.name}&format=Standard&no_letterhead=0`, "_blank");
}

async function convertToInvoice() {
  if (!viewDoc.value) return;
  converting.value = true;
  try {
    await apiSubmit("Sales Invoice", viewDoc.value.name);
    toast.success(`Invoice ${viewDoc.value.name} finalized`);
    viewOpen.value = false;
    router.push("/invoices");
  } catch (e) { toast.error(e.message || "Conversion failed"); }
  finally { converting.value = false; }
}

function openNew() {
  Object.assign(form, { customer:"", posting_date: new Date().toISOString().slice(0,10), due_date:"", remarks:"Proforma Invoice", items:[] });
  custSugg.value = [];
  addItem();
  newOpen.value = true;
}

function addItem() { form.items.push({ item_code:"", qty:1, rate:0, amount:0 }); }
function removeItem(i) { form.items.splice(i, 1); }
function calcAmount(it) { it.amount = (parseFloat(it.qty)||0) * (parseFloat(it.rate)||0); }
async function onItemChange(it) {
  if (!it.item_code) return;
  try {
    const doc = await apiGET("Item", it.item_code);
    if (doc?.standard_rate) { it.rate = doc.standard_rate; calcAmount(it); }
  } catch {}
}

function onCustInput() {
  clearTimeout(custTimer);
  const txt = form.customer.trim();
  if (txt.length < 2) { custSugg.value = []; return; }
  custTimer = setTimeout(async () => {
    try { custSugg.value = await apiLinkValues("Customer", txt); } catch { custSugg.value = []; }
  }, 250);
}
function pickCust(s) { form.customer = s.name; custSugg.value = []; }

async function saveProforma() {
  if (!form.customer.trim()) { toast.error("Customer is required"); return; }
  if (!form.items.length || !form.items[0].item_code) { toast.error("Add at least one item"); return; }
  saving.value = true;
  try {
    const company = await resolveCompany();
    const doc = {
      doctype: "Sales Invoice",
      customer: form.customer,
      posting_date: form.posting_date,
      due_date: form.due_date || form.posting_date,
      company,
      remarks: form.remarks || "Proforma Invoice",
      items: form.items.filter(it => it.item_code.trim()).map(it => ({
        doctype: "Sales Invoice Item",
        item_code: it.item_code,
        item_name: it.item_code,
        description: it.item_code,
        qty: parseFloat(it.qty) || 1,
        rate: parseFloat(it.rate) || 0,
        amount: parseFloat(it.amount) || 0,
      })),
    };
    const saved = await apiSave(doc);
    toast.success(`Proforma ${saved.name} saved`);
    newOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save"); }
  finally { saving.value = false; }
}

function confirmDel(p) { delTarget.value = p; showDel.value = true; }
async function doDelete() {
  try {
    await apiDelete("Sales Invoice", delTarget.value.name);
    toast.success("Deleted");
    showDel.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

import { onMounted } from "vue";
onMounted(load);
</script>
