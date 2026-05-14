<template>
<div class="inv-page">

  <!-- ── Top toolbar ── -->
  <div class="inv-toolbar">
    <div class="inv-toolbar-left">
      <h2 class="inv-heading">All Invoices</h2>
    </div>
    <div class="inv-toolbar-right">
      <div class="inv-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search invoices…" class="inv-search-input"/>
      </div>
      <button class="inv-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',14)"></span></button>
      <button class="inv-btn-primary" @click="openAdd">
        <span v-html="icon('plus',13)"></span> New Invoice
      </button>
    </div>
  </div>

  <!-- ── Summary strip ── -->
  <div class="inv-sum-strip">
    <div class="inv-sum-card">
      <div class="inv-sum-lbl">Total Invoices</div>
      <div class="inv-sum-val">{{list.length}}</div>
    </div>
    <div class="inv-sum-card" style="border-left:3px solid #d97706">
      <div class="inv-sum-lbl" style="color:#d97706">Unpaid</div>
      <div class="inv-sum-val" style="color:#d97706">{{summary.unpaidCount}}</div>
    </div>
    <div class="inv-sum-card" style="border-left:3px solid #dc2626">
      <div class="inv-sum-lbl" style="color:#dc2626">Overdue</div>
      <div class="inv-sum-val" style="color:#dc2626">{{summary.overdueCount}}</div>
    </div>
    <div class="inv-sum-card" style="border-left:3px solid #059669">
      <div class="inv-sum-lbl" style="color:#059669">Total Receivable</div>
      <div class="inv-sum-val" style="color:#059669">{{fmtAmt(summary.totalDue)}}</div>
    </div>
  </div>

  <!-- ── Filter pills ── -->
  <div class="inv-filters">
    <button v-for="f in FILTERS" :key="f.key" class="inv-pill" :class="{active: activeFilter===f.key}" @click="activeFilter=f.key">
      {{f.label}}
      <span v-if="f.key!=='all'" class="inv-pill-count" :class="pillCls(f.key)">{{counts[f.key]}}</span>
    </button>
  </div>

  <!-- ── Table ── -->
  <div class="inv-table-wrap">
    <table class="inv-table">
      <thead><tr>
        <th class="th-check"><input type="checkbox" @change="toggleAll" :checked="allSelected"/></th>
        <th class="sortable" @click="sort('posting_date')">DATE <span class="sort-arrow">{{sortArrow('posting_date')}}</span></th>
        <th class="sortable" @click="sort('name')">INVOICE# <span class="sort-arrow">{{sortArrow('name')}}</span></th>
        <th>PO NUMBER</th>
        <th class="sortable" @click="sort('customer_name')">CUSTOMER <span class="sort-arrow">{{sortArrow('customer_name')}}</span></th>
        <th class="sortable" @click="sort('status')">STATUS <span class="sort-arrow">{{sortArrow('status')}}</span></th>
        <th class="sortable" @click="sort('due_date')">DUE DATE <span class="sort-arrow">{{sortArrow('due_date')}}</span></th>
        <th class="ta-r sortable" @click="sort('grand_total')">AMOUNT <span class="sort-arrow">{{sortArrow('grand_total')}}</span></th>
        <th class="ta-r sortable" @click="sort('outstanding_amount')">BALANCE DUE <span class="sort-arrow">{{sortArrow('outstanding_amount')}}</span></th>
        <th style="width:80px;text-align:center">ACTIONS</th>
      </tr></thead>
      <tbody>
        <template v-if="loading">
          <tr v-for="n in 7" :key="n" class="shimmer-row">
            <td><div class="shimmer" style="width:14px;height:14px;border-radius:3px"></div></td>
            <td><div class="shimmer" style="width:80px"></div></td>
            <td><div class="shimmer" style="width:110px"></div></td>
            <td><div class="shimmer" style="width:60px"></div></td>
            <td><div class="shimmer" style="width:130px"></div></td>
            <td><div class="shimmer" style="width:90px"></div></td>
            <td><div class="shimmer" style="width:80px"></div></td>
            <td><div class="shimmer" style="width:80px;margin-left:auto"></div></td>
            <td><div class="shimmer" style="width:80px;margin-left:auto"></div></td>
            <td></td>
          </tr>
        </template>
        <template v-else>
          <tr v-for="inv in sorted" :key="inv.name" class="inv-row" :class="{selected: selectedRows.has(inv.name)}"
            @click.self="openView(inv)">
            <td class="td-check" @click.stop>
              <input type="checkbox" :checked="selectedRows.has(inv.name)" @change="toggleRow(inv.name)"/>
            </td>
            <td @click="openView(inv)" class="text-muted mono-sm">{{fmtDate(inv.posting_date)}}</td>
            <td @click="openView(inv)"><span class="inv-link">{{inv.name}}</span></td>
            <td @click="openView(inv)" class="text-muted">{{inv.po_no||'—'}}</td>
            <td @click="openView(inv)"><span class="inv-customer">{{inv.customer_name||inv.customer}}</span></td>
            <td @click="openView(inv)">
              <span class="inv-status-badge" :class="statusCls(inv)">{{statusLabel(inv)}}</span>
            </td>
            <td @click="openView(inv)" :class="isOverdue(inv)?'text-danger':'text-muted'" class="mono-sm">{{fmtDate(inv.due_date)}}</td>
            <td class="ta-r mono-sm" @click="openView(inv)">{{fmtAmt(inv.grand_total)}}</td>
            <td class="ta-r mono-sm" @click="openView(inv)" :class="inv.outstanding_amount>0?'text-danger':'text-success'">
              {{fmtAmt(inv.outstanding_amount)}}
            </td>
            <td style="text-align:center" @click.stop>
              <div style="display:flex;gap:4px;justify-content:center">
                <button class="inv-act-btn" @click="openView(inv)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="inv.docstatus===0" class="inv-act-btn" @click="openEdit(inv)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                <button v-if="inv.outstanding_amount>0&&inv.docstatus===1" class="inv-act-btn inv-act-pay" @click="openPayment(inv)" title="Record Payment">₹</button>
              </div>
            </td>
          </tr>
          <tr v-if="!sorted.length">
            <td colspan="10" class="empty-state">
              <div class="empty-inner">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" opacity=".3"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
                <p>{{search?'No invoices match':'No invoices yet'}}</p>
                <button v-if="!search" class="inv-btn-primary" style="margin-top:4px" @click="openAdd">
                  <span v-html="icon('plus',13)"></span> New Invoice
                </button>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
  <div v-if="!loading&&sorted.length" style="text-align:right;font-size:12px;color:#9ca3af;padding:6px 20px">
    {{sorted.length}} of {{list.length}} invoices
  </div>

  <!-- ── Create / Edit Drawer ── -->
  <Teleport to="body">
    <div v-if="drawerOpen" class="inv-drawer-bg" @click.self="drawerOpen=false">
      <div class="inv-drawer-panel">
        <div class="inv-dh">
          <div>
            <div class="inv-dh-title">{{editingName?'Edit Invoice':'New Invoice'}}</div>
            <div class="inv-dh-sub">{{editingName?editingName:'Fill in the details below'}}</div>
          </div>
          <button class="inv-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>

        <div class="inv-dbody">
          <!-- Customer + dates row -->
          <div class="inv-sec-lbl">Invoice Details</div>
          <div class="inv-fg inv-fg3">
            <div style="grid-column:1/3">
              <label class="inv-lbl">Customer <span style="color:#dc2626">*</span></label>
              <SearchableSelect v-model="form.customer" :options="customers"
                value-key="name" label-key="customer_name" placeholder="Select customer"
                @update:modelValue="onCustomerChange"/>
            </div>
            <div>
              <label class="inv-lbl">Invoice Date <span style="color:#dc2626">*</span></label>
              <input v-model="form.posting_date" type="date" class="inv-fi"/>
            </div>
            <div>
              <label class="inv-lbl">Due Date</label>
              <input v-model="form.due_date" type="date" class="inv-fi"/>
            </div>
            <div>
              <label class="inv-lbl">PO Number</label>
              <input v-model="form.po_no" class="inv-fi" placeholder="Customer PO ref"/>
            </div>
          </div>

          <!-- Line items -->
          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;margin-top:4px">
            <span class="inv-sec-lbl" style="margin:0;border:none;padding:0">Line Items</span>
            <button class="inv-add-line-btn" @click="addLine">
              <span v-html="icon('plus',12)"></span> Add Item
            </button>
          </div>

          <div style="border:1px solid #e8ecf0;border-radius:8px;overflow:hidden;margin-bottom:16px">
            <table class="inv-lines-tbl">
              <thead>
                <tr>
                  <th style="width:28%">Item / Description <span style="color:#dc2626">*</span></th>
                  <th style="width:18%">Description</th>
                  <th style="width:8%">Qty</th>
                  <th style="width:10%">UOM</th>
                  <th style="width:14%;text-align:right">Rate (₹)</th>
                  <th style="width:14%;text-align:right">Amount (₹)</th>
                  <th style="width:4%"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="line in lines" :key="line.id">
                  <td>
                    <SearchableSelect v-model="line.item_code" :options="items"
                      value-key="name" label-key="item_name" placeholder="— Select item —"
                      :compact="true" @update:modelValue="onItemChange(line)"/>
                  </td>
                  <td><input v-model="line.description" class="inv-ci" placeholder="Optional"/></td>
                  <td><input v-model.number="line.qty" type="number" min="0.001" step="0.001" class="inv-ci" @input="calcLine(line)"/></td>
                  <td><input v-model="line.uom" class="inv-ci" placeholder="Nos"/></td>
                  <td><input v-model.number="line.rate" type="number" min="0" step="0.01" class="inv-ci" style="text-align:right" @input="calcLine(line)"/></td>
                  <td style="text-align:right;padding:4px 10px;font-family:monospace;font-size:13px;font-weight:600;color:#1a1a2e">
                    {{fmtAmt(line.amount)}}
                  </td>
                  <td style="padding:4px 6px">
                    <button @click="removeLine(line.id)" class="inv-rm-line"><span v-html="icon('x',12)"></span></button>
                  </td>
                </tr>
                <tr v-if="!lines.length">
                  <td colspan="7" style="text-align:center;padding:20px;color:#9ca3af;font-size:13px">
                    No line items — click "Add Item"
                  </td>
                </tr>
              </tbody>
            </table>

            <!-- Totals -->
            <div class="inv-totals">
              <div class="inv-total-row">
                <span>Subtotal</span>
                <span class="inv-total-amt">{{fmtAmt(subtotal)}}</span>
              </div>
              <div class="inv-total-row">
                <span style="display:flex;align-items:center;gap:8px">
                  Tax (%)
                  <input v-model.number="form.tax_rate" type="number" min="0" max="100" step="0.1"
                    class="inv-ci" style="width:60px;text-align:right;padding:3px 6px"/>
                </span>
                <span class="inv-total-amt">{{fmtAmt(taxAmount)}}</span>
              </div>
              <div class="inv-total-row inv-grand-total">
                <span>Grand Total</span>
                <span class="inv-total-amt" style="font-size:16px;color:#1a6ef7">{{fmtAmt(grandTotal)}}</span>
              </div>
            </div>
          </div>

          <!-- Notes + Status -->
          <div class="inv-fg inv-fg2">
            <div>
              <label class="inv-lbl">Notes / Remarks</label>
              <textarea v-model="form.remarks" class="inv-fi" rows="3" style="resize:vertical" placeholder="Optional notes for the customer…"></textarea>
            </div>
            <div>
              <label class="inv-lbl">Status</label>
              <select v-model="form.docstatus" class="inv-fi">
                <option :value="0">Draft</option>
                <option :value="1">Submit (Post to Ledger)</option>
              </select>
              <div style="font-size:11px;color:#9ca3af;margin-top:4px">Submitted invoices are posted to the ledger and can be paid against.</div>
            </div>
          </div>
        </div>

        <div class="inv-dfooter">
          <div style="font-size:12px;color:#9ca3af">{{editingName?'Editing: '+editingName:'New invoice'}}</div>
          <div style="display:flex;gap:10px">
            <button class="inv-btn-ghost" @click="drawerOpen=false">Cancel</button>
            <button class="inv-btn-ghost" style="border-color:#3b82f6;color:#3b82f6" :disabled="drawerSaving" @click="saveInvoice(0)">Save Draft</button>
            <button class="inv-btn-primary" :disabled="drawerSaving" @click="saveInvoice(1)" style="min-width:140px">
              <span v-html="icon('check',13)"></span> {{drawerSaving?'Saving…':'Submit Invoice'}}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── View Drawer ── -->
    <div v-if="viewOpen&&viewInv" class="inv-drawer-bg" @click.self="viewOpen=false">
      <div class="inv-drawer-panel">
        <div class="inv-dh" :style="'background:'+statusBg(viewInv)">
          <div>
            <div class="inv-dh-title" style="color:#fff">{{viewInv.name}}</div>
            <div class="inv-dh-sub" style="color:rgba(255,255,255,.75)">
              {{viewInv.customer_name}} · {{fmtDate(viewInv.posting_date)}}
            </div>
          </div>
          <button class="inv-dclose" style="color:#fff;background:rgba(255,255,255,.15)" @click="viewOpen=false">
            <span v-html="icon('x',16)"></span>
          </button>
        </div>
        <div class="inv-dbody">
          <div style="display:flex;gap:24px;flex-wrap:wrap;margin-bottom:20px">
            <div><div class="inv-meta-lbl">Status</div><span class="inv-status-badge" :class="statusCls(viewInv)">{{statusLabel(viewInv)}}</span></div>
            <div><div class="inv-meta-lbl">Customer</div><div style="font-weight:600">{{viewInv.customer_name||viewInv.customer}}</div></div>
            <div><div class="inv-meta-lbl">Due Date</div><div :class="isOverdue(viewInv)?'text-danger':''">{{fmtDate(viewInv.due_date)||'—'}}</div></div>
            <div><div class="inv-meta-lbl">Grand Total</div><div style="font-weight:700;font-family:monospace;font-size:15px">{{fmtAmt(viewInv.grand_total)}}</div></div>
            <div><div class="inv-meta-lbl">Balance Due</div><div :class="viewInv.outstanding_amount>0?'text-danger':'text-success'" style="font-weight:700;font-family:monospace">{{fmtAmt(viewInv.outstanding_amount)}}</div></div>
          </div>

          <div v-if="viewInv.items&&viewInv.items.length" style="border:1px solid #e8ecf0;border-radius:8px;overflow:hidden;margin-bottom:16px">
            <div style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:8px;padding:8px 14px;background:#f8fafc;border-bottom:1px solid #e8ecf0;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#9ca3af">
              <div>Item</div><div style="text-align:right">Qty</div><div style="text-align:right">Rate</div><div style="text-align:right">Amount</div>
            </div>
            <div v-for="(it,i) in viewInv.items" :key="i"
              style="display:grid;grid-template-columns:2fr 1fr 1fr 1fr;gap:8px;padding:9px 14px;border-bottom:1px solid #f0f2f5;font-size:13px">
              <div><div style="font-weight:500">{{it.item_name||it.item_code}}</div><div v-if="it.description" style="font-size:11.5px;color:#9ca3af">{{it.description}}</div></div>
              <div style="text-align:right;font-family:monospace">{{flt(it.qty)}}</div>
              <div style="text-align:right;font-family:monospace">{{fmtAmt(it.rate)}}</div>
              <div style="text-align:right;font-family:monospace;font-weight:600">{{fmtAmt(it.amount)}}</div>
            </div>
          </div>
          <div v-else style="color:#9ca3af;font-size:13px;margin-bottom:16px">No item details available.</div>

          <div v-if="viewInv.remarks" style="background:#f8fafc;border-radius:8px;padding:12px 14px;font-size:13px;color:#374151;margin-bottom:16px">
            <div style="font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#9ca3af;margin-bottom:4px">Remarks</div>
            {{viewInv.remarks}}
          </div>
        </div>
        <div class="inv-dfooter" style="justify-content:space-between">
          <div style="font-size:12px;color:#9ca3af">Invoice {{viewInv.name}}</div>
          <div style="display:flex;gap:10px">
            <button v-if="viewInv.docstatus===0" class="inv-btn-ghost" @click="viewOpen=false;openEdit(viewInv)">
              <span v-html="icon('edit',13)"></span> Edit
            </button>
            <button v-if="viewInv.outstanding_amount>0&&viewInv.docstatus===1" class="inv-btn-primary" @click="viewOpen=false;openPayment(viewInv)">
              ₹ Record Payment
            </button>
            <button class="inv-btn-ghost" @click="viewOpen=false">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── Record Payment Modal ── -->
    <div v-if="payModal.open" class="rp-backdrop" @click.self="payModal.open=false">
      <div class="rp-dialog">
        <div class="rp-dialog-header">
          <span class="rp-dialog-title">Record Payment — {{payModal.invName}}</span>
          <button class="rp-close-btn" @click="payModal.open=false">✕</button>
        </div>

        <div v-if="payModal.loading" class="rp-loading">
          <div class="rp-spinner"></div> Loading…
        </div>

        <template v-else>
          <div class="rp-customer-strip">
            <div class="rp-avatar">{{(payModal.customerName||'?').charAt(0).toUpperCase()}}</div>
            <div>
              <div class="rp-cust-name">{{payModal.customerName}}</div>
              <div class="rp-cust-bal">Balance Due: <strong class="text-danger">{{fmtAmt(payModal.balanceDue)}}</strong></div>
            </div>
          </div>

          <div class="rp-body">
            <div class="rp-row">
              <div class="rp-field">
                <label class="rp-label rp-req">Amount Received (₹)</label>
                <input class="rp-input rp-amount-input" v-model.number="payForm.amount" type="number" min="0" step="0.01"/>
              </div>
              <div class="rp-field">
                <label class="rp-label rp-req">Payment Date</label>
                <input class="rp-input" v-model="payForm.date" type="date"/>
              </div>
            </div>
            <div class="rp-row">
              <div class="rp-field">
                <label class="rp-label">Payment Mode</label>
                <select class="rp-input rp-select" v-model="payForm.mode">
                  <option v-for="m in PAY_MODES" :key="m" :value="m">{{m}}</option>
                </select>
              </div>
              <div class="rp-field">
                <label class="rp-label">Reference / Cheque #</label>
                <input class="rp-input" v-model="payForm.ref" placeholder="UTR / Txn ID / Cheque #"/>
              </div>
            </div>
            <div class="rp-row">
              <div class="rp-field">
                <label class="rp-label">Deposit To (Bank Account)</label>
                <select class="rp-input rp-select" v-model="payForm.depositTo">
                  <option value="">— Default —</option>
                  <option v-for="a in payModal.bankAccounts" :key="a" :value="a">{{a}}</option>
                </select>
              </div>
              <div class="rp-field">
                <label class="rp-label">Bank Charges (if any)</label>
                <input class="rp-input" v-model.number="payForm.charges" type="number" min="0" step="0.01"/>
              </div>
            </div>
            <div class="rp-field rp-field-full">
              <label class="rp-label">Notes</label>
              <textarea class="rp-input rp-textarea" v-model="payForm.notes" rows="2" placeholder="Optional notes…"></textarea>
            </div>
            <div class="rp-summary">
              <span>Invoice Total: <strong>{{fmtAmt(payModal.grandTotal)}}</strong></span>
              <span>Recording: <strong>{{fmtAmt(payForm.amount||0)}}</strong></span>
              <span>Balance After: <strong :class="Math.max(0,payModal.balanceDue-(payForm.amount||0))>0?'text-danger':'text-success'">
                {{fmtAmt(Math.max(0,payModal.balanceDue-(payForm.amount||0)))}}
              </strong></span>
            </div>
          </div>

          <div class="rp-footer">
            <button class="rp-btn rp-btn-outline" @click="payModal.open=false">Cancel</button>
            <button class="rp-btn rp-btn-primary" :disabled="payModal.saving" @click="submitPayment">
              {{payModal.saving?'Saving…':'Record Payment'}}
            </button>
          </div>
        </template>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGET, apiPOST, apiSave, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt, fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();

