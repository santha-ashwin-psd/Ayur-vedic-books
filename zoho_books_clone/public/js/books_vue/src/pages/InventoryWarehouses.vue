<template>
<div style="display:flex;height:calc(100vh - 56px);overflow:hidden">

  <!-- Left panel: tree -->
  <div style="width:340px;min-width:340px;border-right:1px solid #e4e8f0;display:flex;flex-direction:column;background:#fff">
    <div style="padding:16px 16px 12px;border-bottom:1px solid #f0f2f5">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div style="font-size:15px;font-weight:700;color:#1A1D23">Warehouses</div>
        <button class="nim-btn nim-btn-primary" style="padding:5px 12px;font-size:12px" @click="openAdd">
          <span v-html="icon('plus')"></span> New
        </button>
      </div>
      <div style="position:relative">
        <span v-html="icon('search')" style="position:absolute;left:9px;top:50%;transform:translateY(-50%);color:#9ca3af;pointer-events:none;width:14px"></span>
        <input v-model="search" placeholder="Search warehouses…"
          style="width:100%;border:1px solid #e4e8f0;border-radius:7px;padding:7px 10px 7px 30px;font-size:13px;outline:none;color:#1A1D23"/>
      </div>
    </div>
    <div style="flex:1;overflow-y:auto">
      <div v-if="loading" style="padding:20px 16px">
        <div class="b-shimmer" style="height:28px;border-radius:6px;margin-bottom:8px"></div>
        <div class="b-shimmer" style="height:28px;border-radius:6px;margin-bottom:8px;margin-left:20px"></div>
        <div class="b-shimmer" style="height:28px;border-radius:6px;margin-bottom:8px;margin-left:20px"></div>
        <div class="b-shimmer" style="height:28px;border-radius:6px;margin-left:40px"></div>
      </div>
      <div v-else-if="!treeNodes.length" style="padding:32px 16px;text-align:center;color:#868E96;font-size:13px">
        No warehouses found
      </div>
      <div v-else v-for="node in treeNodes" :key="node.name"
        @click="selectWarehouse(node)"
        :style="{
          paddingLeft: (14 + node.depth * 20) + 'px',
          paddingRight:'12px', paddingTop:'8px', paddingBottom:'8px',
          cursor:'pointer', display:'flex', alignItems:'center', gap:'6px',
          borderLeft: selectedWH && selectedWH.name===node.name ? '3px solid #2563eb' : '3px solid transparent',
          background: selectedWH && selectedWH.name===node.name ? '#F3F0FF' : 'transparent',
          transition:'background 0.12s',
        }">
        <span v-if="node.is_group" @click.stop="toggleExpand(node.name, $event)"
          style="width:14px;height:14px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:10px;color:#868E96;cursor:pointer">
          {{expanded.has(node.name)?'▼':'▶'}}
        </span>
        <span v-else style="width:14px;flex-shrink:0"></span>
        <span style="font-size:15px;flex-shrink:0">{{whMeta(node.warehouse_type).icon}}</span>
        <span style="font-size:13px;color:#1A1D23;font-weight:500;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">
          {{node.warehouse_name || node.name}}
        </span>
        <span v-if="node.is_group && childCount(node.name)"
          style="font-size:10px;background:#e4e8f0;color:#495057;border-radius:10px;padding:0 6px;flex-shrink:0">
          {{childCount(node.name)}}
        </span>
        <span v-if="node.disabled" style="font-size:10px;background:#FFF5F5;color:#C92A2A;border-radius:10px;padding:0 6px;flex-shrink:0">off</span>
      </div>
    </div>
  </div>

  <!-- Right panel: detail -->
  <div style="flex:1;overflow-y:auto;background:#f0f2f5">
    <div v-if="!selectedWH" style="display:flex;align-items:center;justify-content:center;height:100%">
      <div style="text-align:center;color:#868E96">
        <div style="font-size:48px;margin-bottom:12px">🏭</div>
        <div style="font-size:15px;font-weight:600;color:#343A40;margin-bottom:4px">Select a Warehouse</div>
        <div style="font-size:13px">Click a warehouse on the left to view its stock details</div>
      </div>
    </div>
    <div v-else style="padding:24px">

      <div style="display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:20px;flex-wrap:wrap;gap:12px">
        <div>
          <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
            <span style="font-size:22px">{{whMeta(selectedWH.warehouse_type).icon}}</span>
            <h1 style="font-size:20px;font-weight:700;color:#1A1D23;margin:0">{{selectedWH.warehouse_name || selectedWH.name}}</h1>
            <span :style="{background:whMeta(selectedWH.warehouse_type).bg,color:whMeta(selectedWH.warehouse_type).color,
              padding:'3px 10px',borderRadius:'20px',fontSize:'12px',fontWeight:'600'}">
              {{selectedWH.warehouse_type || 'Stores'}}
            </span>
            <span v-if="selectedWH.disabled" style="background:#FFF5F5;color:#C92A2A;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600">Disabled</span>
          </div>
          <span v-if="selectedWH.is_group" style="background:#eff6ff;color:#2563eb;padding:3px 10px;border-radius:20px;font-size:12px;font-weight:600;margin-left:4px">Group Warehouse</span>
          <div v-if="selectedWH.parent_warehouse" style="font-size:12.5px;color:#868E96;margin-top:4px">
            Parent: {{selectedWH.parent_warehouse}}
          </div>
          <div v-if="selectedWH.is_group" style="font-size:12px;color:#64748b;margin-top:4px">
            Totals aggregated from all child warehouses
          </div>
        </div>
        <div style="display:flex;gap:8px;flex-shrink:0">
          <button class="nim-btn nim-btn-ghost" @click="openEdit(selectedWH)"><span v-html="icon('edit')"></span> Edit</button>
          <button v-if="!selectedWH.is_group" class="nim-btn nim-btn-ghost" style="color:#1971C2;border-color:#1971C2" @click="openTransfer">
            <span v-html="icon('refresh')"></span> Transfer
          </button>
          <button class="nim-btn" style="background:#FFF5F5;color:#C92A2A;border-color:#FFC9C9" @click="confirmDel(selectedWH)">
            <span v-html="icon('trash')"></span>
          </button>
        </div>
      </div>

      <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:20px">
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 16px">
          <div style="font-size:11px;font-weight:600;color:#9CA3AF;letter-spacing:.04em;text-transform:uppercase;margin-bottom:6px">Stock Value</div>
          <div style="font-size:18px;font-weight:700;color:#2563eb;font-family:var(--mono,'JetBrains Mono',monospace)">{{fmt(whStats.value)}}</div>
        </div>
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 16px">
          <div style="font-size:11px;font-weight:600;color:#9CA3AF;letter-spacing:.04em;text-transform:uppercase;margin-bottom:6px">Items in Stock</div>
          <div style="font-size:18px;font-weight:700;color:#111827;font-family:var(--mono,'JetBrains Mono',monospace)">{{whStats.items}}</div>
        </div>
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 16px">
          <div style="font-size:11px;font-weight:600;color:#9CA3AF;letter-spacing:.04em;text-transform:uppercase;margin-bottom:6px">Reserved Qty</div>
          <div style="font-size:18px;font-weight:700;color:#E67700;font-family:var(--mono,'JetBrains Mono',monospace)">{{whStats.reserved.toFixed(2)}}</div>
        </div>
        <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 16px">
          <div style="font-size:11px;font-weight:600;color:#9CA3AF;letter-spacing:.04em;text-transform:uppercase;margin-bottom:6px">Projected Qty</div>
          <div style="font-size:18px;font-weight:700;color:#1971C2;font-family:var(--mono,'JetBrains Mono',monospace)">{{whStats.projected.toFixed(2)}}</div>
        </div>
      </div>

      <div class="cust-table-card">
        <div style="padding:14px 16px 10px;border-bottom:1px solid #f0f2f5;display:flex;justify-content:space-between;align-items:center">
          <div style="font-size:14px;font-weight:600;color:#1A1D23">Stock Items</div>
          <button class="nim-btn nim-btn-ghost" style="font-size:12px;padding:4px 10px" @click="loadStockForWarehouse(selectedWH.name)">
            <span v-html="icon('refresh')"></span> Refresh
          </button>
        </div>
        <div v-if="stockLoading" style="padding:20px">
          <div class="b-shimmer" style="height:32px;border-radius:6px;margin-bottom:6px"></div>
          <div class="b-shimmer" style="height:32px;border-radius:6px;margin-bottom:6px"></div>
          <div class="b-shimmer" style="height:32px;border-radius:6px"></div>
        </div>
        <div v-else-if="!stockItems.length" style="padding:40px;text-align:center;color:#868E96;font-size:13px">
          <div style="font-size:32px;margin-bottom:8px">📦</div>
          <div style="font-weight:600;color:#343A40;margin-bottom:4px">No stock in this warehouse</div>
          <div>{{ selectedWH.is_group ? 'No stock in any child warehouse yet' : 'Stock will appear here once items are received' }}</div>
        </div>
        <div v-else class="cust-table-wrap">
          <table class="cust-table">
            <thead><tr>
              <th>Item Code</th><th>Item Name</th><th>Group</th><th>UOM</th>
              <th style="text-align:right">Actual Qty</th>
              <th style="text-align:right">Reserved</th>
              <th style="text-align:right">Val. Rate</th>
              <th style="text-align:right">Stock Value</th>
              <th style="text-align:center">Alert</th>
            </tr></thead>
            <tbody>
              <tr v-for="r in stockItems" :key="r.item_code" class="cust-row">
                <td style="font-family:var(--mono);font-size:12.5px;color:#5C7CFA">{{r.item_code}}</td>
                <td style="font-weight:500">{{r.item_name}}</td>
                <td style="font-size:12px;color:#868E96">{{r.item_group||'—'}}</td>
                <td style="font-size:12px;color:#868E96">{{r.uom||'Nos'}}</td>
                <td style="text-align:right;font-family:var(--mono);font-weight:600;color:#2F9E44">{{flt(r.actual_qty).toFixed(2)}}</td>
                <td style="text-align:right;font-family:var(--mono);color:#E67700">{{flt(r.reserved_qty).toFixed(2)}}</td>
                <td style="text-align:right;font-family:var(--mono)">{{fmt(r.valuation_rate)}}</td>
                <td style="text-align:right;font-family:var(--mono);font-weight:600">{{fmt(r.stock_value)}}</td>
                <td style="text-align:center">
                  <span v-if="r.below_reorder" style="font-size:11px;background:#FFF3BF;color:#E67700;padding:2px 7px;border-radius:12px;font-weight:600">⚠ Low</span>
                  <span v-else style="color:#d1d5db">—</span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="stockItems.length" class="cust-row-count">{{stockItems.length}} items</div>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <!-- Add/Edit drawer -->
    <div v-if="showDrawer" class="nim-overlay" @click.self="showDrawer=false">
      <div class="nim-dialog" style="width:560px">
        <div class="nim-header">
          <div class="nim-header-title">{{drawerMode==='add'?'New Warehouse':'Edit Warehouse'}}</div>
          <button class="nim-close" @click="showDrawer=false"><span v-html="icon('x')"></span></button>
        </div>
        <div class="nim-body">
          <div class="nim-section-label">Warehouse Details</div>
          <div class="nim-grid-2 nim-mb">
            <div>
              <label class="nim-label">Warehouse Name <span class="nim-req">*</span></label>
              <input class="nim-input" v-model="form.warehouse_name" placeholder="e.g. Main Store"/>
            </div>
            <div>
              <label class="nim-label">Warehouse Type</label>
              <select class="nim-input" v-model="form.warehouse_type">
                <option v-for="t in WH_TYPES" :key="t" :value="t">{{WH_TYPE_META[t].icon}} {{t}}</option>
              </select>
            </div>
          </div>
          <div class="nim-mb">
            <label class="nim-label">Parent Warehouse</label>
            <SearchableSelect v-model="form.parent_warehouse" :options="parentOptions"
              value-key="name" label-key="label" placeholder="— None (top-level) —"/>
          </div>
          <div class="nim-section-label">Address</div>
          <div class="nim-grid-2 nim-mb">
            <div><label class="nim-label">Address</label><input class="nim-input" v-model="form.address_line1" placeholder="Street address"/></div>
            <div><label class="nim-label">City</label><input class="nim-input" v-model="form.city" placeholder="City"/></div>
            <div>
              <label class="nim-label">Country</label>
              <select class="nim-input" v-model="form.country" @change="form.state=''">
                <option value="">— Select Country —</option>
                <option v-for="c in COUNTRIES" :key="c">{{c}}</option>
              </select>
            </div>
            <div>
              <label class="nim-label">State / Province</label>
              <select v-if="statesFor(form.country).length" class="nim-input" v-model="form.state">
                <option value="">— Select State —</option>
                <option v-for="s in statesFor(form.country)" :key="s" :value="s">{{s}}</option>
              </select>
              <input v-else class="nim-input" v-model="form.state" placeholder="Enter state / province"/>
            </div>
            <div><label class="nim-label">Pincode</label><input class="nim-input" v-model="form.pincode" placeholder="Pincode"/></div>
          </div>
          <div class="nim-section-label">Flags</div>
          <div style="display:flex;gap:24px">
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px">
              <input type="checkbox" :checked="form.is_group" @change="form.is_group=$event.target.checked?1:0"
                style="width:16px;height:16px;cursor:pointer"/> Is Group
            </label>
            <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13px">
              <input type="checkbox" :checked="form.disabled" @change="form.disabled=$event.target.checked?1:0"
                style="width:16px;height:16px;cursor:pointer"/> Disabled
            </label>
          </div>
        </div>
        <div class="nim-footer">
          <div></div>
          <div style="display:flex;gap:10px">
            <button class="nim-btn nim-btn-ghost" @click="showDrawer=false">Cancel</button>
            <button class="nim-btn nim-btn-primary" :disabled="saving" @click="saveWarehouse">
              <span v-html="icon('check')"></span> {{saving?'Saving…':'Save'}}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Stock Transfer modal -->
    <div v-if="showTransfer" class="nim-overlay" @click.self="showTransfer=false">
      <div class="nim-dialog" style="width:480px">
        <div class="nim-header">
          <div class="nim-header-title">Stock Transfer</div>
          <button class="nim-close" @click="showTransfer=false"><span v-html="icon('x')"></span></button>
        </div>
        <div class="nim-body">
          <div class="nim-mb">
            <label class="nim-label">From Warehouse</label>
            <SearchableSelect v-model="transferForm.from_warehouse" :options="list.filter(w=>!w.is_group)" placeholder="Source warehouse"/>
          </div>
          <div class="nim-mb">
            <label class="nim-label">To Warehouse <span class="nim-req">*</span></label>
            <SearchableSelect v-model="transferForm.to_warehouse"
              :options="list.filter(w=>!w.is_group&&w.name!==transferForm.from_warehouse)" placeholder="Target warehouse"/>
          </div>
          <div class="nim-mb">
            <label class="nim-label">Item <span class="nim-req">*</span></label>
            <SearchableSelect v-model="transferForm.item_code" :options="allItems"
              value-key="name" label-key="item_name" placeholder="Select item"/>
          </div>
          <div class="nim-mb">
            <label class="nim-label">Quantity <span class="nim-req">*</span></label>
            <input class="nim-input" type="number" min="0.001" step="0.001" v-model="transferForm.qty"/>
          </div>
        </div>
        <div class="nim-footer">
          <div></div>
          <div style="display:flex;gap:10px">
            <button class="nim-btn nim-btn-ghost" @click="showTransfer=false">Cancel</button>
            <button class="nim-btn nim-btn-primary" :disabled="transferSaving" @click="doTransfer">
              <span v-html="icon('check')"></span> {{transferSaving?'Processing…':'Create Transfer'}}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Delete confirm -->
    <div v-if="showDel" class="nim-overlay" @click.self="showDel=false">
      <div style="background:#fff;border-radius:12px;padding:28px 32px;max-width:420px;width:100%;margin:auto">
        <div style="font-size:16px;font-weight:700;color:#1A1D23;margin-bottom:8px">Delete Warehouse?</div>
        <div style="font-size:14px;color:#868E96;margin-bottom:24px">Delete <b>{{delTarget?.warehouse_name}}</b>? This cannot be undone.</div>
        <div style="display:flex;gap:10px;justify-content:flex-end">
          <button class="nim-btn nim-btn-ghost" @click="showDel=false">Cancel</button>
          <button class="nim-btn" style="background:#C92A2A;color:#fff;border-color:#C92A2A" @click="doDelete">Yes, Delete</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGET, apiSave, apiSubmit, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { fmt, fmtDate, flt } from "../utils/format.js";
