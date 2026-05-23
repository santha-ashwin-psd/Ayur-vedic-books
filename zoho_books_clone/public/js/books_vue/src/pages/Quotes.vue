<template>
  <div class="qt-page">

    <!-- ── Toolbar ── -->
    <div class="qt-actions">
      <div class="qt-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search quotes, customers…" class="qt-search-input" />
      </div>
      <div class="qt-pills">
        <button v-for="t in tabs" :key="t.key"
          class="qt-pill" :class="{active:activeTab===t.key}"
          @click="activeTab=t.key">
          {{ t.label }}
          <span v-if="t.key!=='all'" class="qt-pill-count">{{ counts[t.key] }}</span>
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="qt-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
        <button class="qt-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',14)"></span> CSV</button>
        <button class="qt-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Quotation
        </button>
      </div>
    </div>

    <!-- ── Summary strip ── -->
    <SummaryStrip :cards="[
      { label: 'Total Quotes', value: list.length },
      { label: 'Sent',     value: counts.sent,     accent: '#1a6ef7' },
      { label: 'Accepted', value: counts.accepted, accent: '#16a34a' },
      { label: 'Expired',  value: counts.expired,  accent: '#dc2626' },
    ]" />

    <!-- ── Bulk action bar ── -->
    <BulkActionBar :count="selected.size" @clear="selected=new Set()">
      <button @click="bulkEmail"><span v-html="icon('mail',13)"></span> Send Email</button>
      <button @click="bulkMarkSent">Mark as Sent</button>
      <button @click="bulkMarkExpired">Mark Expired</button>
      <button class="bab-danger" @click="bulkDelete">Delete Drafts</button>
      <button @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
    </BulkActionBar>

    <!-- ── Table ── -->
    <div class="qt-card">
      <table class="qt-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" @change="toggleAll" :checked="allChecked" /></th>
            <th @click="sortBy('name')" class="sortable">Quote # <span v-html="sortArrow('name')"></span></th>
            <th @click="sortBy('customer_name')" class="sortable">Customer <span v-html="sortArrow('customer_name')"></span></th>
            <th @click="sortBy('transaction_date')" class="sortable">Date <span v-html="sortArrow('transaction_date')"></span></th>
            <th @click="sortBy('valid_till')" class="sortable">Valid Till <span v-html="sortArrow('valid_till')"></span></th>
            <th>Status</th>
            <th @click="sortBy('grand_total')" class="sortable ta-r">Amount <span v-html="sortArrow('grand_total')"></span></th>
            <th style="width:120px;text-align:center">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="8"><div class="qt-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="q in sorted" :key="q.name" class="qt-row" :class="{selected:selected.has(q.name)}">
              <td><input type="checkbox" :checked="selected.has(q.name)" @change="toggle(q.name)" /></td>
              <td @click="openView(q)"><span class="qt-num">{{ q.name }}</span></td>
              <td @click="openView(q)">{{ q.customer_name || q.customer || '—' }}</td>
              <td @click="openView(q)" class="text-muted mono-sm">{{ fmtDate(q.transaction_date) }}</td>
              <td @click="openView(q)" :class="isExpired(q)?'text-danger':'text-muted'" class="mono-sm">{{ fmtDate(q.valid_till)||'—' }}</td>
              <td @click="openView(q)"><span class="qt-badge" :class="badgeClass(q)">{{ displayStatus(q) }}</span></td>
              <td @click="openView(q)" class="ta-r mono-sm">{{ fmtCur(q.grand_total) }}</td>
              <td class="qt-act-cell">
                <button class="qt-act-btn" @click="openView(q)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button class="qt-act-btn" @click="openEdit(q)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button class="qt-act-btn qt-act-conv" v-if="canConvert(q)" @click="openConvertModal(q)" title="Convert"><span v-html="icon('arrow-right',13)"></span></button>
                <button class="qt-act-btn qt-act-del" @click="deleteQT(q)" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="8" class="qt-empty">No quotations match</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Create / Edit Drawer ── -->
    <div v-if="drawerOpen" class="qt-drawer-bg" @click.self="drawerOpen=false">
      <div class="qt-drawer-panel" :class="{'qt-split':showPreview}">

        <!-- Header -->
        <div class="qt-dh">
          <div>
            <div class="qt-dh-title">{{ editingName ? 'Edit Quotation' : 'New Quotation' }}</div>
            <div class="qt-dh-sub">{{ editingName || 'Fill in the details below' }}</div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <button class="qt-preview-toggle" @click="showPreview=!showPreview" :title="showPreview?'Hide preview':'Live preview'">
              <span v-html="icon('eye',13)"></span> {{ showPreview ? 'Hide' : 'Preview' }}
            </button>
            <button class="qt-dclose-new" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
          </div>
        </div>

        <!-- Template / branding toolbar -->
        <div class="qt-tmpl-bar">
          <div class="qt-tmpl-group">
            <span class="qt-tmpl-lbl">Template</span>
            <div class="qt-tmpl-btns">
              <button v-for="t in TEMPLATES" :key="t.key" class="qt-tmpl-btn" :class="{active:selectedTemplate===t.key}" @click="selectedTemplate=t.key">{{ t.label }}</button>
            </div>
          </div>
          <label class="qt-tmpl-group">
            <span class="qt-tmpl-lbl">Brand Color</span>
            <div style="display:flex;align-items:center;gap:6px">
              <input type="color" v-model="brandColor" class="qt-color-pick"/>
              <span class="qt-color-val">{{ brandColor }}</span>
            </div>
          </label>
          <div class="qt-tmpl-group" style="flex:1">
            <span class="qt-tmpl-lbl">Logo URL</span>
            <input v-model="logoUrl" class="qt-logo-input" placeholder="https://yoursite.com/logo.png"/>
          </div>
        </div>

        <!-- Content row: form + optional preview -->
        <div class="qt-content-row">
        <div class="qt-dbody">

        <!-- Quote Details section -->
        <div class="qt-sec-lbl">Quote Details</div>
        <div class="qt-fg qt-fg3">
          <div style="grid-column:1/3">
            <label class="qt-lbl">Customer <span class="qt-req">*</span></label>
            <SearchableSelect v-model="form.customer" :options="customers" placeholder="Select customer"
              :createable="true" createDoctype="Customer"
              @search="fetchCustomers" />
          </div>
          <div>
            <label class="qt-lbl">Quote Date <span class="qt-req">*</span></label>
            <input v-model="form.transaction_date" type="date" class="qt-fi"/>
          </div>
          <div>
            <label class="qt-lbl">Valid Till</label>
            <input v-model="form.valid_till" type="date" class="qt-fi"/>
          </div>
          <div>
            <label class="qt-lbl">Currency</label>
            <select v-model="form.currency" class="qt-fi">
              <option v-for="(sym,code) in CURRENCY_SYMBOLS" :key="code" :value="code">{{ code }} {{ sym }}</option>
            </select>
          </div>
          <div style="grid-column:1/-1">
            <label class="qt-lbl">Title / Project</label>
            <input v-model="form.title" type="text" class="qt-fi" placeholder="Project name or short description"/>
          </div>
        </div>

        <!-- Billing Address -->
        <div class="qt-sec-lbl">Billing Address</div>
        <div class="qt-fg" style="margin-bottom:14px">
          <div>
            <label class="qt-lbl">Address</label>
            <textarea v-model="form.billing_address" class="qt-fi" rows="2" style="resize:vertical" placeholder="Auto-filled from customer, or enter manually"></textarea>
          </div>
        </div>

        <!-- Line Items -->
        <div class="qt-sec-lbl" style="display:flex;align-items:center;justify-content:space-between;border-top:1px solid #f0f2f5;padding-top:16px;margin-top:4px">
          LINE ITEMS
          <button class="qt-add-item-btn" @click.prevent="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <div class="qt-lines-wrap">
          <!-- Column headers -->
          <div class="qt-lines-head">
            <div>ITEM <span class="qt-req">*</span></div>
            <div>DESCRIPTION</div>
            <div>HSN/SAC</div>
            <div class="ta-r">QTY</div>
            <div>UOM</div>
            <div class="ta-r">RATE (₹)</div>
            <div class="ta-r">DISC %</div>
            <div class="ta-r">AMOUNT</div>
            <div></div>
          </div>

          <!-- Line rows -->
          <div v-for="line in lines" :key="line.id" class="qt-lines-row">
            <div style="min-width:0">
              <SearchableSelect v-model="line.item_code" :options="items" placeholder="Item…"
                :createable="true" createDoctype="Item"
                @search="fetchItems" @select="opt => onItemSelect(line, opt)"/>
            </div>
            <div><input v-model="line.description" class="qt-ci" placeholder="Description"/></div>
            <div><input v-model="line.hsn_code" class="qt-ci" placeholder="HSN/SAC"/></div>
            <div><input v-model.number="line.qty" type="number" min="0" step="0.001" class="qt-ci qt-ci-r" @input="calcLine(line)"/></div>
            <div><input v-model="line.uom" class="qt-ci" placeholder="Nos"/></div>
            <div><input v-model.number="line.rate" type="number" min="0" step="0.01" class="qt-ci qt-ci-r" @input="calcLine(line)"/></div>
            <div><input v-model.number="line.discount_percentage" type="number" min="0" max="100" step="0.5" class="qt-ci qt-ci-r" @input="calcLine(line)"/></div>
            <div class="ta-r mono-sm" style="display:flex;align-items:center;justify-content:flex-end;font-weight:600;font-size:13px">{{ fmtCur(line.amount) }}</div>
            <div style="display:flex;align-items:center;justify-content:center">
              <button @click.prevent="removeLine(line.id)" class="qt-rm-line"><span v-html="icon('x',12)"></span></button>
            </div>
          </div>

          <div v-if="!lines.length" class="qt-lines-empty">No items yet — click <strong>Add Item</strong> to begin.</div>

          <button class="qt-add-line-btn" @click.prevent="addLine"><span v-html="icon('plus',12)"></span> Add Item</button>
        </div>

        <!-- Tax + Totals -->
        <div class="qt-totals-wrap">
          <div class="qt-tax-section">
            <div class="qt-tax-header">
              <span class="qt-tax-title">Taxes</span>
              <div class="qt-tax-presets">
                <button v-for="p in TAX_PRESETS" :key="p.label" class="qt-preset-btn" @click="applyTaxPreset(p)">{{ p.label }}</button>
                <button class="qt-preset-btn qt-preset-custom" @click="addTaxRow">+ Custom</button>
                <button v-if="taxRows.length" class="qt-preset-btn qt-preset-clear" @click="taxRows=[]">Clear</button>
              </div>
            </div>
            <table v-if="taxRows.length" class="qt-tax-tbl">
              <thead><tr><th>Description</th><th class="ta-r">Rate %</th><th class="ta-r">Amount</th><th></th></tr></thead>
              <tbody>
                <tr v-for="tx in taxRows" :key="tx.id">
                  <td><input v-model="tx.description" class="qt-ci" placeholder="e.g. CGST @ 9%"/></td>
                  <td><input v-model.number="tx.rate" type="number" min="0" max="100" step="0.5" class="qt-ci qt-ci-r" @input="recalcTax(tx)"/></td>
                  <td class="ta-r mono-sm">{{ fmtCur(tx.amount) }}</td>
                  <td><button @click="taxRows=taxRows.filter(r=>r.id!==tx.id)" class="qt-rm-line"><span v-html="icon('x',12)"></span></button></td>
                </tr>
              </tbody>
            </table>
            <div v-else style="font-size:12px;color:#9ca3af;padding:6px 0">No taxes — use preset buttons above or add a custom row.</div>
          </div>

          <div class="qt-totals-right-panel">
            <div class="qt-total-row-item">
              <span>Subtotal</span>
              <span class="qt-total-amt">{{ fmtCur(subtotal) }}</span>
            </div>
            <div v-for="tx in taxRows" :key="'tot-'+tx.id" class="qt-total-row-item" style="color:#6b7280;font-size:12px">
              <span>{{ tx.description || 'Tax' }}</span>
              <span class="qt-total-amt">{{ fmtCur(tx.amount) }}</span>
            </div>
            <div class="qt-total-row-item qt-grand-total">
              <span>Grand Total</span>
              <span class="qt-total-amt" style="font-size:16px;color:#1a6ef7">{{ fmtCur(grandTotal) }}</span>
            </div>
          </div>
        </div>

        <!-- Notes & Terms -->
        <div class="qt-sec-lbl">Notes & Terms</div>
        <div class="qt-fg qt-fg2" style="margin-bottom:14px">
          <div>
            <label class="qt-lbl">Terms & Conditions <span style="color:#9ca3af;font-weight:400">(printed on quote)</span></label>
            <textarea v-model="form.terms" rows="3" class="qt-fi" style="resize:vertical" placeholder="Payment terms, delivery terms, validity…"></textarea>
          </div>
          <div>
            <label class="qt-lbl">Internal Remarks <span style="color:#9ca3af;font-weight:400">(not printed)</span></label>
            <textarea v-model="form.remarks" rows="3" class="qt-fi" style="resize:vertical" placeholder="Internal notes for your team…"></textarea>
          </div>
        </div>

        </div><!-- /qt-dbody -->

          <!-- Live preview pane -->
          <div v-if="showPreview" class="qt-preview-pane">
            <div class="qt-preview-toolbar">
              <span style="font-size:11px;font-weight:700;letter-spacing:.05em;color:#6b7280">LIVE PREVIEW</span>
              <span style="font-size:11px;color:#9ca3af">{{ TEMPLATES.find(t=>t.key===selectedTemplate)?.label }}</span>
            </div>
            <div class="qt-preview-placeholder">
              <svg width="48" height="48" fill="none" stroke="#d1d5db" stroke-width="1.5" viewBox="0 0 24 24"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M7 8h10M7 12h10M7 16h6"/></svg>
              <p style="color:#9ca3af;font-size:13px;margin:8px 0 0">Preview coming soon</p>
            </div>
          </div>

        </div><!-- /qt-content-row -->

        <div class="qt-dfooter-new">
          <div style="font-size:12px;color:#9ca3af">{{ editingName ? 'Editing: '+editingName : 'New quotation' }}</div>
          <div style="display:flex;gap:10px">
            <button class="qt-btn-ghost" @click="drawerOpen=false">Cancel</button>
            <button class="qt-btn-ghost" style="border-color:#3b82f6;color:#3b82f6" :disabled="drawerSaving" @click="saveQT('Draft')">Save Draft</button>
            <button class="qt-btn-primary" :disabled="drawerSaving" @click="saveQT('Sent')">
              <span v-html="icon('check',13)"></span> {{ drawerSaving ? 'Saving…' : 'Submit Quote' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen" class="qt-overlay" @click.self="viewOpen=false"></div>
    <div class="qt-drawer qt-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="qt-view-head" :style="`background:${headerBg(viewDoc)}`">
          <div>
            <div class="qt-view-num">{{ viewDoc.name }}</div>
            <div class="qt-view-sub">{{ viewDoc.customer_name||viewDoc.customer }}</div>
          </div>
          <div style="text-align:right">
            <div class="qt-view-amount">{{ fmtCur(viewDoc.grand_total) }}</div>
            <span class="qt-badge qt-badge-white">{{ displayStatus(viewDoc) }}</span>
          </div>
          <button class="qt-dclose qt-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <TimelineStepper :steps="timelineSteps" />

        <div class="qt-tabs">
          <button class="qt-tab" :class="{active:viewTab==='details'}" @click="viewTab='details'">Details</button>
          <button class="qt-tab" :class="{active:viewTab==='conversions'}" @click="viewTab='conversions'">
            Conversions<span v-if="(conv.sales_orders.length+conv.sales_invoices.length)>0" class="qt-tab-count">{{ conv.sales_orders.length + conv.sales_invoices.length }}</span>
          </button>
        </div>

        <div class="qt-dbody">
          <template v-if="viewTab==='details'">
            <div class="qt-meta-grid">
              <div><div class="qt-meta-lbl">Date</div><div class="mono-sm">{{ fmtDate(viewDoc.transaction_date) }}</div></div>
              <div><div class="qt-meta-lbl">Valid Till</div>
                <div class="mono-sm" :class="isExpired(viewDoc)?'text-danger':''">{{ fmtDate(viewDoc.valid_till)||'—' }}</div>
              </div>
              <div><div class="qt-meta-lbl">Status</div><div class="mono-sm">{{ displayStatus(viewDoc) }}</div></div>
              <div><div class="qt-meta-lbl">Title</div><div>{{ viewDoc.title||'—' }}</div></div>
            </div>

            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else-if="viewItems.length">
              <div class="qt-section-title">Line Items</div>
              <div class="qt-view-items">
                <div class="qt-view-items-head"><span>Item</span><span class="ta-r">Qty</span><span class="ta-r">Rate</span><span class="ta-r">Amount</span></div>
                <div v-for="it in viewItems" :key="it.name" class="qt-view-items-row">
                  <span><strong>{{ it.item_name||it.item_code }}</strong>
                    <div v-if="it.description" class="text-muted" style="font-size:11px">{{ it.description }}</div></span>
                  <span class="ta-r mono-sm">{{ it.qty }}</span>
                  <span class="ta-r mono-sm">{{ fmtCur(it.rate) }}</span>
                  <span class="ta-r mono-sm" style="font-weight:600">{{ fmtCur(it.amount) }}</span>
                </div>
              </div>
            </template>
            <div v-if="viewDoc.terms" class="qt-terms">
              <div class="qt-meta-lbl">Terms & Conditions</div>
              <div style="white-space:pre-wrap;font-size:12.5px;color:#374151">{{ viewDoc.terms }}</div>
            </div>
          </template>

          <template v-if="viewTab==='conversions'">
            <div v-if="viewLoading" style="text-align:center;padding:24px;color:#6b7280;font-size:13px">Loading…</div>
            <template v-else>
              <div v-if="conv.sales_orders.length" class="qt-section-title">Sales Orders</div>
              <div v-for="so in conv.sales_orders" :key="so.name" class="qt-conv-row">
                <span class="qt-num">{{ so.name }}</span>
                <span class="text-muted">{{ fmtDate(so.transaction_date) }}</span>
                <span style="text-align:right;font-weight:600">{{ fmtCur(so.grand_total) }}</span>
              </div>
              <div v-if="conv.sales_invoices.length" class="qt-section-title">Sales Invoices</div>
              <div v-for="si in conv.sales_invoices" :key="si.name" class="qt-conv-row">
                <span class="qt-num">{{ si.name }}</span>
                <span class="text-muted">{{ fmtDate(si.posting_date) }}</span>
                <span style="text-align:right;font-weight:600">{{ fmtCur(si.grand_total) }}</span>
              </div>
              <div v-if="!conv.sales_orders.length && !conv.sales_invoices.length"
                style="text-align:center;padding:24px;color:#9ca3af;font-size:13px">
                Not converted yet.
                <div v-if="canConvert(viewDoc)" style="margin-top:8px">
                  <button class="qt-btn-primary" @click="openConvertModal(viewDoc)" style="font-size:12px;padding:6px 12px">Convert →</button>
                </div>
              </div>
            </template>
          </template>
        </div>

        <div class="qt-dfooter">
          <button class="qt-btn-ghost" @click="viewOpen=false">Close</button>
          <button class="qt-btn-save" @click="openEdit(viewDoc);viewOpen=false">
            <span v-html="icon('edit',13)"></span> Edit
          </button>
          <button class="qt-btn-ghost" @click="emailQT(viewDoc)">
            <span v-html="icon('mail',13)"></span> Email
          </button>
          <button class="qt-btn-ghost" @click="printQT(viewDoc)" title="Print preview">
            🖨 Print
          </button>
          <button v-if="viewDoc.status!=='Accepted' && viewDoc.status!=='Converted'" class="qt-btn-ghost" @click="markStatus(viewDoc,'Accepted')">✓ Accept</button>
          <button v-if="viewDoc.status!=='Declined' && viewDoc.status!=='Converted'" class="qt-btn-ghost" @click="markStatus(viewDoc,'Declined')">✕ Decline</button>
          <button v-if="canConvert(viewDoc)" class="qt-btn-primary" @click="openConvertModal(viewDoc)">Convert →</button>
          <button class="qt-btn-danger" @click="deleteQT(viewDoc)">Delete</button>
        </div>
      </template>
    </div>

    <!-- ── Convert modal ── -->
    <div v-if="convertModal.open" class="qt-overlay" @click.self="convertModal.open=false" style="z-index:60"></div>
    <div v-if="convertModal.open" class="qt-apply-dialog">
      <div class="qt-dheader" style="background:linear-gradient(135deg,#1e3a5f,#1a6ef7);color:#fff;height:auto;padding:14px 18px">
        <div style="color:#fff;font-weight:700">Convert Quotation — {{ convertModal.qtName }}</div>
        <button class="qt-dclose" style="color:#fff" @click="convertModal.open=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="qt-dbody">
        <div style="font-size:13px;color:#374151;margin-bottom:8px">Choose how to convert this quote:</div>
        <div class="qt-convert-options">
          <button class="qt-convert-card" @click="convertModal.target='SO'" :class="{active:convertModal.target==='SO'}">
            <div class="qt-convert-icon" style="background:#dcfce7;color:#16a34a">SO</div>
            <div>
              <div style="font-weight:700">Sales Order</div>
              <div style="font-size:11.5px;color:#6b7280">Track fulfillment + delivery separately</div>
            </div>
          </button>
          <button class="qt-convert-card" @click="convertModal.target='Invoice'" :class="{active:convertModal.target==='Invoice'}">
            <div class="qt-convert-icon" style="background:#dbeafe;color:#1a6ef7">$</div>
            <div>
              <div style="font-weight:700">Sales Invoice</div>
              <div style="font-size:11.5px;color:#6b7280">Bill the customer immediately</div>
            </div>
          </button>
        </div>
        <div v-if="convertModal.target==='SO'" class="qt-field" style="margin-top:12px">
          <label class="qt-label">Delivery Date</label>
          <input v-model="convertModal.deliveryDate" type="date" class="qt-input" />
        </div>
        <div v-if="convertModal.target==='Invoice'" class="qt-field" style="margin-top:12px">
          <label class="qt-label">Due Date</label>
          <input v-model="convertModal.dueDate" type="date" class="qt-input" />
        </div>
      </div>
      <div class="qt-dfooter">
        <button class="qt-btn-ghost" @click="convertModal.open=false" :disabled="convertModal.saving">Cancel</button>
        <button class="qt-btn-primary" :disabled="convertModal.saving||!convertModal.target" @click="submitConvert">
          {{ convertModal.saving ? 'Converting…' : (convertModal.target ? `Convert to ${convertModal.target==='SO' ? 'Sales Order' : 'Invoice'}` : 'Choose target') }}
        </button>
      </div>
    </div>

  </div>
</template>
<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { apiList, apiSave, apiGet, apiGET, apiPOST, apiDelete, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useEmailDialog } from "../composables/useEmailDialog.js";
import { useConfirm } from "../composables/useConfirm.js";
import { useLivePreview } from "../composables/useLivePreview.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import BulkActionBar from "../components/BulkActionBar.vue";
import TimelineStepper from "../components/TimelineStepper.vue";

const { toast } = useToast();
const { confirm } = useConfirm();
const { printDoc } = useLivePreview();
function printQT(d) {
  printDoc(d, {
    title: "QUOTATION",
    partyLabel: "Customer",
    partyField: "customer_name",
    companyName: d?.company || "",
  });
}
const { openEmail } = useEmailDialog();

// ── Tabs ──────────────────────────────────────────────────────────────
const activeTab = ref("all");
const tabs = [
  { key: "all",       label: "All" },
  { key: "draft",     label: "Draft" },
  { key: "sent",      label: "Sent" },
  { key: "accepted",  label: "Accepted" },
  { key: "declined",  label: "Declined" },
  { key: "expired",   label: "Expired" },
  { key: "converted", label: "Converted" },
];

// ── Templates & branding (mirrors Invoice) ───────────────────────────
const TEMPLATES = [
  { key: "classic", label: "Classic" },
  { key: "modern",  label: "Modern"  },
  { key: "minimal", label: "Minimal" },
];
const CURRENCY_SYMBOLS = {
  INR: "₹", USD: "$", EUR: "€", GBP: "£", AED: "د.إ", SGD: "S$", AUD: "A$", CAD: "C$",
};

// ── Tax presets — exactly like Invoice ───────────────────────────────
const TAX_PRESETS = [
  { label: "GST 5%",   rows: [{ desc: "CGST @ 2.5%", rate: 2.5 }, { desc: "SGST @ 2.5%", rate: 2.5 }] },
  { label: "GST 12%",  rows: [{ desc: "CGST @ 6%",   rate: 6   }, { desc: "SGST @ 6%",   rate: 6   }] },
  { label: "GST 18%",  rows: [{ desc: "CGST @ 9%",   rate: 9   }, { desc: "SGST @ 9%",   rate: 9   }] },
  { label: "GST 28%",  rows: [{ desc: "CGST @ 14%",  rate: 14  }, { desc: "SGST @ 14%",  rate: 14  }] },
  { label: "IGST 5%",  rows: [{ desc: "IGST @ 5%",   rate: 5   }] },
  { label: "IGST 12%", rows: [{ desc: "IGST @ 12%",  rate: 12  }] },
  { label: "IGST 18%", rows: [{ desc: "IGST @ 18%",  rate: 18  }] },
  { label: "IGST 28%", rows: [{ desc: "IGST @ 28%",  rate: 28  }] },
];

// ── State ─────────────────────────────────────────────────────────────
const list        = ref([]);
const loading     = ref(false);
const search      = ref("");
const selected    = ref(new Set());
const showPreview     = ref(false);
const selectedTemplate = ref("modern");
const brandColor      = ref("#1a6ef7");
const logoUrl         = ref("");
const drawerOpen  = ref(false);
const drawerSaving = ref(false);
const editingName = ref("");
const viewOpen    = ref(false);
const viewDoc     = ref(null);
const viewTab     = ref("details");
const viewLoading = ref(false);
const viewItems   = ref([]);
const conv        = reactive({ sales_orders: [], sales_invoices: [] });
const customers   = ref([]);
const items       = ref([]);
const lines       = ref([]);
const taxRows     = ref([]);          // ← replaces single tax_rate
const taxAccountHead = ref("");
const sortCol     = ref("transaction_date");
const sortDir     = ref("desc");

const convertModal = reactive({
  open: false, saving: false, qtName: "",
  target: "", deliveryDate: "", dueDate: "",
});

// ── Helpers ───────────────────────────────────────────────────────────
function todayStr() { return new Date().toISOString().slice(0, 10); }
function validTillDefault() {
  const d = new Date(); d.setDate(d.getDate() + 30);
  return d.toISOString().slice(0, 10);
}
function fmtCur(v) {
  return new Intl.NumberFormat("en-IN", {
    style: "currency", currency: "INR", minimumFractionDigits: 2,
  }).format(flt(v));
}

// ── Form ──────────────────────────────────────────────────────────────
const form = reactive({
  customer: "",
  transaction_date: todayStr(),
  valid_till: validTillDefault(),
  title: "",
  terms: "",
  remarks: "",
  billing_address: "",
  currency: "INR",
});

// ── Blank line — matches Invoice exactly ─────────────────────────────
let _id = 1;
function blankLine() {
  return {
    id: _id++,
    item_code: "",
    item_name: "",
    description: "",
    hsn_code: "",
    qty: 1,
    rate: 0,
    uom: "Nos",
    discount_percentage: 0,
    discount_amount: 0,
    amount: 0,
  };
}

// ── Status helpers ────────────────────────────────────────────────────
function isExpired(q) {
  if (!q?.valid_till) return false;
  if (q.status === "Converted" || q.status === "Accepted") return false;
  return new Date(q.valid_till) < new Date();
}
function effectiveStatus(q) {
  if (
    q?.status === "Converted" || q?.status === "Accepted" ||
    q?.status === "Declined"  || q?.status === "Lost"
  ) return q.status;
  if (isExpired(q)) return "Expired";
  return q?.status || "Draft";
}
function displayStatus(q) { return effectiveStatus(q).toUpperCase(); }
function badgeClass(q) {
  const s = effectiveStatus(q);
  if (s === "Draft")                         return "qt-bdg-grey";
  if (s === "Sent")                          return "qt-bdg-blue";
  if (s === "Accepted")                      return "qt-bdg-green";
  if (s === "Converted")                     return "qt-bdg-purple";
  if (s === "Declined" || s === "Lost")      return "qt-bdg-red";
  if (s === "Expired")                       return "qt-bdg-red";
  return "qt-bdg-grey";
}
function headerBg(q) {
  const s = effectiveStatus(q);
  if (s === "Converted") return "linear-gradient(135deg,#581c87,#a855f7)";
  if (s === "Accepted")  return "linear-gradient(135deg,#064e3b,#059669)";
  if (s === "Declined" || s === "Lost" || s === "Expired")
    return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  if (s === "Sent")      return "linear-gradient(135deg,#1e3a5f,#1a6ef7)";
  return "linear-gradient(135deg,#374151,#6b7280)";
}
function canConvert(q) {
  const s = effectiveStatus(q);
  return s !== "Converted" && s !== "Declined" && s !== "Lost";
}

// ── Load list ─────────────────────────────────────────────────────────
async function load() {
  loading.value = true;
  try {
    const co = await resolveCompany();
    list.value = await apiList("Quotation", {
      fields: ["name","customer","customer_name","transaction_date",
               "valid_till","status","grand_total","title"],
      filters: [["company","=",co]],
      limit: 500,
      order: "transaction_date desc",
    });
  } catch (e) {
    toast.error(e.message || "Failed to load quotations");
  } finally {
    loading.value = false;
  }
}

async function loadTaxAccount() {
  try {
    const co = await resolveCompany();
    const r = await apiList("Account", {
      fields: ["name"],
      filters: [
        ["company",       "=", co],
        ["account_type",  "=", "Tax"],
        ["is_group",      "=", 0],
      ],
      limit: 1,
    });
    if (r?.length) taxAccountHead.value = r[0].name;
  } catch {}
}

// ── Counts & filters ──────────────────────────────────────────────────
const counts = computed(() => {
  const c = { draft:0, sent:0, accepted:0, declined:0, expired:0, converted:0 };
  for (const q of list.value) {
    const s = effectiveStatus(q).toLowerCase();
    if      (s === "draft")                   c.draft++;
    else if (s === "sent")                    c.sent++;
    else if (s === "accepted")                c.accepted++;
    else if (s === "converted")               c.converted++;
    else if (s === "declined" || s === "lost") c.declined++;
    else if (s === "expired")                 c.expired++;
  }
  return c;
});

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") {
    r = r.filter(q => {
      const s = effectiveStatus(q).toLowerCase();
      if (activeTab.value === "declined") return s === "declined" || s === "lost";
      return s === activeTab.value;
    });
  }
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x =>
      (x.name || "").toLowerCase().includes(q) ||
      (x.customer_name || x.customer || "").toLowerCase().includes(q) ||
      (x.title || "").toLowerCase().includes(q)
    );
  }
  return r;
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const av = a[col] ?? "", bv = b[col] ?? "";
    const c = typeof av === "number"
      ? av - bv
      : String(av).localeCompare(String(bv));
    return sortDir.value === "asc" ? c : -c;
  });
});

