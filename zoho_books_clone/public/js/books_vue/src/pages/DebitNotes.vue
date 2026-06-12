<template>
  <div class="list-page">

    <!-- ── Toolbar ── -->
    <div class="sales-toolbar">
      <div class="sales-search">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search debit notes, vendors…" class="sales-search-input" />
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
        <button class="sales-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Debit Note</button>
      </div>
    </div>

    <!-- ── KPI Cards ── -->
    <div class="bk-kpi-grid bk-kpi-grid-4">
      <div class="bk-kpi-card bk-kpi-accent clickable" @click="activeTab='all'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total Debit Notes</div><div class="bk-kpi-value">{{ list.length }}</div><div class="bk-kpi-trend" :class="dnTrends.total.up?'bk-trend-up':'bk-trend-down'">{{ dnTrends.total.up?'↑':'↓' }} {{ dnTrends.total.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-success clickable" @click="activeTab='issued'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dcfce7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#16a34a" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Issued</div><div class="bk-kpi-value bk-kpi-green">{{ counts.issued }}</div><div class="bk-kpi-trend" :class="dnTrends.issued.up?'bk-trend-up':'bk-trend-down'">{{ dnTrends.issued.up?'↑':'↓' }} {{ dnTrends.issued.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#fef3c7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="1.8"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Open Balance</div><div class="bk-kpi-value bk-kpi-amber" style="font-size:18px">{{ fmtCur(summary.openBalance) }}</div><div class="bk-kpi-trend bk-trend-neutral">unapplied debit</div></div></div></div>
      <div class="bk-kpi-card"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#f3f4f6"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12"/><path d="M6 8h12"/><path d="m6 13 8.5 8"/><path d="M6 13h3"/><path d="M9 13c6.667 0 6.667-10 0-10"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total Value</div><div class="bk-kpi-value" style="font-size:18px">{{ fmtCur(summary.totalValue) }}</div><div class="bk-kpi-trend" :class="dnTrends.value.up?'bk-trend-up':'bk-trend-down'">{{ dnTrends.value.up?'↑':'↓' }} {{ dnTrends.value.pct }}% vs last month</div></div></div></div>
    </div>
    <div class="bk-stat-grid">
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month</div><div class="bk-stat-value">{{ dnThisMonth.count }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month Value</div><div class="bk-stat-value" style="font-size:16px">{{ fmtCur(dnThisMonth.value) }}</div></div><div class="bk-stat-icon" style="background:#f8fafc;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Draft</div><div class="bk-stat-value">{{ counts.draft }}</div></div><div class="bk-stat-icon" style="background:#f8fafc;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Avg Debit Value</div><div class="bk-stat-value" style="font-size:16px">{{ fmtCur(dnAvg) }}</div></div><div class="bk-stat-icon" style="background:#e5e7eb;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div></div></div>
    </div>

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button class="bab-danger" @click="bulkDelete">Delete Drafts</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="inv-table-wrap">
      <table class="inv-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">Debit Note # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('supplier_name')" class="sortable">Vendor <span v-html="sortArrow('supplier_name')"></span></th>
            <th @click="sortBy('posting_date')" class="sortable">Date <span v-html="sortArrow('posting_date')"></span></th>
            <th>Against Bill</th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th class="ta-r">Available</th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="9"><div class="shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="d in paged" :key="d.name" class="inv-row" :class="{selected:selected.has(d.name)}">
              <td><input type="checkbox" :checked="selected.has(d.name)" @change="toggle(d.name)" /></td>
              <td @click="openView(d)"><span class="inv-link">{{ d.name }}</span></td>
              <td @click="openView(d)">{{ d.supplier_name || d.supplier || '—' }}</td>
              <td @click="openView(d)" class="text-muted mono-sm">{{ fmtDate(d.posting_date) }}</td>
              <td @click="openView(d)" class="text-muted mono-sm">{{ d.return_against||'—' }}</td>
              <td @click="openView(d)"><span class="inv-status-badge" :class="statusCls(d)">{{ statusLabel(d) }}</span></td>
              <td @click="openView(d)" class="ta-r mono-sm" style="color:#7c2d12">{{ fmtCur(Math.abs(d.grand_total||0)) }}</td>
              <td @click="openView(d)" class="ta-r mono-sm">
                <span v-if="d.docstatus===1" :class="balanceFor(d.name)>0?'text-danger':'text-success'">{{ fmtCur(balanceFor(d.name)) }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="dn-act-cell">
                <button class="inv-act-btn" @click="openView(d)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="d.docstatus===0" class="inv-act-btn" @click="openEdit(d)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button v-if="d.docstatus===1 && balanceFor(d.name)>0" class="inv-act-btn dn-act-apply" @click="applyDN(d)" title="Apply to Bill">↳</button>
                <button v-if="d.docstatus===0 || d.docstatus===2" class="inv-act-btn dn-act-del" @click="deleteDN(d)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="9" class="dn-empty">No debit notes match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Pagination ── -->
    <div v-if="!loading && sorted.length" style="padding:12px 4px 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ── Create/Edit Drawer ── -->
    <div v-if="drawerOpen" class="inv-drawer-bg" @click.self="drawerOpen=false"></div>
    <div class="dn-drawer" :class="{open:drawerOpen}">

      <!-- Header -->
      <div class="inv-dh">
        <div class="dn-dheader-left">
          <div class="dn-dheader-ico" :class="editingName?'edit':''">
            <span><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="12" y1="18" x2="12" y2="12"></line><line x1="9" y1="15" x2="15" y2="15"></line></svg></span>
          </div>
          <div>
            <div class="inv-dh-title">{{ editingName ? 'Edit Debit Note' : 'New Debit Note' }}</div>
            <div class="inv-dh-sub">
              {{ editingName ? editingName : 'Issue a debit against a vendor bill' }}
            </div>
          </div>
        </div>
        <button class="inv-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="inv-dbody dn-dbody">

        <!-- ══ CARD 1: Vendor & Date ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="dnCollapsed.vendor=!dnCollapsed.vendor">
            <div class="add-card-title">
              <span class="add-card-title-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              </span>
              Vendor &amp; Date
            </div>
            <span class="add-card-chevron" :class="{collapsed:dnCollapsed.vendor}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:dnCollapsed.vendor}">
            <div class="inv-fg inv-fg2">
              <div class="dn-field" style="grid-column:1/-1">
                <label class="inv-lbl">Vendor <span class="inv-req">*</span></label>
                <SearchableSelect v-model="form.supplier" :options="vendors" placeholder="Select vendor…"
                  :createable="true" createDoctype="Supplier"
                  @search="fetchVendors" @select="onVendorSelect" />
              </div>
              <div class="dn-field">
                <label class="inv-lbl">Date <span class="inv-req">*</span></label>
                <input v-model="form.posting_date" type="date" class="inv-fi" />
              </div>
              <div class="dn-field">
                <label class="inv-lbl">Reason</label>
                <select v-model="form.reason" class="inv-fi">
                  <option>Vendor Overcharge</option>
                  <option>Goods Returned</option>
                  <option>Damaged Goods</option>
                  <option>Short Delivery</option>
                  <option>Duplicate Invoice</option>
                  <option>Other</option>
                </select>
              </div>
              <div class="dn-field">
                <label class="inv-lbl">Cost Center</label>
                <select v-model="form.cost_center" class="inv-fi">
                  <option value="">— Select —</option>
                  <option v-for="cc in costCenters" :key="cc" :value="cc">{{ cc }}</option>
                </select>
              </div>
            </div>
          </div>
        </div>

        <!-- ══ CARD 2: Bill Selection ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="dnCollapsed.bill=!dnCollapsed.bill">
            <div class="add-card-title">
              <span class="add-card-title-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              </span>
              Bills to Debit Against
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span v-if="selectedBillDocs.length" class="dn-bill-loaded-badge">{{ selectedBillDocs.length }} Bill{{ selectedBillDocs.length > 1 ? 's' : '' }} Loaded</span>
              <span class="add-card-chevron" :class="{collapsed:dnCollapsed.bill}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </span>
            </div>
          </div>
          <div class="add-card-body" :class="{collapsed:dnCollapsed.bill}">

            <!-- No vendor yet -->
            <div v-if="!form.supplier" class="dn-bill-ph">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="2"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
              Select a vendor first to view their bills
            </div>

            <!-- Vendor selected — always show search + bill list -->
            <template v-else>
              <!-- Search bar (always visible) -->
              <div class="dn-field">
                <label class="inv-lbl">Add Bill <span class="inv-opt">(select one or more)</span></label>
                <SearchableSelect v-model="billSearchVal"
                  :options="bills.filter(b => !selectedBillDocs.find(d => d.name === b.value))"
                  placeholder="Search bills for this vendor…"
                  @search="fetchBills" @select="addBill" />
              </div>
              <div v-if="!bills.length && !billLoading && !selectedBillDocs.length" class="dn-no-bills-note">
                No submitted bills found for this vendor.
              </div>

              <!-- List of added bill mini-cards -->
              <div v-if="selectedBillDocs.length" class="dn-bill-list">
                <div v-for="doc in selectedBillDocs" :key="doc.name" class="dn-bill-mini-card">
                  <div class="dn-bill-mini-hdr">
                    <div>
                      <span class="dn-bill-num">{{ doc.name }}</span>
                      <span class="dn-bill-meta" style="margin-left:8px">{{ doc.supplier_name || doc.supplier }} · {{ fmtDate(doc.posting_date) }}</span>
                    </div>
                    <button class="dn-remove-bill-btn" @click="removeBillDoc(doc.name)" title="Remove this bill">×</button>
                  </div>
                  <div class="dn-bill-mini-amounts">
                    <div class="dn-bill-amount-item">
                      <span class="dn-bill-amount-lbl">Grand Total</span>
                      <span class="dn-bill-amount-val">{{ fmtCur(Math.abs(doc.grand_total||0)) }}</span>
                    </div>
                    <div class="dn-bill-amount-sep">·</div>
                    <div class="dn-bill-amount-item">
                      <span class="dn-bill-amount-lbl">Outstanding</span>
                      <span class="dn-bill-amount-val outstanding">{{ fmtCur(Math.abs(doc.outstanding_amount||0)) }}</span>
                    </div>
                    <div class="dn-bill-amount-sep">·</div>
                    <div class="dn-bill-amount-item">
                      <span class="dn-bill-amount-lbl">Items</span>
                      <span class="dn-bill-amount-val">{{ doc.items?.length || 0 }}</span>
                    </div>
                  </div>
                </div>

                <!-- Combined totals (only when 2+ bills) -->
                <div v-if="selectedBillDocs.length > 1" class="dn-bill-combined">
                  <span class="dn-bill-combined-lbl">Combined</span>
                  <div class="dn-bill-amount-item">
                    <span class="dn-bill-amount-lbl">Grand Total</span>
                    <span class="dn-bill-amount-val">{{ fmtCur(totalGrand) }}</span>
                  </div>
                  <div class="dn-bill-amount-sep">·</div>
                  <div class="dn-bill-amount-item">
                    <span class="dn-bill-amount-lbl">Outstanding</span>
                    <span class="dn-bill-amount-val outstanding">{{ fmtCur(totalOutstanding) }}</span>
                  </div>
                  <div class="dn-bill-amount-sep">·</div>
                  <div class="dn-bill-amount-item">
                    <span class="dn-bill-amount-lbl">Items</span>
                    <span class="dn-bill-amount-val">{{ lines.length }}</span>
                  </div>
                </div>
              </div>

              <!-- Preset strip (only when at least one bill added) -->
              <div v-if="selectedBillDocs.length" class="dn-preset-strip">
                <span class="dn-preset-lbl">Quick Debit:</span>
                <button class="dn-preset-btn" :class="{active:debitPreset==='full'}" @click="applyPreset('full')">
                  Full Bill
                </button>
                <button class="dn-preset-btn" :class="{active:debitPreset==='outstanding'}" @click="applyPreset('outstanding')"
                  :disabled="!totalOutstanding" title="Debit only the outstanding amount">
                  Outstanding Only
                </button>
                <button class="dn-preset-btn" :class="{active:debitPreset==='selective'}" @click="applyPreset('selective')">
                  Selective
                </button>
                <span v-if="debitPreset==='custom'" class="dn-preset-custom-badge">Custom</span>
              </div>
            </template>

          </div>
        </div>

        <!-- ══ CARD 3: Debit Items ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="dnCollapsed.items=!dnCollapsed.items">
            <div class="add-card-title">
              <span class="add-card-title-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/></svg>
              </span>
              Debit Items
            </div>
            <div style="display:flex;align-items:center;gap:10px">
              <span v-if="selectedBillDocs.length" class="dn-lines-badge">{{ lines.length }} line{{ lines.length!==1?'s':'' }}</span>
              <span class="add-card-chevron" :class="{collapsed:dnCollapsed.items}">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
              </span>
            </div>
          </div>
          <div class="add-card-body" :class="{collapsed:dnCollapsed.items}" style="padding:0">

            <!-- No bill selected placeholder -->
            <div v-if="!selectedBillDocs.length" class="dn-items-ph">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>
              Add a bill above to load its line items
            </div>

            <!-- Bill(s) loaded — deep item table -->
            <template v-else>
              <!-- Select-all toolbar -->
              <div class="dn-items-toolbar">
                <label class="dn-select-all-label">
                  <input type="checkbox" :checked="lines.every(l=>l.included)" @change="e=>lines.forEach(l=>l.included=e.target.checked)" />
                  <span>Select All</span>
                </label>
                <span class="dn-toolbar-sep"></span>
                <span class="dn-toolbar-hint">{{ includedCt }} of {{ lines.length }} items included</span>
              </div>

              <!-- Deep rows -->
              <div class="dn-items-table" style="border:none;border-radius:0;border-bottom:1px solid #e5e7eb">
                <div class="dn-items-head dn-items-head-deep">
                  <div></div>
                  <div>Item</div>
                  <div class="ta-r">Orig Qty</div>
                  <div>Mode</div>
                  <div>Debit Input</div>
                  <div class="ta-r">Rate</div>
                  <div class="ta-r">Debit Amt</div>
                  <div></div>
                </div>
                <template v-for="group in groupedLines" :key="group.billName">
                  <!-- Bill group header (only shown when 2+ bills) -->
                  <div v-if="selectedBillDocs.length > 1" class="dn-bill-group-header">
                    <span class="dn-bill-group-name">{{ group.billName || 'Unassigned' }}</span>
                    <span class="dn-bill-group-total">{{ fmtCur(group.items.reduce((s,l)=>s+flt(l.original_amount),0)) }}</span>
                  </div>
                <div v-for="line in group.items" :key="line.id"
                  class="dn-items-row-deep-wrap"
                  :class="{'dn-row-excluded': !line.included}">
                  <div class="dn-items-row dn-items-row-deep">
                    <!-- Checkbox -->
                    <div class="dn-row-check">
                      <input type="checkbox" v-model="line.included" />
                    </div>
                    <!-- Item name + orig amount -->
                    <div class="dn-item-deep-name">
                      <span class="dn-item-name">{{ line.item_name || line.item_code || '—' }}</span>
                      <span class="dn-item-orig-amt">{{ fmtCur(line.original_amount) }}</span>
                    </div>
                    <!-- Orig qty -->
                    <div class="ta-r dn-orig-qty">{{ line.original_qty }}</div>
                    <!-- Mode pill -->
                    <div class="dn-mode-cell">
                      <div class="dn-mode-pill-group">
                        <button class="dn-mode-pill" :class="{active:line.mode==='qty'}" @click="line.mode='qty'" :disabled="!line.included" title="Qty Return">Qty</button>
                        <button class="dn-mode-pill" :class="{active:line.mode==='amount'}" @click="line.mode='amount'" :disabled="!line.included" title="Price Adjustment">Amt</button>
                        <button class="dn-mode-pill" :class="{active:line.mode==='pct'}" @click="line.mode='pct'" :disabled="!line.included" title="Percentage">%</button>
                      </div>
                    </div>
                    <!-- Debit Input (changes by mode) -->
                    <div class="dn-debit-input-cell">
                      <!-- Qty mode -->
                      <template v-if="line.mode==='qty'">
                        <div class="dn-input-wrap">
                          <input v-model.number="line.qty" type="number" min="0" :max="line.original_qty" step="0.001"
                            class="dn-deep-input" :disabled="!line.included" @input="syncLineAmount(line)" />
                          <span class="dn-input-sfx">units</span>
                        </div>
                      </template>
                      <!-- Amount mode -->
                      <template v-else-if="line.mode==='amount'">
                        <div class="dn-input-wrap">
                          <span class="dn-input-pfx">₹</span>
                          <input v-model.number="line.custom_amount" type="number" min="0" step="0.01"
                            class="dn-deep-input" :disabled="!line.included" @input="syncLineAmount(line)" />
                        </div>
                      </template>
                      <!-- Pct mode -->
                      <template v-else>
                        <div class="dn-input-wrap">
                          <input v-model.number="line.pct" type="number" min="0" max="100" step="1"
                            class="dn-deep-input" :disabled="!line.included" @input="syncLineAmount(line)" />
                          <span class="dn-input-sfx">%</span>
                        </div>
                        <div class="dn-pct-hint">= {{ fmtCur(effectiveAmount(line)) }}</div>
                      </template>
                    </div>
                    <!-- Rate -->
                    <div class="ta-r mono-sm dn-rate-cell">{{ fmtCur(line.rate) }}</div>
                    <!-- Debit amount -->
                    <div class="ta-r mono-sm dn-deep-amt" :class="{'dn-amt-excluded': !line.included}">
                      {{ line.included ? fmtCur(effectiveAmount(line)) : '—' }}
                    </div>
                    <!-- Remove -->
                    <div><button @click="removeLine(line.id)" class="inv-rm-line"><span v-html="icon('x',12)"></span></button></div>
                  </div>
                  <!-- Per-row progress bar -->
                  <div v-if="line.included && line.original_amount > 0" class="dn-debit-progress-wrap">
                    <div class="dn-debit-progress-bar"
                      :style="`width:${Math.min(100, Math.round(effectiveAmount(line)/line.original_amount*100))}%`">
                    </div>
                  </div>
                </div>
                </template>
              </div>

              <!-- Summary panel -->
              <div class="dn-summary-panel">
                <div class="dn-summary-row">
                  <span class="dn-summary-lbl">Bill Total</span>
                  <span class="dn-summary-bar-wrap">
                    <span class="dn-summary-bar" style="width:100%;background:#e5e7eb"></span>
                  </span>
                  <span class="dn-summary-val">{{ fmtCur(billTotal) }}</span>
                  <span class="dn-summary-pct">100%</span>
                </div>
                <div class="dn-summary-row">
                  <span class="dn-summary-lbl">Debit Total</span>
                  <span class="dn-summary-bar-wrap">
                    <span class="dn-summary-bar" :style="`width:${debitPct}%;background:#ea580c`"></span>
                  </span>
                  <span class="dn-summary-val" style="color:#7c2d12;font-weight:700">{{ fmtCur(subtotal) }}</span>
                  <span class="dn-summary-pct">{{ debitPct }}%</span>
                </div>
                <div class="dn-summary-divider"></div>
                <div class="dn-summary-row">
                  <span class="dn-summary-lbl">Remaining</span>
                  <span class="dn-summary-bar-wrap"></span>
                  <span class="dn-summary-val" :style="remaining < 0 ? 'color:#dc2626' : 'color:#16a34a'">
                    {{ fmtCur(Math.abs(remaining)) }}{{ remaining < 0 ? ' (over)' : '' }}
                  </span>
                  <span class="dn-summary-pct"></span>
                </div>
                <div class="dn-summary-row">
                  <span class="dn-summary-lbl">Items</span>
                  <span class="dn-summary-bar-wrap"></span>
                  <span class="dn-summary-val" style="color:#6b7280">{{ includedCt }} of {{ lines.length }} included</span>
                  <span class="dn-summary-pct"></span>
                </div>
              </div>
            </template>

          </div>
        </div>

        <!-- ══ CARD 4: Notes ══ -->
        <div class="add-card">
          <div class="add-card-header" @click="dnCollapsed.notes=!dnCollapsed.notes">
            <div class="add-card-title">
              <span class="add-card-title-icon">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>
              </span>
              Notes
            </div>
            <span class="add-card-chevron" :class="{collapsed:dnCollapsed.notes}">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="6 9 12 15 18 9"/></svg>
            </span>
          </div>
          <div class="add-card-body" :class="{collapsed:dnCollapsed.notes}">
            <textarea v-model="form.remark" rows="3" maxlength="500" class="inv-fi" placeholder="Internal note (optional)…"></textarea>
              <div class="exp-field-hint" :class="{'exp-field-hint-err': form.remark.length >= 500}">{{ form.remark.length }}/500 characters</div>
          </div>
        </div>

      </div>

      <div class="inv-dfooter">
        <button class="form-btn form-btn-outline" @click="drawerOpen=false" :disabled="drawerSaving">Cancel</button>
        <div>
          <button class="add-btn-draft" style="margin-right:5px" :disabled="drawerSaving" @click="saveDN(0)"><span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}</button>
          <button class="add-btn-more" :disabled="drawerSaving" @click="saveDN(1)"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}</button>
        </div>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="inv-drawer-bg" @click.self="viewOpen=false"></div>
    <div class="dn-drawer dn-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="inv-view-header">
          <div class="dn-view-head-body">
            <div class="dn-view-head-left">
              <div class="inv-view-number">{{ viewDoc.name }}</div>
              <div class="inv-view-subtitle">{{ viewDoc.supplier_name||viewDoc.supplier }}</div>
            </div>
            <div class="dn-view-head-right">
              <div class="dn-view-amount">{{ fmtCur(Math.abs(viewDoc.grand_total||0)) }}</div>
              <span class="inv-hdr-badge" :class="statusCls(viewDoc)">{{ statusLabel(viewDoc) }}</span>
            </div>
          </div>
          <button class="inv-dclose dn-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <div class="dn-stepper-wrap"><TimelineStepper :steps="timelineSteps" /></div>

        <div class="inv-view-tabs">
          <button class="inv-vtab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="inv-vtab" :class="{active:viewTab==='applied'}" @click="viewTab='applied'">
            Applied To<span v-if="viewApplications.length" class="inv-vtab-count">{{ viewApplications.length }}</span>
          </button>
        </div>

        <div class="inv-dbody">
          <template v-if="viewTab==='details'">
            <div class="dn-meta-grid">
              <div><div class="dn-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
              <div><div class="dn-meta-lbl">Return Against</div><div class="mono-sm">{{ viewDoc.return_against||'—' }}</div></div>
              <div><div class="dn-meta-lbl">Total Debit</div><div class="mono-sm" style="color:#7c2d12;font-weight:600">{{ fmtCur(Math.abs(viewDoc.grand_total||0)) }}</div></div>
              <div><div class="dn-meta-lbl">Available Balance</div>
                <div class="mono-sm" :class="viewBalance>0?'text-danger':'text-success'">{{ fmtCur(viewBalance) }}</div>
              </div>
            </div>

            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="inv-sec-lbl">Line Items</div>
              <div class="dn-view-items">
                <div class="dn-view-items-head"><span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span></div>
                <div v-for="it in viewItems" :key="it.name" class="dn-view-items-row">
                  <span>{{ it.item_name||it.item_code }}</span>
                  <span class="ta-r mono-sm">{{ Math.abs(it.qty||0) }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(Math.abs(it.amount||0)) }}</span>
                </div>
              </div>
            </template>
          </template>

          <template v-if="viewTab==='applied'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <div v-else-if="viewApplications.length">
              <div class="dn-app-head"><span>Bill</span><span>Date</span><span>Payment Entry</span><span class="ta-r">Amount Applied</span></div>
              <div v-for="a in viewApplications" :key="a.payment_entry" class="dn-app-row">
                <span class="mono-sm inv-link">{{ a.bill }}</span>
                <span class="mono-sm">{{ fmtDate(a.date) }}</span>
                <span class="mono-sm text-muted">{{ a.payment_entry }}</span>
                <span class="ta-r mono-sm" style="font-weight:600;color:#059669">{{ fmtCur(a.amount) }}</span>
              </div>
            </div>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
              No applications yet.
              <div v-if="viewBalance>0 && viewDoc.docstatus===1" style="margin-top:8px">
                <button class="add-btn-draft" @click="applyDN(viewDoc)" style="font-size:12px;padding:6px 12px">↳ Apply to Bill</button>
              </div>
            </div>
          </template>
        </div>

        <div class="inv-dfooter">
          <button class="form-btn form-btn-outline" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="form-btn form-btn-outline" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button v-if="viewDoc.docstatus===0" class="form-btn form-btn-primary" @click="submitDraftDN(viewDoc)">
            <span v-html="icon('check',13)"></span> Submit
          </button>
          <button v-if="viewDoc.docstatus===1" class="form-btn form-btn-outline" @click="emailDN(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="form-btn form-btn-outline" @click="printDN(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="viewDoc.docstatus===1 && viewBalance>0" class="add-btn-draft" @click="applyDN(viewDoc)">↳ Apply to Bill</button>
          <button v-if="viewDoc.docstatus===1" class="form-btn form-btn-danger" @click="cancelDN(viewDoc)">Cancel</button>
          <button v-if="viewDoc.docstatus===0 || viewDoc.docstatus===2" class="form-btn form-btn-danger" @click="deleteDN(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Apply-to-Bill modal ── -->
    <div v-if="applyModal.open" class="inv-drawer-bg" @click.self="applyModal.open=false" style="z-index:60"></div>
    <div v-if="applyModal.open" class="dn-apply-dialog">
      <div class="inv-dh" style="background:linear-gradient(135deg,#7c2d12,#ea580c);height:auto;padding:14px 18px">
        <div class="inv-dh-title">Apply Debit Note — {{ applyModal.dnName }}</div>
        <button class="inv-dclose" @click="applyModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="inv-dbody">
        <div style="font-size:12.5px;color:#374151">Available Balance: <strong>{{ fmtCur(applyModal.balance) }}</strong></div>
        <div class="dn-field">
          <label class="inv-lbl">Target Bill <span class="inv-req">*</span></label>
          <select v-model="applyModal.bill" class="inv-fi">
            <option value="">— Select bill —</option>
            <option v-for="b in applyModal.openBills" :key="b.name" :value="b.name">
              {{ b.name }} · {{ fmtCur(b.outstanding_amount) }} due
            </option>
          </select>
        </div>
        <div class="dn-field">
          <label class="inv-lbl">Amount to Apply <span class="inv-req">*</span></label>
          <input v-model.number="applyModal.amount" type="number" min="0.01" :max="applyModal.balance" step="0.01" class="inv-fi ta-r" />
        </div>
      </div>
      <div class="inv-dfooter">
        <button class="form-btn form-btn-outline" @click="applyModal.open=false" :disabled="applyModal.saving">Cancel</button>
        <button class="form-btn form-btn-primary" :disabled="applyModal.saving || !applyModal.bill || applyModal.amount<=0" @click="submitApply">
          {{ applyModal.saving ? 'Applying…' : `Apply ${fmtCur(applyModal.amount)}` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiPOST, apiSubmit, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useDocStatus } from "../composables/useDocStatus.js";
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
function printDN(d) { printDoc(d, { title: "DEBIT NOTE", partyLabel: "Vendor", partyField: "supplier_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();
const { statusLabel, statusCls, statusBg } = useDocStatus({
  fallbackDraftLabel: "Draft",
  fallbackSubmittedLabel: "Issued",
  paidStatuses: ["return"],
  pendingStatuses: ["return"],
  completedStatuses: ["return"],
  outstandingField: "_unused",
  dueDateField: "_unused",
  overdueCheck: () => false,
});

const activeTab = ref("all");
const tabs = [
  { key: "all",       label: "All" },
  { key: "draft",     label: "Draft" },
  { key: "issued",    label: "Issued" },
  { key: "cancelled", label: "Cancelled" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const viewLoading = ref(false), viewItems = ref([]), viewApplications = ref([]), viewBalance = ref(0);
const vendors = ref([]), items = ref([]), bills = ref([]), lines = ref([]);
const sortCol = ref("posting_date"), sortDir = ref("desc");
const selectedBillDocs = ref([]);
const billSearchVal = ref("");
const billLoading = ref(false);
const _suppressVendorSelect = ref(false);

// Balance cache by DN name
const _balances = ref({});
function balanceFor(name) { return flt(_balances.value[name] || 0); }

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", item_name: "", description: "", original_qty: 1, original_amount: 0, qty: 1, rate: 0, included: true, mode: "qty", custom_amount: 0, pct: 100, amount: 0 });
const debitPreset = ref("full");
const costCenters = ref([]);
async function fetchCostCenters() {
  try {
    const co = await resolveCompany();
    const r = await apiGET("frappe.client.get_list", { doctype: "Cost Center", fields: JSON.stringify(["name"]), filters: JSON.stringify([["disabled","=",0],["company","=",co],["is_group","=",0]]), order_by: "name asc", limit_page_length: 100 }) || [];
    costCenters.value = r.map(c => c.name);
  } catch { costCenters.value = []; }
}
const form = reactive({ supplier: "", posting_date: todayStr(), return_against: "", reason: "Vendor Overcharge", cost_center: "", remark: "" });
const dnCollapsed = reactive({ vendor: false, bill: false, items: false, notes: true });

// Apply-to-bill modal
const applyModal = reactive({ open: false, saving: false, dnName: "", balance: 0, bill: "", amount: 0, openBills: [] });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function fmtCur(v) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(Math.abs(flt(v))); }

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    const rows = await apiList("Purchase Invoice", {
      fields: ["name", "supplier", "supplier_name", "posting_date", "grand_total", "return_against", "docstatus", "status"],
      filters: [["is_return", "=", 1], ["company", "=", co]],
      limit: 500,
      order: "posting_date desc",
    });
    // Resolve supplier_name for any rows where it's missing
    const missing = [...new Set(rows.filter(d => !d.supplier_name && d.supplier).map(d => d.supplier))];
    if (missing.length) {
      try {
        const suppliers = await apiList("Supplier", {
          fields: ["name", "supplier_name"],
          filters: [["name", "in", missing]],
          limit: missing.length,
        });
        const nameMap = {};
        suppliers.forEach(s => { nameMap[s.name] = s.supplier_name || s.name; });
        rows.forEach(d => { if (!d.supplier_name && d.supplier) d.supplier_name = nameMap[d.supplier] || d.supplier; });
      } catch { /* fallback to supplier id */ }
    }
    list.value = rows;
    // Fetch balances for submitted DNs (parallel)
    const submitted = list.value.filter(d => d.docstatus === 1);
    const balances = await Promise.all(submitted.map(d =>
      apiGET("zoho_books_clone.api.docs.get_debit_note_balance", { debit_note_name: d.name }).catch(() => null)
    ));
    const map = {};
    submitted.forEach((d, i) => { if (balances[i]) map[d.name] = balances[i].balance; });
    _balances.value = map;
  } catch (e) { toast.error(e.message || "Failed to load debit notes"); }
  finally { loading.value = false; }
}

const counts = computed(() => ({
  draft:     list.value.filter(d => d.docstatus === 0).length,
  issued:    list.value.filter(d => d.docstatus === 1).length,
  cancelled: list.value.filter(d => d.docstatus === 2).length,
}));
const summary = computed(() => ({
  totalValue:  list.value.filter(d => d.docstatus === 1).reduce((s, d) => s + Math.abs(flt(d.grand_total)), 0),
  openBalance: Object.values(_balances.value).reduce((s, v) => s + flt(v), 0),
}));
const _dnYM  = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _dnLYM = () => { const d=new Date(); d.setMonth(d.getMonth()-1); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _dnTr  = (a,b) => { if(!b&&!a) return {pct:0,up:true}; if(!b) return {pct:100,up:true}; const p=Math.round((a-b)/b*100); return {pct:Math.abs(p),up:p>=0}; };
const dnThisMonth = computed(()=>{ const ym=_dnYM(); const r=list.value.filter(d=>(d.posting_date||'').startsWith(ym)); return {count:r.length,value:r.reduce((s,d)=>s+Math.abs(flt(d.grand_total)),0)}; });
const dnAvg = computed(()=>{ const p=list.value.filter(d=>d.grand_total); return p.length?p.reduce((s,d)=>s+Math.abs(flt(d.grand_total)),0)/p.length:0; });
const dnTrends = computed(()=>({
  total:  _dnTr(dnThisMonth.value.count, list.value.filter(d=>(d.posting_date||'').startsWith(_dnLYM())).length),
  issued: _dnTr(counts.value.issued, list.value.filter(d=>(d.posting_date||'').startsWith(_dnLYM())&&d.docstatus===1).length),
  value:  _dnTr(dnThisMonth.value.value, list.value.filter(d=>(d.posting_date||'').startsWith(_dnLYM())&&d.docstatus===1).reduce((s,d)=>s+Math.abs(flt(d.grand_total)),0)),
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value === "draft")     r = r.filter(d => d.docstatus === 0);
  if (activeTab.value === "issued")    r = r.filter(d => d.docstatus === 1);
  if (activeTab.value === "cancelled") r = r.filter(d => d.docstatus === 2);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.supplier_name || x.supplier || "").toLowerCase().includes(q)
      || (x.return_against || "").toLowerCase().includes(q));
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
const { page, pageSize, paged } = usePagination(sorted, { storageKey: "debit-notes" });
function sortBy(col) { if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc"; else { sortCol.value = col; sortDir.value = "asc"; } }
function sortArrow(col) { if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value === "asc" ? "↑" : "↓"; }

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(d => selected.value.has(d.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(d => d.name)) : new Set(); }

function effectiveAmount(line) {
  if (!line.included) return 0;
  if (line.mode === "amount") return Math.round(flt(line.custom_amount) * 100) / 100;
  if (line.mode === "pct")    return Math.round(flt(line.original_amount) * flt(line.pct) / 100 * 100) / 100;
  return Math.round(flt(line.qty) * flt(line.rate) * 100) / 100;
}
function syncLineAmount(line) {
  line.amount = effectiveAmount(line);
}
function applyPreset(preset) {
  debitPreset.value = preset;
  if (preset === "full") {
    lines.value.forEach(l => { l.included = true; l.mode = "qty"; l.qty = l.original_qty; l.pct = 100; l.amount = effectiveAmount(l); });
  } else if (preset === "outstanding") {
    lines.value.forEach(l => { l.included = true; l.mode = "qty"; l.qty = l.original_qty; l.pct = 100; l.amount = effectiveAmount(l); });
    const outstanding = totalOutstanding.value;
    let running = 0;
    for (const l of lines.value) {
      const ea = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100;
      if (running + ea <= outstanding) {
        running += ea; l.amount = ea;
      } else {
        const rem = Math.round((outstanding - running) * 100) / 100;
        if (rem <= 0) { l.included = false; l.amount = 0; }
        else { l.mode = "amount"; l.custom_amount = rem; l.amount = rem; running = outstanding; }
        // exclude the rest
        const idx = lines.value.indexOf(l);
        lines.value.slice(idx + 1).forEach(r => { r.included = false; r.amount = 0; });
        break;
      }
    }
  } else if (preset === "selective") {
    lines.value.forEach(l => { l.included = false; l.amount = 0; });
  }
}
watch(lines, () => {
  if (!selectedBillDocs.value.length) return;
  const allFull = lines.value.every(l => l.included && l.mode === "qty" && l.qty === l.original_qty);
  if (!allFull && (debitPreset.value === "full" || debitPreset.value === "outstanding")) {
    debitPreset.value = "custom";
  }
}, { deep: true });

const subtotal       = computed(() => lines.value.reduce((s, l) => s + (l.included ? flt(l.amount) : 0), 0));
const billTotal      = computed(() => lines.value.reduce((s, l) => s + flt(l.original_amount), 0));
const debitPct       = computed(() => billTotal.value ? Math.min(100, Math.round(subtotal.value / billTotal.value * 100)) : 0);
const totalOutstanding = computed(() => selectedBillDocs.value.reduce((s, d) => s + Math.abs(flt(d.outstanding_amount || 0)), 0));
const totalGrand     = computed(() => selectedBillDocs.value.reduce((s, d) => s + Math.abs(flt(d.grand_total || 0)), 0));
const remaining      = computed(() => totalOutstanding.value - subtotal.value);
const includedCt     = computed(() => lines.value.filter(l => l.included).length);
const groupedLines   = computed(() => {
  const map = new Map();
  for (const l of lines.value) {
    const k = l.bill_name || "";
    if (!map.has(k)) map.set(k, []);
    map.get(k).push(l);
  }
  return [...map.entries()].map(([billName, items]) => ({ billName, items }));
});

const timelineSteps = computed(() => {
  const d = viewDoc.value;
  if (!d) return [];
  if (d.docstatus === 2) {
    return [
      { key: "draft", label: "Draft", done: true },
      { key: "issued", label: "Issued", done: true },
      { key: "cancelled", label: "Cancelled", danger: true, current: true },
    ];
  }
  const fullyApplied = d.docstatus === 1 && viewBalance.value <= 0;
  return [
    { key: "draft",   label: "Draft",   done: true },
    { key: "issued",  label: "Issued",  done: d.docstatus >= 1, current: d.docstatus === 1 && !fullyApplied },
    { key: "closed",  label: "Closed",  done: fullyApplied, current: fullyApplied },
  ];
});

// ── Create / Edit ─────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { supplier: "", posting_date: todayStr(), return_against: "", reason: "Vendor Overcharge", cost_center: "", remark: "" });
  lines.value = [blankLine()];
  selectedBillDocs.value = [];
  billSearchVal.value = "";
  fetchVendors(""); fetchItems(""); fetchCostCenters(); bills.value = [];
  drawerOpen.value = true;
}
async function openEdit(d) {
  editingName.value = d.name;
  _suppressVendorSelect.value = true;
  Object.assign(form, { supplier: d.supplier || "", posting_date: d.posting_date || todayStr(), return_against: d.return_against || "", reason: "Vendor Overcharge", cost_center: d.cost_center || "", remark: d.remark ||"" });
  _suppressVendorSelect.value = false;
  lines.value = [blankLine()];
  selectedBillDocs.value = [];
  billSearchVal.value = "";
  fetchVendors(""); fetchItems(""); fetchCostCenters();
  if (d.supplier) fetchBills("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Purchase Invoice", d.name);
    const billRef = d.return_against || "";
    if (doc?.cost_center) form.cost_center = doc.cost_center;
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => {
        const qty = Math.abs(i.qty || 0);
        const rate = Math.abs(i.rate || 0);
        const origAmt = Math.abs(i.amount || 0) || Math.round(qty * rate * 100) / 100;
        return {
          id: _id++, item_code: i.item_code || "", item_name: i.item_name || i.item_code || "",
          description: i.description || "",
          original_qty: qty, original_amount: origAmt,
          qty, rate,
          bill_name: billRef,
          included: true, mode: "qty",
          custom_amount: origAmt, pct: 100,
          amount: origAmt,
        };
      });
    }
    if (doc?.remark) {
        form.remark = doc.remark;
    }
    if (billRef) {
      try {
        const billDoc = await apiGet("Purchase Invoice", billRef);
        selectedBillDocs.value = [billDoc];
      } catch {}
    }
  } catch {}
}
async function openView(d) {
  viewDoc.value = d;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  viewApplications.value = [];
  viewBalance.value = 0;
  try {
    const doc = await apiGet("Purchase Invoice", d.name);
    viewItems.value = doc?.items || [];
    if (d.docstatus === 1) {
      const [bal, apps] = await Promise.all([
        apiGET("zoho_books_clone.api.docs.get_debit_note_balance", { debit_note_name: d.name }).catch(() => null),
        apiGET("zoho_books_clone.api.docs.get_debit_note_applications", { debit_note_name: d.name }).catch(() => []),
      ]);
      if (bal) viewBalance.value = flt(bal.balance);
      viewApplications.value = apps || [];
    }
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
    const r = await apiList("Item", { fields: ["name", "item_name", "standard_rate", "stock_uom"], filters: f, limit: 30, order: "item_name asc" });
    items.value = r.map(x => ({ ...x, label: x.item_name || x.name, value: x.name, rate: x.standard_rate || 0 }));
  } catch { items.value = []; }
}
async function fetchBills(q = "") {
  try {
    const f = [["is_return", "=", 0], ["docstatus", "=", 1]];
    if (form.supplier) f.push(["supplier", "=", form.supplier]);
    if (q) f.push(["name", "like", "%" + q + "%"]);
    const r = await apiList("Purchase Invoice", { fields: ["name", "supplier", "supplier_name", "outstanding_amount"], filters: f, limit: 30 });
    bills.value = r.map(x => ({ ...x, label: x.name + (x.supplier_name ? ` · ${x.supplier_name}` : ""), value: x.name }));
  } catch { bills.value = []; }
}
function onVendorSelect(opt) {
  if (_suppressVendorSelect.value) return;
  clearBills();
  fetchBills("");
}
async function addBill(opt) {
  const billName = opt?.value ?? opt;
  if (!billName || selectedBillDocs.value.find(d => d.name === billName)) return;
  billLoading.value = true;
  try {
    const doc = await apiGet("Purchase Invoice", billName);
    selectedBillDocs.value.push(doc);
    if (doc?.items?.length) {
      const newLines = doc.items.map(i => {
        const qty = Math.abs(i.qty || 0);
        const rate = Math.abs(i.rate || 0);
        const origAmt = Math.abs(i.amount || 0) || Math.round(qty * rate * 100) / 100;
        return {
          id: _id++,
          bill_name: doc.name,
          item_code: i.item_code || "",
          item_name: i.item_name || i.item_code || "",
          description: i.description || i.item_name || "",
          original_qty: qty,
          original_amount: origAmt,
          qty,
          rate,
          included: true,
          mode: "qty",
          custom_amount: origAmt,
          pct: 100,
          amount: Math.round(qty * rate * 100) / 100,
        };
      });
      // Remove the blank placeholder line if it's the only line
      if (lines.value.length === 1 && !lines.value[0].item_code) lines.value = [];
      lines.value.push(...newLines);
    }
    if (!form.supplier && doc?.supplier) form.supplier = doc.supplier;
    debitPreset.value = "full";
    billSearchVal.value = "";
  } catch {}
  billLoading.value = false;
}
function removeBillDoc(name) {
  selectedBillDocs.value = selectedBillDocs.value.filter(d => d.name !== name);
  lines.value = lines.value.filter(l => l.bill_name !== name);
  if (!selectedBillDocs.value.length) { lines.value = [blankLine()]; debitPreset.value = "full"; }
}
function clearBills() {
  selectedBillDocs.value = [];
  billSearchVal.value = "";
  lines.value = [blankLine()];
  debitPreset.value = "full";
  form.return_against = "";
}
function onItemSelect(line, opt) { line.item_code = opt?.value ?? opt; if (opt?.rate) { line.rate = Number(opt.rate) || 0; calcLine(line); } }
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }

async function saveDN(submit) {
  if (!form.supplier) return toast.error("Vendor is required");
  const activeLines = lines.value.filter(l => l.included && (l.item_code || l.item_name) && effectiveAmount(l) > 0);
  if (!activeLines.length) return toast.error("At least one included item with amount > 0 is required");
  if (form.remark.length > 500) return toast.error("Internal note cannot exceed 500 characters");
  // Set return_against to first selected bill
  form.return_against = selectedBillDocs.value[0]?.name || "";
  drawerSaving.value = true;
  try {
    if (!editingName.value) {
      const itemsPayload = activeLines.map(l => ({
        item_code: l.item_code || l.item_name,
        item_name: l.item_name || l.item_code,
        description: l.description,
        qty: l.mode === "qty" ? flt(l.qty) : 1,
        rate: l.mode === "qty" ? flt(l.rate) : effectiveAmount(l),
      }));
      const r = await apiPOST("zoho_books_clone.api.docs.create_debit_note", {
        vendor: form.supplier,
        against_bill: form.return_against || "",
        date: form.posting_date,
        reason: form.reason,
        cost_center: form.cost_center || "",
        remark: form.remark || "",
        items: JSON.stringify(itemsPayload),
        draft_only: submit ? 0 : 1,
      });
      toast.success(`Debit Note ${r?.debit_note || ""} ${submit ? "submitted" : "saved as draft"}`);
    } else {
      const company = await resolveCompany();
      const doc = {
        doctype: "Purchase Invoice", name: editingName.value,
        company, supplier: form.supplier,
        posting_date: form.posting_date,
        is_return: 1, return_against: form.return_against || null,
        cost_center: form.cost_center || "",
        remark: form.remark || "",
        items: activeLines.map(l => ({
          doctype: "Purchase Invoice Item",
          item_code: l.item_code,
          description: l.description || l.item_code,
          qty: l.mode === "qty" ? -Math.abs(flt(l.qty)) : -1,
          rate: l.mode === "qty" ? flt(l.rate) : effectiveAmount(l),
          amount: -Math.abs(effectiveAmount(l)),
        })),
      };
      const saved = await apiSave(doc);
      if (submit) await apiSubmit("Purchase Invoice", saved.name);
      toast.success(`Debit Note ${saved?.name || ""} ${submit ? "submitted" : "saved"}`);
    }
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save debit note"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailDN(d) {
  // Reuse bill email defaults — supplier-side, same shape
  await openEmail({
    doctype: "Purchase Invoice", name: d.name, docLabel: `Debit Note ${d.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_bill_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_bill_email",
    paramKey: "bill_name",
  });
}
async function applyDN(d) {
  // Load open bills for the same vendor
  try {
    const r = await apiList("Purchase Invoice", {
      fields: ["name", "outstanding_amount", "grand_total"],
      filters: [["is_return", "=", 0], ["docstatus", "=", 1], ["supplier", "=", d.supplier], ["outstanding_amount", ">", 0]],
      limit: 50, order: "posting_date desc",
    });
    if (!r.length) { toast.info("No open bills for this vendor"); return; }
    const balance = balanceFor(d.name) || viewBalance.value || Math.abs(flt(d.grand_total));
    const returnAgainst = d.return_against || "";
    const matchedBill = r.find(b => b.name === returnAgainst);
    const defaultBill = matchedBill?.name || r[0]?.name || "";
    const defaultOutstanding = flt(matchedBill?.outstanding_amount ?? r[0]?.outstanding_amount ?? 0);
    Object.assign(applyModal, {
      open: true, saving: false, dnName: d.name, balance,
      bill: defaultBill,
      amount: Math.min(balance, defaultOutstanding),
      openBills: r,
    });
  } catch (e) { toast.error(e.message || "Failed to load bills"); }
}
async function submitApply() {
  if (!applyModal.bill || applyModal.amount <= 0) return;
  applyModal.saving = true;
  try {
    await apiPOST("zoho_books_clone.api.docs.apply_debit_note_to_bill", {
      debit_note: applyModal.dnName,
      bill: applyModal.bill,
      amount: applyModal.amount,
    });
    toast.success(`Applied ${fmtCur(applyModal.amount)} to ${applyModal.bill}`);
    applyModal.open = false;
    await load();
    if (viewDoc.value?.name === applyModal.dnName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Apply failed"); }
  applyModal.saving = false;
}
async function submitDraftDN(d) {
  if (!await confirm({ title: "Submit Debit Note", body: `Submit ${d.name}? GL entries will be posted and the note cannot be edited.`, okLabel: "Submit" })) return;
  try {
    await apiSubmit("Purchase Invoice", d.name);
    toast.success(`${d.name} submitted`);
    viewOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Submit failed"); }
}
async function cancelDN(d) {
  if (!await confirm({ title: "Cancel Debit Note", body: `Cancel ${d.name}? Any applications must be cancelled separately.`, okLabel: "Cancel DN" })) return;
  try {
    await apiPOST("zoho_books_clone.api.docs.cancel_doc", { doctype: "Purchase Invoice", name: d.name });
    toast.success("Debit Note cancelled");
    await load(); if (viewDoc.value?.name === d.name) await openView(d);
  } catch (e) { toast.error(e.message || "Cancel failed"); }
}
async function deleteDN(d) {
  if (!await confirm({ title: "Delete Debit Note", body: `Permanently delete ${d.name}? This cannot be undone.`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Purchase Invoice", d.name);
    toast.success("Debit Note deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk ──────────────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(d => selected.value.has(d.name) && d.docstatus === 0);
  if (!drafts.length) { toast.info("No draft debit notes selected"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft debit note(s)?`, okLabel: "Delete" })) return;
  for (const d of drafts) { try { await apiDelete("Purchase Invoice", d.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length} draft(s)`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(d => selected.value.has(d.name) && d.docstatus === 1);
  if (!subs.length) { toast.info("No submitted debit notes selected"); return; }
  let sent = 0;
  for (const d of subs) {
    const ok = await openEmail({
      doctype: "Purchase Invoice", name: d.name, docLabel: `Debit Note ${d.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_bill_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_bill_email",
      paramKey: "bill_name",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} debit note(s)`);
}

function exportCSV() {
  const rows = selected.value.size
    ? sorted.value.filter(d => selected.value.has(d.name))
    : sorted.value;
  if (!rows.length) return;
  const head = ["Debit Note","Vendor","Date","Against Bill","Status","Amount","Available Balance"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const d of rows) {
    out.push([d.name, d.supplier_name || d.supplier, d.posting_date, d.return_against || "",
      statusLabel(d), Math.abs(flt(d.grand_total)).toFixed(2), balanceFor(d.name).toFixed(2)
    ].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `debit_notes_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} note(s)`);
}

onMounted(load);
</script>

<style scoped>
/* ── Drawer slide-in transition ── */
.dn-drawer {
  position: fixed;
  top: 0; right: -625px; bottom: 0;
  width: 625px; max-width: 96vw;
  background: #fff;
  box-shadow: -8px 0 24px rgba(0,0,0,.08);
  z-index: 9001;
  display: flex; flex-direction: column;
  transition: right .22s ease;
}
.dn-drawer.open { right: 0; }
.dn-view-drawer { width: 625px; right: -625px; }
.dn-view-drawer.open { right: 0; }

/* ── Drawer add/edit body ── */
.dn-dbody .add-card-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #e8ecf0;
  cursor: pointer; user-select: none;
  border-radius: 10px 10px 0 0;
}
.dn-dbody .add-card-title {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; font-weight: 700; color: #1a1a2e;
}
.dn-dbody .add-card-title-icon {
  width: 20px; height: 20px;
  display: flex; align-items: center; justify-content: center;
  color: #ea580c; flex-shrink: 0;
}
.dn-dbody .add-card-chevron {
  color: #9ca3af; transition: transform .2s; display: inline-flex;
}
.dn-dbody .add-card-chevron.collapsed { transform: rotate(-90deg); }
.dn-dbody .add-card-body { padding: 16px; }
.dn-dbody .add-card-body.collapsed { display: none; }

/* Line count badge in items card header */
.dn-lines-badge {
  font-size: 11.5px; font-weight: 600;
  color: #374151; background: #f3f4f6;
  border: 1px solid #e5e7eb;
  border-radius: 5px; padding: 2px 8px;
}

/* ── Drawer header icon ── */
.dn-dheader-left { display: flex; align-items: flex-start; gap: 12px; }
.dn-dheader-ico {
  width: 38px; height: 38px; border-radius: 10px;
  background: #fff; border: 1px solid rgba(234,88,12,.22);
  display: inline-flex; align-items: center; justify-content: center;
  color: #ea580c; flex-shrink: 0;
}
.dn-dheader-ico.edit { color: #ca8a04; border-color: rgba(202,138,4,.25); }

/* ── Field helpers ── */
.dn-field { display: flex; flex-direction: column; gap: 4px; }

/* ── Items line table ── */
.dn-items-table {
  display: flex; flex-direction: column;
  border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;
}
.dn-items-head {
  display: grid;
  grid-template-columns: 2fr 2fr 80px 100px 100px 32px;
  gap: 8px; background: #f9fafb; padding: 8px 12px;
  font-size: 11.5px; font-weight: 600; color: #374151;
}
.dn-items-row {
  display: grid;
  grid-template-columns: 2fr 2fr 80px 100px 100px 32px;
  gap: 8px; padding: 8px 12px;
  border-top: 1px solid #f3f4f6; align-items: center;
}
.dn-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 8px 0; }
.dn-total-row.grand { font-weight: 700; font-size: 15px; color: #111827; border-top: 2px solid #e5e7eb; padding-top: 10px; }

/* ── View panel header ── */
.dn-view-head-body { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin-top: 4px; }
.dn-view-head-left { display: flex; flex-direction: column; gap: 2px; }
.dn-view-head-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; flex-shrink: 0; }
.dn-view-amount { font-size: 22px; font-weight: 800; color: #1a1a2e; line-height: 1; }
.dn-vclose { align-self: flex-end; margin-left: auto; margin-bottom: 4px; }

/* ── Meta/detail 2-col grid ── */
.dn-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.dn-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }

/* ── View items table ── */
.dn-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.dn-view-items-head {
  display: grid; grid-template-columns: 2.5fr 70px 90px 100px;
  gap: 8px; background: #f9fafb; padding: 8px 12px;
  font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;
}
.dn-view-items-row {
  display: grid; grid-template-columns: 2.5fr 70px 90px 100px;
  gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6;
  align-items: center; font-size: 12.5px;
}

/* ── Applications grid ── */
.dn-app-head {
  display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px; background: #f9fafb; padding: 8px 12px;
  font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;
  border-radius: 6px 6px 0 0; border: 1px solid #e5e7eb; border-bottom: none;
}
.dn-app-row {
  display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6;
  border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb;
  align-items: center; font-size: 12.5px;
}
.dn-app-row:last-child { border-bottom: 1px solid #e5e7eb; border-radius: 0 0 6px 6px; }

/* ── Row action button variants ── */
.dn-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.dn-act-apply { background: #fff7ed; border-color: #ea580c; color: #ea580c; }
.dn-act-apply:hover { background: #ffedd5; color: #c2410c; }
.dn-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.dn-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }

/* ── Apply-to-Bill dialog ── */
.dn-apply-dialog {
  position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 480px; max-width: 96vw; background: #fff;
  border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.2);
  z-index: 9100; display: flex; flex-direction: column; overflow: hidden;
}

/* ── Timeline stepper wrapper ── */
.dn-stepper-wrap { background: #fff; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; }

/* ── Bill selection card ── */
.dn-bill-ph {
  display: flex; align-items: center; gap: 8px;
  color: #9ca3af; font-size: 13px; font-style: italic;
  padding: 10px 4px;
}
.dn-no-bills-note {
  margin-top: 8px; font-size: 12px; color: #9ca3af; font-style: italic;
}
.dn-bill-loaded-badge {
  font-size: 11px; font-weight: 700;
  background: #fff7ed; color: #ea580c;
  border: 1px solid #fed7aa;
  border-radius: 5px; padding: 2px 8px;
}

/* ── Bill preview card ── */
.dn-bill-preview {
  background: #fff8f5;
  border: 1px solid #fed7aa;
  border-radius: 8px;
  padding: 14px 16px;
}
.dn-bill-preview-hdr {
  display: flex; align-items: flex-start; justify-content: space-between; gap: 12px;
}
.dn-bill-num {
  font-size: 14px; font-weight: 800; color: #7c2d12; letter-spacing: -0.2px;
}
.dn-bill-meta {
  font-size: 12px; color: #92400e; margin-top: 2px;
}
.dn-change-bill-btn {
  border: 1px solid #fed7aa; background: #fff;
  color: #ea580c; border-radius: 6px;
  padding: 4px 10px; font-size: 12px; font-weight: 600;
  cursor: pointer; white-space: nowrap; font-family: inherit;
  transition: all .15s; flex-shrink: 0;
}
.dn-change-bill-btn:hover { background: #fff7ed; border-color: #ea580c; }
.dn-bill-preview-divider { height: 1px; background: #fed7aa; margin: 12px 0; }
.dn-bill-amounts {
  display: flex; align-items: center; gap: 0; flex-wrap: wrap;
}
.dn-bill-amount-item {
  display: flex; flex-direction: column; gap: 2px; flex: 1;
}
.dn-bill-amount-sep {
  color: #fbbf24; font-size: 16px; padding: 0 8px; align-self: center;
}
.dn-bill-amount-lbl {
  font-size: 10.5px; color: #92400e; text-transform: uppercase; letter-spacing: .05em; font-weight: 600;
}
.dn-bill-amount-val {
  font-size: 14px; font-weight: 700; color: #7c2d12;
}
.dn-bill-amount-val.outstanding { color: #dc2626; }

/* ── Items placeholder (no bill) ── */
.dn-items-ph {
  display: flex; align-items: center; justify-content: center; gap: 8px;
  color: #9ca3af; font-size: 13px; font-style: italic;
  padding: 28px 16px;
}

/* ── Bill-driven items table (7 cols, legacy) ── */
.dn-items-head-bill {
  grid-template-columns: 2fr 2fr 70px 80px 90px 100px 32px !important;
}
.dn-items-row-bill {
  grid-template-columns: 2fr 2fr 70px 80px 90px 100px 32px !important;
}
.dn-item-name-cell { display: flex; align-items: center; padding: 4px 0; }
.dn-item-name { font-size: 13px; font-weight: 500; color: #374151; }
.dn-orig-qty {
  padding: 8px 0; font-size: 12px;
  color: #9ca3af; font-variant-numeric: tabular-nums;
}
.dn-rate-cell {
  padding: 8px 0; color: #6b7280;
}

/* ── Preset strip ── */
.dn-preset-strip {
  display: flex; align-items: center; gap: 6px;
  margin-top: 14px; padding-top: 12px;
  border-top: 1px dashed #fed7aa;
  flex-wrap: wrap;
}
.dn-preset-lbl { font-size: 11px; font-weight: 600; color: #9a3412; text-transform: uppercase; letter-spacing: .04em; margin-right: 2px; }
.dn-preset-btn {
  font: inherit; font-size: 12px; font-weight: 600;
  padding: 4px 12px; border-radius: 20px; cursor: pointer;
  border: 1.5px solid #e5e7eb; background: #f9fafb; color: #374151;
  transition: all .15s;
}
.dn-preset-btn:hover:not(:disabled) { border-color: #ea580c; color: #ea580c; background: #fff7ed; }
.dn-preset-btn.active { background: #ea580c; color: #fff; border-color: #ea580c; }
.dn-preset-btn:disabled { opacity: .4; cursor: not-allowed; }
.dn-preset-custom-badge {
  font-size: 11px; font-weight: 700; padding: 3px 10px; border-radius: 20px;
  background: #fef3c7; color: #92400e; border: 1px solid #fcd34d;
}

/* ── Deep items toolbar ── */
.dn-items-toolbar {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 16px; background: #f9fafb;
  border-bottom: 1px solid #e5e7eb; font-size: 12.5px;
}
.dn-select-all-label { display: flex; align-items: center; gap: 6px; cursor: pointer; color: #374151; font-weight: 500; }
.dn-toolbar-sep { width: 1px; height: 14px; background: #e5e7eb; }
.dn-toolbar-hint { color: #9ca3af; font-size: 12px; }

/* ── Deep items table (8 cols) ── */
.dn-items-head-deep {
  grid-template-columns: 28px 2fr 70px 100px 150px 90px 110px 28px !important;
}
.dn-items-row-deep {
  grid-template-columns: 28px 2fr 70px 100px 150px 90px 110px 28px !important;
  padding: 6px 12px;
}
.dn-items-row-deep-wrap {
  border-top: 1px solid #f0f2f5;
}
.dn-items-row-deep-wrap:first-child { border-top: none; }
.dn-row-excluded { opacity: 0.45; }

/* Item name cell */
.dn-item-deep-name { display: flex; flex-direction: column; justify-content: center; padding: 2px 0; }
.dn-item-orig-amt { font-size: 11px; color: #9ca3af; margin-top: 1px; }

/* Mode pill group */
.dn-mode-cell { display: flex; align-items: center; }
.dn-mode-pill-group { display: flex; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.dn-mode-pill {
  font: inherit; font-size: 11px; font-weight: 600; padding: 3px 7px;
  border: none; background: #f9fafb; color: #6b7280; cursor: pointer;
  border-right: 1px solid #e5e7eb; transition: all .12s;
}
.dn-mode-pill:last-child { border-right: none; }
.dn-mode-pill:hover:not(:disabled) { background: #f3f4f6; color: #374151; }
.dn-mode-pill.active { background: #ea580c; color: #fff; }
.dn-mode-pill:disabled { cursor: not-allowed; }

/* Debit input cell */
.dn-debit-input-cell { display: flex; flex-direction: column; justify-content: center; gap: 2px; }
.dn-input-wrap { display: flex; align-items: center; gap: 4px; }
.dn-input-pfx { font-size: 12px; color: #6b7280; font-weight: 600; }
.dn-input-sfx { font-size: 11px; color: #9ca3af; }
.dn-deep-input {
  width: 72px; border: 1px solid #e2e8f0; border-radius: 5px;
  padding: 4px 6px; font-size: 12.5px; text-align: right;
  outline: none; font-family: inherit;
}
.dn-deep-input:focus { border-color: #ea580c; box-shadow: 0 0 0 2px rgba(234,88,12,.08); }
.dn-deep-input:disabled { background: #f9fafb; color: #9ca3af; }
.dn-pct-hint { font-size: 11px; color: #6b7280; padding-left: 2px; }

/* Debit amount col */
.dn-deep-amt { font-weight: 600; color: #7c2d12; padding: 8px 0; }
.dn-amt-excluded { color: #d1d5db !important; font-weight: 400; font-style: italic; }

/* Per-row progress bar */
.dn-debit-progress-wrap {
  height: 3px; background: #fee2e2; margin: 0 12px 4px;
  border-radius: 2px; overflow: hidden;
}
.dn-debit-progress-bar {
  height: 100%; background: #ea580c; border-radius: 2px;
  transition: width .2s;
}

/* Row checkbox */
.dn-row-check { display: flex; align-items: center; justify-content: center; }

/* ── Summary panel ── */
.dn-summary-panel {
  margin: 0; padding: 12px 16px;
  border-top: 2px solid #e5e7eb;
  background: #fafafa;
  display: flex; flex-direction: column; gap: 6px;
}
.dn-summary-row {
  display: grid; grid-template-columns: 90px 1fr 120px 40px;
  align-items: center; gap: 10px; font-size: 12.5px;
}
.dn-summary-lbl { font-weight: 600; color: #6b7280; font-size: 11.5px; text-transform: uppercase; letter-spacing: .03em; }
.dn-summary-bar-wrap {
  height: 6px; background: #f3f4f6; border-radius: 3px; overflow: hidden; position: relative;
}
.dn-summary-bar {
  position: absolute; top: 0; left: 0; height: 100%; border-radius: 3px; transition: width .3s;
}
.dn-summary-val { text-align: right; font-variant-numeric: tabular-nums; font-weight: 600; color: #111827; }
.dn-summary-pct { text-align: right; font-size: 11px; color: #9ca3af; }
.dn-summary-divider { height: 1px; background: #e5e7eb; margin: 2px 0; }

/* ── Multi-bill list ── */
.dn-bill-list {
  display: flex; flex-direction: column; gap: 0;
  border: 1px solid #fed7aa; border-radius: 8px; overflow: hidden;
  margin-top: 10px;
}
.dn-bill-mini-card {
  padding: 10px 14px; background: #fff8f5;
  border-bottom: 1px solid #fed7aa;
}
.dn-bill-mini-card:last-child { border-bottom: none; }
.dn-bill-mini-hdr {
  display: flex; align-items: center; justify-content: space-between; gap: 8px;
  margin-bottom: 8px;
}
.dn-remove-bill-btn {
  border: 1px solid #fed7aa; background: #fff; color: #ea580c;
  border-radius: 5px; padding: 2px 8px; font-size: 13px; font-weight: 700;
  cursor: pointer; line-height: 1; font-family: inherit; flex-shrink: 0;
  transition: all .15s;
}
.dn-remove-bill-btn:hover { background: #fff7ed; border-color: #ea580c; }
.dn-bill-mini-amounts {
  display: flex; align-items: center; gap: 0; flex-wrap: wrap;
}

/* ── Combined totals strip ── */
.dn-bill-combined {
  display: flex; align-items: center; gap: 0; flex-wrap: wrap;
  padding: 8px 14px;
  background: linear-gradient(90deg, #fff7ed, #fef9f5);
  border-top: 1px dashed #fed7aa;
}
.dn-bill-combined-lbl {
  font-size: 11px; font-weight: 800; color: #9a3412;
  text-transform: uppercase; letter-spacing: .05em;
  margin-right: 12px; flex-shrink: 0;
}

/* ── Bill group header row in items table ── */
.dn-bill-group-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 5px 12px; background: #fff7ed;
  border-top: 1px solid #fed7aa;
  border-bottom: 1px solid #fde68a;
}
.dn-bill-group-header:first-child { border-top: none; }
.dn-bill-group-name {
  font-size: 11.5px; font-weight: 700; color: #9a3412;
  text-transform: uppercase; letter-spacing: .04em;
}
.dn-bill-group-total { font-size: 11.5px; font-weight: 600; color: #7c2d12; }
.exp-field-hint { font-size:11.5px;color:#9ca3af;margin-top:4px;text-align:right; }
.exp-field-hint-err { color:#dc2626;font-weight:600; }
</style>