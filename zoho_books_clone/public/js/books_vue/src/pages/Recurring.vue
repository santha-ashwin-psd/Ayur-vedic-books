<template>
  <div class="rec-page">
    <!-- ============================================================ TOOLBAR -->
    <div class="rec-actions">
      <div class="rec-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search subscriptions, reference, party…" class="rec-search-input" />
      </div>
      <div class="rec-pills">
        <button v-for="t in tabs" :key="t.key" class="rec-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">
          {{ t.label }}<span v-if="t.count!=null" class="rec-pill-count">{{ t.count }}</span>
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="rec-btn-ghost" @click="exportCSV" :disabled="!sorted.length" title="Export to CSV">
          <span v-html="icon('download',14)"></span> CSV
        </button>
        <button class="rec-btn-ghost" @click="load" :disabled="loading">
          <span v-html="icon('refresh',14)"></span>
        </button>
        <button class="rec-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Subscription
        </button>
      </div>
    </div>

    <!-- ============================================================ SUMMARY -->
    <div class="rec-summary" v-if="!loading">
      <div class="rec-sum-card" :class="{accent:true}">
        <div class="rec-sum-lbl">TOTAL</div>
        <div class="rec-sum-val">{{ stats.total }}</div>
      </div>
      <div class="rec-sum-card">
        <div class="rec-sum-lbl">ACTIVE</div>
        <div class="rec-sum-val green">{{ stats.active }}</div>
      </div>
      <div class="rec-sum-card">
        <div class="rec-sum-lbl">PAUSED</div>
        <div class="rec-sum-val orange">{{ stats.paused }}</div>
      </div>
      <div class="rec-sum-card" :class="{warn: stats.due_today>0}">
        <div class="rec-sum-lbl">DUE TODAY</div>
        <div class="rec-sum-val" :class="stats.due_today>0?'blue':''">{{ stats.due_today }}</div>
      </div>
      <div class="rec-sum-card" :class="{danger: stats.overdue>0}">
        <div class="rec-sum-lbl">OVERDUE</div>
        <div class="rec-sum-val" :class="stats.overdue>0?'red':''">{{ stats.overdue }}</div>
      </div>
    </div>

    <!-- ============================================================ BULK BAR -->
    <div v-if="selected.length" class="inv-bulk-bar">
      <span class="inv-bulk-count">{{ selected.length }} selected</span>
      <button class="inv-bulk-btn" @click="bulkDo('pause')">Pause</button>
      <button class="inv-bulk-btn" @click="bulkDo('resume')">Resume</button>
      <button class="inv-bulk-btn inv-bulk-danger" @click="bulkDo('cancel')">Cancel</button>
      <button class="inv-bulk-btn inv-bulk-danger" @click="bulkDo('delete')">Delete</button>
      <button class="inv-bulk-btn" @click="exportCSV"><span v-html="icon('download',13)"></span> Export CSV</button>
      <button class="inv-bulk-clear" @click="selected=[]">✕ Clear</button>
    </div>

    <!-- ============================================================ TABLE -->
    <div class="rec-card">
      <table class="rec-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" :checked="allSelected" @change="toggleAll" /></th>
            <th @click="sort('name')" class="sortable">Subscription # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('reference_doctype')" class="sortable">Type <span v-html="sortArrow('reference_doctype')"></span></th>
            <th @click="sort('reference_document')" class="sortable">Reference <span v-html="sortArrow('reference_document')"></span></th>
            <th>Party</th>
            <th style="text-align:right">Amount</th>
            <th @click="sort('frequency')" class="sortable">Frequency <span v-html="sortArrow('frequency')"></span></th>
            <th @click="sort('next_schedule_date')" class="sortable">Next Run <span v-html="sortArrow('next_schedule_date')"></span></th>
            <th>Status</th>
            <th style="width:120px;text-align:right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="10"><div class="rec-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="r in paged" :key="r.name" class="rec-row" :class="{selected:selected.includes(r.name)}" @click="openView(r)">
              <td @click.stop>
                <input type="checkbox" :checked="selected.includes(r.name)" @change="toggleOne(r.name)" />
              </td>
              <td><span class="rec-num">{{ r.name }}</span></td>
              <td class="text-muted">{{ r.reference_doctype||'—' }}</td>
              <td @click.stop><DocLink :doctype="r.reference_doctype" :name="r.reference_document" /></td>
              <td class="text-muted">{{ r.party||'—' }}</td>
              <td style="text-align:right" class="mono-sm">{{ fmtCurrency(r.amount) }}</td>
              <td>{{ freqLabel(r.frequency) }}</td>
              <td class="mono-sm" :class="r.is_due?'text-accent':''">
                {{ fmtDate(r.next_schedule_date)||'—' }}
                <span v-if="r.is_due" class="rec-due-dot" title="Due"></span>
              </td>
              <td><span class="rec-badge" :class="statusClass(r.ui_status)">{{ r.ui_status }}</span></td>
              <td @click.stop style="text-align:right">
                <button class="rec-act-btn" @click="openView(r)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="r.ui_status==='Active'" class="rec-act-btn" @click="quickAction(r,'pause')" title="Pause"><span v-html="icon('pause',13)"></span></button>
                <button v-else-if="r.ui_status==='Paused'" class="rec-act-btn" @click="quickAction(r,'resume')" title="Resume"><span v-html="icon('play',13)"></span></button>
                <button class="rec-act-btn rec-act-danger" @click="quickAction(r,'delete')" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length"><td colspan="10" class="rec-empty">
              <div class="rec-empty-wrap">
                <div class="rec-empty-icon" v-html="icon('repeat',32)"></div>
                <div class="rec-empty-title">No subscriptions yet</div>
                <div class="rec-empty-sub">Create a recurring subscription to auto-generate invoices, bills, or journals on a schedule.</div>
                <button class="rec-btn-primary" @click="openNew" style="margin-top:12px"><span v-html="icon('plus',13)"></span> Create your first subscription</button>
              </div>
            </td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <div v-if="!loading && sorted.length">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ============================================================ CREATE / EDIT DRAWER -->
    <div v-if="drawerOpen" class="rec-overlay" @click.self="onOverlayClose"></div>
    <div class="rec-drawer" :class="{open:drawerOpen}">
      <div class="rec-dheader" :class="editMode?'edit':''">
        <div class="rec-dheader-left">
          <div class="rec-dheader-ico" :class="editMode?'edit':''">
            <span v-html="icon(editMode?'edit':'repeat',18)"></span>
          </div>
          <div>
            <div class="rec-dheader-title">{{ editMode?'Edit Subscription':'New Recurring Subscription' }}</div>
            <div class="rec-dheader-sub">
              {{ editMode ? form._name : 'Schedule a document to repeat on a cadence' }}
            </div>
          </div>
        </div>
        <button class="rec-dclose" @click="onOverlayClose"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="rec-dbody">
        <!-- Intro/context card when a reference is selected -->
        <div v-if="form.reference_document && referenceMeta.party" class="rec-ctx-card">
          <div class="rec-ctx-ico"><span v-html="icon('folder',16)"></span></div>
          <div style="flex:1;min-width:0">
            <div class="rec-ctx-doctype">{{ form.reference_doctype }}</div>
            <div class="rec-ctx-name">{{ form.reference_document }}</div>
          </div>
          <div class="rec-ctx-meta">
            <div class="rec-ctx-party">{{ referenceMeta.party }}</div>
            <div class="rec-ctx-amount mono">{{ fmtCurrency(referenceMeta.amount) }}</div>
          </div>
        </div>

        <!-- Section: Reference -->
        <div class="rec-section">
          <div class="rec-section-hdr">
            <span v-html="icon('folder',13)"></span>
            <span>Reference Document</span>
          </div>
          <div class="rec-fields-grid">
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Document Type <span class="req">*</span></label>
              <select v-model="form.reference_doctype" class="rec-select" :disabled="editMode" @change="onTypeChange">
                <option value="Sales Invoice">Sales Invoice</option>
                <option value="Quotation">Quotation</option>
              </select>
            </div>
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Source Document <span class="req">*</span></label>
              <SearchableSelect
                v-model="form.reference_document"
                :options="refDocs"
                :disabled="editMode"
                placeholder="Search a saved document…"
                @search="fetchRefDocs"
              />
              <div class="rec-field-help" v-if="!form.reference_document">
                Pick an existing {{ form.reference_doctype.toLowerCase() }} to use as the template.
              </div>
            </div>
          </div>
        </div>

        <!-- Section: Schedule -->
        <div class="rec-section">
          <div class="rec-section-hdr">
            <span v-html="icon('refresh',13)"></span>
            <span>Schedule</span>
          </div>
          <div class="rec-fields-grid">
            <div class="rec-field">
              <label class="rec-label">Frequency <span class="req">*</span></label>
              <select v-model="form.frequency" class="rec-select">
                <option value="Daily">Daily</option>
                <option value="Weekly">Weekly</option>
                <option value="Monthly">Monthly</option>
                <option value="Quarterly">Quarterly</option>
                <option value="Half-yearly">Half-yearly</option>
                <option value="Yearly">Yearly</option>
              </select>
            </div>
            <div class="rec-field">
              <label class="rec-label">Submit on Creation</label>
              <select v-model="form.submit_on_creation" class="rec-select">
                <option :value="1">Yes — auto-submit</option>
                <option :value="0">No — save as draft</option>
              </select>
            </div>
            <div class="rec-field">
              <label class="rec-label">Start Date <span class="req">*</span></label>
              <input v-model="form.start_date" type="date" class="rec-input" :disabled="editMode" />
            </div>
            <div class="rec-field">
              <label class="rec-label">End Date <span class="rec-hint">(optional)</span></label>
              <input v-model="form.end_date" type="date" class="rec-input" :min="form.start_date" />
            </div>
            <div v-if="planHint" class="rec-plan-hint" style="grid-column:1/-1">
              <span v-html="icon('info',13)"></span>
              <span>{{ planHint }}</span>
            </div>
          </div>
        </div>

        <!-- Section: Notification -->
        <div class="rec-section">
          <div class="rec-section-hdr">
            <span v-html="icon('mail',13)"></span>
            <span>Notification</span>
            <label class="rec-toggle">
              <input type="checkbox" v-model="form._notify" />
              <span class="rec-toggle-slider"></span>
            </label>
          </div>
          <div v-if="!form._notify" class="rec-section-empty">
            Email notifications are off. Toggle to email someone every time a document is generated.
          </div>
          <div v-else class="rec-fields-grid">
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Recipients <span class="rec-hint">(comma separated)</span></label>
              <input v-model="form.recipients" type="text" class="rec-input" placeholder="finance@company.com, owner@company.com" />
            </div>
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Email Subject</label>
              <input v-model="form.subject" type="text" class="rec-input" placeholder="Your recurring invoice is ready" />
            </div>
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Email Message</label>
              <textarea v-model="form.message" class="rec-input" rows="3" placeholder="Hello, please find your latest document attached…"></textarea>
            </div>
          </div>
        </div>
      </div>

      <div class="rec-dfooter">
        <button class="rec-btn-ghost" @click="onOverlayClose" :disabled="drawerSaving">Cancel</button>
        <button class="rec-btn-primary" :disabled="drawerSaving" @click="saveRec">
          <span v-html="icon('check',13)"></span>
          {{ drawerSaving?'Saving…':(editMode?'Save Changes':'Create Subscription') }}
        </button>
      </div>
    </div>

    <!-- ============================================================ VIEW DRAWER -->
    <div v-if="viewOpen" class="rec-overlay" @click.self="viewOpen=false"></div>
    <div class="rec-drawer rec-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <!-- gradient header -->
        <div class="rec-view-head" :class="viewDoc.ui_status==='Paused'?'paused':viewDoc.ui_status==='Completed'?'completed':''">
          <div class="rec-view-head-row">
            <div>
              <div class="rec-view-num">{{ viewDoc.name }}</div>
              <div class="rec-view-sub">
                {{ viewDoc.reference_doctype }} · {{ freqLabel(viewDoc.frequency) }}
                <span v-if="viewDoc.party"> · {{ viewDoc.party }}</span>
              </div>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span class="rec-badge rec-badge-lg" :class="statusClass(viewDoc.ui_status)">{{ viewDoc.ui_status }}</span>
              <button class="rec-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
            </div>
          </div>
          <div class="rec-view-stats">
            <div><div class="vh-lbl">Total Billed</div><div class="vh-val">{{ fmtCurrency(viewDoc.total_billed) }}</div></div>
            <div><div class="vh-lbl">Generated</div><div class="vh-val">{{ viewDoc.runs_count }}</div></div>
            <div><div class="vh-lbl">Next Run</div><div class="vh-val" :class="isDue(viewDoc)?'text-accent':''">{{ fmtDate(viewDoc.next_schedule_date)||'—' }}</div></div>
          </div>
        </div>

        <!-- action bar -->
        <div class="rec-view-actbar">
          <button class="rec-va-btn" @click="openEdit(viewDoc)" :disabled="viewDoc.ui_status==='Completed'"><span v-html="icon('edit',13)"></span> Edit</button>
          <button class="rec-va-btn" @click="runNow(viewDoc)" :disabled="viewDoc.ui_status!=='Active' || actionLoading"><span v-html="icon('play',13)"></span> Run Now</button>
          <button v-if="viewDoc.ui_status==='Active'" class="rec-va-btn" @click="actionOn(viewDoc,'pause')" :disabled="actionLoading"><span v-html="icon('pause',13)"></span> Pause</button>
          <button v-else-if="viewDoc.ui_status==='Paused'" class="rec-va-btn" @click="actionOn(viewDoc,'resume')" :disabled="actionLoading"><span v-html="icon('play',13)"></span> Resume</button>
          <button class="rec-va-btn rec-va-warn" @click="actionOn(viewDoc,'cancel')" :disabled="actionLoading || viewDoc.ui_status==='Completed'"><span v-html="icon('x',13)"></span> Cancel</button>
          <button class="rec-va-btn rec-va-danger" @click="actionOn(viewDoc,'delete')" :disabled="actionLoading"><span v-html="icon('trash',13)"></span> Delete</button>
        </div>

        <!-- timeline -->
        <div class="rec-timeline">
          <div class="rec-tl-step" :class="{done:true}">
            <div class="rec-tl-dot"></div>
            <div class="rec-tl-lbl">Created<br/><span class="rec-tl-sub">{{ fmtDate(viewDoc.creation) }}</span></div>
          </div>
          <div class="rec-tl-line" :class="{done:viewDoc.ui_status!=='Paused'}"></div>
          <div class="rec-tl-step" :class="{done:viewDoc.ui_status==='Active' || viewDoc.runs_count>0, current:viewDoc.ui_status==='Active'}">
            <div class="rec-tl-dot"></div>
            <div class="rec-tl-lbl">{{ viewDoc.ui_status==='Paused'?'Paused':'Active' }}<br/><span class="rec-tl-sub">{{ fmtDate(viewDoc.start_date) }}</span></div>
          </div>
          <div class="rec-tl-line" :class="{done:viewDoc.runs_count>0}"></div>
          <div class="rec-tl-step" :class="{done:viewDoc.runs_count>0}">
            <div class="rec-tl-dot"></div>
            <div class="rec-tl-lbl">Last Run<br/><span class="rec-tl-sub">{{ viewDoc.runs.length?fmtDate(viewDoc.runs[0].creation):'—' }}</span></div>
          </div>
          <div class="rec-tl-line" :class="{done:viewDoc.ui_status==='Completed', danger:viewDoc.ui_status==='Paused'}"></div>
          <div class="rec-tl-step" :class="{done:viewDoc.ui_status==='Completed'}">
            <div class="rec-tl-dot"></div>
            <div class="rec-tl-lbl">{{ viewDoc.end_date?'Ends':'Open-ended' }}<br/><span class="rec-tl-sub">{{ fmtDate(viewDoc.end_date)||'No end' }}</span></div>
          </div>
        </div>

        <!-- tabs -->
        <div class="rec-view-tabs">
          <button v-for="t in viewTabs" :key="t.key" class="rec-vt-btn" :class="{active:viewTab===t.key}" @click="viewTab=t.key">
            {{ t.label }}<span v-if="t.count!=null" class="rec-vt-count">{{ t.count }}</span>
          </button>
        </div>

        <div class="rec-dbody">
          <!-- Details tab -->
          <div v-if="viewTab==='details'">
            <div class="rec-meta-grid">
              <div><div class="rec-meta-lbl">Reference</div><div><DocLink :doctype="viewDoc.reference_doctype" :name="viewDoc.reference_document" /></div></div>
              <div><div class="rec-meta-lbl">{{ viewDoc.party_label||'Party' }}</div><div>{{ viewDoc.party||'—' }}</div></div>
              <div><div class="rec-meta-lbl">Frequency</div><div>{{ freqLabel(viewDoc.frequency) }}</div></div>
              <div><div class="rec-meta-lbl">Template Amount</div><div class="mono-sm">{{ fmtCurrency(viewDoc.template_amount) }}</div></div>
              <div><div class="rec-meta-lbl">Start Date</div><div class="mono-sm">{{ fmtDate(viewDoc.start_date) }}</div></div>
              <div><div class="rec-meta-lbl">End Date</div><div class="mono-sm">{{ fmtDate(viewDoc.end_date)||'Open-ended' }}</div></div>
              <div><div class="rec-meta-lbl">Submit on Creation</div><div>{{ viewDoc.submit_on_creation?'Yes':'No (Draft)' }}</div></div>
              <div><div class="rec-meta-lbl">Notify by Email</div><div>{{ viewDoc.notify_by_email?'Yes':'No' }}</div></div>
              <div v-if="viewDoc.notify_by_email" style="grid-column:1/-1">
                <div class="rec-meta-lbl">Recipients</div>
                <div class="mono-sm" style="word-break:break-all">{{ viewDoc.recipients||'—' }}</div>
              </div>
              <div v-if="viewDoc.subject" style="grid-column:1/-1">
                <div class="rec-meta-lbl">Email Subject</div>
                <div>{{ viewDoc.subject }}</div>
              </div>
            </div>
          </div>

          <!-- Generated tab -->
          <div v-else-if="viewTab==='generated'">
            <div v-if="!viewDoc.runs.length" class="rec-tab-empty">No documents generated yet.</div>
            <table v-else class="rec-table rec-table-inner">
              <thead>
                <tr><th>Document</th><th>Created</th><th style="text-align:right">Amount</th><th>Status</th></tr>
              </thead>
              <tbody>
                <tr v-for="d in viewDoc.runs" :key="d.name">
                  <td><DocLink :doctype="viewDoc.reference_doctype" :name="d.name" /></td>
                  <td class="text-muted mono-sm">{{ fmtDate(d.creation) }}</td>
                  <td style="text-align:right" class="mono-sm">{{ fmtCurrency(d.grand_total) }}</td>
                  <td>
                    <span class="rec-badge" :class="d.docstatus===1?'badge-green':d.docstatus===2?'badge-red':'badge-grey'">
                      {{ d.docstatus===1?'Submitted':d.docstatus===2?'Cancelled':'Draft' }}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Upcoming tab -->
          <div v-else-if="viewTab==='upcoming'">
            <div v-if="!viewDoc.upcoming.length" class="rec-tab-empty">No upcoming runs scheduled. End date may have passed or subscription is paused.</div>
            <ol v-else class="rec-upcoming-list">
              <li v-for="(u,i) in viewDoc.upcoming" :key="i">
                <span class="rec-upcoming-idx">#{{ i+1 }}</span>
                <span class="mono-sm">{{ fmtDate(u.date) }}</span>
                <span class="text-muted">— {{ u.frequency }}</span>
              </li>
            </ol>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from "vue";
