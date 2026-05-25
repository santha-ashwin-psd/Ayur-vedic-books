<template>
  <div class="rec-page">
    <div class="rec-actions">
      <div class="rec-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search recurring bills…" class="rec-search-input" />
      </div>
      <div class="rec-pills">
        <button v-for="t in tabs" :key="t.key" class="rec-pill" :class="{active:activeTab===t.key}" @click="activeTab=t.key">{{ t.label }}</button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="rec-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="rec-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Recurring Bill</button>
      </div>
    </div>

    <div class="rec-summary" v-if="!loading">
      <div class="rec-sum-card"><div class="rec-sum-lbl">Active</div><div class="rec-sum-val green">{{ counts.active }}</div></div>
      <div class="rec-sum-card"><div class="rec-sum-lbl">Paused</div><div class="rec-sum-val orange">{{ counts.paused }}</div></div>
      <div class="rec-sum-card"><div class="rec-sum-lbl">Cancelled</div><div class="rec-sum-val red">{{ counts.cancelled }}</div></div>
      <div class="rec-sum-card"><div class="rec-sum-lbl">Total</div><div class="rec-sum-val">{{ list.length }}</div></div>
    </div>

    <div class="rec-card">
      <table class="rec-table">
        <thead>
          <tr>
            <th @click="sort('name')" class="sortable">Subscription # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('reference_document')" class="sortable">Bill Reference <span v-html="sortArrow('reference_document')"></span></th>
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
            <tr v-for="r in sorted" :key="r.name" class="rec-row" @click="openView(r)">
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
            <tr v-if="!sorted.length"><td colspan="7" class="rec-empty">No recurring bills found</td></tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- Create Drawer -->
    <div v-if="drawerOpen" class="rec-overlay" @click.self="drawerOpen=false"></div>
    <div class="rec-drawer" :class="{open:drawerOpen}">
      <div class="rec-dheader">
        <div class="rec-dheader-title">New Recurring Bill</div>
        <button class="rec-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="rec-dbody">
        <div class="rec-fields-grid">
          <div class="rec-field" style="grid-column:1/-1">
            <label class="rec-label">Purchase Invoice <span class="req">*</span></label>
            <SearchableSelect v-model="form.reference_document" :options="refDocs" placeholder="Select purchase invoice…" @search="fetchRefDocs" />
          </div>
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
            <label class="rec-label">Start Date <span class="req">*</span></label>
            <input v-model="form.start_date" type="date" class="rec-input" />
          </div>
          <div class="rec-field">
            <label class="rec-label">End Date</label>
            <input v-model="form.end_date" type="date" class="rec-input" />
          </div>
          <div class="rec-field">
            <label class="rec-label">Submit on Creation</label>
            <select v-model="form.submit_on_creation" class="rec-select">
              <option :value="1">Yes</option>
              <option :value="0">No (Save Draft)</option>
            </select>
          </div>
          <div class="rec-field">
            <label class="rec-label">Notify By Email</label>
            <input v-model="form.notify_by_email" type="email" class="rec-input" placeholder="email@example.com" />
          </div>
        </div>
      </div>
      <div class="rec-dfooter">
        <button class="rec-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="rec-btn-primary" :disabled="drawerSaving" @click="saveRec">
          <span v-html="icon('check',13)"></span> {{ drawerSaving?'Saving…':'Create' }}
        </button>
      </div>
    </div>

    <!-- View Drawer -->
    <div v-if="viewOpen" class="rec-overlay" @click.self="viewOpen=false"></div>
    <div class="rec-drawer rec-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="rec-view-head">
          <div><div class="rec-view-num">{{ viewDoc.name }}</div><div class="rec-view-sub">Purchase Invoice · {{ viewDoc.frequency }}</div></div>
          <span class="rec-badge" :class="statusClass(viewDoc.status)">{{ viewDoc.status||'Active' }}</span>
          <button class="rec-dclose rec-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="rec-dbody">
          <div class="rec-meta-grid">
            <div><div class="rec-meta-lbl">Bill Reference</div><div class="mono-sm">{{ viewDoc.reference_document||'—' }}</div></div>
            <div><div class="rec-meta-lbl">Frequency</div><div>{{ viewDoc.frequency }}</div></div>
            <div><div class="rec-meta-lbl">Start Date</div><div class="mono-sm">{{ fmtDate(viewDoc.start_date) }}</div></div>
            <div><div class="rec-meta-lbl">End Date</div><div class="mono-sm">{{ fmtDate(viewDoc.end_date)||'No end' }}</div></div>
            <div><div class="rec-meta-lbl">Next Run</div><div class="mono-sm" :class="isDue(viewDoc)?'text-accent':''">{{ fmtDate(viewDoc.next_schedule_date)||'—' }}</div></div>
            <div><div class="rec-meta-lbl">Last Run</div><div class="mono-sm">{{ fmtDate(viewDoc.last_scheduled_date)||'Never' }}</div></div>
          </div>
        </div>
        <div class="rec-dfooter"><button class="rec-btn-ghost" @click="viewOpen=false">Close</button></div>
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