import { icon } from "../utils/icons.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import { COUNTRIES, statesFor } from "../composables/useCountryState.js";

const { toast } = useToast();

const WH_TYPE_META = {
  "Stores":             { icon: "🏪", color: "#2563eb", bg: "#F3F0FF" },
  "Finished Goods":     { icon: "📦", color: "#1971C2", bg: "#E7F5FF" },
  "Raw Material":       { icon: "🧲", color: "#2F9E44", bg: "#EBFBEE" },
  "Work In Progress":   { icon: "🔧", color: "#E67700", bg: "#FFF3BF" },
  "Transit":            { icon: "🚚", color: "#C92A2A", bg: "#FFF5F5" },
  "Virtual":            { icon: "🔒", color: "#868E96", bg: "#F8F9FA" },
  "Scrap":              { icon: "♻️", color: "#5C7CFA", bg: "#EDF2FF" },
};
const WH_DEFAULT = { icon: "🏭", color: "#495057", bg: "#F1F3F5" };
const WH_TYPES = Object.keys(WH_TYPE_META);

const list           = ref([]);
const loading        = ref(false);
const selectedWH     = ref(null);
const stockItems     = ref([]);
const stockLoading   = ref(false);
const expanded       = ref(new Set());
const search         = ref("");
const showDrawer     = ref(false);
const showTransfer   = ref(false);
const showDel        = ref(false);
const delTarget      = ref(null);
const drawerMode     = ref("add");
const saving         = ref(false);
const transferSaving = ref(false);
const allItems       = ref([]);