import { apiSave, apiGET, apiPOST, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useRoute } from "vue-router";
import { useConfirm } from "../composables/useConfirm.js";
import { useOpenFromQuery } from "../composables/useOpenFromQuery.js";
import { usePagination } from "../composables/usePagination.js";
import DocLink from "../components/DocLink.vue";
import Pagination from "../components/Pagination.vue";
import { icon } from "../utils/icons.js";
import { fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const route = useRoute();
const { confirm } = useConfirm();

// state
const list = ref([]);
const loading = ref(false);
const search = ref("");
const activeTab = ref("all");
const stats = ref({ total: 0, active: 0, paused: 0, due_today: 0, overdue: 0, completed: 0 });
const sortCol = ref("next_schedule_date");
const sortDir = ref("asc");
const selected = ref([]);
const actionLoading = ref(false);

// create/edit drawer
const drawerOpen = ref(false);
const drawerSaving = ref(false);
const editMode = ref(false);
const refDocs = ref([]);
const referenceMeta = reactive({ party_label: "", party: "", amount: 0 });
const form = reactive({
  _name: "",
  reference_doctype: "Sales Invoice",
  reference_document: "",
  frequency: "Monthly",
  start_date: new Date().toISOString().slice(0, 10),
  end_date: "",
  submit_on_creation: 1,
  _notify: false,
  recipients: "",
  subject: "",
  message: "",
});

// view drawer
const viewOpen = ref(false);
const viewDoc = ref(null);
const viewTab = ref("details");

// ----- derived
const tabs = computed(() => [
  { key: "all", label: "All", count: stats.value.total },
  { key: "Active", label: "Active", count: stats.value.active },
  { key: "Paused", label: "Paused", count: stats.value.paused },
  { key: "Completed", label: "Completed", count: stats.value.completed || null },
]);

const viewTabs = computed(() => [
  { key: "details", label: "Details" },
  { key: "generated", label: "Generated", count: viewDoc.value?.runs_count ?? 0 },
  { key: "upcoming", label: "Upcoming", count: viewDoc.value?.upcoming?.length ?? 0 },
]);

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") r = r.filter((x) => x.ui_status === activeTab.value);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter((x) =>
      (x.name || "").toLowerCase().includes(q) ||
      (x.reference_document || "").toLowerCase().includes(q) ||
      (x.party || "").toLowerCase().includes(q)
    );
  }
  return r;
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const av = a[col] ?? "";
    const bv = b[col] ?? "";
    const c = String(av).localeCompare(String(bv));
    return sortDir.value === "asc" ? c : -c;
  });
});

