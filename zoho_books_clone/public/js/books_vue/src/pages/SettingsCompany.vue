<template>
<div class="cust-page">
  <div class="cust-toolbar">
    <span style="font-size:18px;font-weight:700;color:#1a1a2e">Company Settings</span>
    <button class="nim-btn nim-btn-primary" @click="save" :disabled="saving">{{saving?'Saving…':'Save Changes'}}</button>
  </div>

  <div style="display:flex;gap:0;border-bottom:2px solid #e4e8f0;margin-bottom:24px">
    <button v-for="t in [{k:'profile',l:'Company Profile'},{k:'invoices',l:'Invoices'},{k:'tax',l:'Tax'},{k:'reminders',l:'Reminders'}]" :key="t.k"
      @click="activeTab=t.k"
      :style="'padding:10px 20px;border:none;background:none;cursor:pointer;font-size:13px;font-weight:600;'+(activeTab===t.k?'color:#2563eb;border-bottom:2px solid #2563eb;margin-bottom:-2px':'color:#868E96')">
      {{t.l}}
    </button>
  </div>

  <div v-if="activeTab==='profile'" style="max-width:680px;display:grid;gap:20px">
    <div style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:24px">
      <div style="font-size:14px;font-weight:700;color:#1a1a2e;margin-bottom:16px">Company Logo</div>
      <div style="display:flex;align-items:center;gap:20px">
        <div style="width:80px;height:80px;border:2px dashed #c5d0fa;border-radius:10px;display:flex;align-items:center;justify-content:center;overflow:hidden;background:#f8f9fc">
          <img v-if="form.logo_url" :src="form.logo_url" style="width:100%;height:100%;object-fit:contain"/>
          <span v-else style="font-size:28px">🏢</span>
        </div>
        <div>
          <label style="cursor:pointer" class="nim-btn nim-btn-ghost">
            Upload Logo<input type="file" accept="image/*" style="display:none" @change="handleLogoUpload"/>
          </label>
          <div style="font-size:11px;color:#868e96;margin-top:6px">PNG, JPG up to 2MB. Appears on PDF invoices.</div>
          <div v-if="form.logo_url" style="margin-top:4px"><button class="nim-btn" style="font-size:11px;padding:2px 8px" @click="form.logo_url=''">Remove</button></div>
        </div>
      </div>
    </div>

    <div style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:24px">
      <div style="font-size:14px;font-weight:700;color:#1a1a2e;margin-bottom:16px">Company Information</div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
        <div class="nim-field" style="grid-column:1/-1"><label class="nim-label">Company Name</label><input class="nim-input" v-model="form.default_company"/></div>
        <div class="nim-field"><label class="nim-label">Phone</label><input class="nim-input" v-model="form.company_phone"/></div>
        <div class="nim-field"><label class="nim-label">Email</label><input class="nim-input" v-model="form.company_email"/></div>
        <div class="nim-field" style="grid-column:1/-1"><label class="nim-label">Website</label><input class="nim-input" v-model="form.company_website"/></div>
        <div class="nim-field" style="grid-column:1/-1"><label class="nim-label">Address</label><input class="nim-input" v-model="form.company_address"/></div>
        <div class="nim-field"><label class="nim-label">City</label><input class="nim-input" v-model="form.company_city"/></div>
        <div class="nim-field"><label class="nim-label">State</label><input class="nim-input" v-model="form.company_state"/></div>
        <div class="nim-field"><label class="nim-label">Pincode</label><input class="nim-input" v-model="form.company_pincode"/></div>
        <div class="nim-field"><label class="nim-label">Currency</label><input class="nim-input" v-model="form.default_currency"/></div>
        <div class="nim-field"><label class="nim-label">Fiscal Year Start</label>
          <select class="nim-input" v-model="form.fiscal_year_start_month">
            <option v-for="m in MONTHS" :key="m" :value="m">{{m}}</option>
          </select>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="activeTab==='invoices'" style="max-width:560px;display:grid;gap:16px">
    <div style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:24px">
      <div style="font-size:14px;font-weight:700;color:#1a1a2e;margin-bottom:16px">Invoice Settings</div>
      <div style="display:grid;gap:14px">
        <div class="nim-field"><label class="nim-label">Invoice Number Prefix</label><input class="nim-input" v-model="form.invoice_prefix" placeholder="INV"/></div>
        <div style="display:flex;align-items:center;gap:10px;padding:12px;background:#f8f9fc;border-radius:8px;cursor:pointer" @click="form.auto_send_invoice=form.auto_send_invoice?0:1">
          <div :style="'width:36px;height:20px;border-radius:10px;transition:.2s;position:relative;background:'+(form.auto_send_invoice?'#2563eb':'#cbd5e0')">
            <div :style="'width:16px;height:16px;border-radius:50%;background:#fff;position:absolute;top:2px;transition:.2s;left:'+(form.auto_send_invoice?'18px':'2px')"></div>
          </div>
          <div><div style="font-size:13px;font-weight:600">Auto-Send Invoice on Submit</div><div style="font-size:11.5px;color:#868e96">Email invoice to customer automatically when submitted</div></div>
        </div>
      </div>
    </div>
  </div>

  <div v-else-if="activeTab==='tax'" style="max-width:560px">
    <div style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:24px">
      <div style="font-size:14px;font-weight:700;color:#1a1a2e;margin-bottom:16px">Tax Configuration</div>
      <div style="display:grid;gap:14px">
        <div class="nim-field"><label class="nim-label">GSTIN</label><input class="nim-input" v-model="form.gstin" placeholder="22AAAAA0000A1Z5"/></div>
        <div class="nim-field"><label class="nim-label">GST State</label><input class="nim-input" v-model="form.gst_state" placeholder="Maharashtra"/></div>
      </div>
    </div>
  </div>

  <div v-else style="max-width:560px">
    <div style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:24px">
      <div style="font-size:14px;font-weight:700;color:#1a1a2e;margin-bottom:16px">Payment Reminders</div>
      <div style="display:grid;gap:14px">
        <div style="display:flex;align-items:center;gap:10px;padding:12px;background:#f8f9fc;border-radius:8px;cursor:pointer" @click="form.send_payment_reminders=form.send_payment_reminders?0:1">
          <div :style="'width:36px;height:20px;border-radius:10px;transition:.2s;position:relative;background:'+(form.send_payment_reminders?'#2563eb':'#cbd5e0')">
            <div :style="'width:16px;height:16px;border-radius:50%;background:#fff;position:absolute;top:2px;transition:.2s;left:'+(form.send_payment_reminders?'18px':'2px')"></div>
          </div>
          <div><div style="font-size:13px;font-weight:600">Send Overdue Payment Reminders</div><div style="font-size:11.5px;color:#868e96">Automatically email overdue invoice reminders</div></div>
        </div>
        <div v-if="form.send_payment_reminders" style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
          <div class="nim-field"><label class="nim-label">Remind N days before due</label><input class="nim-input" type="number" v-model="form.reminder_days_before" min="0"/></div>
          <div class="nim-field"><label class="nim-label">Remind N days after due</label><input class="nim-input" type="number" v-model="form.reminder_days_after" min="1"/></div>
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, reactive, onMounted } from "vue";
import { apiGET, apiPOST } from "../api/client.js";
import { useToast } from "../composables/useToast.js";

const { toast } = useToast();

const form = reactive({
  default_company: "", default_currency: "INR", fiscal_year_start_month: "April",
  invoice_prefix: "INV", gstin: "", gst_state: "", logo_url: "",
  company_address: "", company_city: "", company_state: "", company_pincode: "",
  company_phone: "", company_email: "", company_website: "",
  auto_send_invoice: 0, send_payment_reminders: 0,
  reminder_days_before: 3, reminder_days_after: 7, auto_reconcile: 0,
});
const saving    = ref(false);
const activeTab = ref("profile");

const MONTHS = ["January","February","March","April","May","June","July","August","September","October","November","December"];

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
