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
      <div class="inv-dh">
        <div class="inv-dh-title">{{ editingName ? 'Edit Bill' : 'New Bill' }}</div>
        <button class="inv-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="inv-dbody">
        <div class="inv-fg inv-fg2">
          <div style="grid-column:1/-1">
            <label class="inv-lbl">Vendor <span class="req">*</span></label>
            <SearchableSelect v-model="form.supplier" :options="vendors"
              placeholder="Select vendor…" :createable="true" createDoctype="Supplier"
              @search="fetchVendors" @select="onVendorSelect" />
          </div>
          <div>
            <label class="inv-lbl">Bill Date <span class="req">*</span></label>
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
          <div style="grid-column:1/-1">
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
        </div>

        <!-- Billing Address -->
        <div style="margin-bottom:14px">
          <div style="font-size:11px;font-weight:700;color:#374151;text-transform:uppercase;letter-spacing:.04em;margin-bottom:8px">Billing Address</div>
          <div v-if="vendorBillingAddrs.length > 1" style="margin-bottom:8px">
            <select v-model="form.selected_billing_addr_name" class="inv-fi" @change="applyVendorBillingAddr">
              <option value="">— Select address —</option>
              <option v-for="a in vendorBillingAddrs" :key="a.name" :value="a.name">{{ a.address_title || a.address_line1 }}, {{ a.city }}</option>
            </select>
          </div>
          <textarea v-model="form.billing_address" class="inv-fi" rows="2" style="resize:vertical;width:100%;box-sizing:border-box" placeholder="Auto-filled from vendor, or enter manually"></textarea>
        </div>

        <div class="bill-section-row">
          <div class="inv-sec-lbl" style="border-top:none;padding-top:0;margin-top:0">Items</div>
          <button v-if="form.supplier" class="bill-copy-btn" @click="copyLastItems" :disabled="copyingLast">
            <span v-html="icon('copy',12)"></span> {{ copyingLast ? 'Loading…' : 'Copy Last' }}
          </button>
        </div>
        <div class="bill-items-table">
          <div class="bill-items-head">
            <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
          </div>
          <div v-for="line in lines" :key="line.id" class="bill-items-row">
            <div><SearchableSelect v-model="line.item_code" :options="items"
              placeholder="Select item…" :createable="true" createDoctype="Item"
              @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
            <div><input v-model="line.description" class="inv-fi" placeholder="Description" /></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="inv-fi ta-r" @input="calcLine(line)" /></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="inv-fi ta-r" @input="calcLine(line)" /></div>
            <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
            <div><button @click="removeLine(line.id)" class="inv-rm-line"><span v-html="icon('x',12)"></span></button></div>
          </div>
          <button class="inv-add-line-btn" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <div class="bill-totals">
          <div style="max-width:160px">
            <label class="inv-lbl">Tax Rate %</label>
            <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="inv-fi" />
          </div>
          <div class="bill-totals-right">
            <div class="bill-total-row"><span>Subtotal</span><span>{{ fmtCur(subtotal) }}</span></div>
            <div class="bill-total-row"><span>Tax ({{ form.tax_rate||0 }}%)</span><span>{{ fmtCur(taxAmount) }}</span></div>
            <div class="bill-total-row grand"><span>Total</span><span>{{ fmtCur(subtotal+taxAmount) }}</span></div>
          </div>
        </div>

        <div>
          <label class="inv-lbl">Remarks</label>
          <textarea v-model="form.remarks" rows="2" class="inv-fi" placeholder="Optional…"></textarea>
        </div>
      </div>
      <div class="inv-dfooter">
        <button class="form-btn form-btn-outline" @click="drawerOpen=false">Cancel</button>
        <button class="form-btn form-btn-success" :disabled="drawerSaving" @click="saveBill(0)">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}
        </button>
        <button class="form-btn form-btn-primary" :disabled="drawerSaving" @click="saveBill(1)">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}
        </button>
      </div>
    </div>

    <!-- ── View drawer ── -->
    <div v-if="viewOpen" class="inv-drawer-bg" @click.self="viewOpen=false"></div>
    <div class="inv-drawer-panel bill-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="inv-view-header bill-view-head">
          <div>
            <div class="inv-view-number">{{ viewDoc.name }}</div>
            <div class="inv-view-subtitle">{{ viewDoc.supplier_name||viewDoc.supplier }}</div>
          </div>
          <div style="text-align:right">
            <div class="bill-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="inv-hdr-badge" :class="statusCls(viewDoc)">{{ statusLabel(viewDoc) }}</span>
          </div>
          <button class="inv-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <TimelineStepper :steps="timelineSteps" />

        <div class="inv-view-tabs">
          <button class="inv-vtab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="inv-vtab" :class="{active:viewTab==='payments'}" @click="viewTab='payments'">
            Payments<span v-if="viewPayments.length" class="inv-vtab-count">{{ viewPayments.length }}</span>
          </button>
        </div>

        <div class="inv-dbody">
          <template v-if="viewTab==='details'">
            <div class="bill-meta-grid">
              <div><div class="bill-meta-lbl">Bill Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
              <div><div class="bill-meta-lbl">Due Date</div>
                <div class="mono-sm" :class="isOverdue(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.due_date)||'—' }}</div>
              </div>
              <div><div class="bill-meta-lbl">Vendor Bill #</div><div class="mono-sm">{{ viewDoc.bill_no||'—' }}</div></div>
              <div><div class="bill-meta-lbl">Outstanding</div><div class="mono-sm" :class="flt(viewDoc.outstanding_amount)>0?'text-danger':'text-success'">{{ fmtCur(viewDoc.outstanding_amount) }}</div></div>
            </div>

            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading details…</div>
            <template v-else>
              <div v-if="viewItems.length" class="bill-meta-lbl" style="margin-top:12px">Line Items</div>
              <div v-if="viewItems.length" class="bill-view-items">
                <div class="bill-view-items-head">
                  <span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span>
                </div>
                <div v-for="it in viewItems" :key="it.name" class="bill-view-items-row">
                  <span><strong>{{ it.item_name||it.item_code }}</strong>
                    <div v-if="it.description" class="text-muted" style="font-size:11px">{{ it.description }}</div></span>
                  <span class="ta-r mono-sm">{{ it.qty }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(it.amount) }}</span>
                </div>
              </div>
            </template>
          </template>

          <template v-if="viewTab==='payments'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading payments…</div>
            <div v-else-if="viewPayments.length">
              <div class="bill-pay-head">
                <span>Date</span><span>Mode</span><span>Reference</span><span class="ta-r">Amount</span>
              </div>
              <div v-for="p in viewPayments" :key="p.name" class="bill-pay-row">
                <span class="mono-sm">{{ fmtDate(p.payment_date) }}</span>
                <span>{{ p.mode_of_payment || '—' }}</span>
                <span class="mono-sm text-muted">{{ p.reference_no || '—' }}</span>
                <span class="ta-r mono-sm" style="font-weight:600;color:#059669">{{ fmtCur(p.paid_amount) }}</span>
              </div>
            </div>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
              No payments recorded yet.
              <div v-if="flt(viewDoc.outstanding_amount)>0 && viewDoc.docstatus===1" style="margin-top:8px">
                <button class="form-btn form-btn-primary" @click="payBill(viewDoc)" style="font-size:12px;padding:6px 12px">₹ Record Payment</button>
              </div>
            </div>
          </template>
        </div>

        <div class="inv-dfooter">
          <button class="form-btn form-btn-outline" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="form-btn form-btn-success" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button v-if="viewDoc.docstatus===1" class="form-btn form-btn-outline" @click="emailBill(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="form-btn form-btn-outline" @click="printBILL(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="viewDoc.docstatus===1 && flt(viewDoc.outstanding_amount)>0" class="form-btn form-btn-primary" @click="payBill(viewDoc)">
            ₹ Record Payment
          </button>
          <button v-if="viewDoc.docstatus===1" class="form-btn form-btn-danger" @click="issueDebitNote(viewDoc)">
            <span v-html="icon('arrow-left',13)"></span> Issue Debit Note
          </button>
          <button v-if="viewDoc.docstatus===1" class="form-btn form-btn-outline" @click="makeRecurringBill(viewDoc)">
            <span v-html="icon('repeat',13)"></span> Make Recurring
          </button>
          <button v-if="viewDoc.docstatus===1" class="form-btn form-btn-danger" @click="cancelBill(viewDoc)">
            Cancel
          </button>
          <button v-if="viewDoc.docstatus===0 || viewDoc.docstatus===2" class="form-btn form-btn-danger" @click="deleteBill(viewDoc)">
            Delete
          </button>
        </div>
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
const viewLoading = ref(false), viewItems = ref([]), viewPayments = ref([]);
const vendors = ref([]), items = ref([]), lines = ref([]), taxAccountHead = ref("");
const sortCol = ref("posting_date"), sortDir = ref("desc");
const copyingLast = ref(false);

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const BILL_CURRENCIES = { INR:"₹", USD:"$", EUR:"€", GBP:"£", AED:"د.إ", SGD:"S$", JPY:"¥", AUD:"A$", CAD:"C$", CHF:"₣" };
const form = reactive({ supplier: "", posting_date: todayStr(), due_date: "", bill_no: "", bill_date: "", tax_rate: 0, remarks: "", currency: "INR", exchange_rate: 1, update_stock: 1, set_warehouse: "", billing_address: "", selected_billing_addr_name: "" });
const vendorBillingAddrs = ref([]);
const warehouses = ref([]);
async function fetchWarehouses(q=""){try{const co=await resolveCompany();const r=await apiList("Warehouse",{fields:["name","parent_warehouse"],filters:[["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:30});warehouses.value=r.map(x=>({label:x.parent_warehouse?`${x.parent_warehouse} / ${x.name}`:x.name,value:x.name}));}catch{warehouses.value=[];}}

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

// ── Create/Edit ───────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { supplier: "", posting_date: todayStr(), due_date: "", bill_no: "", bill_date: "", tax_rate: 0, remarks: "", currency: "INR", exchange_rate: 1, update_stock: 1, set_warehouse: "", billing_address: "", selected_billing_addr_name: "" });
  vendorBillingAddrs.value = [];
  lines.value = [blankLine()];
  fetchVendors(""); fetchItems(""); fetchWarehouses("");
  drawerOpen.value = true;
}
async function openEdit(b) {
  editingName.value = b.name;
  Object.assign(form, { supplier: b.supplier || "", posting_date: b.posting_date || todayStr(), due_date: b.due_date || "", bill_no: b.bill_no || "", bill_date: b.bill_date || "", tax_rate: 0, remarks: b.remarks || "", currency: "INR", exchange_rate: 1, update_stock: 1, set_warehouse: "", billing_address: "", selected_billing_addr_name: "" });
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

onMounted(() => { load(); loadTaxAccount(); });
</script>

<style scoped>
/* ── Edit drawer: narrower than default 720px ── */
.bill-edit-drawer { width: 600px; right: -600px; transition: right .22s ease; position: fixed; top: 0; bottom: 0; }
.bill-edit-drawer.open { right: 0; }

/* ── View drawer: even narrower ── */
.bill-view-drawer { width: 540px; right: -540px; transition: right .22s ease; position: fixed; top: 0; bottom: 0; }
.bill-view-drawer.open { right: 0; }

/* ── View header: flat (no status-based background) ── */
.bill-view-head {
  position: relative;
  flex-shrink: 0;
  border-bottom: 1px solid #e5e7eb;
  background: #f8fafc !important;
  padding: 20px;
}
.bill-view-head .inv-view-number { color: #1a1a2e; }
.bill-view-head .inv-view-subtitle { color: #6b7280; }
.bill-view-amount { font-size: 22px; font-weight: 800; font-family: monospace; color: #1a1a2e; }

/* ── Meta grid in view ── */
.bill-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.bill-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }

/* ── Line items table (edit drawer) ── */
.bill-section-row { display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px; }
.bill-copy-btn { background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; padding: 4px 10px; border-radius: 6px; font: inherit; font-size: 11.5px; font-weight: 600; cursor: pointer; display: inline-flex; align-items: center; gap: 4px; margin-left: 8px; }
.bill-copy-btn:hover { background: #dcfce7; }
.bill-copy-btn:disabled { opacity: .5; cursor: not-allowed; }
.bill-items-table { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 8px; }
.bill-items-head { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #374151; }
.bill-items-row { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; }

/* ── Totals block ── */
.bill-totals { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.bill-totals-right { display: flex; flex-direction: column; gap: 4px; min-width: 220px; }
.bill-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 3px 0; }
.bill-total-row.grand { font-weight: 700; font-size: 14px; color: #111827; border-top: 1px solid #e5e7eb; padding-top: 6px; margin-top: 2px; }

/* ── View: line items grid ── */
.bill-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.bill-view-items-head { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.bill-view-items-row { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }

/* ── View: payments grid ── */
.bill-pay-head { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; border-radius: 6px 6px 0 0; border: 1px solid #e5e7eb; border-bottom: none; }
.bill-pay-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb; align-items: center; font-size: 12.5px; }
.bill-pay-row:last-child { border-bottom: 1px solid #e5e7eb; border-radius: 0 0 6px 6px; }

/* ── Row actions cell ── */
.bill-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.bill-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
</style>