const { page, pageSize, paged } = usePagination(sorted, { storageKey: "recurring" });

const allSelected = computed(() => sorted.value.length > 0 && sorted.value.every((r) => selected.value.includes(r.name)));

const planHint = computed(() => {
  if (!form.start_date || !form.end_date) return form.start_date ? "Open-ended subscription — runs until paused or cancelled." : "";
  const start = new Date(form.start_date);
  const end = new Date(form.end_date);
  if (end < start) return "End date is before start date.";
  const months = (end.getFullYear() - start.getFullYear()) * 12 + (end.getMonth() - start.getMonth());
  const map = { Daily: Math.max(1, Math.round((end - start) / 86400000)), Weekly: Math.max(1, Math.round((end - start) / (7 * 86400000))), Monthly: months + 1, Quarterly: Math.floor(months / 3) + 1, "Half-yearly": Math.floor(months / 6) + 1, Yearly: end.getFullYear() - start.getFullYear() + 1 };
  const n = map[form.frequency] || 0;
  return `Will generate approximately ${n} document${n !== 1 ? "s" : ""}.`;
});

// ----- helpers
function freqLabel(f) { return f || "—"; }
function statusClass(s) {
  if (s === "Cancelled" || s === "Completed") return "badge-grey";
  if (s === "Paused") return "badge-orange";
  return "badge-green";
}
function isDue(r) {
  const t = new Date().toISOString().slice(0, 10);
  return r.next_schedule_date && r.next_schedule_date <= t && r.ui_status === "Active";
}
function fmtCurrency(v) {
  if (v == null || v === "") return "—";
  const n = Number(v) || 0;
  return "₹" + n.toLocaleString("en-IN", { maximumFractionDigits: 2 });
}

