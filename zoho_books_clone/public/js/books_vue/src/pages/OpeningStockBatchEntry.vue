<template>
  <div class="ob-page">

    <!-- ── Summary strip ── -->
    <div class="ob-kpi-strip">
      <div class="ob-kpi">
        <div class="ob-kpi-ico" style="background:#eff6ff;color:#2563eb"><span v-html="icon('opening',16)"></span></div>
        <div><div class="ob-kpi-lbl">Opening Entries</div><div class="ob-kpi-val">{{ kpi.total }}</div></div>
      </div>
      <div class="ob-kpi">
        <div class="ob-kpi-ico" style="background:#f0fdf4;color:#16a34a"><span v-html="icon('box',16)"></span></div>
        <div><div class="ob-kpi-lbl">Items Set</div><div class="ob-kpi-val" style="color:#16a34a">{{ kpi.itemCount }}</div></div>
      </div>
      <div class="ob-kpi">
        <div class="ob-kpi-ico" style="background:#fffbeb;color:#d97706"><span v-html="icon('hash',16)"></span></div>
        <div><div class="ob-kpi-lbl">Batches Created</div><div class="ob-kpi-val" style="color:#d97706">{{ kpi.batchCount }}</div></div>
      </div>
      <div class="ob-kpi ob-kpi-value">
        <div class="ob-kpi-ico" style="background:#faf5ff;color:#7c3aed"><span v-html="icon('chart',16)"></span></div>
        <div><div class="ob-kpi-lbl">Opening Value</div><div class="ob-kpi-val" style="color:#7c3aed;font-size:13px">{{ fmtCur(kpi.value) }}</div></div>
      </div>
    </div>

    <!-- ── Action bar ── -->
    <div class="ob-actions">
      <div class="ob-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search entry #, item, warehouse, batch…" class="ob-search-input" />
      </div>
      <div style="display:flex;gap:8px;">
        <button class="ob-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="ob-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Opening Stock Entry</button>
      </div>
    </div>

    <p class="ob-hint">
      Use this to set the starting stock-on-hand for each item/warehouse before go-live.
      Items flagged <em>Has Batch No</em> require a Batch No, manufacturing date, and
      expiry date per line — the batch record is created automatically when you save.
    </p>

    <!-- ── Table ── -->
    <div class="ob-card">
      <table class="ob-table ob-desktop-table">
        <thead><tr>
          <th>Entry #</th>
          <th>Date</th>
          <th>Warehouse(s)</th>
          <th class="ta-r">Items</th>
          <th class="ta-r">Batched Lines</th>
          <th class="ta-r">Value</th>
          <th>Status</th>
          <th style="width:44px"></th>
        </tr></thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="8"><div class="ob-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="e in filtered" :key="e.name" class="ob-row" @click="openView(e)">
              <td><span class="ob-num">{{ e.name }}</span></td>
              <td class="mono-sm text-muted">{{ fmtDate(e.posting_date) }}</td>
              <td><span class="ob-wh-tag" v-if="e.to_warehouse">{{ shortWH(e.to_warehouse) }}</span><span v-else class="text-muted">Multiple</span></td>
              <td class="ta-r">{{ e._itemCount ?? '—' }}</td>
              <td class="ta-r">{{ e._batchCount ?? '—' }}</td>
              <td class="ta-r" style="font-weight:600">{{ fmtCur(e.total_incoming_value) }}</td>
              <td><span class="ob-badge" :class="statusClass(e)">{{ statusLabel(e) }}</span></td>
              <td @click.stop><button class="ob-act-btn" @click="openView(e)"><span v-html="icon('eye',13)"></span></button></td>
            </tr>
            <tr v-if="!filtered.length">
              <td colspan="8" class="ob-empty">
                <div style="font-size:32px;margin-bottom:8px">🗃️</div>
                <div style="font-weight:600;margin-bottom:4px">No opening stock entries yet</div>
                <div style="font-size:13px;color:#9ca3af;margin-bottom:12px">Set starting balances and batches before go-live</div>
                <button class="ob-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Opening Stock Entry</button>
              </td>
            </tr>
          </template>
        </tbody>
      </table>

      <!-- Mobile cards -->
      <div class="ob-mobile-cards">
        <template v-if="loading">
          <div v-for="n in 4" :key="n" class="ob-mobile-card ob-mc--skeleton">
            <div class="ob-mc-shimmer" style="height:13px;width:55%;margin-bottom:8px"></div>
            <div class="ob-mc-shimmer" style="height:11px;width:40%"></div>
          </div>
        </template>
        <div v-else-if="!filtered.length" class="ob-mc-empty">No opening stock entries yet</div>
        <template v-else>
          <div v-for="e in filtered" :key="e.name" class="ob-mobile-card" @click="openView(e)">
            <div class="ob-mc-top">
              <span class="ob-mc-docno">{{ e.name }}</span>
              <span class="ob-badge" :class="statusClass(e)">{{ statusLabel(e) }}</span>
            </div>
            <div class="ob-mc-meta">
              <span>{{ fmtDate(e.posting_date) }}</span>
              <span style="font-weight:700">{{ fmtCur(e.total_incoming_value) }}</span>
            </div>
          </div>
        </template>
      </div>
    </div>

    <!-- ── Create Drawer ── -->
    <div v-if="drawerOpen" class="ob-overlay" @click.self="drawerOpen=false"></div>
    <div class="ob-drawer" :class="{open:drawerOpen}">
      <div class="ob-dheader">
        <button class="ob-dclose ob-dclose-abs" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
        <div class="ob-dh-top">
          <div class="ob-dh-ico"><span v-html="icon('opening',20)" style="color:#fff"></span></div>
          <div>
            <div class="ob-dh-title" style="color:#fff">Opening Stock & Batch Entry</div>
            <div class="ob-dh-sub" style="color:rgba(255,255,255,.75)">Set starting balances and batch numbers</div>
          </div>
        </div>
      </div>
      <div class="ob-dbody">
        <div class="ob-fields-grid">
          <div class="ob-field">
            <label class="ob-label">Posting Date <span class="req">*</span></label>
            <input v-model="form.posting_date" type="date" class="ob-input" />
          </div>
          <div class="ob-field">
            <label class="ob-label">Default Warehouse</label>
            <SearchableSelect v-model="form.to_warehouse" :options="warehouses" placeholder="Applies to lines left blank…" @search="fetchWarehouses" />
          </div>
          <div class="ob-field" style="grid-column:1/-1">
            <label class="ob-label">Remarks</label>
            <input v-model="form.remarks" class="ob-input" placeholder="e.g. Opening balance as of go-live date"/>
          </div>
        </div>

        <div class="ob-section-title" style="margin-top:4px">Items & Batches</div>

        <!-- Desktop table -->
        <div class="ob-items-table ob-add-items-desktop">
          <div class="ob-items-head">
            <div>Item</div>
            <div>Warehouse</div>
            <div class="ta-r">Qty</div>
            <div class="ta-r">Rate (₹)</div>
            <div>Batch No</div>
            <div>Mfg Date</div>
            <div>Expiry Date</div>
            <div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="ob-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items" placeholder="Item…" @search="fetchItems" @select="opt=>onItemSelect(line,opt)" /></div>
            <div><SearchableSelect v-model="line.t_warehouse" :options="warehouses" placeholder="Warehouse…" @search="fetchWarehouses" :compact="true"/></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="ob-input ta-r" /></div>
            <div><input v-model.number="line.basic_rate" type="number" min="0" step="0.01" class="ob-input ta-r" /></div>
            <div>
              <input
                v-model="line.batch_no"
                class="ob-input"
                :class="{'ob-input-req': line.has_batch_no && !line.batch_no}"
                :placeholder="line.has_batch_no ? 'Required — auto or type…' : 'Optional'"
              />
            </div>
            <div><input v-model="line.manufacturing_date" type="date" class="ob-input" :disabled="!line.has_batch_no"/></div>
            <div><input v-model="line.expiry_date" type="date" class="ob-input" :disabled="!line.has_batch_no"/></div>
            <div><button @click="removeLine(line.id)" class="ob-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <div class="ob-items-total" v-if="lines.length">
            <div style="grid-column:1/5;text-align:right;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.05em;color:#6b7280">Total Opening Value</div>
            <div class="ta-r" style="grid-column:5/9;font-weight:700;color:#0f172a">{{ fmtCur(lineTotal) }}</div>
          </div>
          <button class="ob-add-line" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <!-- Mobile cards -->
        <div class="ob-add-items-mobile">
          <div v-for="(line, idx) in lines" :key="line.id" class="ob-aic">
            <div class="ob-aic-header">
              <span class="ob-aic-num">Item {{ idx + 1 }}</span>
              <button @click="removeLine(line.id)" class="ob-rm-line"><span v-html="icon('x',12)"></span></button>
            </div>
            <div class="ob-aic-field">
              <label class="ob-label">Item</label>
              <SearchableSelect v-model="line.item_code" :options="items" placeholder="Item…" @search="fetchItems" @select="opt=>onItemSelect(line,opt)" />
            </div>
            <div class="ob-aic-field">
              <label class="ob-label">Warehouse</label>
              <SearchableSelect v-model="line.t_warehouse" :options="warehouses" placeholder="Warehouse…" @search="fetchWarehouses" />
            </div>
            <div style="display:flex;gap:8px">
              <div class="ob-aic-field" style="flex:1">
                <label class="ob-label">Qty</label>
                <input v-model.number="line.qty" type="number" min="0" step="0.001" class="ob-input ta-r" />
              </div>
              <div class="ob-aic-field" style="flex:1">
                <label class="ob-label">Rate (₹)</label>
                <input v-model.number="line.basic_rate" type="number" min="0" step="0.01" class="ob-input ta-r" />
              </div>
            </div>
            <template v-if="line.has_batch_no">
              <div class="ob-aic-field">
                <label class="ob-label">Batch No <span class="req">*</span></label>
                <input v-model="line.batch_no" class="ob-input" placeholder="Auto or type…" />
              </div>
              <div style="display:flex;gap:8px">
                <div class="ob-aic-field" style="flex:1">
                  <label class="ob-label">Mfg Date</label>
                  <input v-model="line.manufacturing_date" type="date" class="ob-input" />
                </div>
                <div class="ob-aic-field" style="flex:1">
                  <label class="ob-label">Expiry Date</label>
                  <input v-model="line.expiry_date" type="date" class="ob-input" />
                </div>
              </div>
            </template>
            <div class="ob-aic-amount">{{ fmtCur(flt(line.qty)*flt(line.basic_rate)) }}</div>
          </div>
        </div>
      </div>
      <div class="ob-dfooter">
        <button class="ob-btn-cancel" @click="drawerOpen=false">Cancel</button>
        <button class="ob-btn-save" :disabled="drawerSaving" @click="saveEntry(0)"><span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}</button>
        <button class="ob-btn-primary" :disabled="drawerSaving" @click="saveEntry(1)"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Submitting…':'Submit' }}</button>
      </div>
    </div>

    <!-- ── View Panel ── -->
    <div v-if="viewOpen" class="ob-overlay" @click.self="viewOpen=false"></div>
    <div class="ob-drawer ob-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="ob-dheader">
          <button class="ob-dclose ob-dclose-abs" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
          <div class="ob-dh-top">
            <div class="ob-dh-ico" style="background:rgba(255,255,255,.2)"><span v-html="icon('opening',20)" style="color:#fff"></span></div>
            <div>
              <div class="ob-dh-title" style="color:#fff">{{ viewDoc.name }}</div>
              <div class="ob-dh-sub" style="color:rgba(255,255,255,.8)">Opening Stock · {{ fmtDate(viewDoc.posting_date) }}</div>
            </div>
            <span class="ob-badge" :class="statusClass(viewDoc)" style="margin-left:auto;flex-shrink:0">{{ statusLabel(viewDoc) }}</span>
          </div>
        </div>
        <div class="ob-dbody">
          <div class="ob-view-section" v-if="viewLoading">
            <div class="ob-view-sec-lbl">Items</div>
            <div v-for="n in 3" :key="n" class="ob-shimmer" style="height:36px;margin-bottom:6px;border-radius:6px"></div>
          </div>
          <div class="ob-view-section" v-else-if="(viewDoc.items||[]).length">
            <div class="ob-view-sec-lbl">Items ({{ viewDoc.items.length }})</div>
            <table class="ob-view-items-tbl">
              <thead><tr>
                <th>Item</th><th>Warehouse</th><th>Batch No</th><th class="ta-r">Qty</th><th class="ta-r">Rate</th><th class="ta-r">Amount</th>
              </tr></thead>
              <tbody>
                <tr v-for="it in viewDoc.items" :key="it.name||it.idx">
                  <td>
                    <div style="font-weight:600;font-size:12.5px">{{ it.item_code }}</div>
                    <div v-if="it.item_name && it.item_name!==it.item_code" style="font-size:11px;color:#9ca3af">{{ it.item_name }}</div>
                  </td>
                  <td class="text-muted" style="font-size:12px">{{ it.t_warehouse||viewDoc.to_warehouse||'—' }}</td>
                  <td class="text-muted" style="font-size:12px">{{ it.batch_no||'—' }}</td>
                  <td class="ta-r">{{ it.qty }}</td>
                  <td class="ta-r">{{ fmtCur(it.basic_rate) }}</td>
                  <td class="ta-r" style="font-weight:600">{{ fmtCur(flt(it.qty)*flt(it.basic_rate)) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="ob-view-section">
            <div class="ob-view-sec-lbl">Value Summary</div>
            <div class="ob-val-box">
              <div class="ob-val-lbl">Total Opening Value</div>
              <div class="ob-val-num">{{ fmtCur(viewDoc.total_incoming_value||0) }}</div>
            </div>
          </div>
          <div v-if="viewDoc.docstatus===0" style="display:flex;justify-content:flex-end">
            <button class="ob-btn-primary" @click="submitEntry(viewDoc.name)"><span v-html="icon('check',13)"></span> Submit</button>
          </div>
        </div>
      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGet, apiSave, apiSubmit, resolveCompany, apiLinkValues } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();

const search       = ref("");
const list         = ref([]);
const loading      = ref(false);
const drawerOpen   = ref(false);
const drawerSaving = ref(false);
const viewOpen     = ref(false);
const viewDoc      = ref(null);
const viewLoading  = ref(false);
const warehouses   = ref([]);
const items        = ref([]);
const lines        = ref([]);
let _id = 1;
const blankLine = () => ({
  id: _id++, item_code: "", item_name: "", qty: 1, basic_rate: 0,
  t_warehouse: "", batch_no: "", manufacturing_date: "", expiry_date: "",
  has_batch_no: 0,
});

const form = reactive({
  posting_date: new Date().toISOString().slice(0, 10),
  to_warehouse: "",
  remarks: "",
});

const lineTotal = computed(() => lines.value.reduce((s, l) => s + flt(l.qty) * flt(l.basic_rate), 0));

const filtered = computed(() => {
  const q = search.value.trim().toLowerCase();
  if (!q) return list.value;
  return list.value.filter(e =>
    (e.name || "").toLowerCase().includes(q) ||
    (e.to_warehouse || "").toLowerCase().includes(q) ||
    (e.remarks || "").toLowerCase().includes(q)
  );
});

const kpi = computed(() => ({
  total:       list.value.length,
  itemCount:   list.value.reduce((s, e) => s + (e._itemCount || 0), 0),
  batchCount:  list.value.reduce((s, e) => s + (e._batchCount || 0), 0),
  value:       list.value.filter(e => e.docstatus === 1).reduce((s, e) => s + flt(e.total_incoming_value), 0),
}));

function statusClass(e) {
  if (e.docstatus === 1) return "badge-green";
  if (e.docstatus === 2) return "badge-grey";
  return "badge-orange";
}
function statusLabel(e) {
  return e.docstatus === 1 ? "Submitted" : e.docstatus === 2 ? "Cancelled" : "Draft";
}
function shortWH(wh) {
  if (!wh) return "";
  const parts = wh.split(" - ");
  return parts[0].length > 18 ? parts[0].slice(0, 16) + "…" : parts[0];
}
function fmtCur(v) {
  return "₹" + flt(v).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    const rows = await apiList("Stock Entry", {
      fields: ["name", "posting_date", "to_warehouse", "total_incoming_value", "docstatus", "remarks", "company"],
      filters: [["company", "=", co], ["stock_entry_type", "=", "Opening Stock"]],
      limit: 500, order: "posting_date desc, creation desc",
    });
    // Pull item/batch counts for each entry (best-effort; small N expected)
    for (const e of rows) {
      try {
        const full = await apiGet("Stock Entry", e.name);
        e._itemCount = (full?.items || []).length;
        e._batchCount = (full?.items || []).filter(i => i.batch_no).length;
      } catch { e._itemCount = null; e._batchCount = null; }
    }
    list.value = rows;
  } catch (e) {
    toast.error(e.message || "Failed to load opening stock entries");
  } finally {
    loading.value = false;
  }
}