const form = reactive({
  name: "", warehouse_name: "", warehouse_type: "Stores",
  parent_warehouse: "", city: "", country: "India", state: "", address_line1: "", pincode: "",
  is_group: 0, disabled: 0,
});
const transferForm = reactive({
  from_warehouse: "", to_warehouse: "", item_code: "", qty: 1,
});

function whMeta(type) { return WH_TYPE_META[type] || WH_DEFAULT; }

const flatFiltered = computed(() => {
  const q = search.value.toLowerCase().trim();
  if (!q) return list.value;
  return list.value.filter((w) =>
    (w.warehouse_name || w.name).toLowerCase().includes(q) ||
    (w.city || "").toLowerCase().includes(q)
  );
});

const treeNodes = computed(() => {
  if (search.value.trim()) {
    return flatFiltered.value.map((w) => ({ ...w, depth: 0, _children: [] }));
  }
  const map = {};
  list.value.forEach((w) => { map[w.name] = { ...w, _children: [] }; });
  const roots = [];
  list.value.forEach((w) => {
    if (w.parent_warehouse && map[w.parent_warehouse]) {
      map[w.parent_warehouse]._children.push(map[w.name]);
    } else {
      roots.push(map[w.name]);
    }
  });
  const flat = [];
  function walk(node, depth) {
    flat.push({ ...node, depth });
    if (expanded.value.has(node.name)) {
      node._children.forEach((c) => walk(c, depth + 1));
    }
  }
  roots.forEach((r) => walk(r, 0));
  return flat;
});