function sortBy(col) {
  if (sortCol.value === col)
    sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  else { sortCol.value = col; sortDir.value = "asc"; }
}
function sortArrow(col) {
  if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>';
  return sortDir.value === "asc" ? "↑" : "↓";
}

// ── Selection ─────────────────────────────────────────────────────────
const allChecked = computed(() =>
  sorted.value.length > 0 && sorted.value.every(q => selected.value.has(q.name))
);
function toggle(n) {
  const s = new Set(selected.value);
  s.has(n) ? s.delete(n) : s.add(n);
  selected.value = s;
}
function toggleAll(e) {
  selected.value = e.target.checked
    ? new Set(sorted.value.map(q => q.name))
    : new Set();
}

// ── Totals ────────────────────────────────────────────────────────────
const subtotal  = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const totalTax  = computed(() => taxRows.value.reduce((s, r) => s + flt(r.amount), 0));
const grandTotal = computed(() => subtotal.value + totalTax.value);

// Auto-recalc tax rows when subtotal changes — exactly like Invoice
watch(subtotal, () => {
  taxRows.value.forEach(r => {
    r.amount = Math.round(subtotal.value * flt(r.rate) / 100 * 100) / 100;
  });
});

// ── Timeline ──────────────────────────────────────────────────────────
const timelineSteps = computed(() => {
  const q = viewDoc.value;
  if (!q) return [];
  const s = effectiveStatus(q);
  if (s === "Declined" || s === "Lost") {
    return [
      { key: "draft", label: "Draft", done: true },
      { key: "sent",  label: "Sent",  done: true },
      { key: "end",   label: "Declined", danger: true, current: true },
    ];
  }
  if (s === "Expired") {
    return [
      { key: "draft", label: "Draft", done: true },
      { key: "sent",  label: "Sent",  done: true },
      { key: "end",   label: "Expired", danger: true, current: true },
    ];
  }
  return [
    { key: "draft",     label: "Draft",     done: true },
    { key: "sent",      label: "Sent",      done: s !== "Draft",     current: s === "Sent" },
    { key: "accepted",  label: "Accepted",  done: s === "Accepted" || s === "Converted", current: s === "Accepted" },
    { key: "converted", label: "Converted", done: s === "Converted", current: s === "Converted" },
  ];
});