async function openView(e) {
  viewDoc.value = { ...e, items: [] };
  viewOpen.value = true;
  viewLoading.value = true;
  try {
    const full = await apiGet("Stock Entry", e.name);
    if (full) viewDoc.value = full;
  } catch { /* keep list-row data */ }
  viewLoading.value = false;
}

async function submitEntry(name) {
  try {
    await apiSubmit("Stock Entry", name);
    toast.success("Opening Stock Entry submitted");
    viewOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Submit failed"); }
}

async function fetchWarehouses(q = "") {
  try {
    const co = await resolveCompany();
    const r = await apiList("Warehouse", {
      fields: ["name"],
      filters: [["company", "=", co], ["is_group", "=", 0], ...(q ? [["name", "like", `%${q}%`]] : [])],
      limit: 20,
    });
    warehouses.value = r.map(x => ({ label: x.name, value: x.name }));
  } catch { warehouses.value = []; }
}
async function fetchItems(q = "") {
  try {
    const r = await apiLinkValues("Item", q);
    items.value = r.map(x => ({ label: x.name, value: x.name }));
  } catch { items.value = []; }
}
async function onItemSelect(line, opt) {
  line.item_code = opt?.value ?? opt;
  if (!line.item_code) return;
  try {
    const r = await apiList("Item", {
      fields: ["name", "item_name", "standard_buying_rate", "standard_rate", "has_batch_no"],
      filters: [["name", "=", line.item_code]], limit: 1,
    });
    const it = r && r[0];
    if (it) {
      line.item_name = it.item_name || line.item_code;
      line.has_batch_no = it.has_batch_no ? 1 : 0;
      if (!flt(line.basic_rate)) line.basic_rate = flt(it.standard_buying_rate) || flt(it.standard_rate) || 0;
      if (line.has_batch_no && !line.batch_no) {
        line.batch_no = `${line.item_code}-OB-${new Date().toISOString().slice(0, 10).replace(/-/g, "")}`;
      }
    }
  } catch {}
}
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }

