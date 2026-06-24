<template>
<div class="sc-page">

  <!-- Single sticky block: header + tabs stick together as one unit -->
  <div class="sc-sticky">
    <div class="sc-header">
      <span class="sc-title">Company Settings</span>
      <button class="nim-btn nim-btn-primary" @click="save" :disabled="saving">
        {{ saving ? 'Saving…' : 'Save Changes' }}
      </button>
    </div>
    <div class="sc-tabs">
      <button v-for="t in TABS" :key="t.k"
        class="sc-tab" :class="{ 'sc-tab--active': activeTab === t.k }"
        @click="activeTab = t.k">
        {{ t.l }}
      </button>
    </div>
  </div>

  <!-- ── Company Profile ──────────────────────────────────────────── -->
  <div v-if="activeTab === 'profile'" class="sc-body">

    <div class="sc-card">
      <div class="sc-card-title">Company Logo</div>
      <div class="sc-logo-row">
        <div class="sc-logo-box">
          <img v-if="form.logo_url" :src="form.logo_url" style="width:100%;height:100%;object-fit:contain"/>
          <span v-else style="font-size:28px">🏢</span>
        </div>
        <div class="sc-logo-actions">
          <label class="nim-btn nim-btn-ghost" style="cursor:pointer">
            Upload Logo
            <input type="file" accept="image/*" style="display:none" @change="handleLogoUpload"/>
          </label>
          <div class="sc-hint">PNG, JPG up to 2 MB. Appears on PDF invoices.</div>
          <button v-if="form.logo_url" class="nim-btn" style="font-size:11px;padding:2px 8px;margin-top:4px" @click="form.logo_url=''">Remove</button>
        </div>
      </div>
    </div>

    <div class="sc-card">
      <div class="sc-card-title">Company Information</div>
      <div class="sc-fg">
        <div class="nim-field sc-full"><label class="nim-label">Company Name</label><input class="nim-input" v-model="form.default_company"/></div>
        <div class="nim-field"><label class="nim-label">Phone</label><input class="nim-input" v-model="form.company_phone"/></div>
        <div class="nim-field"><label class="nim-label">Email</label><input class="nim-input" v-model="form.company_email"/></div>
        <div class="nim-field sc-full"><label class="nim-label">Website</label><input class="nim-input" v-model="form.company_website"/></div>
        <div class="nim-field sc-full"><label class="nim-label">Address</label><input class="nim-input" v-model="form.company_address"/></div>
        <div class="nim-field"><label class="nim-label">City</label><input class="nim-input" v-model="form.company_city"/></div>
        <div class="nim-field">
          <label class="nim-label">Country</label>
          <select class="nim-input" v-model="form.company_country" @change="form.company_state = ''">
            <option value="">— Select Country —</option>
            <option v-for="c in COUNTRIES" :key="c" :value="c">{{ c }}</option>
          </select>
        </div>
        <div class="nim-field">
          <label class="nim-label">State / Province</label>
          <select v-if="stateOptions.length" class="nim-input" v-model="form.company_state">
            <option value="">— Select State —</option>
            <option v-for="s in stateOptions" :key="s" :value="s">{{ s }}</option>
          </select>
          <input v-else class="nim-input" v-model="form.company_state" placeholder="Enter state / province"/>
        </div>
        <div class="nim-field"><label class="nim-label">Pincode / ZIP</label><input class="nim-input" v-model="form.company_pincode"/></div>
        <div class="nim-field">
          <label class="nim-label">Fiscal Year Start</label>
          <select class="nim-input" v-model="form.fiscal_year_start_month">
            <option v-for="m in MONTHS" :key="m" :value="m">{{ m }}</option>
          </select>
        </div>
      </div>
    </div>
  </div>

  <!-- ── Invoices ─────────────────────────────────────────────────── -->
  <div v-else-if="activeTab === 'invoices'" class="sc-body sc-body--narrow">
    <div class="sc-card">
      <div class="sc-card-title">Invoice Settings</div>
      <div class="sc-fg sc-fg--single">
        <div class="nim-field"><label class="nim-label">Invoice Number Prefix</label><input class="nim-input" v-model="form.invoice_prefix" placeholder="INV"/></div>
        <div class="sc-toggle-row" @click="form.auto_send_invoice = form.auto_send_invoice ? 0 : 1">
          <div class="sc-toggle" :class="{ 'sc-toggle--on': form.auto_send_invoice }">
            <div class="sc-toggle-knob"></div>
          </div>
          <div>
            <div class="sc-toggle-label">Auto-Send Invoice on Submit</div>
            <div class="sc-hint">Email invoice to customer automatically when submitted</div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- ── Tax ─────────────────────────────────────────────────────── -->
  <div v-else-if="activeTab === 'tax'" class="sc-body sc-body--narrow">
    <div class="sc-card">
      <div class="sc-card-title">Tax Configuration</div>
      <div class="sc-fg sc-fg--single">
        <div class="nim-field"><label class="nim-label">GSTIN</label><input class="nim-input" v-model="form.gstin" placeholder="22AAAAA0000A1Z5"/></div>
        <div class="nim-field"><label class="nim-label">GST State</label><input class="nim-input" v-model="form.gst_state" placeholder="Maharashtra"/></div>
      </div>
    </div>
  </div>

  <!-- ── Reminders ───────────────────────────────────────────────── -->
  <div v-else class="sc-body sc-body--narrow">
    <div class="sc-card">
      <div class="sc-card-title">Payment Reminders</div>
      <div class="sc-fg sc-fg--single">
        <div class="sc-toggle-row" @click="form.send_payment_reminders = form.send_payment_reminders ? 0 : 1">
          <div class="sc-toggle" :class="{ 'sc-toggle--on': form.send_payment_reminders }">
            <div class="sc-toggle-knob"></div>
          </div>
          <div>
            <div class="sc-toggle-label">Send Overdue Payment Reminders</div>
            <div class="sc-hint">Automatically email overdue invoice reminders</div>
          </div>
        </div>
        <template v-if="form.send_payment_reminders">
          <div class="nim-field"><label class="nim-label">Remind N days before due</label><input class="nim-input" type="number" v-model="form.reminder_days_before" min="0"/></div>
          <div class="nim-field"><label class="nim-label">Remind N days after due</label><input class="nim-input" type="number" v-model="form.reminder_days_after" min="1"/></div>
        </template>
      </div>
    </div>
  </div>

