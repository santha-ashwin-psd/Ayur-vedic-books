<template>
<div class="b-page">
  <!-- Toolbar -->
  <div class="b-action-bar" style="flex-wrap:wrap;gap:8px">
    <div style="display:flex;align-items:center;gap:6px;background:#fff;border:1px solid #E2E8F0;border-radius:20px;padding:5px 14px;flex:1;max-width:280px">
      <span v-html="icon('search',13)" style="color:#868E96;flex-shrink:0"></span>
      <input v-model="search" placeholder="Search items..." style="border:none;outline:none;font-size:13px;width:100%;background:transparent;font-family:inherit"/>
    </div>
    <div class="b-filter-row" style="gap:4px">
      <button v-for="t in [{k:'all',l:'All'},{k:'active',l:'Active'},{k:'inactive',l:'Inactive'},{k:'services',l:'Services'},{k:'stock',l:'Stock Items'}]" :key="t.k"
        class="b-pill" :class="{active:filterTab===t.k}" @click="filterTab=t.k">{{t.l}}
      </button>
    </div>
    <div class="it-group-filter-wrap">
      <select class="it-group-filter-select" v-model="filterGroup">
        <option value="">All Groups</option>
        <option v-for="g in itemGroupsFull.filter(g => !g.is_group)" :key="g.name" :value="g.name">{{ g.name }}</option>
      </select>
    </div>
    <div style="display:flex;gap:6px;margin-left:auto">
      <button class="b-btn b-btn-ghost view-toggle-btn" @click="viewMode=viewMode==='table'?'grid':'table'" style="padding:7px 10px">
        <span v-html="icon(viewMode==='table'?'grid':'file',14)"></span>
      </button>
      <button class="b-btn b-btn-ghost" @click="load"><span v-html="icon('refresh',13)"></span></button>
      <button class="b-btn b-btn-ghost" @click="exportCSV" :disabled="!filtered.length"><span v-html="icon('download',13)"></span> Export</button>
      <button class="b-btn b-btn-primary" @click="openAdd"><span v-html="icon('plus',13)"></span> New Item</button>
    </div>
  </div>

  <!-- Table view -->
  <template v-if="viewMode==='table'">
    <div class="b-card items-tbl-wrap" style="padding:0;overflow:hidden">
      <table class="b-table">
        <thead><tr><th>Item Code</th><th>Name</th><th>Group</th><th>Type</th><th>UOM</th><th class="ta-r">Rate (₹)</th><th class="ta-r">GST %</th><th>Status</th><th></th></tr></thead>
        <tbody>
          <template v-if="loading"><tr v-for="n in 6" :key="n"><td colspan="9" style="padding:14px"><div class="b-shimmer" style="height:12px"></div></td></tr></template>
          <tr v-else-if="!filtered.length"><td colspan="9" class="b-empty">No items found</td></tr>
          <tr v-else v-for="row in filtered" :key="row.name" class="clickable" @click="openEdit(row)">
            <td><span  style="font-size:12px;color:#3B5BDB">{{row.item_code||row.name}}</span></td>
            <td class="fw-600">{{row.item_name}}</td>
            <td><span v-if="row.item_group" class="it-group-badge">{{row.item_group}}</span><span v-else class="c-muted">—</span></td>
            <td><span class="b-badge b-badge-muted" style="font-size:11px">{{row.item_type||'—'}}</span></td>
            <td class="c-muted" style="font-size:12.5px">{{row.stock_uom||'Nos'}}</td>
            <td class="ta-r fw-600">{{fmt(row.standard_rate)}}</td>
            <td class="ta-r c-muted" style="font-size:12.5px">{{row.gst_rate||0}}%</td>
            <td><span class="b-badge" :class="row.disabled?'b-badge-red':'b-badge-green'">{{row.disabled?'Inactive':'Active'}}</span></td>
            <td style="text-align:center">
              <button @click.stop="confirmDel(row)" style="background:none;border:none;cursor:pointer;color:#C92A2A;padding:4px" v-html="icon('trash',13)"></button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </template>

  <!-- Grid view -->
  <template v-else>
    <div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:14px">
      <div v-if="loading" v-for="n in 6" :key="n" class="b-shimmer" style="height:120px;border-radius:10px"></div>
      <div v-else-if="!filtered.length" style="grid-column:1/-1;text-align:center;padding:40px;color:#868E96">No items found</div>
      <div v-else v-for="row in filtered" :key="row.name" class="b-card b-card-body" style="cursor:pointer;transition:box-shadow .15s" @click="openEdit(row)">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:8px">
          <span class="b-badge" :class="row.disabled?'b-badge-red':'b-badge-green'" style="font-size:10.5px">{{row.disabled?'Inactive':'Active'}}</span>
          <span class="b-badge b-badge-muted" style="font-size:10.5px">{{row.item_type||'—'}}</span>
        </div>
        <div class="fw-700" style="font-size:14px;margin-bottom:3px;line-height:1.3">{{row.item_name}}</div>
        <div class="c-muted" style="font-size:11px;margin-bottom:8px">{{row.item_code}}</div>
        <div style="display:flex;justify-content:space-between;align-items:center">
          <span v-if="row.item_group" class="it-group-badge" style="font-size:11px">{{row.item_group}}</span>
          <span v-else class="c-muted" style="font-size:12px">—</span>
          <span class="fw-700" style="font-size:13px;color:#2F9E44">{{fmt(row.standard_rate)}}</span>
        </div>
      </div>
    </div>
  </template>

  <!-- Delete confirm -->
  <Teleport to="body">
    <div v-if="showDel" style="position:fixed;inset:0;background:rgba(0,0,0,.45);z-index:1000;display:flex;align-items:center;justify-content:center" @click.self="showDel=false">
      <div class="b-card b-card-body" style="max-width:400px;width:90%">
        <div style="font-size:15px;font-weight:700;margin-bottom:8px;color:#C92A2A">Delete Item?</div>
        <div style="font-size:13px;color:#374151;margin-bottom:20px">Delete <strong>{{delTarget?.item_name}}</strong>? This cannot be undone.</div>
        <div style="display:flex;gap:8px;justify-content:flex-end">
          <button class="b-btn b-btn-ghost" @click="showDel=false">Cancel</button>
          <button class="b-btn" style="background:#C92A2A;color:#fff;border-color:#C92A2A" :disabled="deleting" @click="doDelete">{{deleting?'Deleting…':'Yes, Delete'}}</button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- Detail Drawer -->
  <Teleport to="body">
    <div v-if="showDrawer" style="position:fixed;inset:0;background:rgba(0,0,0,.4);z-index:900;display:flex;justify-content:flex-end" @click.self="showDrawer=false">
      <div style="width:100%;max-width:540px;height:100%;background:#fff;display:flex;flex-direction:column;box-shadow:-4px 0 24px rgba(0,0,0,.15);animation:slideInR .2s ease">
        <div style="padding:18px 22px;border-bottom:1px solid #E2E8F0;display:flex;align-items:center;justify-content:space-between;background:linear-gradient(135deg,#1a1d23,#2d3748)">
          <div>
            <div style="font-size:15px;font-weight:700;color:#fff">{{drawerMode==='add'?'New Item':'Edit Item'}}</div>
            <div style="font-size:12px;color:rgba(255,255,255,.6);margin-top:2px">{{drawerMode==='edit'?form.item_code:'Fill in item details'}}</div>
          </div>
          <button @click="showDrawer=false" style="background:rgba(255,255,255,.12);border:none;cursor:pointer;color:#fff;width:30px;height:30px;border-radius:6px;display:flex;align-items:center;justify-content:center" v-html="icon('x',16)"></button>
        </div>

        <div style="display:flex;padding:10px 16px;gap:6px;background:#F8FAFC;border-bottom:1px solid #E2E8F0;overflow-x:auto">
          <button v-for="t in [{k:'basic',l:'Basic Info'},{k:'pricing',l:'Pricing & Tax'},{k:'inventory',l:'Inventory'},{k:'variants',l:'Variants'}]" :key="t.k"
            @click="drawerTab=t.k"
            style="padding:5px 12px;border-radius:16px;border:1.5px solid;font-size:12px;font-weight:600;cursor:pointer;white-space:nowrap;transition:all .12s"
            :style="drawerTab===t.k?{background:'#1a1d23',color:'#fff',borderColor:'#1a1d23'}:{background:'#fff',color:'#495057',borderColor:'#E2E8F0'}">
            {{t.l}}
          </button>
        </div>

        <div style="flex:1;overflow-y:auto;padding:20px 22px">
          <template v-if="drawerTab==='basic'">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
              <div><label class="nim-label">Item Name <span style="color:#C92A2A">*</span></label><input class="nim-input" v-model="form.item_name" placeholder="e.g. Laptop 15-inch"/></div>
              <div><label class="nim-label">Item Code</label><input class="nim-input" v-model="form.item_code" placeholder="Auto-generated if blank"/></div>
            </div>
            <div style="margin-bottom:12px">
              <label class="nim-label">Item Group</label>
              <SearchableSelect
                v-model="form.item_group"
                :options="leafGroupOptions"
                placeholder="Search or create a group…"
                :createable="true"
                @create="createItemGroup"
              />
            </div>
            <div style="margin-bottom:12px">
              <label class="nim-label">Item Type</label>
              <div class="it-type-pills">
                <button v-for="t in ITEM_TYPES" :key="t" type="button"
                  class="it-type-pill" :class="{ 'it-type-pill--active': form.item_type === t }"
                  @click="form.item_type = t">
                  <span>{{ ITEM_TYPE_ICONS[t] }}</span>
                  <span>{{ t }}</span>
                </button>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
              <div><label class="nim-label">Default UOM</label>
                <select class="nim-input" v-model="form.stock_uom">
                  <option value="">— Select UOM —</option>
                  <option v-for="u in uomList" :key="u" :value="u">{{u}}</option>
                </select>
              </div>
              <div><label class="nim-label">HSN / SAC Code</label><input class="nim-input" v-model="form.hsn_code" placeholder="e.g. 847130"/></div>
            </div>
            <div style="margin-bottom:12px"><label class="nim-label">Description</label><textarea class="nim-input" v-model="form.description" rows="3" placeholder="Item description..." style="resize:vertical"></textarea></div>
            <div style="display:flex;align-items:center;gap:10px;padding:12px;background:#F8FAFC;border-radius:8px;border:1px solid #E2E8F0">
              <input type="checkbox" :checked="!!form.disabled" @change="form.disabled=($event.target.checked?1:0)" style="width:16px;height:16px;accent-color:#C92A2A"/>
              <div><div style="font-size:13px;font-weight:600;color:#374151">Mark as Inactive</div><div style="font-size:11.5px;color:#868E96">Inactive items won't appear in transaction dropdowns</div></div>
            </div>
          </template>

          <template v-else-if="drawerTab==='pricing'">
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
              <div><label class="nim-label">Selling Rate (₹)</label><input type="number" class="nim-input" v-model="form.standard_rate" min="0" /></div>
              <div><label class="nim-label">Buying Rate (₹)</label><input type="number" class="nim-input" v-model="form.standard_buying_rate" min="0" /></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
              <div><label class="nim-label">GST Rate (%)</label>
                <select class="nim-input" v-model.number="form.gst_rate">
                  <option v-for="r in [0,5,12,18,28]" :key="r" :value="r">{{r}}%</option>
                </select>
              </div>
              <div>
                <label class="nim-label">Tax Template</label>
                <select class="nim-input" v-model="form.tax_code">
                  <option value="">— Select —</option>
                  <option v-for="t in taxTemplates" :key="t.name" :value="t.name">{{ t.label }}</option>
                </select>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
              <div><label class="nim-label">Income Account</label><SearchableSelect v-model="form.income_account" :options="accountsList" placeholder="Select income account…" :createable="true" createDoctype="Account" @create="reloadAccounts"/></div>
              <div><label class="nim-label">Expense Account</label><SearchableSelect v-model="form.expense_account" :options="accountsList" placeholder="Select expense account…" :createable="true" createDoctype="Account" @create="reloadAccounts"/></div>
            </div>
          </template>

          <template v-else-if="drawerTab==='inventory'">
            <div style="display:flex;align-items:center;gap:10px;padding:12px;background:#F8FAFC;border-radius:8px;border:1px solid #E2E8F0;margin-bottom:16px">
              <input type="checkbox" :checked="!!form.is_stock_item" @change="form.is_stock_item=($event.target.checked?1:0)" style="width:16px;height:16px;accent-color:#2F9E44"/>
              <div><div style="font-size:13px;font-weight:600;color:#374151">Track Inventory</div><div style="font-size:11.5px;color:#868E96">Maintain stock levels and ledger for this item</div></div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
              <div><label class="nim-label">Valuation Method</label>
                <select class="nim-input" v-model="form.valuation_method">
                  <option v-for="m in VAL_METHODS" :key="m" :value="m">{{m}}</option>
                </select>
              </div>
              <div><label class="nim-label">Default Warehouse</label>
                <SearchableSelect v-model="form.default_warehouse" :options="warehouses" value-key="name" label-key="label" placeholder="Select warehouse…"/>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
              <div><label class="nim-label">Reorder Level</label><input type="number" class="nim-input" v-model="form.reorder_level" min="0" /></div>
              <div><label class="nim-label">Reorder Qty</label><input type="number" class="nim-input" v-model="form.reorder_qty" min="0"/></div>
            </div>
            <div style="background:#eff6ff;border:1px solid #bfdbfe;border-radius:8px;padding:10px 14px;font-size:12px;color:#1e40af;margin-top:4px">
              To set or adjust stock quantities, go to <strong>Inventory → Warehouses</strong> → select a warehouse → click <strong>Adjust</strong> next to any item.
            </div>
          </template>

          <template v-else>
            <div style="text-align:center;padding:40px 20px;color:#868E96">
              <div style="font-size:32px;margin-bottom:12px">🧩</div>
              <div style="font-size:14px;font-weight:600;margin-bottom:4px">Item Variants</div>
              <div style="font-size:13px">Configure attributes like Size, Colour etc. to create item variants.</div>
              <div style="font-size:12px;margin-top:8px;color:#ADB5BD">Coming soon</div>
            </div>
          </template>
        </div>

        <div style="padding:14px 22px;border-top:1px solid #E2E8F0;display:flex;justify-content:flex-end;gap:8px;background:#FAFAFA">
          <button class="b-btn b-btn-ghost" @click="showDrawer=false">Cancel</button>
          <button class="b-btn b-btn-primary" :disabled="saving" @click="saveItem">{{saving?'Saving…':(drawerMode==='edit'?'Update Item':'Create Item')}}</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from "vue";
