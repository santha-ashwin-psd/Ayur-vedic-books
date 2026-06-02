<template>
  <div class="so-page">

    <!-- ── Unified toolbar (matches e-Way Bills) ── -->
    <div class="sales-toolbar">
      <div class="sales-search">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search orders, customers…" class="sales-search-input"/>
      </div>
      <div class="sales-pills">
        <button v-for="t in tabs" :key="t.key" class="sales-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">
          {{ t.label }}<span v-if="t.key!=='all'" class="sales-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div class="sales-actions">
        <button class="sales-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="sales-btn-ghost" @click="load" title="Refresh" :disabled="loading"><span v-html="icon('refresh',14)"></span></button>
        <button class="sales-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Sales Order
        </button>
      </div>
    </div>

    <!-- ── Summary strip ── -->
    <SummaryStrip :cards="[
      { label: 'Total Orders', tone: 'accent', value: list.length },
      { label: 'To Deliver', tone: counts.toDeliver>0?'warn':'default', value: counts.toDeliver, valueClass: counts.toDeliver>0?'orange':'' },
      { label: 'To Invoice', tone: 'info', value: counts.toInvoice, valueClass: 'blue' },
      { label: 'Pipeline Value', tone: 'success', value: fmtCur(summary.totalValue), valueClass: 'green' },
    ]" />

    <!-- ── Bulk actions bar ── -->
    <div v-if="selected.size>0" class="inv-bulk-bar">
      <span class="inv-bulk-count">{{ selected.size }} selected</span>
      <button class="inv-bulk-btn" @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button class="inv-bulk-btn inv-bulk-danger" @click="bulkDelete">Delete</button>
      <button class="inv-bulk-btn" @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
      <button class="inv-bulk-clear" @click="selected=new Set()">✕ Clear</button>
    </div>

    <!-- ── Table ── -->
    <div class="inv-table-wrap">
      <table class="inv-table">
        <thead><tr>
          <th class="th-check"><input type="checkbox" @change="toggleAll" :checked="allChecked"/></th>
          <th class="sortable" @click="sortBy('transaction_date')">DATE <span class="sort-arrow">{{ sortArrowTxt('transaction_date') }}</span></th>
          <th class="sortable" @click="sortBy('name')">ORDER # <span class="sort-arrow">{{ sortArrowTxt('name') }}</span></th>
          <th class="sortable" @click="sortBy('customer_name')">CUSTOMER <span class="sort-arrow">{{ sortArrowTxt('customer_name') }}</span></th>
          <th class="sortable" @click="sortBy('delivery_date')">DELIVERY <span class="sort-arrow">{{ sortArrowTxt('delivery_date') }}</span></th>
          <th class="sortable" @click="sortBy('status')">STATUS <span class="sort-arrow">{{ sortArrowTxt('status') }}</span></th>
          <th class="ta-r sortable" @click="sortBy('grand_total')">AMOUNT <span class="sort-arrow">{{ sortArrowTxt('grand_total') }}</span></th>
          <th style="width:120px;text-align:center">ACTIONS</th>
        </tr></thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 7" :key="n" class="shimmer-row">
              <td><div class="shimmer" style="width:14px;height:14px;border-radius:3px"></div></td>
              <td><div class="shimmer" style="width:80px"></div></td>
              <td><div class="shimmer" style="width:110px"></div></td>
              <td><div class="shimmer" style="width:130px"></div></td>
              <td><div class="shimmer" style="width:80px"></div></td>
              <td><div class="shimmer" style="width:90px"></div></td>
              <td><div class="shimmer" style="width:80px;margin-left:auto"></div></td>
              <td></td>
            </tr>
          </template>
          <template v-else>
            <tr v-for="o in paged" :key="o.name" class="inv-row" :class="{selected:selected.has(o.name)}">
              <td class="td-check" @click.stop>
                <input type="checkbox" :checked="selected.has(o.name)" @change="toggle(o.name)"/>
              </td>
              <td @click="openView(o)" class="text-muted mono-sm">{{ fmtDate(o.transaction_date) }}</td>
              <td @click="openView(o)"><span class="inv-link">{{ o.name }}</span></td>
              <td @click="openView(o)"><span class="inv-customer">{{ o.customer_name || o.customer || '—' }}</span></td>
              <td @click="openView(o)" :class="isPastDelivery(o)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(o.delivery_date)||'—' }}</td>
              <td @click="openView(o)">
                <span class="inv-status-badge" :class="badgeClass(o)">{{ displayStatus(o) }}</span>
              </td>
              <td class="ta-r mono-sm" @click="openView(o)">{{ fmtCur(o.grand_total) }}</td>
              <td style="text-align:center" @click.stop>
                <div style="display:flex;gap:4px;justify-content:center">
                  <button class="inv-act-btn" @click="openView(o)" title="View"><span v-html="icon('eye',13)"></span></button>
                  <button class="inv-act-btn" @click="openEdit(o)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                  <button v-if="canInvoice(o)" class="inv-act-btn inv-act-conv" @click="openInvoiceModal(o)" title="Invoice"><svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button>
                  <button class="inv-act-btn" style="color:#dc2626" @click.stop="deleteSO(o)" title="Delete"><span v-html="icon('trash',13)"></span></button>
                </div>
              </td>
            </tr>
            <tr v-if="!sorted.length">
              <td colspan="8" class="empty-state">
                <div class="empty-inner">
                  <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity=".3"><path d="M9 5H7a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2h-2"/><rect x="9" y="3" width="6" height="4" rx="1"/></svg>
                  <p>{{ search ? 'No sales orders match' : 'No sales orders yet' }}</p>
                  <button v-if="!search" class="inv-btn-primary" style="margin-top:4px" @click="openNew">
                    <span v-html="icon('plus',13)"></span> New Sales Order
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>
    <div v-if="!loading && sorted.length" style="padding:12px 20px 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ── Create / Edit Drawer ── -->
    <div v-if="drawerOpen" class="so-drawer-bg" @click.self="drawerOpen=false">
      <div class="so-drawer-panel">

        <!-- Header -->
        <div class="so-dh">
          <div>
            <div class="so-dh-title">{{ editingName ? 'Edit Sales Order' : 'New Sales Order' }}</div>
            <div class="so-dh-sub">{{ editingName || 'Fill in the details below' }}</div>
          </div>
          <button class="so-dclose-new" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <!-- Body -->
        <div class="so-dbody">

          <div class="so-sec-lbl">Order Details</div>
          <div class="so-fg so-fg3">
            <div style="grid-column:1/3">
              <label class="so-lbl">Customer <span class="so-req">*</span></label>
              <SearchableSelect v-model="form.customer" :options="customers" placeholder="Select customer…"
                :createable="true" createDoctype="Customer"
                @search="fetchCustomers" @update:modelValue="onCustomerChange" />
            </div>
            <div>
              <label class="so-lbl">Order Date <span class="so-req">*</span></label>
              <input v-model="form.transaction_date" type="date" class="so-fi"/>
            </div>
            <div>
              <label class="so-lbl">Delivery Date</label>
              <input v-model="form.delivery_date" type="date" class="so-fi"/>
            </div>
            <div>
              <label class="so-lbl">Customer PO #</label>
              <input v-model="form.po_number" type="text" class="so-fi" placeholder="Customer's purchase order #"/>
            </div>
            <div style="grid-column:1/-1">
              <label class="so-lbl">Shipping Address <span v-if="addressLoading" style="color:#9ca3af;font-weight:400">(loading…)</span></label>
              <input v-model="form.shipping_address" type="text" class="so-fi" placeholder="Auto-filled from customer, or enter manually"/>
            </div>
            <div style="grid-column:1/-1">
              <div class="so-inv-block" :class="form.set_warehouse ? 'so-wh-on' : 'so-wh-off'">
                <div class="so-inv-toggle-row">
                  <div class="so-inv-icon" v-html="icon('warehouse',16)"></div>
                  <div class="so-inv-text">
                    <div class="so-inv-title">Dispatch Warehouse <span style="color:#dc2626">*</span></div>
                    <div class="so-inv-sub">Stock will be deducted from this warehouse when the invoice is submitted</div>
                  </div>
                </div>
                <SearchableSelect v-model="form.set_warehouse" :options="warehouses" placeholder="Select warehouse stock will be dispatched from…" @search="fetchWarehouses" />
              </div>
            </div>
          </div>

          <!-- Line Items -->
          <div class="so-sec-lbl" style="display:flex;align-items:center;justify-content:space-between;border-top:1px solid #f0f2f5;padding-top:16px;margin-top:4px">
            LINE ITEMS
            <button class="so-add-item-btn" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
          </div>

          <div class="so-lines-wrap">
            <div class="so-lines-head">
              <div>ITEM <span class="so-req">*</span></div>
              <div>DESCRIPTION</div>
              <div class="ta-r">QTY</div>
              <div class="ta-r">RATE (₹)</div>
              <div class="ta-r">AMOUNT</div>
              <div></div>
            </div>
            <div v-for="line in lines" :key="line.id" class="so-lines-row">
              <div style="min-width:0">
                <SearchableSelect v-model="line.item_code" :options="items"
                  placeholder="Item…" :createable="true" createDoctype="Item"
                  @search="fetchItems" @select="v=>onItemSelect(line,v)"/>
              </div>
              <div><input v-model="line.description" class="so-ci" placeholder="Description"/></div>
              <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="so-ci so-ci-r" @input="calcLine(line)"/></div>
              <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="so-ci so-ci-r" @input="calcLine(line)"/></div>
              <div class="ta-r mono-sm" style="display:flex;align-items:center;justify-content:flex-end;font-weight:600;font-size:13px">{{ fmtCur(line.amount) }}</div>
              <div style="display:flex;align-items:center;justify-content:center">
                <button @click="removeLine(line.id)" class="so-rm-line"><span v-html="icon('x',12)"></span></button>
              </div>
            </div>
            <div v-if="!lines.length" class="so-lines-empty">No items yet — click <strong>Add Item</strong> to begin.</div>
            <button class="so-add-line-btn" @click="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
          </div>

          <!-- Totals -->
          <div class="so-totals-wrap">
            <div class="so-tax-section">
              <div class="so-tax-header">
                <span class="so-tax-title">Tax</span>
              </div>
              <div style="display:flex;align-items:center;gap:10px">
                <label class="so-lbl" style="margin:0;white-space:nowrap">Tax Rate %</label>
                <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.5" class="so-ci" style="max-width:100px"/>
              </div>
            </div>
            <div class="so-totals-right-panel">
              <div class="so-total-row-item">
                <span>Subtotal</span>
                <span class="so-total-amt">{{ fmtCur(subtotal) }}</span>
              </div>
              <div class="so-total-row-item" style="color:#6b7280;font-size:12px">
                <span>Tax ({{ form.tax_rate||0 }}%)</span>
                <span class="so-total-amt">{{ fmtCur(taxAmount) }}</span>
              </div>
              <div class="so-total-row-item so-grand-total">
                <span>Grand Total</span>
                <span class="so-total-amt" style="font-size:16px;color:#1a6ef7">{{ fmtCur(subtotal+taxAmount) }}</span>
              </div>
            </div>
          </div>

          <!-- Terms -->
          <div class="so-sec-lbl">Notes & Terms</div>
          <div style="margin-bottom:14px">
            <label class="so-lbl">Terms & Conditions <span style="color:#9ca3af;font-weight:400">(printed on order)</span></label>
            <textarea v-model="form.terms" rows="3" class="so-fi" style="resize:vertical" placeholder="Payment terms, delivery terms…"></textarea>
          </div>

        </div><!-- /so-dbody -->

        <div class="so-dfooter-new">
          <div style="font-size:12px;color:#9ca3af">{{ editingName ? 'Editing: '+editingName : 'New sales order' }}</div>
          <div style="display:flex;gap:10px">
            <button class="so-btn-ghost" @click="drawerOpen=false">Cancel</button>
            <button class="so-btn-ghost" style="border-color:#3b82f6;color:#3b82f6" :disabled="drawerSaving" @click="saveSO('Draft')">
              <span v-html="icon('save',13)"></span> Save Draft
            </button>
            <button class="inv-btn-primary" :disabled="drawerSaving" @click="saveSO('To Deliver')">
              <span v-html="icon('check',13)"></span> {{ drawerSaving ? 'Saving…' : 'Confirm Order' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="so-overlay" @click.self="viewOpen=false"></div>
    <div class="so-view-drawer-panel" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="so-view-head" :style="`background:${headerBg(viewDoc)}`">
          <div>
            <div class="so-view-num">{{ viewDoc.name }}</div>
            <div class="so-view-sub">{{ viewDoc.customer_name||viewDoc.customer }}</div>
          </div>
          <div style="text-align:right">
            <div class="so-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="inv-status-badge so-badge-white" style="margin-top:4px;display:inline-flex">{{ displayStatus(viewDoc) }}</span>
          </div>
          <button class="so-dclose-view" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <!-- Inline timeline -->
        <div class="so-timeline">
          <template v-for="(step, i) in timelineSteps" :key="i">
            <div class="so-tl-step" :class="{ done: step.done, danger: step.danger, current: step.current }">
              <div class="so-tl-dot">
                <span v-if="step.done && !step.danger" v-html="icon('check', 9)"></span>
                <span v-else-if="step.danger" style="font-size:9px;font-weight:700">!</span>
              </div>
              <div class="so-tl-label">{{ step.label }}</div>
            </div>
            <div v-if="i < timelineSteps.length - 1" class="so-tl-line"
              :class="{ done: timelineSteps[i+1]?.done, danger: timelineSteps[i+1]?.danger }"></div>
          </template>
        </div>

        <div class="so-tabs">
          <button class="so-tab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="so-tab" :class="{active:viewTab==='fulfill'}" @click="viewTab='fulfill'">Fulfillment</button>
          <button class="so-tab" :class="{active:viewTab==='links'}" @click="viewTab='links'">
            Linked<span v-if="links.sales_invoices.length>0" class="so-tab-count">{{ links.sales_invoices.length }}</span>
          </button>
        </div>

        <div class="so-vbody">
          <template v-if="viewTab==='details'">
            <div class="so-meta-grid">
              <div><div class="so-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
              <div>
                <div class="so-meta-lbl">Delivery Date</div>
                <div class="mono-sm" :class="isPastDelivery(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.delivery_date)||'—' }}</div>
              </div>
              <div><div class="so-meta-lbl">Customer PO</div><div class="mono-sm">{{ viewDoc.po_number||'—' }}</div></div>
              <div><div class="so-meta-lbl">From Quote</div><div class="mono-sm">{{ viewDoc.ref_quote||'—' }}</div></div>
            </div>

            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="so-section-title" style="margin-top:12px">Line Items</div>
              <div class="so-view-items">
                <div class="so-view-items-head">
                  <span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span>
                </div>
                <div v-for="it in viewItems" :key="it.name" class="so-view-items-row">
                  <span>
                    <strong>{{ it.item_name||it.item_code }}</strong>
                    <div v-if="it.description" class="text-muted" style="font-size:11px">{{ it.description }}</div>
                  </span>
                  <span class="ta-r mono-sm">{{ it.qty }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(it.amount) }}</span>
                </div>
              </div>
              <div v-if="viewDoc.grand_total" style="display:flex;justify-content:flex-end;padding:10px 12px;border-top:1px solid #e8ecf0;gap:32px;font-size:13px">
                <span style="color:#6b7280">Grand Total</span>
                <span style="font-family:monospace;font-weight:700;color:#1a6ef7;font-size:15px">{{ fmtCur(viewDoc.grand_total) }}</span>
              </div>
            </template>

            <div v-if="viewDoc.terms" class="so-terms" style="margin-top:12px">
              <div class="so-meta-lbl">Terms & Conditions</div>
              <div style="white-space:pre-wrap;font-size:12.5px;color:#374151">{{ viewDoc.terms }}</div>
            </div>
          </template>

          <template v-if="viewTab==='fulfill'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="fulfill.lines.length">
              <div style="font-size:12px;color:#6b7280;margin-bottom:8px">Status: <strong>{{ fulfill.computed_status }}</strong></div>
              <div class="so-fulfill-tbl">
                <div class="so-fulfill-head">
                  <span>Item</span>
                  <span class="ta-r">Ordered</span>
                  <span class="ta-r">Delivered</span>
                  <span class="ta-r">Invoiced</span>
                  <span class="ta-r">Remaining</span>
                </div>
                <div v-for="l in fulfill.lines" :key="l.name" class="so-fulfill-row">
                  <span>{{ l.item_name||l.item_code }}</span>
                  <span class="ta-r mono-sm">{{ l.qty }}</span>
                  <span class="ta-r mono-sm" :class="l.delivered_qty>=l.qty?'text-success':'text-muted'">{{ l.delivered_qty }}</span>
                  <span class="ta-r mono-sm" :class="l.billed_qty>=l.qty?'text-success':'text-muted'">{{ l.billed_qty }}</span>
                  <span class="ta-r mono-sm text-danger">{{ l.remaining_to_deliver }} / {{ l.remaining_to_bill }}</span>
                </div>
              </div>
              <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px">
                <button v-if="hasUndelivered" class="so-btn-ghost" @click="markAllDelivered" :disabled="actionRunning">📦 Mark All Delivered</button>
              </div>
            </template>
            <div v-else style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">No line items.</div>
          </template>

          <template v-if="viewTab==='links'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else>
              <div v-if="viewDoc.ref_quote" class="so-section-title">Originating Quote</div>
              <div v-if="viewDoc.ref_quote" class="so-link-row">
                <span class="inv-link">{{ viewDoc.ref_quote }}</span>
                <span class="text-muted">Quotation</span>
              </div>
              <div v-if="links.sales_invoices.length" class="so-section-title">Sales Invoices</div>
              <div v-for="si in links.sales_invoices" :key="si.name" class="so-link-row">
                <span class="inv-link">{{ si.name }}</span>
                <span class="text-muted">{{ fmtDate(si.posting_date) }}</span>
                <span class="text-muted">Out: {{ fmtCur(si.outstanding_amount) }}</span>
                <span style="text-align:right;font-weight:600">{{ fmtCur(si.grand_total) }}</span>
              </div>
              <div v-if="!viewDoc.ref_quote && !links.sales_invoices.length"
                style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
                No linked documents yet.
              </div>
            </template>
          </template>
        </div>

        <div class="so-vfooter">
          <button class="so-btn-ghost" @click="viewOpen=false">Close</button>
          <button class="so-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button class="so-btn-ghost" @click="emailSO(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="so-btn-ghost" @click="printSO(viewDoc)" title="Print preview">🖨 Print</button>
          <button v-if="canInvoice(viewDoc)" class="inv-btn-primary" @click="openInvoiceModal(viewDoc)">→ Invoice</button>
          <button class="so-btn-danger" @click="cancelSO(viewDoc)">Cancel</button>
          <button class="so-btn-danger" @click="deleteSO(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Convert-to-Invoice modal ── -->
    <div v-if="invModal.open" class="so-overlay" @click.self="invModal.open=false" style="z-index:60"></div>
    <div v-if="invModal.open" class="so-inv-dialog">
      <div class="so-dh" style="border-radius:12px 12px 0 0">
        <div>
          <div class="so-dh-title">Convert to Invoice</div>
          <div class="so-dh-sub">{{ invModal.soName }}</div>
        </div>
        <button class="so-dclose-new" @click="invModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="so-vbody" style="padding:20px 24px;gap:12px">
        <div style="font-size:12.5px;color:#374151">Enter the quantity to invoice for each line (defaults to remaining):</div>
        <div class="so-inv-tbl">
          <div class="so-inv-head">
            <span>Item</span><span class="ta-r">Remaining</span><span class="ta-r">Invoice</span>
          </div>
          <div v-for="l in invModal.lines" :key="l.name" class="so-inv-row">
            <span>{{ l.item_name||l.item_code }}</span>
            <span class="ta-r mono-sm text-muted">{{ l.remaining_to_bill }}</span>
            <input v-model.number="l.toInvoice" type="number" min="0" :max="l.remaining_to_bill" step="0.001"
              class="so-ci so-ci-r" style="width:90px"/>
          </div>
        </div>
        <div>
          <label class="so-lbl">Due Date</label>
          <input v-model="invModal.dueDate" type="date" class="so-fi" style="max-width:200px"/>
        </div>
        <div style="text-align:right;font-size:13px;color:#6b7280">
          Invoice Total: <strong style="color:#1a6ef7;font-size:15px;font-family:monospace">{{ fmtCur(invModalTotal) }}</strong>
        </div>
      </div>
      <div class="so-vfooter">
        <button class="so-btn-ghost" @click="invModal.open=false" :disabled="invModal.saving">Cancel</button>
        <button class="inv-btn-primary" :disabled="invModal.saving||invModalTotal<=0" @click="submitInvoice">
          {{ invModal.saving ? 'Creating…' : `Create Invoice ${fmtCur(invModalTotal)}` }}
        </button>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiPOST, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useRoute } from "vue-router";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { useOpenFromQuery } from "../composables/useOpenFromQuery.js";
import { usePagination } from "../composables/usePagination.js";
import DocLink from "../components/DocLink.vue";
import Pagination from "../components/Pagination.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import { useConfirm } from "../composables/useConfirm.js";
import { useLivePreview } from "../composables/useLivePreview.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";



const { toast } = useToast();
const route = useRoute();
const { confirm } = useConfirm();
const { printDoc } = useLivePreview();
function printSO(d) { printDoc(d, { title: "SALES ORDER", partyLabel: "Customer", partyField: "customer_name", companyName: d?.company || "" }); }

const { openEmail } = useEmailDialog();

const activeTab = ref("all");
const tabs = [
  { key: "all",       label: "All" },
  { key: "draft",     label: "Draft" },
  { key: "toDeliver", label: "To Deliver" },
  { key: "toInvoice", label: "To Invoice" },
  { key: "closed",    label: "Closed" },
  { key: "cancelled", label: "Cancelled" },
];

const list = ref([]), loading = ref(false), search = ref(""), selected = ref(new Set());
const drawerOpen = ref(false), drawerSaving = ref(false), editingName = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const viewLoading = ref(false), viewItems = ref([]);
const fulfill = reactive({ lines: [], computed_status: "" });
const links = reactive({ sales_invoices: [], delivery_challans: [] });
const customers = ref([]), items = ref([]), lines = ref([]), taxAccountHead = ref("");
const addressLoading = ref(false);
const sortCol = ref("transaction_date"), sortDir = ref("desc");
const actionRunning = ref(false);

let _id = 1;
const blankLine = () => ({ id: _id++, item_code: "", description: "", qty: 1, rate: 0, amount: 0 });
const form = reactive({
  customer: "", transaction_date: todayStr(), delivery_date: deliveryDefault(),
  po_number: "", shipping_address: "", set_warehouse: "", tax_rate: 0, terms: "",
});
const warehouses = ref([]);
async function fetchWarehouses(q = "") {
  try {
    const co = await resolveCompany();
    const rows = await apiList("Warehouse", { filters: [["company","=",co],["disabled","=",0],["is_group","=",0]], fields: ["name"], limit: 50 });
    warehouses.value = (rows || []).filter(r => !q || r.name.toLowerCase().includes(q.toLowerCase())).map(r => ({ label: r.name, value: r.name }));
  } catch { warehouses.value = []; }
}

const invModal = reactive({ open: false, saving: false, soName: "", lines: [], dueDate: "" });

function todayStr() { return new Date().toISOString().slice(0, 10); }
function deliveryDefault() { const d = new Date(); d.setDate(d.getDate() + 14); return d.toISOString().slice(0, 10); }
function fmtCur(v) { return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(flt(v)); }

function isPastDelivery(o) {
  if (!o?.delivery_date) return false;
  const s = (o.status||"").toLowerCase();
  if (s === "closed" || s === "invoiced" || s === "cancelled") return false;
  return new Date(o.delivery_date) < new Date();
}
function displayStatus(o) {
  const s = o?.status;
  if (!s) return "DRAFT";
  return s.toUpperCase();
}
function badgeClass(o) {
  const s = (o?.status||"").toLowerCase();
  if (!s || s === "draft")  return "so-bdg-grey";
  if (s === "cancelled")    return "so-bdg-red";
  if (s === "closed" || s === "invoiced") return "so-bdg-green";
  if (s.includes("delivered") && !s.includes("partially")) return "so-bdg-blue";
  if (s === "to deliver" || s.includes("partially"))      return "so-bdg-orange";
  return "so-bdg-blue";
}
function headerBg(o) {
  const s = (o?.status||"").toLowerCase();
  if (s === "cancelled") return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  if (s === "closed" || s === "invoiced") return "linear-gradient(135deg,#064e3b,#059669)";
  if (s === "to deliver" || s.includes("partially"))    return "linear-gradient(135deg,#78350f,#d97706)";
  if (s === "delivered") return "linear-gradient(135deg,#1e3a5f,#1a6ef7)";
  return "linear-gradient(135deg,#374151,#6b7280)";
}
function canInvoice(o) {
  const s = (o?.status||"").toLowerCase();
  return s !== "cancelled" && s !== "closed" && s !== "invoiced";
}

async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    list.value = await apiList("Sales Order", {
      fields: ["name", "customer", "customer_name", "transaction_date", "delivery_date", "status", "grand_total", "billed_amount", "ref_quote", "po_number"],
      filters: [["company", "=", co]],
      limit: 500,
      order: "transaction_date desc",
    });
  } catch (e) { toast.error(e.message || "Failed to load sales orders"); }
  finally { loading.value = false; }
}
async function loadTaxAccount() {
  try {
    const r = await apiList("Account", { fields: ["name"], filters: [["account_type", "=", "Tax"], ["is_group", "=", 0]], limit: 1 });
    if (r?.length) taxAccountHead.value = r[0].name;
  } catch {}
}

