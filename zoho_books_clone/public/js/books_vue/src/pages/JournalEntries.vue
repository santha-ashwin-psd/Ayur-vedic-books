<template>
<div class="b-page jen-page">

  <div class="jen-info-banner">
    <span v-html="icon('info',15)" style="flex-shrink:0"></span>
    <span>Journal entries record any financial transaction not covered by Sales/Purchase. Total <strong>Debits must equal Credits</strong> in every entry.</span>
  </div>

  <div class="jen-sum-strip">
    <div class="jen-sum-card">
      <div class="jen-sum-lbl">Total Entries</div>
      <div class="jen-sum-val">{{summary.total}}</div>
    </div>
    <div class="jen-sum-card">
      <div class="jen-sum-lbl" style="color:#3b5bdb">This Month</div>
      <div class="jen-sum-val" style="color:#3b5bdb">{{summary.month}}</div>
    </div>
    <div class="jen-sum-card">
      <div class="jen-sum-lbl" style="color:#2f9e44">Total Debits</div>
      <div class="jen-sum-val" style="color:#2f9e44">{{summary.totalDr>=1000?'₹'+(summary.totalDr/1000).toFixed(1)+'K':fmtINR(summary.totalDr)||'₹0'}}</div>
    </div>
    <div class="jen-sum-card">
      <div class="jen-sum-lbl" style="color:#c92a2a">Drafts</div>
      <div class="jen-sum-val" style="color:#c92a2a">{{summary.drafts}}</div>
    </div>
  </div>

  <div class="b-action-bar" style="margin-bottom:14px;flex-wrap:wrap;gap:10px">
    <div style="display:flex;gap:6px;flex-wrap:wrap">
      <button class="jen-pill" :class="{active:currentFilter==='all'}" @click="currentFilter='all'">All</button>
      <button class="jen-pill" :class="{active:currentFilter==='Draft'}" @click="currentFilter='Draft'">
        Draft <span class="jen-pc" style="background:#f1f3f5;color:#868e96">{{counts.Draft}}</span>
      </button>
      <button class="jen-pill" :class="{active:currentFilter==='Submitted'}" @click="currentFilter='Submitted'">
        Submitted <span class="jen-pc" style="background:#ebfbee;color:#2f9e44">{{counts.Submitted}}</span>
      </button>
      <button class="jen-pill" :class="{active:currentFilter==='Cancelled'}" @click="currentFilter='Cancelled'">
        Cancelled <span class="jen-pc" style="background:#ffe3e3;color:#c92a2a">{{counts.Cancelled}}</span>
      </button>
    </div>
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <div style="display:flex;align-items:center;gap:6px;font-size:12.5px;color:#868e96">
        <span>From</span>
        <input type="date" v-model="dateFrom" class="jen-date-input"/>
        <span>To</span>
        <input type="date" v-model="dateTo" class="jen-date-input"/>
      </div>
      <div class="b-search" style="border-radius:20px;padding:6px 12px">
        <span v-html="icon('search',13)"></span>
        <input v-model="searchQ" placeholder="Search JE, narration..." style="border:none;outline:none;font-size:13px;background:transparent;width:180px"/>
      </div>
      <button class="b-btn b-btn-ghost" @click="load"><span v-html="icon('refresh',13)"></span> Refresh</button>
      <button class="b-btn b-btn-primary" @click="openAdd"><span v-html="icon('plus',13)"></span> New Entry</button>
    </div>
  </div>

  <div class="b-card" style="padding:0;overflow:hidden">
    <table class="b-table">
      <thead>
        <tr>
          <th>Entry #</th><th>Date</th><th>Type</th><th>Narration</th>
          <th class="ta-r">Total Debit</th><th class="ta-r">Total Credit</th>
          <th>Lines</th><th>Status</th>
          <th style="text-align:center;width:100px">Actions</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="loading">
          <tr v-for="n in 6" :key="n"><td colspan="9" style="padding:12px 14px"><div class="b-shimmer" style="height:12px"></div></td></tr>
        </template>
        <template v-else-if="filteredRows.length===0">
          <tr><td colspan="9" class="b-empty">
            <div style="font-size:32px;margin-bottom:8px">📄</div>
            <div style="font-weight:600;margin-bottom:4px">{{searchQ?'No entries match':'No journal entries yet'}}</div>
            <div style="font-size:13px;color:#868e96;margin-bottom:12px">{{searchQ?'Try a different search':'Record adjustments, depreciation, accruals and more'}}</div>
            <button v-if="!searchQ" class="b-btn b-btn-primary" @click="openAdd"><span v-html="icon('plus',13)"></span> New Entry</button>
          </td></tr>
        </template>
        <template v-else>
          <tr v-for="e in filteredRows" :key="e.name" class="clickable" @click="openView(e.name)">
            <td style="font-family:monospace;font-size:12px;font-weight:700;color:#2563eb">{{e.name}}</td>
            <td style="font-size:12.5px;color:#868e96">{{fmtDateLocal(e.date)}}</td>
            <td><span class="b-badge" :class="JE_TYPE_COLOR[e.type]||'je-type-info'">{{e.type||'Journal Entry'}}</span></td>
            <td style="font-size:13px;max-width:200px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{e.narration||'—'}}</td>
            <td class="ta-r" style="font-family:monospace;font-weight:600;color:#c92a2a">{{fmtINR(e.total_debit)}}</td>
            <td class="ta-r" style="font-family:monospace;font-weight:600;color:#2f9e44">{{fmtINR(e.total_credit)}}</td>
            <td style="font-size:12px;color:#868e96">{{(e.lines||[]).length||'—'}}</td>
            <td><span class="b-badge" :class="JE_STATUS_COLOR[e.status]||'je-s-draft'">{{e.status}}</span></td>
            <td style="text-align:center">
              <div style="display:flex;gap:4px;justify-content:center">
                <button class="b-icon-btn" @click.stop="openView(e.name)" title="View"><span v-html="icon('eye',14)"></span></button>
                <button v-if="e.status==='Draft'" class="b-icon-btn" @click.stop="openEdit(e.name)" title="Edit"><span v-html="icon('edit',14)"></span></button>
                <button v-if="e.status==='Draft'" class="b-icon-btn danger" @click.stop="confirmAction(e.name,'delete')" title="Delete"><span v-html="icon('trash',14)"></span></button>
                <button v-if="e.status==='Submitted'" class="b-icon-btn danger" @click.stop="confirmAction(e.name,'cancel')" title="Cancel"><span v-html="icon('cancel',14)"></span></button>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
  <div style="text-align:right;font-size:12px;color:#868e96;padding:6px 4px">Showing {{filteredRows.length}} of {{allEntries.length}} entries</div>

  <Teleport to="body">
    <div v-if="drawerOpen" class="coa-drawer-bg" @click.self="drawerOpen=false">
      <div class="jen-drawer-panel">
        <div class="coa-dh">
          <div><div class="coa-dh-title">{{editingName?'Edit Journal Entry':'New Journal Entry'}}</div>
          <div class="coa-dh-sub">Debits must equal Credits</div></div>
          <button class="coa-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="coa-dbody">

          <span class="coa-sec-lbl" style="margin-top:0;border-top:none;padding-top:0">Quick Template <span style="font-weight:400;text-transform:none;letter-spacing:0">(optional)</span></span>
          <div class="jen-tpl-grid">
            <div v-for="tpl in JE_TEMPLATES" :key="tpl.id"
              class="jen-tpl-card" :class="{selected:selectedTpl===tpl.id}"
              @click="applyTemplate(tpl.id)">
              <div class="jen-tpl-name">{{tpl.name}}</div>
              <div class="jen-tpl-desc">{{tpl.desc}}</div>
            </div>
          </div>

          <span class="coa-sec-lbl">Entry Details</span>
          <div class="coa-fg jen-fg4">
            <div>
              <label class="coa-lbl">Date <span style="color:#c92a2a">*</span></label>
              <input v-model="form.date" type="date" class="coa-fi"/>
            </div>
            <div>
              <label class="coa-lbl">Entry Type</label>
              <select v-model="form.type" class="coa-fi">
                <option value="Journal Entry">Journal Entry</option>
                <option value="Depreciation">Depreciation</option>
                <option value="Accrual">Accrual Entry</option>
                <option value="Prepaid">Prepaid Expense</option>
                <option value="Provision">Provision Entry</option>
                <option value="Contra">Contra Entry</option>
                <option value="Rectification">Rectification Entry</option>
                <option value="Opening Entry">Opening Entry</option>
              </select>
            </div>
            <div>
              <label class="coa-lbl">Cheque / Ref No.</label>
              <input v-model="form.ref" class="coa-fi" placeholder="Optional reference"/>
            </div>
            <div>
              <label class="coa-lbl">Cheque Date</label>
              <input v-model="form.cheque_date" type="date" class="coa-fi"/>
            </div>
          </div>
          <div style="margin-bottom:16px">
            <label class="coa-lbl">Narration <span style="color:#c92a2a">*</span></label>
            <textarea v-model="form.narration" class="coa-fi" rows="2" style="resize:vertical" placeholder="Describe this journal entry — e.g. Depreciation for March 2026..."></textarea>
          </div>

          <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
            <span style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#868e96">Lines</span>
            <div style="display:flex;gap:8px">
              <button @click="addLine('Debit')" class="jen-add-line-btn" style="border-color:rgba(201,42,42,.3);color:#c92a2a">
                <span v-html="icon('plus',12)"></span> Debit Row
              </button>
              <button @click="addLine('Credit')" class="jen-add-line-btn" style="border-color:rgba(47,158,68,.3);color:#2f9e44">
                <span v-html="icon('plus',12)"></span> Credit Row
              </button>
            </div>
          </div>

          <div class="jen-balance-bar" :class="lines.length&&(totalDr>0||totalCr>0)?(balanced?'jen-bal-ok':'jen-bal-err'):'jen-bal-zero'">
            <div style="display:flex;align-items:center;gap:8px">
              <span v-html="icon(balanced&&(totalDr>0)?'check':'info',14)"></span>
              <span>{{!lines.length||(totalDr===0&&totalCr===0)?'Add debit and credit lines':balanced?'Balanced — ready to post':'Difference: ₹'+Math.abs(totalDr-totalCr).toLocaleString('en-IN',{minimumFractionDigits:2})}}</span>
            </div>
            <div style="font-family:monospace;font-weight:700">
              <span v-if="totalDr>0||totalCr>0">Dr: ₹{{totalDr.toLocaleString('en-IN',{minimumFractionDigits:2})}} / Cr: ₹{{totalCr.toLocaleString('en-IN',{minimumFractionDigits:2})}}</span>
            </div>
          </div>

          <div style="border:1px solid #e8ecf0;border-radius:8px;overflow:hidden;margin-bottom:16px;overflow-x:auto">
            <table class="jen-lines-tbl" style="min-width:680px">
              <thead>
                <tr>
                  <th style="width:28%">Account <span style="color:#c92a2a">*</span></th>
                  <th style="width:20%">Party (Customer/Vendor)</th>
                  <th style="width:15%">Cost Center</th>
                  <th style="width:13%;text-align:right">Debit (Dr)</th>
                  <th style="width:13%;text-align:right">Credit (Cr)</th>
                  <th style="width:7%">Type</th>
                  <th style="width:4%"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="line in lines" :key="line.id">
                  <td>
                    <SearchableSelect v-model="line.account" :options="accounts" placeholder="— Select Account —" :compact="true" class="ss-cell-wrap"/>
                  </td>
                  <td><input v-model="line.party" class="jen-ci" placeholder="Optional"/></td>
                  <td>
                    <select v-model="line.cost_center" class="jen-ci">
                      <option value="">—</option>
                      <option v-for="cc in costCenters" :key="cc" :value="cc">{{cc}}</option>
                    </select>
                  </td>
                  <td><input v-model="line.dr" type="number" min="0" step="0.01" class="jen-ci" style="text-align:right" placeholder="0.00" @input="line.cr=''"/></td>
                  <td><input v-model="line.cr" type="number" min="0" step="0.01" class="jen-ci" style="text-align:right" placeholder="0.00" @input="line.dr=''"/></td>
                  <td style="font-size:11px;color:#868e96;padding:0 6px">{{flt(line.dr)>0?'Dr':flt(line.cr)>0?'Cr':'—'}}</td>
                  <td style="padding:4px 6px">
                    <button @click="removeLine(line.id)" class="b-icon-btn danger" style="padding:3px 5px"><span v-html="icon('x',12)"></span></button>
                  </td>
                </tr>
                <tr v-if="!lines.length">
                  <td colspan="7" style="text-align:center;padding:20px;color:#868e96;font-size:13px">No lines — click Debit Row or Credit Row to add</td>
                </tr>
                <tr class="jen-total-row">
                  <td colspan="3" style="padding:8px 10px;font-size:12px;font-weight:700;color:#868e96;text-transform:uppercase;letter-spacing:.04em">Totals</td>
                  <td style="text-align:right;padding:8px 10px;font-family:monospace;font-weight:700;color:#c92a2a">₹{{totalDr.toLocaleString('en-IN',{minimumFractionDigits:2})}}</td>
                  <td style="text-align:right;padding:8px 10px;font-family:monospace;font-weight:700;color:#2f9e44">₹{{totalCr.toLocaleString('en-IN',{minimumFractionDigits:2})}}</td>
                  <td colspan="2"></td>
                </tr>
              </tbody>
            </table>
          </div>

          <div class="coa-fg coa-fg2">
            <div>
              <label class="coa-lbl">Cost Center (global)</label>
              <select v-model="form.cost_center" class="coa-fi">
                <option value="">— All Centers —</option>
                <option v-for="cc in costCenters" :key="cc" :value="cc">{{cc}}</option>
              </select>
            </div>
            <div>
              <label class="coa-lbl">Status</label>
              <select v-model="form.status" class="coa-fi">
                <option value="Draft">Draft</option>
                <option value="Submitted">Submit (Post to Ledger)</option>
              </select>
            </div>
          </div>

        </div>
        <div class="coa-dfooter" style="justify-content:space-between">
          <div style="font-size:12px;color:#868e96">{{editingName?'Editing: '+editingName:'New entry'}}</div>
          <div style="display:flex;gap:10px">
            <button class="b-btn b-btn-ghost" @click="drawerOpen=false">Cancel</button>
            <button class="b-btn b-btn-ghost" @click="saveEntry('Draft')" :disabled="drawerSaving" style="border-color:#3b5bdb;color:#3b5bdb">Save Draft</button>
            <button class="b-btn b-btn-primary" @click="saveEntry('Submitted')" :disabled="drawerSaving||!balanced" style="min-width:140px">
              <span v-html="icon('check',13)"></span> Post to Ledger
            </button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="viewOpen && viewEntry" class="coa-drawer-bg" @click.self="viewOpen=false">
      <div class="jen-drawer-panel">
        <div class="coa-dh" :style="'background:'+(viewEntry.status==='Submitted'?'linear-gradient(135deg,#1a4731,#2f9e44)':viewEntry.status==='Cancelled'?'linear-gradient(135deg,#6b1212,#c92a2a)':'linear-gradient(135deg,#1e3a5f,#2563eb)')">
          <div>
            <div class="coa-dh-title">{{viewEntry.name}}</div>
            <div class="coa-dh-sub">{{viewEntry.type}} · {{fmtDateLocal(viewEntry.date)}}</div>
          </div>
          <button class="coa-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="coa-dbody">
          <div style="display:flex;gap:16px;flex-wrap:wrap;margin-bottom:20px">
            <div>
              <div style="font-size:11px;color:#868e96;font-weight:600;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Status</div>
              <span class="b-badge" :class="JE_STATUS_COLOR[viewEntry.status]||'je-s-draft'">{{viewEntry.status}}</span>
            </div>
            <div>
              <div style="font-size:11px;color:#868e96;font-weight:600;text-transform:uppercase;letter-spacing:.04em;margin-bottom:4px">Narration</div>
              <div style="font-size:13px;max-width:500px">{{viewEntry.narration||'—'}}</div>
            </div>
          </div>
          <div style="display:flex;gap:24px;margin-bottom:20px;font-size:13px">
            <div><span style="color:#868e96">Total Debit:</span> <strong style="color:#c92a2a;font-family:monospace">{{fmtINR(viewEntry.total_debit)}}</strong></div>
            <div><span style="color:#868e96">Total Credit:</span> <strong style="color:#2f9e44;font-family:monospace">{{fmtINR(viewEntry.total_credit)}}</strong></div>
          </div>
          <div v-if="(viewEntry.lines||[]).length" style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden">
            <div style="display:grid;grid-template-columns:1fr 120px 120px;gap:8px;padding:8px 14px;background:#f8f9fc;border-bottom:1px solid #e2e8f0;font-size:10.5px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#868e96">
              <div>Account</div><div style="text-align:right">Debit (Dr)</div><div style="text-align:right">Credit (Cr)</div>
            </div>
            <div v-for="(l,i) in viewEntry.lines" :key="i"
              style="display:grid;grid-template-columns:1fr 120px 120px;gap:8px;padding:9px 14px;border-bottom:1px solid #f1f3f5;font-size:13px">
              <div>{{l.account}}<span v-if="l.party" style="color:#868e96;font-size:11px;margin-left:6px">{{l.party}}</span></div>
              <div style="text-align:right;font-family:monospace;color:#c92a2a">{{flt(l.dr)>0?fmtINR(l.dr):'—'}}</div>
              <div style="text-align:right;font-family:monospace;color:#2f9e44">{{flt(l.cr)>0?fmtINR(l.cr):'—'}}</div>
            </div>
          </div>
          <div v-else style="color:#868e96;font-size:13px;margin-top:16px">No line detail available for this entry.</div>
        </div>
        <div class="coa-dfooter" style="justify-content:space-between">
          <div style="font-size:12px;color:#868e96">{{viewEntry.source==='frappe'?'From Frappe':'Local record'}}</div>
          <div style="display:flex;gap:10px">
            <button v-if="viewEntry.status==='Draft'" class="b-btn b-btn-ghost" @click="viewOpen=false;openEdit(viewEntry.name)"><span v-html="icon('edit',13)"></span> Edit</button>
            <button v-if="viewEntry.status==='Submitted'" class="b-btn b-btn-ghost" style="border-color:rgba(201,42,42,.4);color:#c92a2a" @click="viewOpen=false;confirmAction(viewEntry.name,'cancel')"><span v-html="icon('cancel',13)"></span> Cancel</button>
            <button class="b-btn b-btn-ghost" @click="viewOpen=false">Close</button>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showConf" class="coa-drawer-bg" @click.self="showConf=false" style="justify-content:center;align-items:center">
      <div style="background:#fff;border-radius:12px;padding:28px 32px;max-width:440px;width:100%;border:1px solid #e2e8f0">
        <div style="font-size:17px;font-weight:700;margin-bottom:8px">{{confType==='delete'?'Delete Entry?':'Cancel Entry?'}}</div>
        <div style="font-size:14px;color:#868e96;margin-bottom:24px;line-height:1.5">
          {{confType==='delete'?'This journal entry will be permanently removed.':'This will mark the entry as Cancelled. It cannot be edited after cancellation.'}}
          <br><strong>{{confTarget}}</strong>
        </div>
        <div style="display:flex;gap:10px;justify-content:flex-end">
          <button @click="showConf=false" class="b-btn b-btn-ghost">Keep It</button>
          <button @click="doAction" class="b-btn" style="background:#c92a2a;color:#fff;border-color:#c92a2a">{{confType==='delete'?'Yes, Delete':'Yes, Cancel'}}</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiDelete, apiSubmit, apiPOST, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { flt } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();

