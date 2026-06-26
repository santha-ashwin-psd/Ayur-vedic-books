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
        <div class="nim-field">
          <label class="nim-label">GSTIN</label>
          <input class="nim-input" v-model="form.gstin" placeholder="22AAAAA0000A1Z5"
            @input="form.gstin = form.gstin.toUpperCase()"
            :style="form.gstin && !GSTIN_REGEX.test(form.gstin) ? 'border-color:#dc2626;background:#fff5f5' :
                    form.gstin && GSTIN_REGEX.test(form.gstin) ? 'border-color:#2f9e44' : ''"/>
          <div v-if="form.gstin && !GSTIN_REGEX.test(form.gstin)" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
            Invalid GSTIN format (e.g. 22AAAAA0000A1Z5)
          </div>
          <div v-else-if="form.gstin && GSTIN_REGEX.test(form.gstin)" style="margin-top:4px;font-size:12px;color:#2f9e44;display:flex;align-items:center;gap:4px">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
            Valid GSTIN
          </div>
        </div>
        <div class="nim-field"><label class="nim-label">GST State</label><input class="nim-input" v-model="form.gst_state" placeholder="Maharashtra"/></div>
      </div>
    </div>
  </div>

  <!-- ── Reminders ───────────────────────────────────────────────── -->
  <!-- Branding tab -->
  <div v-else-if="activeTab === 'branding'" class="sc-body sc-body--narrow">
    <div class="sc-card">
      <div class="sc-card-title">Invoice Template</div>
      <div class="sc-branding-templates">
        <button v-for="t in TEMPLATES" :key="t.key"
          class="sc-tmpl-btn" :class="{ 'sc-tmpl-btn--active': form.pdf_template === t.key }"
          @click="form.pdf_template = t.key">
          <div class="sc-tmpl-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><rect x="3" y="3" width="18" height="18" rx="2"/><line x1="3" y1="9" x2="21" y2="9"/><line x1="9" y1="21" x2="9" y2="9"/></svg>
          </div>
          <div class="sc-tmpl-label">{{ t.label }}</div>
          <div v-if="form.pdf_template === t.key" class="sc-tmpl-check">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
          </div>
        </button>
      </div>
    </div>

    <div class="sc-card">
      <div class="sc-card-title">Brand Color</div>
      <div class="sc-color-row">
        <label class="sc-color-pick" style="cursor:pointer">
          <span class="sc-color-swatch" :style="{ background: form.brand_color }"></span>
          <span class="sc-color-hex">{{ form.brand_color }}</span>
          <input type="color" v-model="form.brand_color" class="sc-color-input"/>
        </label>
        <div class="sc-hint">Used as the accent color on your PDF invoices.</div>
      </div>
    </div>

    <div class="sc-card">
      <div class="sc-card-title">Company Logo</div>
      <div class="sc-logo-row">
        <div class="sc-logo-box">
          <img v-if="form.company_logo" :src="resolveSrc(form.company_logo)" style="width:100%;height:100%;object-fit:contain"/>
          <span v-else style="font-size:28px">🏷️</span>
        </div>
        <div class="sc-logo-actions">
          <label class="nim-btn nim-btn-ghost" style="cursor:pointer">
            Upload Logo
            <input type="file" accept="image/*" style="display:none" @change="handleBrandingLogoUpload"/>
          </label>
          <div class="sc-hint">PNG, JPG or SVG (max. 2MB). Default logo on PDF invoices.</div>
          <button v-if="form.company_logo" class="nim-btn" style="font-size:11px;padding:2px 8px;margin-top:4px" @click="form.company_logo=''">Remove</button>
        </div>
      </div>
    </div>
  </div>

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
import { useRoute } from "vue-router";
import { apiGET, apiPOST } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { COUNTRIES, statesFor } from "../composables/useCountryState.js";
import { GSTIN_REGEX } from "../composables/useValidation.js";

const { toast } = useToast();
const route = useRoute();

const form = reactive({
  default_company: "", default_currency: "INR", fiscal_year_start_month: "April",
  invoice_prefix: "INV", gstin: "", gst_state: "", logo_url: "",
  company_address: "", company_city: "", company_country: "India",
  company_state: "", company_pincode: "",
  company_phone: "", company_email: "", company_website: "",
  auto_send_invoice: 0, send_payment_reminders: 0,
  reminder_days_before: 3, reminder_days_after: 7, auto_reconcile: 0,
  pdf_template: "classic", brand_color: "#1a6ef7", company_logo: "",
});
const saving    = ref(false);

const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];
const TABS = [
  { k: "profile",   l: "Company Profile" },
  { k: "invoices",  l: "Invoices" },
  { k: "tax",       l: "Tax" },
  { k: "branding",  l: "Branding & Template" },
  { k: "reminders", l: "Reminders" },
];

// Allow deep-linking to a specific tab, e.g. /settings/company?tab=branding
const validTabKeys = TABS.map(t => t.k);
const activeTab = ref(validTabKeys.includes(route.query.tab) ? route.query.tab : "profile");

const TEMPLATES = [
  { key: "classic", label: "Classic" },
  { key: "modern",  label: "Modern"  },
  { key: "minimal", label: "Minimal" },
];

function resolveSrc(path) {
  if (!path) return "";
  if (path.startsWith("data:") || path.startsWith("http")) return path;
  return (window.location.origin || "") + path;
}

function handleBrandingLogoUpload(e) {
  const file = e.target.files[0];
  if (!file) return;
  const fd = new FormData();
  fd.append("file", file);
  fd.append("doctype", "Books Company");
  fd.append("docname", form.default_company || "");
  fd.append("fieldname", "company_logo");
  fd.append("csrf_token", window.frappe?.csrf_token || "");
  fetch("/api/method/upload_file", { method: "POST", credentials: "same-origin", body: fd })
    .then((r) => r.json())
    .then((d) => { if (d.message?.file_url) { form.company_logo = d.message.file_url; toast("Logo uploaded"); } })
    .catch(() => toast("Upload failed", "error"));
}

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

/* Branding tab */
.sc-branding-templates {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.sc-tmpl-btn {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 16px 20px;
  border: 2px solid #e4e8f0;
  border-radius: 10px;
  background: #f8f9fc;
  cursor: pointer;
  min-width: 90px;
  transition: border-color .15s, background .15s;
}
.sc-tmpl-btn:hover { border-color: #93c5fd; background: #eff6ff; }
.sc-tmpl-btn--active { border-color: #2563eb; background: #eff6ff; }
.sc-tmpl-icon { color: #2563eb; }
.sc-tmpl-label { font-size: 12px; font-weight: 600; color: #374151; }
.sc-tmpl-check {
  position: absolute;
  top: -8px; right: -8px;
  width: 20px; height: 20px; border-radius: 50%;
  background: #2563eb; color: #fff;
  display: flex; align-items: center; justify-content: center;
}
.sc-color-row { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.sc-color-pick {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 14px;
  border: 1px solid #e4e8f0; border-radius: 8px;
  background: #fff;
}
.sc-color-swatch {
  width: 24px; height: 24px; border-radius: 4px;
  border: 1px solid rgba(0,0,0,.1); flex-shrink: 0;
}
.sc-color-hex { font-size: 13px; font-weight: 600; color: #374151; }
.sc-color-input { display: none; }
</style>