import { apiList, apiGET, apiPOST, apiSave, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { fmt, fmtDate, flt } from "../utils/format.js";
import { icon } from "../utils/icons.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();

const list       = ref([]);
const loading    = ref(true);
const search     = ref("");
const filterTab  = ref("all");
const viewMode   = ref(window.innerWidth <= 480 ? "grid" : "table");
const showDrawer = ref(false);
const drawerMode = ref("add");
const saving     = ref(false);
const deleting   = ref(false);
const showDel    = ref(false);
const delTarget  = ref(null);
const drawerTab  = ref("basic");
const itemGroups    = ref([]);
const itemGroupsFull = ref([]);
const filterGroup   = ref("");
const warehouses    = ref([]);
const taxTemplates  = ref([]);
const uomList       = ref([]);
const defaultAccounts = ref({ income: "", expense: "" });
const accountsList    = ref([]);

const form = reactive({
  name: "", item_code: "", item_name: "", item_group: "", item_type: "Product",
  stock_uom: "Nos", hsn_code: "", description: "", disabled: 0,
  standard_rate: 0, standard_buying_rate: 0, gst_rate: 18, tax_code: "",
  income_account: "", expense_account: "",
  is_stock_item: 1, valuation_method: "FIFO", default_warehouse: "",
  reorder_level: 0, reorder_qty: 0, opening_stock: 0,
});

const ITEM_TYPES      = ["Product", "Service", "Raw Material", "Finished Good"];
const ITEM_TYPE_ICONS = { Product: "📦", Service: "🛠️", "Raw Material": "⚙️", "Finished Good": "✅" };
const VAL_METHODS     = ["FIFO", "Moving Average", "LIFO"];

const leafGroupOptions = computed(() =>
  itemGroupsFull.value.filter(g => !g.is_group).map(g => ({ value: g.name, label: g.name }))
);

async function load() {
  loading.value = true;
  try {
    const rows = await apiList("Item", {
      fields: ["name","item_code","item_name","item_group","item_type","stock_uom","standard_rate","gst_rate","disabled","is_stock_item"],
      order: "item_name asc", limit: 500,
    });
    list.value = rows || [];
  } catch { list.value = []; }
  try {
    const g = await apiList("Item Group", { fields: ["name", "is_group"], order: "name asc", limit: 200 });
    itemGroupsFull.value = g || [];
    itemGroups.value = (g || []).map((r) => r.name);
  } catch { itemGroups.value = ["All Item Groups", "Products", "Services", "Raw Materials", "Finished Goods", "Furniture"]; }
  try {
    const wh = await apiList("Warehouse", {
      fields: ["name", "warehouse_name", "warehouse_type"],
      filters: [["disabled", "=", 0]], order: "warehouse_name asc", limit: 200,
    });
    warehouses.value = (wh || []).map((r) => ({
      name: r.name,
      label: (r.warehouse_name || r.name) + (r.warehouse_type ? " (" + r.warehouse_type + ")" : ""),
    }));
  } catch { warehouses.value = []; }
  try {
    const tt = await apiList("Tax Template", {
      fields: ["name", "template_name"],
      filters: [["disabled", "=", 0]],
      order: "template_name asc", limit: 100,
    });
    taxTemplates.value = (tt || []).map((r) => ({ name: r.name, label: r.template_name || r.name }));
  } catch { taxTemplates.value = []; }
  try {
    const uoms = await apiList("UOM", { fields: ["name"], order: "name asc", limit: 200 });
    uomList.value = (uoms || []).map((r) => r.name);
  } catch { uomList.value = ["Nos", "Kg", "Ltr", "Mtr", "Box", "Pcs", "Set", "Dozen"]; }
  try {
    const company = await resolveCompany();
    // Load full account list for dropdowns
    const allAccts = await apiList("Account", {
      fields: ["name"], filters: [["is_group","=",0],["company","=",company]], order: "name asc", limit: 500,
    });
    accountsList.value = (allAccts || []).map((a) => ({ value: a.name, label: a.name }));
    // Determine defaults
    try {
      const accts = await apiGET("zoho_books_clone.api.docs.get_accounts", { company });
      const incomeAcc = (accts.income || [])[0]?.name || "";
      const expenseAccs = await apiList("Account", {
        fields: ["name"],
        filters: [["account_type", "in", ["Expense", "Cost of Goods Sold"]], ["is_group", "=", 0], ["company", "=", company]],
        order: "name asc", limit: 10,
      });
      const expenseAcc = (expenseAccs || [])[0]?.name || "";
      defaultAccounts.value = { income: incomeAcc, expense: expenseAcc };
    } catch { defaultAccounts.value = { income: "", expense: "" }; }
  } catch { defaultAccounts.value = { income: "", expense: "" }; accountsList.value = []; }
  loading.value = false;
}

async function reloadGroups() {
  try {
    const g = await apiList("Item Group", { fields: ["name", "is_group"], order: "name asc", limit: 200 });
    itemGroupsFull.value = g || [];
    itemGroups.value = (g || []).map(r => r.name);
  } catch {}
}

async function createItemGroup(name) {
  if (!name?.trim()) return;
  try {
    await apiSave({ doctype: "Item Group", name: name.trim(), parent_item_group: "All Item Groups", is_group: 0 });
    await reloadGroups();
    form.item_group = name.trim();
    toast("Group \"" + name.trim() + "\" created");
  } catch (e) { toast("Could not create group: " + e.message, "error"); }
}

async function reloadAccounts() {
  try {
    const company = await resolveCompany();
    const allAccts = await apiList("Account", {
      fields: ["name"], filters: [["is_group","=",0],["company","=",company]], order: "name asc", limit: 500,
    });
    accountsList.value = (allAccts || []).map((a) => ({ value: a.name, label: a.name }));
  } catch {}
}

const filtered = computed(() => {
  let r = list.value;
  if (filterTab.value === "active")   r = r.filter((i) => !i.disabled);
  if (filterTab.value === "inactive") r = r.filter((i) =>  i.disabled);
  if (filterTab.value === "services") r = r.filter((i) => !i.is_stock_item);
  if (filterTab.value === "stock")    r = r.filter((i) =>  i.is_stock_item);
  if (filterGroup.value) r = r.filter((i) => i.item_group === filterGroup.value);
  const q = search.value.toLowerCase().trim();
  if (q) r = r.filter((i) => ((i.item_name || "") + (i.item_code || "") + (i.item_group || "")).toLowerCase().includes(q));
  return r;
});

function exportCSV() {
  const rows = filtered.value;
  if (!rows.length) return;
  const esc = v => { const s = v==null?"":String(v); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; };
  const lines = [["Item Code","Item Name","Group","Type","UOM","Sales Rate","GST %","Stock Item","Status"].join(",")];
  for (const i of rows) {
    lines.push([i.item_code||"",i.item_name||"",i.item_group||"",i.item_type||"",i.stock_uom||"",flt(i.standard_rate),flt(i.gst_rate),i.is_stock_item?"Yes":"No",i.disabled?"Inactive":"Active"].map(esc).join(","));
  }
  const blob = new Blob(["﻿"+lines.join("\r\n")], {type:"text/csv;charset=utf-8;"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `items_${new Date().toISOString().slice(0,10)}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast(`Exported ${rows.length} item(s)`);
}

function openAdd() {
  drawerMode.value = "add"; drawerTab.value = "basic";
  Object.assign(form, {
    name: "", item_code: "", item_name: "", item_group: "", item_type: "Product",
    stock_uom: "Nos", hsn_code: "", description: "", disabled: 0,
    standard_rate: 0, standard_buying_rate: 0, gst_rate: 18, tax_code: "",
    income_account:  defaultAccounts.value.income,
    expense_account: defaultAccounts.value.expense,
    is_stock_item: 1, valuation_method: "FIFO", default_warehouse: "",
    reorder_level: 0, reorder_qty: 0, opening_stock: 0,
  });
  showDrawer.value = true;
}

async function openEdit(row) {
  drawerMode.value = "edit"; drawerTab.value = "basic";
  Object.assign(form, {
    ...row,
    hsn_code: "", description: "", standard_buying_rate: 0,
    tax_code: "", income_account: "", expense_account: "",
    valuation_method: "FIFO", default_warehouse: "",
    reorder_level: 0, reorder_qty: 0, opening_stock: 0,
  });
  showDrawer.value = true;
  try {
    const full = await apiGET("zoho_books_clone.api.docs.get_doc", { doctype: "Item", name: row.name });
    Object.assign(form, {
      hsn_code:             full.hsn_code             || "",
      description:          full.description          || "",
      standard_rate:        flt(full.standard_rate),
      standard_buying_rate: flt(full.standard_buying_rate),
      gst_rate:             flt(full.gst_rate) || 18,
      tax_code:             full.tax_code             || "",
      income_account:       full.income_account       || defaultAccounts.value.income,
      expense_account:      full.expense_account      || defaultAccounts.value.expense,
      is_stock_item:        full.is_stock_item ? 1 : 0,
      valuation_method:     full.valuation_method     || "FIFO",
      default_warehouse:    full.default_warehouse    || "",
      reorder_level:        flt(full.reorder_level),
      reorder_qty:          flt(full.reorder_qty),
      opening_stock:        flt(full.opening_stock),
      disabled:             full.disabled ? 1 : 0,
    });
  } catch (e) { toast("Could not load full item details: " + e.message, "error"); }
}

async function saveItem() {
  if (!form.item_name.trim()) { toast("Item name is required", "error"); return; }
  saving.value = true;
  try {
    const isEdit = drawerMode.value === "edit";
    const itemCode = form.item_code || form.item_name;
    const openingQty = flt(form.opening_stock);
    const openingRate = flt(form.standard_buying_rate) || flt(form.standard_rate) || 0;

    const doc = {
      doctype: "Item", item_name: form.item_name, item_code: itemCode,
      item_group: form.item_group || "Products", item_type: form.item_type, stock_uom: form.stock_uom,
      hsn_code: form.hsn_code, description: form.description, disabled: form.disabled ? 1 : 0,
      standard_rate: flt(form.standard_rate), standard_buying_rate: flt(form.standard_buying_rate),
      gst_rate: flt(form.gst_rate), tax_code: form.tax_code,
      income_account: form.income_account, expense_account: form.expense_account,
      is_stock_item: form.is_stock_item ? 1 : 0, valuation_method: form.valuation_method,
      default_warehouse: form.default_warehouse, reorder_level: flt(form.reorder_level),
      reorder_qty: flt(form.reorder_qty), opening_stock: openingQty,
    };
    if (isEdit) doc.name = form.name;
    const saved = await apiSave(doc);
    const savedName = saved?.name || form.name || itemCode;

    // Opening stock is posted only when the item is first created — re-posting
    // on every edit would keep adding a Material Receipt and inflate inventory.
    if (!isEdit && form.is_stock_item && openingQty > 0 && form.default_warehouse) {
      try {
        const res = await apiPOST("zoho_books_clone.api.inventory.create_opening_stock", {
          item_code: savedName,
          item_name: form.item_name,
          warehouse: form.default_warehouse,
          qty: openingQty,
          rate: openingRate,
        });
        toast("Stock entry " + res.stock_entry + " created: +" + openingQty + " in " + form.default_warehouse);
      } catch (seErr) {
        toast("Item saved but stock entry failed: " + seErr.message, "error");
      }
    }

    await load();
    toast(isEdit ? "Item updated" : "Item created");
    showDrawer.value = false;
  } catch (e) { toast("Save failed: " + e.message, "error"); }
  finally { saving.value = false; }
}

function confirmDel(row) { delTarget.value = row; showDel.value = true; }

async function doDelete() {
  deleting.value = true;
  try {
    await apiDelete("Item", delTarget.value.name);
    list.value = list.value.filter((i) => i.name !== delTarget.value.name);
    toast("Item deleted");
    showDel.value = false;
  } catch (e) { toast("Delete failed: " + e.message, "error"); }
  finally { deleting.value = false; }
}

function onHashChange() {
  const h = window.location.hash;
  if (h === "#/inventory/items" || h.startsWith("#/inventory/items?") || h.startsWith("#/inventory/items/")) {
    load();
  }
}

onMounted(() => { load(); window.addEventListener("hashchange", onHashChange); });
onUnmounted(() => { window.removeEventListener("hashchange", onHashChange); });
</script>

<style>
/* ── Group filter select ── */
.it-group-filter-wrap {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}
.it-group-filter-select {
  border: 1.5px solid #e2e8f0;
  border-radius: 8px;
  padding: 5px 10px;
  font-size: 12.5px;
  color: #374151;
  background: #fff;
  outline: none;
  cursor: pointer;
  transition: border-color .15s;
  max-width: 160px;
}
.it-group-filter-select:focus { border-color: #3b82f6; }

/* ── Item Type pill group ── */
.it-type-pills {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px;
  margin-top: 2px;
}
.it-type-pill {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 9px 12px;
  border: 1.5px solid #e2e8f0;
  border-radius: 9px;
  background: #f8fafc;
  font-size: 12.5px;
  font-weight: 600;
  color: #374151;
  cursor: pointer;
  transition: all .12s;
  text-align: left;
  font-family: inherit;
}
.it-type-pill:hover { background: #eff6ff; border-color: #93c5fd; color: #1d4ed8; }
.it-type-pill--active {
  background: #eff6ff;
  border-color: #2563eb;
  color: #1d4ed8;
  box-shadow: 0 0 0 2px rgba(37,99,235,.12);
}

/* ── Group badge ── */
.it-group-badge {
  display: inline-block;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 9px;
  border-radius: 8px;
  background: #ede9fe;
  color: #5b21b6;
  white-space: nowrap;
}

/* ── Responsive ── */
@media (max-width: 768px) {
  .items-tbl-wrap { overflow-x: auto !important; -webkit-overflow-scrolling: touch; }
  .items-tbl-wrap .b-table { min-width: 500px; }
  /* hide Group (3), UOM (5), GST% (7) */
  .items-tbl-wrap .b-table th:nth-child(3), .items-tbl-wrap .b-table td:nth-child(3),
  .items-tbl-wrap .b-table th:nth-child(5), .items-tbl-wrap .b-table td:nth-child(5),
  .items-tbl-wrap .b-table th:nth-child(7), .items-tbl-wrap .b-table td:nth-child(7) { display: none; }
  /* Toolbar: stack action row below filters */
  .b-action-bar { flex-direction: column !important; align-items: stretch !important; }
  .b-action-bar > div[style*="margin-left:auto"] { margin-left: 0 !important; display: flex; flex-wrap: wrap; gap: 6px; }
  .b-action-bar > div[style*="margin-left:auto"] .b-btn-primary { flex: 1; justify-content: center; }
  .b-filter-row { overflow-x: auto; -webkit-overflow-scrolling: touch; flex-wrap: nowrap !important; padding-bottom: 2px; }
}

@media (max-width: 480px) {
  .it-group-filter-wrap { display: none; }
  /* also hide Type (4) */
  .items-tbl-wrap .b-table th:nth-child(4), .items-tbl-wrap .b-table td:nth-child(4) { display: none; }
  .items-tbl-wrap .b-table { min-width: 360px; }
  /* Compact action buttons */
  .b-action-bar > div[style*="margin-left:auto"] .b-btn-ghost { flex: 0 0 auto; padding: 7px 10px !important; }
  /* Hide grid/list toggle — mobile always shows card view */
  .view-toggle-btn { display: none !important; }
}
</style>