const PAY_MODES  = ["Cash","Cheque","Bank Transfer","UPI","NEFT","RTGS","IMPS","Credit Card","Debit Card","DD"];
const FILTERS    = [
  { key: "all",     label: "All" },
  { key: "Draft",   label: "Draft" },
  { key: "Unpaid",  label: "Unpaid" },
  { key: "Overdue", label: "Overdue" },
  { key: "Paid",    label: "Paid" },
];

const list          = ref([]);
const loading       = ref(false);
const customers     = ref([]);
const items         = ref([]);
const activeFilter  = ref("all");
const search        = ref("");
const selectedRows  = ref(new Set());
const sortKey       = ref("posting_date");
const sortDir       = ref(-1);

/* ── Drawer (create/edit) ── */
const drawerOpen   = ref(false);
const editingName  = ref(null);
const drawerSaving = ref(false);
const form = reactive({
  customer: "", posting_date: "", due_date: "", po_no: "",
  tax_rate: 18, remarks: "", docstatus: 0,
});
const lines = ref([]);

/* ── View drawer ── */
const viewOpen  = ref(false);
const viewInv   = ref(null);

/* ── Payment modal ── */
const payModal = reactive({
  open: false, loading: false, saving: false,
  invName: "", customerName: "", grandTotal: 0, balanceDue: 0, bankAccounts: [],
});
const payForm = reactive({
  amount: 0, date: "", mode: "Cash", ref: "", depositTo: "", charges: 0, notes: "",
});

