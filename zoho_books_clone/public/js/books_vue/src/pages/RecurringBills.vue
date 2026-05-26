<template>
  <div class="rec-page">
    <!-- ============================================================ TOOLBAR -->
    <div class="rec-actions">
      <div class="rec-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search recurring bills…" class="rec-search-input" />
      </div>
      <div class="rec-pills">
        <button v-for="t in tabs" :key="t.key" class="rec-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">
          {{ t.label }}
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="rec-btn-ghost" @click="load" :disabled="loading">
          <span v-html="icon('refresh',14)"></span>
        </button>
        <button class="rec-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Recurring Bill
        </button>
      </div>
    </div>

    <!-- ============================================================ SUMMARY -->
    <SummaryStrip v-if="!loading" :cards="[
      { label: 'Total',     tone: 'accent',                                      value: list.length },
      { label: 'Active',    tone: 'success',                                     value: counts.active,    valueClass: 'green' },
      { label: 'Paused',    tone: counts.paused>0 ? 'warn' : 'default',          value: counts.paused,    valueClass: counts.paused>0 ? 'orange' : '' },
      { label: 'Cancelled', tone: counts.cancelled>0 ? 'danger' : 'default',     value: counts.cancelled, valueClass: counts.cancelled>0 ? 'red' : '' },
    ]" />

    <!-- ============================================================ TABLE -->
    <div class="rec-card">
      <table class="rec-table">
        <thead>
          <tr>
            <th @click="sort('name')" class="sortable">Subscription # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('reference_document')" class="sortable">PO Reference <span v-html="sortArrow('reference_document')"></span></th>
            <th @click="sort('frequency')" class="sortable">Frequency <span v-html="sortArrow('frequency')"></span></th>
            <th @click="sort('start_date')" class="sortable">Start Date <span v-html="sortArrow('start_date')"></span></th>
            <th @click="sort('next_schedule_date')" class="sortable">Next Run <span v-html="sortArrow('next_schedule_date')"></span></th>
            <th>Status</th>
            <th style="width:50px"></th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="7"><div class="rec-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="r in paged" :key="r.name" class="rec-row" @click="openView(r)">
              <td><span class="rec-num">{{ r.name }}</span></td>
              <td><span class="rec-ref">{{ r.reference_document||'—' }}</span></td>
              <td>{{ r.frequency||'—' }}</td>
              <td class="text-muted mono-sm">{{ fmtDate(r.start_date) }}</td>
              <td class="mono-sm" :class="isDue(r)?'text-accent':''">{{ fmtDate(r.next_schedule_date)||'—' }}</td>
              <td><span class="rec-badge" :class="statusClass(r.status)">{{ r.status||'Active' }}</span></td>
              <td @click.stop>
                <button class="rec-act-btn" @click="openView(r)"><span v-html="icon('eye',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length">
              <td colspan="7" class="rec-empty">
                <div class="rec-empty-wrap">
                  <div class="rec-empty-icon" v-html="icon('repeat',32)"></div>
                  <div class="rec-empty-title">No recurring bills found</div>
                  <div class="rec-empty-sub">Create a recurring bill to auto-generate purchase orders on a schedule.</div>
                  <button class="rec-btn-primary" @click="openNew" style="margin-top:12px">
                    <span v-html="icon('plus',13)"></span> Create your first recurring bill
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Pagination ── -->
    <div v-if="!loading && sorted.length" style="padding:12px 4px 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ============================================================ CREATE DRAWER -->
    <div v-if="drawerOpen" class="rec-overlay" @click.self="drawerOpen=false"></div>
    <div class="rec-drawer" :class="{open:drawerOpen}">
      <div class="rec-dheader">
        <div class="rec-dheader-left">
          <div class="rec-dheader-ico">
            <span v-html="icon('repeat',18)"></span>
          </div>
          <div>
            <div class="rec-dheader-title">New Recurring Bill</div>
            <div class="rec-dheader-sub">Schedule a purchase order to repeat on a cadence</div>
          </div>
        </div>
        <button class="rec-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="rec-dbody">
        <!-- Section: Reference -->
        <div class="rec-section">
          <div class="rec-section-hdr">
            <span v-html="icon('folder',13)"></span>
            <span>Reference Document</span>
          </div>
          <div class="rec-fields-grid">
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Purchase Order <span class="req">*</span></label>
              <SearchableSelect v-model="form.reference_document" :options="refDocs" placeholder="Search a saved purchase order…" @search="fetchRefDocs" />
              <div class="rec-field-help" v-if="!form.reference_document">
                Pick an existing purchase order to use as the template.
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
                <option value="Half-Yearly">Half-Yearly</option>
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
              <input v-model="form.start_date" type="date" class="rec-input" />
            </div>
            <div class="rec-field">
              <label class="rec-label">End Date <span class="rec-hint">(optional)</span></label>
              <input v-model="form.end_date" type="date" class="rec-input" :min="form.start_date" />
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
              <input v-model="form.subject" type="text" class="rec-input" placeholder="Your recurring bill is ready" />
            </div>
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Email Message</label>
              <textarea v-model="form.message" class="rec-input" rows="3" placeholder="Hello, please find your latest purchase order attached…"></textarea>
            </div>
          </div>
        </div>
      </div>

      <div class="rec-dfooter">
        <button class="rec-btn-ghost" @click="drawerOpen=false" :disabled="drawerSaving">Cancel</button>
        <button class="rec-btn-primary" :disabled="drawerSaving" @click="saveRec">
          <span v-html="icon('check',13)"></span>
          {{ drawerSaving ? 'Saving…' : 'Create Recurring Bill' }}
        </button>
      </div>
    </div>

    <!-- ============================================================ VIEW DRAWER -->
    <div v-if="viewOpen" class="rec-overlay" @click.self="viewOpen=false"></div>
    <div class="rec-drawer rec-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="rec-view-head" :class="viewDoc.status==='Paused'?'paused':viewDoc.status==='Cancelled'?'completed':''">
          <div class="rec-view-head-row">
            <div>
              <div class="rec-view-num">{{ viewDoc.name }}</div>
              <div class="rec-view-sub">Purchase Order · {{ viewDoc.frequency }}</div>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span class="rec-badge rec-badge-lg" :class="statusClass(viewDoc.status)">{{ viewDoc.status||'Active' }}</span>
              <button class="rec-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
            </div>
          </div>
          <div class="rec-view-stats">
            <div>
              <div class="vh-lbl">Start Date</div>
              <div class="vh-val">{{ fmtDate(viewDoc.start_date)||'—' }}</div>
            </div>
            <div>
              <div class="vh-lbl">Next Run</div>
              <div class="vh-val" :class="isDue(viewDoc)?'text-accent':''">{{ fmtDate(viewDoc.next_schedule_date)||'—' }}</div>
            </div>
            <div>
              <div class="vh-lbl">End Date</div>
              <div class="vh-val">{{ fmtDate(viewDoc.end_date)||'No end' }}</div>
            </div>
          </div>
        </div>

        <div class="rec-dbody">
          <div class="rec-section">
            <div class="rec-section-hdr">
              <span v-html="icon('folder',13)"></span>
              <span>Details</span>
            </div>
            <div class="rec-meta-grid">
              <div><div class="rec-meta-lbl">Bill Reference</div><div class="mono-sm">{{ viewDoc.reference_document||'—' }}</div></div>
              <div><div class="rec-meta-lbl">Frequency</div><div>{{ viewDoc.frequency }}</div></div>
              <div><div class="rec-meta-lbl">Start Date</div><div class="mono-sm">{{ fmtDate(viewDoc.start_date) }}</div></div>
              <div><div class="rec-meta-lbl">End Date</div><div class="mono-sm">{{ fmtDate(viewDoc.end_date)||'No end' }}</div></div>
              <div><div class="rec-meta-lbl">Next Run</div><div class="mono-sm" :class="isDue(viewDoc)?'text-accent':''">{{ fmtDate(viewDoc.next_schedule_date)||'—' }}</div></div>
              <div><div class="rec-meta-lbl">Submit on Creation</div><div>{{ viewDoc.submit_on_creation?'Yes':'No (Draft)' }}</div></div>
            </div>
          </div>

          <div v-if="viewDoc.recipients" class="rec-section">
            <div class="rec-section-hdr">
              <span v-html="icon('mail',13)"></span>
              <span>Notification</span>
            </div>
            <div class="rec-meta-grid">
              <div style="grid-column:1/-1">
                <div class="rec-meta-lbl">Recipients</div>
                <div class="mono-sm" style="word-break:break-all">{{ viewDoc.recipients }}</div>
              </div>
              <div v-if="viewDoc.subject" style="grid-column:1/-1">
                <div class="rec-meta-lbl">Email Subject</div>
                <div>{{ viewDoc.subject }}</div>
              </div>
              <div v-if="viewDoc.message" style="grid-column:1/-1">
                <div class="rec-meta-lbl">Email Message</div>
                <div style="font-size:13px;color:#374151;white-space:pre-wrap;">{{ viewDoc.message }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="rec-dfooter">
          <button class="rec-btn-ghost" @click="viewOpen=false">Close</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiLinkValues } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import Pagination from "../components/Pagination.vue";