const { toast } = useToast();
const activeTab = ref("all");
const tabs = [{key:"all",label:"All"},{key:"Active",label:"Active"},{key:"Paused",label:"Paused"},{key:"Cancelled",label:"Cancelled"}];
const list = ref([]), loading = ref(false), search = ref("");
const drawerOpen = ref(false), drawerSaving = ref(false);
const viewOpen = ref(false), viewDoc = ref(null);
const refDocs = ref([]);
const sortCol = ref("next_schedule_date"), sortDir = ref("asc");
const form = reactive({
  reference_document: "", frequency: "Monthly",
  start_date: new Date().toISOString().slice(0, 10),
  end_date: "", submit_on_creation: 1, notify_by_email: "",
});

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Auto Repeat", {
      fields: ["name","reference_doctype","reference_document","frequency","start_date","end_date","next_schedule_date","last_scheduled_date","status"],
      filters: [["reference_doctype","=","Purchase Invoice"]],
      limit: 200, order: "next_schedule_date asc",
    });
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

function sort(col) { if (sortCol.value===col) sortDir.value=sortDir.value==="asc"?"desc":"asc"; else { sortCol.value=col; sortDir.value="asc"; } }
function sortArrow(col) { if (sortCol.value!==col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value==="asc"?"↑":"↓"; }

function openNew() {
  Object.assign(form, { reference_document:"", frequency:"Monthly", start_date:new Date().toISOString().slice(0,10), end_date:"", submit_on_creation:1, notify_by_email:"" });
  refDocs.value = [];
  drawerOpen.value = true;
}
function openView(r) { viewDoc.value = r; viewOpen.value = true; }

async function fetchRefDocs(q = "") {
  try {
    const r = await apiLinkValues("Purchase Invoice", q, [["docstatus","=",1]]);
    refDocs.value = r.map(x => ({ label: x.name, value: x.name }));
  } catch { refDocs.value = []; }
}

async function saveRec() {
  if (!form.reference_document) return toast.error("Purchase invoice is required");
  drawerSaving.value = true;
  try {
    const doc = {
      doctype: "Auto Repeat",
      reference_doctype: "Purchase Invoice",
      reference_document: form.reference_document,
      frequency: form.frequency,
      start_date: form.start_date,
      end_date: form.end_date || null,
      submit_on_creation: form.submit_on_creation,
      notify_by_email: form.notify_by_email || "",
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
.rec-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.rec-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.rec-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;}
.rec-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.rec-pills{display:flex;gap:6px;}
.rec-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.rec-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.rec-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.rec-btn-primary:hover{background:#1d4ed8;}.rec-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.rec-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.rec-btn-ghost:hover{background:#f9fafb;}
.rec-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;}
.rec-sum-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;}
.rec-sum-lbl{font-size:11px;color:#6b7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px;}
.rec-sum-val{font-size:18px;font-weight:700;color:#111827;font-family:monospace;}
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
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fff7ed;color:#ea580c;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.rec-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.rec-act-btn:hover{background:#f3f4f6;color:#2563eb;}
.rec-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.rec-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.rec-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.rec-drawer{position:fixed;top:0;right:-480px;bottom:0;width:480px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.rec-drawer.open{right:0;}
.rec-view-drawer{width:420px;right:-420px;}.rec-view-drawer.open{right:0;}
.rec-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.rec-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.rec-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.rec-dclose:hover{background:#f3f4f6;color:#111827;}
.rec-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.rec-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.rec-field{display:flex;flex-direction:column;gap:4px;}
.rec-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.rec-input{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.rec-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
.rec-select{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;cursor:pointer;}
.rec-select:focus{border-color:#2563eb;}
.rec-view-head{position:relative;display:flex;align-items:center;justify-content:space-between;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#eff6ff;gap:12px;}
.rec-view-num{font-size:16px;font-weight:700;font-family:monospace;color:#111827;}
.rec-view-sub{font-size:12px;color:#6b7280;margin-top:2px;}
.rec-vclose{position:absolute;top:12px;right:12px;}
.rec-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.rec-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.rec-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