// ── Fetch helpers ─────────────────────────────────────────────────────
async function fetchCustomers(q = "") {
  try {
    const f = [["disabled","=",0]];
    if (q) f.push(["customer_name","like","%" + q + "%"]);
    const r = await apiList("Customer", {
      fields: ["name","customer_name"], filters: f, limit: 30, order: "customer_name asc",
    });
    customers.value = r.map(x => ({ ...x, label: x.customer_name || x.name, value: x.name }));
  } catch { customers.value = []; }
}

async function fetchItems(q = "") {
  try {
    const f = [["disabled","=",0]];
    if (q) f.push(["item_name","like","%" + q + "%"]);
    const r = await apiList("Item", {
      fields: ["name","item_name","standard_rate","stock_uom"], filters: f, limit: 30, order: "item_name asc",
    });
    items.value = r.map(x => ({
      ...x,
      label: x.item_name || x.name,
      value: x.name,
      rate:  x.standard_rate || 0,
      uom:   x.stock_uom || "Nos",
    }));
  } catch { items.value = []; }
}

// ── Line item helpers — mirrors Invoice exactly ───────────────────────
function addLine() {
  lines.value.push(blankLine());
}
function removeLine(id) {
  lines.value = lines.value.filter(l => l.id !== id);
}
function calcLine(line) {
  const base = Math.round(flt(line.qty) * flt(line.rate) * 100) / 100;
  const disc = Math.round(base * flt(line.discount_percentage) / 100 * 100) / 100;
  line.discount_amount = disc;
  line.amount = base - disc;
}