import { usePagination } from "../composables/usePagination.js";

const { toast } = useToast();
const activeTab = ref("all");
const tabs = [
  { key: "all", label: "All" },
  { key: "Active", label: "Active" },
  { key: "Paused", label: "Paused" },
  { key: "Cancelled", label: "Cancelled" },
];
const list = ref([]), loading = ref(false), search = ref("");
const drawerOpen = ref(false), drawerSaving = ref(false);
const viewOpen = ref(false), viewDoc = ref(null);
const refDocs = ref([]);
const sortCol = ref("next_schedule_date"), sortDir = ref("asc");
const form = reactive({
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

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Auto Repeat", {
      fields: ["name","reference_doctype","reference_document","frequency","start_date","end_date","next_schedule_date","status"],
      filters: [["reference_doctype","=","Purchase Order"]],
      limit: 500, order: "next_schedule_date asc",
    }) || [];
  } catch (e) {
    console.warn("Auto Repeat load failed:", e.message);
    list.value = [];
  } finally { loading.value = false; }
}

const today = new Date().toISOString().slice(0, 10);
function isDue(r) { return r.next_schedule_date && r.next_schedule_date <= today && (r.status||"Active") === "Active"; }
function statusClass(s) { if (s==="Cancelled") return "badge-grey"; if (s==="Paused") return "badge-orange"; return "badge-green"; }