function sort(col) {
  if (sortCol.value === col) sortDir.value = sortDir.value === "asc" ? "desc" : "asc";
  else { sortCol.value = col; sortDir.value = "asc"; }
}
function sortArrow(col) {
  if (sortCol.value !== col) return '<span style="color:#d1d5db">⇅</span>';
  return sortDir.value === "asc" ? "↑" : "↓";
}

function toggleAll() { selected.value = allSelected.value ? [] : sorted.value.map((r) => r.name); }
function toggleOne(n) { selected.value = selected.value.includes(n) ? selected.value.filter((x) => x !== n) : [...selected.value, n]; }

// ----- load
async function load() {
  loading.value = true;
  try {
    const [rows, st] = await Promise.all([
      apiGET("zoho_books_clone.api.recurring.get_subscriptions", { limit: 200 }),
      apiGET("zoho_books_clone.api.recurring.get_subscription_stats", {}),
    ]);
    list.value = Array.isArray(rows) ? rows : (rows?.message ?? []);
    stats.value = st?.message ?? st ?? stats.value;
  } catch (e) {
    console.warn("Failed to load subscriptions", e);
    list.value = [];
    toast.error(e.message || "Failed to load subscriptions");
  } finally {
    loading.value = false;
  }
}
onMounted(async () => {
  await load();
  useOpenFromQuery({
    route,
    openByName: (n) => openView(list.value.find(x => x.name === n) || { name: n }),
  });
});