const JE_TEMPLATES = [
  { id: "depreciation", name: "Depreciation",       desc: "Monthly asset depreciation posting",
    lines: [{ account: "Depreciation", dr: 0, cr: 0, type: "Debit" }, { account: "Accumulated Depreciation", dr: 0, cr: 0, type: "Credit" }] },
  { id: "salary",       name: "Salary Accrual",     desc: "Record salary expense before payment",
    lines: [{ account: "Salaries & Wages", dr: 0, cr: 0, type: "Debit" }, { account: "Salary Payable", dr: 0, cr: 0, type: "Credit" }] },
  { id: "bank-charge",  name: "Bank Charges",       desc: "Bank processing / service fee",
    lines: [{ account: "Bank Charges", dr: 0, cr: 0, type: "Debit" }, { account: "HDFC Current Account", dr: 0, cr: 0, type: "Credit" }] },
  { id: "gst-payment",  name: "GST Payment",         desc: "Pay GST liability to government",
    lines: [{ account: "CGST Payable", dr: 0, cr: 0, type: "Debit" }, { account: "SGST Payable", dr: 0, cr: 0, type: "Debit" }, { account: "HDFC Current Account", dr: 0, cr: 0, type: "Credit" }] },
  { id: "prepaid",      name: "Prepaid Expense",    desc: "Advance payment treated as asset",
    lines: [{ account: "Prepaid Expenses", dr: 0, cr: 0, type: "Debit" }, { account: "HDFC Current Account", dr: 0, cr: 0, type: "Credit" }] },
  { id: "provision",    name: "Bad Debt Provision", desc: "Provision for doubtful receivables",
    lines: [{ account: "Bad Debt Expense", dr: 0, cr: 0, type: "Debit" }, { account: "Provision for Bad Debts", dr: 0, cr: 0, type: "Credit" }] },
];
const JE_TYPE_COLOR   = { "Journal Entry": "je-type-info", Depreciation: "je-type-muted", Accrual: "je-type-info", Prepaid: "je-type-info", Provision: "je-type-muted", Contra: "je-type-muted", Rectification: "je-type-muted", "Opening Entry": "je-type-info" };
const JE_STATUS_COLOR = { Draft: "je-s-draft", Submitted: "je-s-submitted", Cancelled: "je-s-cancelled" };