/* ── Helpers ── */
function fmtAmt(v) {
  const n = Number(v || 0);
  return "₹" + n.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function todayStr() { return new Date().toISOString().slice(0, 10); }
function dueDateDefault() {
  const d = new Date(); d.setDate(d.getDate() + 30);
  return d.toISOString().slice(0, 10);
}

function isOverdue(inv) {
  return inv.outstanding_amount > 0 && inv.due_date && new Date(inv.due_date) < new Date();
}
function statusLabel(inv) {
  if (isOverdue(inv)) {
    const days = Math.floor((Date.now() - new Date(inv.due_date)) / 86400000);
    return `OVERDUE ${days}d`;
  }
  return (inv.status || (inv.docstatus === 0 ? "Draft" : "Unpaid")).toUpperCase();
}
function statusCls(inv) {
  if (isOverdue(inv)) return "status-overdue";
  const s = (inv.status || "").toLowerCase();
  if (s === "paid") return "status-paid";
  if (s === "submitted" || s === "unpaid") return "status-unpaid";
  if (s === "cancelled") return "status-cancelled";
  return "status-draft";
}
function statusBg(inv) {
  if (isOverdue(inv)) return "linear-gradient(135deg,#7f1d1d,#dc2626)";
  const s = (inv.status || "").toLowerCase();
  if (s === "paid") return "linear-gradient(135deg,#064e3b,#059669)";
  if (s === "submitted" || s === "unpaid") return "linear-gradient(135deg,#78350f,#d97706)";
  return "linear-gradient(135deg,#1e3a5f,#2563eb)";
}
function pillCls(k) {
  return { Draft: "pc-muted", Unpaid: "pc-amber", Overdue: "pc-red", Paid: "pc-green" }[k] || "pc-muted";
}

/* ── Computed ── */
const counts = computed(() => ({
  Draft:   list.value.filter(i => i.docstatus === 0).length,
  Unpaid:  list.value.filter(i => !isOverdue(i) && (i.status === "Unpaid" || (i.docstatus === 1 && i.outstanding_amount > 0))).length,
  Overdue: list.value.filter(isOverdue).length,
  Paid:    list.value.filter(i => i.outstanding_amount <= 0 && i.docstatus === 1).length,
}));

const summary = computed(() => ({
  unpaidCount: list.value.filter(i => i.outstanding_amount > 0 && !isOverdue(i)).length,
  overdueCount: list.value.filter(isOverdue).length,
  totalDue: list.value.reduce((s, i) => s + flt(i.outstanding_amount), 0),
}));

const allSelected = computed(() =>
  sorted.value.length > 0 && sorted.value.every(i => selectedRows.value.has(i.name))
);

const filtered = computed(() => {
  const q = search.value.toLowerCase();
  let r = list.value;
  if (activeFilter.value === "Draft")   r = r.filter(i => i.docstatus === 0);
  else if (activeFilter.value === "Overdue") r = r.filter(isOverdue);
  else if (activeFilter.value === "Unpaid")  r = r.filter(i => !isOverdue(i) && i.outstanding_amount > 0 && i.docstatus === 1);
  else if (activeFilter.value === "Paid")    r = r.filter(i => i.outstanding_amount <= 0 && i.docstatus === 1);
  if (q) r = r.filter(i => (i.name + (i.customer_name || "") + (i.customer || "") + (i.po_no || "")).toLowerCase().includes(q));
  return r;
});

const sorted = computed(() => {
  return [...filtered.value].sort((a, b) => {
    const va = a[sortKey.value] ?? "", vb = b[sortKey.value] ?? "";
    if (va < vb) return -1 * sortDir.value;
    if (va > vb) return  1 * sortDir.value;
    return 0;
  });
});

const subtotal  = computed(() => lines.value.reduce((s, l) => s + flt(l.amount), 0));
const taxAmount = computed(() => Math.round(subtotal.value * flt(form.tax_rate) / 100 * 100) / 100);
const grandTotal = computed(() => subtotal.value + taxAmount.value);

/* ── Load ── */
async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Sales Invoice", {
      fields: ["name","customer","customer_name","posting_date","due_date",
               "grand_total","outstanding_amount","status","docstatus","po_no"],
      limit: 200,
      order: "posting_date desc",
    }) || [];
  } catch { list.value = []; toast("Could not load invoices", "error"); }
  loading.value = false;
}