function toggleExpand(name, e) {
  e.stopPropagation();
  const s = new Set(expanded.value);
  if (s.has(name)) s.delete(name); else s.add(name);
  expanded.value = s;
}

function childCount(name) {
  return list.value.filter((w) => w.parent_warehouse === name).length;
}

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Warehouse", {
      fields: ["name","warehouse_name","warehouse_type","parent_warehouse","city","is_group","disabled"],
      limit: 500,
    }) || [];
    list.value.filter((w) => w.is_group && !w.parent_warehouse).forEach((w) => {
      const s = new Set(expanded.value); s.add(w.name); expanded.value = s;
    });
  } catch { list.value = []; toast("Could not load warehouses", "error"); }
  loading.value = false;
}

async function loadStockForWarehouse(name) {
  stockLoading.value = true;
  stockItems.value = [];
  try {
    stockItems.value = await apiGET("zoho_books_clone.api.inventory.get_stock_summary", { warehouse: name }) || [];
  } catch { stockItems.value = []; }
  stockLoading.value = false;
}

async function loadItems() {
  try { allItems.value = await apiList("Item", { fields: ["name", "item_name"], limit: 500, order: "item_name asc" }) || []; }
  catch {}
}

function selectWarehouse(wh) {
  selectedWH.value = wh;
  loadStockForWarehouse(wh.name);
}

