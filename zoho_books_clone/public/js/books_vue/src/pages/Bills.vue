<template>
  <div class="list-page">

    <!-- ── Toolbar ── -->
    <div class="sales-toolbar">
      <div class="sales-search">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search bills, vendors, bill #…" class="sales-search-input" />
      </div>
      <div class="sales-pills">
        <button v-for="t in tabs" :key="t.key"
          class="sales-pill" :class="{active:activeTab===t.key, ['pill-'+t.key]: t.key!=='all'}"
          @click="activeTab=t.key">
          {{ t.label }}
          <span v-if="t.key!=='all'" class="sales-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="sales-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="sales-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="sales-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Bill
        </button>
      </div>
    </div>

    <!-- ── KPI Cards ── -->
    <div class="bk-kpi-grid">
      <div class="bk-kpi-card bk-kpi-accent clickable" @click="activeTab='all'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total Bills</div><div class="bk-kpi-value">{{ list.length }}</div><div class="bk-kpi-trend" :class="billTrends.total.up?'bk-trend-up':'bk-trend-down'">{{ billTrends.total.up?'↑':'↓' }} {{ billTrends.total.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card clickable" @click="activeTab='draft'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#f1f5f9"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#6b7280" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Draft</div><div class="bk-kpi-value bk-kpi-amber">{{ counts.draft }}</div><div class="bk-kpi-trend bk-trend-neutral">— drafts</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-warn clickable" @click="activeTab='unpaid'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#fef3c7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Unpaid</div><div class="bk-kpi-value bk-kpi-amber">{{ counts.unpaid }}</div><div class="bk-kpi-trend" :class="billTrends.unpaid.up?'bk-trend-up':'bk-trend-down'">{{ billTrends.unpaid.up?'↑':'↓' }} {{ billTrends.unpaid.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-danger clickable" @click="activeTab='overdue'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#fee2e2"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="1.8"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Overdue</div><div class="bk-kpi-value bk-kpi-red">{{ counts.overdue }}</div><div class="bk-kpi-trend" :class="billTrends.overdue.up?'bk-trend-down':'bk-trend-up'">{{ billTrends.overdue.up?'↑':'↓' }} {{ billTrends.overdue.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-success clickable" @click="activeTab='paid'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dcfce7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#16a34a" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Paid</div><div class="bk-kpi-value bk-kpi-green">{{ counts.paid }}</div><div class="bk-kpi-trend" :class="billTrends.paid.up?'bk-trend-up':'bk-trend-down'">{{ billTrends.paid.up?'↑':'↓' }} {{ billTrends.paid.pct }}% vs last month</div></div></div></div>
    </div>
    <div class="bk-stat-grid">
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month Bills</div><div class="bk-stat-value">{{ billThisMonth.count }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month Spend</div><div class="bk-stat-value" style="font-size:16px">{{ fmtCur(billThisMonth.spend) }}</div></div><div class="bk-stat-icon" style="background:#fee2e2;color:#dc2626"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Total Payable</div><div class="bk-stat-value bk-kpi-amber" style="font-size:16px">{{ fmtCur(summary.totalDue) }}</div></div><div class="bk-stat-icon" style="background:#fef3c7;color:#d97706"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Avg Bill Value</div><div class="bk-stat-value" style="font-size:16px">{{ fmtCur(billAvg) }}</div></div><div class="bk-stat-icon" style="background:#e5e7eb;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div></div></div>
    </div>

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button @click="bulkCancel">Cancel Submitted</button>
      <button class="bab-danger" @click="bulkDelete">Delete Drafts</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="inv-table-wrap">
      <table class="inv-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">Bill # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('supplier_name')" class="sortable">Vendor <span v-html="sortArrow('supplier_name')"></span></th>
            <th @click="sortBy('bill_no')" class="sortable">Vendor Bill # <span v-html="sortArrow('bill_no')"></span></th>
            <th @click="sortBy('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
            <th @click="sortBy('due_date')" class="sortable">Due Date <span v-html="sortArrow('due_date')"></span></th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th @click="sortBy('outstanding_amount')" class="sortable ta-r">Balance <span v-html="sortArrow('outstanding_amount')"></span></th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 7" :key="n"><td colspan="10"><div class="shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="b in paged" :key="b.name" class="inv-row" :class="{selected:selected.has(b.name)}">
              <td><input type="checkbox" :checked="selected.has(b.name)" @change="toggle(b.name)" /></td>
              <td @click="openView(b)"><span class="inv-link">{{ b.name }}</span></td>
              <td @click="openView(b)">{{ b.supplier_name || b.supplier || '—' }}</td>
              <td @click="openView(b)" class="text-muted mono-sm">{{ b.bill_no||'—' }}</td>
              <td @click="openView(b)" class="text-muted mono-sm">{{ fmtDate(b.posting_date) }}</td>
              <td @click="openView(b)" :class="isOverdue(b)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(b.due_date)||'—' }}</td>
              <td @click="openView(b)"><span class="inv-status-badge" :class="statusCls(b)">{{ statusLabel(b) }}</span></td>
              <td @click="openView(b)" class="ta-r mono-sm">{{ fmtCur(b.grand_total) }}</td>
              <td @click="openView(b)" class="ta-r mono-sm" :class="{'text-danger':flt(b.outstanding_amount)>0,'text-success':flt(b.outstanding_amount)<=0&&b.docstatus===1}">{{ fmtCur(b.outstanding_amount) }}</td>
              <td class="bill-act-cell">
                <button class="inv-act-btn" @click="openView(b)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="b.docstatus===0" class="inv-act-btn" @click="openEdit(b)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button v-if="b.docstatus===1 && flt(b.outstanding_amount)>0" class="inv-act-btn inv-act-pay" @click="payBill(b)" title="Record Payment">₹</button>
                <button v-if="b.docstatus===0 || b.docstatus===2" class="inv-act-btn bill-act-del" @click="deleteBill(b)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="10" class="bk-empty-state"><div class="bk-empty-inner"><template v-if="search||filterVendor"><svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.3"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg><p class="bk-empty-title">No bills match your filters</p></template><template v-else><div class="bk-empty-illus"><svg width="80" height="96" viewBox="0 0 80 96" fill="none"><rect x="10" y="8" width="60" height="80" rx="6" fill="#e2e8f0"/><rect x="14" y="12" width="52" height="72" rx="4" fill="#fff"/><rect x="22" y="26" width="36" height="3" rx="2" fill="#e2e8f0"/><rect x="22" y="34" width="28" height="3" rx="2" fill="#e2e8f0"/><rect x="22" y="42" width="32" height="3" rx="2" fill="#e2e8f0"/><rect x="50" y="64" width="18" height="20" rx="3" fill="#f59e0b" opacity=".7"/><rect x="36" y="70" width="12" height="14" rx="3" fill="#2563eb" opacity=".6"/></svg></div><p class="bk-empty-title">No bills created yet</p><p class="bk-empty-sub">Add your first vendor bill to start tracking payables.</p><button class="bk-empty-btn" @click="openNew"><span v-html="icon('plus',13)"></span> New Bill</button></template></div></td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Pagination ── -->
    <div v-if="!loading && sorted.length" style="padding:12px 4px 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ── Create / Edit drawer ── -->
    <div v-if="drawerOpen" class="inv-drawer-bg" @click.self="drawerOpen=false"></div>
    <div class="inv-drawer-panel bill-edit-drawer" :class="{open:drawerOpen}">

      <!-- Header -->
      <div class="inv-dh">
        <div style="display:flex;align-items:center;gap:10px;flex-wrap:wrap">
          <div class="inv-dh-title">{{ editingName ? 'Edit Bill' : 'New Bill' }}</div>
          <span v-if="!editingName" class="add-status-badge">Draft</span>
        </div>
        <button class="inv-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="inv-dbody">

        <!-- ══ CARD 1: Bill Details ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="billCollapsed.details=!billCollapsed.details">
            <div class="add-card-title">
              <span class="add-card-title-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg></span>
              Bill Details
            </div>
            <span class="add-card-chevron" :class="{collapsed:billCollapsed.details}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:billCollapsed.details}">
            <div>
              <label class="inv-lbl">Vendor <span class="inv-req">*</span></label>
              <SearchableSelect v-model="form.supplier" :options="vendors"
                placeholder="Select vendor…" :createable="true" createDoctype="Supplier"
                @search="fetchVendors" @select="onVendorSelect" />
            </div>
            <div class="add-details-grid" style="margin-top:14px">
              <div>
                <label class="inv-lbl">Bill Date <span class="inv-req">*</span></label>
                <input v-model="form.posting_date" type="date" class="inv-fi" />
              </div>
              <div>
                <label class="inv-lbl">Due Date</label>
                <input v-model="form.due_date" type="date" class="inv-fi" />
              </div>
              <div>
                <label class="inv-lbl">Vendor Bill #</label>
                <input v-model="form.bill_no" type="text" class="inv-fi" placeholder="Vendor's invoice number" />
              </div>
              <div>
                <label class="inv-lbl">Vendor Bill Date</label>
                <input v-model="form.bill_date" type="date" class="inv-fi" />
              </div>
              <div>
                <label class="inv-lbl">Currency</label>
                <select v-model="form.currency" class="inv-fi" @change="form.exchange_rate=form.currency==='INR'?1:form.exchange_rate">
                  <option v-for="(sym,code) in BILL_CURRENCIES" :key="code" :value="code">{{ code }} {{ sym }}</option>
                </select>
              </div>
              <div v-if="form.currency !== 'INR'">
                <label class="inv-lbl">Exchange Rate</label>
                <input v-model.number="form.exchange_rate" type="number" min="0.0001" step="0.0001" class="inv-fi"/>
              </div>
              <div>
                <label class="inv-lbl">Cost Center</label>
                <select v-model="form.cost_center" class="inv-fi">
                  <option value="">— Select —</option>
                  <option v-for="cc in costCenters" :key="cc" :value="cc">{{ cc }}</option>
                </select>
              </div>
            </div>

            <!-- Inventory toggle -->
            <div style="margin-top:14px">
              <div class="inv-inv-block" :class="form.update_stock ? 'inv-on' : 'inv-off'">
                <div class="inv-inv-toggle-row">
                  <div class="inv-inv-icon" v-html="icon('box', 16)"></div>
                  <div class="inv-inv-text">
                    <div class="inv-inv-title">Update Inventory on Submit</div>
                    <div class="inv-inv-sub">Stock increases in the selected warehouse when this bill is submitted</div>
                  </div>
                  <label class="inv-inv-switch">
                    <input type="checkbox" v-model="form.update_stock" :true-value="1" :false-value="0" />
                    <span class="inv-inv-slider"></span>
                  </label>
                </div>
                <div v-if="form.update_stock" class="inv-inv-wh-row">
                  <label class="inv-lbl" style="margin-bottom:6px">Receiving Warehouse <span style="color:#dc2626">*</span></label>
                  <SearchableSelect v-model="form.set_warehouse" :options="warehouses" placeholder="Select warehouse where stock will be received…" @search="fetchWarehouses" />
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ══ CARD 2: Billing Address ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="billCollapsed.billing=!billCollapsed.billing">
            <div class="add-card-title">
              <span class="add-card-title-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></span>
              Billing Address
            </div>
            <span class="add-card-chevron" :class="{collapsed:billCollapsed.billing}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:billCollapsed.billing}">
            <div v-if="vendorBillingAddrs.length > 1" style="margin-bottom:8px">
              <label class="inv-lbl">Select Address</label>
              <select v-model="form.selected_billing_addr_name" class="inv-fi" @change="applyVendorBillingAddr">
                <option value="">— Select address —</option>
                <option v-for="a in vendorBillingAddrs" :key="a.name" :value="a.name">{{ a.address_title || a.address_line1 }}, {{ a.city }}</option>
              </select>
            </div>
            <div>
              <label class="inv-lbl">Address <span style="color:#9ca3af;font-weight:400">(auto-filled from vendor)</span></label>
              <textarea v-model="form.billing_address" class="inv-fi" rows="3" style="resize:vertical;width:100%;box-sizing:border-box" placeholder="Auto-filled from vendor, or enter manually"></textarea>
            </div>
          </div>
        </div>

        <!-- ══ CARD 3: Line Items ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="billCollapsed.lines=!billCollapsed.lines">
            <div class="add-card-title">
              <span class="add-card-title-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="8" y1="6" x2="21" y2="6"/><line x1="8" y1="12" x2="21" y2="12"/><line x1="8" y1="18" x2="21" y2="18"/><line x1="3" y1="6" x2="3.01" y2="6"/><line x1="3" y1="12" x2="3.01" y2="12"/><line x1="3" y1="18" x2="3.01" y2="18"/></svg></span>
              Line Items
            </div>
            <div style="display:flex;align-items:center;gap:8px" @click.stop>
              <button v-if="form.supplier" class="inv-add-line-btn inv-copy-btn" @click="copyLastItems" :disabled="copyingLast">
                <span v-html="icon('copy',12)"></span> {{ copyingLast ? 'Loading…' : 'Copy Last' }}
              </button>
              <button class="add-lines-add-btn" @click="addLine">
                <span v-html="icon('plus',13)"></span> Add Item
              </button>
              <span class="add-card-chevron" :class="{collapsed:billCollapsed.lines}" @click.stop="billCollapsed.lines=!billCollapsed.lines">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </span>
            </div>
          </div>
          <div class="add-card-body" :class="{collapsed:billCollapsed.lines}" style="padding:0">
            <div style="overflow-x:auto">
              <table class="inv-lines-tbl">
                <thead>
                  <tr>
                    <th style="width:28px">#</th>
                    <th style="min-width:150px">Item</th>
                    <th style="min-width:120px">Description</th>
                    <th style="min-width:70px;text-align:right">Qty</th>
                    <th style="min-width:90px;text-align:right">Rate (₹)</th>
                    <th style="min-width:90px;text-align:right">Amount (₹)</th>
                    <th style="width:32px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(line, idx) in lines" :key="line.id">
                    <td><span class="add-line-num">{{ idx+1 }}</span></td>
                    <td>
                      <SearchableSelect v-model="line.item_code" :options="items"
                        placeholder="Select item…" :compact="true" :createable="true" createDoctype="Item"
                        @search="fetchItems" @select="v=>onItemSelect(line,v)" />
                    </td>
                    <td><input v-model="line.description" class="inv-ci" placeholder="Description" /></td>
                    <td><input v-model.number="line.qty" type="number" min="0" step="0.001" class="inv-ci inv-ci-r" @input="calcLine(line)" /></td>
                    <td><input v-model.number="line.rate" type="number" min="0" step="0.01" class="inv-ci inv-ci-r" @input="calcLine(line)" /></td>
                    <td class="add-line-amount">{{ fmtCur(line.amount) }}</td>
                    <td style="padding:4px 6px">
                      <button @click="removeLine(line.id)" class="add-line-del"><span v-html="icon('trash',12)"></span></button>
                    </td>
                  </tr>
                  <tr class="add-new-line-row">
                    <td colspan="7" style="padding:6px 14px;border-bottom:none">
                      <button class="add-new-line-btn" @click="addLine">
                        <span v-html="icon('plus',12)"></span> Add new line
                      </button>
                    </td>
                  </tr>
                  <tr v-if="!lines.length">
                    <td colspan="7" style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
                      No line items — click "+ Add Item" to get started
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
            <!-- Totals -->
            <div class="inv-totals-wrap">
              <div style="max-width:160px">
                <label class="inv-lbl">Tax Rate %</label>
                <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="inv-fi" />
              </div>
              <div class="inv-totals">
                <div class="inv-total-row"><span>Subtotal</span><span class="inv-total-amt">{{ fmtCur(subtotal) }}</span></div>
                <div class="inv-total-row" style="color:#6b7280;font-size:12px"><span>Tax ({{ form.tax_rate||0 }}%)</span><span class="inv-total-amt">{{ fmtCur(taxAmount) }}</span></div>
                <div class="inv-total-row inv-grand-total"><span>Grand Total</span><span class="inv-total-amt" style="font-size:16px;color:#1565c0">{{ fmtCur(subtotal+taxAmount) }}</span></div>
              </div>
            </div>
          </div>
        </div>

        <!-- ══ CARD 4: Remarks ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="billCollapsed.remarks=!billCollapsed.remarks">
            <div class="add-card-title">
              <span class="add-card-title-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></span>
              Remarks
            </div>
            <span class="add-card-chevron" :class="{collapsed:billCollapsed.remarks}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:billCollapsed.remarks}">
            <label class="inv-lbl">Internal Remarks <span style="color:#9ca3af;font-weight:400">(not printed)</span></label>
            <textarea v-model="form.remarks" rows="3" class="inv-fi" placeholder="Internal notes for your team…"></textarea>
          </div>
        </div>

      </div><!-- /inv-dbody -->

      <!-- Footer -->
      <div class="inv-dfooter">
        <div class="add-footer-status">{{ editingName ? 'Editing: ' + editingName : 'New bill — unsaved changes' }}</div>
        <div class="add-footer-actions">
          <button class="add-btn-cancel" @click="drawerOpen=false">Cancel</button>
          <button class="add-btn-draft" :disabled="drawerSaving" @click="saveBill(0)">
            <span v-html="icon('save',13)"></span> {{ drawerSaving ? 'Saving…' : 'Save Draft' }}
          </button>
          <button class="add-btn-submit" :disabled="drawerSaving" @click="saveBill(1)">
            <span v-html="icon('check',13)"></span> {{ drawerSaving ? 'Saving…' : 'Submit' }}
          </button>
        </div>
      </div>
    </div>

    <!-- ── View drawer ── -->
    <div v-if="viewOpen" class="inv-drawer-bg" @click.self="viewOpen=false"></div>
    <div class="inv-drawer-panel bill-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">

        <!-- Top header: bill number + badge | Pay CTA -->
        <div class="inv-view-header bill-view-page-header">
          <div class="inv-view-header-left">
            <div class="inv-view-title-row">
              <span class="inv-view-number">{{ viewDoc.name }}</span>
              <span class="inv-hdr-badge" :class="statusCls(viewDoc)">{{ statusLabel(viewDoc) }}</span>
            </div>
            <div class="inv-view-subtitle">
              {{ viewDoc.supplier_name || viewDoc.supplier }}
              <span v-if="viewDoc.due_date"> · Due {{ fmtDate(viewDoc.due_date) }}
                <span v-if="isOverdue(viewDoc)" style="color:#dc2626">(overdue)</span>
              </span>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap">
            <button v-if="flt(viewDoc.outstanding_amount)>0 && viewDoc.docstatus===1"
                    class="inv-view-cta"
                    @click="payBill(viewDoc)">
              <span v-html="icon('indianrupee',15)"></span> Record Payment
            </button>
            <button class="inv-ab-btn" style="padding:7px 12px;font-size:13px" @click="viewOpen=false">
              <span v-html="icon('x',14)"></span> <span class="ab-label">Close</span>
            </button>
          </div>
        </div>

        <!-- Main white card -->
        <div class="inv-view-body">

          <!-- Status timeline -->
          <div class="inv-tl-wrap">
            <div class="inv-tl">
              <div class="inv-tl-progress" :style="{ width: billTlProgressWidth }"></div>
              <template v-for="(step, i) in timelineSteps" :key="i">
                <div class="inv-tl-step"
                     :class="{ 'tl-done': step.done && !step.danger, 'tl-danger': step.danger, 'tl-success': step.success, 'tl-pending': !step.done && !step.danger }">
                  <div class="inv-tl-dot">
                    <span v-if="step.done && !step.danger" v-html="icon('check',14)"></span>
                    <span v-else-if="step.danger" style="font-size:11px;font-weight:800">!</span>
                    <span v-else v-html="icon(step.icon||'circle',14)"></span>
                  </div>
                  <div class="inv-tl-label">{{ step.label }}</div>
                  <div class="inv-tl-date">{{ step.date ? fmtDate(step.date) : '—' }}</div>
                </div>
              </template>
            </div>
          </div>

          <!-- Action buttons bar -->
          <div class="inv-action-bar">
            <button v-if="viewDoc.docstatus===0" class="inv-ab-btn" @click="viewOpen=false;openEdit(viewDoc)">
              <span v-html="icon('edit',13)"></span> <span class="ab-label">Edit</span>
            </button>
            <button class="inv-ab-btn" @click="printBILL(viewDoc)">
              <span v-html="icon('printer',13)"></span> <span class="ab-label">Print</span>
            </button>
            <button v-if="viewDoc.docstatus===1" class="inv-ab-btn" @click="emailBill(viewDoc)">
              <span v-html="icon('mail',13)"></span> <span class="ab-label">Email</span>
            </button>
            <button v-if="viewDoc.docstatus===1" class="inv-ab-btn" @click="issueDebitNote(viewDoc)">
              <span v-html="icon('arrow-left',13)"></span> <span class="ab-label">Debit Note</span>
            </button>
            <button v-if="viewDoc.docstatus===1" class="inv-ab-btn" @click="makeRecurringBill(viewDoc)">
              <span v-html="icon('repeat',13)"></span> <span class="ab-label">Make Recurring</span>
            </button>
            <button v-if="viewDoc.docstatus===1" class="inv-ab-btn inv-ab-danger" @click="cancelBill(viewDoc)">
              Cancel
            </button>
            <button v-if="viewDoc.docstatus===0 || viewDoc.docstatus===2" class="inv-ab-btn inv-ab-danger" @click="deleteBill(viewDoc)">
              <span v-html="icon('trash',13)"></span> <span class="ab-label">Delete</span>
            </button>
          </div>

          <!-- Tabs -->
          <div class="inv-view-tabs">
            <button class="inv-vtab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
            <button class="inv-vtab" :class="{active:viewTab==='payments'}" @click="viewTab='payments'">
              Payments<span v-if="viewPayments.length" class="inv-vtab-count">{{ viewPayments.length }}</span>
            </button>
          </div>

          <!-- ── Details tab ── -->
          <template v-if="viewTab==='details'">
            <div class="inv-tab-body">

              <!-- Meta row -->
              <div class="inv-details-meta" style="grid-template-columns:repeat(3,1fr)">
                <div class="inv-details-meta-col">
                  <div class="inv-dmeta-icon-row">
                    <span class="inv-dmeta-icon" v-html="icon('user',13)"></span>
                    <span class="inv-dmeta-lbl">Vendor</span>
                  </div>
                  <div class="inv-dmeta-primary">{{ viewDoc.supplier_name||viewDoc.supplier }}</div>
                  <div v-if="viewDoc.bill_no" class="inv-dmeta-secondary">Vendor Bill # {{ viewDoc.bill_no }}</div>
                </div>
                <div class="inv-details-meta-col">
                  <div class="inv-dmeta-icon-row">
                    <span class="inv-dmeta-icon" v-html="icon('calendar',13)"></span>
                    <span class="inv-dmeta-lbl">Bill Date</span>
                  </div>
                  <div class="inv-dmeta-date-val">{{ fmtDate(viewDoc.posting_date) }}</div>
                </div>
                <div class="inv-details-meta-col col-balance">
                  <div class="inv-dmeta-icon-row">
                    <span class="inv-dmeta-icon" v-html="icon('indianrupee',13)"></span>
                    <span class="inv-dmeta-lbl">Balance Due</span>
                  </div>
                  <div class="inv-balance-val"
                       :class="{'is-paid': flt(viewDoc.outstanding_amount)===0, 'is-zero': flt(viewDoc.outstanding_amount)===0}">
                    {{ fmtCur(viewDoc.outstanding_amount) }}
                  </div>
                  <button v-if="flt(viewDoc.outstanding_amount)>0 && viewDoc.docstatus===1"
                          class="inv-rec-pay-btn"
                          @click="payBill(viewDoc)">
                    Record Payment
                  </button>
                </div>
              </div>

              <div v-if="viewLoading" style="padding:24px;text-align:center;color:#9ca3af">Loading details…</div>

              <template v-else>
                <!-- Line items table -->
                <div v-if="viewItems.length" class="inv-items-wrap">
                  <table class="inv-items-table">
                    <thead>
                      <tr>
                        <th style="width:36px">#</th>
                        <th>Item &amp; Description</th>
                        <th class="th-r">Qty</th>
                        <th class="th-r">Rate (₹)</th>
                        <th class="th-r">Amount (₹)</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(it,i) in viewItems" :key="i">
                        <td class="inv-item-num">{{ i+1 }}</td>
                        <td>
                          <div class="inv-item-name">{{ it.item_name||it.item_code }}</div>
                          <div v-if="it.description" class="inv-item-desc">{{ it.description }}</div>
                        </td>
                        <td class="td-r">{{ flt(it.qty) }}</td>
                        <td class="td-r">{{ fmtCur(it.rate) }}</td>
                        <td class="td-r" style="font-weight:600">{{ fmtCur(it.amount) }}</td>
                      </tr>
                    </tbody>
                  </table>

                  <!-- Totals -->
                  <div class="inv-totals-section">
                    <div class="inv-totals-inner">
                      <div class="inv-total-line">
                        <span class="t-lbl">Subtotal</span>
                        <span class="t-amt">{{ fmtCur((viewDoc.grand_total||0)-(viewDoc.total_taxes_and_charges||0)) }}</span>
                      </div>
                      <template v-if="viewDoc.taxes&&viewDoc.taxes.length">
                        <div v-for="(tx,i) in viewDoc.taxes" :key="i" class="inv-total-line">
                          <span class="t-lbl">{{ tx.description||tx.account_head }}</span>
                          <span class="t-amt">{{ fmtCur(tx.tax_amount||tx.amount||0) }}</span>
                        </div>
                      </template>
                      <div v-else class="inv-total-line">
                        <span class="t-lbl">Tax (0%)</span>
                        <span class="t-amt">{{ fmtCur(0) }}</span>
                      </div>
                      <div class="inv-grand-total-line">
                        <span class="inv-grand-lbl">Grand Total</span>
                        <span class="inv-grand-amt">{{ fmtCur(viewDoc.grand_total) }}</span>
                      </div>
                    </div>
                  </div>
                </div>
                <div v-else style="color:#9ca3af;font-size:13px;padding:8px 0">No item details available.</div>
              </template>
            </div>
          </template>

          <!-- ── Payments tab ── -->
          <template v-if="viewTab==='payments'">
            <div class="inv-tab-body">
              <div v-if="viewLoading" style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">Loading payments…</div>
              <div v-else-if="viewPayments.length" class="inv-items-wrap">
                <table class="inv-items-table">
                  <thead>
                    <tr>
                      <th>Date</th>
                      <th>Mode</th>
                      <th>Reference</th>
                      <th class="th-r">Amount</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="p in viewPayments" :key="p.name">
                      <td class="mono-sm">{{ fmtDate(p.payment_date) }}</td>
                      <td>{{ p.mode_of_payment || '—' }}</td>
                      <td class="mono-sm text-muted">{{ p.reference_no || '—' }}</td>
                      <td class="td-r" style="font-weight:600;color:#059669">{{ fmtCur(p.paid_amount) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
              <div v-else style="text-align:center;padding:40px 24px;color:#9ca3af;font-size:13px">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.3" style="margin-bottom:10px"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg>
                <div>No payments recorded yet.</div>
                <div v-if="flt(viewDoc.outstanding_amount)>0 && viewDoc.docstatus===1" style="margin-top:12px">
                  <button class="inv-view-cta" @click="payBill(viewDoc)" style="font-size:12px;padding:7px 14px">₹ Record Payment</button>
                </div>
              </div>
            </div>
          </template>

        </div><!-- /inv-view-body -->

      </template>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiSubmit, apiDelete, apiPOST, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useDocStatus } from "../composables/useDocStatus.js";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { usePaymentDialog } from "../composables/usePaymentDialog.js";
import { useConfirmCascade } from "../composables/useConfirmCascade.js";
import { useReturnNote } from "../composables/useReturnNote.js";
import { useMakeRecurring } from "../composables/useMakeRecurring.js";
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
function printBILL(d) { printDoc(d, { title: "BILL", partyLabel: "Vendor", partyField: "supplier_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();
const { openPayment } = usePaymentDialog();
const { confirmCascade } = useConfirmCascade();
const { openReturnNote } = useReturnNote();

// Status helpers tuned for Purchase Invoice
const { statusLabel, statusCls, statusBg, isOverdue } = useDocStatus({
  dueDateField: "due_date",
  outstandingField: "outstanding_amount",
  fallbackDraftLabel: "Draft",
  fallbackSubmittedLabel: "Unpaid",
});

const activeTab = ref("all");
const tabs = [
  { key: "all",     label: "All" },
  { key: "draft",   label: "Draft" },
  { key: "unpaid",  label: "Unpaid" },
  { key: "overdue", label: "Overdue" },
  { key: "paid",    label: "Paid" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const billCollapsed = reactive({ details: false, billing: true, lines: false, remarks: true });
const viewLoading = ref(false), viewItems = ref([]), viewPayments = ref([]);
const vendors = ref([]), items = ref([]), lines = ref([]), taxAccountHead = ref("");
const sortCol = ref("posting_date"), sortDir = ref("desc");
const copyingLast = ref(false);

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const BILL_CURRENCIES = { INR:"₹", USD:"$", EUR:"€", GBP:"£", AED:"د.إ", SGD:"S$", JPY:"¥", AUD:"A$", CAD:"C$", CHF:"₣" };
const form = reactive({ supplier: "", posting_date: todayStr(), due_date: "", bill_no: "", bill_date: "", tax_rate: 0, remarks: "", currency: "INR", exchange_rate: 1, update_stock: 1, set_warehouse: "", billing_address: "", selected_billing_addr_name: "", cost_center: "" });
const vendorBillingAddrs = ref([]);
const warehouses = ref([]);
async function fetchWarehouses(q=""){try{const co=await resolveCompany();const r=await apiList("Warehouse",{fields:["name","parent_warehouse"],filters:[["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:30});warehouses.value=r.map(x=>({label:x.parent_warehouse?`${x.parent_warehouse} / ${x.name}`:x.name,value:x.name}));}catch{warehouses.value=[];}}
const costCenters = ref([]);
async function fetchCostCenters(){try{const co=await resolveCompany();const r=await apiGET("frappe.client.get_list",{doctype:"Cost Center",fields:JSON.stringify(["name"]),filters:JSON.stringify([["disabled","=",0],["company","=",co],["is_group","=",0]]),order_by:"name asc",limit_page_length:100})||[];costCenters.value=r.map(c=>c.name);}catch{costCenters.value=[];}}

function todayStr() { return new Date().toISOString().slice(0, 10); }
function fmtCur(v) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(Math.abs(flt(v)));
}

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Purchase Invoice", {
      fields: ["name", "supplier", "supplier_name", "posting_date", "due_date", "bill_no", "grand_total", "outstanding_amount", "docstatus", "status"],
      filters: [["is_return", "=", 0]],
      limit: 500,
      order: "posting_date desc",
    });
  } catch (e) { toast.error(e.message || "Failed to load bills"); }
  finally { loading.value = false; }
}
async function loadTaxAccount() {
  try {
    const r = await apiList("Account", { fields: ["name"], filters: [["account_type", "=", "Tax"], ["is_group", "=", 0]], limit: 1 });
    if (r?.length) taxAccountHead.value = r[0].name;
  } catch {}
}

const counts = computed(() => ({
  draft:   list.value.filter(b => b.docstatus === 0).length,
  unpaid:  list.value.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) > 0 && !isOverdue(b)).length,
  overdue: list.value.filter(b => isOverdue(b)).length,
  paid:    list.value.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) <= 0).length,
}));
const summary = computed(() => ({
  totalUnpaid:   list.value.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) > 0 && !isOverdue(b)).reduce((s, b) => s + flt(b.outstanding_amount), 0),
  overdueCount:  counts.value.overdue,
  totalDue:      list.value.filter(b => b.docstatus === 1).reduce((s, b) => s + flt(b.outstanding_amount), 0),
}));
const _bYM  = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _bLYM = () => { const d=new Date(); d.setMonth(d.getMonth()-1); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _bTrend = (a,b) => { if(!b&&!a) return {pct:0,up:true}; if(!b) return {pct:100,up:true}; const p=Math.round((a-b)/b*100); return {pct:Math.abs(p),up:p>=0}; };
const billThisMonth = computed(()=>{ const ym=_bYM(); const r=list.value.filter(b=>(b.posting_date||'').startsWith(ym)); return {count:r.length,spend:r.reduce((s,b)=>s+flt(b.grand_total),0)}; });
const billAvg = computed(()=>{ const p=list.value.filter(b=>b.grand_total>0); return p.length?p.reduce((s,b)=>s+flt(b.grand_total),0)/p.length:0; });
const billTrends = computed(()=>({
  total:  _bTrend(billThisMonth.value.count, list.value.filter(b=>(b.posting_date||'').startsWith(_bLYM())).length),
  unpaid: _bTrend(counts.value.unpaid, list.value.filter(b=>(b.posting_date||'').startsWith(_bLYM())&&b.docstatus===1&&flt(b.outstanding_amount)>0&&!isOverdue(b)).length),
  overdue:_bTrend(counts.value.overdue, list.value.filter(b=>(b.posting_date||'').startsWith(_bLYM())&&isOverdue(b)).length),
  paid:   _bTrend(counts.value.paid, list.value.filter(b=>(b.posting_date||'').startsWith(_bLYM())&&b.docstatus===1&&flt(b.outstanding_amount)<=0).length),
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value === "draft")   r = r.filter(b => b.docstatus === 0);
  if (activeTab.value === "unpaid")  r = r.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) > 0 && !isOverdue(b));
  if (activeTab.value === "overdue") r = r.filter(b => isOverdue(b));
  if (activeTab.value === "paid")    r = r.filter(b => b.docstatus === 1 && flt(b.outstanding_amount) <= 0);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.supplier_name || x.supplier || "").toLowerCase().includes(q)
      || (x.bill_no || "").toLowerCase().includes(q));
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
const { page, pageSize, paged } = usePagination(sorted, { storageKey: "bills" });
function sortBy(col) {
  if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  else { sortCol.value = col; sortDir.value = "asc"; }
}
function sortArrow(col) {
  if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>';
  return sortDir.value === "asc" ? "↑" : "↓";
}

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(b => selected.value.has(b.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(b => b.name)) : new Set(); }

// ── Timeline ──────────────────────────────────────────────────────────────
const timelineSteps = computed(() => {
  const b = viewDoc.value;
  if (!b) return [];
  if (b.docstatus === 2) {
    return [
      { key: "draft", label: "Draft", done: true },
      { key: "submitted", label: "Submitted", done: true },
      { key: "cancelled", label: "Cancelled", danger: true, current: true },
    ];
  }
  const paid = b.docstatus === 1 && flt(b.outstanding_amount) <= 0;
  const overdue = isOverdue(b);
  return [
    { key: "draft",     label: "Draft", done: true },
    { key: "submitted", label: "Submitted", done: b.docstatus >= 1, current: b.docstatus === 1 && !paid },
    { key: "paid",      label: overdue ? "Overdue" : "Paid", done: paid, danger: overdue && !paid, current: paid },
  ];
});

const billTlProgressWidth = computed(() => {
  const steps = timelineSteps.value;
  if (!steps.length) return "0%";
  const doneIdx = steps.reduce((last, s, i) => (s.done || s.danger) ? i : last, -1);
  if (doneIdx < 0) return "0%";
  const pct = (doneIdx / (steps.length - 1)) * 100;
  return pct + "%";
});
function openNew() {
  editingName.value = "";
  Object.assign(form, { supplier: "", posting_date: todayStr(), due_date: "", bill_no: "", bill_date: "", tax_rate: 0, remarks: "", currency: "INR", exchange_rate: 1, update_stock: 1, set_warehouse: "", billing_address: "", selected_billing_addr_name: "", cost_center: "" });
  vendorBillingAddrs.value = [];
  lines.value = [blankLine()];
  Object.assign(billCollapsed, { details: false, billing: true, lines: false, remarks: true });
  fetchVendors(""); fetchItems(""); fetchWarehouses("");
  drawerOpen.value = true;
}
async function openEdit(b) {
  editingName.value = b.name;
  Object.assign(form, { supplier: b.supplier || "", posting_date: b.posting_date || todayStr(), due_date: b.due_date || "", bill_no: b.bill_no || "", bill_date: b.bill_date || "", tax_rate: 0, remarks: b.remarks || "", currency: "INR", exchange_rate: 1, update_stock: 1, set_warehouse: "", billing_address: "", selected_billing_addr_name: "", cost_center: "" });
  vendorBillingAddrs.value = [];
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems(""); fetchWarehouses("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Purchase Invoice", b.name);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || "",
        qty: i.qty || 1, rate: i.rate || 0, amount: i.amount || 0,
      }));
    }
    if (doc?.currency) form.currency = doc.currency;
    if (doc?.conversion_rate) form.exchange_rate = doc.conversion_rate;
    if (doc?.taxes?.[0]?.rate) form.tax_rate = doc.taxes[0].rate;
    if (doc?.taxes?.[0]?.account_head) taxAccountHead.value = doc.taxes[0].account_head;
    if (doc?.update_stock !== undefined) form.update_stock = doc.update_stock ? 1 : 0;
    if (doc?.set_warehouse) form.set_warehouse = doc.set_warehouse;
    if (doc?.billing_address) form.billing_address = doc.billing_address;
    if (doc?.cost_center) form.cost_center = doc.cost_center;
    // Load vendor addresses
    if (b.supplier) {
      try {
        const addrs = await apiList("Address", {
          fields: ["name","address_title","address_line1","address_line2","city","state","pincode"],
          filters:[["Dynamic Link","link_name","=",b.supplier],["Dynamic Link","link_doctype","=","Supplier"],["address_type","=","Billing"]],
          order:"`tabAddress`.modified desc", limit:20,
        });
        vendorBillingAddrs.value = addrs || [];
        if (!form.billing_address && addrs?.[0]) {
          const a = addrs[0];
          form.billing_address = [a.address_line1,a.address_line2,a.city,a.state,a.pincode].filter(Boolean).join(", ");
          form.selected_billing_addr_name = a.name;
        }
      } catch {}
    }
  } catch {}
}
async function openView(b) {
  viewDoc.value = b;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  viewPayments.value = [];
  try {
    const [doc, payments] = await Promise.all([
      apiGet("Purchase Invoice", b.name),
      b.docstatus === 1 ? apiGET("zoho_books_clone.api.docs.get_bill_payments", { bill_name: b.name }) : Promise.resolve([]),
    ]);
    viewItems.value = doc?.items || [];
    viewPayments.value = (payments || []).filter(p => p.docstatus === 1);
  } catch (e) { /* keep dialog open */ }
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
    const r = await apiList("Item", { fields: ["name", "item_name", "standard_rate", "stock_uom"], filters: f, limit: 30, order: "item_name asc" });
    items.value = r.map(x => ({ ...x, label: x.item_name || x.name, value: x.name, rate: x.standard_rate || 0 }));
  } catch { items.value = []; }
}
async function onVendorSelect(_opt) {
  form.billing_address = ""; form.selected_billing_addr_name = "";
  vendorBillingAddrs.value = [];
  if (!form.supplier) return;
  try {
    const addrs = await apiList("Address", {
      fields: ["name","address_title","address_line1","address_line2","city","state","pincode"],
      filters: [["Dynamic Link","link_name","=",form.supplier],["Dynamic Link","link_doctype","=","Supplier"],["address_type","=","Billing"]],
      order: "`tabAddress`.modified desc", limit: 20,
    });
    vendorBillingAddrs.value = addrs || [];
    if (addrs?.[0]) {
      const a = addrs[0];
      form.billing_address = [a.address_line1,a.address_line2,a.city,a.state,a.pincode].filter(Boolean).join(", ");
      form.selected_billing_addr_name = a.name;
    }
  } catch {}
}
function applyVendorBillingAddr() {
  const a = vendorBillingAddrs.value.find(x=>x.name===form.selected_billing_addr_name);
  if (a) form.billing_address = [a.address_line1,a.address_line2,a.city,a.state,a.pincode].filter(Boolean).join(", ");
}
function onItemSelect(line, opt) {
  line.item_code = opt?.value ?? opt;
  if (opt?.rate) { line.rate = Number(opt.rate) || 0; calcLine(line); }
}
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }
const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const taxAmount = computed(() => Math.round(subtotal.value * flt(form.tax_rate) / 100 * 100) / 100);