async function loadCustomers() {
  try {
    customers.value = await apiList("Customer", {
      fields: ["name","customer_name"], limit: 500, order: "customer_name asc",
    }) || [];
  } catch {}
}

async function loadItems() {
  try {
    items.value = await apiList("Item", {
      fields: ["name","item_name","standard_rate","stock_uom"], limit: 500, order: "item_name asc",
    }) || [];
  } catch {}
}

/* ── Sorting & selection ── */
function sort(key) {
  sortKey.value === key ? (sortDir.value *= -1) : (sortKey.value = key, sortDir.value = -1);
}
function sortArrow(k) {
  return sortKey.value !== k ? "" : sortDir.value === 1 ? "↑" : "↓";
}
function toggleAll(e) {
  if (e.target.checked) sorted.value.forEach(i => selectedRows.value.add(i.name));
  else selectedRows.value.clear();
  selectedRows.value = new Set(selectedRows.value);
}
function toggleRow(name) {
  const s = new Set(selectedRows.value);
  s.has(name) ? s.delete(name) : s.add(name);
  selectedRows.value = s;
}

/* ── Line item helpers ── */
function addLine() {
  lines.value.push({ id: Date.now(), item_code: "", item_name: "", description: "", qty: 1, rate: 0, uom: "Nos", amount: 0 });
}
function removeLine(id) {
  lines.value = lines.value.filter(l => l.id !== id);
}
function calcLine(line) {
  line.amount = Math.round(flt(line.qty) * flt(line.rate) * 100) / 100;
}
function onItemChange(line) {
  const it = items.value.find(i => i.name === line.item_code);
  if (it) {
    line.item_name = it.item_name;
    line.rate = flt(it.standard_rate);
    line.uom  = it.stock_uom || "Nos";
    calcLine(line);
  }
}
function onCustomerChange() {}  // future: auto-fill payment terms