function openNew() {
  Object.assign(form, {
    posting_date: new Date().toISOString().slice(0, 10),
    to_warehouse: "", remarks: "",
  });
  lines.value = [blankLine()];
  fetchWarehouses(""); fetchItems("");
  drawerOpen.value = true;
}

async function saveEntry(submit) {
  const usable = lines.value.filter(l => l.item_code);
  if (!usable.length) return toast.error("At least one item is required");
  for (const [idx, l] of usable.entries()) {
    if (!(l.t_warehouse || form.to_warehouse))
      return toast.error(`Row ${idx + 1}: warehouse is required`);
    if (l.has_batch_no && !l.batch_no)
      return toast.error(`Row ${idx + 1}: ${l.item_code} is batch-tracked — Batch No is required`);
  }

  drawerSaving.value = true;
  try {
    const company = await resolveCompany();

    // Pre-create Batch records for batch-tracked lines so the Stock Entry
    // submit can resolve them as valid Links.
    for (const l of usable) {
      if (!l.has_batch_no || !l.batch_no) continue;
      const exists = await apiList("Batch", { fields: ["name"], filters: [["name", "=", l.batch_no]], limit: 1 });
      if (!exists.length) {
        await apiSave({
          doctype: "Batch",
          batch_no: l.batch_no,
          item: l.item_code,
          warehouse: l.t_warehouse || form.to_warehouse,
          manufacturing_date: l.manufacturing_date || null,
          expiry_date: l.expiry_date || null,
          batch_qty: flt(l.qty),
        });
      }
    }

    const doc = {
      doctype: "Stock Entry", company,
      stock_entry_type: "Opening Stock",
      posting_date: form.posting_date,
      to_warehouse: form.to_warehouse || null,
      remarks: form.remarks || "",
      items: usable.map(l => ({
        doctype: "Stock Entry Detail",
        item_code: l.item_code,
        item_name: l.item_name || l.item_code,
        qty: flt(l.qty),
        basic_rate: flt(l.basic_rate),
        t_warehouse: l.t_warehouse || form.to_warehouse || null,
        batch_no: l.batch_no || null,
      })),
    };
    const saved = await apiSave(doc);
    if (submit) await apiSubmit("Stock Entry", saved.name);
    toast.success(`Opening Stock Entry ${saved?.name || ""} ${submit ? "submitted" : "saved as draft"}`);
    drawerOpen.value = false;
    await load();
  } catch (e) {
    toast.error(e.message || "Failed to save opening stock entry");
  } finally { drawerSaving.value = false; }
}