const counts = computed(() => {
  const c = { draft:0, toDeliver:0, toInvoice:0, closed:0, cancelled:0 };
  for (const o of list.value) {
    const s = (o.status||"draft").toLowerCase();
    if (s === "cancelled") c.cancelled++;
    else if (s === "closed" || s === "invoiced") c.closed++;
    else if (s === "draft") c.draft++;
    else if (s === "delivered") c.toInvoice++;
    else c.toDeliver++;   // To Deliver / Partially Delivered / Submitted
  }
  return c;
});
const summary = computed(() => ({
  totalValue: list.value.filter(o => (o.status||"").toLowerCase() !== "cancelled")
    .reduce((s, o) => s + flt(o.grand_total), 0),
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") {
    r = r.filter(o => {
      const s = (o.status||"draft").toLowerCase();
      if (activeTab.value === "draft")     return s === "draft";
      if (activeTab.value === "cancelled") return s === "cancelled";
      if (activeTab.value === "closed")    return s === "closed" || s === "invoiced";
      if (activeTab.value === "toInvoice") return s === "delivered";
      if (activeTab.value === "toDeliver") return s !== "cancelled" && s !== "closed" && s !== "invoiced" && s !== "draft" && s !== "delivered";
      return true;
    });
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name || "").toLowerCase().includes(q)
      || (x.customer_name || x.customer || "").toLowerCase().includes(q)
      || (x.po_number || "").toLowerCase().includes(q));
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

const { page, pageSize, paged } = usePagination(sorted, { storageKey: "sales-orders" });

function sortBy(col) { if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc"; else { sortCol.value = col; sortDir.value = "asc"; } }
function sortArrow(col) { if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value === "asc" ? "↑" : "↓"; }
function sortArrowTxt(col) { if (sortCol.value !== col) return "⇅"; return sortDir.value === "asc" ? "↑" : "↓"; }
function pillCls(key) {
  if (key === "toDeliver") return "pc-orange";
  if (key === "toInvoice") return "pc-blue";
  if (key === "closed")    return "pc-green";
  if (key === "cancelled") return "pc-red";
  return "pc-muted";
}

const allChecked = computed(() => sorted.value.length > 0 && sorted.value.every(o => selected.value.has(o.name)));
function toggle(n) { const s = new Set(selected.value); s.has(n) ? s.delete(n) : s.add(n); selected.value = s; }
function toggleAll(e) { selected.value = e.target.checked ? new Set(sorted.value.map(o => o.name)) : new Set(); }

const subtotal = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const taxAmount = computed(() => Math.round(subtotal.value * flt(form.tax_rate) / 100 * 100) / 100);

const hasUndelivered = computed(() => fulfill.lines.some(l => l.remaining_to_deliver > 0));

const timelineSteps = computed(() => {
  const o = viewDoc.value;
  if (!o) return [];
  const s = (o.status||"").toLowerCase();
  if (s === "cancelled") {
    return [
      { key:"draft", label:"Draft", done:true },
      { key:"sub",   label:"Submitted", done:true },
      { key:"end",   label:"Cancelled", danger:true, current:true },
    ];
  }
  const delivered = s === "delivered" || s === "invoiced" || s === "closed";
  const invoiced  = s === "invoiced"  || s === "closed";
  const closed    = s === "closed";
  return [
    { key:"draft",     label:"Draft",     done:true },
    { key:"submitted", label:"Submitted", done:s!=="draft", current:s==="to deliver"||s==="submitted" },
    { key:"delivered", label:"Delivered", done:delivered, current:s==="delivered" && !invoiced },
    { key:"invoiced",  label:"Invoiced",  done:invoiced, current:invoiced && !closed },
    { key:"closed",    label:"Closed",    done:closed, current:closed },
  ];
});

const invModalTotal = computed(() =>
  (invModal.lines || []).reduce((s, l) => s + flt(l.toInvoice) * flt(l.rate), 0)
);

// ── Create / Edit ─────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, { customer: "", transaction_date: todayStr(), delivery_date: deliveryDefault(), po_number: "", shipping_address: "", set_warehouse: "", tax_rate: 0, terms: "" });
  lines.value = [blankLine()];
  fetchCustomers(""); fetchItems(""); fetchWarehouses("");
  drawerOpen.value = true;
}
async function openEdit(o) {
  editingName.value = o.name;
  Object.assign(form, {
    customer: o.customer || "", transaction_date: o.transaction_date || todayStr(),
    delivery_date: o.delivery_date || deliveryDefault(), po_number: o.po_number || "",
    shipping_address: "", set_warehouse: "", tax_rate: 0, terms: o.terms || "",
  });
  lines.value = [blankLine()];
  fetchCustomers(""); fetchItems(""); fetchWarehouses("");
  drawerOpen.value = true;
  try {
    const doc = await apiGet("Sales Order", o.name);
    if (doc?.items?.length) {
      lines.value = doc.items.map(i => ({
        id: _id++, item_code: i.item_code || "", description: i.description || "",
        qty: i.qty || 1, rate: i.rate || 0, amount: i.amount || 0,
      }));
    }
    if (doc?.taxes?.[0]?.rate) form.tax_rate = doc.taxes[0].rate;
    if (doc?.taxes?.[0]?.account_head) taxAccountHead.value = doc.taxes[0].account_head;
    if (doc?.terms) form.terms = doc.terms;
    if (doc?.shipping_address) form.shipping_address = doc.shipping_address;
    if (doc?.set_warehouse) form.set_warehouse = doc.set_warehouse;
  } catch {}
}
async function openView(o) {
  viewDoc.value = o;
  viewOpen.value = true;
  viewTab.value = "details";
  viewLoading.value = true;
  viewItems.value = [];
  fulfill.lines = []; fulfill.computed_status = "";
  links.sales_invoices = []; links.delivery_challans = [];
  try {
    const [doc, ful, lnk] = await Promise.all([
      apiGet("Sales Order", o.name),
      apiGET("zoho_books_clone.api.docs.get_sales_order_fulfillment", { sales_order: o.name }).catch(() => null),
      apiGET("zoho_books_clone.api.docs.get_sales_order_links", { sales_order: o.name }).catch(() => null),
    ]);
    viewItems.value = doc?.items || [];
    viewDoc.value = { ...o, ...doc };
    if (ful) { fulfill.lines = ful.lines || []; fulfill.computed_status = ful.computed_status || ""; }
    if (lnk) { links.sales_invoices = lnk.sales_invoices || []; }
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

// ── Customer change: auto-fill shipping address from customer ship_* fields ──
async function onCustomerChange() {
  form.shipping_address = "";
  if (!form.customer) return;
  addressLoading.value = true;
  try {
    const custDoc = await apiGet("Customer", form.customer);
    // Build shipping address from ship_* fields, fall back to billing fields
    const shipFields = [
      custDoc?.ship_address_line1, custDoc?.ship_address_line2,
      custDoc?.ship_city, custDoc?.ship_state, custDoc?.ship_pincode, custDoc?.ship_country,
    ];
    const billingFields = [
      custDoc?.address_line1, custDoc?.address_line2,
      custDoc?.city, custDoc?.state, custDoc?.pincode, custDoc?.country,
    ];
    const builtAddr = shipFields.filter(Boolean).join(", ")
      || billingFields.filter(Boolean).join(", ");
    if (builtAddr) form.shipping_address = builtAddr;
  } catch {}
  addressLoading.value = false;
}
async function fetchItems(q = "") {
  try {
    const f = [["disabled", "=", 0]];
    if (q) f.push(["item_name", "like", "%" + q + "%"]);
    const r = await apiList("Item", { fields: ["name", "item_name", "standard_rate", "stock_uom", "description"], filters: f, limit: 30, order: "item_name asc" });
    items.value = r.map(x => ({ ...x, label: x.item_name || x.name, value: x.name, rate: x.standard_rate || 0, uom: x.stock_uom || "Nos", description: x.description || "" }));
  } catch { items.value = []; }
}
async function onItemSelect(line, opt) {
  const code = opt?.value ?? opt;
  line.item_code = code;

  // Fill from already-loaded items list
  const found = items.value.find(i => i.name === code || i.value === code);
  if (found) {
    line.rate = flt(found.standard_rate ?? found.rate);
    if (found.description) line.description = found.description;
    calcLine(line);
  }

  // Fetch full Item doc to get any fields not in the list
  if (code) {
    try {
      const doc = await apiGet("Item", code);
      if (doc?.description)  line.description = doc.description;
      if (!found) {
        line.rate = flt(doc.standard_rate || 0);
      }
      calcLine(line);
    } catch {}
  }
}
function addLine() { lines.value.push(blankLine()); }
function removeLine(id) { if (lines.value.length > 1) lines.value = lines.value.filter(l => l.id !== id); }
function calcLine(l) { l.amount = Math.round(flt(l.qty) * flt(l.rate) * 100) / 100; }

async function saveSO(newStatus) {
  if (!form.customer) return toast.error("Customer is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0)) return toast.error("At least one item required");
  if (!form.set_warehouse) return toast.error("Dispatch Warehouse is required");
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const taxes = form.tax_rate > 0 && taxAccountHead.value
      ? [{ doctype: "Tax Line", charge_type: "On Net Total", account_head: taxAccountHead.value, description: taxAccountHead.value, rate: form.tax_rate }]
      : [];
    const doc = {
      doctype: "Sales Order", company,
      customer: form.customer, transaction_date: form.transaction_date,
      delivery_date: form.delivery_date || null,
      po_number: form.po_number || "",
      shipping_address: form.shipping_address || "",
      set_warehouse: form.set_warehouse || "",
      status: newStatus || "Draft",
      terms: form.terms || "",
      items: lines.value.filter(l => l.item_code).map(l => ({
        doctype: "Sales Order Item", item_code: l.item_code,
        description: l.description || l.item_code,
        qty: flt(l.qty) || 1, rate: flt(l.rate), amount: flt(l.amount),
      })),
      taxes,
    };
    if (editingName.value) doc.name = editingName.value;
    const saved = await apiSave(doc);
    toast.success(`Sales Order ${saved?.name || ""} saved`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to save order"); }
  finally { drawerSaving.value = false; }
}

// ── Actions ───────────────────────────────────────────────────────────────
async function emailSO(o) {
  await openEmail({
    doctype: "Sales Order", name: o.name, docLabel: `Sales Order ${o.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_sales_order_email_defaults",
    sendEndpoint: "zoho_books_clone.api.docs.send_sales_order_email",
    paramKey: "sales_order",
  });
}

function openInvoiceModal(o) {
  // Fetch fresh fulfillment to ensure we have remaining_to_bill
  apiGET("zoho_books_clone.api.docs.get_sales_order_fulfillment", { sales_order: o.name })
    .then(r => {
      const ful = r?.lines || [];
      Object.assign(invModal, {
        open: true, saving: false, soName: o.name,
        lines: ful.filter(l => l.remaining_to_bill > 0)
                  .map(l => ({ ...l, toInvoice: l.remaining_to_bill })),
        dueDate: o.delivery_date || todayStr(),
      });
      if (!invModal.lines.length) { invModal.open = false; toast.info("Nothing left to invoice"); }
    })
    .catch(e => toast.error(e.message || "Failed to load fulfillment"));
}
async function submitInvoice() {
  const lineMap = {};
  for (const l of invModal.lines) {
    if (flt(l.toInvoice) > 0) lineMap[l.name] = flt(l.toInvoice);
  }
  if (!Object.keys(lineMap).length) { toast.error("Enter at least one qty to invoice"); return; }
  invModal.saving = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.docs.convert_sales_order_to_invoice", {
      sales_order: invModal.soName,
      line_qtys: JSON.stringify(lineMap),
      due_date: invModal.dueDate || "",
    });
    toast.success(`Invoice created: ${r?.sales_invoice}`);
    invModal.open = false;
    await load();
    if (viewDoc.value?.name === invModal.soName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Convert failed"); }
  invModal.saving = false;
}

async function markAllDelivered() {
  actionRunning.value = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.docs.mark_so_delivered", { sales_order: viewDoc.value.name });
    toast.success(`Marked ${r?.lines_updated || 0} line(s) delivered`);
    await load();
    if (viewDoc.value) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Mark delivered failed"); }
  actionRunning.value = false;
}

async function cancelSO(o) {
  if (!await confirm({ title: "Cancel Sales Order", body: `Cancel ${o.name}? Linked invoices must be cancelled separately.`, okLabel: "Cancel SO" })) return;
  try {
    await apiPOST("zoho_books_clone.api.docs.cancel_sales_order_safe", { sales_order: o.name });
    toast.success("Sales Order cancelled");
    await load(); if (viewDoc.value?.name === o.name) await openView(o);
  } catch (e) { toast.error(e.message || "Cancel failed"); }
}
async function deleteSO(o) {
  if (!await confirm({ title: "Delete Sales Order", body: `Permanently delete ${o.name}?`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Sales Order", o.name);
    toast.success("Sales Order deleted");
    viewOpen.value = false; await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk actions ──────────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(o => selected.value.has(o.name) && (!o.status || o.status === "Draft"));
  if (!drafts.length) { toast.info("Select drafts to delete"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft order(s)?`, okLabel: "Delete" })) return;
  for (const o of drafts) { try { await apiDelete("Sales Order", o.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length}`);
  await load();
}
async function bulkEmail() {
  const subs = sorted.value.filter(o => selected.value.has(o.name));
  if (!subs.length) { toast.info("No orders selected"); return; }
  let sent = 0;
  for (const o of subs) {
    const ok = await openEmail({
      doctype: "Sales Order", name: o.name, docLabel: `Sales Order ${o.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_sales_order_email_defaults",
      sendEndpoint: "zoho_books_clone.api.docs.send_sales_order_email",
      paramKey: "sales_order",
    });
    if (ok) sent++;
  }
  if (sent) toast.success(`Emailed ${sent} order(s)`);
}

function exportCSV() {
  const rows = selected.value.size
    ? sorted.value.filter(o => selected.value.has(o.name))
    : sorted.value;
  if (!rows.length) return;
  const head = ["Order #","Customer","Date","Delivery","Status","PO #","Amount"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const o of rows) {
    out.push([o.name, o.customer_name || o.customer, o.transaction_date, o.delivery_date || "",
      o.status || "Draft", o.po_number || "", Number(o.grand_total || 0).toFixed(2)].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `sales_orders_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} order(s)`);
}

onMounted(async () => {
  await load();
  loadTaxAccount();
  useOpenFromQuery({
    route,
    openByName: (n) => openView(list.value.find(x => x.name === n) || { name: n }),
  });
});
</script>

<style scoped>
/* ══ Page ══ */
.so-page { display:flex; flex-direction:column; gap:16px; padding:24px; background:#f5f6f8; min-height:100vh; }

/* ══ Toolbar ══ */
.inv-toolbar { display:flex; align-items:center; justify-content:space-between; padding:16px 24px 12px; gap:12px; flex-wrap:wrap; background:#fff; border-bottom:1px solid #e8ecf0; }
.inv-heading { font-size:18px; font-weight:700; color:#1a1a2e; margin:0; }
.inv-toolbar-right { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.inv-search-wrap { display:flex; align-items:center; gap:8px; background:#ffffff; border-radius:8px; padding:7px 12px; min-width:240px; }
.inv-search-input { border:none; background:transparent; outline:none; font:inherit; color:#111827; width:100%; font-size:13px; }
.inv-btn-primary { display:inline-flex; align-items:center; gap:6px; background:#1a6ef7; color:#fff; border:none; border-radius:8px; padding:8px 14px; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit; }
.inv-btn-primary:hover:not(:disabled) { background:#155fd4; }
.inv-btn-primary:disabled { opacity:.5; cursor:not-allowed; }
.inv-btn-ghost { display:inline-flex; align-items:center; gap:6px; background:transparent; border:1px solid #e2e8f0; border-radius:8px; padding:7px 12px; font-size:13px; color:#374151; cursor:pointer; font-family:inherit; }
.inv-btn-ghost:hover { background:#f8fafc; }

/* ══ Summary strip ══ */
.inv-sum-strip { display:flex; gap:0; background:#fff; border-bottom:1px solid #e8ecf0; }
.inv-sum-card { flex:1; padding:16px 24px; display:flex; flex-direction:column; gap:4px; border-left:3px solid transparent; }
.inv-sum-lbl { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.06em; color:#9ca3af; }
.inv-sum-val { font-size:26px; font-weight:800; color:#1a1a2e; font-family:monospace; }

/* ══ Filter bar ══ */
.inv-filter-bar { display:flex; align-items:center; justify-content:space-between; padding:10px 24px; background:#fff; border-bottom:1px solid #e8ecf0; gap:12px; flex-wrap:wrap; }
.inv-pills { display:flex; gap:6px; flex-wrap:wrap; }
.inv-pill { padding:5px 14px; border-radius:20px; font-size:12.5px; font-weight:600; border:1px solid #e2e8f0; background:#fff; color:#6b7280; cursor:pointer; font-family:inherit; display:inline-flex; align-items:center; gap:6px; transition:all .12s; }
.inv-pill:hover { color:#1a6ef7; border-color:#1a6ef7; }
.inv-pill.active { background:#eaf1ff; border-color:#1a6ef7; color:#1a6ef7; }
.inv-pill-count { padding:1px 7px; border-radius:999px; font-size:11px; font-weight:700; background:#f3f4f6; color:#6b7280; }
.inv-pill.active .inv-pill-count { background:#1a6ef7; color:#fff; }
.pc-muted   { background:#f3f4f6 !important; color:#6b7280 !important; }
.pc-blue    { background:#dbeafe !important; color:#1a6ef7 !important; }
.pc-green   { background:#d1fae5 !important; color:#059669 !important; }
.pc-orange  { background:#fef3c7 !important; color:#d97706 !important; }
.pc-red     { background:#fee2e2 !important; color:#dc2626 !important; }

/* ══ Bulk bar ══ */
.inv-bulk-bar { display:flex; align-items:center; gap:8px; padding:10px 16px; background:#eff6ff; border:1px solid #bfdbfe; border-radius:10px; flex-wrap:wrap; }
.inv-bulk-count { font-size:13px; font-weight:700; color:#1a6ef7; margin-right:4px; }
.inv-bulk-btn { display:inline-flex; align-items:center; gap:5px; background:#fff; border:1px solid #e2e8f0; border-radius:6px; padding:5px 12px; font-size:12.5px; font-weight:600; color:#374151; cursor:pointer; font-family:inherit; }
.inv-bulk-btn:hover { background:#f8fafc; border-color:#1a6ef7; color:#1a6ef7; }
.inv-bulk-danger { border-color:rgba(220,38,38,.3); color:#dc2626; }
.inv-bulk-danger:hover { background:#fee2e2; border-color:#dc2626; }
.inv-bulk-clear { background:none; border:none; font-size:12.5px; color:#6b7280; cursor:pointer; font-family:inherit; padding:4px 8px; border-radius:4px; }
.inv-bulk-clear:hover { background:#e0e7ff; color:#1a6ef7; }

/* ══ Table ══ */
.inv-table-wrap { background:#fff; border:1px solid #e5e7eb; border-radius:10px; overflow:hidden; overflow-x:auto; }
.inv-table { width:100%; border-collapse:collapse; font-size:13px; }
.inv-table thead tr { background:#f8fafc; }
.inv-table th { padding:10px 14px; border-bottom:2px solid #e8ecf0; font-size:11px; font-weight:600; letter-spacing:normal; color:#6b7280; text-align:left; white-space:nowrap; background:#f9f9fb; user-select:none;}
.inv-table th.sortable { cursor:pointer; }
.inv-table th.sortable:hover { color:#1a6ef7; }
.th-check { width:36px; }
.sort-arrow { font-size:11px; color:#1a6ef7; margin-left:2px; }
.ta-r { text-align:right !important; }
.inv-row td { padding:11px 12px; border-bottom:1px solid #f0f2f5; vertical-align:middle; cursor:pointer; color:#374151; }
.inv-row:last-child td { border-bottom:none; }
.inv-row:hover td { background:#f8faff; }
.inv-row.selected td { background:#eaf1ff; }
.td-check { cursor:default !important; width:36px; }
.inv-link { font-family:monospace; font-size:12.5px; color:#1a6ef7; font-weight:700; }
.inv-customer { font-weight:600; color:#1a1a2e; }
.mono-sm { font-family:monospace; font-size:12.5px; }
.text-muted { color:#9ca3af; }
.text-danger { color:#dc2626; font-weight:600; }
.text-success { color:#059669; font-weight:600; }

/* ══ Status badges ══ */
.inv-status-badge { display:inline-flex; align-items:center; padding:3px 9px; border-radius:12px; font-size:11px; font-weight:700; letter-spacing:.03em; white-space:nowrap; }
.so-bdg-grey   { background:#f3f4f6; color:#6b7280; }
.so-bdg-blue   { background:#dbeafe; color:#1a6ef7; }
.so-bdg-green  { background:#d1fae5; color:#059669; }
.so-bdg-orange { background:#fef3c7; color:#d97706; }
.so-bdg-red    { background:#fee2e2; color:#dc2626; }
.so-badge-white { background:rgba(255,255,255,.2); color:#fff !important; border:1px solid rgba(255,255,255,.4); }

/* ══ Action buttons ══ */
.inv-act-btn { background:transparent; border:1px solid #e2e8f0; border-radius:6px; width:28px; height:28px; display:inline-flex; align-items:center; justify-content:center; cursor:pointer; color:#6b7280; }
.inv-act-btn:hover { background:#f3f4f6; color:#1a6ef7; border-color:#1a6ef7; }
.inv-act-conv { background:#eaf1ff; border-color:#1a6ef7; color:#1a6ef7; }
.inv-act-conv:hover { background:#dbeafe; }

/* ══ Shimmer skeleton ══ */
.shimmer-row td { padding:10px 12px; border-bottom:1px solid #f0f2f5; }
.shimmer { height:13px; border-radius:4px; background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%); background-size:200% 100%; animation:shimmer 1.2s infinite; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ══ Empty state ══ */
.empty-state { text-align:center; padding:56px 20px !important; cursor:default !important; color:#9ca3af; }
.empty-inner { display:flex; flex-direction:column; align-items:center; gap:8px; }
.empty-inner p { font-size:14px; color:#9ca3af; margin:0; }

/* ══ Shared button styles ══ */
.so-btn-ghost { display:inline-flex; align-items:center; gap:6px; background:transparent; border:1px solid #e2e8f0; border-radius:8px; padding:7px 12px; font-size:13px; color:#374151; cursor:pointer; font-family:inherit; }
.so-btn-ghost:hover { background:#f8fafc; }
.so-btn-save { display:inline-flex; align-items:center; gap:6px; background:#f0fdf4; border:1px solid #16a34a; color:#16a34a; border-radius:8px; padding:8px 14px; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit; }
.so-btn-save:hover { background:#dcfce7; }
.so-btn-save:disabled { opacity:.5; cursor:not-allowed; }
.so-btn-danger { display:inline-flex; align-items:center; gap:6px; background:#fef2f2; border:1px solid #dc2626; color:#dc2626; border-radius:8px; padding:8px 14px; font-size:13px; font-weight:600; cursor:pointer; font-family:inherit; }
.so-btn-danger:hover { background:#fee2e2; }

/* ══ Create / Edit Drawer ══ */
.so-drawer-bg { position:fixed; inset:0; z-index:8000; background:rgba(15,23,42,.45); display:flex; justify-content:flex-end; backdrop-filter:blur(2px); }
.so-drawer-panel { width:720px; max-width:96vw; height:100%; background:#fff; display:flex; flex-direction:column; box-shadow:-20px 0 60px rgba(0,0,0,.15); overflow:hidden; }

/* Blue gradient header */
.so-dh { display:flex; align-items:center; justify-content:space-between; padding:18px 24px; background:linear-gradient(135deg,#1e3a5f,#1a6ef7); flex-shrink:0; }
.so-dh-title { color:#fff; font-size:16px; font-weight:700; }
.so-dh-sub   { color:rgba(255,255,255,.75); font-size:12px; margin-top:2px; }
.so-dclose-new { background:rgba(255,255,255,.15); border:none; cursor:pointer; width:30px; height:30px; border-radius:8px; color:#fff; display:grid; place-items:center; }
.so-dclose-new:hover { background:rgba(255,255,255,.25); }

/* Body */
.so-dbody { flex:1; overflow-y:auto; padding:20px 24px; display:flex; flex-direction:column; }

/* Section labels */
.so-sec-lbl { font-size:10.5px; font-weight:700; letter-spacing:.6px; text-transform:uppercase; color:#9ca3af; margin-bottom:12px; margin-top:4px; padding-top:16px; border-top:1px solid #f0f2f5; display:block; }
.so-sec-lbl:first-child { border-top:none; padding-top:0; margin-top:0; }
.so-fg { display:grid; gap:12px; margin-bottom:14px; }
.so-fg2 { grid-template-columns:1fr 1fr; }
.so-fg3 { grid-template-columns:1fr 1fr 1fr; }
.so-lbl { display:block; font-size:11.5px; font-weight:600; color:#495057; margin-bottom:5px; }
.so-inv-block { border-radius:10px; padding:14px 16px; display:flex; flex-direction:column; gap:10px; border:1.5px solid #e5e7eb; background:#f9fafb; transition:border-color .2s,background .2s; }
.so-inv-block.so-wh-on { background:#eff6ff; border-color:#93c5fd; }
.so-inv-toggle-row { display:flex; align-items:center; gap:12px; }
.so-inv-icon { width:32px; height:32px; border-radius:8px; background:#dbeafe; color:#2563eb; display:flex; align-items:center; justify-content:center; flex-shrink:0; }
.so-inv-block.so-wh-off .so-inv-icon { background:#f3f4f6; color:#9ca3af; }
.so-inv-text { flex:1; }
.so-inv-title { font-size:13px; font-weight:700; color:#111827; }
.so-inv-sub { font-size:11.5px; color:#6b7280; margin-top:2px; line-height:1.4; }
.so-req { color:#dc2626; }
.so-fi { width:100%; border:1px solid #e2e8f0; border-radius:6px; padding:7px 10px; font-size:13px; font-family:inherit; outline:none; box-sizing:border-box; }
.so-fi:focus { border-color:#1a6ef7; box-shadow:0 0 0 3px rgba(26,110,247,.08); }
textarea.so-fi { resize:vertical; }

/* Add item button */
.so-add-item-btn { display:inline-flex; align-items:center; gap:5px; border:1px solid rgba(26,110,247,.3); background:#eaf1ff; color:#1a6ef7; border-radius:6px; padding:4px 12px; font-size:12px; font-weight:600; cursor:pointer; }
.so-add-item-btn:hover { background:#dbeafe; }

/* Line items grid */
.so-lines-wrap { border:1px solid #e8ecf0; border-radius:8px; overflow:visible; margin-bottom:0; }
.so-lines-head { display:grid; grid-template-columns:2fr 2fr 0.7fr 0.9fr 0.9fr 30px; gap:6px; padding:7px 10px; background:#f8fafc; border-bottom:1px solid #e8ecf0; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; }
.so-lines-row { display:grid; grid-template-columns:2fr 2fr 0.7fr 0.9fr 0.9fr 30px; gap:6px; padding:5px 10px; border-bottom:1px solid #f0f2f5; align-items:center; }
.so-lines-row:last-of-type { border-bottom:none; }
.so-lines-empty { padding:16px; text-align:center; color:#9ca3af; font-size:13px; border-bottom:1px solid #f0f2f5; }
.so-ci { width:100%; border:1px solid #e2e8f0; border-radius:5px; padding:5px 7px; font-size:12.5px; font-family:inherit; outline:none; box-sizing:border-box; }
.so-ci:focus { border-color:#1a6ef7; box-shadow:0 0 0 2px rgba(26,110,247,.08); }
.so-ci-r { text-align:right; }
.so-rm-line { background:none; border:1px solid rgba(220,38,38,.3); border-radius:4px; padding:3px 5px; cursor:pointer; color:#dc2626; display:inline-flex; align-items:center; flex-shrink:0; }
.so-rm-line:hover { background:#fee2e2; }
.so-add-line-btn { display:inline-flex; align-items:center; gap:5px; border:none; background:transparent; color:#1a6ef7; font-size:12.5px; font-weight:600; cursor:pointer; padding:8px 12px; width:100%; }
.so-add-line-btn:hover { background:#f0f7ff; }

/* Totals section */
.so-totals-wrap { border-top:1px solid #e8ecf0; padding:12px 14px; background:#f8fafc; display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap; margin-top:0; }
.so-tax-section { flex:1; min-width:240px; }
.so-tax-header { display:flex; align-items:center; gap:10px; margin-bottom:8px; }
.so-tax-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; }
.so-totals-right-panel { min-width:240px; display:flex; flex-direction:column; gap:5px; align-items:flex-end; }
.so-total-row-item { display:flex; justify-content:space-between; align-items:center; width:240px; font-size:13px; color:#374151; }
.so-total-amt { font-family:monospace; font-weight:600; font-size:13px; }
.so-grand-total { border-top:1px solid #e8ecf0; padding-top:7px; margin-top:2px; font-weight:700; }

/* Footer */
.so-dfooter-new { padding:14px 24px; border-top:1px solid #e8ecf0; display:flex; justify-content:space-between; align-items:center; background:#f8fafc; flex-shrink:0; }

/* ══ View Drawer ══ */
.so-overlay { position:fixed; inset:0; background:rgba(15,23,42,.45); z-index:7900; backdrop-filter:blur(2px); }
.so-view-drawer-panel { position:fixed; top:0; right:-560px; bottom:0; width:560px; max-width:96vw; background:#fff; display:flex; flex-direction:column; box-shadow:-20px 0 60px rgba(0,0,0,.15); z-index:7950; transition:right .22s ease; overflow:hidden; }
.so-view-drawer-panel.open { right:0; }

.so-view-head { position:relative; display:flex; align-items:flex-start; justify-content:space-between; padding:20px 24px; flex-shrink:0; color:#fff; }
.so-view-num { font-size:18px; font-weight:700; font-family:monospace; color:#fff; }
.so-view-sub { font-size:13px; color:rgba(255,255,255,.8); margin-top:2px; }
.so-view-amount { font-size:22px; font-weight:800; font-family:monospace; color:#fff; }
.so-dclose-view { position:absolute; top:12px; right:12px; background:rgba(255,255,255,.15); border:none; cursor:pointer; width:30px; height:30px; border-radius:8px; color:#fff; display:grid; place-items:center; }
.so-dclose-view:hover { background:rgba(255,255,255,.25); }

.so-tabs { display:flex; gap:4px; padding:0 20px; border-bottom:1px solid #e8ecf0; flex-shrink:0; background:#fff; }
.so-tab { background:transparent; border:none; padding:10px 14px; font:inherit; font-size:12.5px; font-weight:600; color:#6b7280; cursor:pointer; border-bottom:2px solid transparent; display:inline-flex; align-items:center; gap:6px; }
.so-tab:hover { color:#1a6ef7; }
.so-tab.active { color:#1a6ef7; border-bottom-color:#1a6ef7; }
.so-tab-count { background:#1a6ef7; color:#fff; padding:1px 7px; border-radius:999px; font-size:11px; font-weight:700; }

.so-vbody { flex:1; overflow-y:auto; padding:20px 24px; display:flex; flex-direction:column; gap:14px; }
.so-vfooter { display:flex; align-items:center; justify-content:flex-end; gap:8px; padding:14px 20px; border-top:1px solid #e8ecf0; flex-shrink:0; flex-wrap:wrap; background:#f8fafc; }

.so-meta-grid { display:grid; grid-template-columns:1fr 1fr; gap:14px; }
.so-meta-lbl { font-size:11px; color:#9ca3af; text-transform:uppercase; letter-spacing:.05em; margin-bottom:2px; }
.so-section-title { font-size:10.5px; font-weight:700; color:#9ca3af; text-transform:uppercase; letter-spacing:.6px; padding-bottom:6px; border-bottom:1px solid #f0f2f5; margin-top:4px; }

.so-view-items { display:flex; flex-direction:column; border:1px solid #e8ecf0; border-radius:6px; }
.so-view-items-head { display:grid; grid-template-columns:2.5fr 70px 90px 100px; gap:8px; background:#f8fafc; padding:8px 12px; font-size:11px; font-weight:700; color:#9ca3af; text-transform:uppercase; }
.so-view-items-row { display:grid; grid-template-columns:2.5fr 70px 90px 100px; gap:8px; padding:10px 12px; border-top:1px solid #f3f4f6; align-items:center; font-size:13px; color:#111827; background:#fff; }
.so-view-items-row:hover { background:#f8faff; }
.so-view-items-row strong { color:#1a1a2e; font-weight:600; }

.so-terms { padding:10px 12px; background:#f8fafc; border-radius:6px; color:#374151; }

.so-fulfill-tbl { display:flex; flex-direction:column; border:1px solid #e8ecf0; border-radius:6px; overflow:hidden; }
.so-fulfill-head { display:grid; grid-template-columns:2fr 80px 100px 90px 110px; gap:8px; background:#f8fafc; padding:8px 12px; font-size:11px; font-weight:700; color:#9ca3af; text-transform:uppercase; }
.so-fulfill-row { display:grid; grid-template-columns:2fr 80px 100px 90px 110px; gap:8px; padding:8px 12px; border-top:1px solid #f3f4f6; align-items:center; font-size:12.5px; }

.so-link-row { display:grid; grid-template-columns:1fr 1fr 1fr 1fr; gap:8px; padding:8px 12px; border:1px solid #e8ecf0; border-radius:6px; font-size:12.5px; align-items:center; background:#fff; color:#111827; }

/* ══ Invoice modal ══ */
.so-inv-dialog { position:fixed; top:50%; left:50%; transform:translate(-50%,-50%); width:520px; max-width:96vw; background:#fff; border-radius:12px; box-shadow:0 12px 40px rgba(0,0,0,.2); z-index:8100; display:flex; flex-direction:column; overflow:hidden; }
.so-inv-tbl { display:flex; flex-direction:column; border:1px solid #e8ecf0; border-radius:6px; overflow:hidden; }
.so-inv-head { display:grid; grid-template-columns:2fr 100px 110px; gap:8px; background:#f8fafc; padding:8px 12px; font-size:11px; font-weight:700; color:#9ca3af; text-transform:uppercase; }
.so-inv-row { display:grid; grid-template-columns:2fr 100px 110px; gap:8px; padding:8px 12px; border-top:1px solid #f3f4f6; align-items:center; font-size:12.5px; }

/* ══ Inline timeline ══ */
.so-timeline { display:flex; align-items:center; padding:14px 20px; background:#fff; border-bottom:1px solid #e8ecf0; flex-shrink:0; }
.so-tl-step { display:flex; align-items:center; gap:6px; flex-shrink:0; }
.so-tl-dot { width:22px; height:22px; border-radius:50%; border:2px solid #d1d5db; background:#fff; display:flex; align-items:center; justify-content:center; font-size:10px; color:#9ca3af; flex-shrink:0; transition:all .2s; }
.so-tl-step.done .so-tl-dot { background:#059669; border-color:#059669; color:#fff; }
.so-tl-step.danger .so-tl-dot { background:#dc2626; border-color:#dc2626; color:#fff; }
.so-tl-step.current:not(.done):not(.danger) .so-tl-dot { border-color:#1a6ef7; color:#1a6ef7; }
.so-tl-label { font-size:11px; font-weight:600; color:#9ca3af; white-space:nowrap; }
.so-tl-step.done .so-tl-label { color:#059669; }
.so-tl-step.danger .so-tl-label { color:#dc2626; }
.so-tl-step.current:not(.done):not(.danger) .so-tl-label { color:#1a6ef7; }
.so-tl-line { flex:1; height:2px; background:#e5e7eb; min-width:16px; }
.so-tl-line.done { background:#059669; }
.so-tl-line.danger { background:#dc2626; }
</style>