/* ── Drawer open ── */
function openAdd() {
  editingName.value = null;
  lines.value = [{ id: Date.now(), item_code: "", item_name: "", description: "", qty: 1, rate: 0, uom: "Nos", amount: 0 }];
  Object.assign(form, { customer: "", posting_date: todayStr(), due_date: dueDateDefault(), po_no: "", tax_rate: 18, remarks: "", docstatus: 0 });
  drawerOpen.value = true;
}
function openEdit(inv) {
  editingName.value = inv.name;
  Object.assign(form, {
    customer: inv.customer || "",
    posting_date: inv.posting_date || todayStr(),
    due_date: inv.due_date || dueDateDefault(),
    po_no: inv.po_no || "",
    tax_rate: 18,
    remarks: inv.remarks || "",
    docstatus: inv.docstatus || 0,
  });
  lines.value = (inv.items || []).map((it, i) => ({
    id: Date.now() + i,
    item_code: it.item_code || "",
    item_name: it.item_name || "",
    description: it.description || "",
    qty: flt(it.qty) || 1,
    rate: flt(it.rate) || 0,
    uom: it.uom || "Nos",
    amount: flt(it.amount) || 0,
  }));
  if (!lines.value.length) addLine();
  drawerOpen.value = true;
}
function openView(inv) {
  viewInv.value = inv;
  viewOpen.value = true;
}

