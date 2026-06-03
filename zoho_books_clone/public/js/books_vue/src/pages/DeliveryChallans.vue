<template>
<div class="b-page">
  <!-- Toolbar -->
  <div class="b-action-bar">
    <div class="rec-search-wrap" style="min-width:220px">
      <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
      <input v-model="search" placeholder="Search challans, customers…" class="rec-search-input"/>
    </div>
    <div style="display:flex;gap:6px">
      <button v-for="t in TABS" :key="t.k" class="b-pill" :class="{active:tab===t.k}" @click="tab=t.k">
        {{t.l}}
        <span v-if="t.k!=='all'" class="b-pill-count">{{tabCounts[t.k]}}</span>
      </button>
    </div>
    <div style="margin-left:auto;display:flex;gap:6px">
      <button class="b-btn b-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',13)"></span> CSV</button>
      <button class="b-btn b-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',13)"></span></button>
      <button class="b-btn b-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Challan</button>
    </div>
  </div>

  <!-- ── KPI Cards ── -->
  <div class="bk-kpi-grid bk-kpi-grid-4">
    <div class="bk-kpi-card bk-kpi-accent clickable" @click="activeTab='all'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><rect x="1" y="3" width="15" height="13" rx="1"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total Challans</div><div class="bk-kpi-value">{{ list.length }}</div><div class="bk-kpi-trend" :class="dcTrends.total.up?'bk-trend-up':'bk-trend-down'">{{ dcTrends.total.up?'↑':'↓' }} {{ dcTrends.total.pct }}% vs last month</div></div></div></div>
    <div class="bk-kpi-card clickable" @click="activeTab='draft'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#f1f5f9"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Draft</div><div class="bk-kpi-value bk-kpi-amber">{{ counts.draft }}</div><div class="bk-kpi-trend bk-trend-neutral">pending</div></div></div></div>
    <div class="bk-kpi-card bk-kpi-info clickable" @click="activeTab='toDeliver'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><rect x="1" y="3" width="15" height="13" rx="1"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">To Deliver</div><div class="bk-kpi-value bk-kpi-blue">{{ counts.toDeliver }}</div><div class="bk-kpi-trend" :class="dcTrends.deliver.up?'bk-trend-up':'bk-trend-down'">{{ dcTrends.deliver.up?'↑':'↓' }} {{ dcTrends.deliver.pct }}% vs last month</div></div></div></div>
    <div class="bk-kpi-card bk-kpi-success clickable" @click="activeTab='delivered'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dcfce7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#16a34a" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Delivered</div><div class="bk-kpi-value bk-kpi-green">{{ counts.delivered }}</div><div class="bk-kpi-trend" :class="dcTrends.delivered.up?'bk-trend-up':'bk-trend-down'">{{ dcTrends.delivered.up?'↑':'↓' }} {{ dcTrends.delivered.pct }}% vs last month</div></div></div></div>
  </div>
  <div class="bk-stat-grid">
    <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month</div><div class="bk-stat-value">{{ dcThisMonth }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
    <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Delivery Rate</div><div class="bk-stat-value bk-kpi-green">{{ list.length ? Math.round(counts.delivered/list.length*100) : 0 }}%</div></div><div class="bk-stat-icon" style="background:#dcfce7;color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/></svg></div></div></div>
    <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Cancelled</div><div class="bk-stat-value bk-kpi-red">{{ counts.cancelled }}</div></div><div class="bk-stat-icon" style="background:#fee2e2;color:#dc2626"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></div></div></div>
    <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Pending Dispatch</div><div class="bk-stat-value bk-kpi-amber">{{ counts.draft + counts.toDeliver }}</div></div><div class="bk-stat-icon" style="background:#fef3c7;color:#d97706"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg></div></div></div>
  </div>

  <!-- Table -->
  <!-- Bulk action bar -->
  <div v-if="selected.size" class="inv-bulk-bar">
    <span class="inv-bulk-count">{{ selected.size }} selected</span>
    <button class="inv-bulk-btn" @click="bulkSubmit" :disabled="bulkBusy">Submit Drafts</button>
    <button class="inv-bulk-btn inv-bulk-danger" @click="bulkCancel" :disabled="bulkBusy">Cancel Submitted</button>
    <button class="inv-bulk-btn inv-bulk-danger" @click="bulkDelete" :disabled="bulkBusy">Delete Drafts</button>
    <button class="inv-bulk-btn" @click="exportCSV" :disabled="bulkBusy">
      <span v-html="icon('download',13)"></span> Export CSV
    </button>
    <button class="inv-bulk-clear" @click="selected = new Set()">✕ Clear</button>
  </div>

  <div class="b-card" style="padding:0;overflow:hidden">
    <table class="b-table">
      <thead>
        <tr>
          <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
          <th @click="sort('name')" class="sortable">Challan / SO # <span v-html="sa('name')"></span></th>
          <th @click="sort('customer_name')" class="sortable">Customer <span v-html="sa('customer_name')"></span></th>
          <th @click="sort('posting_date')" class="sortable">Date <span v-html="sa('posting_date')"></span></th>
          <th>Sales Order</th>
          <th>Status</th>
          <th class="ta-r">Qty</th>
          <th style="width:140px;text-align:center">Actions</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="loading">
          <tr v-for="n in 6" :key="n"><td colspan="8" style="padding:14px"><div class="b-shimmer" style="height:12px"></div></td></tr>
        </template>
        <tr v-else-if="!sorted.length">
          <td colspan="8" class="b-empty">{{search?'No challans match your search':'No delivery challans yet'}}</td>
        </tr>
        <tr v-else v-for="r in paged" :key="r.name" class="clickable dc-row" :class="{selected: selected.has(r.name)}" @click="openView(r)">
          <td @click.stop><input v-if="r._source==='dn'" type="checkbox" :checked="selected.has(r.name)" @change="toggle(r.name)" /></td>
          <td><span class="mono" style="font-size:12px;color:#3B5BDB">{{r.name}}</span></td>
          <td class="fw-600">{{r.customer_name||r.customer||'—'}}</td>
          <td class="c-muted" style="font-size:12.5px">{{r.posting_date||'—'}}</td>
          <td class="c-muted mono" style="font-size:12px">{{r.sales_order||r.name||'—'}}</td>
          <td><span class="b-badge" :class="statusClass(r)">{{statusLabel(r)}}</span></td>
          <td class="ta-r c-muted" style="font-size:12.5px">{{r.total_qty||'—'}}</td>
          <td @click.stop>
            <div class="dc-actions-row">
              <button class="dc-act-btn" @click.stop="openView(r)" title="View"><span v-html="icon('eye',12)"></span></button>
              <button v-if="canEdit(r)" class="dc-act-btn" @click.stop="openEdit(r)" title="Edit"><span v-html="icon('edit',12)"></span></button>
              <button v-if="r._source==='dn' && r.docstatus===0" class="dc-act-btn" @click.stop="submitOne(r)" title="Submit"><span v-html="icon('check',12)"></span></button>
              <button v-if="r._source==='dn' && r.docstatus===1 && r.status!=='Cancelled'" class="dc-act-btn dc-act-cancel" @click.stop="deleteTarget={row:r,mode:'cancel'}" title="Cancel"><span v-html="icon('x',12)"></span></button>
              <button v-if="r._source==='dn' && (r.docstatus===0 || r.docstatus===2 || r.status==='Cancelled')" class="dc-act-btn dc-act-del" @click.stop="deleteTarget={row:r,mode:'delete'}" title="Delete"><span v-html="icon('trash',12)"></span></button>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>

  <div v-if="!loading && sorted.length">
    <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
  </div>

  <!-- ===== Drawers ===== -->
  <Teleport to="body">

    <!-- VIEW DRAWER -->
    <div v-if="viewOpen" class="dc-overlay" @click.self="viewOpen=false"></div>
    <div class="dc-drawer dc-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="dc-view-head" :class="dcHeadClass(viewDoc)">
          <div class="dc-view-head-row">
            <div>
              <div class="dc-view-num">{{ viewDoc.name }}</div>
              <div class="dc-view-sub">Delivery Challan · {{ viewDoc.posting_date }}</div>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span class="b-badge" :class="statusClass(viewDoc)">{{ statusLabel(viewDoc) }}</span>
              <button class="dc-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
            </div>
          </div>
        </div>

        <div class="dc-dbody">
          <div class="dc-section">
            <div class="dc-section-hdr"><span v-html="icon('user',13)"></span><span>Customer & Date</span></div>
            <div class="dc-meta-grid">
              <div><div class="dc-meta-lbl">Customer</div><div><DocLink doctype="Customer" :name="viewDoc.customer" :mono-style="false">{{ viewDoc.customer_name||viewDoc.customer||'—' }}</DocLink></div></div>
              <div><div class="dc-meta-lbl">Date</div><div>{{ viewDoc.posting_date||'—' }}</div></div>
              <div><div class="dc-meta-lbl">LR / Tracking #</div><div class="mono">{{ viewDoc.lr_no||'—' }}</div></div>
              <div><div class="dc-meta-lbl">Transporter</div><div>{{ viewDoc.transporter_name||'—' }}</div></div>
              <div v-if="viewDoc.sales_order" style="grid-column:1/-1"><div class="dc-meta-lbl">Sales Order</div><div><DocLink doctype="Sales Order" :name="viewDoc.sales_order" /></div></div>
              <div v-if="viewDoc.shipping_address||viewDoc.customer_address" style="grid-column:1/-1"><div class="dc-meta-lbl">Delivery Address</div><div>{{ viewDoc.shipping_address||viewDoc.customer_address }}</div></div>
              <div v-if="viewDoc.remarks" style="grid-column:1/-1"><div class="dc-meta-lbl">Remarks</div><div>{{ viewDoc.remarks }}</div></div>
            </div>
          </div>

          <div class="dc-section">
            <div class="dc-section-hdr">
              <span v-html="icon('box',13)"></span><span>Items</span>
              <span style="margin-left:auto;font-size:11.5px;color:#6b7280;text-transform:none;letter-spacing:0">
                {{ (viewDoc.items||[]).length }} line{{ (viewDoc.items||[]).length!==1?'s':'' }}
              </span>
            </div>
            <table class="b-table" style="font-size:12.5px">
              <thead><tr><th>Item</th><th>Description</th><th class="ta-r">Qty</th><th>UOM</th></tr></thead>
              <tbody>
                <tr v-for="it in viewDoc.items||[]" :key="it.name||it.item_code">
                  <td>{{ it.item_name||it.item_code }}</td>
                  <td class="c-muted">{{ it.description||'—' }}</td>
                  <td class="ta-r mono">{{ it.qty }}</td>
                  <td class="c-muted">{{ it.uom||'Nos' }}</td>
                </tr>
                <tr v-if="!(viewDoc.items||[]).length"><td colspan="4" class="b-empty">No items</td></tr>
              </tbody>
            </table>
          </div>
        </div>

        <div class="dc-dfooter">
          <button class="b-btn b-btn-ghost" @click="viewOpen=false">Close</button>
          <button v-if="canEdit(viewDoc)" class="b-btn b-btn-ghost" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button v-if="viewDoc.docstatus===0" class="b-btn b-btn-primary" @click="submitChallan" :disabled="submitting">
            {{ submitting?'Submitting…':'Submit Challan' }}
          </button>
        </div>
      </template>
    </div>

    <!-- CREATE / EDIT DRAWER -->
    <div v-if="formOpen" class="dc-overlay" @click.self="formOpen=false"></div>
    <div class="dc-drawer" :class="{open:formOpen}">
      <div class="dc-dheader" :class="editingName?'edit':''">
        <div class="dc-dheader-left">
          <div class="dc-dheader-ico" :class="editingName?'edit':''">
            <span v-html="icon(editingName?'edit':'warehouse',18)"></span>
          </div>
          <div>
            <div class="dc-dheader-title">{{ editingName ? 'Edit Challan' : 'New Delivery Challan' }}</div>
            <div class="dc-dheader-sub">{{ editingName ? editingName : 'Dispatch goods to a customer' }}</div>
          </div>
        </div>
        <button class="dc-dclose" @click="formOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="dc-dbody">

        <!-- Customer & Date -->
        <div class="dc-section">
          <div class="dc-section-hdr"><span v-html="icon('user',13)"></span><span>Customer & Date</span></div>
          <div class="dc-grid">
            <div class="dc-field" style="grid-column:1/-1">
              <label class="dc-flbl">Customer <span class="req">*</span></label>
              <SearchableSelect
                v-model="form.customer"
                :options="customers"
                placeholder="Select customer…"
                :createable="true"
                createDoctype="Customer"
                @search="fetchCustomers"
                @select="onCustomerSelect"
              />
            </div>
            <div class="dc-field">
              <label class="dc-flbl">Date <span class="req">*</span></label>
              <input class="dc-input" type="date" v-model="form.posting_date"/>
            </div>
            <div class="dc-field">
              <label class="dc-flbl">Sales Order (optional)</label>
              <SearchableSelect
                v-model="form.sales_order"
                :options="salesOrders"
                placeholder="Link to Sales Order…"
                @search="fetchSalesOrders"
                @select="onSOSelect"
              />
            </div>
          </div>
        </div>

        <!-- Transport -->
        <div class="dc-section">
          <div class="dc-section-hdr"><span v-html="icon('warehouse',13)"></span><span>Transport</span></div>
          <div class="dc-grid">
            <div class="dc-field" style="grid-column:1/-1">
              <label class="dc-flbl">Dispatch Warehouse</label>
              <SearchableSelect v-model="form.set_warehouse" :options="warehouses" placeholder="Ship stock from…" @search="fetchWarehouses" />
            </div>
            <div class="dc-field">
              <label class="dc-flbl">LR / Tracking #</label>
              <input class="dc-input" v-model="form.lr_no" placeholder="e.g. LR12345"/>
            </div>
            <div class="dc-field">
              <label class="dc-flbl">Transporter</label>
              <input class="dc-input" v-model="form.transporter_name" placeholder="e.g. BlueDart, VRL"/>
            </div>
            <div class="dc-field" style="grid-column:1/-1">
              <label class="dc-flbl">Delivery Address</label>
              <input class="dc-input" v-model="form.shipping_address" :placeholder="addressLoading?'Loading…':'Shipping address'"/>
            </div>
            <div class="dc-field" style="grid-column:1/-1">
              <label class="dc-flbl">Remarks</label>
              <input class="dc-input" v-model="form.remarks" placeholder="Optional remarks"/>
            </div>
          </div>
        </div>

        <!-- Items -->
        <div class="dc-section">
          <div class="dc-section-hdr">
            <span v-html="icon('box',13)"></span><span>Items <span class="req">*</span></span>
            <span style="margin-left:auto;font-size:11.5px;color:#6b7280;text-transform:none;letter-spacing:0">
              {{ form.items.length }} line{{ form.items.length!==1?'s':'' }}
            </span>
            <button class="b-btn b-btn-ghost" style="padding:4px 10px;font-size:12px;margin-left:8px" @click="addItem">
              <span v-html="icon('plus',11)" style="vertical-align:-1px;margin-right:3px"></span> Add Item
            </button>
          </div>
          <div class="dc-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div>UOM</div><div></div>
          </div>
          <div v-for="(it,i) in form.items" :key="i" class="dc-item-row">
            <div>
              <SearchableSelect
                v-model="it.item_code"
                :options="items"
                placeholder="Select item…"
                :createable="true"
                createDoctype="Item"
                @search="fetchItems"
                @select="opt => onItemSelect(it, opt)"
              />
            </div>
            <div>
              <input class="dc-input" v-model="it.description" placeholder="Description"/>
            </div>
            <div>
              <input class="dc-input ta-r" type="number" v-model.number="it.qty" placeholder="Qty" min="0.01" step="0.01"/>
            </div>
            <div>
              <input class="dc-input" v-model="it.uom" placeholder="Nos"/>
            </div>
            <div>
              <button class="dc-rm" @click="removeItem(i)"><span v-html="icon('trash',12)"></span></button>
            </div>
          </div>
          <div v-if="!form.items.length" class="dc-items-empty">No items yet — click Add Item</div>
        </div>

      </div>

      <div class="dc-dfooter">
        <button class="b-btn b-btn-ghost" @click="formOpen=false" :disabled="saving">Cancel</button>
        <button class="b-btn b-btn-save" @click="saveChallan(0)" :disabled="saving">
          <span v-html="icon('save',13)"></span> {{ saving?'Saving…':'Save Draft' }}
        </button>
        <button class="b-btn b-btn-primary" @click="saveChallan(1)" :disabled="saving">
          <span v-html="icon('check',13)"></span> {{ saving?'Saving…':'Submit' }}
        </button>
      </div>
    </div>


    <!-- DELETE / CANCEL CONFIRM DIALOG -->
    <div v-if="deleteTarget" class="dc-overlay" style="z-index:60" @click.self="deleteTarget=null"></div>
    <div v-if="deleteTarget" class="dc-confirm" style="z-index:61">
      <div class="dc-confirm-icon" :class="deleteTarget.mode==='delete'?'danger':'warn'">
        <span v-html="icon(deleteTarget.mode==='delete'?'trash':'x', 20)"></span>
      </div>
      <div class="dc-confirm-title">
        {{ deleteTarget.mode === 'delete' ? 'Delete Challan?' : 'Cancel Challan?' }}
      </div>
      <div class="dc-confirm-sub">
        <template v-if="deleteTarget.mode==='delete'">
          <strong>{{ deleteTarget.row.name }}</strong> will be permanently deleted. This cannot be undone.
        </template>
        <template v-else>
          <strong>{{ deleteTarget.row.name }}</strong> will be cancelled and can no longer be edited.
        </template>
      </div>
      <div class="dc-confirm-actions">
        <button class="b-btn b-btn-ghost" @click="deleteTarget=null" :disabled="deleting">Keep it</button>
        <button class="b-btn" :class="deleteTarget.mode==='delete'?'dc-btn-danger':'dc-btn-warn'"
          @click="confirmDeleteAction" :disabled="deleting">
          {{ deleting ? (deleteTarget.mode==='delete'?'Deleting…':'Cancelling…') : (deleteTarget.mode==='delete'?'Yes, Delete':'Yes, Cancel') }}
        </button>
      </div>
    </div>

  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGet, apiGET, apiPOST, apiSave, apiSubmit, apiDelete, apiCancel, resolveCompany } from "../api/client.js";
