<template>
<div class="b-page">
  <!-- Toolbar -->
  <div class="b-action-bar">
    <div style="display:flex;align-items:center;gap:10px;flex:1">
      <div style="display:flex;align-items:center;gap:6px;background:#fff;border:1px solid #E2E8F0;border-radius:20px;padding:5px 14px;max-width:260px;width:100%">
        <span v-html="icon('search',13)" style="color:#868E96;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search items…" style="border:none;outline:none;font-size:13px;width:100%;background:transparent;font-family:inherit"/>
      </div>
    </div>
    <div style="display:flex;gap:6px">
      <button class="b-btn b-btn-ghost" @click="loadPriceLists"><span v-html="icon('refresh',13)"></span></button>
      <button class="b-btn b-btn-ghost" @click="exportCSV" :disabled="!filteredPrices.length"><span v-html="icon('download',13)"></span> Export</button>
      <button class="b-btn b-btn-primary" @click="openAddPrice"><span v-html="icon('plus',13)"></span> Add Price</button>
    </div>
  </div>

  <div style="display:grid;grid-template-columns:240px 1fr;gap:16px;align-items:start">

    <!-- Left: Price List selector -->
    <div class="b-card" style="padding:0;overflow:hidden">
      <div style="padding:14px 16px;border-bottom:1px solid #F1F3F5;font-size:12px;font-weight:700;color:#868E96;letter-spacing:.04em;text-transform:uppercase">Price Lists</div>
      <div v-if="loadingLists" style="padding:20px;text-align:center;color:#868e96;font-size:13px">Loading…</div>
      <div v-else>
        <div v-for="pl in priceLists" :key="pl.name"
          @click="selectList(pl)"
          :style="'padding:12px 16px;cursor:pointer;border-bottom:1px solid #F8F9FA;display:flex;align-items:center;gap:10px;transition:background .12s;'+(selectedList?.name===pl.name?'background:#EDF2FF;':'background:#fff;')"
        >
          <div :style="'width:34px;height:34px;border-radius:8px;display:flex;align-items:center;justify-content:center;flex-shrink:0;font-size:14px;'+(pl.selling?'background:#EBFBEE;':'background:#FFF3BF;')">
            {{ pl.selling ? '🏷️' : '🛒' }}
          </div>
          <div style="flex:1;min-width:0">
            <div style="font-size:13px;font-weight:600;color:#1a1a2e;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{pl.name}}</div>
            <div style="font-size:11.5px;color:#868E96;margin-top:1px">{{pl.selling?'Selling':'Buying'}} · {{pl.currency||'INR'}}</div>
          </div>
          <span v-if="selectedList?.name===pl.name" v-html="icon('chevron-right',12)" style="color:#3B5BDB;flex-shrink:0"></span>
        </div>
        <div v-if="!priceLists.length" style="padding:20px;text-align:center;color:#868E96;font-size:12.5px">No price lists found</div>
        <div style="padding:10px 12px;border-top:1px solid #F1F3F5">
          <button class="b-btn b-btn-ghost" @click="openNewPriceList" style="width:100%;font-size:12px;padding:6px 10px">
            <span v-html="icon('plus',11)" style="vertical-align:-1px;margin-right:4px"></span> New Price List
          </button>
        </div>
      </div>
    </div>

    <!-- Right: Item prices table -->
    <div>
      <div v-if="!selectedList" style="background:#fff;border:1px dashed #E2E8F0;border-radius:12px;padding:60px;text-align:center;color:#868E96">
        <div style="font-size:36px;margin-bottom:10px">🏷️</div>
        <div style="font-size:14px;font-weight:600;margin-bottom:4px">Select a Price List</div>
        <div style="font-size:12.5px">Choose a price list on the left to view and manage item prices</div>
      </div>

      <template v-else>
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px">
          <div>
            <div style="font-size:15px;font-weight:700;color:#1a1a2e">{{selectedList.name}}</div>
            <div style="font-size:12px;color:#868E96;margin-top:2px">
              {{filteredPrices.length}} item{{filteredPrices.length!==1?'s':''}}
              · {{selectedList.currency||'INR'}}
              · {{selectedList.selling?'Selling':'Buying'}}
            </div>
          </div>
        </div>

        <div class="b-card" style="padding:0;overflow:hidden">
          <table class="b-table">
            <thead>
              <tr>
                <th>Item Code</th>
                <th>Item Name</th>
                <th>UOM</th>
                <th class="ta-r">Rate (₹)</th>
                <th>Valid From</th>
                <th>Valid Upto</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              <template v-if="loadingPrices">
                <tr v-for="n in 5" :key="n"><td colspan="7" style="padding:14px"><div class="b-shimmer" style="height:12px"></div></td></tr>
              </template>
              <tr v-else-if="!filteredPrices.length">
                <td colspan="7" class="b-empty">
                  {{ search ? 'No items match your search' : 'No item prices in this list — click "Add Price" to start' }}
                </td>
              </tr>
              <tr v-else v-for="p in filteredPrices" :key="p.name" class="clickable" @click="openEditPrice(p)">
                <td><span  style="font-size:12px;color:#3B5BDB">{{p.item_code}}</span></td>
                <td class="fw-600">{{p.item_name||p.item_code}}</td>
                <td class="c-muted" style="font-size:12.5px">{{p.uom||'Nos'}}</td>
                <td class="ta-r fw-600" style="color:#2F9E44">{{fmtRate(p.price_list_rate)}}</td>
                <td class="c-muted" style="font-size:12.5px">{{p.valid_from||'—'}}</td>
                <td class="c-muted" style="font-size:12.5px">{{p.valid_upto||'—'}}</td>
                <td style="text-align:center">
                  <button @click.stop="confirmDelPrice(p)" style="background:none;border:none;cursor:pointer;color:#C92A2A;padding:4px" v-html="icon('trash',13)"></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </template>
    </div>
  </div>

  <!-- ===== Item Price Drawer ===== -->
  <Teleport to="body">
    <div v-if="showPriceDrawer" class="nim-overlay" @click.self="showPriceDrawer=false">
      <div class="nim-dialog" style="width:500px">
        <div class="nim-header">
          <span style="font-size:15px;font-weight:700">{{priceMode==='add'?'Add Item Price':'Edit Item Price'}}</span>
          <button class="nim-btn nim-btn-ghost" @click="showPriceDrawer=false"><span v-html="icon('x',14)"/></button>
        </div>
        <div class="nim-body" style="display:grid;gap:14px">
          <div class="nim-field">
            <label class="nim-label">Price List</label>
            <input class="nim-input" :value="priceForm.price_list" readonly style="background:#f8f9fc;color:#868e96"/>
          </div>
          <div class="nim-field">
            <label class="nim-label">Item Code <span style="color:#c92a2a">*</span></label>
            <input class="nim-input" v-model="priceForm.item_code" :readonly="priceMode==='edit'"
              :style="priceMode==='edit'?'background:#f8f9fc;color:#868e96':''"
              @input="onItemCodeInput" placeholder="e.g. ITEM-001"/>
            <div v-if="itemSuggestions.length && priceMode==='add'" style="position:relative">
              <div style="position:absolute;top:2px;left:0;right:0;background:#fff;border:1px solid #E2E8F0;border-radius:6px;box-shadow:0 4px 12px rgba(0,0,0,.1);z-index:100;max-height:180px;overflow-y:auto">
                <div v-for="s in itemSuggestions" :key="s.name"
                  @click="pickItem(s)"
                  style="padding:8px 12px;cursor:pointer;font-size:13px;border-bottom:1px solid #F8F9FA"
                  onmouseover="this.style.background='#F8F9FA'" onmouseout="this.style.background=''"
                >{{s.item_code||s.name}} — {{s.item_name||s.name}}</div>
              </div>
            </div>
          </div>
          <div class="nim-field">
            <label class="nim-label">Item Name</label>
            <input class="nim-input" v-model="priceForm.item_name" placeholder="Auto-filled from item code"/>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="nim-field">
              <label class="nim-label">Rate (₹) <span style="color:#c92a2a">*</span></label>
              <input class="nim-input" type="number" v-model="priceForm.price_list_rate" min="0" step="0.01" placeholder="0.00"/>
            </div>
            <div class="nim-field">
              <label class="nim-label">UOM</label>
              <input class="nim-input" v-model="priceForm.uom" placeholder="Nos"/>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="nim-field">
              <label class="nim-label">Valid From</label>
              <input class="nim-input" type="date" v-model="priceForm.valid_from"/>
            </div>
            <div class="nim-field">
              <label class="nim-label">Valid Upto</label>
              <input class="nim-input" type="date" v-model="priceForm.valid_upto"/>
            </div>
          </div>
        </div>
        <div class="nim-footer">
          <button class="nim-btn nim-btn-ghost" @click="showPriceDrawer=false">Cancel</button>
          <button class="nim-btn nim-btn-primary" @click="savePrice" :disabled="savingPrice">
            {{savingPrice?'Saving…':'Save Price'}}
          </button>
        </div>
      </div>
    </div>

    <!-- New Price List dialog -->
    <div v-if="showNewListDialog" class="nim-overlay" @click.self="showNewListDialog=false">
      <div class="nim-dialog" style="width:440px">
        <div class="nim-header">
          <span style="font-size:15px;font-weight:700">New Price List</span>
          <button class="nim-btn nim-btn-ghost" @click="showNewListDialog=false"><span v-html="icon('x',14)"/></button>
        </div>
        <div class="nim-body" style="display:grid;gap:14px">
          <div class="nim-field">
            <label class="nim-label">Price List Name <span style="color:#c92a2a">*</span></label>
            <input class="nim-input" v-model="newListForm.name" placeholder="e.g. Wholesale Selling"/>
          </div>
          <div class="nim-field">
            <label class="nim-label">Currency</label>
            <input class="nim-input" v-model="newListForm.currency" placeholder="INR"/>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="nim-field" style="display:flex;align-items:center;gap:8px;padding:10px;background:#f8f9fa;border-radius:8px;cursor:pointer" @click="newListForm.selling=!newListForm.selling">
              <input type="checkbox" :checked="newListForm.selling" style="width:15px;height:15px;cursor:pointer" @click.stop="newListForm.selling=!newListForm.selling"/>
              <label style="font-size:13px;font-weight:600;cursor:pointer">Selling</label>
            </div>
            <div class="nim-field" style="display:flex;align-items:center;gap:8px;padding:10px;background:#f8f9fa;border-radius:8px;cursor:pointer" @click="newListForm.buying=!newListForm.buying">
              <input type="checkbox" :checked="newListForm.buying" style="width:15px;height:15px;cursor:pointer" @click.stop="newListForm.buying=!newListForm.buying"/>
              <label style="font-size:13px;font-weight:600;cursor:pointer">Buying</label>
            </div>
          </div>
        </div>
        <div class="nim-footer">
          <button class="nim-btn nim-btn-ghost" @click="showNewListDialog=false">Cancel</button>
          <button class="nim-btn nim-btn-primary" @click="saveNewPriceList" :disabled="savingList">
            {{savingList?'Saving…':'Create'}}
          </button>
        </div>
      </div>
    </div>

    <!-- Delete Item Price confirm -->
    <div v-if="showDelPrice" class="nim-overlay" @click.self="showDelPrice=false">
      <div class="nim-dialog" style="width:400px">
        <div class="nim-header"><span style="font-weight:700;color:#C92A2A">Delete Item Price?</span></div>
        <div class="nim-body">
          <p style="font-size:13.5px;color:#374151">Remove price for <b>{{delPriceTarget?.item_code}}</b> from <b>{{selectedList?.name}}</b>? This cannot be undone.</p>
        </div>
        <div class="nim-footer">
          <button class="nim-btn nim-btn-ghost" @click="showDelPrice=false">Cancel</button>
          <button class="nim-btn" style="background:#C92A2A;color:#fff;border-color:#C92A2A" @click="doDelPrice">Delete</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiGET, apiPOST, apiList, apiSave, apiDelete } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";

