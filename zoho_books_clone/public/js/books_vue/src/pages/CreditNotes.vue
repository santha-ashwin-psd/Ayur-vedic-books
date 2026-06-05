<template>
  <div class="list-page">

    <!-- ── Toolbar ── -->
    <div class="sales-toolbar">
      <div class="sales-search">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search credit notes, customers…" class="sales-search-input" />
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
          <span v-html="icon('plus',13)"></span> New Credit Note
        </button>
      </div>
    </div>

    <!-- ── KPI Cards ── -->
    <div class="bk-kpi-grid bk-kpi-grid-4">
      <div class="bk-kpi-card bk-kpi-accent clickable" @click="activeTab='all'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="12" y1="18" x2="12" y2="12"/><line x1="9" y1="15" x2="15" y2="15"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total Credit Notes</div><div class="bk-kpi-value">{{ list.length }}</div><div class="bk-kpi-trend" :class="cnTrends.total.up?'bk-trend-up':'bk-trend-down'">{{ cnTrends.total.up?'↑':'↓' }} {{ cnTrends.total.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-success clickable" @click="activeTab='issued'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dcfce7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#16a34a" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Issued</div><div class="bk-kpi-value bk-kpi-green">{{ counts.issued }}</div><div class="bk-kpi-trend" :class="cnTrends.issued.up?'bk-trend-up':'bk-trend-down'">{{ cnTrends.issued.up?'↑':'↓' }} {{ cnTrends.issued.pct }}% vs last month</div></div></div></div>
      <div class="bk-kpi-card"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#fee2e2"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="1.8"><rect x="1" y="4" width="22" height="16" rx="2"/><line x1="1" y1="10" x2="23" y2="10"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Open Balance</div><div class="bk-kpi-value bk-kpi-red" style="font-size:18px">{{ fmtCur(summary.openBalance) }}</div><div class="bk-kpi-trend bk-trend-neutral">unapplied credit</div></div></div></div>
      <div class="bk-kpi-card"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dcfce7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="1.8"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total Credit Value</div><div class="bk-kpi-value bk-kpi-green" style="font-size:18px">{{ fmtCur(summary.totalValue) }}</div><div class="bk-kpi-trend" :class="cnTrends.value.up?'bk-trend-up':'bk-trend-down'">{{ cnTrends.value.up?'↑':'↓' }} {{ cnTrends.value.pct }}% vs last month</div></div></div></div>
    </div>
    <div class="bk-stat-grid">
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month</div><div class="bk-stat-value">{{ cnThisMonth.count }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">This Month Value</div><div class="bk-stat-value bk-kpi-green" style="font-size:16px">{{ fmtCur(cnThisMonth.value) }}</div></div><div class="bk-stat-icon" style="background:#dcfce7;color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Draft</div><div class="bk-stat-value">{{ counts.draft }}</div></div><div class="bk-stat-icon" style="background:#f8fafc;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Avg Credit Value</div><div class="bk-stat-value" style="font-size:16px">{{ fmtCur(cnAvg) }}</div></div><div class="bk-stat-icon" style="background:#e5e7eb;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="20" x2="18" y2="10"/><line x1="12" y1="20" x2="12" y2="4"/><line x1="6" y1="20" x2="6" y2="14"/></svg></div></div></div>
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
            <th @click="sortBy('name')" class="sortable">CREDIT NOTE # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('customer_name')" class="sortable">CUSTOMER <span v-html="sortArrow('customer_name')"></span></th>
            <th @click="sortBy('posting_date')" class="sortable">DATE <span v-html="sortArrow('posting_date')"></span></th>
            <th>AGAINST INVOICE</th>
            <th>STATUS</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">AMOUNT <span v-html="sortArrow('grand_total')"></span></th>
            <th class="ta-r">AVAILABLE</th>
            <th style="width:120px;text-align:center">ACTIONS</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="9"><div class="shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="c in paged" :key="c.name" class="inv-row" :class="{selected:selected.has(c.name)}">
              <td><input type="checkbox" :checked="selected.has(c.name)" @change="toggle(c.name)" /></td>
              <td @click="openView(c)"><span class="inv-link">{{ c.name }}</span></td>
              <td @click="openView(c)">{{ c.customer_name || c.customer || '—' }}</td>
              <td @click="openView(c)" class="text-muted mono-sm">{{ fmtDate(c.posting_date) }}</td>
              <td @click="openView(c)" class="text-muted mono-sm">{{ c.return_against||'—' }}</td>
              <td @click="openView(c)"><span class="inv-status-badge" :class="statusCls(c)">{{ statusLabel(c) }}</span></td>
              <td @click="openView(c)" class="ta-r mono-sm" style="color:#7f1d1d">{{ fmtCur(Math.abs(c.grand_total||0)) }}</td>
              <td @click="openView(c)" class="ta-r mono-sm">
                <span v-if="c.docstatus===1" :class="balanceFor(c.name)>0?'text-danger':'text-success'">{{ fmtCur(balanceFor(c.name)) }}</span>
                <span v-else class="text-muted">—</span>
              </td>
              <td class="cn-act-cell">
                <button class="inv-act-btn" @click="openView(c)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="c.docstatus===0" class="inv-act-btn" @click="openEdit(c)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button v-if="c.docstatus===1 && balanceFor(c.name)>0" class="inv-act-btn cn-act-apply" @click="applyCN(c)" title="Apply to Invoice">↳</button>
                <button v-if="c.docstatus===0 || c.docstatus===2" class="inv-act-btn cn-act-del" @click="deleteCN(c)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="9" class="cn-empty">No credit notes match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && sorted.length" style="padding:12px 0 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ── Create / Edit Drawer ── -->
    <div v-if="drawerOpen" class="inv-drawer-bg" @click.self="drawerOpen=false"></div>
    <div class="cn-drawer" :class="{open:drawerOpen}">
      <div class="inv-dh">
        <div class="cn-dheader-left">
          <div class="cn-dheader-ico" :class="editingName?'edit':''">
            <span v-html="icon(editingName?'edit':'creditnote',18)"></span>
          </div>
          <div>
            <div class="inv-dh-title">{{ editingName ? 'Edit Credit Note' : 'New Credit Note' }}</div>
            <div class="inv-dh-sub">
              {{ editingName ? editingName : 'Issue a credit against a customer invoice' }}
            </div>
          </div>
        </div>
        <button class="inv-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="inv-dbody">
        <!-- Section: Customer & Date -->
        <div class="cn-section">
          <div class="cn-section-hdr"><span v-html="icon('user',13)"></span><span>Customer & Date</span></div>
          <div class="inv-fg inv-fg2">
            <div class="cn-field" style="grid-column:1/-1">
              <label class="inv-lbl">Customer <span class="inv-req">*</span></label>
              <SearchableSelect v-model="form.customer" :options="customers" placeholder="Select customer…"
                :createable="true" createDoctype="Customer"
                @search="fetchCustomers" @select="onCustomerSelect" />
            </div>
            <div class="cn-field">
              <label class="inv-lbl">Date <span class="inv-req">*</span></label>
              <input v-model="form.posting_date" type="date" class="inv-fi" />
            </div>
            <div class="cn-field">
              <label class="inv-lbl">Return Against Invoice</label>
              <SearchableSelect v-model="form.return_against" :options="invoices"
                placeholder="Select invoice (optional)…" @search="fetchInvoices" @select="onInvoiceSelect" />
            </div>
            <div class="cn-field" style="grid-column:1/-1">
              <label class="inv-lbl">Reason</label>
              <select v-model="form.reason" class="inv-fi">
                <option>Price Adjustment</option>
                <option>Goods Returned</option>
                <option>Damaged Goods</option>
                <option>Duplicate Invoice</option>
                <option>Other</option>
              </select>
            </div>
          </div>
        </div>

        <!-- Section: Items -->
        <div class="cn-section">
          <div class="cn-section-hdr">
            <span v-html="icon('box',13)"></span>
            <span>Items to Credit</span>
            <span style="margin-left:auto;font-size:11.5px;color:#6b7280;text-transform:none;letter-spacing:0">{{ lines.length }} line{{ lines.length!==1?'s':'' }}</span>
          </div>
          <div class="cn-items-table">
            <div class="cn-items-head">
              <div>Item</div><div>Description</div><div class="ta-r">Qty</div><div class="ta-r">Rate</div><div class="ta-r">Amount</div><div></div>
            </div>
            <div v-for="line in lines" :key="line.id" class="cn-items-row">
              <div><SearchableSelect v-model="line.item_code" :options="items"
                placeholder="Item…" :createable="true" createDoctype="Item"
                @search="fetchItems" @select="v=>onItemSelect(line,v)" /></div>
              <div><input v-model="line.description" class="inv-fi" placeholder="Description" /></div>
              <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="inv-fi ta-r" @input="calcLine(line)" /></div>
              <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="inv-fi ta-r" @input="calcLine(line)" /></div>
              <div class="ta-r mono-sm" style="padding:8px 0">{{ fmtCur(line.amount) }}</div>
              <div><button @click="removeLine(line.id)" class="inv-rm-line"><span v-html="icon('x',12)"></span></button></div>
            </div>
            <button class="inv-add-line-btn" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
          </div>
          <div class="cn-total-row grand"><span>Total Credit</span><span style="color:#7f1d1d">{{ fmtCur(subtotal) }}</span></div>
        </div>

        <!-- Section: Notes -->
        <div class="cn-section">
          <div class="cn-section-hdr"><span v-html="icon('mail',13)"></span><span>Notes</span></div>
          <textarea v-model="form.notes" rows="3" class="inv-fi" placeholder="Internal note (optional)…"></textarea>
        </div>
      </div>

      <div class="inv-dfooter">
        <button class="form-btn form-btn-outline" @click="drawerOpen=false" :disabled="drawerSaving">Cancel</button>
        <button class="form-btn form-btn-success" :disabled="drawerSaving" @click="saveCN(0)"><span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save Draft' }}</button>
        <button class="form-btn form-btn-primary" :disabled="drawerSaving" @click="saveCN(1)"><span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Submit' }}</button>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="inv-drawer-bg" @click.self="viewOpen=false"></div>
    <div class="cn-drawer cn-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="inv-view-header">
          <div class="cn-view-head-body">
            <div class="cn-view-head-left">
              <div class="inv-view-number">{{ viewDoc.name }}</div>
              <div class="inv-view-subtitle">
                <DocLink doctype="Customer" :name="viewDoc.customer" :mono-style="false">{{ viewDoc.customer_name||viewDoc.customer }}</DocLink>
              </div>
            </div>
          </div>
          <button class="inv-dclose cn-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
          
        </div>

        <div class="cn-stepper-wrap"><TimelineStepper :steps="timelineSteps" /></div>

        <div class="inv-view-tabs">
          <button class="inv-vtab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="inv-vtab" :class="{active:viewTab==='applied'}" @click="viewTab='applied'">
            Applied To<span v-if="viewApplications.length" class="inv-vtab-count">{{ viewApplications.length }}</span>
          </button>
        </div>

        <div class="inv-dbody">
          <template v-if="viewTab==='details'">
            <div class="cn-meta-grid">
              <div><div class="cn-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.posting_date) }}</div></div>
              <div><div class="cn-meta-lbl">Against Invoice</div><div><DocLink doctype="Sales Invoice" :name="viewDoc.return_against" /></div></div>
              <div><div class="cn-meta-lbl">Total Credit</div><div class="mono-sm" style="color:#7f1d1d;font-weight:600">{{ fmtCur(Math.abs(viewDoc.grand_total||0)) }}</div></div>
              <div><div class="cn-meta-lbl">Available Balance</div>
                <div class="mono-sm" :class="viewBalance>0?'text-danger':'text-success'">{{ fmtCur(viewBalance) }}</div>
              </div>
            </div>

            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="inv-sec-lbl">Line Items</div>
              <div class="cn-view-items">
                <div class="cn-view-items-head"><span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span></div>
                <div v-for="it in viewItems" :key="it.name" class="cn-view-items-row">
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
              <div class="cn-app-head"><span>Invoice</span><span>Date</span><span>Journal Entry</span><span class="ta-r">Amount Applied</span></div>
              <div v-for="a in viewApplications" :key="a.payment_entry+'_'+a.invoice" class="cn-app-row">
                <DocLink doctype="Sales Invoice" :name="a.invoice" />
                <span class="mono-sm">{{ fmtDate(a.date) }}</span>
                <DocLink doctype="Payment Entry" :name="a.payment_entry" />
                <span class="ta-r mono-sm" style="font-weight:600;color:#059669">{{ fmtCur(a.amount) }}</span>
              </div>
            </div>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
              No applications yet.
              <div v-if="viewBalance>0 && viewDoc.docstatus===1" style="margin-top:8px">
                <button class="form-btn form-btn-primary" @click="applyCN(viewDoc)" style="font-size:12px;padding:6px 12px">↳ Apply to Invoice</button>
              </div>
            </div>
          </template>
        </div>

        <div class="inv-dfooter">
          <button class="form-btn form-btn-outline" @click="viewOpen=false">Close</button>
          <button v-if="viewDoc.docstatus===0" class="form-btn form-btn-success" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button v-if="viewDoc.docstatus===1" class="form-btn form-btn-outline" @click="emailCN(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="form-btn form-btn-outline" @click="printCN(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="viewDoc.docstatus===1 && viewBalance>0" class="form-btn form-btn-primary" @click="applyCN(viewDoc)">↳ Apply to Invoice</button>
          <button v-if="viewDoc.docstatus===1 && viewBalance>0" class="form-btn form-btn-outline" @click="refundCN(viewDoc)">↩ Refund</button>
          <button v-if="viewDoc.docstatus===1" class="form-btn form-btn-danger" @click="cancelCN(viewDoc)">Cancel</button>
          <button v-if="viewDoc.docstatus===0 || viewDoc.docstatus===2" class="form-btn form-btn-danger" @click="deleteCN(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Apply-to-Invoice modal ── -->
    <div v-if="applyModal.open" class="inv-drawer-bg" @click.self="applyModal.open=false" style="z-index:60"></div>
    <div v-if="applyModal.open" class="cn-apply-dialog">
      <div class="inv-dh" style="background:linear-gradient(135deg,#7f1d1d,#dc2626);height:auto;padding:14px 18px">
        <div class="inv-dh-title">Apply Credit Note — {{ applyModal.cnName }}</div>
        <button class="inv-dclose" @click="applyModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="inv-dbody">
        <div style="font-size:12.5px;color:#374151">Available Balance: <strong>{{ fmtCur(applyModal.balance) }}</strong></div>
        <div class="cn-field">
          <label class="inv-lbl">Target Invoice <span class="inv-req">*</span></label>
          <select v-model="applyModal.invoice" class="inv-fi">
            <option value="">— Select invoice —</option>
            <option v-for="i in applyModal.openInvoices" :key="i.name" :value="i.name">
              {{ i.name }} · {{ fmtCur(i.outstanding_amount) }} due
            </option>
          </select>
        </div>
        <div class="cn-field">
          <label class="inv-lbl">Amount to Apply <span class="inv-req">*</span></label>
          <input v-model.number="applyModal.amount" type="number" min="0.01" :max="applyModal.balance" step="0.01" class="inv-fi ta-r" />
        </div>
      </div>
      <div class="inv-dfooter">
        <button class="form-btn form-btn-outline" @click="applyModal.open=false" :disabled="applyModal.saving">Cancel</button>
        <button class="form-btn form-btn-primary" :disabled="applyModal.saving || !applyModal.invoice || applyModal.amount<=0" @click="submitApply">
          {{ applyModal.saving ? 'Applying…' : `Apply ${fmtCur(applyModal.amount)}` }}
        </button>
      </div>
    </div>

    <!-- ── Refund modal ── -->
    <div v-if="refundModal.open" class="inv-drawer-bg" @click.self="refundModal.open=false" style="z-index:60"></div>
    <div v-if="refundModal.open" class="cn-apply-dialog">
      <div class="inv-dh" style="background:linear-gradient(135deg,#78350f,#d97706);height:auto;padding:14px 18px">
        <div class="inv-dh-title">Refund Credit Note — {{ refundModal.cnName }}</div>
        <button class="inv-dclose" @click="refundModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="inv-dbody">
        <div style="font-size:12.5px;color:#374151">Available Balance: <strong>{{ fmtCur(refundModal.balance) }}</strong></div>
        <div class="inv-fg inv-fg2">
          <div class="cn-field">
            <label class="inv-lbl">Refund Amount <span class="inv-req">*</span></label>
            <input v-model.number="refundModal.amount" type="number" min="0.01" :max="refundModal.balance" step="0.01" class="inv-fi ta-r"/>
          </div>
          <div class="cn-field">
            <label class="inv-lbl">Mode</label>
            <select v-model="refundModal.mode" class="inv-fi">
              <option>Bank Transfer</option>
              <option>Cash</option>
              <option>Cheque</option>
              <option>UPI</option>
              <option>NEFT</option>
            </select>
          </div>
          <div class="cn-field" style="grid-column:1/-1">
            <label class="inv-lbl">Reference / Cheque #</label>
            <input v-model="refundModal.reference" class="inv-fi" placeholder="Optional reference" />
          </div>
        </div>
      </div>
      <div class="inv-dfooter">
        <button class="form-btn form-btn-outline" @click="refundModal.open=false" :disabled="refundModal.saving">Cancel</button>
        <button class="form-btn form-btn-outline" :disabled="refundModal.saving || refundModal.amount<=0" @click="submitRefund">
          {{ refundModal.saving ? 'Processing…' : `Refund ${fmtCur(refundModal.amount)}` }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiPOST, apiSubmit, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useDocStatus } from "../composables/useDocStatus.js";
import { useRoute } from "vue-router";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { useOpenFromQuery } from "../composables/useOpenFromQuery.js";
import { usePagination } from "../composables/usePagination.js";
import DocLink from "../components/DocLink.vue";
import Pagination from "../components/Pagination.vue";
import { useConfirm } from "../composables/useConfirm.js";
import { useLivePreview } from "../composables/useLivePreview.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import BulkActionBar from "../components/BulkActionBar.vue";
import TimelineStepper from "../components/TimelineStepper.vue";

const { toast } = useToast();
const route = useRoute();
const { confirm } = useConfirm();
const { printDoc } = useLivePreview();
function printCN(d) { printDoc(d, { title: "CREDIT NOTE", partyLabel: "Customer", partyField: "customer_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();
const { statusLabel, statusCls, statusBg } = useDocStatus({
  fallbackDraftLabel: "Draft",
  fallbackSubmittedLabel: "Issued",
  paidStatuses: ["return"], pendingStatuses: ["return"], completedStatuses: ["return"],
  outstandingField: "_unused", dueDateField: "_unused",
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
const customers = ref([]), items = ref([]), invoices = ref([]), lines = ref([]);
const sortCol = ref("posting_date"), sortDir = ref("desc");
const _balances = ref({});
function balanceFor(name) { return flt(_balances.value[name] || 0); }

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const form = reactive({ customer: "", posting_date: todayStr(), return_against: "", reason: "Price Adjustment", notes: "" });

const applyModal = reactive({ open: false, saving: false, cnName: "", balance: 0, invoice: "", amount: 0, openInvoices: [] });
const refundModal = reactive({ open: false, saving: false, cnName: "", balance: 0, amount: 0, mode: "Bank Transfer", reference: "" });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function fmtCur(v) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(Math.abs(flt(v))); }

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    list.value = await apiList("Sales Invoice", {
      fields: ["name", "customer", "customer_name", "posting_date", "grand_total", "return_against", "docstatus", "status"],
      filters: [["is_return", "=", 1], ["company", "=", co]],
      limit: 500,
      order: "posting_date desc",
    });
    // Frappe sometimes omits customer_name on return invoices — resolve missing ones
    const missingNames = [...new Set(list.value.filter(c => !c.customer_name && c.customer).map(c => c.customer))];
    if (missingNames.length) {
      const custRows = await apiList("Customer", {
        fields: ["name", "customer_name"],
        filters: [["name", "in", missingNames]],
        limit: missingNames.length,
      }).catch(() => []);
      const nameMap = Object.fromEntries(custRows.map(r => [r.name, r.customer_name || r.name]));
      list.value = list.value.map(c => c.customer_name ? c : { ...c, customer_name: nameMap[c.customer] || c.customer });
    }
    const submitted = list.value.filter(c => c.docstatus === 1);
    const balances = await Promise.all(submitted.map(c =>
      apiGET("zoho_books_clone.api.docs.get_credit_note_balance", { credit_note_name: c.name }).catch(() => null)
    ));
    const map = {};
    submitted.forEach((c, i) => { if (balances[i]) map[c.name] = balances[i].balance; });
    _balances.value = map;
  } catch (e) { toast.error(e.message || "Failed to load credit notes"); }
  finally { loading.value = false; }
}

const counts = computed(() => ({
  draft:     list.value.filter(c => c.docstatus === 0).length,
  issued:    list.value.filter(c => c.docstatus === 1).length,
  cancelled: list.value.filter(c => c.docstatus === 2).length,
}));
const summary = computed(() => ({
  totalValue:  list.value.filter(c => c.docstatus === 1).reduce((s, c) => s + Math.abs(flt(c.grand_total)), 0),
  openBalance: Object.values(_balances.value).reduce((s, v) => s + flt(v), 0),
}));
const _cnYM  = () => { const d=new Date(); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _cnLYM = () => { const d=new Date(); d.setMonth(d.getMonth()-1); return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`; };
const _cnTr  = (a,b) => { if(!b&&!a) return {pct:0,up:true}; if(!b) return {pct:100,up:true}; const p=Math.round((a-b)/b*100); return {pct:Math.abs(p),up:p>=0}; };
const cnThisMonth = computed(()=>{ const ym=_cnYM(); const r=list.value.filter(c=>(c.posting_date||'').startsWith(ym)); return {count:r.length,value:r.reduce((s,c)=>s+Math.abs(flt(c.grand_total)),0)}; });
const cnAvg = computed(()=>{ const p=list.value.filter(c=>c.grand_total); return p.length?p.reduce((s,c)=>s+Math.abs(flt(c.grand_total)),0)/p.length:0; });
const cnTrends = computed(()=>({
  total:  _cnTr(cnThisMonth.value.count, list.value.filter(c=>(c.posting_date||'').startsWith(_cnLYM())).length),
  issued: _cnTr(counts.value.issued, list.value.filter(c=>(c.posting_date||'').startsWith(_cnLYM())&&c.docstatus===1).length),
  value:  _cnTr(cnThisMonth.value.value, list.value.filter(c=>(c.posting_date||'').startsWith(_cnLYM())&&c.docstatus===1).reduce((s,c)=>s+Math.abs(flt(c.grand_total)),0)),
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value === "draft")     r = r.filter(c => c.docstatus === 0);
  if (activeTab.value === "issued")    r = r.filter(c => c.docstatus === 1);
  if (activeTab.value === "cancelled") r = r.filter(c => c.docstatus === 2);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.customer_name || x.customer || "").toLowerCase().includes(q)
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
function sortBy(col) { if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc"; else { sortCol.value = col; sortDir.value = "asc"; } }
function sortArrow(col) { if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value === "asc" ? "↑" : "↓"; }

const { page, pageSize, paged } = usePagination(sorted, { storageKey: "credit-notes" });

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(c => selected.value.has(c.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(c => c.name)) : new Set(); }

const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));

const timelineSteps = computed(() => {
  const c = viewDoc.value;
  if (!c) return [];
  if (c.docstatus === 2) {
    return [
      { key: "draft", label: "Draft", done: true },
      { key: "issued", label: "Issued", done: true },
      { key: "cancelled", label: "Cancelled", danger: true, current: true },
    ];
  }
  const fullyApplied = c.docstatus === 1 && viewBalance.value <= 0;
  return [
    { key: "draft",  label: "Draft",  done: true },
    { key: "issued", label: "Issued", done: c.docstatus >= 1, current: c.docstatus === 1 && !fullyApplied },
    { key: "closed", label: "Closed", done: fullyApplied, current: fullyApplied },
  ];
});

// ── Create / Edit ─────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { customer: "", posting_date: todayStr(), return_against: "", reason: "Price Adjustment", notes: "" });
  lines.value = [blankLine()];
  fetchCustomers(""); fetchItems(""); fetchInvoices("");
  drawerOpen.value = true;
}
async function openEdit(c) {
  editingName.value = c.name;
  Object.assign(form, { customer: c.customer || "", posting_date: c.posting_date || todayStr(), return_against: c.return_against || "", reason: "Price Adjustment", notes: "" });
  lines.value = [blankLine()];
  fetchCustomers(""); fetchItems(""); fetchInvoices("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Sales Invoice", c.name);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || "",
        qty: Math.abs(i.qty || 0), rate: Math.abs(i.rate || 0),
        amount: Math.abs(i.amount || 0),
      }));
    }
    if (doc?.remarks) form.notes = doc.remarks;
  } catch {}
}
async function openView(c) {
  viewDoc.value = c;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  viewApplications.value = [];
  viewBalance.value = 0;
  try {
    const doc = await apiGet("Sales Invoice", c.name);
    viewItems.value = doc?.items || [];
    if (c.docstatus === 1) {
      const [bal, apps] = await Promise.all([
        apiGET("zoho_books_clone.api.docs.get_credit_note_balance", { credit_note_name: c.name }).catch(() => null),
        apiGET("zoho_books_clone.api.docs.get_credit_note_applications", { credit_note_name: c.name }).catch(() => []),
      ]);
      if (bal) viewBalance.value = flt(bal.balance);
      viewApplications.value = apps || [];
    }
  } catch {}
  viewLoading.value = false;
}

async function fetchCustomers(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["customer_name", "like", "%" + q + "%"]);
    const r = await apiList("Customer", { fields: ["name", "customer_name"], filters: f, limit: 30, order: "customer_name asc" });
    customers.value = r.map(x => ({ ...x, label: x.customer_name || x.name, value: x.name }));
  } catch { customers.value = []; }
}
async function fetchItems(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["item_name", "like", "%" + q + "%"]);
    const r = await apiList("Item", { fields: ["name", "item_name", "standard_rate", "stock_uom"], filters: f, limit: 30, order: "item_name asc" });
    items.value = r.map(x => ({ ...x, label: x.item_name || x.name, value: x.name, rate: x.standard_rate || 0 }));
  } catch { items.value = []; }
}
async function fetchInvoices(q = "") {
  try {
    const f = [["is_return", "=", 0], ["docstatus", "=", 1]];
    if (form.customer) f.push(["customer", "=", form.customer]);
    if (q) f.push(["name", "like", "%" + q + "%"]);
    const r = await apiList("Sales Invoice", { fields: ["name", "customer", "customer_name", "outstanding_amount"], filters: f, limit: 30 });
    invoices.value = r.map(x => ({ ...x, label: x.name + (x.customer_name ? ` · ${x.customer_name}` : ""), value: x.name }));
  } catch { invoices.value = []; }
}
function onCustomerSelect(_opt) { form.return_against = ""; fetchInvoices(""); }
async function onInvoiceSelect(opt) {
  const invName = opt?.value ?? opt;
  if (!invName) return;
  try {
    const doc = await apiGet("Sales Invoice", invName);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || i.item_name || "",
        qty: Math.abs(i.qty || 1), rate: Math.abs(i.rate || 0),
        amount: Math.round(Math.abs(i.qty || 1) * Math.abs(i.rate || 0) * 100) / 100,
      }));
      toast.success(`Loaded ${doc.items.length} item(s) from ${invName}`);
    }
    if (!form.customer && doc?.customer) form.customer = doc.customer;
  } catch {}
}
function onItemSelect(line, opt) { line.item_code = opt?.value ?? opt; if (opt?.rate) { line.rate = Number(opt.rate) || 0; calcLine(line); } }
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }

async function saveCN(submit) {
  if (!form.customer) return toast.error("Customer is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  drawerSaving.value = true;
  try {
    if (!editingName.value) {
      const itemsPayload = lines.value
        .filter(l => l.item_code)
        .map(l => ({ item_code: l.item_code, item_name: l.item_code, description: l.description, qty: flt(l.qty), rate: flt(l.rate) }));
      const r = await apiPOST("zoho_books_clone.api.docs.create_credit_note", {
        customer: form.customer,
        against_invoice: form.return_against || "",
        date: form.posting_date,
        reason: form.reason,
        notes: form.notes || "",
        items: JSON.stringify(itemsPayload),
        taxes: "[]",
      });
      toast.success(`Credit Note ${r?.credit_note || ""} ${submit ? "submitted" : "issued"}`);
    } else {
      const company = await resolveCompany();
      const doc = {
        doctype: "Sales Invoice", name: editingName.value,
        company, customer: form.customer,
        posting_date: form.posting_date,
        is_return: 1, return_against: form.return_against || null,
        remarks: (form.reason || "") + (form.notes ? " — " + form.notes : ""),
        items: lines.value.filter(l => l.item_code).map(l => ({
          doctype: "Sales Invoice Item",
          item_code: l.item_code,
          description: l.description || l.item_code,
          qty: -Math.abs(flt(l.qty)),
          rate: flt(l.rate),
          amount: -Math.abs(flt(l.amount)),
        })),
      };
      const saved = await apiSave(doc);
      if (submit) await apiSubmit("Sales Invoice", saved.name);
      toast.success(`Credit Note ${saved?.name || ""} ${submit ? "submitted" : "saved"}`);
    }
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save credit note"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailCN(c) {
  await openEmail({
    doctype: "Sales Invoice", name: c.name, docLabel: `Credit Note ${c.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_credit_note_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_credit_note_email",
    paramKey: "credit_note_name",
  });
}
async function applyCN(c) {
  try {
    const r = await apiList("Sales Invoice", {
      fields: ["name", "outstanding_amount", "grand_total"],
      filters: [["is_return", "=", 0], ["docstatus", "=", 1], ["customer", "=", c.customer], ["outstanding_amount", ">", 0]],
      limit: 50, order: "posting_date desc",
    });
    if (!r.length) { toast.info("No open invoices for this customer"); return; }
    const balance = balanceFor(c.name) || viewBalance.value || Math.abs(flt(c.grand_total));
    Object.assign(applyModal, {
      open: true, saving: false, cnName: c.name, balance, invoice: "",
      amount: Math.min(balance, flt(r[0].outstanding_amount)), openInvoices: r,
    });
  } catch (e) { toast.error(e.message || "Failed to load invoices"); }
}
async function submitApply() {
  if (!applyModal.invoice || applyModal.amount <= 0) return;
  applyModal.saving = true;
  try {
    await apiPOST("zoho_books_clone.api.docs.apply_credit_note_to_invoice", {
      credit_note: applyModal.cnName,
      invoice: applyModal.invoice,
      amount: applyModal.amount,
    });
    toast.success(`Applied ${fmtCur(applyModal.amount)} to ${applyModal.invoice}`);
    applyModal.open = false;
    await load();
    if (viewDoc.value?.name === applyModal.cnName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Apply failed"); }
  applyModal.saving = false;
}
async function refundCN(c) {
  const balance = balanceFor(c.name) || viewBalance.value;
  if (balance <= 0) { toast.info("No available balance to refund"); return; }
  Object.assign(refundModal, { open: true, saving: false, cnName: c.name, balance, amount: balance, mode: "Bank Transfer", reference: "" });
}
async function submitRefund() {
  if (refundModal.amount <= 0) return;
  refundModal.saving = true;
  try {
    await apiPOST("zoho_books_clone.api.docs.refund_credit_note", {
      credit_note_name: refundModal.cnName,
      amount: refundModal.amount,
      refund_mode: refundModal.mode,
      reference_no: refundModal.reference,
    });
    toast.success(`Refunded ${fmtCur(refundModal.amount)} from ${refundModal.cnName}`);
    refundModal.open = false;
    await load();
    if (viewDoc.value?.name === refundModal.cnName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Refund failed"); }
  refundModal.saving = false;
}
async function cancelCN(c) {
  if (!await confirm({ title: "Cancel Credit Note", body: `Cancel ${c.name}? Any applications must be cancelled separately.`, okLabel: "Cancel CN" })) return;
  try {
    await apiPOST("zoho_books_clone.api.docs.cancel_doc", { doctype: "Sales Invoice", name: c.name });
    toast.success("Credit Note cancelled");
    await load(); if (viewDoc.value?.name === c.name) await openView(c);
  } catch (e) { toast.error(e.message || "Cancel failed"); }
}
async function deleteCN(c) {
  if (!await confirm({ title: "Delete Credit Note", body: `Permanently delete ${c.name}?`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Sales Invoice", c.name);
    toast.success("Credit Note deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk ──────────────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(c => selected.value.has(c.name) && c.docstatus === 0);
  if (!drafts.length) { toast.info("No draft credit notes selected"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft credit note(s)?`, okLabel: "Delete" })) return;
  for (const c of drafts) { try { await apiDelete("Sales Invoice", c.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length} draft(s)`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(c => selected.value.has(c.name) && c.docstatus === 1);
  if (!subs.length) { toast.info("No submitted credit notes selected"); return; }
  let sent = 0;
  for (const c of subs) {
    const ok = await openEmail({
      doctype: "Sales Invoice", name: c.name, docLabel: `Credit Note ${c.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_credit_note_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_credit_note_email",
      paramKey: "credit_note_name",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} credit note(s)`);
}

function exportCSV() {
  // Export selected rows if any are selected; otherwise export the full filtered view.
  const rows = selected.value.size
    ? sorted.value.filter(c => selected.value.has(c.name))
    : sorted.value;
  if (!rows.length) return;
  const head = ["Credit Note","Customer","Date","Against Invoice","Status","Amount","Available Balance"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const c of rows) {
    out.push([c.name, c.customer_name || c.customer, c.posting_date, c.return_against || "",
      statusLabel(c), Math.abs(flt(c.grand_total)).toFixed(2), balanceFor(c.name).toFixed(2)
    ].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `credit_notes_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} note(s)`);
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
/* ── Drawer slide-in transition ── */
.cn-drawer {
  position: fixed;
  top: 0; right: -620px; bottom: 0;
  width: 620px; max-width: 96vw;
  background: #fff;
  box-shadow: -12px 0 32px rgba(15,23,42,.12);
  z-index: 9001;
  display: flex; flex-direction: column;
  transition: right .24s cubic-bezier(.32,.72,0,1);
}
.cn-drawer.open { right: 0; }
.cn-view-drawer { width: 520px; right: -520px; }
.cn-view-drawer.open { right: 0; }

/* ── Section cards inside drawer body ── */
.cn-section {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 12px;
  box-shadow: 0 1px 2px rgba(15,23,42,.03);
}
.cn-section-hdr {
  display: flex; align-items: center; gap: 8px;
  font-size: 12px; font-weight: 700;
  text-transform: uppercase; letter-spacing: .04em; color: #0f172a;
}
.cn-dheader-left { display: flex; align-items: flex-start; gap: 12px; }
.cn-dheader-ico {
  width: 38px; height: 38px; border-radius: 10px;
  background: #fff; border: 1px solid rgba(220,38,38,.22);
  display: inline-flex; align-items: center; justify-content: center;
  color: #dc2626; flex-shrink: 0;
}
.cn-dheader-ico.edit { color: #ca8a04; border-color: rgba(202,138,4,.25); }

/* ── Field helpers ── */
.cn-field { display: flex; flex-direction: column; gap: 4px; }

/* ── Items line table ── */
.cn-items-table {
  display: flex; flex-direction: column;
  border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden;
}
.cn-items-head {
  display: grid;
  grid-template-columns: 2fr 2fr 80px 100px 100px 32px;
  gap: 8px; background: #f9fafb; padding: 8px 12px;
  font-size: 11.5px; font-weight: 600; color: #374151;
}
.cn-items-row {
  display: grid;
  grid-template-columns: 2fr 2fr 80px 100px 100px 32px;
  gap: 8px; padding: 8px 12px;
  border-top: 1px solid #f3f4f6; align-items: center;
}
.cn-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 8px 0; }
.cn-total-row.grand { font-weight: 700; font-size: 15px; color: #111827; border-top: 2px solid #e5e7eb; padding-top: 10px; }

/* ── View panel header ── */
.cn-view-head-body { display: flex; align-items: flex-end; justify-content: space-between; gap: 12px; margin-top: 4px; }
.cn-view-head-left { display: flex; flex-direction: column; gap: 2px; }
.cn-view-head-right { display: flex; flex-direction: column; align-items: flex-end; gap: 6px; flex-shrink: 0; }
.cn-view-amount { font-size: 22px; font-weight: 800; color: #1a1a2e; line-height: 1; }
.cn-vclose { align-self: flex-end; margin-left: auto; margin-bottom: 4px; }

/* ── Meta/detail 2-col grid ── */
.cn-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.cn-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }

/* ── View items table ── */
.cn-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.cn-view-items-head {
  display: grid; grid-template-columns: 2.5fr 70px 90px 100px;
  gap: 8px; background: #f9fafb; padding: 8px 12px;
  font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;
}
.cn-view-items-row {
  display: grid; grid-template-columns: 2.5fr 70px 90px 100px;
  gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6;
  align-items: center; font-size: 12.5px;
}

/* ── Applications grid ── */
.cn-app-head {
  display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px; background: #f9fafb; padding: 8px 12px;
  font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase;
  border-radius: 6px 6px 0 0; border: 1px solid #e5e7eb; border-bottom: none;
}
.cn-app-row {
  display: grid; grid-template-columns: 1fr 1fr 1fr 1fr;
  gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6;
  border-left: 1px solid #e5e7eb; border-right: 1px solid #e5e7eb;
  align-items: center; font-size: 12.5px;
}
.cn-app-row:last-child { border-bottom: 1px solid #e5e7eb; border-radius: 0 0 6px 6px; }

/* ── Row action button variants ── */
.cn-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.cn-act-apply { background: #fef2f2; border-color: #dc2626; color: #dc2626; }
.cn-act-apply:hover { background: #fee2e2; color: #b91c1c; }
.cn-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.cn-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }

/* ── Apply/Refund dialog ── */
.cn-apply-dialog {
  position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%);
  width: 480px; max-width: 96vw; background: #fff;
  border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.2);
  z-index: 9100; display: flex; flex-direction: column; overflow: hidden;
}

/* ── Timeline stepper wrapper ── */
.cn-stepper-wrap { background: #fff; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; }
</style>