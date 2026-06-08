<template>
  <div class="list-page">

    <!-- ── Toolbar ── -->
    <div class="sales-toolbar">
      <div class="sales-search">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search POs, vendors…" class="sales-search-input" />
      </div>
      <div class="sales-pills">
        <button v-for="t in tabs" :key="t.key"
          class="sales-pill" :class="{active:activeTab===t.key, ['pill-'+t.key]: t.key!=='all'}"
          @click="activeTab=t.key">
          {{ t.label }}
          <span v-if="t.key!=='all'" class="sales-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div style="display:flex;align-items:center;gap:8px;flex-shrink:0;flex-wrap:nowrap;">
        <button class="sales-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="sales-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="sales-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Purchase Order
        </button>
      </div>
    </div>

    <!-- ── KPI Cards ── -->
    <div class="bk-kpi-grid">
      <div class="bk-kpi-card bk-kpi-accent clickable" @click="activeTab='all'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total POs</div><div class="bk-kpi-value">{{ list.length }}</div><div class="bk-kpi-trend" :class="poTrends.total.up?'bk-trend-up':'bk-trend-down'">{{ poTrends.total.up?'↑':'↓' }} {{ poTrends.total.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card clickable" @click="activeTab='draft'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#e2e8f0"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Draft</div><div class="bk-kpi-value">{{ counts.draft }}</div><div class="bk-kpi-trend" :class="poTrends.draft.up?'bk-trend-up':'bk-trend-down'">{{ poTrends.draft.up?'↑':'↓' }} {{ poTrends.draft.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-warn clickable" @click="activeTab='toReceive'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#fef3c7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="1.8"><rect x="1" y="3" width="15" height="13" rx="1"/><polygon points="16 8 20 8 23 11 23 16 16 16 16 8"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">To Receive</div><div class="bk-kpi-value bk-kpi-amber">{{ counts.toReceive }}</div><div class="bk-kpi-trend" :class="poTrends.receive.up?'bk-trend-up':'bk-trend-down'">{{ poTrends.receive.up?'↑':'↓' }} {{ poTrends.receive.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-info clickable" @click="activeTab='toBill'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#cffafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#0891b2" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">To Bill</div><div class="bk-kpi-value bk-kpi-blue">{{ counts.toBill }}</div><div class="bk-kpi-trend" :class="poTrends.bill.up?'bk-trend-up':'bk-trend-down'">{{ poTrends.bill.up?'↑':'↓' }} {{ poTrends.bill.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-danger clickable" @click="activeTab='cancelled'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#fee2e2"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Cancelled</div><div class="bk-kpi-value bk-kpi-red">{{ counts.cancelled }}</div><div class="bk-kpi-trend" :class="poTrends.cancelled.up?'bk-trend-down':'bk-trend-up'">{{ poTrends.cancelled.up?'↑':'↓' }} {{ poTrends.cancelled.pct }}% vs last month</div></div></div></div>
    </div>
    <div class="bk-stat-grid">
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month</div><div class="bk-stat-value">{{ poThisMonth.count }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month Value</div><div class="bk-stat-value bk-kpi-blue" style="font-size:16px">{{ fmtCur(poThisMonth.value) }}</div></div><div class="bk-stat-icon" style="background:#cffafe;color:#0891b2"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Procurement Value</div><div class="bk-stat-value bk-kpi-green" style="font-size:16px">{{ fmtCur(summary.totalValue) }}</div></div><div class="bk-stat-icon" style="background:#dcfce7;color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Closed</div><div class="bk-stat-value bk-kpi-green">{{ counts.closed }}</div></div><div class="bk-stat-icon" style="background:#dcfce7;color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#16a34a" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div></div></div>
    </div>

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button class="bab-danger" @click="bulkDelete">Delete</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="inv-table-wrap">
      <table class="inv-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">PO # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('supplier_name')" class="sortable">Vendor <span v-html="sortArrow('supplier_name')"></span></th>
            <th @click="sortBy('transaction_date')" class="sortable">Date <span v-html="sortArrow('transaction_date')"></span></th>
            <th @click="sortBy('expected_delivery_date')" class="sortable">Expected <span v-html="sortArrow('expected_delivery_date')"></span></th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="8"><div class="shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="o in paged" :key="o.name" class="inv-row" :class="{selected:selected.has(o.name)}">
              <td><input type="checkbox" :checked="selected.has(o.name)" @change="toggle(o.name)" /></td>
              <td @click="openView(o)"><span class="inv-link">{{ o.name }}</span></td>
              <td @click="openView(o)">{{ o.supplier_name || o.supplier || '—' }}</td>
              <td @click="openView(o)" class="text-muted mono-sm">{{ fmtDate(o.transaction_date) }}</td>
              <td @click="openView(o)" :class="isPastExpected(o)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(o.expected_delivery_date)||'—' }}</td>
              <td @click="openView(o)"><span class="inv-status-badge" :class="badgeClass(o)">{{ displayStatus(o) }}</span></td>
              <td @click="openView(o)" class="ta-r mono-sm">{{ fmtCur(o.grand_total) }}</td>
              <td class="po-act-cell">
                <button class="inv-act-btn" @click="openView(o)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="canEdit(o)" class="inv-act-btn" @click="openEdit(o)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button class="inv-act-btn po-act-conv" v-if="canBill(o)" @click="openBillModal(o)" title="Bill"><span v-html="icon('arrow-right',13)"></span></button>
                <button v-if="canDelete(o)" class="inv-act-btn po-act-del" @click="deletePO(o)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="po-empty">No purchase orders match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Pagination ── -->
    <div v-if="!loading && sorted.length" style="padding:12px 4px 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ── Create / Edit Drawer ── -->
    <div v-if="drawerOpen" class="inv-drawer-bg" @click.self="drawerOpen=false"></div>
    <div class="inv-drawer-panel" :class="{open:drawerOpen}">

      <!-- Header -->
      <div class="inv-dh">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <div class="inv-dh-title">{{ editingName ? 'Edit Purchase Order' : 'New Purchase Order' }}</div>
          <span v-if="!editingName" class="po-draft-badge">Draft</span>
        </div>
        <button class="inv-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="inv-dbody">

        <!-- ══ CARD 1: Order Details ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="poCollapsed.details=!poCollapsed.details">
            <div class="add-card-title">
              <span class="add-card-title-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 2L3 6v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V6l-3-4z"/><line x1="3" y1="6" x2="21" y2="6"/><path d="M16 10a4 4 0 0 1-8 0"/></svg>
              </span>
              Order Details
            </div>
            <span class="add-card-chevron" :class="{collapsed:poCollapsed.details}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:poCollapsed.details}">
            <div class="add-details-grid">
              <div style="grid-column:1/-1">
                <label class="inv-lbl">Vendor <span class="inv-req">*</span></label>
                <SearchableSelect v-model="form.supplier" :options="vendors" placeholder="Select vendor…"
                  :createable="true" createDoctype="Supplier" @search="fetchVendors" />
              </div>
              <div>
                <label class="inv-lbl">Order Date <span class="inv-req">*</span></label>
                <input v-model="form.transaction_date" type="date" class="inv-fi" />
              </div>
              <div>
                <label class="inv-lbl">Expected Delivery</label>
                <input v-model="form.expected_delivery_date" type="date" class="inv-fi" />
              </div>
              <div style="grid-column:1/-1">
                <label class="inv-lbl">Receiving Warehouse <span class="inv-req">*</span></label>
                <SearchableSelect v-model="form.set_warehouse" :options="warehouses" placeholder="Select warehouse where goods will be received…" @search="fetchWarehouses" />
              </div>
            </div>
          </div>
        </div>

        <!-- ══ CARD 2: Addresses ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="poCollapsed.address=!poCollapsed.address">
            <div class="add-card-title">
              <span class="add-card-title-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>
              </span>
              Addresses
            </div>
            <span class="add-card-chevron" :class="{collapsed:poCollapsed.address}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:poCollapsed.address}">
            <div class="inv-fg inv-fg2">
              <div>
                <label class="inv-lbl">Billing Address</label>
                <input v-model="form.billing_address" type="text" class="inv-fi" placeholder="Optional" />
              </div>
              <div>
                <label class="inv-lbl">Delivery Address</label>
                <input v-model="form.delivery_address" type="text" class="inv-fi" placeholder="Optional" />
              </div>
            </div>
          </div>
        </div>

        <!-- ══ CARD 3: Line Items ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="poCollapsed.lines=!poCollapsed.lines">
            <div class="add-card-title">
              <span class="add-card-title-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg>
              </span>
              Line Items
              <span class="po-item-count">{{ lines.length }} item{{ lines.length !== 1 ? 's' : '' }}</span>
            </div>
            <span class="add-card-chevron" :class="{collapsed:poCollapsed.lines}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:poCollapsed.lines}">
            <div class="po-items-table">
              <div class="po-items-head">
                <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
              </div>
              <div v-for="line in lines" :key="line.id" class="po-items-row">
                <div><SearchableSelect v-model="line.item_code" :options="items"
                  placeholder="Item…" :createable="true" createDoctype="Item"
                  @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
                <div><input v-model="line.description" class="inv-fi" placeholder="Description" /></div>
                <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="inv-fi ta-r" @input="calcLine(line)" /></div>
                <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="inv-fi ta-r" @input="calcLine(line)" /></div>
                <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
                <div><button @click="removeLine(line.id)" class="inv-rm-line"><span v-html="icon('x',12)"></span></button></div>
              </div>
            </div>
            <button class="inv-add-line-btn" style="margin-top:10px" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>

            <!-- Totals -->
            <div class="po-totals" style="margin-top:16px">
              <div style="max-width:160px">
                <label class="inv-lbl">Tax Rate %</label>
                <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="inv-fi" />
              </div>
              <div class="po-totals-right">
                <div class="po-total-row"><span>Subtotal</span><span>{{ fmtCur(subtotal) }}</span></div>
                <div class="po-total-row"><span>Tax ({{ form.tax_rate||0 }}%)</span><span>{{ fmtCur(taxAmount) }}</span></div>
                <div class="po-total-row grand"><span>Total</span><span>{{ fmtCur(subtotal+taxAmount) }}</span></div>
              </div>
            </div>
          </div>
        </div>

        <!-- ══ CARD 4: Terms & Conditions ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="poCollapsed.terms=!poCollapsed.terms">
            <div class="add-card-title">
              <span class="add-card-title-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              </span>
              Terms &amp; Conditions
            </div>
            <span class="add-card-chevron" :class="{collapsed:poCollapsed.terms}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:poCollapsed.terms}">
            <textarea v-model="form.terms" rows="4" class="inv-fi" placeholder="Payment terms, delivery conditions, special notes…"></textarea>
          </div>
        </div>

      </div><!-- /inv-dbody -->

      <!-- Footer -->
      <div class="inv-dfooter">
        <div class="add-footer-status">{{ editingName ? 'Editing: ' + editingName : 'New purchase order — unsaved' }}</div>
        <div class="add-footer-actions">
          <button class="add-btn-cancel" @click="drawerOpen=false">Cancel</button>
          <button class="add-btn-draft" :disabled="drawerSaving" @click="savePO('Draft')">
            <span v-html="icon('save',13)"></span> {{ drawerSaving ? 'Saving…' : 'Save Draft' }}
          </button>
          <button class="add-btn-more" :disabled="drawerSaving" @click="savePO('To Receive')">
            <span v-html="icon('check',13)"></span> {{ drawerSaving ? 'Saving…' : 'Issue PO' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="inv-drawer-bg" @click.self="viewOpen=false"></div>
    <div class="inv-drawer-panel po-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="inv-view-header">
          <div class="inv-view-header-left">
            <div class="inv-view-number">{{ viewDoc.name }}</div>
            <div class="inv-view-subtitle">{{ viewDoc.supplier_name||viewDoc.supplier }}</div>
          </div>
          <div style="text-align:right">
            <div class="po-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="inv-hdr-badge status-draft">{{ displayStatus(viewDoc) }}</span>
          </div>
          <button class="inv-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <TimelineStepper :steps="timelineSteps" />

        <div class="inv-view-tabs">
          <button class="inv-vtab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="inv-vtab" :class="{active:viewTab==='fulfill'}" @click="viewTab='fulfill'">Fulfillment</button>
          <button class="inv-vtab" :class="{active:viewTab==='links'}" @click="viewTab='links'">
            Linked<span v-if="links.bills.length>0" class="inv-vtab-count">{{ links.bills.length }}</span>
          </button>
        </div>

        <div class="inv-view-body">
          <template v-if="viewTab==='details'">
            <div class="po-meta-grid">
              <div><div class="po-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
              <div><div class="po-meta-lbl">Expected Delivery</div>
                <div class="mono-sm" :class="isPastExpected(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.expected_delivery_date)||'—' }}</div>
              </div>
              <div><div class="po-meta-lbl">Billing Address</div><div>{{ viewDoc.billing_address||'—' }}</div></div>
              <div><div class="po-meta-lbl">Delivery Address</div><div>{{ viewDoc.delivery_address||'—' }}</div></div>
            </div>
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="inv-sec-lbl">Line Items</div>
              <div class="po-view-items">
                <div class="po-view-items-head"><span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span></div>
                <div v-for="it in viewItems" :key="it.name" class="po-view-items-row">
                  <span><strong>{{ it.item_name||it.item_code }}</strong>
                    <div v-if="it.description" class="text-muted" style="font-size:11px">{{ it.description }}</div></span>
                  <span class="ta-r mono-sm">{{ it.qty }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(it.amount) }}</span>
                </div>
              </div>
            </template>
            <div v-if="viewDoc.terms" class="po-terms">
              <div class="po-meta-lbl">Terms & Conditions</div>
              <div style="white-space:pre-wrap;font-size:12.5px;color:#374151">{{ viewDoc.terms }}</div>
            </div>
          </template>

          <template v-if="viewTab==='fulfill'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="fulfill.lines.length">
              <div style="font-size:12px;color:#6b7280">Status: <strong>{{ fulfill.computed_status }}</strong></div>
              <div class="po-fulfill-tbl">
                <div class="po-fulfill-head">
                  <span>Item</span><span class="ta-r">Ordered</span><span class="ta-r">Received</span>
                  <span class="ta-r">Billed</span><span class="ta-r">Remaining</span>
                </div>
                <div v-for="l in fulfill.lines" :key="l.name" class="po-fulfill-row">
                  <span>{{ l.item_name||l.item_code }}</span>
                  <span class="ta-r mono-sm">{{ l.qty }}</span>
                  <span class="ta-r mono-sm" :class="l.received_qty>=l.qty?'text-success':'text-muted'">{{ l.received_qty }}</span>
                  <span class="ta-r mono-sm" :class="l.billed_qty>=l.qty?'text-success':'text-muted'">{{ l.billed_qty }}</span>
                  <span class="ta-r mono-sm text-danger">{{ l.remaining_to_receive }} / {{ l.remaining_to_bill }}</span>
                </div>
              </div>
              <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px">
                <button v-if="hasUnreceived" class="form-btn form-btn-outline" @click="markAllReceived" :disabled="actionRunning">📦 Mark All Received</button>
              </div>
            </template>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">No line items.</div>
          </template>

          <template v-if="viewTab==='links'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else>
              <div v-if="links.bills.length" class="inv-sec-lbl">Vendor Bills</div>
              <div v-for="b in links.bills" :key="b.name" class="po-link-row">
                <span class="inv-link">{{ b.name }}</span>
                <span class="text-muted">{{ fmtDate(b.posting_date) }}</span>
                <span class="text-muted">Out: {{ fmtCur(b.outstanding_amount) }}</span>
                <span style="text-align:right;font-weight:600">{{ fmtCur(b.grand_total) }}</span>
              </div>
              <div v-if="!links.bills.length"
                style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
                No linked bills yet.
              </div>
            </template>
          </template>
        </div>

        <div class="inv-dfooter">
          <button class="form-btn form-btn-outline" @click="viewOpen=false">Close</button>
          <button v-if="canEdit(viewDoc)" class="form-btn form-btn-success" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button class="form-btn form-btn-outline" @click="emailPO(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="form-btn form-btn-outline" @click="printPO(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="canBill(viewDoc)" class="form-btn form-btn-primary" @click="openBillModal(viewDoc)">→ Bill</button>
          <button v-if="canCancel(viewDoc)" class="form-btn form-btn-danger" @click="cancelPO(viewDoc)">Cancel</button>
          <button v-if="canDelete(viewDoc)" class="form-btn form-btn-danger" @click="deletePO(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Convert-to-Bill modal (partial-qty + 3-way warn) ── -->
    <div v-if="billModal.open" class="inv-drawer-bg" @click.self="billModal.open=false" style="z-index:60"></div>
    <div v-if="billModal.open" class="po-apply-dialog">
      <div class="inv-dh" style="height:auto;padding:14px 18px">
        <div class="inv-dh-title">Convert to Bill — {{ billModal.poName }}</div>
        <button class="inv-dclose" @click="billModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="inv-dbody">
        <div style="font-size:12.5px;color:#374151">Enter the quantity to bill for each line (defaults to remaining):</div>
        <div class="po-inv-tbl">
          <div class="po-inv-head">
            <span>Item</span><span class="ta-r">Recv'd</span><span class="ta-r">Remaining</span><span class="ta-r">Bill</span>
          </div>
          <div v-for="l in billModal.lines" :key="l.name" class="po-inv-row" :class="{warn:l.toBill > (l.received_qty - l.billed_qty)}">
            <span>{{ l.item_name||l.item_code }}</span>
            <span class="ta-r mono-sm text-muted">{{ l.received_qty }}</span>
            <span class="ta-r mono-sm text-muted">{{ l.remaining_to_bill }}</span>
            <input v-model.number="l.toBill" type="number" min="0" :max="l.remaining_to_bill" step="0.001"
              class="inv-fi ta-r" style="font-family:monospace;width:90px" />
          </div>
        </div>
        <div v-if="threeWayMismatch" class="po-warn">
          ⚠ Billing more than received on at least one line. Three-way match will fail. Proceed only if approved.
        </div>
        <div class="inv-fg inv-fg2">
          <div>
            <label class="inv-lbl">Vendor Bill #</label>
            <input v-model="billModal.billNo" type="text" class="inv-fi" />
          </div>
          <div>
            <label class="inv-lbl">Vendor Bill Date</label>
            <input v-model="billModal.billDate" type="date" class="inv-fi" />
          </div>
          <div style="grid-column:1/-1">
            <label class="inv-lbl">Due Date</label>
            <input v-model="billModal.dueDate" type="date" class="inv-fi" />
          </div>
        </div>
        <div style="text-align:right;font-size:13px;color:#6b7280">
          Bill Total: <strong style="color:#111827">{{ fmtCur(billModalTotal) }}</strong>
        </div>
      </div>
      <div class="inv-dfooter">
        <button class="form-btn form-btn-outline" @click="billModal.open=false" :disabled="billModal.saving">Cancel</button>
        <button class="form-btn form-btn-primary" :disabled="billModal.saving||billModalTotal<=0" @click="submitBill">
          {{ billModal.saving ? 'Creating…' : `Create Bill ${fmtCur(billModalTotal)}` }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiPOST, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { useConfirm } from "../composables/useConfirm.js";
import { useLivePreview } from "../composables/useLivePreview.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import Pagination from "../components/Pagination.vue";
import { usePagination } from "../composables/usePagination.js";
import BulkActionBar from "../components/BulkActionBar.vue";
import TimelineStepper from "../components/TimelineStepper.vue";

const { toast } = useToast();
const { confirm } = useConfirm();
const { printDoc } = useLivePreview();
function printPO(d) { printDoc(d, { title: "PURCHASE ORDER", partyLabel: "Vendor", partyField: "supplier_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();

const activeTab = ref("all");
const tabs = [
  { key: "all",       label: "All" },
  { key: "draft",     label: "Draft" },
  { key: "toReceive", label: "To Receive" },
  { key: "toBill",    label: "To Bill" },
  { key: "closed",    label: "Closed" },
  { key: "cancelled", label: "Cancelled" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const poCollapsed = reactive({ details: false, address: true, lines: false, terms: true });
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const viewLoading = ref(false), viewItems = ref([]);
const fulfill = reactive({ lines: [], computed_status: "" });
const links = reactive({ bills: [], purchase_receipts: [] });
const vendors = ref([]), items = ref([]), lines = ref([]), taxAccountHead = ref("");
const sortCol = ref("transaction_date"), sortDir = ref("desc");
const actionRunning = ref(false);

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const form = reactive({
  supplier: "", transaction_date: todayStr(), expected_delivery_date: expectedDefault(),
  billing_address: "", delivery_address: "", set_warehouse: "", tax_rate: 0, terms: "",
});
const warehouses = ref([]);
async function fetchWarehouses(q = "") {
  try {
    const co = await resolveCompany();
    const rows = await apiList("Warehouse", { filters: [["company","=",co],["disabled","=",0],["is_group","=",0]], fields: ["name","parent_warehouse"], limit: 50 });
    warehouses.value = (rows || [])
      .filter(r => !q || r.name.toLowerCase().includes(q.toLowerCase()) || (r.parent_warehouse||"").toLowerCase().includes(q.toLowerCase()))
      .map(r => ({ label: r.parent_warehouse ? `${r.parent_warehouse} / ${r.name}` : r.name, value: r.name }));
  } catch { warehouses.value = []; }
}

const billModal = reactive({ open: false, saving: false, poName: "", lines: [],
  billNo: "", billDate: "", dueDate: "" });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function expectedDefault() { const d = new Date(); d.setDate(d.getDate() + 7); return d.toISOString().slice(0, 10); }
function fmtCur(v) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v)); }

function isPastExpected(o) {
  if (!o?.expected_delivery_date) return false;
  const s = (o.status||"").toLowerCase();
  if (s === "closed" || s === "billed" || s === "cancelled" || s === "received") return false;
  return new Date(o.expected_delivery_date) < new Date();
}
function displayStatus(o) { return (o?.status || "Draft").toUpperCase(); }
function badgeClass(o) {
  const s = (o?.status||"").toLowerCase();
  if (!s || s === "draft")  return "status-draft";
  if (s === "cancelled")    return "status-cancelled";
  if (s === "closed" || s === "billed") return "status-closed";
  if (s.includes("received") && !s.includes("partially")) return "status-submitted";
  if (s === "to receive" || s.includes("partially") || s === "sent" || s === "confirmed") return "status-open";
  return "status-submitted";
}
function headerBg(o) {
  const s = (o?.status||"").toLowerCase();
  if (s === "cancelled") return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  if (s === "closed" || s === "billed") return "linear-gradient(135deg,#064e3b,#059669)";
  if (s === "to receive" || s.includes("partially") || s === "sent" || s === "confirmed") return "linear-gradient(135deg,#78350f,#d97706)";
  if (s === "received") return "linear-gradient(135deg,#1e3a5f,#1a6ef7)";
  return "linear-gradient(135deg,#374151,#6b7280)";
}
function canBill(o) {
  const s = (o?.status||"").toLowerCase();
  return s !== "cancelled" && s !== "closed" && s !== "billed";
}
function canEdit(o) {
  const s = (o?.status||"").toLowerCase();
  return s === "draft" || s === "";
}
function canCancel(o) {
  const s = (o?.status||"").toLowerCase();
  return s !== "cancelled" && s !== "closed" && s !== "billed";
}
function canDelete(o) {
  const s = (o?.status||"").toLowerCase();
  return s === "draft" || s === "" || s === "cancelled";
}

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    list.value = await apiList("Purchase Order", {
      fields: ["name", "supplier", "supplier_name", "transaction_date", "expected_delivery_date", "status", "grand_total", "billed_amount", "billing_address", "delivery_address"],
      filters: [["company", "=", co]],
      limit: 500,
      order: "transaction_date desc",
    });
  } catch (e) { toast.error(e.message || "Failed to load purchase orders"); }
  finally { loading.value = false; }
}
async function loadTaxAccount() {
  try {
    const r = await apiList("Account", { fields: ["name"], filters: [["account_type", "=", "Tax"], ["is_group", "=", 0]], limit: 1 });
    if (r?.length) taxAccountHead.value = r[0].name;
  } catch {}
}

const counts = computed(() => {
  const c = { draft:0, toReceive:0, toBill:0, closed:0, cancelled:0 };
  for (const o of list.value) {
    const s = (o.status||"draft").toLowerCase();
    if (s === "cancelled") c.cancelled++;
    else if (s === "closed" || s === "billed") c.closed++;
    else if (s === "draft") c.draft++;
    else if (s === "received") c.toBill++;
    else c.toReceive++;
  }
  return c;
});
const summary = computed(() => ({
  totalValue: list.value.filter(o => (o.status||"").toLowerCase() !== "cancelled")
    .reduce((s, o) => s + flt(o.grand_total), 0),
}));
const _poYM  = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _poLYM = () => { const d=new Date(); d.setMonth(d.getMonth()-1); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _poTr  = (a,b) => { if(!b&&!a) return {pct:0,up:true}; if(!b) return {pct:100,up:true}; const p=Math.round((a-b)/b*100); return {pct:Math.abs(p),up:p>=0}; };
const poThisMonth = computed(()=>{ const ym=_poYM(); const r=list.value.filter(o=>(o.transaction_date||'').startsWith(ym)); return {count:r.length,value:r.reduce((s,o)=>s+flt(o.grand_total),0)}; });
const poTrends = computed(()=>({
  total:     _poTr(poThisMonth.value.count, list.value.filter(o=>(o.transaction_date||'').startsWith(_poLYM())).length),
  draft:     _poTr(counts.value.draft, list.value.filter(o=>(o.transaction_date||'').startsWith(_poLYM())&&o.docstatus===0).length),
  receive:   _poTr(counts.value.toReceive, list.value.filter(o=>(o.transaction_date||'').startsWith(_poLYM())&&(o.status||'').toLowerCase()!=='cancelled'&&(o.status||'').toLowerCase()!=='closed').length),
  bill:      _poTr(counts.value.toBill, list.value.filter(o=>(o.transaction_date||'').startsWith(_poLYM())&&(o.status||'').toLowerCase()==='received').length),
  cancelled: _poTr(counts.value.cancelled, list.value.filter(o=>(o.transaction_date||'').startsWith(_poLYM())&&(o.status||'').toLowerCase()==='cancelled').length),
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") {
    r = r.filter(o => {
      const s = (o.status||"draft").toLowerCase();
      if (activeTab.value === "draft")     return s === "draft";
      if (activeTab.value === "cancelled") return s === "cancelled";
      if (activeTab.value === "closed")    return s === "closed" || s === "billed";
      if (activeTab.value === "toBill")    return s === "received";
      if (activeTab.value === "toReceive") return s !== "cancelled" && s !== "closed" && s !== "billed" && s !== "draft" && s !== "received";
      return true;
    });
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.supplier_name || x.supplier || "").toLowerCase().includes(q));
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
const { page, pageSize, paged } = usePagination(sorted, { storageKey: "purchase-orders" });
function sortBy(col) { if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc"; else { sortCol.value = col; sortDir.value = "asc"; } }
function sortArrow(col) { if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value === "asc" ? "↑" : "↓"; }

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(o => selected.value.has(o.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(o => o.name)) : new Set(); }

const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const taxAmount = computed(() => Math.round(subtotal.value * flt(form.tax_rate) / 100 * 100) / 100);

const hasUnreceived = computed(() => fulfill.lines.some(l => l.remaining_to_receive > 0));

const timelineSteps = computed(() => {
  const o = viewDoc.value;
  if (!o) return [];
  const s = (o.status||"").toLowerCase();
  if (s === "cancelled") {
    return [
      { key:"draft", label:"Draft", done:true },
      { key:"sub",   label:"Issued", done:true },
      { key:"end",   label:"Cancelled", danger:true, current:true },
    ];
  }
  const received = s === "received" || s === "billed" || s === "closed";
  const billed   = s === "billed"   || s === "closed";
  const closed   = s === "closed";
  return [
    { key:"draft",    label:"Draft",    done:true },
    { key:"issued",   label:"Issued",   done:s!=="draft", current:s==="to receive"||s==="sent"||s==="confirmed" },
    { key:"received", label:"Received", done:received, current:s==="received" && !billed },
    { key:"billed",   label:"Billed",   done:billed, current:billed && !closed },
    { key:"closed",   label:"Closed",   done:closed, current:closed },
  ];
});

const billModalTotal = computed(() =>
  (billModal.lines || []).reduce((s, l) => s + flt(l.toBill) * flt(l.rate), 0)
);
const threeWayMismatch = computed(() =>
  (billModal.lines || []).some(l => flt(l.toBill) > (flt(l.received_qty) - flt(l.billed_qty)))
);

// ── Create / Edit ─────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { supplier: "", transaction_date: todayStr(), expected_delivery_date: expectedDefault(), billing_address: "", delivery_address: "", set_warehouse: "", tax_rate: 0, terms: "" });
  fetchWarehouses("");
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems("");
  drawerOpen.value = true;
}
async function openEdit(o) {
  editingName.value = o.name;
  Object.assign(form, {
    supplier: o.supplier || "", transaction_date: o.transaction_date || todayStr(),
    expected_delivery_date: o.expected_delivery_date || expectedDefault(),
    billing_address: o.billing_address || "", delivery_address: o.delivery_address || "",
    set_warehouse: "", tax_rate: 0, terms: o.terms || "",
  });
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems(""); fetchWarehouses("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Purchase Order", o.name);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || "",
        qty: i.qty || 1, rate: i.rate || 0, amount: i.amount || 0,
      }));
    }
    if (doc?.set_warehouse) form.set_warehouse = doc.set_warehouse;
    if (doc?.taxes?.[0]?.rate) form.tax_rate = doc.taxes[0].rate;
    if (doc?.taxes?.[0]?.account_head) taxAccountHead.value = doc.taxes[0].account_head;
    if (doc?.terms) form.terms = doc.terms;
  } catch {}
}
async function openView(o) {
  viewDoc.value = o;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  fulfill.lines = []; fulfill.computed_status = "";
  links.bills = []; links.purchase_receipts = [];
  try {
    const [doc, ful, lnk] = await Promise.all([
      apiGet("Purchase Order", o.name),
      apiGET("zoho_books_clone.api.docs.get_purchase_order_fulfillment", { purchase_order: o.name }).catch(() => null),
      apiGET("zoho_books_clone.api.docs.get_purchase_order_links", { purchase_order: o.name }).catch(() => null),
    ]);
    viewItems.value = doc?.items || [];
    viewDoc.value = { ...o, ...doc };
    if (ful) { fulfill.lines = ful.lines || []; fulfill.computed_status = ful.computed_status || ""; }
    if (lnk) { links.bills = lnk.bills || []; }
  } catch {}
  viewLoading.value = false;
}

async function fetchVendors(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["supplier_name", "like", "%" + q + "%"]);
    const r = await apiList("Supplier", { fields: ["name", "supplier_name"], filters: f, limit: 30, order: "supplier_name asc" });
    vendors.value = r.map(x => ({ ...x, label: x.supplier_name || x.name, value: x.name }));
  } catch { vendors.value = []; }
}
async function fetchItems(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["item_name", "like", "%" + q + "%"]);
    const r = await apiList("Item", { fields: ["name", "item_name", "description", "standard_rate", "stock_uom"], filters: f, limit: 30, order: "item_name asc" });
    items.value = r.map(x => ({ ...x, label: x.item_name || x.name, value: x.name, rate: x.standard_rate || 0, description: x.description || "" }));
  } catch { items.value = []; }
}
async function onItemSelect(line, opt) {
  line.item_code = opt?.value ?? opt;
  if (opt?.rate)        { line.rate        = Number(opt.rate) || 0; }
  if (opt?.item_name)   { line.item_name   = opt.item_name; }
  if (opt?.description) { line.description = opt.description; }
  else if (opt?.value) {
    // description not in option cache — fetch from Item doc directly
    try {
      const doc = await apiGet("Item", opt.value);
      if (doc?.description) line.description = doc.description;
      if (doc?.item_name)   line.item_name   = doc.item_name;
    } catch {}
  }
  calcLine(line);
}
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }

async function savePO(newStatus) {
  if (!form.supplier) return toast.error("Vendor is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  if (!form.set_warehouse) return toast.error("Receiving Warehouse is required");
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const taxes = form.tax_rate > 0 && taxAccountHead.value
      ? [{ doctype: "Tax Line", charge_type: "On Net Total", account_head: taxAccountHead.value, description: taxAccountHead.value, rate: form.tax_rate }]
      : [];
    const doc = {
      doctype: "Purchase Order", company,
      supplier: form.supplier, transaction_date: form.transaction_date,
      expected_delivery_date: form.expected_delivery_date || null,
      billing_address: form.billing_address || "",
      delivery_address: form.delivery_address || "",
      set_warehouse: form.set_warehouse || "",
      status: newStatus || "Draft",
      terms: form.terms || "",
      items: lines.value.filter(l => l.item_code).map(l => ({
        doctype: "Purchase Order Item", item_code: l.item_code,
        description: l.description || l.item_code,
        qty: flt(l.qty) || 1, rate: flt(l.rate), amount: flt(l.amount),
      })),
      taxes,
    };
    if (editingName.value) doc.name = editingName.value;
    const saved = await apiSave(doc);
    toast.success(`Purchase Order ${saved?.name || ""} saved`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save PO"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailPO(o) {
  await openEmail({
    doctype: "Purchase Order", name: o.name, docLabel: `Purchase Order ${o.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_purchase_order_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_purchase_order_email",
    paramKey: "purchase_order",
  });
}

function openBillModal(o) {
  apiGET("zoho_books_clone.api.docs.get_purchase_order_fulfillment", { purchase_order: o.name })
    .then(r => {
      const ful = r?.lines || [];
      Object.assign(billModal, {
        open: true, saving: false, poName: o.name,
        lines: ful.filter(l => l.remaining_to_bill > 0)
                  .map(l => ({ ...l, toBill: Math.min(l.remaining_to_bill, Math.max(0, l.received_qty - l.billed_qty)) || l.remaining_to_bill })),
        billNo: "", billDate: todayStr(), dueDate: o.expected_delivery_date || todayStr(),
      });
      if (!billModal.lines.length) { billModal.open = false; toast.info("Nothing left to bill"); }
    })
    .catch(e => toast.error(e.message || "Failed to load fulfillment"));
}
async function submitBill() {
  const lineMap = {};
  for (const l of billModal.lines) {
    if (flt(l.toBill) > 0) lineMap[l.name] = flt(l.toBill);
  }
  if (!Object.keys(lineMap).length) { toast.error("Enter at least one qty to bill"); return; }
  billModal.saving = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.docs.convert_purchase_order_to_bill", {
      purchase_order: billModal.poName,
      line_qtys: JSON.stringify(lineMap),
      bill_no: billModal.billNo || "",
      bill_date: billModal.billDate || "",
      due_date: billModal.dueDate || "",
    });
    toast.success(`Bill created: ${r?.bill}`);
    if (r?.three_way_warnings?.length) {
      toast.warn?.("3-way match: " + r.three_way_warnings.join("; ")) || toast.info("3-way mismatch — check fulfillment");
    }
    billModal.open = false;
    await load();
    if (viewDoc.value?.name === billModal.poName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Convert failed"); }
  billModal.saving = false;
}

async function markAllReceived() {
  actionRunning.value = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.docs.mark_po_received", { purchase_order: viewDoc.value.name });
    toast.success(`Marked ${r?.lines_updated || 0} line(s) received`);
    await load();
    if (viewDoc.value) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Mark received failed"); }
  actionRunning.value = false;
}

async function cancelPO(o) {
  if (!await confirm({ title: "Cancel Purchase Order", body: `Cancel ${o.name}? Linked bills must be cancelled separately.`, okLabel: "Cancel PO" })) return;
  try {
    await apiPOST("zoho_books_clone.api.docs.cancel_purchase_order_safe", { purchase_order: o.name });
    toast.success("Purchase Order cancelled");
    await load(); if (viewDoc.value?.name === o.name) await openView(o);
  } catch (e) { toast.error(e.message || "Cancel failed"); }
}
async function deletePO(o) {
  if (!await confirm({ title: "Delete Purchase Order", body: `Permanently delete ${o.name}?`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Purchase Order", o.name);
    toast.success("Purchase Order deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk actions ──────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(o => selected.value.has(o.name) && (!o.status || o.status === "Draft"));
  if (!drafts.length) { toast.info("Select drafts to delete"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft PO(s)?`, okLabel: "Delete" })) return;
  for (const o of drafts) { try { await apiDelete("Purchase Order", o.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length}`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(o => selected.value.has(o.name));
  if (!subs.length) { toast.info("No POs selected"); return; }
  let sent = 0;
  for (const o of subs) {
    const ok = await openEmail({
      doctype: "Purchase Order", name: o.name, docLabel: `Purchase Order ${o.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_purchase_order_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_purchase_order_email",
      paramKey: "purchase_order",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} PO(s)`);
}

function exportCSV() {
  const rows = selected.value.size
    ? sorted.value.filter(p => selected.value.has(p.name))
    : sorted.value;
  if (!rows.length) return;
  const head = ["PO #","Vendor","Date","Expected","Status","Amount"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const o of rows) {
    out.push([o.name, o.supplier_name || o.supplier, o.transaction_date, o.expected_delivery_date || "",
      o.status || "Draft", Number(o.grand_total || 0).toFixed(2)].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `purchase_orders_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} PO(s)`);
}

onMounted(() => { load(); loadTaxAccount(); });
</script>

<style scoped>
/* ── Drawer slide animation + width ── */
.inv-drawer-panel {
  position: fixed;
  top: 0;
  right: -600px;
  bottom: 0;
  width: 600px;
  max-width: 96vw;
  z-index: 8000;
  transition: right .22s ease;
}
.inv-drawer-panel.open { right: 0; }
.po-view-drawer { width: 540px; right: -540px; }
.po-view-drawer.open { right: 0; }

/* ── View panel: large amount display ── */
.po-view-amount {
  font-size: 20px;
  font-weight: 800;
  font-family: monospace;
  color: #dc2626;
}

/* ── View body padding ── */
.inv-view-body {
  padding: 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow-y: auto;
  margin: 0;
  border: none;
  border-radius: 0;
}

/* ── Meta grid (view details tab) ── */
.po-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.po-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }

/* ── View items column grid ── */
.po-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; }
.po-view-items-head { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.po-view-items-row { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }

/* ── Totals block ── */
.po-totals { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.po-totals-right { display: flex; flex-direction: column; gap: 4px; min-width: 220px; }
.po-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 3px 0; }
.po-total-row.grand { font-weight: 700; font-size: 14px; color: #111827; border-top: 1px solid #e5e7eb; padding-top: 6px; }

/* ── Edit drawer line items grid ── */
.po-items-table { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 8px; }
.po-items-head { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #374151; }
.po-items-row { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; }

/* ── Fulfillment table ── */
.po-fulfill-tbl { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.po-fulfill-head { display: grid; grid-template-columns: 2fr 80px 100px 90px 110px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.po-fulfill-row { display: grid; grid-template-columns: 2fr 80px 100px 90px 110px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }

/* ── Misc view helpers ── */
.po-terms { padding: 10px 12px; background: #f8fafc; border-radius: 6px; }
.po-link-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 12.5px; align-items: center; }
.po-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.po-act-conv { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.po-act-conv:hover { background: #dbeafe; }
.po-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.po-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }

/* ── Convert-to-Bill modal ── */
.po-apply-dialog { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 560px; max-width: 96vw; background: #fff; border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.2); z-index: 70; display: flex; flex-direction: column; overflow: hidden; }
.po-inv-tbl { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.po-inv-head { display: grid; grid-template-columns: 2fr 80px 90px 110px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.po-inv-row { display: grid; grid-template-columns: 2fr 80px 90px 110px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.po-inv-row.warn { background: #fef3c7; }
.po-warn { background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px; padding: 10px 12px; font-size: 12.5px; color: #92400e; }

/* ── Drawer add/edit cards (matches Invoice) ── */
.add-card { border: 1px solid #e8ecf0; border-radius: 10px; overflow: hidden; background: #fff; margin-bottom: 12px; }
.add-card-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; cursor: pointer; user-select: none; background: #f8fafc; }
.add-card-header:hover { background: #f1f4f8; }
.add-card-title { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: #1a1a2e; }
.add-card-title-icon { width: 28px; height: 28px; border-radius: 7px; background: #dbeafe; color: #2563eb; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.add-card-chevron { color: #9ca3af; transition: transform .2s; display: flex; }
.add-card-chevron.collapsed { transform: rotate(-90deg); }
.add-card-body { padding: 16px; border-top: 1px solid #e8ecf0; }
.add-card-body.collapsed { display: none; }
.add-details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }

/* ── Item count badge in card title ── */
.po-item-count { font-size: 11px; font-weight: 600; background: #eff6ff; color: #2563eb; border: 1px solid #bfdbfe; border-radius: 12px; padding: 1px 8px; margin-left: 4px; }

/* ── Draft badge in drawer header ── */
.po-draft-badge { display: inline-flex; align-items: center; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; background: rgba(255,255,255,.15); color: rgba(255,255,255,.85); border: 1px solid rgba(255,255,255,.25); }

/* ── Footer action buttons (matches Invoice add-btn-*) ── */
.add-footer-status { font-size: 12px; color: #9ca3af; }
.add-footer-actions { display: flex; align-items: center; gap: 8px; }
.add-btn-cancel { background: none; border: 1px solid #e8ecf0; border-radius: 7px; padding: 7px 16px; font-size: 13px; font-weight: 600; color: #6b7280; cursor: pointer; }
.add-btn-cancel:hover { border-color: #374151; color: #374151; }

.add-btn-draft:disabled { opacity: .5; cursor: not-allowed; }
.add-btn-primary { display: inline-flex; align-items: center; gap: 6px; background: #1a6ef7; color: #fff; border: none; border-radius: 7px; padding: 7px 18px; font-size: 13px; font-weight: 600; cursor: pointer; }
.add-btn-primary:hover { background: #155fd4; }
.add-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
</style>