// ----- view drawer
async function openView(r) {
  if (!r?.name) return;
  viewOpen.value = true;
  viewTab.value = "details";
  // optimistic shallow view first
  viewDoc.value = { ...r, runs: r.runs || [], upcoming: r.upcoming || [], total_billed: r.total_billed || 0, runs_count: r.runs_count || 0 };
  try {
    const detail = await apiGET("zoho_books_clone.api.recurring.get_subscription", { name: r.name });
    // apiGET already unwraps `.message`, so `detail` is the dict directly.
    const d = (detail && typeof detail === "object") ? detail : {};
    // Merge: keep optimistic fields and overlay detail-only fields. Detail's
    // `runs` always wins (it's the authoritative source), even if empty.
    viewDoc.value = {
      ...viewDoc.value,
      ...d,
      runs: Array.isArray(d.runs) ? d.runs : (viewDoc.value.runs || []),
      upcoming: Array.isArray(d.upcoming) ? d.upcoming : (viewDoc.value.upcoming || []),
      runs_count: (d.runs_count != null) ? d.runs_count
                  : (Array.isArray(d.runs) ? d.runs.length : (viewDoc.value.runs_count || 0)),
      total_billed: (d.total_billed != null) ? d.total_billed : (viewDoc.value.total_billed || 0),
    };
  } catch (e) {
    toast.error(e.message || "Failed to load subscription detail");
  }
}

// ----- actions
async function quickAction(r, action) {
  const messages = {
    pause: { title: `Pause ${r.name}?`, body: "It will stop generating documents until resumed.", okLabel: "Pause", okStyle: "primary" },
    resume: { title: `Resume ${r.name}?`, body: "It will start generating documents on schedule.", okLabel: "Resume", okStyle: "primary" },
    cancel: { title: `Cancel ${r.name}?`, body: "Subscription will be ended permanently.", okLabel: "Cancel Sub", okStyle: "danger" },
    delete: { title: `Delete ${r.name}?`, body: "This cannot be undone.", okLabel: "Delete", okStyle: "danger" },
  };
  const m = messages[action];
  if (!(await confirm(m))) return;
  await runLifecycle(r.name, action);
}

async function actionOn(doc, action) {
  if (!doc?.name) return;
  const docName = doc.name;
  await quickAction(doc, action);
  if (action === "delete") {
    viewOpen.value = false;
  } else if (viewOpen.value && docName) {
    await openView({ name: docName });
  }
}

async function runLifecycle(name, action) {
  actionLoading.value = true;
  try {
    const method = `zoho_books_clone.api.recurring.${action}_subscription`;
    const res = await apiPOST(method, { name });
    toast.success(res?.message?.message || res?.message || `${name} ${action}d`);
    await load();
  } catch (e) {
    toast.error(e.message || `Failed to ${action}`);
  } finally {
    actionLoading.value = false;
  }
}

async function runNow(doc) {
  if (!doc?.name) return;
  const docName = doc.name;
  if (!(await confirm({ title: `Run ${docName} now?`, body: "A new document will be generated immediately, ignoring the schedule.", okLabel: "Run Now", okStyle: "primary" }))) return;
  actionLoading.value = true;
  try {
    const res = await apiPOST("zoho_books_clone.api.recurring.run_subscription_now", { name: docName });
    const gen = res?.message?.generated || res?.generated;
    toast.success(gen ? `Generated ${gen}` : "Document generated");
    await load();
    await openView({ name: docName });
  } catch (e) {
    toast.error(e.message || "Failed to run subscription");
  } finally {
    actionLoading.value = false;
  }
}

async function bulkDo(action) {
  if (!selected.value.length) return;
  if (!(await confirm({ title: `${action.charAt(0).toUpperCase()+action.slice(1)} ${selected.value.length} subscription(s)?`, body: "This applies to all selected rows.", okLabel: action.charAt(0).toUpperCase()+action.slice(1), okStyle: action === "delete" || action === "cancel" ? "danger" : "primary" }))) return;
  actionLoading.value = true;
  try {
    const res = await apiPOST("zoho_books_clone.api.recurring.bulk_action", { names: selected.value, action });
    const ok = res?.message?.ok || res?.ok || [];
    const failed = res?.message?.failed || res?.failed || [];
    toast.success(`${ok.length} updated${failed.length ? `, ${failed.length} failed` : ""}`);
    selected.value = [];
    await load();
  } catch (e) {
    toast.error(e.message || "Bulk action failed");
  } finally {
    actionLoading.value = false;
  }
}

// ----- create / edit
function openNew() {
  editMode.value = false;
  Object.assign(form, {
    _name: "",
    reference_doctype: "Sales Invoice",
    reference_document: "",
    frequency: "Monthly",
    start_date: new Date().toISOString().slice(0, 10),
    end_date: "",
    submit_on_creation: 1,
    _notify: false,
    recipients: "",
    subject: "",
    message: "",
  });
  Object.assign(referenceMeta, { party_label: "", party: "", amount: 0 });
  drawerOpen.value = true;
  // Pre-load submitted docs for the default doctype
  fetchRefDocs("");
}