/* ── Save invoice ── */
async function saveInvoice(docstatus) {
  if (!form.customer) { toast("Customer is required", "error"); return; }
  if (!form.posting_date) { toast("Invoice date is required", "error"); return; }
  const hasItems = lines.value.some(l => l.item_code && flt(l.qty) > 0);
  if (!hasItems) { toast("Add at least one line item", "error"); return; }
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const invItems = lines.value
      .filter(l => l.item_code)
      .map(l => ({
        item_code: l.item_code,
        item_name: l.item_name || l.item_code,
        description: l.description || l.item_name || l.item_code,
        qty: flt(l.qty),
        rate: flt(l.rate),
        uom: l.uom || "Nos",
        amount: flt(l.amount),
      }));

    const taxes = form.tax_rate > 0 ? [{
      charge_type: "On Net Total",
      account_head: "Output Tax - " + (company || ""),
      description: "GST @ " + form.tax_rate + "%",
      rate: form.tax_rate,
    }] : [];

    const doc = {
      doctype: "Sales Invoice",
      customer: form.customer,
      posting_date: form.posting_date,
      due_date: form.due_date || form.posting_date,
      po_no: form.po_no || "",
      remarks: form.remarks || "",
      items: invItems,
      taxes,
      docstatus,
      company,
    };
    if (editingName.value) doc.name = editingName.value;

    await apiSave(doc);
    await load();
    toast(docstatus === 1 ? "Invoice submitted" : "Invoice saved as draft");
    drawerOpen.value = false;
  } catch (e) { toast("Save failed: " + e.message, "error"); }
  drawerSaving.value = false;
}

/* ── Payment modal ── */
async function openPayment(inv) {
  payModal.open = true;
  payModal.loading = true;
  payModal.invName = inv.name;
  payModal.customerName = inv.customer_name || inv.customer;
  payModal.grandTotal = flt(inv.grand_total);
  payModal.balanceDue = flt(inv.outstanding_amount);
  payModal.saving = false;
  payModal.bankAccounts = [];
  Object.assign(payForm, { amount: flt(inv.outstanding_amount), date: todayStr(), mode: "Cash", ref: "", depositTo: "", charges: 0, notes: "" });
  try {
    const d = await apiGET("zoho_books_clone.api.books_data.get_payment_defaults", { invoice_name: inv.name });
    if (d) {
      payModal.bankAccounts = (d.bank_accounts || []).map(a => a.name || a);
      payForm.depositTo = payModal.bankAccounts[0] || "";
      payForm.mode = (d.payment_modes || [])[0] || "Cash";
    }
  } catch {}
  payModal.loading = false;
}

async function submitPayment() {
  if (!payForm.amount || payForm.amount <= 0) { toast("Enter a valid amount", "error"); return; }
  payModal.saving = true;
  try {
    const res = await apiGET("zoho_books_clone.api.books_data.record_payment", {
      invoice_name:    payModal.invName,
      amount_received: payForm.amount,
      payment_date:    payForm.date,
      payment_mode:    payForm.mode,
      deposit_to:      payForm.depositTo || "",
      bank_charges:    payForm.charges || 0,
      reference_no:    payForm.ref || "",
      notes:           payForm.notes || "",
      save_as_draft:   0,
    });
    toast("Payment recorded — " + (res?.payment_entry || ""));
    payModal.open = false;
    load();
  } catch (e) { toast("Payment failed: " + e.message, "error"); }
  payModal.saving = false;
}

onMounted(() => { load(); loadCustomers(); loadItems(); });
</script>