// Fires when user picks an item from SearchableSelect
// mirrors Invoice's onItemChange
async function onItemSelect(line, opt) {
  // opt can be an option object or a raw string value
  const code = opt?.value ?? opt;
  line.item_code = code;

  // Fill from already-loaded items list
  const found = items.value.find(i => i.name === code || i.value === code);
  if (found) {
    line.item_name = found.item_name || found.label || code;
    line.rate      = flt(found.standard_rate ?? found.rate);
    line.uom       = found.stock_uom || found.uom || "Nos";
    calcLine(line);
  }

  // Fetch HSN code from full Item doc — exactly like Invoice
  if (code) {
    try {
      const doc = await apiGet("Item", code);
      if (doc?.gst_hsn_code) line.hsn_code = doc.gst_hsn_code;
      if (doc?.item_name)    line.item_name = doc.item_name;
      if (!found) {
        line.rate = flt(doc.standard_rate || 0);
        line.uom  = doc.stock_uom || "Nos";
        calcLine(line);
      }
    } catch {}
  }
}

// ── Tax helpers — mirrors Invoice exactly ─────────────────────────────
function addTaxRow() {
  taxRows.value.push({
    id: Date.now(),
    description: "",
    rate: 0,
    account_head: taxAccountHead.value,
    amount: 0,
  });
}
function removeTaxRow(id) {
  taxRows.value = taxRows.value.filter(r => r.id !== id);
}
function recalcTax(tx) {
  tx.amount = Math.round(subtotal.value * flt(tx.rate) / 100 * 100) / 100;
}
function applyTaxPreset(preset) {
  taxRows.value = preset.rows.map((r, i) => ({
    id: Date.now() + i,
    description:  r.desc,
    rate:         r.rate,
    account_head: taxAccountHead.value,
    amount:       Math.round(subtotal.value * r.rate / 100 * 100) / 100,
  }));
}