function openEdit(doc) {
  if (!doc?.name) return;
  editMode.value = true;
  // Close view drawer so edit drawer is the only visible one
  viewOpen.value = false;
  Object.assign(form, {
    _name: doc.name,
    reference_doctype: doc.reference_doctype,
    reference_document: doc.reference_document,
    frequency: doc.frequency,
    start_date: doc.start_date || "",
    end_date: doc.end_date || "",
    submit_on_creation: doc.submit_on_creation ? 1 : 0,
    _notify: !!doc.notify_by_email,
    recipients: doc.recipients || "",
    subject: doc.subject || "",
    message: doc.message || "",
  });
  refDocs.value = doc.reference_document ? [{ label: doc.reference_document, value: doc.reference_document }] : [];
  Object.assign(referenceMeta, { party_label: doc.party_label || "", party: doc.party || "", amount: doc.template_amount || 0 });
  drawerOpen.value = true;
}

function onOverlayClose() {
  if (drawerSaving.value) return;
  drawerOpen.value = false;
}

function onTypeChange() {
  form.reference_document = "";
  refDocs.value = [];
  Object.assign(referenceMeta, { party_label: "", party: "", amount: 0 });
  // Immediately load submitted docs for the newly selected doctype
  fetchRefDocs("");
}

async function fetchRefDocs(q = "") {
  const doctype = form.reference_doctype || "Sales Invoice";
  try {
    // Sales Invoices: only submitted (docstatus=1) — must be posted to ledger.
    // Quotations: all statuses (draft, submitted, etc.) are valid templates.
    const filters = doctype === "Sales Invoice" ? [["docstatus", "=", 1]] : [];
    if (q) filters.push(["name", "like", `%${q}%`]);

    const r = await apiGET("frappe.client.get_list", {
      doctype,
      filters: JSON.stringify(filters),
      fields: JSON.stringify(["name"]),
      limit: 50,
      order_by: "name asc",
    });
    const rows = Array.isArray(r) ? r : (r?.message ?? []);
    refDocs.value = rows.map((x) => ({ label: x.name, value: x.name }));
  } catch {
    refDocs.value = [];
  }
}

// Watch the chosen reference document to fetch its party + amount
watch(() => form.reference_document, async (v) => {
  if (!v || !form.reference_doctype) {
    Object.assign(referenceMeta, { party_label: "", party: "", amount: 0 });
    return;
  }
  try {
    const fieldsByType = {
      "Sales Invoice": ["customer_name", "grand_total"],
      "Quotation": ["customer_name", "grand_total"],
    };
    const fields = fieldsByType[form.reference_doctype];
    if (!fields) return;
    const r = await apiGET("frappe.client.get_value", {
      doctype: form.reference_doctype,
      filters: JSON.stringify({ name: v }),
      fieldname: JSON.stringify(fields),
    });
    const row = r?.message || {};
    Object.assign(referenceMeta, {
      party_label: form.reference_doctype === "Customer",
      party: row[fields[0]] || "",
      amount: Number(row[fields[1]]) || 0,
    });
  } catch {
    /* silent */
  }
});

async function saveRec() {
  if (!form.reference_document) return toast.error("Reference document is required");
  if (!form.start_date) return toast.error("Start date is required");
  if (form.end_date && form.end_date < form.start_date) return toast.error("End date must be after start date");

  drawerSaving.value = true;
  try {
    if (editMode.value) {
      await apiPOST("zoho_books_clone.api.recurring.update_subscription", {
        name: form._name,
        frequency: form.frequency,
        end_date: form.end_date || null,
        notify_by_email: form._notify ? 1 : 0,
        submit_on_creation: form.submit_on_creation,
        recipients: form.recipients,
        subject: form.subject,
        message: form.message,
      });
      toast.success(`${form._name} updated`);
    } else {
      const doc = {
        doctype: "Auto Repeat",
        reference_doctype: form.reference_doctype,
        reference_document: form.reference_document,
        frequency: form.frequency,
        start_date: form.start_date,
        end_date: form.end_date || null,
        submit_on_creation: form.submit_on_creation,
        notify_by_email: form._notify ? 1 : 0,
        recipients: form.recipients || "",
        subject: form.subject || "",
        message: form.message || "",
      };
      const saved = await apiSave(doc);
      toast.success(`Subscription ${saved?.name || ""} created`);
    }
    drawerOpen.value = false;
    // After an edit, reopen the view drawer with refreshed data
    if (editMode.value && form._name) await openView({ name: form._name });
    else if (viewOpen.value && viewDoc.value?.name) await openView({ name: viewDoc.value.name });
    await load();
  } catch (e) {
    toast.error(e.message || "Failed to save");
  } finally {
    drawerSaving.value = false;
  }
}