import { useRoute } from "vue-router";
import { useToast } from "../composables/useToast.js";
import { useOpenFromQuery } from "../composables/useOpenFromQuery.js";
import { usePagination } from "../composables/usePagination.js";
import DocLink from "../components/DocLink.vue";
import Pagination from "../components/Pagination.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import { icon } from "../utils/icons.js";
import { flt } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const route = useRoute();

const TABS = [
  { k: "all",       l: "All" },
  { k: "draft",     l: "Draft" },
  { k: "toDeliver", l: "To Deliver" },
  { k: "delivered", l: "Delivered" },
  { k: "cancelled", l: "Cancelled" },
];

// ── State ─────────────────────────────────────────────────────────────────────
const list        = ref([]);
const loading     = ref(false);
const search      = ref("");
const tab         = ref("all");
const sortCol     = ref("posting_date");
const sortDir     = ref("desc");
const selected    = ref(new Set());
const bulkBusy    = ref(false);

const viewOpen    = ref(false);
const viewDoc     = ref(null);
const submitting  = ref(false);
const deleteTarget = ref(null);  // { row, mode: "delete"|"cancel" }
const deleting     = ref(false);

const formOpen    = ref(false);
const editingName = ref("");
const saving      = ref(false);
const addressLoading = ref(false);