// ── Open New ──────────────────────────────────────────────────────────
function openNew() {
  editingName.value = "";
  Object.assign(form, {
    customer:         "",
    transaction_date: todayStr(),
    valid_till:       validTillDefault(),
    title:            "",
    terms:            "",
    remarks:          "",
    billing_address:  "",
    currency:         "INR",
  });
  showPreview.value = false;
  lines.value    = [blankLine()];
  taxRows.value  = [];
  fetchCustomers("");
  fetchItems("");
  drawerOpen.value = true;
}

// ── Open Edit ─────────────────────────────────────────────────────────
async function openEdit(q) {
  editingName.value = q.name;
  Object.assign(form, {
    customer:         q.customer         || "",
    transaction_date: q.transaction_date || todayStr(),
    valid_till:       q.valid_till       || validTillDefault(),
    title:            q.title            || "",
    terms:            q.terms            || "",
  });
  // seed with one blank while loading
  lines.value   = [blankLine()];
  taxRows.value = [];
  fetchCustomers("");
  fetchItems("");
  drawerOpen.value = true;

  try {
    const doc = await apiGet("Quotation", q.name);

    // Map items — mirrors Invoice openEdit exactly
    if (doc?.items?.length) {
      lines.value = doc.items.map((it, i) => ({
        id:                   _id++,
        item_code:            it.item_code            || "",
        item_name:            it.item_name            || it.item_code || "",
        description:          it.description          || "",
        hsn_code:             it.gst_hsn_code         || it.hsn_code || "",
        qty:                  flt(it.qty)             || 1,
        rate:                 flt(it.rate)            || 0,
        uom:                  it.uom                  || "Nos",
        discount_percentage:  flt(it.discount_percentage) || 0,
        discount_amount:      flt(it.discount_amount)     || 0,
        amount:               flt(it.amount)              || 0,
      }));
    }

    // Map taxes — mirrors Invoice openEdit exactly
    if (doc?.taxes?.length) {
      taxRows.value = doc.taxes.map((tx, i) => ({
        id:           Date.now() + 100 + i,
        description:  tx.description  || "",
        rate:         flt(tx.rate)    || 0,
        account_head: tx.account_head || taxAccountHead.value,
        amount:       flt(tx.tax_amount) || flt(tx.amount) || 0,
      }));
    }

    // Fill remaining form fields from full doc
    if (doc?.terms)            form.terms  = doc.terms;
    if (doc?.title)            form.title  = doc.title;
  } catch {}
}

// ── Open View ─────────────────────────────────────────────────────────
async function openView(q) {
  viewDoc.value     = q;
  viewOpen.value    = true;
  viewTab.value     = "details";
  viewLoading.value = true;
  viewItems.value   = [];
  conv.sales_orders   = [];
  conv.sales_invoices = [];
  try {
    const [doc, convData] = await Promise.all([
      apiGet("Quotation", q.name),
      apiGET("zoho_books_clone.api.docs.get_quote_conversions", { quotation_name: q.name }).catch(() => null),
    ]);
    viewItems.value = doc?.items || [];
    viewDoc.value   = { ...q, ...doc };
    if (convData) {
      conv.sales_orders   = convData.sales_orders   || [];
      conv.sales_invoices = convData.sales_invoices || [];
    }
  } catch {}
  viewLoading.value = false;
}

// ── Save ──────────────────────────────────────────────────────────────
async function saveQT(newStatus) {
  if (!form.customer)
    return toast.error("Customer is required");
  if (!lines.value.some(l => l.item_code && flt(l.qty) > 0))
    return toast.error("At least one item required");

  drawerSaving.value = true;
  try {
    const company = await resolveCompany();

    // Items — mirrors Invoice saveInvoice exactly
    const qtItems = lines.value
      .filter(l => l.item_code)
      .map(l => ({
        doctype:              "Quotation Item",
        item_code:            l.item_code,
        item_name:            l.item_name || l.item_code,
        description:          l.description || l.item_name || l.item_code,
        qty:                  flt(l.qty) || 1,
        rate:                 flt(l.rate),
        uom:                  l.uom || "Nos",
        amount:               flt(l.amount),
        gst_hsn_code:         l.hsn_code || "",
        discount_percentage:  flt(l.discount_percentage) || 0,
        discount_amount:      flt(l.discount_amount)     || 0,
      }));

    // Taxes — mirrors Invoice saveInvoice exactly
    const taxes = taxRows.value
      .filter(r => r.rate > 0)
      .map(r => ({
        doctype:      "Sales Taxes and Charges",
        charge_type:  "On Net Total",
        account_head: r.account_head || taxAccountHead.value,
        description:  r.description,
        rate:         r.rate,
      }));

    const doc = {
      doctype:          "Quotation",
      company,
      customer:         form.customer,
      transaction_date: form.transaction_date,
      valid_till:       form.valid_till   || null,
      title:            form.title        || "",
      status:           newStatus         || "Draft",
      terms:            form.terms        || "",
      items:            qtItems,
      taxes,
    };
    if (editingName.value) doc.name = editingName.value;

    const saved = await apiSave(doc);
    toast.success(`Quotation ${saved?.name || ""} saved`);
    drawerOpen.value = false;
    await load();
  } catch (e) {
    toast.error(e.message || "Failed to save quotation");
  } finally {
    drawerSaving.value = false;
  }
}

// ── Actions ───────────────────────────────────────────────────────────
async function emailQT(q) {
  const ok = await openEmail({
    doctype:  "Quotation", name: q.name, docLabel: `Quotation ${q.name}`,
    getDefaultsEndpoint: "zoho_books_clone.api.docs.get_quote_email_defaults",
    sendEndpoint:        "zoho_books_clone.api.docs.send_quote_email",
    paramKey:            "quotation_name",
  });
  if (ok) await load();
}