<style scoped>
/* ── Page ── */
.inv-page { background:#fff; min-height:100%; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif; color:#1a1a2e; }

/* ── Toolbar ── */
.inv-toolbar { display:flex; align-items:center; justify-content:space-between; padding:16px 24px 12px; border-bottom:1px solid #e8ecf0; gap:12px; flex-wrap:wrap; }
.inv-toolbar-left { display:flex; align-items:center; gap:8px; }
.inv-toolbar-right { display:flex; align-items:center; gap:8px; flex-wrap:wrap; }
.inv-heading { font-size:16px; font-weight:700; color:#1a1a2e; margin:0; }
.inv-search-wrap { display:flex; align-items:center; gap:7px; border:1px solid #e8ecf0; border-radius:20px; padding:6px 12px; background:#f9fafb; }
.inv-search-input { border:none; outline:none; background:transparent; font-size:13px; width:180px; color:#374151; }
.inv-btn-primary { display:inline-flex; align-items:center; gap:6px; background:#1a6ef7; color:#fff; border:none; border-radius:6px; padding:7px 16px; font-size:13px; font-weight:600; cursor:pointer; transition:background .15s; }
.inv-btn-primary:hover { background:#155fd4; }
.inv-btn-primary:disabled { opacity:.55; cursor:not-allowed; }
.inv-btn-ghost { display:inline-flex; align-items:center; gap:6px; background:#fff; color:#374151; border:1px solid #e8ecf0; border-radius:6px; padding:7px 12px; font-size:13px; font-weight:500; cursor:pointer; transition:all .15s; }
.inv-btn-ghost:hover { border-color:#374151; }

/* ── Summary strip ── */
.inv-sum-strip { display:grid; grid-template-columns:repeat(4,1fr); gap:0; border-bottom:1px solid #e8ecf0; }
.inv-sum-card { padding:14px 24px; border-right:1px solid #e8ecf0; }
.inv-sum-card:last-child { border-right:none; }
.inv-sum-lbl { font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:.05em; color:#9ca3af; margin-bottom:4px; }
.inv-sum-val { font-size:20px; font-weight:700; font-family:monospace; color:#1a1a2e; }

/* ── Filter pills ── */
.inv-filters { display:flex; gap:8px; padding:12px 24px; border-bottom:1px solid #e8ecf0; flex-wrap:wrap; }
.inv-pill { display:inline-flex; align-items:center; gap:6px; padding:5px 14px; border-radius:20px; font-size:12.5px; font-weight:600; border:1.5px solid #e8ecf0; background:#fff; color:#6b7280; cursor:pointer; transition:all .15s; }
.inv-pill:hover { border-color:#1a6ef7; color:#1a6ef7; }
.inv-pill.active { background:#eaf1ff; border-color:#1a6ef7; color:#1a6ef7; }
.inv-pill-count { font-size:10.5px; font-weight:700; padding:1px 6px; border-radius:12px; }
.pc-muted { background:#e5e7eb; color:#6b7280; }
.pc-amber { background:#fef3c7; color:#d97706; }
.pc-red   { background:#fee2e2; color:#dc2626; }
.pc-green { background:#d1fae5; color:#059669; }

/* ── Table ── */
.inv-table-wrap { overflow-x:auto; }
.inv-table { width:100%; border-collapse:collapse; font-size:13px; }
.inv-table th { padding:10px 14px; border-bottom:2px solid #e8ecf0; font-size:10.5px; font-weight:700; letter-spacing:.06em; color:#6b7280; text-align:left; white-space:nowrap; background:#fff; user-select:none; }
.inv-table th.sortable { cursor:pointer; }
.inv-table th.sortable:hover { color:#1a6ef7; }
.sort-arrow { font-size:10px; margin-left:2px; color:#1a6ef7; }
.th-check { width:40px; padding-left:20px; }
.inv-table td { padding:11px 14px; border-bottom:1px solid #f0f2f5; color:#374151; vertical-align:middle; cursor:pointer; }
.td-check { cursor:default; padding-left:20px; }
.inv-row:hover td { background:#f8faff; }
.inv-row.selected td { background:#eaf1ff; }
.inv-table tr:last-child td { border-bottom:none; }
.inv-link { color:#1a6ef7; font-weight:600; }
.inv-customer { font-weight:600; color:#1a1a2e; }
.mono-sm { font-family:monospace; font-size:12.5px; }
.ta-r { text-align:right; }
.text-danger  { color:#dc2626; }
.text-success { color:#059669; }
.text-muted   { color:#9ca3af; }

/* ── Status badges ── */
.inv-status-badge { display:inline-flex; align-items:center; padding:3px 10px; border-radius:4px; font-size:10.5px; font-weight:700; letter-spacing:.04em; white-space:nowrap; }
.status-overdue  { color:#dc2626; background:transparent; }
.status-paid     { color:#059669; background:#d1fae5; }
.status-unpaid   { color:#d97706; background:#fef3c7; }
.status-draft    { color:#6b7280; background:#f3f4f6; }
.status-cancelled{ color:#dc2626; background:#fee2e2; }

/* ── Action buttons ── */
.inv-act-btn { background:none; border:1px solid #e8ecf0; border-radius:5px; padding:4px 6px; cursor:pointer; color:#6b7280; transition:all .12s; display:inline-flex; align-items:center; }
.inv-act-btn:hover { border-color:#374151; color:#374151; }
.inv-act-pay { border-color:rgba(26,110,247,.3); color:#1a6ef7; font-weight:700; font-size:11px; }
.inv-act-pay:hover { background:#eaf1ff; }

/* ── Shimmer ── */
.shimmer { height:12px; border-radius:4px; background:linear-gradient(90deg,#f0f2f5 25%,#e4e7ec 50%,#f0f2f5 75%); background-size:200% 100%; animation:shimmer 1.4s infinite; }
@keyframes shimmer { 0%{background-position:200% 0} 100%{background-position:-200% 0} }

/* ── Empty state ── */
.empty-state { padding:48px 0 !important; text-align:center; cursor:default !important; }
.empty-inner { display:flex; flex-direction:column; align-items:center; gap:10px; color:#9ca3af; font-size:13px; }

/* ── Drawer ── */
.inv-drawer-bg { position:fixed; inset:0; z-index:8000; background:rgba(15,23,42,.45); display:flex; justify-content:flex-end; backdrop-filter:blur(2px); }
.inv-drawer-panel { width:680px; max-width:96vw; height:100%; background:#fff; display:flex; flex-direction:column; box-shadow:-20px 0 60px rgba(0,0,0,.15); overflow:hidden; }
.inv-dh { display:flex; align-items:center; justify-content:space-between; padding:18px 24px; background:linear-gradient(135deg,#1e3a5f,#1a6ef7); flex-shrink:0; }
.inv-dh-title { color:#fff; font-size:16px; font-weight:700; }
.inv-dh-sub   { color:rgba(255,255,255,.75); font-size:12px; margin-top:2px; }
.inv-dclose { background:rgba(255,255,255,.15); border:none; cursor:pointer; width:30px; height:30px; border-radius:8px; color:#fff; display:grid; place-items:center; }
.inv-dbody { flex:1; overflow-y:auto; padding:20px 24px; }
.inv-dfooter { padding:14px 24px; border-top:1px solid #e8ecf0; display:flex; justify-content:space-between; align-items:center; background:#f8fafc; flex-shrink:0; }
.inv-sec-lbl { font-size:10.5px; font-weight:700; letter-spacing:.6px; text-transform:uppercase; color:#9ca3af; margin-bottom:12px; margin-top:4px; padding-top:16px; border-top:1px solid #f0f2f5; }
.inv-sec-lbl:first-child { border-top:none; padding-top:0; margin-top:0; }
.inv-fg { display:grid; gap:12px; margin-bottom:14px; }
.inv-fg2 { grid-template-columns:1fr 1fr; }
.inv-fg3 { grid-template-columns:1fr 1fr 1fr; }
.inv-lbl { display:block; font-size:11.5px; font-weight:600; color:#495057; margin-bottom:5px; }
.inv-fi { width:100%; border:1px solid #e2e8f0; border-radius:6px; padding:7px 10px; font-size:13px; font-family:inherit; outline:none; box-sizing:border-box; }
.inv-fi:focus { border-color:#1a6ef7; box-shadow:0 0 0 3px rgba(26,110,247,.08); }
.inv-add-line-btn { display:inline-flex; align-items:center; gap:5px; border:1px solid rgba(26,110,247,.3); background:#eaf1ff; color:#1a6ef7; border-radius:6px; padding:5px 12px; font-size:12.5px; font-weight:600; cursor:pointer; }

/* ── Line items table ── */
.inv-lines-tbl { width:100%; border-collapse:collapse; font-size:13px; }
.inv-lines-tbl th { padding:8px 10px; background:#f8fafc; border-bottom:1px solid #e8ecf0; font-size:10.5px; font-weight:700; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; text-align:left; }
.inv-lines-tbl td { padding:4px 6px; border-bottom:1px solid #f0f2f5; }
.inv-ci { width:100%; border:1px solid #e2e8f0; border-radius:5px; padding:5px 7px; font-size:12.5px; font-family:inherit; outline:none; }
.inv-ci:focus { border-color:#1a6ef7; }
.inv-rm-line { background:none; border:1px solid rgba(220,38,38,.3); border-radius:4px; padding:3px 5px; cursor:pointer; color:#dc2626; display:inline-flex; align-items:center; }

/* ── Totals ── */
.inv-totals { padding:12px 14px; background:#f8fafc; border-top:1px solid #e8ecf0; display:flex; flex-direction:column; gap:6px; align-items:flex-end; }
.inv-total-row { display:flex; justify-content:space-between; align-items:center; width:280px; font-size:13px; color:#374151; }
.inv-total-amt { font-family:monospace; font-weight:600; font-size:13px; }
.inv-grand-total { border-top:1px solid #e8ecf0; padding-top:8px; margin-top:2px; font-weight:700; font-size:14px; }

/* ── View meta ── */
.inv-meta-lbl { font-size:10.5px; font-weight:600; text-transform:uppercase; letter-spacing:.04em; color:#9ca3af; margin-bottom:4px; }

/* ══ Record Payment ══ */
.rp-backdrop { position:fixed; inset:0; background:rgba(15,23,42,.45); display:flex; align-items:center; justify-content:center; z-index:9999; backdrop-filter:blur(2px); }
.rp-dialog { background:#fff; border-radius:10px; box-shadow:0 20px 60px rgba(0,0,0,.2); width:min(640px,95vw); max-height:90vh; overflow-y:auto; display:flex; flex-direction:column; animation:rp-in .2s cubic-bezier(.34,1.56,.64,1); }
@keyframes rp-in { from{opacity:0;transform:scale(.95) translateY(10px)} }
.rp-dialog-header { display:flex; align-items:center; justify-content:space-between; padding:16px 22px 14px; border-bottom:1px solid #e8ecf0; }
.rp-dialog-title { font-size:15px; font-weight:700; color:#1a1a2e; }
.rp-close-btn { background:none; border:none; font-size:16px; color:#9ca3af; cursor:pointer; border-radius:50%; width:28px; height:28px; display:grid; place-items:center; }
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
.rp-select { cursor:pointer; }
.rp-textarea { resize:vertical; }
.rp-summary { background:#f8fafc; border-radius:8px; padding:10px 14px; display:flex; justify-content:space-between; font-size:12.5px; color:#374151; flex-wrap:wrap; gap:8px; }
.rp-footer { display:flex; align-items:center; justify-content:flex-end; gap:10px; padding:14px 22px; border-top:1px solid #e8ecf0; background:#f8fafc; }
.rp-btn { display:inline-flex; align-items:center; gap:6px; border-radius:6px; padding:8px 18px; font-size:13px; font-weight:600; cursor:pointer; transition:all .15s; }
.rp-btn:disabled { opacity:.55; cursor:not-allowed; }
.rp-btn-outline { background:#fff; border:1px solid #e2e8f0; color:#374151; }
.rp-btn-secondary { background:#fff; border:1px solid #3b82f6; color:#3b82f6; }
.rp-btn-primary { background:#1a6ef7; border:1px solid #1a6ef7; color:#fff; }
.rp-btn-primary:hover:not(:disabled) { background:#155fd4; }
</style>
