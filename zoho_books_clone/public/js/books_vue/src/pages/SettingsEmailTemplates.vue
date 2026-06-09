<template>
<div class="cust-page">
  <div class="cust-toolbar">
    <div style="display:flex;align-items:center;gap:12px">
      <span style="font-size:18px;font-weight:700;color:#1a1a2e">Email Templates</span>
      <span style="background:#F3F0FF;color:#2563eb;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600">{{list.length}}</span>
    </div>
    <button class="nim-btn nim-btn-primary" @click="openAdd"><span v-html="icon('plus',13)" style="vertical-align:-2px;margin-right:4px"/>New Template</button>
  </div>

  <div style="background:linear-gradient(135deg,#E7F5FF,#D0EBFF);border:1px solid #a5d8ff;border-radius:10px;padding:14px 18px;margin-bottom:16px;display:flex;gap:12px;align-items:center">
    <span style="font-size:20px">📧</span>
    <div style="font-size:12.5px;color:#1971C2">Email templates are used for automated payment reminders, invoice emails, and other customer communications. Use <b v-pre>{{variable}}</b> syntax to insert dynamic data.</div>
  </div>

  <div style="margin-bottom:14px;display:flex;gap:10px">
    <div style="position:relative;flex:1;max-width:360px">
      <span style="position:absolute;left:10px;top:50%;transform:translateY(-50%);opacity:.5" v-html="icon('search',14)"></span>
      <input class="nim-input" v-model="search" placeholder="Search templates…" style="padding-left:32px"/>
    </div>
  </div>

  <div v-if="loading" style="padding:60px;text-align:center;color:#868e96">Loading templates…</div>

  <div v-else-if="!filtered.length" style="padding:60px;text-align:center;color:#868e96;background:#fff;border:1px dashed #e4e8f0;border-radius:12px">
    <div style="font-size:36px;margin-bottom:10px">📭</div>
    <div style="font-size:14px;font-weight:600;margin-bottom:4px">No templates yet</div>
    <div style="font-size:12.5px">Create your first email template to automate customer communications</div>
    <button class="nim-btn nim-btn-primary" @click="openAdd" style="margin-top:16px">Create Template</button>
  </div>

  <div v-else style="display:grid;gap:10px">
    <div v-for="t in filtered" :key="t.name" style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:18px 20px;display:flex;align-items:center;gap:14px">
      <div style="width:44px;height:44px;border-radius:10px;background:#F3F0FF;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0">📧</div>
      <div style="flex:1;min-width:0">
        <div style="font-size:13.5px;font-weight:700;color:#1a1a2e">{{t.name}}</div>
        <div style="font-size:12px;color:#868e96;margin-top:2px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{t.subject||'No subject'}}</div>
      </div>
      <div style="display:flex;align-items:center;gap:6px">
        <span v-if="t.use_html" style="background:#E7F5FF;color:#1971C2;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600">HTML</span>
        <span v-else style="background:#F8F9FA;color:#868E96;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:600">Plain</span>
        <button class="nim-btn nim-btn-ghost" @click="openEdit(t)" style="padding:5px 10px;font-size:12px"><span v-html="icon('edit',12)" style="vertical-align:-2px;margin-right:3px"/>Edit</button>
        <button class="nim-btn" @click="delTarget=t.name;showDel=true" style="padding:5px 10px;font-size:12px;color:#c92a2a;border-color:#ffc9c9;background:#fff5f5"><span v-html="icon('trash',12)" style="vertical-align:-2px"/></button>
      </div>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="showDrawer" class="nim-overlay" @click.self="showDrawer=false">
      <div class="nim-dialog" style="width:640px;max-width:95vw">
        <div class="nim-header">
          <span style="font-size:15px;font-weight:700">{{drawerMode==='add'?'New Email Template':'Edit Template'}}</span>
          <button class="nim-btn nim-btn-ghost" @click="showDrawer=false"><span v-html="icon('x',14)"/></button>
        </div>
        <div class="nim-body" style="display:grid;gap:14px">
          <div class="nim-field">
            <label class="nim-label">Template Name <span style="color:#c92a2a">*</span></label>
            <input class="nim-input" v-model="form.name" :readonly="drawerMode==='edit'" placeholder="e.g. Payment Reminder" :style="drawerMode==='edit'?'background:#f8f9fc;color:#868e96':''"/>
            <div style="font-size:11px;color:#868e96;margin-top:3px">Used as a reference key — no spaces</div>
          </div>
          <div class="nim-field">
            <label class="nim-label">Subject <span style="color:#c92a2a">*</span></label>
            <input class="nim-input" v-model="form.subject" :placeholder="subjectPlaceholder"/>
          </div>
          <div style="display:flex;align-items:center;gap:10px;padding:10px 14px;background:#f8f9fc;border-radius:8px;cursor:pointer" @click="form.use_html=form.use_html?0:1">
            <div :style="'width:34px;height:18px;border-radius:9px;transition:.2s;position:relative;background:'+(form.use_html?'#2563eb':'#cbd5e0')">
              <div :style="'width:14px;height:14px;border-radius:50%;background:#fff;position:absolute;top:2px;transition:.2s;left:'+(form.use_html?'18px':'2px')"></div>
            </div>
            <span style="font-size:13px;font-weight:600">HTML format</span>
            <span style="font-size:12px;color:#868e96">(use for rich text with formatting)</span>
          </div>
          <div>
            <div style="font-size:11.5px;font-weight:600;color:#6b7db3;margin-bottom:6px;text-transform:uppercase;letter-spacing:.5px">Quick insert variables</div>
            <div style="display:flex;flex-wrap:wrap;gap:6px">
              <button v-for="v in BUILTIN_VARS" :key="v.key" class="nim-btn nim-btn-ghost" @click="insertVar(v.key)" :title="v.desc" style="padding:3px 8px;font-size:11.5px;">{{v.key}}</button>
            </div>
          </div>
          <div class="nim-field">
            <label class="nim-label">Email Body <span style="color:#c92a2a">*</span></label>
            <textarea class="nim-input" v-model="form.response" rows="10" :placeholder="bodyPlaceholder" style="font-size:12.5px;resize:vertical"></textarea>
          </div>
          <div v-if="form.use_html && form.response">
            <button class="nim-btn nim-btn-ghost" @click="preview=!preview" style="font-size:12px">{{preview?'Hide Preview':'Show HTML Preview'}}</button>
            <div v-if="preview" style="margin-top:10px;padding:16px;border:1px solid #e4e8f0;border-radius:8px;background:#fff;font-size:13px" v-html="form.response"></div>
          </div>
        </div>
        <div class="nim-footer">
          <button class="nim-btn nim-btn-ghost" @click="showDrawer=false">Cancel</button>
          <button class="nim-btn nim-btn-primary" @click="save" :disabled="saving">{{saving?'Saving…':'Save Template'}}</button>
        </div>
      </div>
    </div>

    <div v-if="showDel" class="nim-overlay" @click.self="showDel=false">
      <div class="nim-dialog" style="width:400px">
        <div class="nim-header"><span style="font-weight:700">Delete Template?</span></div>
        <div class="nim-body"><p style="font-size:13.5px;color:#4a5568">Delete "<b>{{delTarget}}</b>"? This cannot be undone and any automation using this template will stop working.</p></div>
        <div class="nim-footer">
          <button class="nim-btn nim-btn-ghost" @click="showDel=false">Cancel</button>
          <button class="nim-btn" style="background:#c92a2a;color:#fff;border-color:#c92a2a" @click="confirmDel">Delete</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiGET, apiPOST } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";