async function markStatus(q, status) {
  const epMap = {
    Sent:     "mark_quote_sent",
    Accepted: "mark_quote_accepted",
    Declined: "mark_quote_declined",
  };
  const ep = epMap[status];
  if (!ep) return;
  try {
    await apiPOST(`zoho_books_clone.api.docs.${ep}`, { quotation_name: q.name });
    toast.success(`Marked ${status}`);
    await load();
    if (viewDoc.value?.name === q.name) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Update failed"); }
}

function openConvertModal(q) {
  Object.assign(convertModal, {
    open: true, saving: false, qtName: q.name,
    target: "", deliveryDate: q.valid_till || todayStr(), dueDate: todayStr(),
  });
}
async function submitConvert() {
  if (!convertModal.target) return;
  convertModal.saving = true;
  try {
    const ep = convertModal.target === "SO"
      ? "zoho_books_clone.api.docs.convert_quote_to_sales_order"
      : "zoho_books_clone.api.docs.convert_quote_to_invoice";
    const payload = { quotation_name: convertModal.qtName };
    if (convertModal.target === "SO"      && convertModal.deliveryDate) payload.delivery_date = convertModal.deliveryDate;
    if (convertModal.target === "Invoice" && convertModal.dueDate)      payload.due_date      = convertModal.dueDate;
    const r = await apiPOST(ep, payload);
    const created = r?.sales_order || r?.sales_invoice;
    toast.success(`Converted → ${convertModal.target === "SO" ? "Sales Order" : "Invoice"}: ${created}`);
    convertModal.open = false;
    await load();
    if (viewDoc.value?.name === convertModal.qtName) await openView(viewDoc.value);
  } catch (e) { toast.error(e.message || "Convert failed"); }
  convertModal.saving = false;
}

async function deleteQT(q) {
  if (!await confirm({ title: "Delete Quotation", body: `Permanently delete ${q.name}?`, okLabel: "Delete" })) return;
  try {
    await apiDelete("Quotation", q.name);
    toast.success("Quotation deleted");
    viewOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Delete failed"); }
}

// ── Bulk actions ──────────────────────────────────────────────────────
async function bulkDelete() {
  const drafts = sorted.value.filter(q =>
    selected.value.has(q.name) && (q.status === "Draft" || !q.status)
  );
  if (!drafts.length) { toast.info("No draft quotations selected"); return; }
  if (!await confirm({ title: "Delete Drafts", body: `Delete ${drafts.length} draft quotation(s)?`, okLabel: "Delete" })) return;
  for (const q of drafts) { try { await apiDelete("Quotation", q.name); } catch {} }
  selected.value = new Set();
  toast.success(`Deleted ${drafts.length} draft(s)`);
  await load();
}
async function bulkMarkSent() {
  const targets = sorted.value.filter(q =>
    selected.value.has(q.name) && effectiveStatus(q) === "Draft"
  );
  if (!targets.length) { toast.info("Select drafts to mark as sent"); return; }
  let done = 0;
  for (const q of targets) {
    try { await apiPOST("zoho_books_clone.api.docs.mark_quote_sent", { quotation_name: q.name }); done++; } catch {}
  }
  selected.value = new Set();
  toast.success(`Marked ${done} quote(s) as Sent`);
  await load();
}
async function bulkMarkExpired() {
  const targets = sorted.value.filter(q => selected.value.has(q.name));
  if (!targets.length) { toast.info("No quotes selected"); return; }
  try {
    await apiPOST("zoho_books_clone.api.docs.mark_quote_expired_bulk",
      { quotation_names: JSON.stringify(targets.map(q => q.name)) });
    selected.value = new Set();
    toast.success(`Marked ${targets.length} quote(s) as Expired`);
    await load();
  } catch (e) { toast.error(e.message || "Bulk expire failed"); }
}
async function bulkEmail() {
  const subs = sorted.value.filter(q => selected.value.has(q.name));
  if (!subs.length) { toast.info("No quotes selected"); return; }
  let sent = 0;
  for (const q of subs) {
    const ok = await openEmail({
      doctype:  "Quotation", name: q.name, docLabel: `Quotation ${q.name}`,
      getDefaultsEndpoint: "zoho_books_clone.api.docs.get_quote_email_defaults",
      sendEndpoint:        "zoho_books_clone.api.docs.send_quote_email",
      paramKey:            "quotation_name",
    });
    if (ok) sent++;
  }
  if (sent) { toast.success(`Emailed ${sent} quote(s)`); await load(); }
}

// ── Export CSV ────────────────────────────────────────────────────────
function exportCSV() {
  const rows = sorted.value;
  const head = ["Quote #","Customer","Date","Valid Till","Status","Amount"];
  const esc  = v => `"${String(v ?? "").replace(/"/g,'""')}"`;
  const out  = [head.map(esc).join(",")];
  for (const q of rows) {
    out.push([
      q.name, q.customer_name || q.customer,
      q.transaction_date, q.valid_till || "",
      effectiveStatus(q), Number(q.grand_total || 0).toFixed(2),
    ].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url  = URL.createObjectURL(blob);
  const a    = document.createElement("a");
  a.href = url; a.download = `quotations_${todayStr()}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast.success(`CSV exported — ${rows.length} quote(s)`);
}

// ── Mount ─────────────────────────────────────────────────────────────
onMounted(() => {
  load();
  loadTaxAccount();
  fetchCustomers("");   // pre-load — mirrors Invoice
  fetchItems("");       // pre-load — mirrors Invoice
});
</script>
<style scoped>
.qt-page { display: flex; flex-direction: column; gap: 16px; padding: 24px; }
.qt-actions { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.qt-search-wrap { display: flex; align-items: center; gap: 8px; background: #f3f4f6; border-radius: 8px; padding: 6px 12px; min-width: 220px; }
.qt-search-input { border: none; background: transparent; outline: none; font: inherit; color: #111827; width: 100%; font-size: 13px; }
.qt-pills { display: flex; gap: 6px; flex-wrap: wrap; }
.qt-pill { padding: 6px 14px; border-radius: 20px; font-size: 12.5px; font-weight: 600; border: 1px solid #e5e7eb; background: #fff; color: #6b7280; cursor: pointer; font-family: inherit; display: inline-flex; align-items: center; gap: 6px; }
.qt-pill:hover { color: #2563eb; border-color: #2563eb; }
.qt-pill.active { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.qt-pill-count { background: #f3f4f6; color: #6b7280; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.qt-pill.active .qt-pill-count { background: #2563eb; color: #fff; }
.qt-btn-primary { display: inline-flex; align-items: center; gap: 6px; background: #2563eb; color: #fff; border: none; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.qt-btn-primary:hover:not(:disabled) { background: #1d4ed8; }
.qt-btn-primary:disabled { opacity: .5; cursor: not-allowed; }
.qt-btn-ghost { display: inline-flex; align-items: center; gap: 6px; background: transparent; border: 1px solid #e5e7eb; border-radius: 8px; padding: 8px 12px; font-size: 13px; color: #374151; cursor: pointer; }
.qt-btn-ghost:hover { background: #f9fafb; }
.qt-btn-save { display: inline-flex; align-items: center; gap: 6px; background: #f0fdf4; border: 1px solid #16a34a; color: #16a34a; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.qt-btn-save:hover { background: #dcfce7; }
.qt-btn-save:disabled { opacity: .5; cursor: not-allowed; }
.qt-btn-danger { display: inline-flex; align-items: center; gap: 6px; background: #fef2f2; border: 1px solid #dc2626; color: #dc2626; border-radius: 8px; padding: 8px 14px; font-size: 13px; font-weight: 600; cursor: pointer; }
.qt-btn-danger:hover { background: #fee2e2; }

.qt-card { background: #fff; border: 1px solid #e5e7eb; border-radius: 10px; overflow: hidden; }
.qt-table { width: 100%; border-collapse: collapse; font-size: 13px; }
.qt-table th { background: #f9fafb; border-bottom: 1px solid #e5e7eb; padding: 10px 12px; font-size: 11.5px; font-weight: 600; color: #374151; text-align: left; white-space: nowrap; }
.qt-table th.sortable { cursor: pointer; user-select: none; }
.qt-table th.sortable:hover { color: #2563eb; }
.ta-r { text-align: right !important; }
.qt-row td { padding: 10px 12px; border-bottom: 1px solid #f3f4f6; vertical-align: middle; cursor: pointer; }
.qt-row:last-child td { border-bottom: none; }
.qt-row:hover td { background: #f9fafb; }
.qt-row.selected td { background: #eff6ff; }
.qt-num { font-family: monospace; font-size: 12.5px; color: #2563eb; font-weight: 600; }
.mono-sm { font-family: monospace; font-size: 12.5px; }
.text-muted { color: #6b7280; }
.text-danger { color: #dc2626; }
.qt-badge { display: inline-flex; align-items: center; padding: 2px 8px; border-radius: 10px; font-size: 11.5px; font-weight: 600; }
.qt-bdg-grey   { background: #f3f4f6; color: #6b7280; }
.qt-bdg-blue   { background: #dbeafe; color: #1a6ef7; }
.qt-bdg-green  { background: #d1fae5; color: #059669; }
.qt-bdg-purple { background: #ede9fe; color: #7c3aed; }
.qt-bdg-red    { background: #fee2e2; color: #dc2626; }
.qt-badge-white { background: rgba(255,255,255,.2); color: #fff !important; border: 1px solid rgba(255,255,255,.4); }
.qt-act-cell { display: flex; gap: 4px; justify-content: flex-end; cursor: default !important; }
.qt-act-btn { background: transparent; border: 1px solid #e5e7eb; border-radius: 6px; width: 26px; height: 26px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #6b7280; }
.qt-act-btn:hover { background: #f3f4f6; color: #2563eb; }
.qt-act-conv { background: #eff6ff; border-color: #2563eb; color: #2563eb; }
.qt-act-conv:hover { background: #dbeafe; }
.qt-act-del:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.qt-empty { text-align: center; color: #9ca3af; padding: 48px !important; cursor: default !important; }
.qt-shimmer { height: 13px; background: linear-gradient(90deg, #f3f4f6 25%, #e5e7eb 50%, #f3f4f6 75%); border-radius: 4px; animation: shimmer 1.2s infinite; background-size: 200% 100%; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

.qt-overlay { position: fixed; inset: 0; background: rgba(0,0,0,.2); z-index: 40; }
.qt-drawer { position: fixed; top: 0; right: -600px; bottom: 0; width: 600px; max-width: 96vw; background: #fff; border-left: 1px solid #e5e7eb; box-shadow: -8px 0 24px rgba(0,0,0,.08); z-index: 50; display: flex; flex-direction: column; transition: right .22s ease; }
.qt-drawer.open { right: 0; }
.qt-view-drawer { width: 540px; right: -540px; }
.qt-view-drawer.open { right: 0; }
.qt-dheader { display: flex; align-items: center; justify-content: space-between; padding: 0 20px; height: 60px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; }
.qt-dheader-title { font-size: 15px; font-weight: 600; color: #111827; }
.qt-dclose { background: transparent; border: none; cursor: pointer; color: #6b7280; display: inline-flex; align-items: center; justify-content: center; width: 32px; height: 32px; border-radius: 6px; }
.qt-dclose:hover { background: #f3f4f6; color: #111827; }
.qt-dbody { flex: 1; overflow-y: auto; padding: 20px; display: flex; flex-direction: column; gap: 14px; }
.qt-fields-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.qt-field { display: flex; flex-direction: column; gap: 4px; }
.qt-label { font-size: 12px; font-weight: 600; color: #374151; }
.req { color: #dc2626; }
.qt-input { width: 100%; box-sizing: border-box; border: 1px solid #e5e7eb; border-radius: 6px; padding: 7px 10px; font: inherit; font-size: 13px; outline: none; background: #fff; color: #111827; }
.qt-input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.08); }
textarea.qt-input { resize: vertical; }
.qt-section-title { font-size: 12px; font-weight: 700; color: #374151; text-transform: uppercase; letter-spacing: .05em; padding-bottom: 4px; border-bottom: 1px solid #f3f4f6; }
.qt-items-table { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 8px; overflow: hidden; }
.qt-items-head { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11.5px; font-weight: 600; color: #374151; }
.qt-items-row { display: grid; grid-template-columns: 2fr 2fr 80px 100px 100px 32px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; }
.qt-add-line { background: transparent; border: none; color: #2563eb; font-size: 12.5px; font-weight: 600; cursor: pointer; padding: 8px 12px; display: inline-flex; align-items: center; gap: 6px; }
.qt-add-line:hover { background: #eff6ff; }
.qt-rm-line { background: transparent; border: 1px solid #e5e7eb; border-radius: 4px; width: 22px; height: 22px; display: inline-flex; align-items: center; justify-content: center; cursor: pointer; color: #9ca3af; }
.qt-rm-line:hover { background: #fee2e2; color: #dc2626; border-color: #fca5a5; }
.qt-totals { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.qt-totals-right { display: flex; flex-direction: column; gap: 4px; min-width: 220px; }
.qt-total-row { display: flex; justify-content: space-between; gap: 16px; font-size: 13px; color: #374151; padding: 3px 0; }
.qt-total-row.grand { font-weight: 700; font-size: 14px; color: #111827; border-top: 1px solid #e5e7eb; padding-top: 6px; }

.qt-view-head { position: relative; display: flex; align-items: flex-start; justify-content: space-between; padding: 20px; flex-shrink: 0; color: #fff; }
.qt-view-num { font-size: 18px; font-weight: 700; font-family: monospace; color: #fff; }
.qt-view-sub { font-size: 13px; color: rgba(255,255,255,.8); margin-top: 2px; }
.qt-view-amount { font-size: 22px; font-weight: 800; font-family: monospace; color: #fff; }
.qt-vclose { position: absolute; top: 12px; right: 12px; color: #fff; }
.qt-vclose:hover { background: rgba(255,255,255,.18); color: #fff; }
.qt-tabs { display: flex; gap: 4px; padding: 0 20px; border-bottom: 1px solid #e5e7eb; flex-shrink: 0; background: #fff; }
.qt-tab { background: transparent; border: none; padding: 10px 14px; font: inherit; font-size: 12.5px; font-weight: 600; color: #6b7280; cursor: pointer; border-bottom: 2px solid transparent; display: inline-flex; align-items: center; gap: 6px; }
.qt-tab:hover { color: #2563eb; }
.qt-tab.active { color: #2563eb; border-bottom-color: #2563eb; }
.qt-tab-count { background: #2563eb; color: #fff; padding: 1px 7px; border-radius: 999px; font-size: 11px; font-weight: 700; }
.qt-meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.qt-meta-lbl { font-size: 11px; color: #9ca3af; text-transform: uppercase; letter-spacing: .05em; margin-bottom: 2px; }
.qt-view-items { display: flex; flex-direction: column; border: 1px solid #e5e7eb; border-radius: 6px; overflow: hidden; }
.qt-view-items-head { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; background: #f9fafb; padding: 8px 12px; font-size: 11px; font-weight: 700; color: #6b7280; text-transform: uppercase; }
.qt-view-items-row { display: grid; grid-template-columns: 2.5fr 70px 90px 100px; gap: 8px; padding: 8px 12px; border-top: 1px solid #f3f4f6; align-items: center; font-size: 12.5px; }
.qt-terms { padding: 10px 12px; background: #f8fafc; border-radius: 6px; }
.qt-conv-row { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 8px; padding: 8px 12px; border: 1px solid #e5e7eb; border-radius: 6px; font-size: 12.5px; align-items: center; }
.qt-dfooter { display: flex; align-items: center; justify-content: flex-end; gap: 8px; padding: 14px 20px; border-top: 1px solid #e5e7eb; flex-shrink: 0; flex-wrap: wrap; }

.qt-apply-dialog { position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); width: 520px; max-width: 96vw; background: #fff; border-radius: 12px; box-shadow: 0 12px 40px rgba(0,0,0,.2); z-index: 70; display: flex; flex-direction: column; overflow: hidden; }
.qt-convert-options { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.qt-convert-card { background: #fff; border: 2px solid #e5e7eb; border-radius: 10px; padding: 14px; display: flex; align-items: center; gap: 12px; cursor: pointer; font: inherit; text-align: left; transition: all .15s; }
.qt-convert-card:hover { border-color: #1a6ef7; background: #f0f9ff; }
.qt-convert-card.active { border-color: #1a6ef7; background: #eff6ff; box-shadow: 0 0 0 4px rgba(26,110,247,.1); }
.qt-convert-icon { width: 40px; height: 40px; border-radius: 8px; display: grid; place-items: center; font-weight: 800; font-size: 14px; flex-shrink: 0; }

/* ══ Invoice-matching Create/Edit Modal ══ */
.qt-drawer-bg { position:fixed; inset:0; z-index:8000; background:rgba(15,23,42,.45); display:flex; justify-content:flex-end; backdrop-filter:blur(2px); }
.qt-drawer-panel { width:720px; max-width:96vw; height:100%; background:#fff; display:flex; flex-direction:column; box-shadow:-20px 0 60px rgba(0,0,0,.15); overflow:hidden; }
.qt-split { width:min(1300px,98vw) !important; }

/* Blue gradient header — identical to Invoice */
.qt-dh { display:flex; align-items:center; justify-content:space-between; padding:18px 24px; background:linear-gradient(135deg,#1e3a5f,#1a6ef7); flex-shrink:0; }
.qt-dh-title { color:#fff; font-size:16px; font-weight:700; }
.qt-dh-sub   { color:rgba(255,255,255,.75); font-size:12px; margin-top:2px; }
.qt-dclose-new { background:rgba(255,255,255,.15); border:none; cursor:pointer; width:30px; height:30px; border-radius:8px; color:#fff; display:grid; place-items:center; }
.qt-dclose-new:hover { background:rgba(255,255,255,.25); }
.qt-preview-toggle { display:inline-flex; align-items:center; gap:5px; background:rgba(255,255,255,.15); border:1px solid rgba(255,255,255,.3); color:#fff; border-radius:6px; padding:5px 11px; font-size:12px; font-weight:600; cursor:pointer; }
.qt-preview-toggle:hover { background:rgba(255,255,255,.25); }

/* Template / branding bar */
.qt-tmpl-bar { display:flex; align-items:flex-start; gap:24px; padding:9px 22px; border-bottom:1px solid #e8ecf0; background:#f8fafc; flex-shrink:0; flex-wrap:wrap; }
.qt-tmpl-group { display:flex; flex-direction:column; gap:4px; }
.qt-tmpl-lbl { font-size:9.5px; font-weight:700; text-transform:uppercase; letter-spacing:.05em; color:#9ca3af; }
.qt-tmpl-btns { display:flex; gap:4px; }
.qt-tmpl-btn { border:1px solid #e8ecf0; background:#fff; color:#374151; border-radius:5px; padding:4px 11px; font-size:12px; font-weight:600; cursor:pointer; }
.qt-tmpl-btn:hover { border-color:#1a6ef7; color:#1a6ef7; }
.qt-tmpl-btn.active { background:#eaf1ff; border-color:#1a6ef7; color:#1a6ef7; }
.qt-color-pick { width:34px; height:26px; border:1px solid #e8ecf0; border-radius:5px; cursor:pointer; padding:2px 3px; }
.qt-color-val { font-size:12px; font-family:monospace; color:#374151; }
.qt-logo-input { border:1px solid #e2e8f0; border-radius:5px; padding:4px 8px; font-size:12px; outline:none; width:100%; max-width:300px; }
.qt-logo-input:focus { border-color:#1a6ef7; }

/* Content row + body */
.qt-content-row { flex:1; display:flex; overflow:hidden; min-height:0; }
.qt-content-row .qt-dbody { flex:1; overflow-y:auto; min-width:0; padding:20px 24px; }
.qt-dbody { flex:1; overflow-y:auto; padding:20px 24px; display:flex; flex-direction:column; }

/* Section labels — matching Invoice */
.qt-sec-lbl { font-size:10.5px; font-weight:700; letter-spacing:.6px; text-transform:uppercase; color:#9ca3af; margin-bottom:12px; margin-top:4px; padding-top:16px; border-top:1px solid #f0f2f5; display:block; }
.qt-sec-lbl:first-child { border-top:none; padding-top:0; margin-top:0; }
.qt-fg { display:grid; gap:12px; margin-bottom:14px; }
.qt-fg2 { grid-template-columns:1fr 1fr; } .qt-fg3 { grid-template-columns:1fr 1fr 1fr; }
.qt-lbl { display:block; font-size:11.5px; font-weight:600; color:#495057; margin-bottom:5px; }
.qt-req { color:#dc2626; }
.qt-fi { width:100%; border:1px solid #e2e8f0; border-radius:6px; padding:7px 10px; font-size:13px; font-family:inherit; outline:none; box-sizing:border-box; }
.qt-fi:focus { border-color:#1a6ef7; box-shadow:0 0 0 3px rgba(26,110,247,.08); }
textarea.qt-fi { resize:vertical; }
select.qt-fi { cursor:pointer; }

/* Add item header button */
.qt-add-item-btn { display:inline-flex; align-items:center; gap:5px; border:1px solid rgba(26,110,247,.3); background:#eaf1ff; color:#1a6ef7; border-radius:6px; padding:4px 12px; font-size:12px; font-weight:600; cursor:pointer; }
.qt-add-item-btn:hover { background:#dbeafe; }

/* Line items grid (div-based, matching Invoice) */
.qt-lines-wrap { border:1px solid #e8ecf0; border-radius:8px; overflow:visible; margin-bottom:0; }
.qt-lines-head { display:grid; grid-template-columns:2fr 1.5fr 0.7fr 0.6fr 0.6fr 0.8fr 0.6fr 0.8fr 30px; gap:6px; padding:7px 10px; background:#f8fafc; border-bottom:1px solid #e8ecf0; font-size:10px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; }
.qt-lines-row { display:grid; grid-template-columns:2fr 1.5fr 0.7fr 0.6fr 0.6fr 0.8fr 0.6fr 0.8fr 30px; gap:6px; padding:5px 10px; border-bottom:1px solid #f0f2f5; align-items:center; }
.qt-lines-row:last-of-type { border-bottom:none; }
.qt-lines-empty { padding:16px; text-align:center; color:#9ca3af; font-size:13px; border-bottom:1px solid #f0f2f5; }
.qt-ci { width:100%; border:1px solid #e2e8f0; border-radius:5px; padding:5px 7px; font-size:12.5px; font-family:inherit; outline:none; box-sizing:border-box; }
.qt-ci:focus { border-color:#1a6ef7; box-shadow:0 0 0 2px rgba(26,110,247,.08); }
.qt-ci-r { text-align:right; }
.qt-rm-line { background:none; border:1px solid rgba(220,38,38,.3); border-radius:4px; padding:3px 5px; cursor:pointer; color:#dc2626; display:inline-flex; align-items:center; flex-shrink:0; }
.qt-rm-line:hover { background:#fee2e2; }
.qt-add-line-btn { display:inline-flex; align-items:center; gap:5px; border:none; background:transparent; color:#1a6ef7; font-size:12.5px; font-weight:600; cursor:pointer; padding:8px 12px; width:100%; }
.qt-add-line-btn:hover { background:#f0f7ff; }

/* Tax + totals section */
.qt-totals-wrap { border-top:1px solid #e8ecf0; padding:12px 14px; background:#f8fafc; display:flex; gap:20px; align-items:flex-start; flex-wrap:wrap; margin-top:0; }
.qt-tax-section { flex:1; min-width:280px; }
.qt-tax-header { display:flex; align-items:center; gap:10px; margin-bottom:8px; flex-wrap:wrap; }
.qt-tax-title { font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; }
.qt-tax-presets { display:flex; gap:5px; flex-wrap:wrap; }
.qt-preset-btn { border:1px solid #e8ecf0; background:#fff; color:#374151; border-radius:5px; padding:3px 8px; font-size:11.5px; font-weight:600; cursor:pointer; white-space:nowrap; }
.qt-preset-btn:hover { border-color:#1a6ef7; color:#1a6ef7; }
.qt-preset-custom { border-color:rgba(26,110,247,.3); color:#1a6ef7; }
.qt-preset-clear { border-color:rgba(220,38,38,.3); color:#dc2626; }
.qt-tax-tbl { width:100%; border-collapse:collapse; font-size:12.5px; }
.qt-tax-tbl th { padding:5px 8px; font-size:10px; font-weight:700; text-transform:uppercase; color:#9ca3af; text-align:left; border-bottom:1px solid #e8ecf0; }
.qt-tax-tbl td { padding:4px 6px; border-bottom:1px solid #f0f2f5; }
.qt-totals-right-panel { min-width:240px; display:flex; flex-direction:column; gap:5px; align-items:flex-end; }
.qt-total-row-item { display:flex; justify-content:space-between; align-items:center; width:240px; font-size:13px; color:#374151; }
.qt-total-amt { font-family:monospace; font-weight:600; font-size:13px; }
.qt-grand-total { border-top:1px solid #e8ecf0; padding-top:7px; margin-top:2px; font-weight:700; }

/* Preview pane */
.qt-preview-pane { width:480px; flex-shrink:0; border-left:1px solid #e8ecf0; display:flex; flex-direction:column; background:#e8ecf0; overflow:hidden; }
.qt-preview-toolbar { display:flex; align-items:center; justify-content:space-between; padding:8px 12px; background:#fff; border-bottom:1px solid #e8ecf0; flex-shrink:0; }
.qt-preview-placeholder { flex:1; display:flex; flex-direction:column; align-items:center; justify-content:center; }

/* Footer — matches Invoice dfooter */
.qt-dfooter-new { padding:14px 24px; border-top:1px solid #e8ecf0; display:flex; justify-content:space-between; align-items:center; background:#f8fafc; flex-shrink:0; }

</style>