const allEntries  = ref([]);
const accounts    = ref([]);
const costCenters = ref([]);
const loading     = ref(true);
const currentFilter = ref("all");
const searchQ     = ref("");
const dateFrom    = ref("");
const dateTo      = ref("");

const drawerOpen   = ref(false);
const editingName  = ref(null);
const drawerSaving = ref(false);
const selectedTpl  = ref("");
const form = reactive({ date: "", type: "Journal Entry", ref: "", cheque_date: "", narration: "", cost_center: "", status: "Draft" });
const lines = ref([]);

const viewOpen   = ref(false);
const viewEntry  = ref(null);
const showConf   = ref(false);
const confTarget = ref(null);
const confType   = ref("");

const todayStr = () => new Date().toISOString().slice(0, 10);
const thisMonth = (d) => { const n = new Date(); return (d || "").startsWith(n.getFullYear() + "-" + String(n.getMonth() + 1).padStart(2, "0")); };

function fmtINR(v) {
  if (!v && v !== 0) return "—";
  const n = Number(v);
  if (n === 0) return "—";
  return "₹" + Math.abs(n).toLocaleString("en-IN", { minimumFractionDigits: 2 });
}
function fmtDateLocal(d) {
  if (!d) return "—";
  try { return new Date(d).toLocaleDateString("en-IN", { day: "2-digit", month: "short", year: "numeric" }); }
  catch { return d; }
}