onMounted(async () => {
  await load();
});
</script>

<style scoped>
.ob-page { display:flex; flex-direction:column; gap:14px; padding:18px; }
.ob-hint { font-size:12.5px; color:#6b7280; background:#f8fafc; border:1px solid #e5e7eb; border-radius:8px; padding:10px 14px; margin:0; }
.ob-kpi-strip { display:grid; grid-template-columns:repeat(4,1fr); gap:10px; }
.ob-kpi { display:flex; align-items:center; gap:10px; background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:12px 14px; }
.ob-kpi-ico { width:34px; height:34px; border-radius:8px; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.ob-kpi-lbl { font-size:11px; color:#6b7280; }
.ob-kpi-val { font-size:18px; font-weight:700; color:#0f172a; }

.ob-actions { display:flex; gap:10px; flex-wrap:wrap; align-items:center; justify-content:space-between; }
.ob-search-wrap { display:flex; align-items:center; gap:8px; border:1px solid #e2e8f0; border-radius:8px; padding:7px 11px; background:#fff; min-width:260px; flex:1; max-width:420px; }
.ob-search-input { border:none; outline:none; font:inherit; font-size:13px; flex:1; background:transparent; }
.ob-btn-ghost { background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:8px 12px; cursor:pointer; color:#374151; display:inline-flex; align-items:center; gap:6px; font-size:13px; }
.ob-btn-ghost:hover { background:#f8fafc; }
.ob-btn-primary { background:#2563eb; color:#fff; border:none; border-radius:8px; padding:9px 14px; cursor:pointer; font-size:13px; font-weight:600; display:inline-flex; align-items:center; gap:6px; }
.ob-btn-primary:hover { background:#1d4ed8; }
.ob-btn-primary:disabled { opacity:.6; cursor:not-allowed; }
.ob-btn-cancel { background:#fff; border:1px solid #e2e8f0; border-radius:8px; padding:9px 14px; cursor:pointer; font-size:13px; color:#374151; }
.ob-btn-save { background:#fff; border:1px solid #2563eb; color:#2563eb; border-radius:8px; padding:9px 14px; cursor:pointer; font-size:13px; font-weight:600; display:inline-flex; align-items:center; gap:6px; }
.ob-btn-save:disabled { opacity:.6; cursor:not-allowed; }

.ob-card { background:#fff; border:1px solid #e5e7eb; border-radius:10px; overflow:hidden; }
.ob-table { width:100%; border-collapse:collapse; font-size:12.5px; }
.ob-table th { background:#f9fafb; padding:9px 12px; font-size:10.5px; font-weight:700; color:#374151; text-align:left; border-bottom:1px solid #e5e7eb; text-transform:uppercase; letter-spacing:.04em; }
.ob-table td { padding:10px 12px; border-bottom:1px solid #f3f4f6; color:#111827; }
.ob-row { cursor:pointer; } .ob-row:hover td { background:#f9fafb; }
.ob-num { font-weight:600; color:#2563eb; }
.ob-wh-tag { background:#eff6ff; color:#2563eb; padding:2px 8px; border-radius:6px; font-size:11.5px; font-weight:600; }
.ob-badge { display:inline-flex; padding:3px 9px; border-radius:20px; font-size:11px; font-weight:700; }
.badge-green { background:#dcfce7; color:#16a34a; } .badge-grey { background:#f3f4f6; color:#6b7280; } .badge-orange { background:#fff7ed; color:#ea580c; }
.ob-act-btn { background:transparent; border:1px solid #e5e7eb; border-radius:6px; width:26px; height:26px; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; color:#6b7280; }
.ob-act-btn:hover { background:#eff6ff; color:#2563eb; border-color:#bfdbfe; }
.ob-empty { text-align:center; padding:36px 16px; color:#6b7280; }
.ob-shimmer { height:14px; border-radius:6px; background:linear-gradient(90deg,#f3f4f6 25%,#e9ecef 50%,#f3f4f6 75%); background-size:200% 100%; animation:ob-sh 1.4s infinite; }
@keyframes ob-sh { 0%{background-position:200% 0} 100%{background-position:-200% 0} }
.ta-r { text-align:right; } .text-muted { color:#9ca3af; } .mono-sm { font-size:12px; }

.ob-overlay { position:fixed; inset:0; background:rgba(15,23,42,.45); z-index:40; }
.ob-drawer { position:fixed; top:0; right:-560px; width:560px; max-width:92vw; height:100%; background:#fff; box-shadow:-8px 0 30px rgba(0,0,0,.15); z-index:41; display:flex; flex-direction:column; transition:right .25s ease; }
.ob-drawer.open { right:0; }
.ob-dheader { position:relative; padding:20px; background:linear-gradient(135deg,#1e3a8a,#2563eb); flex-shrink:0; }
.ob-dh-top { display:flex; align-items:center; gap:12px; }
.ob-dh-ico { width:40px; height:40px; border-radius:10px; background:rgba(255,255,255,.18); display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.ob-dh-title { font-size:16px; font-weight:700; }
.ob-dh-sub { font-size:12px; margin-top:2px; }
.ob-dclose-abs { position:absolute; top:14px; right:14px; background:rgba(255,255,255,.15); border:none; border-radius:6px; width:28px; height:28px; color:#fff; cursor:pointer; display:flex; align-items:center; justify-content:center; }
.ob-dbody { flex:1; overflow-y:auto; padding:20px; display:flex; flex-direction:column; gap:16px; }
.ob-dfooter { display:flex; align-items:center; justify-content:flex-end; gap:8px; padding:14px 20px; border-top:1px solid #e5e7eb; flex-shrink:0; background:#f9fafb; }

.ob-fields-grid { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.ob-field { display:flex; flex-direction:column; gap:4px; }
.ob-label { font-size:12px; font-weight:600; color:#374151; } .req { color:#dc2626; }
.ob-input { border:1px solid #e2e8f0; border-radius:8px; padding:8px 11px; font:inherit; font-size:13px; outline:none; background:#fff; color:#0f172a; }
.ob-input:focus { border-color:#2563eb; box-shadow:0 0 0 3px rgba(37,99,235,.1); }
.ob-input:disabled { background:#f8fafc; color:#9ca3af; }
.ob-input-req { border-color:#fca5a5; background:#fff7f7; }
.ob-section-title { font-size:11.5px; font-weight:700; color:#374151; text-transform:uppercase; letter-spacing:.05em; padding-bottom:6px; border-bottom:1px solid #f3f4f6; }
.ob-items-table { display:flex; flex-direction:column; border:1px solid #e5e7eb; border-radius:8px; overflow:hidden; overflow-x:auto; }
.ob-items-head { display:grid; grid-template-columns:1.6fr 1.2fr .7fr .8fr 1.2fr 1fr 1fr 28px; gap:6px; background:#f9fafb; padding:8px 10px; font-size:10.5px; font-weight:700; color:#374151; text-transform:uppercase; letter-spacing:.03em; min-width:760px; }
.ob-items-row { display:grid; grid-template-columns:1.6fr 1.2fr .7fr .8fr 1.2fr 1fr 1fr 28px; gap:6px; padding:8px 10px; border-top:1px solid #f3f4f6; align-items:center; min-width:760px; }
.ob-items-total { display:grid; grid-template-columns:1fr 1fr; gap:6px; padding:8px 10px; border-top:2px solid #e5e7eb; background:#f8fafc; }
.ob-add-line { background:transparent; border:none; color:#2563eb; font-size:12.5px; font-weight:600; cursor:pointer; padding:8px 10px; display:inline-flex; align-items:center; gap:6px; }
.ob-add-line:hover { background:#eff6ff; }
.ob-rm-line { background:transparent; border:1px solid #e5e7eb; border-radius:4px; width:22px; height:22px; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; color:#9ca3af; }
.ob-rm-line:hover { background:#fee2e2; color:#dc2626; border-color:#fca5a5; }

.ob-view-section { display:flex; flex-direction:column; gap:8px; }
.ob-view-sec-lbl { font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#9ca3af; }
.ob-view-items-tbl { width:100%; border-collapse:collapse; font-size:12.5px; border:1px solid #e5e7eb; border-radius:8px; overflow:hidden; }
.ob-view-items-tbl th { background:#f9fafb; padding:8px 10px; font-size:10.5px; font-weight:700; color:#374151; text-align:left; border-bottom:1px solid #e5e7eb; text-transform:uppercase; letter-spacing:.04em; }
.ob-view-items-tbl td { padding:9px 10px; border-bottom:1px solid #f3f4f6; color:#111827; }
.ob-val-box { border:1px solid #e2e8f0; border-radius:8px; padding:12px 14px; background:#f8fafc; }
.ob-val-lbl { font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:#6b7280; margin-bottom:4px; }
.ob-val-num { font-weight:700; font-size:16px; color:#7c3aed; }

.ob-mobile-cards { display:none; }
.ob-desktop-table { display:table; }
@media (max-width:768px) {
  .ob-kpi-strip { grid-template-columns:1fr 1fr; }
  .ob-kpi-value { grid-column:1/-1; }
  .ob-drawer, .ob-view-drawer { width:100% !important; max-width:100% !important; right:-100% !important; }
  .ob-drawer.open, .ob-view-drawer.open { right:0 !important; }
  .ob-desktop-table { display:none !important; }
  .ob-mobile-cards { display:flex; flex-direction:column; }
  .ob-mobile-card { background:#fff; border-bottom:1px solid #e5e7eb; padding:12px 14px; cursor:pointer; }
  .ob-mc-top { display:flex; align-items:center; justify-content:space-between; margin-bottom:6px; }
  .ob-mc-docno { font-size:12px; font-weight:700; color:#2563eb; }
  .ob-mc-meta { display:flex; justify-content:space-between; font-size:12px; color:#868e96; }
  .ob-mc-empty { text-align:center; padding:32px 16px; color:#868e96; font-size:13px; }
  .ob-add-items-desktop { display:none !important; }
  .ob-add-items-mobile { display:flex !important; flex-direction:column; }
}
.ob-add-items-mobile { display:none; flex-direction:column; gap:10px; }
.ob-aic { background:#fff; border:1px solid #e5e7eb; border-radius:10px; padding:12px 14px; display:flex; flex-direction:column; gap:10px; }
.ob-aic-header { display:flex; align-items:center; justify-content:space-between; }
.ob-aic-num { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:#6b7280; }
.ob-aic-field { display:flex; flex-direction:column; gap:4px; }
.ob-aic-amount { font-size:12px; color:#6b7280; text-align:right; border-top:1px solid #f3f4f6; padding-top:8px; }
@media (max-width:480px) {
  .ob-page { padding:12px; gap:10px; }
  .ob-fields-grid { grid-template-columns:1fr !important; }
}
</style>