const { toast } = useToast();

const list       = ref([]);
const loading    = ref(false);
const saving     = ref(false);
const showDrawer = ref(false);
const drawerMode = ref("add");
const showDel    = ref(false);
const delTarget  = ref(null);
const search     = ref("");
const form       = reactive({ name: "", subject: "", response: "", use_html: 0 });
const preview    = ref(false);

const BUILTIN_VARS = [
  { key: "{{customer_name}}", desc: "Customer / contact name" },
  { key: "{{invoice_no}}",    desc: "Invoice number" },
  { key: "{{amount}}",        desc: "Total amount" },
  { key: "{{due_date}}",      desc: "Due date" },
  { key: "{{company}}",       desc: "Your company name" },
];

const subjectPlaceholder = "e.g. Invoice {{invoice_no}} is due on {{due_date}}";
const bodyPlaceholder    = "Dear {{customer_name}},\n\nYour invoice {{invoice_no}} of ₹{{amount}} is due on {{due_date}}.";

const filtered = computed(() => {
  const q = search.value.toLowerCase();
  return list.value.filter((t) => !q || (t.name || "").toLowerCase().includes(q) || (t.subject || "").toLowerCase().includes(q));
});

async function load() {
  loading.value = true;
  try {
    list.value = await apiGET("zoho_books_clone.api.admin.get_email_templates") || [];
  } catch (e) { toast("Could not load templates: " + e.message, "error"); }
  loading.value = false;
}

function openAdd() {
  drawerMode.value = "add";
  Object.assign(form, { name: "", subject: "", response: "", use_html: 0 });
  preview.value = false;
  showDrawer.value = true;
}

async function openEdit(t) {
  drawerMode.value = "edit";
  try {
    const d = await apiGET("zoho_books_clone.api.admin.get_email_template", { name: t.name });
    Object.assign(form, { name: d.name, subject: d.subject || "", response: d.response || "", use_html: d.use_html || 0 });
  } catch {
    Object.assign(form, { name: t.name, subject: t.subject || "", response: "", use_html: t.use_html || 0 });
  }
  preview.value = false;
  showDrawer.value = true;
}

async function save() {
  if (!form.name.trim())    return toast("Template name is required", "error");
  if (!form.subject.trim()) return toast("Subject is required", "error");
  saving.value = true;
  try {
    await apiPOST("zoho_books_clone.api.admin.save_email_template", {
      name: form.name, subject: form.subject, response: form.response, use_html: form.use_html,
    });
    toast(drawerMode.value === "add" ? "Template created" : "Template updated");
    showDrawer.value = false;
    load();
  } catch (e) { toast(e.message, "error"); }
  saving.value = false;
}

async function confirmDel() {
  try {
    await apiPOST("zoho_books_clone.api.admin.delete_email_template", { name: delTarget.value });
    toast("Template deleted"); showDel.value = false; load();
  } catch (e) { toast(e.message, "error"); }
}

function insertVar(v) { form.response += v; }

onMounted(load);
</script>