const counts = computed(() => ({
  active:    list.value.filter(r => (r.status||"Active") === "Active").length,
  paused:    list.value.filter(r => r.status === "Paused").length,
  cancelled: list.value.filter(r => r.status === "Cancelled").length,
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") r = r.filter(x => (x.status||"Active") === activeTab.value);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name||"").toLowerCase().includes(q) || (x.reference_document||"").toLowerCase().includes(q));
  }
  return r;
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const c = String(a[col]??"").localeCompare(String(b[col]??""));
    return sortDir.value === "asc" ? c : -c;
  });
});
const { page, pageSize, paged } = usePagination(sorted, { storageKey: "recurring-bills" });

function sort(col) { if (sortCol.value===col) sortDir.value=sortDir.value==="asc"?"desc":"asc"; else { sortCol.value=col; sortDir.value="asc"; } }
function sortArrow(col) { if (sortCol.value!==col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value==="asc"?"↑":"↓"; }

function openNew() {
  Object.assign(form, {
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
  refDocs.value = [];
  drawerOpen.value = true;
  fetchRefDocs();
}
function openView(r) { viewDoc.value = r; viewOpen.value = true; }

async function fetchRefDocs(q = "") {
  try {
    const r = await apiLinkValues("Purchase Order", q, [["docstatus","in",[0,1]]]);
    refDocs.value = r.map(x => ({ label: x.name, value: x.name }));
  } catch { refDocs.value = []; }
}

async function saveRec() {
  if (!form.reference_document) return toast.error("Purchase order is required");
  drawerSaving.value = true;
  try {
    const doc = {
      doctype: "Auto Repeat",
      reference_doctype: "Purchase Order",
      reference_document: form.reference_document,
      frequency: form.frequency,
      start_date: form.start_date,
      end_date: form.end_date || null,
      submit_on_creation: form.submit_on_creation,
      recipients: form._notify ? (form.recipients || "") : "",
      subject: form._notify ? (form.subject || "") : "",
      message: form._notify ? (form.message || "") : "",
    };
    const saved = await apiSave(doc);
    toast.success(`Recurring bill ${saved?.name||""} created`);
    drawerOpen.value = false;
    await load();
  } catch (e) { toast.error(e.message || "Failed to create recurring bill"); }
  finally { drawerSaving.value = false; }
}

onMounted(load);
</script>

<style scoped>
/* ── Page & Toolbar ── */
.rec-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.rec-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.rec-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;border:1px solid #e5e7eb;}
.rec-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.rec-pills{display:flex;gap:6px;}
.rec-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.rec-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.rec-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;}
.rec-btn-primary:hover{background:#1d4ed8;}
.rec-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.rec-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;font-family:inherit;}
.rec-btn-ghost:hover{background:#f9fafb;}
.rec-btn-ghost:disabled{opacity:.5;cursor:not-allowed;}

/* ── Table ── */
.green{color:#16a34a!important;}.orange{color:#ea580c!important;}.red{color:#dc2626!important;}
.rec-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.rec-table{width:100%;border-collapse:collapse;font-size:13px;}
.rec-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;}
.rec-table th.sortable{cursor:pointer;user-select:none;}.rec-table th.sortable:hover{color:#2563eb;}
.rec-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.rec-row:last-child td{border-bottom:none;}.rec-row:hover td{background:#f9fafb;}
.rec-num{font-family:monospace;font-size:12.5px;color:#2563eb;font-weight:600;}
.rec-ref{font-family:monospace;font-size:12.5px;color:#374151;}
.mono-sm{font-family:monospace;font-size:12.5px;}.text-muted{color:#6b7280;}.text-accent{color:#2563eb;font-weight:600;}
.rec-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.rec-badge-lg{padding:4px 10px;font-size:12.5px;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.rec-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.rec-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.rec-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.rec-empty-wrap{display:flex;flex-direction:column;align-items:center;gap:6px;color:#9ca3af;}
.rec-empty-icon{color:#cbd5e1;margin-bottom:6px;}
.rec-empty-title{font-size:15px;font-weight:600;color:#374151;}
.rec-empty-sub{font-size:12.5px;max-width:380px;text-align:center;}
.rec-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* ── Overlay & Drawer ── */
.rec-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);backdrop-filter:blur(2px);z-index:40;}
.rec-drawer{position:fixed;top:0;right:-560px;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-12px 0 32px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s cubic-bezier(.32,.72,0,1);}
.rec-drawer.open{right:0;}
.rec-view-drawer{width:520px;right:-520px;}.rec-view-drawer.open{right:0;}

/* ── Drawer Header ── */
.rec-dheader{display:flex;align-items:flex-start;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.rec-dheader-left{display:flex;align-items:flex-start;gap:12px;}
.rec-dheader-ico{width:38px;height:38px;border-radius:10px;background:#fff;border:1px solid rgba(37,99,235,.18);display:inline-flex;align-items:center;justify-content:center;color:#2563eb;box-shadow:0 1px 3px rgba(15,23,42,.06);flex-shrink:0;}
.rec-dheader-title{font-size:15px;font-weight:700;color:#111827;letter-spacing:-0.01em;}
.rec-dheader-sub{font-size:12px;color:#475569;margin-top:3px;font-weight:500;}
.rec-dclose{background:rgba(255,255,255,.6);border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;transition:background .15s;}
.rec-dclose:hover{background:#fff;color:#111827;}

/* ── Drawer Body ── */
.rec-dbody{flex:1;overflow-y:auto;padding:18px 20px;display:flex;flex-direction:column;gap:18px;background:#f8fafc;}

/* ── Sections ── */
.rec-section{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:12px;box-shadow:0 1px 2px rgba(15,23,42,.03);}
.rec-section-hdr{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#0f172a;}
.rec-section-hdr svg{color:#2563eb;}
.rec-section-empty{font-size:12.5px;color:#6b7280;font-style:italic;line-height:1.5;}
.rec-field-help{font-size:11.5px;color:#9ca3af;margin-top:4px;}

/* ── Toggle ── */
.rec-toggle{position:relative;margin-left:auto;width:34px;height:18px;display:inline-block;cursor:pointer;}
.rec-toggle input{opacity:0;width:0;height:0;}
.rec-toggle-slider{position:absolute;inset:0;background:#cbd5e1;border-radius:18px;transition:background .18s;}
.rec-toggle-slider::before{content:"";position:absolute;width:14px;height:14px;left:2px;top:2px;background:#fff;border-radius:50%;transition:transform .18s;box-shadow:0 1px 3px rgba(0,0,0,.15);}
.rec-toggle input:checked + .rec-toggle-slider{background:#2563eb;}
.rec-toggle input:checked + .rec-toggle-slider::before{transform:translateX(16px);}

/* ── Fields ── */
.rec-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.rec-field{display:flex;flex-direction:column;gap:4px;}
.rec-label{font-size:12px;font-weight:600;color:#374151;}
.rec-hint{font-weight:400;color:#9ca3af;font-size:11px;}
.req{color:#dc2626;}
.rec-input,.rec-select{border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;transition:border-color .15s, box-shadow .15s;}
.rec-input:hover:not(:disabled),.rec-select:hover:not(:disabled){border-color:#cbd5e1;}
.rec-input:focus,.rec-select:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12);}
.rec-input:disabled,.rec-select:disabled{background:#f1f5f9;color:#94a3b8;cursor:not-allowed;border-color:#e2e8f0;}
textarea.rec-input{resize:vertical;min-height:72px;}

/* ── Drawer Footer ── */
.rec-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;background:#fff;}

/* ── View Drawer Header ── */
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
.rec-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.rec-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;font-weight:600;}
</style>