function openAdd() {
  drawerMode.value = "add";
  Object.assign(form, {
    name: "", warehouse_name: "", warehouse_type: "Stores",
    parent_warehouse: "", city: "", state: "", address_line1: "", pincode: "",
    is_group: 0, disabled: 0,
  });
  showDrawer.value = true;
}

function openEdit(wh) {
  drawerMode.value = "edit";
  Object.assign(form, {
    name: wh.name,
    warehouse_name: wh.warehouse_name || wh.name,
    warehouse_type: wh.warehouse_type || "Stores",
    parent_warehouse: wh.parent_warehouse || "",
    city: wh.city || "", state: wh.state || "",
    address_line1: wh.address_line1 || "", pincode: wh.pincode || "",
    is_group: wh.is_group ? 1 : 0,
    disabled: wh.disabled ? 1 : 0,
  });
  showDrawer.value = true;
}

async function saveWarehouse() {
  if (!form.warehouse_name.trim()) { toast("Warehouse name is required", "error"); return; }
  saving.value = true;
  try {
    const company = await resolveCompany();
    const doc = {
      doctype: "Warehouse",
      warehouse_name: form.warehouse_name,
      warehouse_type: form.warehouse_type,
      parent_warehouse: form.parent_warehouse || "",
      city: form.city, state: form.state,
      address_line1: form.address_line1, pincode: form.pincode,
      is_group: form.is_group ? 1 : 0,
      disabled: form.disabled ? 1 : 0,
      company,
    };
    if (drawerMode.value === "edit") doc.name = form.name;
    const saved = await apiSave(doc);
    await load();

    // Optimistic insert: if the reloaded list doesn't contain the saved doc
    // (because the tenancy filter excludes it, or because of indexing lag),
    // splice it in so the UI reflects the user's action.
    if (saved && !list.value.some((w) => w.name === saved.name)) {
      list.value = [saved, ...list.value];
    }

    toast(drawerMode.value === "edit" ? "Warehouse updated" : "Warehouse created");
    showDrawer.value = false;
  } catch (e) { toast("Save failed: " + e.message, "error"); }
  saving.value = false;
}