// ----- export
function exportCSV() {
  // If any rows are selected, export only those; otherwise export the filtered view.
  const source = selected.value.length
    ? sorted.value.filter((r) => selected.value.includes(r.name))
    : sorted.value;
  if (!source.length) return;
  const headers = ["Subscription #", "Type", "Reference", "Party", "Amount", "Frequency", "Start Date", "End Date", "Next Run", "Status", "Runs"];
  const rows = source.map((r) => [
    r.name, r.reference_doctype, r.reference_document, r.party, r.amount, r.frequency,
    r.start_date, r.end_date, r.next_schedule_date, r.ui_status, r.runs_count,
  ]);
  const esc = (v) => {
    const s = v == null ? "" : String(v);
    return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s;
  };
  const csv = "﻿" + [headers, ...rows].map((r) => r.map(esc).join(",")).join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `recurring-subscriptions-${new Date().toISOString().slice(0, 10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
}
</script>

<style scoped>
.rec-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.rec-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.rec-search-wrap{display:flex;align-items:center;gap:8px;background:#f3f4f6;border-radius:8px;padding:6px 12px;min-width:260px;}
.rec-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.rec-pills{display:flex;gap:6px;}
.rec-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;display:inline-flex;align-items:center;gap:6px;}
.rec-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.rec-pill-count{background:#e5e7eb;color:#374151;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:700;}
.rec-pill.active .rec-pill-count{background:#dbeafe;color:#1d4ed8;}
.rec-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.rec-btn-primary:hover{background:#1d4ed8;}.rec-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.rec-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:transparent;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.rec-btn-ghost:hover{background:#f9fafb;}
.rec-btn-ghost:disabled{opacity:.5;cursor:not-allowed;}
.rec-btn-danger{color:#dc2626;border-color:#fecaca;}.rec-btn-danger:hover{background:#fef2f2;}

.rec-summary{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;}
.rec-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;position:relative;overflow:hidden;}
.rec-sum-card.accent{background:linear-gradient(135deg,#eff6ff,#fff);border-color:#bfdbfe;}
.rec-sum-card.warn{background:linear-gradient(135deg,#fffbeb,#fff);border-color:#fde68a;}
.rec-sum-card.danger{background:linear-gradient(135deg,#fef2f2,#fff);border-color:#fecaca;}
.rec-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;font-weight:600;}
.rec-sum-val{font-size:22px;font-weight:700;color:#111827;font-family:monospace;}
.green{color:#16a34a!important;}.orange{color:#ea580c!important;}.red{color:#dc2626!important;}.blue{color:#2563eb!important;}

.inv-bulk-bar{display:flex;align-items:center;gap:8px;padding:10px 16px;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;flex-wrap:wrap;}
.inv-bulk-count{font-size:13px;font-weight:700;color:#1a6ef7;margin-right:4px;}
.inv-bulk-btn{display:inline-flex;align-items:center;gap:5px;background:#fff;border:1px solid #e2e8f0;border-radius:6px;padding:5px 12px;font-size:12.5px;font-weight:600;color:#374151;cursor:pointer;font-family:inherit;transition:border-color .15s,background .15s,color .15s;}
.inv-bulk-btn:hover:not(:disabled){background:#f8fafc;border-color:#1a6ef7;color:#1a6ef7;}
.inv-bulk-btn:disabled{opacity:.5;cursor:not-allowed;}
.inv-bulk-danger{border-color:rgba(220,38,38,.3);color:#dc2626;}
.inv-bulk-danger:hover:not(:disabled){background:#fee2e2;border-color:#dc2626;color:#dc2626;}
.inv-bulk-clear{background:none;border:none;font-size:12.5px;color:#6b7280;cursor:pointer;font-family:inherit;padding:4px 8px;border-radius:4px;}
.inv-bulk-clear:hover{background:#e0e7ff;color:#1a6ef7;}

.rec-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.rec-table{width:100%;border-collapse:collapse;font-size:13px;}
.rec-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.rec-table th.sortable{cursor:pointer;user-select:none;}.rec-table th.sortable:hover{color:#2563eb;}
.rec-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.rec-row:last-child td{border-bottom:none;}
.rec-row:hover td{background:#f9fafb;}
.rec-row.selected td{background:#eff6ff;}
.rec-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.rec-ref{font-family:monospace;font-size:12.5px;color:#374151;}
.mono-sm{font-family:monospace;font-size:12.5px;}
.text-muted{color:#6b7280;}
.text-accent{color:#2563eb;font-weight:600;}
.rec-due-dot{display:inline-block;width:6px;height:6px;background:#2563eb;border-radius:50%;margin-left:6px;vertical-align:middle;}
.rec-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.rec-badge-lg{padding:4px 12px;font-size:12.5px;}
.badge-green{background:#dcfce7;color:#16a34a;}
.badge-orange{background:#fff7ed;color:#ea580c;}
.badge-grey{background:#f3f4f6;color:#6b7280;}
.badge-red{background:#fef2f2;color:#dc2626;}
.rec-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;margin-left:4px;}
.rec-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.rec-act-danger:hover{color:#dc2626;background:#fef2f2;}
.rec-empty{text-align:center;padding:0!important;cursor:default!important;}
.rec-empty-wrap{padding:48px 20px;display:flex;flex-direction:column;align-items:center;gap:6px;color:#6b7280;}
.rec-empty-icon{color:#cbd5e1;margin-bottom:6px;}
.rec-empty-title{font-size:15px;font-weight:600;color:#374151;}
.rec-empty-sub{font-size:12.5px;max-width:380px;text-align:center;}
.rec-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* drawer */
.rec-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);backdrop-filter:blur(2px);z-index:40;}
.rec-drawer{position:fixed;top:0;right:-560px;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-12px 0 32px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s cubic-bezier(.32,.72,0,1);}
.rec-drawer.open{right:0;}
.rec-view-drawer{width:600px;right:-600px;}.rec-view-drawer.open{right:0;}
.rec-dheader{display:flex;align-items:flex-start;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.rec-dheader.edit{background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);}
.rec-dheader-left{display:flex;align-items:flex-start;gap:12px;}
.rec-dheader-ico{width:38px;height:38px;border-radius:10px;background:#fff;border:1px solid rgba(37,99,235,.18);display:inline-flex;align-items:center;justify-content:center;color:#2563eb;box-shadow:0 1px 3px rgba(15,23,42,.06);flex-shrink:0;}
.rec-dheader-ico.edit{color:#ca8a04;border-color:rgba(202,138,4,.25);}
.rec-dheader-title{font-size:15px;font-weight:700;color:#111827;letter-spacing:-0.01em;}
.rec-dheader-sub{font-size:12px;color:#475569;margin-top:3px;font-weight:500;}
.rec-dclose{background:rgba(255,255,255,.6);border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;transition:background .15s;}
.rec-dclose:hover{background:#fff;color:#111827;}
.rec-dbody{flex:1;overflow-y:auto;padding:18px 20px;display:flex;flex-direction:column;gap:18px;background:#f8fafc;}

/* Intro card showing chosen reference */
.rec-ctx-card{display:flex;align-items:center;gap:12px;background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:12px 14px;box-shadow:0 1px 2px rgba(15,23,42,.04);}
.rec-ctx-ico{width:36px;height:36px;border-radius:8px;background:#eff6ff;color:#2563eb;display:inline-flex;align-items:center;justify-content:center;flex-shrink:0;}
.rec-ctx-doctype{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.04em;font-weight:600;}
.rec-ctx-name{font-family:monospace;font-size:13px;color:#0f172a;font-weight:600;margin-top:1px;}
.rec-ctx-meta{text-align:right;display:flex;flex-direction:column;gap:2px;flex-shrink:0;}
.rec-ctx-party{font-size:12px;color:#475569;font-weight:600;max-width:140px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;}
.rec-ctx-amount{font-size:14px;font-weight:700;color:#0f172a;}

/* Sections */
.rec-section{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:12px;box-shadow:0 1px 2px rgba(15,23,42,.03);}
.rec-section-hdr{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#0f172a;}
.rec-section-hdr svg{color:#2563eb;}
.rec-section-empty{font-size:12.5px;color:#6b7280;font-style:italic;line-height:1.5;}
.rec-field-help{font-size:11.5px;color:#9ca3af;margin-top:4px;}

/* Toggle (right side of section header) */
.rec-toggle{position:relative;margin-left:auto;width:34px;height:18px;display:inline-block;cursor:pointer;}
.rec-toggle input{opacity:0;width:0;height:0;}
.rec-toggle-slider{position:absolute;inset:0;background:#cbd5e1;border-radius:18px;transition:background .18s;}
.rec-toggle-slider::before{content:"";position:absolute;width:14px;height:14px;left:2px;top:2px;background:#fff;border-radius:50%;transition:transform .18s;box-shadow:0 1px 3px rgba(0,0,0,.15);}
.rec-toggle input:checked + .rec-toggle-slider{background:#2563eb;}
.rec-toggle input:checked + .rec-toggle-slider::before{transform:translateX(16px);}

.rec-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.rec-field{display:flex;flex-direction:column;gap:4px;}
.rec-label{font-size:12px;font-weight:600;color:#374151;}
.rec-hint{font-weight:400;color:#9ca3af;font-size:11px;}
.req{color:#dc2626;}
.rec-input,.rec-select{border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;transition:border-color .15s, box-shadow .15s;}
.rec-input:hover:not(:disabled),.rec-select:hover:not(:disabled){border-color:#cbd5e1;}
.rec-input:focus,.rec-select:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12);}
.rec-input:disabled,.rec-select:disabled{background:#f1f5f9;color:#94a3b8;cursor:not-allowed;border-color:#e2e8f0;}
.rec-meta-inline{display:flex;gap:6px;margin-top:6px;flex-wrap:wrap;}
.rec-meta-chip{background:#f3f4f6;color:#374151;padding:3px 10px;border-radius:10px;font-size:11.5px;font-weight:500;}
.rec-plan-hint{background:#eff6ff;border:1px solid #bfdbfe;color:#1d4ed8;padding:8px 12px;border-radius:8px;font-size:12px;display:flex;align-items:center;gap:8px;}
.rec-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;background:#fff;}

/* view drawer */
.rec-view-head{padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.rec-view-head.paused{background:linear-gradient(135deg,#fff7ed 0%,#fed7aa 100%);}
.rec-view-head.completed{background:linear-gradient(135deg,#f3f4f6 0%,#e5e7eb 100%);}
.rec-view-head-row{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;}
.rec-view-num{font-size:18px;font-weight:700;font-family:monospace;color:#111827;}
.rec-view-sub{font-size:12.5px;color:#475569;margin-top:2px;}
.rec-view-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px;}
.rec-view-stats > div{background:rgba(255,255,255,.55);border-radius:8px;padding:8px 10px;}
.vh-lbl{font-size:10.5px;color:#475569;text-transform:uppercase;letter-spacing:.05em;font-weight:600;}
.vh-val{font-size:15px;font-weight:700;color:#0f172a;font-family:monospace;margin-top:2px;}
.rec-view-actbar{display:flex;flex-wrap:wrap;gap:6px;padding:10px 20px;border-bottom:1px solid #e5e7eb;background:#fff;flex-shrink:0;}
.rec-va-btn{display:inline-flex;align-items:center;gap:5px;border:1px solid #e5e7eb;background:#fff;color:#374151;border-radius:7px;padding:6px 11px;font-size:12.5px;font-weight:600;cursor:pointer;}
.rec-va-btn:hover{background:#f9fafb;border-color:#cbd5e1;}
.rec-va-btn:disabled{opacity:.45;cursor:not-allowed;}
.rec-va-warn{color:#ea580c;border-color:#fed7aa;}.rec-va-warn:hover:not(:disabled){background:#fff7ed;}
.rec-va-danger{color:#dc2626;border-color:#fecaca;}.rec-va-danger:hover:not(:disabled){background:#fef2f2;}

.rec-timeline{display:flex;align-items:center;padding:14px 20px;background:#fff;border-bottom:1px solid #e5e7eb;gap:0;flex-shrink:0;}
.rec-tl-step{display:flex;flex-direction:column;align-items:center;flex-shrink:0;min-width:80px;}
.rec-tl-dot{width:12px;height:12px;border-radius:50%;background:#e5e7eb;border:2px solid #fff;box-shadow:0 0 0 2px #e5e7eb;}
.rec-tl-step.done .rec-tl-dot{background:#16a34a;box-shadow:0 0 0 2px #16a34a;}
.rec-tl-step.current .rec-tl-dot{background:#2563eb;box-shadow:0 0 0 3px #bfdbfe;}
.rec-tl-lbl{font-size:11px;color:#6b7280;text-align:center;margin-top:6px;font-weight:600;line-height:1.3;}
.rec-tl-sub{font-weight:400;color:#9ca3af;font-size:10.5px;}
.rec-tl-line{flex:1;height:2px;background:#e5e7eb;min-width:20px;}
.rec-tl-line.done{background:#16a34a;}
.rec-tl-line.danger{background:#dc2626;}

.rec-view-tabs{display:flex;border-bottom:1px solid #e5e7eb;padding:0 12px;background:#fff;flex-shrink:0;}
.rec-vt-btn{background:transparent;border:none;padding:10px 14px;font-size:13px;font-weight:600;color:#6b7280;cursor:pointer;border-bottom:2px solid transparent;display:inline-flex;align-items:center;gap:6px;font-family:inherit;}
.rec-vt-btn.active{color:#2563eb;border-bottom-color:#2563eb;}
.rec-vt-count{background:#e5e7eb;color:#374151;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:700;}
.rec-vt-btn.active .rec-vt-count{background:#dbeafe;color:#1d4ed8;}
.rec-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.rec-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;font-weight:600;}
.rec-table-inner{font-size:12.5px;}
.rec-table-inner th{background:#fafafa;}
.rec-tab-empty{padding:24px;text-align:center;color:#9ca3af;font-size:13px;}
.rec-upcoming-list{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;}
.rec-upcoming-list li{background:#f9fafb;border:1px solid #f3f4f6;border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:12px;font-size:13px;}
.rec-upcoming-idx{background:#dbeafe;color:#1d4ed8;font-weight:700;padding:2px 8px;border-radius:8px;font-size:11.5px;font-family:monospace;}
</style>