// Dropdown option lists
const customers  = ref([]);
const items      = ref([]);
const warehouses = ref([]);
const salesOrders = ref([]);

let _lineId = 1;
const blankItem = () => ({ _id: _lineId++, item_code: "", item_name: "", description: "", qty: 1, uom: "Nos" });

const form = reactive({
  customer: "",
  customer_name: "",
  posting_date: new Date().toISOString().slice(0, 10),
  sales_order: "",
  set_warehouse: "",
  lr_no: "",
  transporter_name: "",
  shipping_address: "",
  remarks: "",
  items: [],
});

// ── Counts ────────────────────────────────────────────────────────────────────
const counts = computed(() => ({
  draft:     list.value.filter(r => r.docstatus === 0).length,
  toDeliver: list.value.filter(r => r.docstatus === 1 && r.status !== "Delivered" && r.status !== "Fully Delivered").length,
  delivered: list.value.filter(r => r.status === "Delivered" || r.status === "Fully Delivered").length,
  cancelled: list.value.filter(r => r.docstatus === 2 || r.status === "Cancelled").length,
}));
const _dcYM  = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _dcLYM = () => { const d=new Date(); d.setMonth(d.getMonth()-1); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _dcTr  = (a,b) => { if(!b&&!a) return {pct:0,up:true}; if(!b) return {pct:100,up:true}; const p=Math.round((a-b)/b*100); return {pct:Math.abs(p),up:p>=0}; };
const dcThisMonth = computed(()=>list.value.filter(r=>(r.posting_date||'').startsWith(_dcYM())).length);
const dcTrends = computed(()=>({
  total:     _dcTr(dcThisMonth.value, list.value.filter(r=>(r.posting_date||'').startsWith(_dcLYM())).length),
  deliver:   _dcTr(counts.value.toDeliver, list.value.filter(r=>(r.posting_date||'').startsWith(_dcLYM())&&r.docstatus===1&&r.status!=="Delivered"&&r.status!=="Fully Delivered").length),
  delivered: _dcTr(counts.value.delivered, list.value.filter(r=>(r.posting_date||'').startsWith(_dcLYM())&&(r.status==="Delivered"||r.status==="Fully Delivered")).length),
}));

const tabCounts = computed(() => ({
  draft:     counts.value.draft,
  toDeliver: counts.value.toDeliver,
  delivered: counts.value.delivered,
  cancelled: counts.value.cancelled,
}));

// ── Status helpers ────────────────────────────────────────────────────────────
function statusLabel(r) {
  if (r.docstatus === 2 || r.status === "Cancelled") return "Cancelled";
  if (r.status === "Delivered" || r.status === "Fully Delivered") return "Delivered";
  if (r.status === "Partially Delivered") return "Partial";
  if (r.docstatus === 1) return "To Deliver";
  return "Draft";
}
function statusClass(r) {
  if (r.docstatus === 2 || r.status === "Cancelled") return "b-badge-muted";
  if (r.status === "Delivered" || r.status === "Fully Delivered") return "b-badge-green";
  if (r.status === "Partially Delivered") return "b-badge-yellow";
  if (r.docstatus === 1) return "b-badge-blue";
  return "b-badge-orange";
}
function dcHeadClass(r) {
  if (r.docstatus === 2 || r.status === "Cancelled") return "cancelled";
  if (r.status === "Delivered" || r.status === "Fully Delivered") return "delivered";
  return "";
}
function canEdit(r) {
  return r.docstatus === 0;
}

// ── Load ──────────────────────────────────────────────────────────────────────
async function load() {
  loading.value = true;
  try {
    const company = await resolveCompany();

    // 1) Real Delivery Notes (submitted doctype)
    const dnRows = await apiList("Delivery Note", {
      fields: ["name", "customer", "customer_name", "posting_date", "delivery_date",
               "sales_order", "status", "total_qty", "lr_no", "transporter_name", "docstatus"],
      filters: [["company", "=", company]],
      limit: 500,
      order: "posting_date desc",
    }).catch(() => []);

    // 2) Sales Orders that are Submitted and not yet fully delivered
    //    (docstatus=1 = Submitted in Frappe; status can be "To Deliver", "Partially Delivered", etc.)
    const soRows = await apiList("Sales Order", {
      fields: ["name", "customer", "customer_name", "transaction_date", "delivery_date",
               "status", "grand_total", "docstatus"],
      filters: [
        ["company", "=", company],
        ["status", "in", ["To Deliver", "Partially Delivered", "Submitted"]],
      ],
      limit: 500,
      order: "transaction_date desc",
    }).catch(() => []);

    // Normalise DN rows
    const dnNormalised = dnRows.map(r => ({
      _source:       "dn",
      name:          r.name,
      customer:      r.customer,
      customer_name: r.customer_name,
      posting_date:  r.posting_date || r.delivery_date,
      sales_order:   r.sales_order || "",
      lr_no:         r.lr_no || "",
      transporter_name: r.transporter_name || "",
      status:        r.status || (r.docstatus === 1 ? "To Deliver" : "Draft"),
      docstatus:     r.docstatus,
      total_qty:     flt(r.total_qty),
    }));

    // Sales Orders — only include those that don't already have a matching DN
    const dnSONames = new Set(dnNormalised.map(r => r.sales_order).filter(Boolean));
    const soNormalised = soRows
      .filter(r => !dnSONames.has(r.name))
      .map(r => ({
        _source:       "so",
        name:          r.name,          // SO name shown as the "challan" reference
        customer:      r.customer,
        customer_name: r.customer_name,
        posting_date:  r.delivery_date || r.transaction_date,
        sales_order:   r.name,
        lr_no:         "",
        transporter_name: "",
        status:        r.status === "Partially Delivered" ? "Partially Delivered" : "To Deliver",
        docstatus:     1,
        total_qty:     null,
      }));

    list.value = [...dnNormalised, ...soNormalised];
  } catch (e) {
    console.warn("DC load failed:", e.message);
    list.value = [];
  } finally {
    loading.value = false;
  }
}

// ── Filtering / sorting ───────────────────────────────────────────────────────
const filtered = computed(() => {
  let r = list.value;
  if (tab.value === "draft")     r = r.filter(x => x.docstatus === 0);
  else if (tab.value === "toDeliver") r = r.filter(x => x.docstatus === 1 && x.status !== "Delivered" && x.status !== "Fully Delivered");
  else if (tab.value === "delivered") r = r.filter(x => x.status === "Delivered" || x.status === "Fully Delivered");
  else if (tab.value === "cancelled") r = r.filter(x => x.docstatus === 2 || x.status === "Cancelled");
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x =>
      (x.name || "").toLowerCase().includes(q) ||
      (x.customer_name || x.customer || "").toLowerCase().includes(q) ||
      (x.sales_order || "").toLowerCase().includes(q)
    );
  }
  return r;
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const av = a[col] ?? "", bv = b[col] ?? "";
    const c = typeof av === "number" ? av - bv : String(av).localeCompare(String(bv));
    return sortDir.value === "asc" ? c : -c;
  });
});