const summary = computed(() => {
  const month = allEntries.value.filter((e) => thisMonth(e.date));
  const drafts = allEntries.value.filter((e) => e.status === "Draft");
  const totalDr = allEntries.value.filter((e) => e.status === "Submitted").reduce((s, e) => s + Number(e.total_debit || 0), 0);
  return { total: allEntries.value.length, month: month.length, totalDr, drafts: drafts.length };
});

const counts = computed(() => ({
  Draft:     allEntries.value.filter((e) => e.status === "Draft").length,
  Submitted: allEntries.value.filter((e) => e.status === "Submitted").length,
  Cancelled: allEntries.value.filter((e) => e.status === "Cancelled").length,
}));

const filteredRows = computed(() => {
  const q = searchQ.value.toLowerCase();
  let r = currentFilter.value === "all" ? allEntries.value : allEntries.value.filter((e) => e.status === currentFilter.value);
  if (dateFrom.value) r = r.filter((e) => e.date && e.date >= dateFrom.value);
  if (dateTo.value)   r = r.filter((e) => e.date && e.date <= dateTo.value);
  if (q) r = r.filter((e) => (e.name + e.narration + (e.type || "")).toLowerCase().includes(q));
  return r;
});

const totalDr   = computed(() => lines.value.reduce((s, l) => s + flt(l.dr), 0));
const totalCr   = computed(() => lines.value.reduce((s, l) => s + flt(l.cr), 0));
const balanced  = computed(() => Math.abs(totalDr.value - totalCr.value) < 0.01);