function openTransfer() {
  Object.assign(transferForm, {
    from_warehouse: selectedWH.value?.name || "",
    to_warehouse: "", item_code: "", qty: 1,
  });
  showTransfer.value = true;
}

async function doTransfer() {
  if (!transferForm.to_warehouse || !transferForm.item_code) {
    toast("Target warehouse and item are required", "error"); return;
  }
  if (flt(transferForm.qty) <= 0) {
    toast("Transfer quantity must be greater than 0", "error"); return;
  }
  if (transferForm.from_warehouse === transferForm.to_warehouse) {
    toast("Source and target warehouse must be different", "error"); return;
  }
  transferSaving.value = true;
  try {
    const company = await resolveCompany();
    const saved = await apiSave({
      doctype: "Stock Entry",
      company,
      stock_entry_type: "Material Transfer",
      posting_date: new Date().toISOString().slice(0,10),
      from_warehouse: transferForm.from_warehouse,
      to_warehouse: transferForm.to_warehouse,
      items: [{ doctype: "Stock Entry Detail", item_code: transferForm.item_code, qty: flt(transferForm.qty), s_warehouse: transferForm.from_warehouse, t_warehouse: transferForm.to_warehouse }],
    });
    await apiSubmit("Stock Entry", saved.name);
    toast("Stock transfer created");
    showTransfer.value = false;
    loadStockForWarehouse(selectedWH.value.name);
  } catch (e) { toast("Transfer failed: " + e.message, "error"); }
  transferSaving.value = false;
}

function confirmDel(wh) { delTarget.value = wh; showDel.value = true; }

async function doDelete() {
  try {
    await apiDelete("Warehouse", delTarget.value.name);
    list.value = list.value.filter((w) => w.name !== delTarget.value.name);
    if (selectedWH.value?.name === delTarget.value.name) selectedWH.value = null;
    toast("Warehouse deleted");
    showDel.value = false;
  } catch (e) { toast("Delete failed: " + e.message, "error"); }
}

const parentOptions = computed(() =>
  list.value.filter((w) => w.is_group).map((w) => ({ name: w.name, label: w.warehouse_name || w.name }))
);

const whStats = computed(() => {
  if (!selectedWH.value || !stockItems.value.length) return { value: 0, items: 0, reserved: 0, projected: 0 };
  return {
    value:     stockItems.value.reduce((s, r) => s + flt(r.stock_value),    0),
    items:     stockItems.value.length,
    reserved:  stockItems.value.reduce((s, r) => s + flt(r.reserved_qty),   0),
    projected: stockItems.value.reduce((s, r) => s + flt(r.projected_qty),  0),
  };
});

onMounted(() => { load(); loadItems(); });
</script>