const { toast } = useToast();

const search         = ref("");
const priceLists     = ref([]);
const selectedList   = ref(null);
const itemPrices     = ref([]);
const loadingLists   = ref(false);
const loadingPrices  = ref(false);

// Price drawer
const showPriceDrawer = ref(false);
const priceMode       = ref("add");
const savingPrice     = ref(false);
const priceForm = reactive({
  name: "", price_list: "", item_code: "", item_name: "",
  price_list_rate: "", uom: "Nos", valid_from: "", valid_upto: "",
});

// Item autocomplete
const itemSuggestions = ref([]);
let suggestTimer = null;

// New Price List dialog
const showNewListDialog = ref(false);
const savingList = ref(false);
const newListForm = reactive({ name: "", currency: "INR", selling: 1, buying: 0 });

// Delete price confirm
const showDelPrice    = ref(false);
const delPriceTarget  = ref(null);

const filteredPrices = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return itemPrices.value;
  return itemPrices.value.filter(p =>
    (p.item_code || "").toLowerCase().includes(q) ||
    (p.item_name || "").toLowerCase().includes(q)
  );
});

function exportCSV() {
  const rows = filteredPrices.value;
  if (!rows.length) return;
  const esc = v => { const s = v==null?"":String(v); return /[",\n]/.test(s) ? '"'+s.replace(/"/g,'""')+'"' : s; };
  const listName = selectedList.value?.name || "price_list";
  const lines = [["Item Code","Item Name","Rate","UOM","Currency","Valid From","Valid Upto"].join(",")];
  for (const p of rows) {
    lines.push([p.item_code||"",p.item_name||"",parseFloat(p.price_list_rate)||0,p.uom||"",p.currency||"",p.valid_from||"",p.valid_upto||""].map(esc).join(","));
  }
  const blob = new Blob(["﻿"+lines.join("\r\n")], {type:"text/csv;charset=utf-8;"});
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `prices_${listName}_${new Date().toISOString().slice(0,10)}.csv`.replace(/\s+/g,"_");
  a.click(); URL.revokeObjectURL(url);
  toast(`Exported ${rows.length} price(s)`);
}

function fmtRate(v) {
  const n = parseFloat(v) || 0;
  return "₹" + n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function loadPriceLists() {
  loadingLists.value = true;
  try {
    priceLists.value = await apiGET("frappe.client.get_list", {
      doctype: "Price List",
      fields: JSON.stringify(["name", "currency", "buying", "selling", "enabled"]),
      filters: JSON.stringify([["enabled", "=", 1]]),
      order_by: "name asc",
      limit_page_length: 50,
    }) || [];
  } catch (e) { toast("Could not load price lists: " + e.message, "error"); }
  loadingLists.value = false;
}

async function selectList(pl) {
  selectedList.value = pl;
  search.value = "";
  await loadItemPrices();
}

async function loadItemPrices() {
  if (!selectedList.value) return;
  loadingPrices.value = true;
  try {
    itemPrices.value = await apiGET("frappe.client.get_list", {
      doctype: "Item Price",
      fields: JSON.stringify(["name","item_code","item_name","price_list_rate","uom","currency","valid_from","valid_upto"]),
      filters: JSON.stringify([["price_list","=",selectedList.value.name]]),
      order_by: "item_code asc",
      limit_page_length: 200,
    }) || [];
  } catch (e) { toast("Could not load item prices: " + e.message, "error"); }
  loadingPrices.value = false;
}

function openAddPrice() {
  if (!selectedList.value) { toast("Select a price list first", "error"); return; }
  priceMode.value = "add";
  Object.assign(priceForm, {
    name: "", price_list: selectedList.value.name,
    item_code: "", item_name: "", price_list_rate: "",
    uom: "Nos", valid_from: "", valid_upto: "", note: "",
  });
  itemSuggestions.value = [];
  showPriceDrawer.value = true;
}

function openEditPrice(p) {
  priceMode.value = "edit";
  Object.assign(priceForm, {
    name: p.name,
    price_list: p.price_list || selectedList.value?.name || "",
    item_code: p.item_code,
    item_name: p.item_name || "",
    price_list_rate: p.price_list_rate,
    uom: p.uom || "Nos",
    valid_from: p.valid_from || "",
    valid_upto: p.valid_upto || "",
  });
  itemSuggestions.value = [];
  showPriceDrawer.value = true;
}

function onItemCodeInput() {
  clearTimeout(suggestTimer);
  const txt = priceForm.item_code.trim();
  if (txt.length < 2) { itemSuggestions.value = []; return; }
  suggestTimer = setTimeout(async () => {
    try {
      const res = await apiGET("frappe.client.get_list", {
        doctype: "Item",
        fields: JSON.stringify(["name","item_code","item_name"]),
        filters: JSON.stringify([
          ["item_code","like","%"+txt+"%"],
        ]),
        limit_page_length: 8,
      }) || [];
      itemSuggestions.value = res;
    } catch { itemSuggestions.value = []; }
  }, 250);
}

function pickItem(s) {
  priceForm.item_code = s.item_code || s.name;
  priceForm.item_name = s.item_name || s.name;
  itemSuggestions.value = [];
}

async function savePrice() {
  if (!priceForm.item_code.trim()) { toast("Item code is required", "error"); return; }
  if (!priceForm.price_list_rate && priceForm.price_list_rate !== 0) { toast("Rate is required", "error"); return; }
  savingPrice.value = true;
  try {
    const doc = {
      doctype: "Item Price",
      price_list: priceForm.price_list,
      item_code: priceForm.item_code,
      item_name: priceForm.item_name || priceForm.item_code,
      price_list_rate: parseFloat(priceForm.price_list_rate) || 0,
      uom: priceForm.uom || "Nos",
      valid_from: priceForm.valid_from || null,
      valid_upto: priceForm.valid_upto || null,
    };
    if (priceMode.value === "edit" && priceForm.name) doc.name = priceForm.name;
    await apiSave(doc);
    toast(priceMode.value === "add" ? "Price added" : "Price updated");
    showPriceDrawer.value = false;
    await loadItemPrices();
  } catch (e) { toast(e.message || "Failed to save price", "error"); }
  savingPrice.value = false;
}

function confirmDelPrice(p) {
  delPriceTarget.value = p;
  showDelPrice.value = true;
}

async function doDelPrice() {
  if (!delPriceTarget.value) return;
  try {
    await apiDelete("Item Price", delPriceTarget.value.name);
    toast("Price deleted");
    showDelPrice.value = false;
    await loadItemPrices();
  } catch (e) { toast(e.message || "Delete failed", "error"); }
}

function openNewPriceList() {
  Object.assign(newListForm, { name: "", currency: "INR", selling: 1, buying: 0 });
  showNewListDialog.value = true;
}

async function saveNewPriceList() {
  if (!newListForm.name.trim()) { toast("Name is required", "error"); return; }
  savingList.value = true;
  try {
    await apiSave({
      doctype: "Price List",
      name: newListForm.name,
      currency: newListForm.currency || "INR",
      selling: newListForm.selling ? 1 : 0,
      buying: newListForm.buying ? 1 : 0,
      enabled: 1,
    });
    toast("Price list created");
    showNewListDialog.value = false;
    await loadPriceLists();
  } catch (e) { toast(e.message || "Failed to create price list", "error"); }
  savingList.value = false;
}

onMounted(loadPriceLists);
</script>
