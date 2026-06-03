<template>
<div class="inv-page">

  <!-- ── Unified toolbar (matches e-Way Bills) ── -->
  <div class="sales-toolbar">
    <div class="sales-search">
      <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
      <input v-model="search" placeholder="Search invoices, customers, PO…" class="sales-search-input"/>
    </div>
    <div class="sales-pills">
      <button v-for="f in FILTERS" :key="f.key" class="sales-pill" :class="{ active: activeFilter===f.key, ['pill-'+f.key]: f.key!=='all' }" @click="activeFilter=f.key">
        {{ f.label }}<span v-if="f.key!=='all'" class="sales-pill-count">{{ counts[f.key] }}</span>
      </button>
    </div>
    <div class="sales-actions">
      <select v-model="filterCustomer" class="sales-select" title="Filter by customer">
        <option value="">All Customers</option>
        <option v-for="c in customers" :key="c.name" :value="c.name">{{ c.customer_name }}</option>
      </select>
      <select v-model="dateRange" class="sales-select" title="Date range">
        <option v-for="dr in DATE_RANGES" :key="dr.key" :value="dr.key">{{ dr.label }}</option>
      </select>
      <button class="sales-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
      <button class="sales-btn-ghost" @click="load" title="Refresh" :disabled="loading"><span v-html="icon('refresh',14)"></span></button>
      <button class="sales-btn-primary" @click="openAdd">
        <span v-html="icon('plus',13)"></span> New Invoice
      </button>
    </div>
  </div>

  <!-- Custom-date inputs surface below toolbar only when needed -->
  <div v-if="dateRange==='custom'" class="sales-custom-date">
    <span style="font-size:12px;color:#6b7280;font-weight:600">Date range:</span>
    <input type="date" v-model="customFrom" class="sales-date-input"/>
    <span style="color:#9ca3af;font-size:12px">to</span>
    <input type="date" v-model="customTo" class="sales-date-input"/>
  </div>

  <!-- ── KPI Cards ── -->
  <div class="bk-kpi-grid">
    <div class="bk-kpi-card bk-kpi-accent clickable" @click="activeFilter='all'">
      <div class="bk-kpi-inner">
        <div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/></svg></div>
        <div class="bk-kpi-body">
          <div class="bk-kpi-label">Total Invoices</div>
          <div class="bk-kpi-value">{{ list.length }}</div>
          <div class="bk-kpi-trend" :class="invTrends.total.up?'bk-trend-up':'bk-trend-down'">{{ invTrends.total.up?'↑':'↓' }} {{ invTrends.total.pct }}% vs last month</div>
        </div>
      </div>
    </div>
    <div class="bk-kpi-card clickable" @click="activeFilter='Draft'">
      <div class="bk-kpi-inner">
        <div class="bk-kpi-icon" style="background:#e2e8f0"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#475569" stroke-width="1.8"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></div>
        <div class="bk-kpi-body">
          <div class="bk-kpi-label">Draft</div>
          <div class="bk-kpi-value">{{ counts.Draft }}</div>
          <div class="bk-kpi-trend" :class="invTrends.draft.up?'bk-trend-up':'bk-trend-down'">{{ invTrends.draft.up?'↑':'↓' }} {{ invTrends.draft.pct }}% vs last month</div>
        </div>
      </div>
    </div>
    <div class="bk-kpi-card bk-kpi-warn clickable" @click="activeFilter='Unpaid'">
      <div class="bk-kpi-inner">
        <div class="bk-kpi-icon" style="background:#fef3c7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg></div>
        <div class="bk-kpi-body">
          <div class="bk-kpi-label">Unpaid</div>
          <div class="bk-kpi-value bk-kpi-amber">{{ counts.Unpaid }}</div>
          <div class="bk-kpi-trend" :class="invTrends.unpaid.up?'bk-trend-up':'bk-trend-down'">{{ invTrends.unpaid.up?'↑':'↓' }} {{ invTrends.unpaid.pct }}% vs last month</div>
        </div>
      </div>
    </div>
    <div class="bk-kpi-card bk-kpi-danger clickable" @click="activeFilter='Overdue'">
      <div class="bk-kpi-inner">
        <div class="bk-kpi-icon" style="background:#fee2e2"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="1.8"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg></div>
        <div class="bk-kpi-body">
          <div class="bk-kpi-label">Overdue</div>
          <div class="bk-kpi-value bk-kpi-red">{{ counts.Overdue }}</div>
          <div class="bk-kpi-trend" :class="invTrends.overdue.up?'bk-trend-down':'bk-trend-up'">{{ invTrends.overdue.up?'↑':'↓' }} {{ invTrends.overdue.pct }}% vs last month</div>
        </div>
      </div>
    </div>
    <div class="bk-kpi-card bk-kpi-success clickable" @click="activeFilter='Paid'">
      <div class="bk-kpi-inner">
        <div class="bk-kpi-icon" style="background:#dcfce7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#16a34a" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div>
        <div class="bk-kpi-body">
          <div class="bk-kpi-label">Paid</div>
          <div class="bk-kpi-value bk-kpi-green">{{ counts.Paid }}</div>
          <div class="bk-kpi-trend" :class="invTrends.paid.up?'bk-trend-up':'bk-trend-down'">{{ invTrends.paid.up?'↑':'↓' }} {{ invTrends.paid.pct }}% vs last month</div>
        </div>
      </div>
    </div>
  </div>
  <!-- Secondary stats -->
  <div class="bk-stat-grid">
    <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month</div><div class="bk-stat-value">{{ invThisMonth.count }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
    <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month Revenue</div><div class="bk-stat-value" style="font-size:16px">{{ fmtAmt(invThisMonth.revenue) }}</div></div><div class="bk-stat-icon" style="background:#dcfce7;color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div></div></div>
    <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Total Receivable</div><div class="bk-stat-value bk-kpi-amber" style="font-size:16px">{{ fmtAmt(summary.totalDue) }}</div></div><div class="bk-stat-icon" style="background:#fef3c7;color:#d97706"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg></div></div></div>
    <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Avg Invoice Value</div><div class="bk-stat-value" style="font-size:16px">{{ fmtAmt(invAvg) }}</div></div><div class="bk-stat-icon" style="background:#e5e7eb;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div></div></div>
  </div>

  <!-- ── Bulk actions bar ── -->
  <div v-if="selectedRows.size>0" class="inv-bulk-bar">
    <span class="inv-bulk-count">{{ selectedRows.size }} selected</span>
    <button class="inv-bulk-btn" @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
    <button class="inv-bulk-btn" @click="bulkCancel">Cancel Submitted</button>
    <button class="inv-bulk-btn inv-bulk-danger" @click="bulkDelete">Delete Drafts</button>
    <button class="inv-bulk-btn" @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    <button class="inv-bulk-clear" @click="selectedRows=new Set()">✕ Clear</button>
  </div>

  <!-- ── Table ── -->
  <div class="inv-table-wrap">
    <table class="inv-table">
      <thead><tr>
        <th class="th-check"><input type="checkbox" @change="toggleAll" :checked="allSelected"/></th>
        <th class="sortable" @click="sort('posting_date')">DATE <span class="sort-arrow">{{ sortArrow('posting_date') }}</span></th>
        <th class="sortable" @click="sort('name')">INVOICE# <span class="sort-arrow">{{ sortArrow('name') }}</span></th>
        <th class="sortable" @click="sort('customer_name')">CUSTOMER <span class="sort-arrow">{{ sortArrow('customer_name') }}</span></th>
        <th class="sortable" @click="sort('due_date')">DUE DATE <span class="sort-arrow">{{ sortArrow('due_date') }}</span></th>
        <th class="sortable" @click="sort('status')">STATUS <span class="sort-arrow">{{ sortArrow('status') }}</span></th>
        <th class="ta-r sortable" @click="sort('grand_total')">AMOUNT <span class="sort-arrow">{{ sortArrow('grand_total') }}</span></th>
        <th class="ta-r sortable" @click="sort('outstanding_amount')">BALANCE DUE <span class="sort-arrow">{{ sortArrow('outstanding_amount') }}</span></th>
        <th style="width:80px;text-align:center">ACTIONS</th>
      </tr></thead>
      <tbody>
        <template v-if="loading">
          <tr v-for="n in 7" :key="n" class="shimmer-row">
            <td><div class="shimmer" style="width:14px;height:14px;border-radius:3px"></div></td>
            <td><div class="shimmer" style="width:80px"></div></td>
            <td><div class="shimmer" style="width:110px"></div></td>
            <td><div class="shimmer" style="width:130px"></div></td>
            <td><div class="shimmer" style="width:90px"></div></td>
            <td><div class="shimmer" style="width:80px"></div></td>
            <td><div class="shimmer" style="width:80px;margin-left:auto"></div></td>
            <td><div class="shimmer" style="width:80px;margin-left:auto"></div></td>
            <td></td>
          </tr>
        </template>
        <template v-else>
          <tr v-for="inv in paged" :key="inv.name" class="inv-row" :class="{ selected: selectedRows.has(inv.name) }">
            <td class="td-check" @click.stop>
              <input type="checkbox" :checked="selectedRows.has(inv.name)" @change="toggleRow(inv.name)"/>
            </td>
            <td @click="openView(inv)" class="text-muted mono-sm">{{ fmtDate(inv.posting_date) }}</td>
            <td @click="openView(inv)"><span class="inv-link">{{ inv.name }}</span></td>
            <td @click="openView(inv)"><span class="inv-customer">{{ inv.customer_name||inv.customer }}</span></td>
            <td @click="openView(inv)" :class="isOverdue(inv)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(inv.due_date) }}</td>
            <td @click="openView(inv)">
              <span class="inv-status-badge" :class="statusCls(inv)">{{ statusLabel(inv) }}</span>
            </td>
            <td class="ta-r mono-sm" @click="openView(inv)">{{ fmtAmt(inv.grand_total) }}</td>
            <td class="ta-r mono-sm" @click="openView(inv)" :class="inv.outstanding_amount>0?'text-danger':'text-success'">
              {{ fmtAmt(inv.outstanding_amount) }}
            </td>
            <td style="text-align:center" @click.stop>
              <div style="display:flex;gap:4px;justify-content:center">
                <button class="inv-act-btn" @click="openView(inv)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="inv.docstatus===0" class="inv-act-btn" @click="openEdit(inv)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button v-if="inv.docstatus===0||inv.docstatus===2" class="inv-act-btn" style="color:#dc2626" @click.stop="confirmAction('delete',inv)" title="Delete"><span v-html="icon('trash',13)"></span></button>
                <button v-if="inv.outstanding_amount>0&&inv.docstatus===1" class="inv-act-btn inv-act-pay" @click="openPayment(inv)" title="Record Payment">₹</button>
              </div>
            </td>
          </tr>
          <tr v-if="!sorted.length">
            <td colspan="10" class="bk-empty-state">
              <div class="bk-empty-inner">
                <template v-if="search||filterCustomer">
                  <svg width="44" height="44" viewBox="0 0 24 24" fill="none" stroke="#cbd5e1" stroke-width="1.3"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>
                  <p class="bk-empty-title">No invoices match your filters</p>
                </template>
                <template v-else>
                  <div class="bk-empty-illus"><svg width="80" height="96" viewBox="0 0 80 96" fill="none"><rect x="10" y="8" width="60" height="80" rx="6" fill="#e2e8f0"/><rect x="14" y="12" width="52" height="72" rx="4" fill="#fff"/><rect x="22" y="26" width="36" height="3" rx="2" fill="#e2e8f0"/><rect x="22" y="34" width="28" height="3" rx="2" fill="#e2e8f0"/><rect x="22" y="42" width="32" height="3" rx="2" fill="#e2e8f0"/><rect x="22" y="58" width="20" height="3" rx="2" fill="#e2e8f0"/><rect x="22" y="66" width="24" height="3" rx="2" fill="#e2e8f0"/><rect x="8" y="22" width="20" height="20" rx="4" fill="#2563eb" opacity=".85"/><line x1="13" y1="32" x2="23" y2="32" stroke="#fff" stroke-width="2" stroke-linecap="round"/><line x1="18" y1="27" x2="18" y2="37" stroke="#fff" stroke-width="2" stroke-linecap="round"/></svg></div>
                  <p class="bk-empty-title">No invoices created yet</p>
                  <p class="bk-empty-sub">Create your first invoice to start tracking payments and revenue.</p>
                  <button class="bk-empty-btn" @click="openAdd"><span v-html="icon('plus',13)"></span> New Invoice</button>
                </template>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
  <div v-if="!loading && sorted.length" style="padding:12px 20px 4px">
    <Pagination
      v-model:page="page"
      v-model:page-size="pageSize"
      :total-items="sorted.length"
    />
  </div>

  <!-- ══ Modals / Drawers ══ -->
  <Teleport to="body">

    <!-- ── Create / Edit Drawer ── -->
    <div v-if="drawerOpen" class="inv-drawer-bg" @click.self="drawerOpen=false">
      <div class="inv-drawer-panel" :class="{'inv-split':showPreview}">
        <div class="inv-dh">
          <div>
            <div class="inv-dh-title">{{ editingName ? 'Edit Invoice' : 'New Invoice' }}</div>
            <div class="inv-dh-sub">{{ editingName || 'Fill in the details below' }}</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <button class="inv-preview-toggle" @click="showPreview=!showPreview" :title="showPreview?'Hide preview':'Live preview'">
              <span v-html="icon('eye',13)"></span> {{ showPreview ? 'Hide' : 'Preview' }}
            </button>
            <button class="inv-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
          </div>
        </div>

        <!-- Template / branding toolbar -->
        <div class="inv-tmpl-bar">
          <div class="inv-tmpl-group">
            <span class="inv-tmpl-lbl">Template</span>
            <div class="inv-tmpl-btns">
              <button v-for="t in TEMPLATES" :key="t.key" class="inv-tmpl-btn" :class="{active:selectedTemplate===t.key}" @click="selectedTemplate=t.key;saveBranding()">{{ t.label }}</button>
            </div>
          </div>
          <label class="inv-tmpl-group">
            <span class="inv-tmpl-lbl">Brand Color</span>
            <div style="display:flex;align-items:center;gap:6px">
              <input type="color" v-model="brandColor" @change="saveBranding()" class="inv-color-pick"/>
              <span class="inv-color-val">{{ brandColor }}</span>
            </div>
          </label>
          <div class="inv-tmpl-group" style="flex:1">
            <span class="inv-tmpl-lbl">Logo URL</span>
            <input v-model="logoUrl" @change="saveBranding()" class="inv-logo-input" placeholder="https://yoursite.com/logo.png"/>
          </div>
        </div>

        <!-- Content row: form + optional preview -->
        <div class="inv-content-row">
        <div class="inv-dbody">

          <!-- Invoice Details -->
          <div class="inv-sec-lbl">Invoice Details</div>
          <div class="inv-fg inv-fg3">
            <div style="grid-column:1/3">
              <label class="inv-lbl">Customer <span class="inv-req">*</span></label>
              <SearchableSelect v-model="form.customer" :options="customers"
                placeholder="Select customer"
                :createable="true" createDoctype="Customer"
                @update:modelValue="onCustomerChange"/>
            </div>
            <div>
              <label class="inv-lbl">Invoice Date <span class="inv-req">*</span></label>
              <input v-model="form.posting_date" type="date" class="inv-fi"/>
            </div>
            <div>
              <label class="inv-lbl">Payment Terms</label>
              <select v-model="form.payment_terms" class="inv-fi" @change="applyPaymentTerms">
                <option value="">— Select Payment Terms —</option>
                <option v-for="t in PAYMENT_TERMS" :key="t" :value="t">{{ t }}</option>
              </select>
            </div>
            <div>
              <label class="inv-lbl">Due Date</label>
              <input v-model="form.due_date" type="date" class="inv-fi"/>
            </div>
            <div>
              <label class="inv-lbl">PO Number</label>
              <input v-model="form.po_no" class="inv-fi" placeholder="Customer's PO reference"/>
            </div>
            <div style="grid-column:1/-1">
              <div class="inv-inv-block" :class="form.update_stock ? 'inv-on' : 'inv-off'">
                <div class="inv-inv-toggle-row">
                  <div class="inv-inv-icon" v-html="icon('box',16)"></div>
                  <div class="inv-inv-text">
                    <div class="inv-inv-title">Deduct Inventory on Submit</div>
                    <div class="inv-inv-sub">Stock reduces from the selected warehouse when this invoice is submitted</div>
                  </div>
                  <label class="inv-inv-switch">
                    <input type="checkbox" v-model="form.update_stock" :true-value="1" :false-value="0" />
                    <span class="inv-inv-slider"></span>
                  </label>
                </div>
                <div v-if="form.update_stock" class="inv-inv-wh-row">
                  <label class="inv-lbl" style="margin-bottom:6px">Dispatch Warehouse <span style="color:#dc2626">*</span></label>
                  <SearchableSelect v-model="form.set_warehouse" :options="warehouses" placeholder="Select warehouse stock will be dispatched from…" @search="fetchWarehouses" />
                </div>
              </div>
            </div>
            <div>
              <label class="inv-lbl">Place of Supply</label>
              <div v-if="isOverseas" class="inv-fi" style="background:#dbeafe;color:#1d4ed8;font-size:12px;display:flex;align-items:center;gap:6px;padding:8px 10px;border-color:#bfdbfe">
                <span>🌐</span> Outside India — Not applicable for export invoices
              </div>
              <select v-else v-model="form.place_of_supply" class="inv-fi">
                <option value="">— Select State —</option>
                <option v-for="s in INDIAN_STATES" :key="s" :value="s">{{ s }}</option>
              </select>
            </div>
            <div>
              <label class="inv-lbl">Currency</label>
              <select v-model="form.currency" class="inv-fi" @change="onCurrencyChange">
                <option v-for="(sym,code) in CURRENCY_SYMBOLS" :key="code" :value="code">{{ code }} {{ sym }}</option>
              </select>
            </div>
            <div v-if="form.currency !== 'INR'">
              <label class="inv-lbl">Exchange Rate <span style="color:#6b7280;font-weight:400">(1 {{ form.currency }} = ? INR)</span></label>
              <input v-model.number="form.exchange_rate" type="number" min="0.0001" step="0.0001" class="inv-fi" placeholder="e.g. 83.5"/>
            </div>
          </div>

          <!-- Billing Address -->
          <div class="inv-sec-lbl">Billing Address</div>
          <div class="inv-fg" style="margin-bottom:14px">
            <div v-if="customerBillingAddrs.length > 1" style="margin-bottom:8px">
              <label class="inv-lbl">Select Billing Address</label>
              <select v-model="form.selected_billing_addr_name" class="inv-fi" @change="applySelectedBillingAddr">
                <option v-for="a in customerBillingAddrs" :key="a.name" :value="a.name">{{ a.address_title || a.address_line1 }}, {{ a.city }}</option>
              </select>
            </div>
            <div>
              <label class="inv-lbl">Address <span v-if="addressLoading" style="color:#9ca3af;font-weight:400">(loading…)</span></label>
              <textarea v-model="form.billing_address" class="inv-fi" rows="2" style="resize:vertical" placeholder="Auto-filled from customer, or enter manually"></textarea>
            </div>
          </div>

          <!-- Shipping Address -->
          <div class="inv-sec-lbl">Shipping Address</div>
          <div class="inv-fg" style="margin-bottom:14px">
            <div style="margin-bottom:10px">
              <label style="display:flex;align-items:center;gap:7px;font-size:12.5px;cursor:pointer">
                <input type="checkbox" v-model="sameAsBillingAddr" @change="onSameAsBillingChange" style="accent-color:#3B5BDB"/>
                Use same address as billing
              </label>
            </div>
            <template v-if="!sameAsBillingAddr">
              <div v-if="customerShippingAddrs.length" style="margin-bottom:8px">
                <label class="inv-lbl">Select Shipping Address</label>
                <select v-model="form.selected_shipping_addr_name" class="inv-fi" @change="applySelectedShippingAddr">
                  <option value="">— Select —</option>
                  <option v-for="a in customerShippingAddrs" :key="a.name" :value="a.name">{{ a.address_title || a.address_line1 }}, {{ a.city }}</option>
                </select>
              </div>
              <div>
                <label class="inv-lbl">Shipping Address</label>
                <textarea v-model="form.shipping_address" class="inv-fi" rows="2" style="resize:vertical" placeholder="Shipping address (optional)"></textarea>
              </div>
            </template>
            <div v-else style="font-size:12.5px;color:#9ca3af;font-style:italic">Using billing address for shipping</div>
          </div>

          <!-- Line Items -->
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;margin-top:4px">
            <span class="inv-sec-lbl" style="margin:0;border:none;padding:0">Line Items</span>
            <div style="display:flex;gap:8px">
              <button v-if="form.customer" class="inv-add-line-btn inv-copy-btn" @click="copyLastItems" title="Copy items from last invoice">
                <span v-html="icon('copy',12)"></span> Copy Last
              </button>
              <button class="inv-add-line-btn" @click="addLine">
                <span v-html="icon('plus',12)"></span> Add Item
              </button>
            </div>
          </div>

          <div style="border:1px solid #e8ecf0;border-radius:8px;overflow:hidden;margin-bottom:16px">
            <div style="overflow-x:auto">
              <table class="inv-lines-tbl">
                <thead>
                  <tr>
                    <th style="min-width:160px">Item <span class="inv-req">*</span></th>
                    <th style="min-width:100px">Description</th>
                    <th style="min-width:70px">HSN/SAC</th>
                    <th style="min-width:60px">Qty</th>
                    <th style="min-width:60px">UOM</th>
                    <th style="min-width:90px;text-align:right">Rate ({{ currencySymbol }})</th>
                    <th style="min-width:60px;text-align:right">Disc %</th>
                    <th style="min-width:90px;text-align:right">Amount ({{ currencySymbol }})</th>
                    <th style="width:28px"></th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="line in lines" :key="line.id">
                    <td>
                      <SearchableSelect v-model="line.item_code" :options="items"
                        placeholder="— Select —"
                        :compact="true" :createable="true" createDoctype="Item"
                        @update:modelValue="onItemChange(line)"/>
                    </td>
                    <td><input v-model="line.description" class="inv-ci" placeholder="Optional"/></td>
                    <td><input v-model="line.hsn_code" class="inv-ci" placeholder="HSN/SAC"/></td>
                    <td><input v-model.number="line.qty" type="number" min="0.001" step="0.001" class="inv-ci" @input="calcLine(line)"/></td>
                    <td><input v-model="line.uom" class="inv-ci" placeholder="Nos"/></td>
                    <td><input v-model.number="line.rate" type="number" min="0" step="0.01" class="inv-ci inv-ci-r" @input="calcLine(line)"/></td>
                    <td><input v-model.number="line.discount_percentage" type="number" min="0" max="100" step="0.1" class="inv-ci inv-ci-r" @input="calcLine(line)" placeholder="0"/></td>
                    <td style="text-align:right;padding:4px 10px;font-family:monospace;font-size:13px;font-weight:600;color:#1a1a2e">
                      {{ fmtAmt(line.amount) }}
                    </td>
                    <td style="padding:4px 6px">
                      <button @click="removeLine(line.id)" class="inv-rm-line"><span v-html="icon('x',12)"></span></button>
                    </td>
                  </tr>
                  <tr v-if="!lines.length">
                    <td colspan="9" style="text-align:center;padding:20px;color:#9ca3af;font-size:13px">
                      No line items — click "Add Item"
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>

            <!-- Totals + Taxes -->
            <div class="inv-totals-wrap">
              <!-- Tax section -->
              <div class="inv-tax-section">
                <!-- Overseas notice -->
                <div v-if="isOverseas" style="background:#dbeafe;border:1px solid #bfdbfe;border-radius:6px;padding:10px 14px;margin-bottom:10px;font-size:12.5px;color:#1e40af;display:flex;align-items:flex-start;gap:8px">
                  <span style="font-size:15px;flex-shrink:0">🌐</span>
                  <div>
                    <strong>Export Invoice — Zero Rated Supply</strong><br/>
                    GST is not applicable on exports. Ensure you have a valid LUT (Letter of Undertaking) or pay IGST and claim refund. No tax rows needed.
                  </div>
                </div>
                <!-- SEZ notice -->
                <div v-else-if="isSEZ" style="background:#f3f0ff;border:1px solid #c4b5fd;border-radius:6px;padding:10px 14px;margin-bottom:10px;font-size:12.5px;color:#4c1d95;display:flex;align-items:flex-start;gap:8px">
                  <span style="font-size:15px;flex-shrink:0">🏭</span>
                  <div>
                    <strong>SEZ Supply — Zero Rated</strong><br/>
                    Supplies to SEZ units/developers are zero-rated. Apply IGST @ 0% or supply under LUT/Bond without payment of tax.
                  </div>
                </div>
                <div class="inv-tax-header">
                  <span class="inv-tax-title">Taxes</span>
                  <div class="inv-tax-presets">
                    <template v-if="form.currency !== 'INR'">
                      <!-- Non-INR currency: GST not applicable, only allow custom tax -->
                      <span style="font-size:11.5px;color:#6b7280;font-style:italic">GST presets not applicable for foreign currency invoices</span>
                    </template>
                    <template v-else-if="!isOverseas">
                      <button v-for="p in TAX_PRESETS" :key="p.label" class="inv-preset-btn" @click="applyTaxPreset(p)">{{ p.label }}</button>
                    </template>
                    <template v-else>
                      <span style="font-size:11.5px;color:#6b7280;font-style:italic">Tax presets disabled for overseas customer</span>
                    </template>
                    <button class="inv-preset-btn inv-preset-custom" @click="addTaxRow">+ Custom</button>
                    <button v-if="taxRows.length" class="inv-preset-btn inv-preset-clear" @click="taxRows=[]">Clear</button>
                  </div>
                </div>
                <table v-if="taxRows.length" class="inv-tax-tbl">
                  <thead>
                    <tr>
                      <th>Description</th>
                      <th style="width:80px;text-align:right">Rate %</th>
                      <th style="width:100px;text-align:right">Amount</th>
                      <th style="width:28px"></th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="tx in taxRows" :key="tx.id">
                      <td><input v-model="tx.description" class="inv-ci" placeholder="e.g. CGST @ 9%"/></td>
                      <td><input v-model.number="tx.rate" type="number" min="0" max="100" step="0.1" class="inv-ci inv-ci-r" @input="recalcTax(tx)"/></td>
                      <td style="text-align:right;padding:4px 10px;font-family:monospace;font-size:12.5px">{{ fmtAmt(tx.amount) }}</td>
                      <td><button @click="taxRows=taxRows.filter(r=>r.id!==tx.id)" class="inv-rm-line"><span v-html="icon('x',12)"></span></button></td>
                    </tr>
                  </tbody>
                </table>
                <div v-else style="font-size:12px;color:#9ca3af;padding:6px 0">
                  <span v-if="isOverseas">Zero-rated export — no taxes applicable.</span>
                  <span v-else>No taxes — use preset buttons above or add custom row.</span>
                </div>
              </div>

              <!-- Totals -->
              <div class="inv-totals">
                <div class="inv-total-row">
                  <span>Subtotal</span>
                  <span class="inv-total-amt">{{ fmtAmt(subtotal) }}</span>
                </div>
                <div v-for="tx in taxRows" :key="tx.id" class="inv-total-row" style="color:#6b7280;font-size:12px">
                  <span>{{ tx.description || 'Tax' }}</span>
                  <span class="inv-total-amt">{{ fmtAmt(tx.amount) }}</span>
                </div>
                <div class="inv-total-row inv-grand-total">
                  <span>Grand Total</span>
                  <span class="inv-total-amt" style="font-size:16px;color:#1a6ef7">{{ fmtAmt(grandTotal) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- Notes & Terms -->
          <div class="inv-sec-lbl">Notes & Terms</div>
          <div class="inv-fg inv-fg2" style="margin-bottom:14px">
            <div>
              <label class="inv-lbl">Customer Note <span style="color:#9ca3af;font-weight:400">(printed on invoice)</span></label>
              <textarea v-model="form.terms" class="inv-fi" rows="3" style="resize:vertical" placeholder="Visible to customer on the invoice…"></textarea>
            </div>
            <div>
              <label class="inv-lbl">Internal Remarks <span style="color:#9ca3af;font-weight:400">(not printed)</span></label>
              <textarea v-model="form.remarks" class="inv-fi" rows="3" style="resize:vertical" placeholder="Internal notes for your team…"></textarea>
            </div>
          </div>

          <!-- Status -->
          <div class="inv-sec-lbl">Status</div>
          <div class="inv-fg inv-fg2">
            <div>
              <label class="inv-lbl">Save As</label>
              <select v-model="form.docstatus" class="inv-fi">
                <option :value="0">Draft</option>
                <option :value="1">Submit (Post to Ledger)</option>
              </select>
              <div style="font-size:11px;color:#9ca3af;margin-top:4px">Submitted invoices are posted to the ledger and can be paid against.</div>
            </div>
          </div>

        </div><!-- /inv-dbody -->

          <!-- Live preview pane -->
          <div v-if="showPreview" class="inv-preview-pane">
            <div class="inv-preview-toolbar">
              <span style="font-size:11px;font-weight:700;letter-spacing:.05em;color:#6b7280">LIVE PREVIEW</span>
              <div style="display:flex;gap:6px">
                <span style="font-size:11px;color:#9ca3af">{{ TEMPLATES.find(t=>t.key===selectedTemplate)?.label }}</span>
                <button class="inv-va-btn" style="font-size:11px;padding:4px 10px" @click="printInvoice(previewData)">
                  <span v-html="icon('download',12)"></span> Print PDF
                </button>
              </div>
            </div>
            <iframe :srcdoc="previewHtml" class="inv-preview-iframe" sandbox="allow-same-origin"></iframe>
          </div>

        </div><!-- /inv-content-row -->

        <div class="inv-dfooter">
          <div style="font-size:12px;color:#9ca3af">{{ editingName ? 'Editing: '+editingName : 'New invoice' }}</div>
          <div style="display:flex;gap:10px">
            <button class="inv-btn-ghost" @click="drawerOpen=false">Cancel</button>
            <button class="inv-btn-ghost" style="border-color:#3b82f6;color:#3b82f6" :disabled="drawerSaving" @click="saveInvoice(0)">Save Draft</button>
            <button class="inv-btn-primary" :disabled="drawerSaving" @click="saveInvoice(1)">
              <span v-html="icon('check',13)"></span> {{ drawerSaving ? 'Saving…' : 'Submit Invoice' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen&&viewInv" class="inv-drawer-bg" @click.self="viewOpen=false">
      <div class="inv-drawer-panel inv-drawer-wide">

        <!-- Header -->
        <div class="inv-dh" :style="'background:'+statusBg(viewInv)">
          <div>
            <div class="inv-dh-title" style="color:#fff">{{ viewInv.name }}</div>
            <div class="inv-dh-sub" style="color:rgba(255,255,255,.75)">
              <DocLink doctype="Customer" :name="viewInv.customer" :mono-style="false">{{ viewInv.customer_name||viewInv.customer }}</DocLink> · {{ fmtDate(viewInv.posting_date) }}
            </div>
          </div>
          <button class="inv-dclose" style="color:#fff;background:rgba(255,255,255,.15)" @click="viewOpen=false">
            <span v-html="icon('x',16)"></span>
          </button>
        </div>

        <!-- Status timeline -->
        <div class="inv-timeline">
          <template v-for="(step, i) in timelineSteps" :key="i">
            <div class="inv-tl-step" :class="{ done: step.done, danger: step.danger }">
              <div class="inv-tl-dot">
                <span v-if="step.done&&!step.danger" v-html="icon('check',9)"></span>
                <span v-else-if="step.danger" style="font-size:9px;font-weight:700">!</span>
              </div>
              <div class="inv-tl-label">{{ step.label }}</div>
            </div>
            <div v-if="i<timelineSteps.length-1" class="inv-tl-line" :class="{ done: timelineSteps[i+1]?.done, danger: timelineSteps[i+1]?.danger }"></div>
          </template>
        </div>

        <!-- Quick actions -->
        <div class="inv-view-actions">
          <button v-if="viewInv.docstatus===0" class="inv-va-btn" @click="viewOpen=false;openEdit(viewInv)">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button class="inv-va-btn" @click="printViewInvoice">
            <span v-html="icon('download',13)"></span> Print PDF
          </button>
          <button class="inv-va-btn" @click="duplicateInvoice(viewInv)">
            <span v-html="icon('copy',13)"></span> Duplicate
          </button>
          <button class="inv-va-btn" @click="openEmail(viewInv)">
            <span v-html="icon('mail',13)"></span> Send Email
          </button>
          <button v-if="viewInv.outstanding_amount>0&&viewInv.docstatus===1" class="inv-va-btn inv-va-pay" @click="viewOpen=false;openPayment(viewInv)">
            ₹ Record Payment
          </button>
          <button v-if="viewInv.docstatus===1" class="inv-va-btn" @click="openCreditNote(viewInv)">
            <span v-html="icon('creditnote',13)"></span> Credit Note
          </button>
          <button v-if="viewInv.docstatus===1" class="inv-va-btn" @click="makeRecurring(viewInv)">
            <span v-html="icon('repeat',13)"></span> Make Recurring
          </button>
          <button v-if="viewInv.docstatus===1" class="inv-va-btn inv-va-danger" @click="confirmAction('cancel', viewInv)">
            Cancel
          </button>
          <button v-if="viewInv.docstatus===0" class="inv-va-btn inv-va-danger" @click="confirmAction('delete', viewInv)">
            <span v-html="icon('delete',13)"></span> Delete
          </button>
        </div>

        <!-- Tabs -->
        <div class="inv-view-tabs">
          <button class="inv-vtab" :class="{ active: viewTab==='details' }" @click="viewTab='details'">Details</button>
          <button class="inv-vtab" :class="{ active: viewTab==='payments' }" @click="viewTab='payments';loadPayments(viewInv.name)">
            Payments <span v-if="viewPayments.length" class="inv-vtab-count">{{ viewPayments.length }}</span>
          </button>
        </div>

        <div class="inv-dbody">

          <!-- Details tab -->
          <template v-if="viewTab==='details'">
            <div class="inv-view-meta">
              <div><div class="inv-meta-lbl">Status</div><span class="inv-status-badge" :class="statusCls(viewInv)">{{ statusLabel(viewInv) }}</span></div>
              <div><div class="inv-meta-lbl">Customer</div><div><DocLink doctype="Customer" :name="viewInv.customer" :mono-style="false">{{ viewInv.customer_name||viewInv.customer }}</DocLink></div></div>
              <div v-if="viewInv.po_no"><div class="inv-meta-lbl">PO Number</div><div class="mono-sm">{{ viewInv.po_no }}</div></div>
              <div><div class="inv-meta-lbl">Invoice Date</div><div>{{ fmtDate(viewInv.posting_date) }}</div></div>
              <div><div class="inv-meta-lbl">Due Date</div><div :class="isOverdue(viewInv)?'text-danger':''">{{ fmtDate(viewInv.due_date)||'—' }}</div></div>
              <div><div class="inv-meta-lbl">Place of Supply</div><div>{{ viewInv.place_of_supply||'—' }}</div></div>
              <div><div class="inv-meta-lbl">Grand Total</div><div style="font-weight:700;font-family:monospace;font-size:15px">{{ fmtAmt(viewInv.grand_total, viewInv.currency) }}</div></div>
              <div><div class="inv-meta-lbl">Balance Due</div><div :class="viewInv.outstanding_amount>0?'text-danger':'text-success'" style="font-weight:700;font-family:monospace">{{ fmtAmt(viewInv.outstanding_amount, viewInv.currency) }}</div></div>
            </div>

            <div v-if="viewLoading" style="padding:24px;text-align:center;color:#9ca3af">Loading details…</div>

            <template v-else>
              <!-- Line items -->
              <div v-if="viewInv.items&&viewInv.items.length" style="border:1px solid #e8ecf0;border-radius:8px;overflow:hidden;margin-bottom:16px">
                <div class="inv-view-items-header">
                  <div>Item</div><div>HSN</div><div style="text-align:right">Qty</div><div style="text-align:right">Rate</div><div style="text-align:right">Disc</div><div style="text-align:right">Amount</div>
                </div>
                <div v-for="(it,i) in viewInv.items" :key="i" class="inv-view-item-row">
                  <div><div style="font-weight:500">{{ it.item_name||it.item_code }}</div><div v-if="it.description" style="font-size:11.5px;color:#9ca3af">{{ it.description }}</div></div>
                  <div class="mono-sm text-muted">{{ it.hsn_code||'—' }}</div>
                  <div style="text-align:right;font-family:monospace">{{ flt(it.qty) }}</div>
                  <div style="text-align:right;font-family:monospace">{{ fmtAmt(it.rate, viewInv.currency) }}</div>
                  <div style="text-align:right;font-family:monospace">{{ it.discount_percentage ? it.discount_percentage+'%' : '—' }}</div>
                  <div style="text-align:right;font-family:monospace;font-weight:600">{{ fmtAmt(it.amount, viewInv.currency) }}</div>
                </div>
              </div>
              <div v-else style="color:#9ca3af;font-size:13px;margin-bottom:16px">No item details available.</div>

              <!-- Tax summary -->
              <div v-if="viewInv.taxes&&viewInv.taxes.length" style="margin-bottom:16px">
                <div style="font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#9ca3af;margin-bottom:8px">Taxes</div>
                <div v-for="(tx,i) in viewInv.taxes" :key="i" style="display:flex;justify-content:space-between;font-size:13px;padding:3px 0;color:#374151">
                  <span>{{ tx.description||tx.account_head }}</span>
                  <span class="mono-sm">{{ fmtAmt(tx.tax_amount||tx.amount, viewInv.currency) }}</span>
                </div>
              </div>

              <!-- Totals -->
              <div style="background:#f8fafc;border-radius:8px;padding:12px 16px;margin-bottom:16px">
                <div style="display:flex;justify-content:space-between;font-size:13px;color:#6b7280;margin-bottom:4px">
                  <span>Subtotal</span><span class="mono-sm">{{ fmtAmt((viewInv.grand_total||0)-(viewInv.total_taxes_and_charges||0), viewInv.currency) }}</span>
                </div>
                <div v-if="viewInv.total_taxes_and_charges" style="display:flex;justify-content:space-between;font-size:13px;color:#6b7280;margin-bottom:6px">
                  <span>Total Tax</span><span class="mono-sm">{{ fmtAmt(viewInv.total_taxes_and_charges, viewInv.currency) }}</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:15px;font-weight:700;border-top:1px solid #e8ecf0;padding-top:8px">
                  <span>Grand Total</span><span style="font-family:monospace;color:#1a6ef7">{{ fmtAmt(viewInv.grand_total, viewInv.currency) }}</span>
                </div>
              </div>

              <!-- Notes -->
              <div v-if="viewInv.terms" style="background:#f0f9ff;border-radius:8px;padding:12px 14px;font-size:13px;color:#374151;margin-bottom:12px">
                <div class="inv-meta-lbl" style="margin-bottom:4px">Customer Note</div>
                {{ viewInv.terms }}
              </div>
              <div v-if="viewInv.remarks" style="background:#f8fafc;border-radius:8px;padding:12px 14px;font-size:13px;color:#374151">
                <div class="inv-meta-lbl" style="margin-bottom:4px">Internal Remarks</div>
                {{ viewInv.remarks }}
              </div>
            </template>
          </template>

          <!-- Payments tab -->
          <template v-else-if="viewTab==='payments'">
            <div v-if="viewPaymentsLoading" style="padding:24px;text-align:center;color:#9ca3af">Loading payments…</div>
            <template v-else>
              <div v-if="viewPayments.length" style="border:1px solid #e8ecf0;border-radius:8px;overflow:hidden">
                <div style="display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr 1fr;gap:8px;padding:8px 14px;background:#f8fafc;border-bottom:1px solid #e8ecf0;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#9ca3af">
                  <div>Payment #</div><div>Date</div><div>Mode</div><div>Reference</div><div style="text-align:right">Amount</div>
                </div>
                <div v-for="(p,i) in viewPayments" :key="i" style="display:grid;grid-template-columns:1.2fr 1fr 1fr 1fr 1fr;gap:8px;padding:9px 14px;border-bottom:1px solid #f0f2f5;font-size:13px">
                  <div><DocLink doctype="Payment Entry" :name="p.payment_entry || p.name" /></div>
                  <div class="mono-sm">{{ fmtDate(p.payment_date) }}</div>
                  <div>{{ p.mode_of_payment||'—' }}</div>
                  <div class="text-muted mono-sm">{{ p.reference_no||'—' }}</div>
                  <div style="text-align:right;font-family:monospace;font-weight:600;color:#059669">{{ fmtAmt(p.paid_amount) }}</div>
                </div>
              </div>
              <div v-else style="text-align:center;padding:40px;color:#9ca3af;font-size:13px">
                No payments recorded against this invoice.
                <div v-if="viewInv.outstanding_amount>0&&viewInv.docstatus===1" style="margin-top:12px">
                  <button class="inv-btn-primary" @click="viewOpen=false;openPayment(viewInv)">₹ Record Payment</button>
                </div>
              </div>
            </template>
          </template>

        </div>

        <div class="inv-dfooter" style="justify-content:flex-end">
          <button class="inv-btn-ghost" @click="viewOpen=false">Close</button>
        </div>
      </div>
    </div>

    <!-- Phase 0.9 purge: Payment / Email / Credit Note inline modals removed. Handled by globally mounted PaymentDialog / EmailDialog / ReturnNoteDialog. -->

    <!-- ── Confirm Modal (cancel / delete) ── -->
    <div v-if="confirmModal.open" class="rp-backdrop" @click.self="confirmModal.open=false">
      <div class="rp-dialog" style="max-width:440px">
        <div class="rp-dialog-header">
          <span class="rp-dialog-title">{{ confirmModal.title }}</span>
          <button class="rp-close-btn" @click="confirmModal.open=false">✕</button>
        </div>
        <div class="rp-body">
          <p style="font-size:13px;color:#374151;margin:0 0 12px">{{ confirmModal.message }}</p>
          <div v-if="confirmModal.payments.length" style="border:1px solid #fca5a5;border-radius:8px;overflow:hidden;margin-bottom:8px">
            <div style="background:#fee2e2;padding:8px 12px;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#b91c1c;display:grid;grid-template-columns:1fr 1fr 1fr 1fr">
              <span>Payment</span><span>Mode</span><span>Date</span><span style="text-align:right">Amount</span>
            </div>
            <div v-for="p in confirmModal.payments" :key="p.name" style="padding:8px 12px;font-size:12.5px;display:grid;grid-template-columns:1fr 1fr 1fr 1fr;border-top:1px solid #fee2e2">
              <span class="mono-sm" style="color:#374151">{{ p.name }}</span>
              <span style="color:#6b7280">{{ p.mode_of_payment||'—' }}</span>
              <span class="mono-sm" style="color:#6b7280">{{ fmtDate(p.payment_date) }}</span>
              <span style="text-align:right;font-family:monospace;font-weight:600;color:#059669">{{ fmtAmt(p.paid_amount) }}</span>
            </div>
          </div>
          <p v-if="confirmModal.payments.length" style="font-size:12px;color:#b91c1c;margin:8px 0 0">The payment(s) above will also be cancelled. This cannot be undone.</p>
        </div>
        <div class="rp-footer">
          <button class="rp-btn rp-btn-outline" @click="confirmModal.open=false">Keep Invoice</button>
          <button class="rp-btn" style="background:#dc2626;border-color:#dc2626;color:#fff" :disabled="confirmModal.loading" @click="confirmModal.action()">
            {{ confirmModal.loading ? 'Processing…' : confirmModal.actionLabel }}
          </button>
        </div>
      </div>
    </div>

  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted, nextTick } from "vue";
import { useRoute } from "vue-router";
import { apiList, apiGet, apiGET, apiPOST, apiSave, apiSubmit, apiDelete, apiCancel, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { usePaymentDialog } from "../composables/usePaymentDialog.js";
import { useMakeRecurring } from "../composables/useMakeRecurring.js";
import { useOpenFromQuery } from "../composables/useOpenFromQuery.js";
import { usePagination } from "../composables/usePagination.js";
import DocLink from "../components/DocLink.vue";
import Pagination from "../components/Pagination.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import { useReturnNote } from "../composables/useReturnNote.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const route = useRoute();

// ── Constants ─────────────────────────────────────────────────────────
const PAY_MODES = ["Cash","Cheque","Bank Transfer","UPI","NEFT","RTGS","IMPS","Credit Card","Debit Card","DD"];
const FILTERS   = [
  { key:"all",     label:"All" },
  { key:"Draft",   label:"Draft" },
  { key:"Unpaid",  label:"Unpaid" },
  { key:"Overdue", label:"Overdue" },
  { key:"Paid",    label:"Paid" },
];
const DATE_RANGES = [
  { key:"this_month", label:"This Month" },
  { key:"last_month", label:"Last Month" },
  { key:"all",        label:"All Time" },
  { key:"custom",     label:"Custom" },
];
const PAYMENT_TERMS = ["Due on Receipt","Net 7","Net 15","Net 30","Net 45","Net 60","Net 90"];
const TAX_PRESETS = [
  { label:"GST 5%",   rows:[{desc:"CGST @ 2.5%",rate:2.5},{desc:"SGST @ 2.5%",rate:2.5}] },
  { label:"GST 12%",  rows:[{desc:"CGST @ 6%",  rate:6},  {desc:"SGST @ 6%",  rate:6}]   },
  { label:"GST 18%",  rows:[{desc:"CGST @ 9%",  rate:9},  {desc:"SGST @ 9%",  rate:9}]   },
  { label:"GST 28%",  rows:[{desc:"CGST @ 14%", rate:14}, {desc:"SGST @ 14%", rate:14}]  },
  { label:"IGST 5%",  rows:[{desc:"IGST @ 5%",  rate:5}]  },
  { label:"IGST 12%", rows:[{desc:"IGST @ 12%", rate:12}] },
  { label:"IGST 18%", rows:[{desc:"IGST @ 18%", rate:18}] },
  { label:"IGST 28%", rows:[{desc:"IGST @ 28%", rate:28}] },
];
const IGST_PRESETS = [
  { label:"IGST 5%",  rows:[{desc:"IGST @ 5%",  rate:5}]  },
  { label:"IGST 12%", rows:[{desc:"IGST @ 12%", rate:12}] },
  { label:"IGST 18%", rows:[{desc:"IGST @ 18%", rate:18}] },
  { label:"IGST 28%", rows:[{desc:"IGST @ 28%", rate:28}] },
];
const INDIAN_STATES = [
  "01-Jammu and Kashmir","02-Himachal Pradesh","03-Punjab","04-Chandigarh","05-Uttarakhand",
  "06-Haryana","07-Delhi","08-Rajasthan","09-Uttar Pradesh","10-Bihar","11-Sikkim",
  "12-Arunachal Pradesh","13-Nagaland","14-Manipur","15-Mizoram","16-Tripura","17-Meghalaya",
  "18-Assam","19-West Bengal","20-Jharkhand","21-Odisha","22-Chhattisgarh","23-Madhya Pradesh",
  "24-Gujarat","26-Dadra and Nagar Haveli","27-Maharashtra","29-Karnataka","30-Goa",
  "31-Lakshadweep","32-Kerala","33-Tamil Nadu","34-Puducherry","35-Andaman and Nicobar Islands",
  "36-Telangana","37-Andhra Pradesh","38-Ladakh","97-Other Territory",
];
const CURRENCY_SYMBOLS = { INR:"₹", USD:"$", EUR:"€", GBP:"£", AED:"د.إ", SGD:"S$", JPY:"¥", AUD:"A$", CAD:"C$", CHF:"₣" };
const TEMPLATES = [
  { key:"classic", label:"Classic" },
  { key:"modern",  label:"Modern"  },
  { key:"minimal", label:"Minimal" },
];

// ── State ─────────────────────────────────────────────────────────────
const list         = ref([]);
const loading      = ref(false);
const customers    = ref([]);
const items        = ref([]);
const activeFilter = ref("all");
const search       = ref("");
const selectedRows = ref(new Set());
const sortKey      = ref("posting_date");
const sortDir      = ref(-1);
const dateRange    = ref("this_month");
const customFrom   = ref("");
const customTo     = ref("");
const filterCustomer = ref("");
const taxAccountHead    = ref("");
const selectedTemplate  = ref("classic");
const brandColor        = ref("#1a6ef7");
const logoUrl           = ref("");
const showPreview       = ref(false);

// ── Drawer (create/edit) ───────────────────────────────────────────────
const drawerOpen   = ref(false);
const editingName  = ref(null);
const drawerSaving = ref(false);
const addressLoading = ref(false);
const form = reactive({
  customer:"", posting_date:"", due_date:"", po_no:"",
  payment_terms:"", place_of_supply:"", billing_address:"",
  shipping_address:"", selected_billing_addr_name:"", selected_shipping_addr_name:"",
  terms:"", remarks:"", docstatus:0,
  currency:"INR", exchange_rate:1, gst_treatment:"",
  update_stock:1, set_warehouse:"",
});
const customerBillingAddrs  = ref([]);
const customerShippingAddrs = ref([]);
const sameAsBillingAddr     = ref(false);
const lines   = ref([]);
const warehouses = ref([]);
async function fetchWarehouses(q=""){try{const co=await resolveCompany();const r=await apiList("Warehouse",{fields:["name","parent_warehouse"],filters:[["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:30});warehouses.value=r.map(x=>({label:x.parent_warehouse?`${x.parent_warehouse} / ${x.name}`:x.name,value:x.name}));}catch{warehouses.value=[];}}
const taxRows = ref([]);

// ── View drawer ────────────────────────────────────────────────────────
const viewOpen    = ref(false);
const viewInv     = ref(null);
const viewTab     = ref("details");
const viewLoading = ref(false);
const viewPayments = ref([]);
const viewPaymentsLoading = ref(false);

// Phase 0.9 purge — payModal / emailModal / cnModal removed.
// Their UX is now delegated to globally mounted PaymentDialog / EmailDialog /
// ReturnNoteDialog via useEmailDialog / usePaymentDialog / useReturnNote.

// ── Confirm modal ──────────────────────────────────────────────────────
const confirmModal = reactive({ open:false, loading:false, title:"", message:"", actionLabel:"Confirm", action: null, payments:[] });

// ── Helpers ────────────────────────────────────────────────────────────
const currencySymbol = computed(() => CURRENCY_SYMBOLS[form.currency] || "₹");
function fmtAmt(v, currency) {
  const cur = currency || form.currency || "INR";
  const sym = CURRENCY_SYMBOLS[cur] || "₹";
  const locale = cur === "INR" ? "en-IN" : "en-US";
  return sym + Number(v||0).toLocaleString(locale,{minimumFractionDigits:2,maximumFractionDigits:2});
}
const isOverseas = computed(() => form.gst_treatment === "Overseas");
const isSEZ = computed(() => form.gst_treatment === "SEZ");
function todayStr() { return new Date().toISOString().slice(0,10); }
function dueDateDefault() { const d=new Date(); d.setDate(d.getDate()+30); return d.toISOString().slice(0,10); }

function isOverdue(inv) { return inv.outstanding_amount>0&&inv.due_date&&new Date(inv.due_date)<new Date(); }
function statusLabel(inv) {
  if (inv.docstatus===2) return "CANCELLED";
  if (isOverdue(inv)) { const days=Math.floor((Date.now()-new Date(inv.due_date))/86400000); return `OVERDUE ${days}d`; }
  return (inv.status||(inv.docstatus===0?"Draft":"Unpaid")).toUpperCase();
}
function statusCls(inv) {
  if (inv.docstatus===2) return "status-cancelled";
  if (isOverdue(inv)) return "status-overdue";
  const s=(inv.status||"").toLowerCase();
  if (s==="paid") return "status-paid";
  if (s==="submitted"||s==="unpaid"||s==="partly paid") return "status-unpaid";
  if (s==="cancelled") return "status-cancelled";
  return "status-draft";
}
function statusBg(inv) {
  if (inv.docstatus===2) return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  if (isOverdue(inv)) return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  const s=(inv.status||"").toLowerCase();
  if (s==="paid") return "linear-gradient(135deg,#064e3b,#059669)";
  if (s==="submitted"||s==="unpaid"||s==="partly paid") return "linear-gradient(135deg,#78350f,#d97706)";
  return "linear-gradient(135deg,#1e3a5f,#2563eb)";
}
function pillCls(k) { return {Draft:"pc-muted",Unpaid:"pc-amber",Overdue:"pc-red",Paid:"pc-green"}[k]||"pc-muted"; }

// ── Computed ───────────────────────────────────────────────────────────
const counts = computed(()=>({
  Draft:   list.value.filter(i=>i.docstatus===0).length,
  Unpaid:  list.value.filter(i=>!isOverdue(i)&&i.outstanding_amount>0&&i.docstatus===1).length,
  Overdue: list.value.filter(isOverdue).length,
  Paid:    list.value.filter(i=>i.outstanding_amount<=0&&i.docstatus===1).length,
}));
const summary = computed(()=>({
  unpaidCount:  list.value.filter(i=>i.outstanding_amount>0&&!isOverdue(i)).length,
  overdueCount: list.value.filter(isOverdue).length,
  totalDue:     list.value.reduce((s,i)=>s+flt(i.outstanding_amount),0),
}));
const _thisYM = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _lastYM = () => { const d=new Date(); d.setMonth(d.getMonth()-1); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _trend = (a, b) => { if(!b&&!a) return {pct:0,up:true}; if(!b) return {pct:100,up:true}; const p=Math.round((a-b)/b*100); return {pct:Math.abs(p),up:p>=0}; };
const invThisMonth = computed(() => { const ym=_thisYM(); const r=list.value.filter(i=>(i.posting_date||'').startsWith(ym)); return {count:r.length,revenue:r.reduce((s,i)=>s+flt(i.grand_total),0)}; });
const _invLastCount = computed(() => { const ym=_lastYM(); return list.value.filter(i=>(i.posting_date||'').startsWith(ym)).length; });
const invAvg = computed(() => { const p=list.value.filter(i=>i.grand_total>0); return p.length?p.reduce((s,i)=>s+flt(i.grand_total),0)/p.length:0; });
const invTrends = computed(() => ({
  total:  _trend(invThisMonth.value.count, _invLastCount.value),
  draft:  _trend(counts.value.Draft, list.value.filter(i=>(i.posting_date||'').startsWith(_lastYM())&&i.docstatus===0).length),
  unpaid: _trend(counts.value.Unpaid, list.value.filter(i=>(i.posting_date||'').startsWith(_lastYM())&&i.outstanding_amount>0&&i.docstatus===1).length),
  overdue:_trend(counts.value.Overdue, list.value.filter(i=>(i.posting_date||'').startsWith(_lastYM())&&isOverdue(i)).length),
  paid:   _trend(counts.value.Paid, list.value.filter(i=>(i.posting_date||'').startsWith(_lastYM())&&i.outstanding_amount<=0&&i.docstatus===1).length),
}));
const allSelected = computed(()=>sorted.value.length>0&&sorted.value.every(i=>selectedRows.value.has(i.name)));

const filtered = computed(()=>{
  let r=list.value;
  // Date range
  const now=new Date();
  if (dateRange.value!=="all") {
    let from,to;
    if (dateRange.value==="this_month") { from=new Date(now.getFullYear(),now.getMonth(),1); to=new Date(now.getFullYear(),now.getMonth()+1,0); }
    else if (dateRange.value==="last_month") { from=new Date(now.getFullYear(),now.getMonth()-1,1); to=new Date(now.getFullYear(),now.getMonth(),0); }
    else if (dateRange.value==="custom"&&customFrom.value&&customTo.value) { from=new Date(customFrom.value); to=new Date(customTo.value); }
    if (from&&to) r=r.filter(i=>{ const d=new Date(i.posting_date); return d>=from&&d<=to; });
  }
  // Customer filter
  if (filterCustomer.value) r=r.filter(i=>i.customer===filterCustomer.value);
  // Status filter
  if (activeFilter.value==="Draft")   r=r.filter(i=>i.docstatus===0);
  else if (activeFilter.value==="Overdue") r=r.filter(isOverdue);
  else if (activeFilter.value==="Unpaid")  r=r.filter(i=>!isOverdue(i)&&i.outstanding_amount>0&&i.docstatus===1);
  else if (activeFilter.value==="Paid")    r=r.filter(i=>i.outstanding_amount<=0&&i.docstatus===1);
  // Search
  const q=search.value.toLowerCase();
  if (q) r=r.filter(i=>(i.name+(i.customer_name||"")+(i.customer||"")+(i.po_no||"")).toLowerCase().includes(q));
  return r;
});

const sorted = computed(()=>[...filtered.value].sort((a,b)=>{
  const va=a[sortKey.value]??"",vb=b[sortKey.value]??"";
  if (va<vb) return -1*sortDir.value; if (va>vb) return 1*sortDir.value; return 0;
}));

const { page, pageSize, paged } = usePagination(sorted, { storageKey: "invoices" });

const subtotal  = computed(()=>lines.value.reduce((s,l)=>s+flt(l.amount),0));
const totalTax  = computed(()=>taxRows.value.reduce((s,r)=>s+flt(r.amount),0));
const grandTotal = computed(()=>subtotal.value+totalTax.value);

const previewData = computed(()=>({
  name: editingName.value||"INV-PREVIEW",
  customer: form.customer,
  customer_name: customers.value.find(c=>c.name===form.customer)?.customer_name||form.customer,
  posting_date: form.posting_date,
  due_date: form.due_date,
  po_no: form.po_no,
  place_of_supply: form.place_of_supply,
  billing_address: form.billing_address,
  items: lines.value.filter(l=>l.item_code||l.item_name),
  taxes: taxRows.value,
  subtotal: subtotal.value,
  totalTax: totalTax.value,
  grandTotal: grandTotal.value,
  terms: form.terms,
  company: window.__booksCompany||"",
}));

const previewHtml = computed(()=>renderInvoice(previewData.value, selectedTemplate.value, brandColor.value, logoUrl.value));

const timelineSteps = computed(()=>{
  if (!viewInv.value) return [];
  const inv=viewInv.value;
  const isPaid=inv.outstanding_amount<=0&&inv.docstatus===1;
  const isSubmitted=inv.docstatus>=1;
  const isCancelled=inv.docstatus===2;
  if (isCancelled) return [{label:"Draft",done:true},{label:"Submitted",done:true},{label:"Cancelled",done:true,danger:true}];
  return [
    {label:"Draft",done:true},
    {label:"Submitted",done:isSubmitted},
    {label:isOverdue(inv)?"Overdue":"Paid",done:isPaid,danger:isOverdue(inv)&&!isPaid},
  ];
});

// ── Load ───────────────────────────────────────────────────────────────
async function load() {
  loading.value=true;
  try {
    // Exclude credit notes (is_return=1) — those live on /credit-notes.
    list.value=await apiList("Sales Invoice",{
      fields:["name","customer","customer_name","posting_date","due_date",
              "grand_total","outstanding_amount","status","docstatus","po_no"],
      filters:[["is_return","=",0]],
      limit:500, order:"posting_date desc",
    })||[];
  } catch { list.value=[]; toast("Could not load invoices","error"); }
  loading.value=false;
}
async function loadCustomers() {
  try { const r=await apiList("Customer",{fields:["name","customer_name"],filters:[["disabled","=",0]],limit:500,order:"customer_name asc"})||[]; customers.value=r.map(x=>({...x,value:x.name,label:x.customer_name||x.name})); } catch {}
}
async function loadItems() {
  try { const r=await apiList("Item",{fields:["name","item_name","standard_rate","stock_uom","description","hsn_code"],filters:[["disabled","=",0]],limit:500,order:"item_name asc"})||[]; items.value=r.map(x=>({...x,value:x.name,label:x.item_name||x.name})); } catch {}
}
async function loadTaxAccount() {
  try {
    const co=await resolveCompany();
    const r=await apiList("Account",{fields:["name"],filters:[["company","=",co],["account_type","=","Tax"],["is_group","=",0]],limit:1});
    taxAccountHead.value=r[0]?.name||"";
  } catch {}
}

// ── Sorting & selection ────────────────────────────────────────────────
function sort(key) { sortKey.value===key?(sortDir.value*=-1):(sortKey.value=key,sortDir.value=-1); }
function sortArrow(k) { return sortKey.value!==k?"":sortDir.value===1?"↑":"↓"; }
function toggleAll(e) { if(e.target.checked) sorted.value.forEach(i=>selectedRows.value.add(i.name)); else selectedRows.value.clear(); selectedRows.value=new Set(selectedRows.value); }
function toggleRow(name) { const s=new Set(selectedRows.value); s.has(name)?s.delete(name):s.add(name); selectedRows.value=s; }

// ── Line item helpers ──────────────────────────────────────────────────
function addLine() { lines.value.push({id:Date.now(),item_code:"",item_name:"",description:"",hsn_code:"",qty:1,rate:0,uom:"Nos",discount_percentage:0,discount_amount:0,amount:0}); }
function removeLine(id) { lines.value=lines.value.filter(l=>l.id!==id); }
function calcLine(line) {
  const base=Math.round(flt(line.qty)*flt(line.rate)*100)/100;
  const disc=Math.round(base*flt(line.discount_percentage)/100*100)/100;
  line.discount_amount=disc;
  line.amount=base-disc;
}
async function onItemChange(line) {
  const it=items.value.find(i=>i.name===line.item_code);
  if (it) {
    line.item_name=it.item_name||it.name;
    line.rate=flt(it.standard_rate);
    line.uom=it.stock_uom||"Nos";
    if (it.description) line.description=it.description;
    if (it.hsn_code) line.hsn_code=it.hsn_code;
    calcLine(line);
  }
  if (line.item_code) {
    try {
      const doc=await apiGet("Item",line.item_code);
      if (doc?.item_name) line.item_name=doc.item_name;
      if (doc?.description) line.description=doc.description;
      if (doc?.hsn_code) line.hsn_code=doc.hsn_code;
      if (!flt(line.rate)&&doc?.standard_rate) line.rate=flt(doc.standard_rate);
      if (doc?.stock_uom) line.uom=doc.stock_uom;
      calcLine(line);
    } catch {}
  }
}

// ── Tax helpers ────────────────────────────────────────────────────────
function recalcTax(tx) { tx.amount=Math.round(subtotal.value*flt(tx.rate)/100*100)/100; }
function addTaxRow() { taxRows.value.push({id:Date.now(),description:"",rate:0,account_head:taxAccountHead.value,amount:0}); }
function applyTaxPreset(p) {
  taxRows.value=p.rows.map((r,i)=>({id:Date.now()+i,description:r.desc,rate:r.rate,account_head:taxAccountHead.value,amount:Math.round(subtotal.value*r.rate/100*100)/100}));
}
watch(subtotal,()=>{ taxRows.value.forEach(r=>{ r.amount=Math.round(subtotal.value*flt(r.rate)/100*100)/100; }); });

// ── Payment Terms ──────────────────────────────────────────────────────
function applyPaymentTerms() {
  if (!form.posting_date||!form.payment_terms) return;
  const days={"Due on Receipt":0,"Net 7":7,"Net 15":15,"Net 30":30,"Net 45":45,"Net 60":60,"Net 90":90}[form.payment_terms]??30;
  const d=new Date(form.posting_date); d.setDate(d.getDate()+days);
  form.due_date=d.toISOString().slice(0,10);
}

// ── Currency change & exchange rate fetch ──────────────────────────────
async function onCurrencyChange() {
  if (form.currency === "INR") {
    form.exchange_rate = 1;
    return;
  }
  form.exchange_rate = await fetchExchangeRate(form.currency) || form.exchange_rate || 1;
}
async function fetchExchangeRate(currency) {
  if (!currency || currency === "INR") return 1;
  try {
    const r = await apiGET("frappe.client.get_value", {
      doctype: "Currency Exchange",
      filters: JSON.stringify([["from_currency","=",currency],["to_currency","=","INR"]]),
      fieldname: "exchange_rate",
    });
    if (r?.message?.exchange_rate) return flt(r.message.exchange_rate);
  } catch {}
  return null; // let caller decide fallback
}

// ── Customer change: auto-fill address, currency, GST treatment ───────
async function onCustomerChange() {
  form.billing_address=""; form.shipping_address="";
  form.selected_billing_addr_name=""; form.selected_shipping_addr_name="";
  sameAsBillingAddr.value=false;
  customerBillingAddrs.value=[]; customerShippingAddrs.value=[];
  if (!form.customer) return;
  addressLoading.value=true;
  try {
    const [custDoc, billingAddrs, shippingAddrs] = await Promise.all([
      apiGet("Customer", form.customer),
      apiList("Address",{
        fields:["name","address_title","address_line1","address_line2","city","state","pincode"],
        filters:[["Dynamic Link","link_name","=",form.customer],["Dynamic Link","link_doctype","=","Customer"],["address_type","=","Billing"]],
        order:"`tabAddress`.modified desc", limit:20,
      }),
      apiList("Address",{
        fields:["name","address_title","address_line1","address_line2","city","state","pincode"],
        filters:[["Dynamic Link","link_name","=",form.customer],["Dynamic Link","link_doctype","=","Customer"],["address_type","=","Shipping"]],
        order:"`tabAddress`.modified desc", limit:20,
      }),
    ]);

    customerBillingAddrs.value  = billingAddrs  || [];
    customerShippingAddrs.value = shippingAddrs || [];

    // Apply currency from customer, and fetch exchange rate if foreign
    if (custDoc?.default_currency) {
      form.currency = custDoc.default_currency;
      if (form.currency !== "INR") {
        form.exchange_rate = await fetchExchangeRate(form.currency) || 1;
      } else {
        form.exchange_rate = 1;
      }
    }

    // Apply payment terms from customer (only if user hasn't changed it yet)
    if (custDoc?.payment_terms && !form.payment_terms) {
      form.payment_terms = custDoc.payment_terms;
      applyPaymentTerms();
    }

    // Apply GST treatment
    form.gst_treatment = custDoc?.gst_treatment || "";

    // Overseas: zero-rated export — clear any existing taxes
    if (form.gst_treatment === "Overseas") {
      taxRows.value = [];
      form.place_of_supply = "";
    }
    // SEZ: zero-rated supply — clear taxes, keep place of supply
    if (form.gst_treatment === "SEZ") {
      taxRows.value = [];
    }

    // Auto-fill billing address from first linked record, fallback to Customer fields
    const addrSrc = billingAddrs?.[0] || null;
    const addrFields = addrSrc
      ? [addrSrc.address_line1, addrSrc.address_line2, addrSrc.city, addrSrc.state, addrSrc.pincode]
      : [custDoc?.address_line1, custDoc?.address_line2, custDoc?.city, custDoc?.state, custDoc?.pincode];
    const builtAddr = addrFields.filter(Boolean).join(", ");
    if (builtAddr) {
      form.billing_address = builtAddr;
      if (addrSrc) form.selected_billing_addr_name = addrSrc.name;
    }
    // Auto-fill shipping from first shipping address if present
    if (shippingAddrs?.[0]) {
      const s = shippingAddrs[0];
      form.shipping_address = [s.address_line1,s.address_line2,s.city,s.state,s.pincode].filter(Boolean).join(", ");
      form.selected_shipping_addr_name = s.name;
    }
  } catch {}
  addressLoading.value=false;
}

function applySelectedBillingAddr() {
  const addr = customerBillingAddrs.value.find(a=>a.name===form.selected_billing_addr_name);
  if (addr) form.billing_address=[addr.address_line1,addr.address_line2,addr.city,addr.state,addr.pincode].filter(Boolean).join(", ");
}
function applySelectedShippingAddr() {
  const addr = customerShippingAddrs.value.find(a=>a.name===form.selected_shipping_addr_name);
  if (addr) form.shipping_address=[addr.address_line1,addr.address_line2,addr.city,addr.state,addr.pincode].filter(Boolean).join(", ");
}
function onSameAsBillingChange() {
  if (sameAsBillingAddr.value) form.shipping_address = form.billing_address;
  else form.shipping_address = "";
}

// ── Copy last items ────────────────────────────────────────────────────
async function copyLastItems() {
  if (!form.customer) return;
  try {
    const r=await apiGET("zoho_books_clone.api.docs.get_party_last_items",{party_type:"Customer",party:form.customer,limit:20});
    if (r?.items?.length) {
      lines.value=[...lines.value,...r.items.map((it,i)=>({id:Date.now()+i,item_code:it.item_code||"",item_name:it.item_name||"",description:it.description||"",hsn_code:"",qty:flt(it.qty)||1,rate:flt(it.rate)||0,uom:"Nos",discount_percentage:0,discount_amount:0,amount:Math.round(flt(it.qty)*flt(it.rate)*100)/100}))];
      toast("Copied "+r.items.length+" items from last invoice");
    } else toast("No previous items found for this customer","info");
  } catch (e) { toast("Could not copy items: "+e.message,"error"); }
}

// ── Drawer open ────────────────────────────────────────────────────────
function openAdd() {
  editingName.value=null;
  lines.value=[{id:Date.now(),item_code:"",item_name:"",description:"",hsn_code:"",qty:1,rate:0,uom:"Nos",discount_percentage:0,discount_amount:0,amount:0}];
  taxRows.value=[];
  Object.assign(form,{customer:"",posting_date:todayStr(),due_date:dueDateDefault(),po_no:"",payment_terms:"Net 30",place_of_supply:"",billing_address:"",shipping_address:"",selected_billing_addr_name:"",selected_shipping_addr_name:"",terms:"",remarks:"",docstatus:0,currency:"INR",exchange_rate:1,gst_treatment:"",update_stock:0,set_warehouse:""});
  customerBillingAddrs.value=[]; customerShippingAddrs.value=[]; sameAsBillingAddr.value=false;
  fetchWarehouses("");
  drawerOpen.value=true;
}
async function openEdit(inv) {
  editingName.value=inv.name;
  Object.assign(form,{customer:inv.customer||"",currency:inv.currency||"INR",exchange_rate:inv.exchange_rate||1,posting_date:inv.posting_date||todayStr(),due_date:inv.due_date||dueDateDefault(),po_no:"",payment_terms:"",place_of_supply:"",billing_address:"",shipping_address:"",selected_billing_addr_name:"",selected_shipping_addr_name:"",terms:"",remarks:"",docstatus:inv.docstatus||0,update_stock:0,set_warehouse:""});
  lines.value=[{id:Date.now(),item_code:"",item_name:"",description:"",hsn_code:"",qty:1,rate:0,uom:"Nos",discount_percentage:0,discount_amount:0,amount:0}];
  taxRows.value=[];
  customerBillingAddrs.value=[]; customerShippingAddrs.value=[]; sameAsBillingAddr.value=false;
  fetchWarehouses("");
  drawerOpen.value=true;
  // Load addresses in parallel with doc fetch
  const [doc, billingAddrs, shippingAddrs] = await Promise.all([
    apiGet("Sales Invoice",inv.name).catch(()=>({})),
    apiList("Address",{fields:["name","address_title","address_line1","address_line2","city","state","pincode"],filters:[["Dynamic Link","link_name","=",inv.customer||""],["Dynamic Link","link_doctype","=","Customer"],["address_type","=","Billing"]],order:"`tabAddress`.modified desc",limit:20}).catch(()=>[]),
    apiList("Address",{fields:["name","address_title","address_line1","address_line2","city","state","pincode"],filters:[["Dynamic Link","link_name","=",inv.customer||""],["Dynamic Link","link_doctype","=","Customer"],["address_type","=","Shipping"]],order:"`tabAddress`.modified desc",limit:20}).catch(()=>[]),
  ]);
  customerBillingAddrs.value  = billingAddrs  || [];
  customerShippingAddrs.value = shippingAddrs || [];
  if (doc && doc.name) {
    Object.assign(form,{
      customer:doc.customer||"",posting_date:doc.posting_date||todayStr(),due_date:doc.due_date||dueDateDefault(),
      po_no:doc.po_no||"",payment_terms:doc.payment_terms||"",place_of_supply:doc.place_of_supply||"",
      billing_address:doc.billing_address||"",shipping_address:doc.shipping_address||"",
      terms:doc.terms||"",remarks:doc.remarks||"",docstatus:doc.docstatus||0,
      currency:doc.currency||"INR",exchange_rate:doc.exchange_rate||1,gst_treatment:doc.gst_category||"",
      update_stock:doc.update_stock||0,set_warehouse:doc.set_warehouse||"",
    });
    lines.value=(doc.items||[]).map((it,i)=>({id:Date.now()+i,item_code:it.item_code||"",item_name:it.item_name||"",description:it.description||"",hsn_code:it.hsn_code||"",qty:flt(it.qty)||1,rate:flt(it.rate)||0,uom:it.uom||"Nos",discount_percentage:flt(it.discount_percentage)||0,discount_amount:flt(it.discount_amount)||0,amount:flt(it.amount)||0}));
    taxRows.value=(doc.taxes||[]).map((tx,i)=>({id:Date.now()+100+i,description:tx.description||"",rate:flt(tx.rate)||0,account_head:tx.account_head||taxAccountHead.value,amount:flt(tx.tax_amount)||0}));
    if (!lines.value.length) addLine();
    // Auto-detect "same as billing"
    if (doc.shipping_address && doc.shipping_address===doc.billing_address) sameAsBillingAddr.value=true;
  }
}
async function openView(inv) {
  viewInv.value=inv; viewOpen.value=true; viewTab.value="details"; viewPayments.value=[]; viewLoading.value=true;
  try { const full=await apiGet("Sales Invoice",inv.name); viewInv.value=full; } catch {}
  viewLoading.value=false;
}

// ── Save invoice ───────────────────────────────────────────────────────
async function saveInvoice(docstatus) {
  if (!form.customer) { toast("Customer is required","error"); return; }
  if (!form.posting_date) { toast("Invoice date is required","error"); return; }
  if (!lines.value.some(l=>l.item_code&&flt(l.qty)>0)) { toast("Add at least one line item","error"); return; }
  if (form.update_stock && !form.set_warehouse) { toast("Dispatch Warehouse is required when Update Inventory is on","error"); return; }
  drawerSaving.value=true;
  try {
    const company=await resolveCompany();
    const invItems=lines.value.filter(l=>l.item_code).map(l=>({item_code:l.item_code,item_name:l.item_name||l.item_code,description:l.description||l.item_name||l.item_code,qty:flt(l.qty),rate:flt(l.rate),uom:l.uom||"Nos",amount:flt(l.amount),hsn_code:l.hsn_code||"",discount_percentage:flt(l.discount_percentage)||0,discount_amount:flt(l.discount_amount)||0}));
    const taxes=taxRows.value.filter(r=>r.rate>0).map(r=>({doctype:"Tax Line",charge_type:"On Net Total",account_head:r.account_head||taxAccountHead.value,description:r.description,rate:r.rate}));
    const shipAddr=sameAsBillingAddr.value?form.billing_address:form.shipping_address||"";
    const doc={doctype:"Sales Invoice",customer:form.customer,posting_date:form.posting_date,due_date:form.due_date||form.posting_date,po_no:form.po_no||"",payment_terms:form.payment_terms||"",billing_address:form.billing_address||"",shipping_address:shipAddr,place_of_supply:form.place_of_supply||"",remarks:form.remarks||"",terms:form.terms||"",items:invItems,taxes,company,currency:form.currency||"INR",exchange_rate:form.currency==="INR"?1:(form.exchange_rate||1),gst_category:form.gst_treatment==="Overseas"?"Overseas":form.gst_treatment==="SEZ"?"SEZ":"Regular",update_stock:form.update_stock?1:0,set_warehouse:form.set_warehouse||""};
    if (editingName.value) doc.name=editingName.value;
    const saved=await apiSave(doc);
    if (docstatus===1) await apiSubmit("Sales Invoice",saved.name);
    await load();
    toast(docstatus===1?"Invoice submitted":"Invoice saved as draft");
    drawerOpen.value=false;
  } catch(e) { toast("Save failed: "+e.message,"error"); }
  drawerSaving.value=false;
}

// ── Payment modal ──────────────────────────────────────────────────────
// Phase 0.9 — delegates to the globally mounted PaymentDialog. Same UX as Bills
// (vendor payments) but `direction:"receive"` for customer side.
async function openPayment(inv) {
  const { openPayment: openShared } = usePaymentDialog();
  const paymentName = await openShared({
    direction: "receive",
    doctype: "Sales Invoice", name: inv.name,
    party: inv.customer, partyLabel: inv.customer_name || inv.customer,
    balance: flt(inv.outstanding_amount),
    getDefaultsEndpoint: "zoho_books_clone.api.books_data.get_payment_defaults",
    sendEndpoint:        "zoho_books_clone.api.books_data.record_payment",
    paramKey: "invoice_name",
  });
  if (paymentName) await load();
}
// submitPayment() removed — PaymentDialog handles submission.

// ── Load payments (view tab) ───────────────────────────────────────────
async function loadPayments(invName) {
  if (viewPayments.value.length) return;
  viewPaymentsLoading.value=true;
  try {
    viewPayments.value=await apiGET("zoho_books_clone.api.docs.get_invoice_payments",{invoice_name:invName})||[];
  } catch(e) { console.warn("loadPayments failed:",e.message); viewPayments.value=[]; }
  viewPaymentsLoading.value=false;
}

// ── Email ──────────────────────────────────────────────────────────────
async function openEmail(inv) {
  // Phase 0.9 refactor — delegate to the globally mounted EmailDialog.
  // This gives Invoices the same email UX as Bills / Quotes / SO / PO and
  // removes ~50 lines of inline modal duplication. The legacy inline modal
  // template + sendEmail/enhanceEmail handlers remain in the file as fallback
  // but are no longer opened (emailModal.open stays false).
  const { openEmail: openShared } = useEmailDialog();
  await openShared({
    doctype: "Sales Invoice", name: inv.name, docLabel: `Invoice ${inv.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_invoice_email_defaults",
    sendEndpoint:        "zoho_books_clone.api.docs.send_invoice_email",
    enhanceEndpoint:     "zoho_books_clone.api.books_data.ai_enhance_email",
    paramKey: "invoice_name",
  });
}
// sendEmail / enhanceEmail removed — EmailDialog handles both via its
// `sendEndpoint` + `enhanceEndpoint` props.

// ── Duplicate ──────────────────────────────────────────────────────────
async function duplicateInvoice(inv) {
  try {
    const doc=await apiGet("Sales Invoice",inv.name);
    delete doc.name; doc.docstatus=0; doc.posting_date=todayStr(); doc.due_date=dueDateDefault(); doc.outstanding_amount=0; doc.status="Draft";
    (doc.items||[]).forEach(it=>{ delete it.name; });
    (doc.taxes||[]).forEach(tx=>{ delete tx.name; });
    const saved=await apiSave(doc);
    toast("Duplicated as "+saved.name);
    await load();
  } catch(e) { toast("Duplicate failed: "+e.message,"error"); }
}

// ── Cancel / Delete ────────────────────────────────────────────────────
async function confirmAction(action, inv) {
  if (action==="cancel") {
    const isPaid = inv.outstanding_amount <= 0 && inv.docstatus === 1;
    if (isPaid) {
      // Load linked payments so we can show them in the dialog
      let payments = [];
      try { payments = await apiGET("zoho_books_clone.api.docs.get_invoice_payments", {invoice_name: inv.name}) || []; } catch(e) { /* show dialog anyway */ }
      Object.assign(confirmModal, {
        open: true, loading: false, payments,
        title: "Cancel Invoice & Payment",
        message: `Cancel invoice ${inv.name}? This will reverse all GL entries.`,
        actionLabel: "Cancel Invoice & Payment",
        action: async () => {
          confirmModal.loading = true;
          try {
            await apiPOST("zoho_books_clone.api.docs.cancel_invoice_with_payments", {invoice_name: inv.name});
            toast("Invoice and linked payment(s) cancelled");
            confirmModal.open = false;
            viewOpen.value = false;
            await load();
          } catch(e) {
            toast(e.message || "Cancel failed", "error");
            confirmModal.loading = false;
          }
        },
      });
    } else {
      Object.assign(confirmModal,{open:true,loading:false,payments:[],title:"Cancel Invoice",message:`Cancel ${inv.name}? This will reverse all GL entries. This cannot be undone.`,actionLabel:"Cancel Invoice",action:async()=>{confirmModal.loading=true;try{await apiCancel("Sales Invoice",inv.name);toast("Invoice cancelled");viewOpen.value=false;await load();}catch(e){toast(e.message||"Cancel failed","error");}confirmModal.open=false;}});
    }
  } else {
    Object.assign(confirmModal,{open:true,loading:false,payments:[],title:"Delete Invoice",message:`Permanently delete draft ${inv.name}? This cannot be undone.`,actionLabel:"Delete",action:async()=>{confirmModal.loading=true;try{await apiDelete("Sales Invoice",inv.name);toast("Invoice deleted");viewOpen.value=false;await load();}catch(e){toast(e.message||"Delete failed","error");}confirmModal.open=false;}});
  }
}

// ── Credit Note ────────────────────────────────────────────────────────
// Phase 0.9 — delegates to the globally mounted ReturnNoteDialog. The shared
// dialog already pre-fills items from the invoice and warns about existing CNs.
async function openCreditNote(inv) {
  const { openReturnNote } = useReturnNote();
  const result = await openReturnNote({
    kind: "credit",
    parentName: inv.name,
    party: inv.customer,
    items: (inv.items || []).map(it => ({
      item_code: it.item_code, item_name: it.item_name,
      description: it.description, qty: it.qty, rate: it.rate,
    })),
    existingEndpoint: "zoho_books_clone.api.docs.get_credit_notes",
    createEndpoint:   "zoho_books_clone.api.docs.create_credit_note",
    paramKey:  "invoice_name",
    partyKey:  "customer",
    parentKey: "against_invoice",
  });
  if (result) { viewOpen.value = false; await load(); }
}
// submitCreditNote removed — ReturnNoteDialog handles submission via its
// `createEndpoint` prop. openCreditNote() above now resolves a promise with
// the created CN name.

// ── Make Recurring ─────────────────────────────────────────────────────
async function makeRecurring(inv) {
  const { openMakeRecurring } = useMakeRecurring();
  const subName = await openMakeRecurring({
    doctype: "Sales Invoice",
    name: inv.name,
    partyLabel: inv.customer_name || inv.customer || "",
    amount: inv.grand_total || 0,
  });
  if (subName) toast(`Recurring subscription ${subName} created`);
}

// ── Bulk actions ───────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts=sorted.value.filter(i=>selectedRows.value.has(i.name)&&i.docstatus===0);
  if (!drafts.length) { toast("No draft invoices selected","info"); return; }
  for (const inv of drafts) { try { await apiDelete("Sales Invoice",inv.name); } catch {} }
  selectedRows.value=new Set(); toast(`Deleted ${drafts.length} draft invoice(s)`); await load();
}
async function bulkCancel() {
  const submitted=sorted.value.filter(i=>selectedRows.value.has(i.name)&&i.docstatus===1);
  if (!submitted.length) { toast("No submitted invoices selected","info"); return; }
  let done=0, failed=0;
  for (const inv of submitted) {
    try {
      const isPaid = inv.outstanding_amount <= 0;
      if (isPaid) {
        await apiPOST("zoho_books_clone.api.docs.cancel_invoice_with_payments", {invoice_name: inv.name});
      } else {
        await apiCancel("Sales Invoice", inv.name);
      }
      done++;
    } catch(e) { failed++; toast(`${inv.name}: ${e.message||"cancel failed"}`, "error"); }
  }
  selectedRows.value=new Set();
  if (done) toast(`Cancelled ${done} invoice(s)${failed?`, ${failed} failed`:""}`);
  await load();
}
async function bulkEmail() {
  const sel=sorted.value.filter(i=>selectedRows.value.has(i.name));
  if (!sel.length) return;
  if (sel.length===1) { openEmail(sel[0]); return; }
  toast(`Bulk email for ${sel.length} invoices — opening first invoice`,"info");
  openEmail(sel[0]);
}

// ── Export CSV ─────────────────────────────────────────────────────────
function exportCSV() {
  const source = selectedRows.value.size > 0
    ? sorted.value.filter(i => selectedRows.value.has(i.name))
    : sorted.value;
  if (!source.length) { toast("No invoices to export", "info"); return; }
  const headers=["Date","Invoice#","PO Number","Customer","Status","Due Date","Amount","Balance Due"];
  const rows=source.map(i=>[i.posting_date,i.name,i.po_no||"",i.customer_name||i.customer,statusLabel(i),i.due_date||"",i.grand_total,i.outstanding_amount]);
  const csv=[headers,...rows].map(r=>r.map(c=>`"${String(c).replace(/"/g,'""')}"`).join(",")).join("\n");
  const blob=new Blob(["﻿"+csv],{type:"text/csv;charset=utf-8"}); const url=URL.createObjectURL(blob);
  const a=document.createElement("a"); a.href=url; a.download=`invoices_${todayStr()}.csv`; a.click(); URL.revokeObjectURL(url);
  const label = selectedRows.value.size > 0 ? `${source.length} selected invoice(s)` : `${source.length} invoice(s)`;
  toast(`CSV exported — ${label}`);
}

// ── Branding persistence ───────────────────────────────────────────────
function saveBranding() {
  try {
    const co=window.__booksCompany||"_default";
    localStorage.setItem("books_inv_branding_"+co, JSON.stringify({template:selectedTemplate.value,color:brandColor.value,logo:logoUrl.value}));
  } catch {}
}
function loadBranding() {
  try {
    const co=window.__booksCompany||"_default";
    const s=JSON.parse(localStorage.getItem("books_inv_branding_"+co)||"{}");
    if (s.template) selectedTemplate.value=s.template;
    if (s.color)    brandColor.value=s.color;
    if (s.logo)     logoUrl.value=s.logo;
  } catch {}
}

// ── Invoice rendering ──────────────────────────────────────────────────
function renderInvoice(d, tmpl, color, logo) {
  const fmt = v=>"₹"+Number(v||0).toLocaleString("en-IN",{minimumFractionDigits:2,maximumFractionDigits:2});
  const fmtD = v=>v?new Date(v).toLocaleDateString("en-IN",{day:"2-digit",month:"short",year:"numeric"}):"—";
  const co = d.company||window.__booksCompany||"Your Company";
  const c = color||"#1a6ef7";
  const itemRows = (d.items||[]).filter(it=>it.item_code||it.item_name).map(it=>`
    <tr>
      <td>${it.item_name||it.item_code||""}${it.description?`<br><small style="color:#888">${it.description}</small>`:""}</td>
      <td style="text-align:center">${it.hsn_code||"—"}</td>
      <td style="text-align:center">${Number(it.qty||0)}</td>
      <td style="text-align:right">${fmt(it.rate)}</td>
      <td style="text-align:right">${it.discount_percentage?it.discount_percentage+"%":"—"}</td>
      <td style="text-align:right;font-weight:600">${fmt(it.amount)}</td>
    </tr>`).join("");
  const taxRows2 = (d.taxes||[]).filter(t=>t.rate>0||t.amount>0).map(t=>`
    <tr><td>${t.description||"Tax"}</td><td style="text-align:right">${fmt(t.amount||t.tax_amount||0)}</td></tr>`).join("");
  const logoTag = logo?`<img src="${logo}" style="max-width:80px;max-height:55px;object-fit:contain;display:block;margin-bottom:8px" alt="logo"/>`:"";
  const noItems = `<tr><td colspan="6" style="text-align:center;color:#aaa;padding:20px">No items</td></tr>`;
  if (tmpl==="modern") return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:12px;color:#1a1a2e;background:#fff}
.hband{background:${c};color:#fff;padding:28px 36px}.hinner{display:flex;justify-content:space-between;align-items:flex-start}
.co-name{font-size:19px;font-weight:700}.inv-chip{background:rgba(255,255,255,.2);border-radius:6px;padding:3px 12px;font-size:10px;font-weight:700;letter-spacing:1px;margin-bottom:6px;display:inline-block}
.inv-num{font-size:22px;font-weight:700}.body{padding:28px 36px}
.mgrid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:20px;margin-bottom:24px;padding:18px;background:#f8fafc;border-radius:8px}
.ml{font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#9ca3af;margin-bottom:4px}
.mv{font-size:13px;font-weight:600;color:#1a1a2e}table.it{width:100%;border-collapse:collapse;margin-bottom:18px}
table.it thead th{padding:9px 11px;font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#9ca3af;border-bottom:2px solid #e8ecf0;text-align:left}
table.it tbody td{padding:9px 11px;border-bottom:1px solid #f0f2f5;font-size:12px}
.tw{display:flex;justify-content:flex-end;margin-bottom:20px}.tot{width:270px;background:#f8fafc;border-radius:8px;padding:14px}
.tr2{display:flex;justify-content:space-between;padding:4px 0;font-size:12px}.tr2.gr{border-top:2px solid ${c};margin-top:7px;padding-top:9px;font-size:14px;font-weight:700;color:${c}}
@media print{@page{size:A4;margin:0}body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}</style></head><body>
<div class="hband"><div class="hinner"><div>${logoTag}<div class="co-name">${co}</div></div><div style="text-align:right"><div class="inv-chip">INVOICE</div><div class="inv-num">${d.name||"DRAFT"}</div></div></div></div>
<div class="body"><div class="mgrid">
<div><div class="ml">Bill To</div><div class="mv">${d.customer_name||d.customer||"—"}</div>${d.billing_address?`<div style="font-size:11px;color:#6b7280;margin-top:4px">${d.billing_address}</div>`:""}</div>
<div><div class="ml">Invoice Date</div><div class="mv">${fmtD(d.posting_date)}</div><div class="ml" style="margin-top:10px">Due Date</div><div class="mv">${fmtD(d.due_date)}</div></div>
<div>${d.po_no?`<div class="ml">PO Number</div><div class="mv">${d.po_no}</div>`:""} ${d.place_of_supply?`<div class="ml" style="margin-top:10px">Place of Supply</div><div class="mv">${d.place_of_supply}</div>`:""}</div>
</div>
<table class="it"><thead><tr><th style="width:35%">Item</th><th style="width:10%">HSN/SAC</th><th style="width:8%;text-align:center">Qty</th><th style="width:14%;text-align:right">Rate</th><th style="width:10%;text-align:right">Disc</th><th style="width:14%;text-align:right">Amount</th></tr></thead><tbody>${itemRows||noItems}</tbody></table>
<div class="tw"><div class="tot"><div class="tr2"><span style="color:#6b7280">Subtotal</span><span>${fmt(d.subtotal||0)}</span></div>${taxRows2}<div class="tr2 gr"><span>Total</span><span>${fmt(d.grandTotal||0)}</span></div></div></div>
${d.terms?`<div style="background:#f0f9ff;border-radius:8px;padding:11px 14px;font-size:12px;color:#374151"><strong>Note:</strong> ${d.terms}</div>`:""}</div></body></html>`;

  if (tmpl==="minimal") return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:'Helvetica Neue',Helvetica,Arial,sans-serif;font-size:12px;color:#333;background:#fff;padding:48px}
.page{max-width:720px;margin:0 auto}.header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:40px;padding-bottom:20px;border-bottom:3px solid ${c}}
.co-name{font-size:17px;font-weight:700;color:#111}.inv-label{font-size:30px;font-weight:300;color:#999;letter-spacing:3px}.inv-num{font-size:13px;font-weight:700;color:${c};margin-top:4px}
.brow{display:flex;justify-content:space-between;margin-bottom:32px}.lbl{font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#aaa;margin-bottom:6px}
.val{font-size:13px;color:#222;font-weight:600}.sval{font-size:11.5px;color:#777;margin-top:3px}
table.it{width:100%;border-collapse:collapse;margin-bottom:20px}table.it thead th{padding:7px 0;font-size:9.5px;font-weight:700;text-transform:uppercase;letter-spacing:.7px;color:#bbb;border-bottom:1px solid #eee;text-align:left}
table.it tbody td{padding:9px 0;border-bottom:1px solid #f5f5f5;font-size:12px;vertical-align:top}
.tot{margin-left:auto;width:230px}.tr2{display:flex;justify-content:space-between;padding:4px 0;font-size:12px;color:#666}.tr2.gr{border-top:3px solid ${c};margin-top:7px;padding-top:9px;color:${c};font-size:14px;font-weight:700}
.notes{margin-top:32px;padding-top:16px;border-top:1px solid #eee;font-size:11.5px;color:#888}
@media print{body{padding:24px}@page{size:A4;margin:15mm}}</style></head><body>
<div class="page"><div class="header"><div>${logoTag}<div class="co-name">${co}</div></div><div style="text-align:right"><div class="inv-label">INVOICE</div><div class="inv-num">${d.name||"DRAFT"}</div></div></div>
<div class="brow"><div><div class="lbl">Bill To</div><div class="val">${d.customer_name||d.customer||"—"}</div>${d.billing_address?`<div class="sval">${d.billing_address}</div>`:""}</div>
<div style="text-align:right"><div class="lbl">Invoice Date</div><div class="val">${fmtD(d.posting_date)}</div><div class="lbl" style="margin-top:10px">Due Date</div><div class="val">${fmtD(d.due_date)}</div></div>
${d.po_no?`<div style="text-align:right"><div class="lbl">PO Number</div><div class="val">${d.po_no}</div></div>`:""}</div>
<table class="it"><thead><tr><th style="width:40%">Description</th><th style="width:10%;text-align:center">Qty</th><th style="width:15%;text-align:right">Rate</th><th style="width:10%;text-align:right">Disc</th><th style="width:15%;text-align:right">Amount</th></tr></thead>
<tbody>${(d.items||[]).filter(it=>it.item_code||it.item_name).map(it=>`<tr><td>${it.item_name||it.item_code||""}${it.description?`<br><span style="color:#bbb;font-size:11px">${it.description}</span>`:""}</td><td style="text-align:center">${Number(it.qty||0)}</td><td style="text-align:right">${fmt(it.rate)}</td><td style="text-align:right">${it.discount_percentage?it.discount_percentage+"%":"—"}</td><td style="text-align:right;font-weight:600">${fmt(it.amount)}</td></tr>`).join("")||`<tr><td colspan="5" style="text-align:center;color:#bbb;padding:20px">No items</td></tr>`}</tbody></table>
<div class="tot"><div class="tr2"><span>Subtotal</span><span>${fmt(d.subtotal||0)}</span></div>${(d.taxes||[]).filter(t=>t.rate>0||t.amount>0).map(t=>`<div class="tr2"><span>${t.description||"Tax"}</span><span>${fmt(t.amount||t.tax_amount||0)}</span></div>`).join("")}<div class="tr2 gr"><span>Total</span><span>${fmt(d.grandTotal||0)}</span></div></div>
${d.terms?`<div class="notes"><strong>Note:</strong> ${d.terms}</div>`:""}</div></body></html>`;

  return `<!DOCTYPE html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box}body{font-family:Georgia,'Times New Roman',serif;font-size:12px;color:#333;background:#fff;padding:40px}
.page{max-width:750px;margin:0 auto}.header{display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:32px}
.co-name{font-size:21px;font-weight:bold;color:${c};margin-bottom:4px}.inv-label{font-size:28px;font-weight:bold;color:${c};text-align:right;letter-spacing:2px}
.meta{text-align:right;margin-top:8px}.meta table{margin-left:auto}.meta td{padding:2px 6px;font-size:12px}.meta td:first-child{color:#666;text-align:right}.meta td:last-child{font-weight:600;color:#333}
.div{border:none;border-top:2px solid ${c};margin:18px 0}.brow{display:flex;justify-content:space-between;margin-bottom:22px}
.lbl{font-size:10px;font-weight:bold;text-transform:uppercase;letter-spacing:.5px;color:#888;margin-bottom:5px}.val{font-size:14px;font-weight:bold;color:#222}.sval{font-size:12px;color:#555;margin-top:3px;white-space:pre-wrap}
table.it{width:100%;border-collapse:collapse;margin-bottom:14px}table.it thead tr{background:${c};color:#fff}table.it thead th{padding:8px 10px;font-size:11px;font-weight:600;text-align:left}
table.it tbody td{padding:8px 10px;border-bottom:1px solid #eee;font-size:12px}table.it tbody tr:last-child td{border-bottom:2px solid ${c}}
.tw{display:flex;justify-content:flex-end;margin-bottom:22px}.tot{width:260px}.tr2{display:flex;justify-content:space-between;padding:4px 0;font-size:12px}
.tr2.gr{border-top:2px solid ${c};margin-top:6px;padding-top:8px;font-size:14px;font-weight:bold;color:${c}}
.fn{border-top:1px solid #ddd;padding-top:12px;font-size:11px;color:#666}
@media print{body{padding:0}@page{size:A4;margin:20mm}}</style></head><body>
<div class="page"><div class="header"><div>${logoTag}<div class="co-name">${co}</div></div><div><div class="inv-label">INVOICE</div><div class="meta"><table><tr><td>Invoice #</td><td>${d.name||"DRAFT"}</td></tr><tr><td>Date</td><td>${fmtD(d.posting_date)}</td></tr><tr><td>Due Date</td><td>${fmtD(d.due_date)}</td></tr>${d.po_no?`<tr><td>PO #</td><td>${d.po_no}</td></tr>`:""}</table></div></div></div>
<hr class="div"/>
<div class="brow"><div><div class="lbl">Bill To</div><div class="val">${d.customer_name||d.customer||"—"}</div>${d.billing_address?`<div class="sval">${d.billing_address}</div>`:""}</div>${d.place_of_supply?`<div><div class="lbl">Place of Supply</div><div style="font-size:12px">${d.place_of_supply}</div></div>`:""}</div>
<table class="it"><thead><tr><th style="width:35%">Item</th><th style="width:10%">HSN/SAC</th><th style="width:8%;text-align:center">Qty</th><th style="width:14%;text-align:right">Rate</th><th style="width:10%;text-align:right">Discount</th><th style="width:14%;text-align:right">Amount</th></tr></thead><tbody>${itemRows||noItems}</tbody></table>
<div class="tw"><div class="tot"><div class="tr2"><span>Subtotal</span><span>${fmt(d.subtotal||0)}</span></div>${taxRows2}<div class="tr2 gr"><span>Grand Total</span><span>${fmt(d.grandTotal||0)}</span></div></div></div>
${d.terms?`<div class="fn"><div class="lbl">Notes</div><p>${d.terms}</p></div>`:""}</div></body></html>`;
}

function printInvoice(data) {
  const html=renderInvoice(data, selectedTemplate.value, brandColor.value, logoUrl.value);
  const win=window.open("","_blank","width=820,height=1060,scrollbars=yes");
  if (!win) { toast("Pop-up blocked — allow pop-ups to print","error"); return; }
  win.document.write(html);
  win.document.close();
  setTimeout(()=>{ try { win.focus(); win.print(); } catch {} }, 600);
}

function printViewInvoice() {
  const inv=viewInv.value;
  if (!inv) return;
  printInvoice({
    name:inv.name, customer:inv.customer, customer_name:inv.customer_name,
    posting_date:inv.posting_date, due_date:inv.due_date, po_no:inv.po_no,
    place_of_supply:inv.place_of_supply, billing_address:inv.billing_address_display||"",
    items:inv.items||[], taxes:inv.taxes||[],
    subtotal:(flt(inv.grand_total)-flt(inv.total_taxes_and_charges)),
    totalTax:flt(inv.total_taxes_and_charges), grandTotal:flt(inv.grand_total),
    terms:inv.terms||"", company:inv.company||window.__booksCompany||"",
  });
}

onMounted(async () => {
  await load();
  loadCustomers(); loadItems(); loadTaxAccount(); loadBranding();

  // Cross-document deep link: /invoices?open=INV-...
  useOpenFromQuery({
    route,
    openByName: (n) => {
      const row = list.value.find(r => r.name === n) || { name: n };
      openView(row);
    },
  });

  // Apply AI-driven URL params (set by AppShell AI handlers via router.push)
  const q = route.query;
  if (q.ai_filter) {
    activeFilter.value = q.ai_filter;          // "Overdue" | "Unpaid" | "Draft" | "Paid"
  }
  if (q.ai_search) {
    search.value = decodeURIComponent(q.ai_search);
    activeFilter.value = "all";
  }
  if (q.ai_create) {
    openAdd();
    nextTick(() => {
      if (q.ai_customer) form.customer = decodeURIComponent(q.ai_customer);
      if (q.ai_item) {
        lines.value = [{
          id: Date.now(), item_code: "",
          item_name:  decodeURIComponent(q.ai_item),
          description: "", hsn_code: "",
          qty:    Number(q.ai_qty)    || 1,
          rate:   Number(q.ai_rate)   || 0,
          uom:    "Nos",
          discount_percentage: 0, discount_amount: 0,
          amount: Number(q.ai_amount) || 0,
        }];
      }
    });
  }
});

// Re-apply AI params when query changes (user is already on page when AI fires)
watch(() => route.query, (q) => {
  if (!q) return;
  if (q.ai_filter) activeFilter.value = q.ai_filter;
  if (q.ai_search) { search.value = decodeURIComponent(q.ai_search); activeFilter.value = "all"; }
  if (q.ai_create) {
    openAdd();
    nextTick(() => {
      if (q.ai_customer) form.customer = decodeURIComponent(q.ai_customer);
      if (q.ai_item) {
        lines.value = [{
          id: Date.now(), item_code: "",
          item_name:  decodeURIComponent(q.ai_item),
          description: "", hsn_code: "",
          qty:    Number(q.ai_qty)    || 1,
          rate:   Number(q.ai_rate)   || 0,
          uom:    "Nos",
          discount_percentage: 0, discount_amount: 0,
          amount: Number(q.ai_amount) || 0,
        }];
      }
    });
  }
});
</script>

<style scoped>
.inv-page { display:flex; flex-direction:column; gap:16px; padding:24px; min-height:100%; color:#1a1a2e; background:#f5f6f8; }

/* ── Toolbar ── */
.inv-toolbar { display:flex; align-items:center; justify-content:space-between; padding:16px 24px 12px; border-bottom:1px solid #e8ecf0; gap:12px; flex-wrap:wrap; }
.inv-heading { font-size:16px; font-weight:700; color:#1a1a2e; margin:0; }
.inv-toolbar-right { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.inv-search-wrap { display:flex; align-items:center; gap:7px; border:1px solid #ffffff; border-radius:20px; padding:6px 12px; background:#f9fafb; }
.inv-search-input { border:none; outline:none; background:transparent; font-size:13px; width:200px; color:#374151; }
.inv-btn-primary { display:inline-flex; align-items:center; gap:6px; background:#1a6ef7; color:#fff; border:none; border-radius:6px; padding:7px 16px; font-size:13px; font-weight:600; cursor:pointer; }
.inv-btn-primary:hover { background:#155fd4; } .inv-btn-primary:disabled { opacity:.55; cursor:not-allowed; }
.inv-btn-ghost { display:inline-flex; align-items:center; gap:6px; background:#fff; color:#374151; border:1px solid #e8ecf0; border-radius:6px; padding:7px 12px; font-size:13px; font-weight:500; cursor:pointer; }
.inv-btn-ghost:hover { border-color:#374151; }

/* ── Summary strip ── */
.inv-sum-strip { display:grid; grid-template-columns:repeat(4,1fr); border-bottom:1px solid #e8ecf0; }
.inv-sum-card { padding:14px 24px; border-right:1px solid #e8ecf0; }
.inv-sum-card:last-child { border-right:none; }
.inv-sum-lbl { font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:#9ca3af; margin-bottom:4px; }
.inv-sum-val { font-size:20px; font-weight:700; font-family:monospace; color:#1a1a2e; }

/* ── Filter bar ── */
.inv-filter-bar { display:flex; align-items:center; justify-content:space-between; padding:10px 24px; border-bottom:1px solid #e8ecf0; flex-wrap:wrap; gap:8px; }
.inv-pills { display:flex; gap:6px; flex-wrap:wrap; }
.inv-pill { display:inline-flex; align-items:center; gap:6px; padding:5px 12px; border-radius:20px; font-size:12.5px; font-weight:600; border:1.5px solid #e8ecf0; background:#fff; color:#6b7280; cursor:pointer; }
.inv-pill:hover { border-color:#1a6ef7; color:#1a6ef7; }
.inv-pill.active { background:#eaf1ff; border-color:#1a6ef7; color:#1a6ef7; }
.inv-pill-count { font-size:10.5px; font-weight:700; padding:1px 6px; border-radius:12px; }
.pc-muted { background:#e5e7eb; color:#6b7280; } .pc-amber { background:#fef3c7; color:#d97706; }
.pc-red   { background:#fee2e2; color:#dc2626; } .pc-green { background:#d1fae5; color:#059669; }
.inv-filter-right { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.inv-date-btns { display:flex; gap:4px; }
.inv-date-btn { border:1px solid #e8ecf0; background:#fff; color:#6b7280; border-radius:6px; padding:4px 10px; font-size:12px; font-weight:600; cursor:pointer; }
.inv-date-btn:hover { border-color:#1a6ef7; color:#1a6ef7; }
.inv-date-btn.active { background:#eaf1ff; border-color:#1a6ef7; color:#1a6ef7; }
.inv-date-input { border:1px solid #e8ecf0; border-radius:6px; padding:4px 8px; font-size:12px; outline:none; }
.inv-filter-select { border:1px solid #e8ecf0; border-radius:6px; padding:5px 8px; font-size:12.5px; outline:none; background:#fff; cursor:pointer; color:#374151; }

/* ── Bulk bar ── */
.inv-bulk-bar { display:flex; align-items:center; gap:10px; padding:10px 16px; background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; flex-wrap:wrap; }
.inv-bulk-count { font-size:13px; font-weight:700; color:#1d4ed8; }
.inv-bulk-btn { display:inline-flex; align-items:center; gap:5px; border:1px solid #bfdbfe; background:#fff; color:#374151; border-radius:6px; padding:5px 12px; font-size:12.5px; font-weight:600; cursor:pointer; }
.inv-bulk-btn:hover { border-color:#374151; }
.inv-bulk-danger { border-color:rgba(220,38,38,.3); color:#dc2626; }
.inv-bulk-danger:hover { background:#fee2e2; }
.inv-bulk-clear { background:none; border:none; color:#6b7280; font-size:12px; cursor:pointer; margin-left:auto; }
.inv-bulk-clear:hover { color:#374151; }

/* ── Table ── */
.inv-table-wrap { background:#fff; border:1px solid #e5e7eb; border-radius:10px; overflow:hidden; overflow-x:auto; }
.inv-table { width:100%; border-collapse:collapse; font-size:13px; }
.inv-table th { padding:10px 14px; border-bottom:2px solid #e8ecf0; font-size:11px; font-weight:600; letter-spacing:normal; color:#6b7280; text-align:left; white-space:nowrap; background:#f9f9fb; user-select:none; }
.inv-table th.sortable { cursor:pointer; } .inv-table th.sortable:hover { color:#1a6ef7; }
.sort-arrow { font-size:10px; margin-left:2px; color:#1a6ef7; }
.th-check { width:40px; padding-left:20px; }
.inv-table td { padding:11px 14px; border-bottom:1px solid #f0f2f5; color:#374151; vertical-align:middle; cursor:pointer; }
.td-check { cursor:default; padding-left:20px; }
.inv-row:hover td { background:#f8faff; } .inv-row.selected td { background:#eaf1ff; }
.inv-table tr:last-child td { border-bottom:none; }
.inv-link { color:#1a6ef7; font-weight:600; } .inv-customer { font-weight:600; color:#1a1a2e; }
.mono-sm { font-family:monospace; font-size:12.5px; } .ta-r { text-align:right; }
.text-danger { color:#dc2626; } .text-success { color:#059669; } .text-muted { color:#9ca3af; }

/* ── Status badges ── */
.inv-status-badge { display:inline-flex; align-items:center; padding:3px 10px; border-radius:4px; font-size:10.5px; font-weight:700; letter-spacing:.04em; white-space:nowrap; }
.status-overdue  { color:#dc2626; background:transparent; } .status-paid { color:#059669; background:#d1fae5; }
.status-unpaid   { color:#d97706; background:#fef3c7; }    .status-draft { color:#6b7280; background:#f3f4f6; }
.status-cancelled{ color:#dc2626; background:#fee2e2; }

/* ── Action buttons ── */
.inv-act-btn { background:none; border:1px solid #e8ecf0; border-radius:5px; padding:4px 6px; cursor:pointer; color:#6b7280; display:inline-flex; align-items:center; }
.inv-act-btn:hover { border-color:#374151; color:#374151; }
.inv-act-pay { border-color:rgba(26,110,247,.3); color:#1a6ef7; font-weight:700; font-size:11px; }
.inv-act-pay:hover { background:#eaf1ff; }

/* ── Shimmer ── */
.shimmer { height:12px; border-radius:4px; background:linear-gradient(90deg,#f0f2f5 25%,#e4e7ec 50%,#f0f2f5 75%); background-size:200% 100%; animation:shimmer 1.4s infinite; }
@keyframes shimmer { 0%{background-position:200% 0}100%{background-position:-200% 0} }

/* ── Empty state ── */
.empty-state { padding:48px 0 !important; text-align:center; cursor:default !important; }
.empty-inner { display:flex; flex-direction:column; align-items:center; gap:10px; color:#9ca3af; font-size:13px; }

/* ── Drawer ── */
.inv-drawer-bg { position:fixed; inset:0; z-index:8000; background:rgba(15,23,42,.45); display:flex; justify-content:flex-end; backdrop-filter:blur(2px); }
.inv-drawer-panel { width:720px; max-width:96vw; height:100%; background:#fff; display:flex; flex-direction:column; box-shadow:-20px 0 60px rgba(0,0,0,.15); overflow:hidden; }
.inv-drawer-wide { width:800px; }
.inv-dh { display:flex; align-items:center; justify-content:space-between; padding:18px 24px; background:linear-gradient(135deg,#1e3a5f,#1a6ef7); flex-shrink:0; }
.inv-dh-title { color:#fff; font-size:16px; font-weight:700; }
.inv-dh-sub   { color:rgba(255,255,255,.75); font-size:12px; margin-top:2px; }
.inv-dclose { background:rgba(255,255,255,.15); border:none; cursor:pointer; width:30px; height:30px; border-radius:8px; color:#fff; display:grid; place-items:center; }
.inv-dbody { flex:1; overflow-y:auto; padding:20px 24px; }
.inv-dfooter { padding:14px 24px; border-top:1px solid #e8ecf0; display:flex; justify-content:space-between; align-items:center; background:#f8fafc; flex-shrink:0; }

/* ── Status timeline ── */
.inv-timeline { display:flex; align-items:center; padding:12px 24px; border-bottom:1px solid #e8ecf0; background:#fafbfc; flex-shrink:0; }
.inv-tl-step { display:flex; flex-direction:column; align-items:center; gap:4px; }
.inv-tl-dot { width:22px; height:22px; border-radius:50%; border:2px solid #e2e8f0; background:#fff; display:flex; align-items:center; justify-content:center; font-size:10px; color:#9ca3af; }
.inv-tl-step.done .inv-tl-dot { background:#059669; border-color:#059669; color:#fff; }
.inv-tl-step.danger .inv-tl-dot { background:#dc2626; border-color:#dc2626; color:#fff; }
.inv-tl-label { font-size:11px; font-weight:600; color:#9ca3af; white-space:nowrap; }
.inv-tl-step.done .inv-tl-label { color:#374151; }
.inv-tl-step.danger .inv-tl-label { color:#dc2626; }
.inv-tl-line { flex:1; height:2px; background:#e2e8f0; margin:0 6px; margin-bottom:16px; min-width:40px; }
.inv-tl-line.done { background:#059669; }
.inv-tl-line.danger { background:#dc2626; }

/* ── View actions ── */
.inv-view-actions { display:flex; align-items:center; gap:8px; padding:10px 24px; border-bottom:1px solid #e8ecf0; flex-wrap:wrap; flex-shrink:0; background:#fff; }
.inv-va-btn { display:inline-flex; align-items:center; gap:5px; border:1px solid #e8ecf0; background:#fff; color:#374151; border-radius:6px; padding:6px 12px; font-size:12.5px; font-weight:600; cursor:pointer; }
.inv-va-btn:hover { border-color:#374151; background:#f9fafb; }
.inv-va-pay { background:#1a6ef7; border-color:#1a6ef7; color:#fff; }
.inv-va-pay:hover { background:#155fd4; }
.inv-va-danger { color:#dc2626; border-color:rgba(220,38,38,.3); }
.inv-va-danger:hover { background:#fee2e2; }

/* ── View tabs ── */
.inv-view-tabs { display:flex; gap:0; border-bottom:2px solid #e8ecf0; padding:0 24px; flex-shrink:0; }
.inv-vtab { background:none; border:none; border-bottom:2px solid transparent; padding:10px 16px; margin-bottom:-2px; font-size:13px; font-weight:600; color:#9ca3af; cursor:pointer; display:inline-flex; align-items:center; gap:6px; }
.inv-vtab:hover { color:#374151; }
.inv-vtab.active { color:#1a6ef7; border-bottom-color:#1a6ef7; }
.inv-vtab-count { background:#e0e7ff; color:#1a6ef7; border-radius:10px; padding:1px 6px; font-size:10.5px; font-weight:700; }

/* ── View meta ── */
.inv-view-meta { display:flex; gap:20px; flex-wrap:wrap; margin-bottom:20px; padding-bottom:16px; border-bottom:1px solid #f0f2f5; }
.inv-meta-lbl { font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; margin-bottom:4px; }

/* ── View item rows ── */
.inv-view-items-header { display:grid; grid-template-columns:2fr .7fr .7fr 1fr .7fr 1fr; gap:8px; padding:8px 14px; background:#f8fafc; border-bottom:1px solid #e8ecf0; font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; }
.inv-view-item-row { display:grid; grid-template-columns:2fr .7fr .7fr 1fr .7fr 1fr; gap:8px; padding:9px 14px; border-bottom:1px solid #f0f2f5; font-size:13px; }
.inv-view-item-row:last-child { border-bottom:none; }

/* ── Form helpers ── */
.inv-req { color:#dc2626; }
.inv-sec-lbl { font-size:10.5px; font-weight:700; letter-spacing:.6px; text-transform:uppercase; color:#9ca3af; margin-bottom:12px; margin-top:4px; padding-top:16px; border-top:1px solid #f0f2f5; }
.inv-sec-lbl:first-child { border-top:none; padding-top:0; margin-top:0; }
.inv-fg { display:grid; gap:12px; margin-bottom:14px; }
.inv-fg2 { grid-template-columns:1fr 1fr; } .inv-fg3 { grid-template-columns:1fr 1fr 1fr; }
.inv-lbl { display:block; font-size:11.5px; font-weight:600; color:#495057; margin-bottom:5px; }
.inv-fi { width:100%; border:1px solid #e2e8f0; border-radius:6px; padding:7px 10px; font-size:13px; font-family:inherit; outline:none; box-sizing:border-box; }
.inv-inv-block { border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; gap:12px; transition:background .2s,border-color .2s; }
.inv-inv-block.inv-on  { background:#eff6ff; border:1.5px solid #93c5fd; }
.inv-inv-block.inv-off { background:#f9fafb; border:1.5px solid #e5e7eb; }
.inv-inv-toggle-row { display:flex; align-items:center; gap:12px; }
.inv-inv-icon { width:32px; height:32px; border-radius:8px; background:#dbeafe; color:#2563eb; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.inv-inv-block.inv-off .inv-inv-icon { background:#f3f4f6; color:#9ca3af; }
.inv-inv-text { flex:1; }
.inv-inv-title { font-size:13px; font-weight:700; color:#111827; }
.inv-inv-sub { font-size:11.5px; color:#6b7280; margin-top:2px; line-height:1.4; }
.inv-inv-wh-row { display:flex; flex-direction:column; padding-top:4px; border-top:1px solid #bfdbfe; }
.inv-inv-switch { position:relative; display:inline-block; width:42px; height:24px; flex-shrink:0; }
.inv-inv-switch input { opacity:0; width:0; height:0; }
.inv-inv-slider { position:absolute; cursor:pointer; inset:0; background:#d1d5db; border-radius:24px; transition:.2s; }
.inv-inv-slider:before { content:""; position:absolute; height:18px; width:18px; left:3px; bottom:3px; background:#fff; border-radius:50%; transition:.2s; }
.inv-inv-switch input:checked + .inv-inv-slider { background:#2563eb; }
.inv-inv-switch input:checked + .inv-inv-slider:before { transform:translateX(18px); }
.inv-fi:focus { border-color:#1a6ef7; box-shadow:0 0 0 3px rgba(26,110,247,.08); }
.inv-add-line-btn { display:inline-flex; align-items:center; gap:5px; border:1px solid rgba(26,110,247,.3); background:#eaf1ff; color:#1a6ef7; border-radius:6px; padding:5px 12px; font-size:12.5px; font-weight:600; cursor:pointer; }
.inv-copy-btn { background:#f0fdf4; border-color:rgba(5,150,105,.3); color:#059669; }

/* ── Line items table ── */
.inv-lines-tbl { width:100%; border-collapse:collapse; font-size:13px; }
.inv-lines-tbl th { padding:7px 8px; background:#f8fafc; border-bottom:1px solid #e8ecf0; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; text-align:left; }
.inv-lines-tbl td { padding:4px 6px; border-bottom:1px solid #f0f2f5; }
.inv-ci { width:100%; border:1px solid #e2e8f0; border-radius:5px; padding:5px 7px; font-size:12.5px; font-family:inherit; outline:none; }
.inv-ci:focus { border-color:#1a6ef7; }
.inv-ci-r { text-align:right; }
.inv-rm-line { background:none; border:1px solid rgba(220,38,38,.3); border-radius:4px; padding:3px 5px; cursor:pointer; color:#dc2626; display:inline-flex; align-items:center; }

/* ── Tax section ── */
.inv-totals-wrap { border-top:1px solid #e8ecf0; padding:12px 14px; background:#f8fafc; display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap; }
.inv-tax-section { flex:1; min-width:280px; }
.inv-tax-header { display:flex; align-items:center; gap:10px; margin-bottom:8px; flex-wrap:wrap; }
.inv-tax-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; }
.inv-tax-presets { display:flex; gap:5px; flex-wrap:wrap; }
.inv-preset-btn { border:1px solid #e8ecf0; background:#fff; color:#374151; border-radius:5px; padding:3px 8px; font-size:11.5px; font-weight:600; cursor:pointer; white-space:nowrap; }
.inv-preset-btn:hover { border-color:#1a6ef7; color:#1a6ef7; }
.inv-preset-custom { border-color:rgba(26,110,247,.3); color:#1a6ef7; }
.inv-preset-clear { border-color:rgba(220,38,38,.3); color:#dc2626; }
.inv-tax-tbl { width:100%; border-collapse:collapse; font-size:12.5px; }
.inv-tax-tbl th { padding:5px 8px; font-size:10px; font-weight:700; text-transform:uppercase; color:#9ca3af; text-align:left; border-bottom:1px solid #e8ecf0; }
.inv-tax-tbl td { padding:4px 6px; border-bottom:1px solid #f0f2f5; }

/* ── Totals ── */
.inv-totals { min-width:240px; display:flex; flex-direction:column; gap:5px; align-items:flex-end; }
.inv-total-row { display:flex; justify-content:space-between; align-items:center; width:240px; font-size:13px; color:#374151; }
.inv-total-amt { font-family:monospace; font-weight:600; font-size:13px; }
.inv-grand-total { border-top:1px solid #e8ecf0; padding-top:7px; margin-top:2px; font-weight:700; }

/* ══ Record Payment ══ */
.rp-backdrop { position:fixed; inset:0; background:rgba(15,23,42,.45); display:flex; align-items:center; justify-content:center; z-index:9999; backdrop-filter:blur(2px); }
.rp-dialog { background:#fff; border-radius:10px; box-shadow:0 20px 60px rgba(0,0,0,.2); width:min(640px,95vw); max-height:90vh; overflow-y:auto; display:flex; flex-direction:column; animation:rp-in .2s cubic-bezier(.34,1.56,.64,1); }
@keyframes rp-in { from{opacity:0;transform:scale(.95) translateY(10px)} }
.rp-dialog-header { display:flex; align-items:center; justify-content:space-between; padding:16px 22px 14px; border-bottom:1px solid #e8ecf0; }
.rp-dialog-title { font-size:15px; font-weight:700; color:#1a1a2e; }
.rp-close-btn { background:none; border:none; font-size:16px; color:#9ca3af; cursor:pointer; width:28px; height:28px; display:grid; place-items:center; border-radius:50%; }
.rp-loading { padding:40px; display:flex; align-items:center; justify-content:center; gap:12px; color:#6b7280; }
.rp-spinner { width:20px; height:20px; border-radius:50%; border:2px solid #e8ecf0; border-top-color:#1a6ef7; animation:spin .7s linear infinite; }
@keyframes spin { to{transform:rotate(360deg)} }
.rp-customer-strip { display:flex; align-items:center; gap:12px; padding:12px 22px; background:#f8faff; border-bottom:1px solid #e8ecf0; }
.rp-avatar { width:38px; height:38px; border-radius:50%; background:#1a6ef7; color:#fff; display:flex; align-items:center; justify-content:center; font-size:16px; font-weight:700; flex-shrink:0; }
.rp-cust-name { font-size:14px; font-weight:700; color:#1a1a2e; }
.rp-cust-bal { font-size:12.5px; color:#6b7280; margin-top:2px; }
.rp-body { padding:16px 22px; display:flex; flex-direction:column; gap:12px; }
.rp-row { display:grid; grid-template-columns:1fr 1fr; gap:12px; }
.rp-field { display:flex; flex-direction:column; gap:4px; }
.rp-field-full { display:flex; flex-direction:column; gap:4px; }
.rp-label { font-size:12px; font-weight:600; color:#374151; }
.rp-req::after { content:" *"; color:#dc2626; }
.rp-input { border:1px solid #e2e8f0; border-radius:6px; padding:7px 10px; font-size:13px; font-family:inherit; outline:none; }
.rp-input:focus { border-color:#1a6ef7; box-shadow:0 0 0 3px rgba(26,110,247,.08); }
.rp-amount-input { font-family:monospace; font-size:16px; font-weight:700; }
.rp-select { cursor:pointer; } .rp-textarea { resize:vertical; }
.rp-rich-body { min-height:160px; max-height:280px; overflow-y:auto; line-height:1.6; font-size:13px; cursor:text; }
.rp-rich-body:focus { border-color:#1a6ef7; box-shadow:0 0 0 3px rgba(26,110,247,.08); outline:none; }
.rp-rich-body table { border-collapse:collapse; font-size:13px; margin:8px 0; }
.rp-rich-body td { padding:3px 10px 3px 0; color:#4b5563; }
.rp-summary { background:#f8fafc; border-radius:8px; padding:10px 14px; display:flex; justify-content:space-between; font-size:12.5px; color:#374151; flex-wrap:wrap; gap:8px; }
.rp-footer { display:flex; align-items:center; justify-content:flex-end; gap:10px; padding:14px 22px; border-top:1px solid #e8ecf0; background:#f8fafc; }
.rp-btn { display:inline-flex; align-items:center; gap:6px; border-radius:6px; padding:8px 18px; font-size:13px; font-weight:600; cursor:pointer; border:1px solid transparent; }
.rp-btn:disabled { opacity:.55; cursor:not-allowed; }
.rp-btn-outline { background:#fff; border-color:#e2e8f0; color:#374151; }
.rp-btn-primary { background:#1a6ef7; border-color:#1a6ef7; color:#fff; }
.rp-btn-primary:hover:not(:disabled) { background:#155fd4; }

/* ── Template / branding bar ── */
.inv-tmpl-bar { display:flex; align-items:flex-start; gap:24px; padding:9px 22px; border-bottom:1px solid #e8ecf0; background:#f8fafc; flex-shrink:0; flex-wrap:wrap; }
.inv-tmpl-group { display:flex; flex-direction:column; gap:4px; }
.inv-tmpl-lbl { font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:#9ca3af; }
.inv-tmpl-btns { display:flex; gap:4px; }
.inv-tmpl-btn { border:1px solid #e8ecf0; background:#fff; color:#374151; border-radius:5px; padding:4px 11px; font-size:12px; font-weight:600; cursor:pointer; }
.inv-tmpl-btn:hover { border-color:#1a6ef7; color:#1a6ef7; }
.inv-tmpl-btn.active { background:#eaf1ff; border-color:#1a6ef7; color:#1a6ef7; }
.inv-color-pick { width:34px; height:26px; border:1px solid #e8ecf0; border-radius:5px; cursor:pointer; padding:2px 3px; }
.inv-color-val { font-size:12px; font-family:monospace; color:#374151; }
.inv-logo-input { border:1px solid #e2e8f0; border-radius:5px; padding:4px 8px; font-size:12px; outline:none; width:100%; max-width:300px; }
.inv-logo-input:focus { border-color:#1a6ef7; }
.inv-preview-toggle { display:inline-flex; align-items:center; gap:5px; background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.3); color:#fff; border-radius:6px; padding:5px 11px; font-size:12px; font-weight:600; cursor:pointer; }
.inv-preview-toggle:hover { background:rgba(255,255,255,.25); }

/* ── 3-panel / preview layout ── */
.inv-split { width:min(1400px,98vw) !important; }
.inv-content-row { flex:1; display:flex; overflow:hidden; min-height:0; }
.inv-content-row .inv-dbody { flex:1; overflow-y:auto; min-width:0; }
.inv-preview-pane { width:480px; flex-shrink:0; border-left:1px solid #e8ecf0; display:flex; flex-direction:column; background:#e8ecf0; overflow:hidden; }
.inv-preview-toolbar { display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#fff; border-bottom:1px solid #e8ecf0; flex-shrink:0; }
.inv-preview-iframe { flex:1; border:none; width:100%; min-height:0; background:#fff; }
</style>