const { page, pageSize, paged } = usePagination(sorted, { storageKey: "delivery-challans" });

function sort(col) {
  if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  else { sortCol.value = col; sortDir.value = "asc"; }
}
function sa(col) {
  if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>';
  return sortDir.value === "asc" ? "↑" : "↓";
}

// ── View ──────────────────────────────────────────────────────────────────────
async function openView(r) {
  viewOpen.value = true;
  viewDoc.value = { ...r, items: [] };
  try {
    if (r._source === "dn") {
      // Real Delivery Note — fetch full doc
      const doc = await apiGet("Delivery Note", r.name);
      viewDoc.value = { ...r, items: doc?.items || [], remarks: doc?.remarks || r.remarks || "" };
    } else {
      // Sales Order — fetch delivered lines
      const lines = await apiGET("zoho_books_clone.api.docs.get_delivery_challan_lines", { sales_order: r.name }).catch(() => []);
      viewDoc.value = { ...r, items: lines || [] };
    }
  } catch (e) {
    console.warn("DC view load failed:", e.message);
  }
}

async function submitChallan() {
  if (!viewDoc.value) return;
  submitting.value = true;
  try {
    await apiSubmit("Delivery Note", viewDoc.value.name);
    toast.success("Challan submitted");
    viewOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Submit failed"); }
  finally { submitting.value = false; }
}

// ── Selection + bulk actions ──────────────────────────────────────────────────
const allChecked = computed(() => {
  const dnRows = sorted.value.filter(r => r._source === "dn");
  return dnRows.length > 0 && dnRows.every(r => selected.value.has(r.name));
});
function toggle(name) {
  const s = new Set(selected.value);
  s.has(name) ? s.delete(name) : s.add(name);
  selected.value = s;
}
function toggleAll(e) {
  selected.value = e.target.checked
    ? new Set(sorted.value.filter(r => r._source === "dn").map(r => r.name))
    : new Set();
}
function selectedRows() {
  return sorted.value.filter(r => r._source === "dn" && selected.value.has(r.name));
}
async function submitOne(r) {
  try {
    await apiSubmit("Delivery Note", r.name);
    toast.success(`${r.name} submitted`);
    await load();
  } catch (e) { toast.error(e.message || "Submit failed"); }
}
async function bulkSubmit() {
  const rows = selectedRows().filter(r => r.docstatus === 0);
  if (!rows.length) { toast.error("No draft challans selected"); return; }
  bulkBusy.value = true;
  let ok = 0, fail = 0;
  for (const r of rows) {
    try { await apiSubmit("Delivery Note", r.name); ok++; } catch { fail++; }
  }
  bulkBusy.value = false;
  toast.success(`${ok} submitted${fail?`, ${fail} failed`:''}`);
  selected.value = new Set();
  await load();
}
async function bulkCancel() {
  const rows = selectedRows().filter(r => r.docstatus === 1 && r.status !== "Cancelled");
  if (!rows.length) { toast.error("No submitted challans selected"); return; }
  bulkBusy.value = true;
  let ok = 0, fail = 0;
  for (const r of rows) {
    try { await apiCancel("Delivery Note", r.name); ok++; } catch { fail++; }
  }
  bulkBusy.value = false;
  toast.success(`${ok} cancelled${fail?`, ${fail} failed`:''}`);
  selected.value = new Set();
  await load();
}
async function bulkDelete() {
  const rows = selectedRows().filter(r => r.docstatus === 0 || r.docstatus === 2 || r.status === "Cancelled");
  if (!rows.length) { toast.error("Only drafts and cancelled rows can be deleted"); return; }
  bulkBusy.value = true;
  let ok = 0, fail = 0;
  for (const r of rows) {
    try { await apiDelete("Delivery Note", r.name); ok++; } catch { fail++; }
  }
  bulkBusy.value = false;
  toast.success(`${ok} deleted${fail?`, ${fail} failed`:''}`);
  selected.value = new Set();
  await load();
}
function exportCSV() {
  // Selection-aware: if rows are selected export those, else export filtered view.
  // Only "real" DN rows (not derived SO rows) are exported — derived rows
  // don't have transporter/LR data anyway.
  const source = selected.value.size
    ? sorted.value.filter(r => r._source === "dn" && selected.value.has(r.name))
    : sorted.value.filter(r => r._source === "dn");
  if (!source.length) { toast.error("Nothing to export"); return; }
  const headers = ["Challan #","Customer","Date","Sales Order","Status","Qty","LR / Tracking","Transporter"];
  const lines = source.map(r => [
    r.name, r.customer_name || r.customer || "", r.posting_date || "",
    r.sales_order || "", statusLabel(r), r.total_qty || "",
    r.lr_no || "", r.transporter_name || "",
  ]);
  const esc = v => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const csv = "﻿" + [headers, ...lines].map(r => r.map(esc).join(",")).join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `delivery-challans-${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  toast.success(`${source.length} row(s) exported`);
}

// ── Open New / Edit ───────────────────────────────────────────────────────────
function resetForm() {
  Object.assign(form, {
    customer: "",
    customer_name: "",
    posting_date: new Date().toISOString().slice(0, 10),
    sales_order: "",
    set_warehouse: "",
    lr_no: "",
    transporter_name: "",
    shipping_address: "",
    remarks: "",
    items: [blankItem()],
  });
}

function openNew() {
  editingName.value = "";
  resetForm();
  fetchCustomers("");
  fetchItems("");
  fetchWarehouses("");
  fetchSalesOrders("");
  formOpen.value = true;
}

async function openEdit(r) {
  editingName.value = r.name;
  resetForm();
  fetchCustomers("");
  fetchItems("");
  fetchWarehouses("");
  fetchSalesOrders("");
  formOpen.value = true;

  // Pre-fill from existing doc
  Object.assign(form, {
    customer:          r.customer || "",
    customer_name:     r.customer_name || r.customer || "",
    posting_date:      r.posting_date || new Date().toISOString().slice(0, 10),
    sales_order:       r.sales_order || "",
    lr_no:             r.lr_no || "",
    transporter_name:  r.transporter_name || "",
    shipping_address:  r.shipping_address || "",
    remarks:           r.remarks || "",
    items:             [],
  });

  if (r._source === "dn") {
    try {
      const doc = await apiGet("Delivery Note", r.name);
      form.items = (doc?.items || []).map(it => ({
        _id:         _lineId++,
        item_code:   it.item_code || "",
        item_name:   it.item_name || "",
        description: it.description || "",
        qty:         flt(it.qty) || 1,
        uom:         it.uom || "Nos",
      }));
      if (doc?.remarks) form.remarks = doc.remarks;
    } catch {}
  } else if (r._source === "so") {
    try {
      const lines = await apiGET("zoho_books_clone.api.docs.get_delivery_challan_lines", { sales_order: r.name }).catch(() => []);
      form.items = (lines || []).map(it => ({
        _id:         _lineId++,
        item_code:   it.item_code || "",
        item_name:   it.item_name || "",
        description: it.description || "",
        qty:         flt(it.delivered_qty || it.qty) || 1,
        uom:         it.uom || "Nos",
      }));
    } catch {}
  }
  if (!form.items.length) form.items = [blankItem()];
}

// ── Dropdown fetchers ─────────────────────────────────────────────────────────
async function fetchCustomers(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["customer_name", "like", "%" + q + "%"]);
    const r = await apiList("Customer", {
      fields: ["name", "customer_name"],
      filters: f, limit: 30, order: "customer_name asc",
    });
    customers.value = (r || []).map(x => ({ ...x, label: x.customer_name || x.name, value: x.name }));
  } catch { customers.value = []; }
}

async function fetchWarehouses(q = "") {
  try {
    const co = await resolveCompany();
    const r = await apiList("Warehouse", {
      fields: ["name", "parent_warehouse"],
      filters: [["company", "=", co], ["is_group", "=", 0], ...(q ? [["name", "like", `%${q}%`]] : [])],
      limit: 30,
    });
    warehouses.value = r.map(x => ({ label: x.parent_warehouse ? `${x.parent_warehouse} / ${x.name}` : x.name, value: x.name }));
  } catch { warehouses.value = []; }
}

async function fetchItems(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["item_name", "like", "%" + q + "%"]);
    const r = await apiList("Item", {
      fields: ["name", "item_name", "stock_uom", "description"],
      filters: f, limit: 30, order: "item_name asc",
    });
    items.value = (r || []).map(x => ({
      ...x,
      label: x.item_name || x.name,
      value: x.name,
      uom: x.stock_uom || "Nos",
      description: x.description || "",
    }));
  } catch { items.value = []; }
}

async function fetchSalesOrders(q = "") {
  try {
    const f = [];
    if (form.customer) f.push(["customer", "=", form.customer]);
    if (q) f.push(["name", "like", "%" + q + "%"]);
    const r = await apiList("Sales Order", {
      fields: ["name", "customer", "customer_name", "delivery_date", "status"],
      filters: f, limit: 30, order: "transaction_date desc",
    });
    salesOrders.value = (r || []).map(x => ({
      ...x,
      label: x.name + (x.customer_name ? " · " + x.customer_name : ""),
      value: x.name,
    }));
  } catch { salesOrders.value = []; }
}

// ── Customer select: auto-fill address + filter SO list ───────────────────────
async function onCustomerSelect(opt) {
  const custName = opt?.value ?? opt;
  form.customer_name = opt?.label ?? opt?.customer_name ?? custName ?? "";
  form.sales_order = "";
  salesOrders.value = [];
  if (!custName) return;

  addressLoading.value = true;
  fetchSalesOrders("");
  try {
    const custDoc = await apiGet("Customer", custName);
    const shipFields = [
      custDoc?.ship_address_line1, custDoc?.ship_address_line2,
      custDoc?.ship_city, custDoc?.ship_state, custDoc?.ship_pincode, custDoc?.ship_country,
    ];
    const billFields = [
      custDoc?.address_line1, custDoc?.address_line2,
      custDoc?.city, custDoc?.state, custDoc?.pincode, custDoc?.country,
    ];
    const built = shipFields.filter(Boolean).join(", ") || billFields.filter(Boolean).join(", ");
    if (built) form.shipping_address = built;
  } catch {}
  addressLoading.value = false;
}

// ── SO select: pull items from Sales Order ────────────────────────────────────
async function onSOSelect(opt) {
  const soName = opt?.value ?? opt;
  if (!soName) return;
  try {
    const so = await apiGet("Sales Order", soName);
    if (!form.customer && so?.customer) {
      form.customer = so.customer;
      form.customer_name = so.customer_name || so.customer;
      await onCustomerSelect({ value: so.customer, label: so.customer_name || so.customer });
    }
    if (so?.items?.length) {
      form.items = so.items.map(it => ({
        _id:         _lineId++,
        item_code:   it.item_code || "",
        item_name:   it.item_name || it.item_code || "",
        description: it.description || "",
        qty:         flt(Math.max(0, flt(it.qty) - flt(it.delivered_qty))) || flt(it.qty) || 1,
        uom:         it.uom || "Nos",
      })).filter(it => it.qty > 0);
      if (!form.items.length) form.items = [blankItem()];
      toast.success(`Loaded ${so.items.length} item(s) from ${soName}`);
    }
    if (so?.delivery_date) form.posting_date = so.delivery_date;
  } catch {}
}

// ── Item select: auto-fill UOM + description ──────────────────────────────────
function onItemSelect(line, opt) {
  const code = opt?.value ?? opt;
  line.item_code = code;
  const found = items.value.find(i => i.value === code || i.name === code);
  if (found) {
    if (found.uom)         line.uom = found.uom;
    if (found.description) line.description = found.description;
    line.item_name = found.label || found.item_name || code;
  }
}

function addItem() { form.items.push(blankItem()); }
function removeItem(i) { if (form.items.length > 1) form.items.splice(i, 1); }

// ── Save ──────────────────────────────────────────────────────────────────────
async function saveChallan(submit) {
  if (!form.customer) { toast.error("Customer is required"); return; }
  const validItems = form.items.filter(it => it.item_code && flt(it.qty) > 0);
  if (!validItems.length) { toast.error("At least one item with qty > 0 is required"); return; }

  saving.value = true;
  try {
    const company = await resolveCompany();
    const doc = {
      doctype:          "Delivery Note",
      company,
      customer:         form.customer,
      customer_name:    form.customer_name || form.customer,
      posting_date:     form.posting_date,
      sales_order:      form.sales_order || undefined,
      set_warehouse:    form.set_warehouse || "",
      lr_no:            form.lr_no || "",
      transporter_name: form.transporter_name || "",
      shipping_address: form.shipping_address || "",
      remarks:          form.remarks || "",
      items: validItems.map(it => ({
        doctype:    "Delivery Note Item",
        item_code:  it.item_code,
        item_name:  it.item_name || it.item_code,
        description:it.description || "",
        qty:        flt(it.qty),
        uom:        it.uom || "Nos",
        stock_uom:  it.uom || "Nos",
        conversion_factor: 1,
        warehouse:  it.warehouse || form.set_warehouse || "",
      })),
    };
    if (editingName.value) doc.name = editingName.value;

    const saved = await apiSave(doc);
    if (submit && saved?.name) await apiSubmit("Delivery Note", saved.name);

    toast.success(`Challan ${saved?.name || ""} ${submit ? "submitted" : "saved"}`);
    formOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save"); }
  finally { saving.value = false; }
}

// ── Delete / Cancel ───────────────────────────────────────────────────────────
async function confirmDeleteAction() {
  if (!deleteTarget.value) return;
  const { row, mode } = deleteTarget.value;
  deleting.value = true;
  try {
    if (mode === "delete") {
      await apiDelete("Delivery Note", row.name);
      toast.success(`Challan ${row.name} deleted`);
    } else {
      await apiCancel("Delivery Note", row.name);
      toast.success(`Challan ${row.name} cancelled`);
    }
    deleteTarget.value = null;
    await load();
  } catch (e) {
    toast.error(e.message || (mode === "delete" ? "Delete failed" : "Cancel failed"));
  } finally {
    deleting.value = false;
  }
}

onMounted(async () => {
  await load();
  useOpenFromQuery({
    route,
    openByName: (n) => openView(list.value.find(x => x.name === n) || { name: n }),
  });
});
</script>

<style scoped>
.rec-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;}
.rec-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.sortable{cursor:pointer;user-select:none;}.sortable:hover{color:#2563eb;}
.dc-strip-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px}
.dc-strip-val{font-size:20px;font-weight:700;font-family:monospace}

/* Badges */
.b-badge-yellow{background:#fff9db;color:#e67700;border:1px solid #ffe066;}
.b-pill-count{background:#e5e7eb;color:#6b7280;padding:1px 7px;border-radius:999px;font-size:11px;font-weight:700;}
.b-pill.active .b-pill-count{background:#2563eb;color:#fff;}

/* Row */
.dc-row:hover td{background:#f9fafb;}
.dc-act-btn{background:#ffffff;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;font:inherit;font-size:14px;margin:0 2px;}
.dc-act-btn:hover{background:#e5e7eb;color:#2563eb;}
.dc-actions-row{display:flex;align-items:center;justify-content:center;gap:4px;flex-wrap:nowrap;}
.dc-act-del:hover{background:#fef2f2 !important;border-color:#fecaca !important;color:#dc2626 !important;}
.dc-act-cancel:hover{background:#fffbeb !important;border-color:#fde68a !important;color:#d97706 !important;}
.dc-confirm{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;border-radius:16px;padding:28px 28px 22px;box-shadow:0 20px 60px rgba(15,23,42,.18);z-index:61;width:340px;max-width:92vw;display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center;}
.dc-confirm-icon{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:4px;}
.dc-confirm-icon.danger{background:#fee2e2;color:#dc2626;}
.dc-confirm-icon.warn{background:#fffbeb;color:#d97706;}
.dc-confirm-title{font-size:16px;font-weight:700;color:#111827;}
.dc-confirm-sub{font-size:13px;color:#6b7280;line-height:1.5;}
.dc-confirm-actions{display:flex;gap:8px;margin-top:6px;width:100%;}
.dc-confirm-actions .b-btn{flex:1;justify-content:center;}
.dc-btn-danger{background:#dc2626;border:1px solid #dc2626;color:#fff;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:6px;}
.dc-btn-danger:hover{background:#b91c1c;}
.dc-btn-danger:disabled,.dc-btn-warn:disabled{opacity:.5;cursor:not-allowed;}
.dc-btn-warn{background:#d97706;border:1px solid #d97706;color:#fff;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:6px;}
.dc-btn-warn:hover{background:#b45309;}
.dc-act-del:hover{background:#fef2f2 !important;border-color:#fecaca !important;color:#dc2626 !important;}
.dc-act-cancel:hover{background:#fffbeb !important;border-color:#fde68a !important;color:#d97706 !important;}

/* Confirm dialog */
.dc-confirm{position:fixed;top:50%;left:50%;transform:translate(-50%,-50%);background:#fff;border-radius:16px;padding:28px 28px 22px;box-shadow:0 20px 60px rgba(15,23,42,.18);z-index:61;width:340px;max-width:92vw;display:flex;flex-direction:column;align-items:center;gap:10px;text-align:center;}
.dc-confirm-icon{width:52px;height:52px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-bottom:4px;}
.dc-confirm-icon.danger{background:#fee2e2;color:#dc2626;}
.dc-confirm-icon.warn{background:#fffbeb;color:#d97706;}
.dc-confirm-title{font-size:16px;font-weight:700;color:#111827;}
.dc-confirm-sub{font-size:13px;color:#6b7280;line-height:1.5;}
.dc-confirm-actions{display:flex;gap:8px;margin-top:6px;width:100%;}
.dc-confirm-actions .b-btn{flex:1;justify-content:center;}
.dc-btn-danger{background:#dc2626;border:1px solid #dc2626;color:#fff;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:6px;}
.dc-btn-danger:hover{background:#b91c1c;border-color:#b91c1c;}
.dc-btn-danger:disabled{opacity:.5;cursor:not-allowed;}
.dc-btn-warn{background:#d97706;border:1px solid #d97706;color:#fff;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;display:inline-flex;align-items:center;justify-content:center;gap:6px;}
.dc-btn-warn:hover{background:#b45309;border-color:#b45309;}
.dc-btn-warn:disabled{opacity:.5;cursor:not-allowed;}

/* Drawer */
.dc-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);backdrop-filter:blur(2px);z-index:40;}
.dc-drawer{position:fixed;top:0;right:-620px;bottom:0;width:620px;max-width:96vw;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-12px 0 32px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s cubic-bezier(.32,.72,0,1);}
.dc-drawer.open{right:0;}
.dc-view-drawer{width:560px;right:-560px;}.dc-view-drawer.open{right:0;}

.dc-dheader{display:flex;align-items:flex-start;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.dc-dheader.edit{background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);}
.dc-dheader-left{display:flex;align-items:flex-start;gap:12px;}
.dc-dheader-ico{width:38px;height:38px;border-radius:10px;background:#fff;border:1px solid rgba(37,99,235,.18);display:inline-flex;align-items:center;justify-content:center;color:#2563eb;box-shadow:0 1px 3px rgba(15,23,42,.06);flex-shrink:0;}
.dc-dheader-ico.edit{color:#ca8a04;border-color:rgba(202,138,4,.25);}
.dc-dheader-title{font-size:15px;font-weight:700;color:#111827;letter-spacing:-0.01em;}
.dc-dheader-sub{font-size:12px;color:#475569;margin-top:3px;font-weight:500;}
.dc-dclose{background:rgba(255,255,255,.6);border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;transition:background .15s;}
.dc-dclose:hover{background:#fff;color:#111827;}

.dc-view-head{padding:18px 20px;border-bottom:1px solid #e5e7eb;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);flex-shrink:0;}
.dc-view-head.delivered{background:linear-gradient(135deg,#f0fdf4 0%,#bbf7d0 100%);}
.dc-view-head.cancelled{background:linear-gradient(135deg,#f3f4f6 0%,#e5e7eb 100%);}
.dc-view-head-row{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;}
.dc-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.dc-view-sub{font-size:12.5px;color:#475569;margin-top:2px;}

.dc-dbody{flex:1;overflow-y:auto;padding:18px 20px;display:flex;flex-direction:column;gap:14px;background:#f8fafc;}
.dc-section{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:12px;box-shadow:0 1px 2px rgba(15,23,42,.03);}
.dc-section-hdr{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#0f172a;}
.dc-section-hdr svg{color:#2563eb;}
.dc-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.dc-field{display:flex;flex-direction:column;gap:4px;}
.dc-flbl{font-size:12px;font-weight:600;color:#374151;}
.dc-input{border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;transition:border-color .15s,box-shadow .15s;width:100%;box-sizing:border-box;}
.dc-input:hover:not(:disabled){border-color:#cbd5e1;}
.dc-input:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12);}
.req{color:#dc2626;}

/* Items table in form */
.dc-items-head{display:grid;grid-template-columns:2fr 2fr 80px 80px 32px;gap:8px;background:#f9fafb;padding:6px 10px;border-radius:6px 6px 0 0;font-size:11.5px;font-weight:600;color:#374151;border:1px solid #e5e7eb;border-bottom:none;}
.dc-item-row{display:grid;grid-template-columns:2fr 2fr 80px 80px 32px;gap:8px;padding:6px 0;border-top:1px solid #f3f4f6;align-items:center;}
.dc-rm{background:#fef2f2;border:1px solid #fecaca;border-radius:6px;cursor:pointer;color:#dc2626;height:32px;width:32px;display:inline-flex;align-items:center;justify-content:center;}
.dc-rm:hover{background:#fee2e2;}
.dc-items-empty{font-size:12px;color:#868E96;text-align:center;padding:14px;background:#f9fafb;border:1px dashed #e5e7eb;border-radius:8px;}

.dc-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.dc-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.04em;margin-bottom:3px;font-weight:600;}

.dc-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;background:#fff;flex-shrink:0;flex-wrap:wrap;}
.b-btn-save{display:inline-flex;align-items:center;gap:6px;background:#f0fdf4;border:1px solid #16a34a;color:#16a34a;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.b-btn-save:hover{background:#dcfce7;}
.b-btn-save:disabled{opacity:.5;cursor:not-allowed;}
.mono{font-family:monospace;}
.ta-r{text-align:right;}
.fw-600{font-weight:600;}
.c-muted{color:#6b7280;}
</style>