</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiGET, apiPOST } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { COUNTRIES, statesFor } from "../composables/useCountryState.js";

const { toast } = useToast();

const form = reactive({
  default_company: "", default_currency: "INR", fiscal_year_start_month: "April",
  invoice_prefix: "INV", gstin: "", gst_state: "", logo_url: "",
  company_address: "", company_city: "", company_country: "India",
  company_state: "", company_pincode: "",
  company_phone: "", company_email: "", company_website: "",
  auto_send_invoice: 0, send_payment_reminders: 0,
  reminder_days_before: 3, reminder_days_after: 7, auto_reconcile: 0,
});
const saving    = ref(false);
const activeTab = ref("profile");

const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const TABS = [
  { k: "profile",   l: "Company Profile" },
  { k: "invoices",  l: "Invoices" },
  { k: "tax",       l: "Tax" },
  { k: "reminders", l: "Reminders" },
];

// COUNTRIES and statesFor() come from the shared useCountryState composable.
const stateOptions = computed(() => statesFor(form.company_country));

async function load() {
  try {
    const d = await apiGET("zoho_books_clone.api.admin.get_company_settings");
    Object.assign(form, d);
  } catch (e) { toast("Could not load settings", "error"); }
}

async function save() {
  saving.value = true;
  try {
    await apiPOST("zoho_books_clone.api.admin.save_company_settings", { ...form });
    toast("Settings saved");
  } catch (e) { toast(e.message, "error"); }
  saving.value = false;
}

function handleLogoUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  fd.append("doctype", "Books Company");
  fd.append("docname", form.default_company || "");
  fd.append("fieldname", "logo_url");
  fd.append("csrf_token", window.frappe?.csrf_token || "");
  fetch("/api/method/upload_file", { method: "POST", credentials: "same-origin", body: fd })
    .then((r) => r.json())
    .then((d) => { if (d.message?.file_url) { form.logo_url = d.message.file_url; toast("Logo uploaded"); } })
    .catch(() => toast("Upload failed", "error"));
}

onMounted(load);
</script>

<style scoped>
/* Page wrapper — plain block, no flex/height tricks.
   bv-app-content (overflow-y: auto) is the scroll container. */
.sc-page {
  background: #f0f2f5;
  padding-bottom: 32px;
}

/* ── Sticky block pins to the top of bv-app-content as it scrolls ── */
.sc-sticky {
  position: sticky;
  top: 0;
  z-index: 20;
  background: #f0f2f5;
}

.sc-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 24px 0;
}
.sc-title {
  font-size: 18px;
  font-weight: 700;
  color: #1a1a2e;
}

/* ── Tab bar ── */
.sc-tabs {
  display: flex;
  gap: 0;
  border-bottom: 2px solid #e4e8f0;
  padding: 0 24px;
  margin-top: 14px;
  overflow-x: auto;
  scrollbar-width: none;
}
.sc-tabs::-webkit-scrollbar { display: none; }

.sc-tab {
  padding: 10px 18px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  color: #868e96;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  margin-bottom: -2px;
  transition: color .15s;
}
.sc-tab:hover { color: #374151; }
.sc-tab--active {
  color: #2563eb;
  border-bottom-color: #2563eb;
}

/* ── Body — no overflow, just padding + grid layout ── */
.sc-body {
  padding: 24px;
  display: grid;
  gap: 20px;
  align-content: start;
  max-width: 720px;
  width: 100%;
}
.sc-body--narrow { max-width: 560px; }

/* ── Cards ── */
.sc-card {
  background: #fff;
  border: 1px solid #e4e8f0;
  border-radius: 12px;
  padding: 24px;
}
.sc-card-title {
  font-size: 14px;
  font-weight: 700;
  color: #1a1a2e;
  margin-bottom: 18px;
}

/* Logo row */
.sc-logo-row { display: flex; align-items: center; gap: 20px; flex-wrap: wrap; }
.sc-logo-box {
  width: 80px; height: 80px; flex-shrink: 0;
  border: 2px dashed #c5d0fa; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  overflow: hidden; background: #f8f9fc;
}
.sc-logo-actions { display: flex; flex-direction: column; gap: 6px; }
.sc-hint { font-size: 11px; color: #868e96; }

/* Form grid: 2 cols → 1 col on narrow */
.sc-fg {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 14px;
}
.sc-fg--single { grid-template-columns: 1fr; }
.sc-full { grid-column: 1 / -1; }

@media (max-width: 600px) {
  .sc-fg { grid-template-columns: 1fr; }
  .sc-full { grid-column: auto; }
  .sc-header { padding: 12px 16px 0; }
  .sc-tabs  { padding: 0 16px; }
  .sc-body  { padding: 16px; }
  .sc-card  { padding: 16px; }
  .sc-title { font-size: 15px; }
}

/* Toggle */
.sc-toggle-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #f8f9fc;
  border-radius: 8px;
  cursor: pointer;
  user-select: none;
}
.sc-toggle-row:hover { background: #f0f2f5; }
.sc-toggle {
  width: 36px; height: 20px; border-radius: 10px;
  position: relative; flex-shrink: 0;
  background: #cbd5e0; transition: background .2s;
}
.sc-toggle--on { background: #2563eb; }
.sc-toggle-knob {
  width: 16px; height: 16px; border-radius: 50%;
  background: #fff; position: absolute; top: 2px; left: 2px;
  transition: left .2s;
}
.sc-toggle--on .sc-toggle-knob { left: 18px; }
.sc-toggle-label { font-size: 13px; font-weight: 600; color: #1a1a2e; }
</style>