async function copyLastItems() {
  if (!form.supplier) return;
  copyingLast.value = true;
  try {
    const r = await apiGET("zoho_books_clone.api.docs.get_party_last_items", { party_type: "Supplier", party: form.supplier, limit: 20 });
    if (r?.items?.length) {
      lines.value = r.items.map(it => ({
        id: _id++, item_code: it.item_code || "", description: it.description || it.item_name || "",
        qty: flt(it.qty) || 1, rate: flt(it.rate) || 0,
        amount: Math.round(flt(it.qty || 1) * flt(it.rate || 0) * 100) / 100,
      }));
      toast.success(`Copied ${r.items.length} item(s) from ${r.source || "last bill"}`);
    } else { toast.info("No previous items found for this vendor"); }
  } catch (e) { toast.error("Failed to copy items"); }
  copyingLast.value = false;
}

async function saveBill(submit) {
  if (!form.supplier) return toast.error("Vendor is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  if (form.update_stock && !form.set_warehouse) return toast.error("Receiving Warehouse is required when Update Inventory is on");
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const taxes = form.tax_rate > 0 && taxAccountHead.value
      ? [{ doctype: "Tax Line", charge_type: "On Net Total", account_head: taxAccountHead.value, description: taxAccountHead.value, rate: form.tax_rate }]
      : [];
    const doc = {
      doctype: "Purchase Invoice", company,
      supplier: form.supplier, posting_date: form.posting_date,
      due_date: form.due_date || null, bill_no: form.bill_no || "",
      bill_date: form.bill_date || null, remarks: form.remarks || "",
      update_stock: form.update_stock ? 1 : 0, set_warehouse: form.set_warehouse || "",
      billing_address: form.billing_address || "",
      cost_center: form.cost_center || "",
      currency: form.currency || "INR",
      conversion_rate: form.currency === "INR" ? 1 : (form.exchange_rate || 1),
      items: lines.value.filter(l => l.item_code).map(l => ({
        doctype: "Purchase Invoice Item", item_code: l.item_code,
        description: l.description || l.item_code,
        qty: flt(l.qty) || 1, rate: flt(l.rate), amount: flt(l.amount),
      })),
      taxes,
    };
    if (editingName.value) doc.name = editingName.value;
    const saved = await apiSave(doc);
    if (submit && saved?.name) await apiSubmit("Purchase Invoice", saved.name);
    toast.success(`Bill ${saved?.name || ""} ${submit ? "submitted" : "saved"}`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save bill"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailBill(b) {
  await openEmail({
    doctype: "Purchase Invoice", name: b.name,
    docLabel: `Bill ${b.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_bill_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_bill_email",
    paramKey: "bill_name",
  });
}
async function payBill(b) {
  const paid = await openPayment({
    direction: "pay", doctype: "Purchase Invoice", name: b.name,
    party: b.supplier, partyLabel: b.supplier_name || b.supplier,
    balance: flt(b.outstanding_amount),
    sendEndpoint: "zoho_books_clone.api.docs.record_vendor_payment",
    paramKey: "bill_name",
  });
  if (paid) { await load(); if (viewDoc.value?.name === b.name) await openView(b); }
}
async function issueDebitNote(b) {
  // Pre-fill items from the bill
  let billItems = viewItems.value;
  if (!billItems.length) {
    try { const doc = await apiGet("Purchase Invoice", b.name); billItems = doc?.items || []; }
    catch { billItems = []; }
  }
  const result = await openReturnNote({
    kind: "debit", parentName: b.name, party: b.supplier,
    items: billItems.map(i => ({ item_code: i.item_code, item_name: i.item_name, description: i.description, qty: i.qty, rate: i.rate })),
    existingEndpoint: "zoho_books_clone.api.docs.get_debit_notes",
    createEndpoint: "zoho_books_clone.api.docs.create_debit_note",
    paramKey: "bill_name",
    partyKey: "vendor",
    parentKey: "against_bill",
  });
  if (result) { await load(); if (viewDoc.value?.name === b.name) await openView(b); }
}

async function makeRecurringBill(b) {
  const { openMakeRecurring } = useMakeRecurring();
  const subName = await openMakeRecurring({
    doctype: "Purchase Invoice",
    name: b.name,
    partyLabel: b.supplier_name || b.supplier || "",
    amount: b.grand_total || 0,
  });
  if (subName) toast(`Recurring subscription ${subName} created`);
}

async function cancelBill(b) {
  let payments = [];
  try { payments = await apiGET("zoho_books_clone.api.docs.get_bill_payments", { bill_name: b.name }) || []; } catch {}
  const submittedPays = payments.filter(p => p.docstatus === 1);
  if (submittedPays.length) {
    const ok = await confirmCascade({
      title: "Cancel Bill & Payments",
      message: `${b.name} has ${submittedPays.length} linked payment(s). Both must be cancelled together.`,
      actionLabel: "Cancel Both",
      links: submittedPays.map(p => ({ name: p.name, mode: p.mode_of_payment, date: p.payment_date, amount: p.paid_amount })),
    });
    if (!ok) return;
    try {
      await apiPOST("zoho_books_clone.api.docs.cancel_bill_with_payments", { bill_name: b.name });
      toast.success("Bill and payment(s) cancelled");
      await load(); if (viewDoc.value?.name === b.name) await openView(b);
    } catch (e) { toast.error(e.message || "Cancel failed"); }
  } else {
    if (!await confirm({ title: "Cancel Bill", body: `Cancel ${b.name}? This cannot be undone.`, okLabel: "Cancel Bill" })) return;
    try {
      await apiPOST("zoho_books_clone.api.docs.cancel_doc", { doctype: "Purchase Invoice", name: b.name });
      toast.success("Bill cancelled");
      await load(); if (viewDoc.value?.name === b.name) await openView(b);
    } catch (e) { toast.error(e.message || "Cancel failed"); }
  }
}
async function deleteBill(b) {
  if (!await confirm({ title: "Delete Bill", body: `Permanently delete ${b.name}? This cannot be undone.`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Purchase Invoice", b.name);
    toast.success("Bill deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk actions ──────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(b => selected.value.has(b.name) && b.docstatus === 0);
  if (!drafts.length) { toast.info("No draft bills selected"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft bill(s)?`, okLabel: "Delete" })) return;
  for (const b of drafts) { try { await apiDelete("Purchase Invoice", b.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length} draft bill(s)`);
  await load();
}
async function bulkCancel() {
  const submitted = sorted.value.filter(b => selected.value.has(b.name) && b.docstatus === 1);
  if (!submitted.length) { toast.info("No submitted bills selected"); return; }
  let done = 0, failed = 0;
  for (const b of submitted) {
    try { await apiPOST("zoho_books_clone.api.docs.cancel_bill_with_payments", { bill_name: b.name }); done++; }
    catch (e) { failed++; }
  }
  selected.value = new Set();
  toast.success(`Cancelled ${done} bill(s)${failed ? `; ${failed} failed` : ""}`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(b => selected.value.has(b.name) && b.docstatus === 1);
  if (!subs.length) { toast.info("No submitted bills selected"); return; }
  let sent = 0;
  for (const b of subs) {
    const ok = await openEmail({
      doctype: "Purchase Invoice", name: b.name, docLabel: `Bill ${b.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_bill_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_bill_email",
      paramKey: "bill_name",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} bill(s)`);
}

function exportCSV() {
  const rows = selected.value.size
    ? sorted.value.filter(b => selected.value.has(b.name))
    : sorted.value;
  if (!rows.length) return;
  const head = ["Bill #","Vendor","Vendor Bill #","Date","Due Date","Status","Amount","Balance"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const lines = [head.map(esc).join(",")];
  for (const b of rows) {
    lines.push([b.name, b.supplier_name || b.supplier, b.bill_no || "", b.posting_date || "", b.due_date || "",
      statusLabel(b), Number(b.grand_total || 0).toFixed(2), Number(b.outstanding_amount || 0).toFixed(2)
    ].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + lines.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `bills_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} bill(s)`);
}

onMounted(() => { load(); loadTaxAccount(); fetchCostCenters(); });
</script>

<style scoped>
@import '../styles/list.css';
@import '../styles/view.css';
@import '../styles/edit.css';
@import '../styles/add.css';

/* ── Edit drawer ── */
.bill-edit-drawer { width: 680px; right: -680px; transition: right .22s ease; position: fixed; top: 0; bottom: 0; }
.bill-edit-drawer.open { right: 0; }

/* ── View drawer ── */
.bill-view-drawer { width: 680px; right: -680px; transition: right .22s ease; position: fixed; top: 0; bottom: 0; background: #f5f6f8; display: flex; flex-direction: column; overflow-y: auto; }
.bill-view-drawer.open { right: 0; }

/* ── View page header ── */
.bill-view-page-header {
  padding: 16px 20px 10px;
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  flex-wrap: wrap;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
}
.inv-view-header-left { flex: 1; min-width: 0; }
.inv-view-title-row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; margin-bottom: 4px; }
.inv-view-number { font-size: 18px; font-weight: 800; color: #1a1a2e; }
.inv-view-subtitle { font-size: 13px; color: #6b7280; }
.inv-hdr-badge { display: inline-block; padding: 3px 10px; border-radius: 20px; font-size: 11px; font-weight: 700; letter-spacing: .04em; }

/* ── View CTA button ── */
.inv-view-cta { display: inline-flex; align-items: center; gap: 6px; background: #1a6ef7; color: #fff; border: none; border-radius: 7px; padding: 8px 16px; font-size: 13px; font-weight: 700; cursor: pointer; white-space: nowrap; }
.inv-view-cta:hover { background: #155fd4; }

/* ── inv-view-body wraps everything below header ── */
.inv-view-body { margin: 12px 16px 16px; background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; }

/* ── Status timeline ── */
.inv-tl-wrap { padding: 20px 24px 4px; border-bottom: 1px solid #f0f2f5; }
.inv-tl { position: relative; display: flex; align-items: flex-start; justify-content: space-between; }
.inv-tl-progress { position: absolute; top: 18px; left: 0; height: 3px; background: #1a6ef7; border-radius: 2px; transition: width .4s ease; z-index: 0; }
.inv-tl-step { display: flex; flex-direction: column; align-items: center; gap: 6px; flex: 1; position: relative; z-index: 1; }
.inv-tl-dot { width: 28px; height: 28px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 13px; font-weight: 700; border: 2px solid #e5e7eb; background: #fff; }
.tl-done .inv-tl-dot   { background: #1a6ef7; border-color: #1a6ef7; color: #fff; }
.tl-danger .inv-tl-dot { background: #dc2626; border-color: #dc2626; color: #fff; }
.tl-success .inv-tl-dot{ background: #16a34a; border-color: #16a34a; color: #fff; }
.tl-pending .inv-tl-dot { background: #f9fafb; border-color: #d1d5db; color: #9ca3af; }
.inv-tl-label { font-size: 11.5px; font-weight: 600; color: #374151; }
.tl-danger .inv-tl-label { color: #dc2626; }
.tl-pending .inv-tl-label { color: #9ca3af; }
.inv-tl-date { font-size: 10.5px; color: #9ca3af; }

/* ── Action button bar ── */
.inv-action-bar { display: flex; align-items: center; gap: 6px; padding: 12px 16px; flex-wrap: wrap; border-bottom: 1px solid #f0f2f5; background: #fafafa; }
.inv-ab-btn { display: inline-flex; align-items: center; gap: 5px; background: #fff; border: 1px solid #e5e7eb; border-radius: 6px; padding: 6px 12px; font-size: 12.5px; font-weight: 600; color: #374151; cursor: pointer; white-space: nowrap; font-family: inherit; }
.inv-ab-btn:hover { border-color: #94a3b8; background: #f8fafc; }
.inv-ab-danger { color: #dc2626; border-color: #fca5a5; }
.inv-ab-danger:hover { background: #fee2e2; border-color: #dc2626; }
.ab-label { display: inline; }

/* ── Tabs ── */
.inv-view-tabs { display: flex; gap: 2px; padding: 0 16px; border-bottom: 1px solid #e5e7eb; background: #fff; }
.inv-vtab { background: none; border: none; border-bottom: 2px solid transparent; padding: 10px 14px; font-size: 13px; font-weight: 600; color: #6b7280; cursor: pointer; font-family: inherit; }
.inv-vtab.active { color: #1a6ef7; border-bottom-color: #1a6ef7; }
.inv-vtab-count { background: #eff6ff; color: #1a6ef7; border-radius: 10px; padding: 1px 7px; font-size: 11px; margin-left: 4px; }

/* ── Tab body ── */
.inv-tab-body { padding: 16px; }

/* ── Details meta row ── */
.inv-details-meta { display: grid; gap: 0; border-bottom: 1px solid #f0f2f5; }
.inv-details-meta-col { padding: 16px; border-right: 1px solid #f0f2f5; }
.inv-details-meta-col:last-child { border-right: none; }
.inv-dmeta-icon-row { display: flex; align-items: center; gap: 5px; margin-bottom: 4px; }
.inv-dmeta-icon { color: #9ca3af; }
.inv-dmeta-lbl { font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; color: #9ca3af; }
.inv-dmeta-primary { font-size: 14px; font-weight: 700; color: #111827; margin-bottom: 2px; }
.inv-dmeta-secondary { font-size: 12px; color: #6b7280; }
.inv-dmeta-date-val { font-size: 14px; font-weight: 600; color: #111827; }
.inv-dmeta-date-val.is-overdue { color: #dc2626; }
.col-balance { background: #f8fafc; }
.inv-balance-val { font-size: 20px; font-weight: 800; color: #dc2626; font-family: monospace; }
.inv-balance-val.is-zero, .inv-balance-val.is-paid { color: #16a34a; }
.inv-rec-pay-btn { margin-top: 8px; background: #1a6ef7; color: #fff; border: none; border-radius: 6px; padding: 5px 12px; font-size: 12px; font-weight: 600; cursor: pointer; font-family: inherit; }
.inv-rec-pay-btn:hover { background: #155fd4; }

/* ── Line items table ── */
.inv-items-wrap { margin-top: 16px; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.inv-items-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.inv-items-table th { padding: 9px 12px; background: #f8fafc; border-bottom: 1px solid #e5e7eb; font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: .04em; color: #9ca3af; text-align: left; }
.inv-items-table td { padding: 10px 12px; border-bottom: 1px solid #f0f2f5; }
.inv-items-table tbody tr:last-child td { border-bottom: none; }
.th-r { text-align: right; }
.td-r { text-align: right; }
.inv-item-num { color: #9ca3af; font-size: 12px; text-align: center; }
.inv-item-name { font-weight: 600; color: #111827; }
.inv-item-desc { font-size: 11.5px; color: #6b7280; margin-top: 2px; }

/* ── Totals section (view) ── */
.inv-totals-section { border-top: 1px solid #e5e7eb; background: #f8fafc; padding: 12px 16px; display: flex; justify-content: flex-end; }
.inv-totals-inner { min-width: 240px; display: flex; flex-direction: column; gap: 5px; }
.inv-total-line { display: flex; justify-content: space-between; align-items: center; font-size: 13px; color: #374151; padding: 2px 0; }
.t-lbl { color: #6b7280; }
.t-amt { font-weight: 600; }
.inv-grand-total-line { display: flex; justify-content: space-between; align-items: center; border-top: 1px solid #e5e7eb; padding-top: 8px; margin-top: 4px; }
.inv-grand-lbl { font-size: 14px; font-weight: 700; color: #111827; }
.inv-grand-amt { font-size: 18px; font-weight: 800; color: #1a6ef7; font-family: monospace; }

/* ── Edit drawer: add-card styles ── */
.add-card { border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; margin-bottom: 12px; background: #fff; }
.add-card-header { display: flex; align-items: center; justify-content: space-between; padding: 12px 16px; cursor: pointer; user-select: none; background: #f8fafc; border-bottom: 1px solid #e5e7eb; }
.add-card-title { display: flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: #374151; }
.add-card-title-icon { color: #6b7280; display: flex; }
.add-card-chevron { color: #9ca3af; display: flex; transition: transform .2s; }
.add-card-chevron.collapsed { transform: rotate(-90deg); }
.add-card-body { padding: 16px; transition: all .18s ease; }
.add-card-body.collapsed { display: none; }
.add-details-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.add-line-num { display: inline-block; width: 20px; text-align: center; color: #9ca3af; font-size: 12px; }
.add-line-amount { text-align: right; font-size: 12.5px; font-weight: 600; padding: 4px 8px; color: #374151; }
.add-line-del { background: none; border: 1px solid rgba(220,38,38,.3); border-radius: 4px; padding: 3px 5px; cursor: pointer; color: #dc2626; display: inline-flex; align-items: center; }
.add-new-line-row { }
.add-new-line-btn { display: inline-flex; align-items: center; gap: 5px; background: none; border: none; color: #1a6ef7; font-size: 12.5px; font-weight: 600; cursor: pointer; padding: 4px 0; }
.add-new-line-btn:hover { text-decoration: underline; }
.add-lines-add-btn { display: inline-flex; align-items: center; gap: 4px; background: #eaf1ff; border: 1px solid rgba(26,110,247,.3); color: #1a6ef7; border-radius: 6px; padding: 4px 10px; font-size: 12px; font-weight: 600; cursor: pointer; }
.add-status-badge { display: inline-block; background: #f1f5f9; color: #475569; border-radius: 6px; padding: 2px 10px; font-size: 12px; font-weight: 600; }

/* ── Footer ── */
.add-footer-status { font-size: 12px; color: #9ca3af; }
.add-footer-actions { display: flex; gap: 8px; align-items: center; }
.add-btn-cancel { background: none; border: 1px solid #e5e7eb; border-radius: 7px; padding: 8px 14px; font-size: 13px; font-weight: 600; color: #6b7280; cursor: pointer; font-family: inherit; }
.add-btn-cancel:hover { border-color: #94a3b8; }
.add-btn-draft { display: inline-flex; align-items: center; gap: 5px; background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; border-radius: 7px; padding: 8px 16px; font-size: 13px; font-weight: 700; cursor: pointer; font-family: inherit; }
.add-btn-draft:hover { background: #dcfce7; }
.add-btn-draft:disabled { opacity: .5; cursor: not-allowed; }
.add-btn-submit { display: inline-flex; align-items: center; gap: 5px; background: #1a6ef7; color: #fff; border: none; border-radius: 7px; padding: 8px 16px; font-size: 13px; font-weight: 700; cursor: pointer; font-family: inherit; }
.add-btn-submit:hover { background: #155fd4; }
.add-btn-submit:disabled { opacity: .5; cursor: not-allowed; }

/* ── Row actions cell ── */
.bill-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.bill-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
</style>