async function load() {
  loading.value = true;
  try {
    let frappeEntries = [];
    try {
      frappeEntries = await apiList("Journal Entry", {
        fields: ["name", "posting_date", "voucher_type", "remark", "total_debit", "total_credit", "docstatus"],
        order: "posting_date desc", limit: 300,
      });
    } catch {}
    if (frappeEntries && frappeEntries.length) {
      allEntries.value = frappeEntries.map((e) => ({
        name: e.name, date: e.posting_date, type: e.voucher_type || "Journal Entry",
        narration: e.remark || "",
        total_debit: e.total_debit || 0, total_credit: e.total_credit || 0,
        status: e.docstatus === 1 ? "Submitted" : e.docstatus === 2 ? "Cancelled" : "Draft",
        lines: [], source: "frappe",
      }));
    } else {
      allEntries.value = [];
    }
    try {
      const accts = await apiList("Account", { fields: ["name", "account_name", "account_type"], filters: [["is_group", "=", 0], ["disabled", "=", 0]], limit: 500 });
      accounts.value = accts.map((a) => a.name || a.account_name);
    } catch { accounts.value = []; }
    try {
      const cc = await apiList("Cost Center", { fields: ["name"], filters: [["is_group", "=", 0]], limit: 100 });
      costCenters.value = cc.map((c) => c.name);
    } catch {}
  } finally { loading.value = false; }
}

function openAdd() {
  editingName.value = null;
  selectedTpl.value = "";
  lines.value = [
    { id: Date.now(),     account: "", party: "", cost_center: "", dr: "", cr: "", type: "Debit" },
    { id: Date.now() + 1, account: "", party: "", cost_center: "", dr: "", cr: "", type: "Credit" },
  ];
  Object.assign(form, { date: todayStr(), type: "Journal Entry", ref: "", cheque_date: "", narration: "", cost_center: "", status: "Draft" });
  drawerOpen.value = true;
}

function openEdit(name) {
  const e = allEntries.value.find((x) => x.name === name);
  if (!e || e.status !== "Draft") return;
  editingName.value = name;
  selectedTpl.value = "";
  Object.assign(form, { date: e.date || todayStr(), type: e.type || "Journal Entry", ref: e.ref || "", cheque_date: e.cheque_date || "", narration: e.narration || "", cost_center: e.cost_center || "", status: e.status || "Draft" });
  lines.value = (e.lines && e.lines.length)
    ? e.lines.map((l, i) => ({ ...l, id: Date.now() + i }))
    : [
        { id: Date.now(),     account: "", party: "", cost_center: "", dr: "", cr: "", type: "Debit" },
        { id: Date.now() + 1, account: "", party: "", cost_center: "", dr: "", cr: "", type: "Credit" },
      ];
  drawerOpen.value = true;
}

function openView(name) {
  viewEntry.value = allEntries.value.find((x) => x.name === name) || null;
  viewOpen.value = true;
}

function applyTemplate(tplId) {
  const tpl = JE_TEMPLATES.find((t) => t.id === tplId);
  if (!tpl) return;
  selectedTpl.value = selectedTpl.value === tplId ? "" : tplId;
  if (selectedTpl.value) {
    lines.value = tpl.lines.map((l, i) => ({
      id: Date.now() + i, account: l.account, party: "", cost_center: "",
      dr: l.type === "Debit" ? l.dr : "", cr: l.type === "Credit" ? l.cr : "", type: l.type,
    }));
    form.narration = tpl.name + " — " + new Date().toLocaleDateString("en-IN", { month: "short", year: "numeric" });
  }
}

function addLine(type) {
  lines.value.push({ id: Date.now(), account: "", party: "", cost_center: "", dr: type === "Debit" ? "0" : "", cr: type === "Credit" ? "0" : "", type });
}

function removeLine(id) {
  if (lines.value.length <= 1) return;
  lines.value = lines.value.filter((l) => l.id !== id);
}

async function saveEntry(status) {
  if (!form.date)             { toast("Date is required", "error"); return; }
  if (!form.narration.trim()) { toast("Narration is required", "error"); return; }
  const hasLines = lines.value.some((l) => l.account && (flt(l.dr) > 0 || flt(l.cr) > 0));
  if (!hasLines)  { toast("Add at least one line with an account and amount", "error"); return; }
  if (!balanced.value) { toast("Total debits must equal total credits", "error"); return; }
  drawerSaving.value = true;
  try {
    const company = await resolveCompany();
    const payload = {
      posting_date: form.date,
      voucher_type: form.type,
      remark: form.narration,
      accounts: lines.value.filter((l) => l.account).map((l) => ({
        doctype: "Journal Entry Account",
        account: l.account,
        party: l.party || null,
        cost_center: l.cost_center || form.cost_center || null,
        debit_in_account_currency: flt(l.dr),
        credit_in_account_currency: flt(l.cr),
      })),
    };
    const frappeDoc = { doctype: "Journal Entry", naming_series: "JV-.YYYY.-.#####", company, ...payload };
    if (editingName.value) frappeDoc.name = editingName.value;
    const saved = await apiSave(frappeDoc);
    if (status === "Submitted" && saved?.name) {
      await apiSubmit("Journal Entry", saved.name);
    }
    await load();
    toast(editingName.value ? "Journal entry updated" : "Journal entry created", "success");
    drawerOpen.value = false;
  } catch (e) {
    toast(e.message || "Save failed", "error");
  } finally { drawerSaving.value = false; }
}

function confirmAction(name, type) {
  confTarget.value = name;
  confType.value = type;
  showConf.value = true;
}

async function doAction() {
  const name = confTarget.value;
  try {
    if (confType.value === "delete") {
      await apiDelete("Journal Entry", name);
      allEntries.value = allEntries.value.filter((e) => e.name !== name);
      toast("Entry deleted", "success");
    } else if (confType.value === "cancel") {
      await apiPOST("frappe.client.cancel", { doctype: "Journal Entry", name });
      const idx = allEntries.value.findIndex((e) => e.name === name);
      if (idx >= 0) allEntries.value[idx] = { ...allEntries.value[idx], status: "Cancelled" };
      toast("Entry cancelled", "success");
    }
  } catch (e) { toast("Action failed: " + e.message, "error"); }
  showConf.value = false;
  confTarget.value = null;
}

onMounted(load);
</script>
