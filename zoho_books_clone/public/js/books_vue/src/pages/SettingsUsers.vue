<template>
<div class="cust-page">

  <div class="cust-toolbar">
    <div style="display:flex;align-items:center;gap:12px">
      <span style="font-size:18px;font-weight:700;color:#1a1a2e">Team Members</span>
      <span style="background:#F3F0FF;color:#2563eb;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:600">{{users.length}} members</span>
    </div>
    <button v-if="!accessDenied" class="nim-btn nim-btn-primary" @click="openInvite"><span v-html="icon('plus',13)" style="vertical-align:-2px;margin-right:4px"/>Add Member</button>
  </div>

  <div v-if="!accessDenied" style="background:#f0f4ff;border:1px solid #c5d0fa;border-radius:10px;padding:14px 18px;margin-bottom:18px;font-size:13px;color:#3b4a7a;display:flex;gap:12px;align-items:flex-start">
    <span style="font-size:18px;margin-top:-1px">🏢</span>
    <div><strong>Company-scoped access:</strong> Members you add here will only see data belonging to your company. Each member gets their own email &amp; password. New user sign-ups always create a separate, isolated company.</div>
  </div>

  <div v-if="accessDenied" style="background:#fff5f5;border:1px solid #ffd0d0;border-radius:10px;padding:24px;text-align:center;color:#C92A2A;font-size:13.5px;margin-top:0">
    <div style="font-size:22px;margin-bottom:8px">🔒</div>
    <strong>Access Denied</strong><br/>
    <span style="color:#4a5568;font-size:13px">Only company admins can manage team members.</span>
  </div>

  <div v-else class="cust-table-card su-tbl-card" style="margin-top:0">
    <div v-if="loading" style="padding:40px;text-align:center;color:#868E96">Loading members…</div>
    <table v-else class="su-desktop-table" style="width:100%;border-collapse:collapse;font-size:13px">
      <thead><tr style="background:#f8f9fc;border-bottom:2px solid #e4e8f0">
        <th style="padding:10px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6b7db3">Member</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6b7db3">Email</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6b7db3">Role</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6b7db3">Status</th>
        <th style="padding:10px 14px;text-align:left;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6b7db3">Last Login</th>
        <th style="padding:10px 14px;text-align:right;font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.5px;color:#6b7db3">Actions</th>
      </tr></thead>
      <tbody>
        <tr v-for="u in users" :key="u.name" style="border-bottom:1px solid #f0f2f7">
          <td style="padding:12px 14px">
            <div style="display:flex;align-items:center;gap:10px">
              <div v-if="u.user_image" style="width:34px;height:34px;border-radius:50%;overflow:hidden;flex-shrink:0"><img :src="u.user_image" style="width:100%;height:100%;object-fit:cover"/></div>
              <div v-else style="width:34px;height:34px;border-radius:50%;background:linear-gradient(135deg,#2563eb,#5e3dc7);display:flex;align-items:center;justify-content:center;color:#fff;font-size:12px;font-weight:700;flex-shrink:0">{{userInitials(u.full_name||u.name)}}</div>
              <div>
                <div style="font-weight:600;color:#1a1a2e">{{u.full_name||u.name}}</div>
                <div v-if="u.is_owner" style="font-size:10.5px;color:#f59e0b;font-weight:700;margin-top:1px">👑 Owner</div>
              </div>
            </div>
          </td>
          <td style="padding:12px 14px;color:#4a5568">{{u.name}}</td>
          <td style="padding:12px 14px"><span :style="'background:'+(ROLE_BG[displayRole(u)]||'#F8F9FA')+';color:'+(ROLE_COLORS[displayRole(u)]||'#868E96')+';padding:2px 10px;border-radius:20px;font-size:11.5px;font-weight:600'">{{displayRole(u)||'—'}}</span></td>
          <td style="padding:12px 14px"><span :style="u.enabled?'background:#ebfbee;color:#2f9e44;padding:2px 10px;border-radius:20px;font-size:11.5px;font-weight:600':'background:#f8f9fa;color:#868e96;padding:2px 10px;border-radius:20px;font-size:11.5px;font-weight:600'">{{u.enabled?'Active':'Inactive'}}</span></td>
          <td style="padding:12px 14px;color:#868e96;font-size:12px">{{u.last_login?fmtDate(u.last_login):'Never'}}</td>
          <td style="padding:12px 14px;text-align:right">
            <div style="display:flex;gap:6px;justify-content:flex-end">
              <button v-if="!u.is_owner" class="nim-btn nim-btn-ghost" style="padding:4px 10px;font-size:12px" @click="editUser=u;editRole=u.books_role">Change Role</button>
              <button v-if="!u.is_owner && !u.is_company_admin" class="nim-btn nim-btn-ghost" style="padding:4px 10px;font-size:12px" @click="openPerms(u)">Module Access</button>
              <button v-if="!u.is_owner" class="nim-btn nim-btn-ghost" style="padding:4px 10px;font-size:12px" @click="toggleActive(u)">{{u.enabled?'Deactivate':'Activate'}}</button>
              <button v-if="!u.is_owner" class="nim-btn nim-btn-ghost" style="padding:4px 10px;font-size:12px;color:#C92A2A;border-color:#ffd0d0" @click="showRemoveConfirm=u">Remove</button>
            </div>
          </td>
        </tr>
        <tr v-if="!users.length"><td colspan="6" style="padding:40px;text-align:center;color:#868e96">No members yet — add your first team member above</td></tr>
      </tbody>
    </table>

    <!-- Mobile cards (shown at ≤768px) -->
    <div v-if="!loading" class="su-mobile-cards">
      <div v-if="!users.length" class="su-mc-empty">
        <div style="font-size:32px;margin-bottom:8px">👥</div>
        <div>No members yet</div>
      </div>
      <template v-else>
        <div v-for="u in users" :key="u.name" class="su-mobile-card">
          <div class="su-mc-top">
            <span class="su-mc-name">{{ u.full_name||u.name }}</span>
            <span :style="'background:'+(u.enabled?'#ebfbee':'#f8f9fa')+';color:'+(u.enabled?'#2f9e44':'#868e96')+';padding:2px 8px;border-radius:20px;font-size:11.5px;font-weight:600'">{{ u.enabled?'Active':'Inactive' }}</span>
          </div>
          <div class="su-mc-mid">{{ u.name }}</div>
          <div class="su-mc-meta">
            <span :style="'background:'+(ROLE_BG[displayRole(u)]||'#F8F9FA')+';color:'+(ROLE_COLORS[displayRole(u)]||'#868E96')+';padding:1px 7px;border-radius:20px;font-size:11px;font-weight:600'">{{ displayRole(u)||'—' }}</span>
            <span v-if="!u.is_owner" style="display:flex;gap:4px">
              <button class="nim-btn nim-btn-ghost" style="padding:3px 8px;font-size:11.5px" @click.stop="editUser=u;editRole=u.books_role">Role</button>
              <button class="nim-btn nim-btn-ghost" style="padding:3px 8px;font-size:11.5px;color:#C92A2A;border-color:#ffd0d0" @click.stop="showRemoveConfirm=u">Remove</button>
            </span>
          </div>
        </div>
      </template>
    </div>
  </div><!-- end v-else -->

  <Teleport to="body">
    <div v-if="showInvite" class="nim-overlay" @click.self="showInvite=false">
      <div class="nim-dialog" style="width:560px">
        <div class="nim-header">
          <div>
            <span style="font-weight:700;color:#fff;font-size:15px">Add Team Member</span>
            <div style="font-size:11.5px;color:#868e96;margin-top:2px">
              Step {{stepIndex}} of {{totalSteps}} —
              {{step===1?'Assign a Role':(step===2?'Module Access':'Set Credentials')}}
            </div>
          </div>
          <button class="nim-close" @click="showInvite=false">✕</button>
        </div>
        <div style="display:flex;gap:0;padding:0 24px;margin-bottom:-1px">
          <div v-for="s in stepsForRole" :key="s" :style="'flex:1;height:3px;border-radius:2px;margin:0 2px;background:'+(step>=s?'#2563eb':'#e4e8f0')"></div>
        </div>

        <!-- Step 1: Role selection -->
        <div v-if="step===1" class="nim-body" style="display:grid;gap:12px">
          <div style="font-size:13px;color:#4a5568">Select the role this member will have in your company:</div>
          <div v-for="r in ROLES" :key="r" @click="selectRole(r)"
            :style="'padding:14px 16px;border-radius:10px;cursor:pointer;display:flex;align-items:center;gap:14px;transition:all .15s;'+(inviteForm.role===r?'border:2px solid #2563eb;background:#f5f0ff':'border:2px solid #e4e8f0;background:#fff')">
            <div :style="'width:10px;height:10px;border-radius:50%;flex-shrink:0;background:'+ROLE_COLORS[r]"></div>
            <div style="flex:1">
              <div style="font-weight:700;font-size:13px;color:#1a1a2e">{{r}}</div>
              <div style="font-size:12px;color:#868e96;margin-top:2px">{{ROLE_DESC[r]}}</div>
            </div>
            <div v-if="inviteForm.role===r" style="color:#2563eb;font-size:16px">✓</div>
          </div>
          <div v-if="inviteError" style="background:#fff5f5;border:1px solid #ffd0d0;border-radius:8px;padding:10px 14px;color:#C92A2A;font-size:12.5px">{{inviteError}}</div>
        </div>

        <!-- Step 2: Module access -->
        <div v-if="step===2" class="nim-body" style="display:grid;gap:14px">
          <div style="background:#f5f0ff;border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:10px">
            <span :style="'background:'+ROLE_COLORS[inviteForm.role]+';color:#fff;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700'">{{inviteForm.role}}</span>
            <span style="font-size:12.5px;color:#3b4a7a">Selected — <a href="#" @click.prevent="step=1" style="color:#2563eb;text-decoration:none">Change</a></span>
          </div>
          <div style="font-size:13px;color:#4a5568">
            {{ inviteForm.role==='Custom' ? 'Pick exactly which modules this member can access. Nothing is granted by default.' : 'Choose which modules this member can access. Defaults are based on the selected role.' }}
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;background:#f8f9fc;border-radius:8px;padding:14px">
            <label v-for="m in MODULES" :key="m.key" style="display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:6px;cursor:pointer;font-size:13px;color:#3b4a7a">
              <input type="checkbox" :checked="inviteForm.modules[m.key]" @change="inviteForm.modules[m.key] = $event.target.checked" style="width:14px;height:14px;cursor:pointer"/>
              <span>{{m.label}}</span>
            </label>
          </div>
        </div>

        <!-- Step 3: Credentials -->
        <div v-if="step===3" class="nim-body" style="display:grid;gap:14px">
          <div style="background:#f5f0ff;border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:10px">
            <span :style="'background:'+ROLE_COLORS[inviteForm.role]+';color:#fff;padding:2px 10px;border-radius:20px;font-size:12px;font-weight:700'">{{inviteForm.role}}</span>
            <span style="font-size:12.5px;color:#3b4a7a">Selected — <a href="#" @click.prevent="step=1" style="color:#2563eb;text-decoration:none">Change</a></span>
          </div>
          <div class="nim-field"><label class="nim-label">Email Address *</label><input class="nim-input" v-model="inviteForm.email" type="email" placeholder="member@company.com"/></div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div class="nim-field"><label class="nim-label">First Name *</label><input class="nim-input" v-model="inviteForm.first_name" placeholder="First"/></div>
            <div class="nim-field"><label class="nim-label">Last Name</label><input class="nim-input" v-model="inviteForm.last_name" placeholder="Last"/></div>
          </div>
          <div style="background:#f0f9ff;border:1px solid #c5d9fa;border-radius:8px;padding:12px 14px;font-size:12.5px;color:#1971C2;line-height:1.5">
            <strong>📧 Invite by email</strong> — Books will email <em>{{inviteForm.email||'this user'}}</em> a temporary password and a sign-in link. They should change it on first login.
          </div>
          <div v-if="inviteError" style="background:#fff5f5;border:1px solid #ffd0d0;border-radius:8px;padding:10px 14px;color:#C92A2A;font-size:12.5px">{{inviteError}}</div>
        </div>

        <div class="nim-footer">
          <button class="nim-btn" @click="step===1?showInvite=false:prevStep()">{{step===1?'Cancel':'Back'}}</button>
          <button v-if="step!==3" class="nim-btn nim-btn-primary" @click="nextStep">{{nextLabel}}</button>
          <button v-else class="nim-btn nim-btn-primary" @click="sendInvite" :disabled="saving">{{saving?'Sending…':'Send Invite'}}</button>
        </div>
      </div>
    </div>

    <div v-if="permsUser" class="nim-overlay" @click.self="permsUser=null">
      <div class="nim-dialog" style="width:520px">
        <div class="nim-header"><span style="font-weight:700">Module Access — {{permsUser.full_name||permsUser.name}}</span><button class="nim-close" @click="permsUser=null">✕</button></div>
        <div class="nim-body" style="display:grid;gap:14px">
          <div style="font-size:13px;color:#4a5568">Toggle which modules this member can access. Changes apply immediately on save.</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;background:#f8f9fc;border-radius:8px;padding:14px">
            <label v-for="m in MODULES" :key="m.key" style="display:flex;align-items:center;gap:8px;padding:6px 8px;border-radius:6px;cursor:pointer;font-size:13px;color:#3b4a7a">
              <input type="checkbox" :checked="permsDraft[m.key]" @change="permsDraft[m.key] = $event.target.checked" style="width:14px;height:14px;cursor:pointer"/>
              <span>{{m.label}}</span>
            </label>
          </div>
        </div>
        <div class="nim-footer">
          <button class="nim-btn" @click="permsUser=null">Cancel</button>
          <button class="nim-btn nim-btn-primary" @click="savePerms" :disabled="permsSaving">{{permsSaving?'Saving…':'Save Access'}}</button>
        </div>
      </div>
    </div>

    <div v-if="editUser" class="nim-overlay" @click.self="editUser=null">
      <div class="nim-dialog" style="width:420px">
        <div class="nim-header"><span style="font-weight:700">Change Role — {{editUser.full_name||editUser.name}}</span><button class="nim-close" @click="editUser=null">✕</button></div>
        <div class="nim-body" style="display:grid;gap:10px">
          <div v-for="r in CHANGEABLE_ROLES" :key="r" @click="editRole=r"
            :style="'padding:12px 14px;border-radius:8px;cursor:pointer;display:flex;align-items:center;gap:12px;transition:all .15s;'+(editRole===r?'border:2px solid #2563eb;background:#f5f0ff':'border:2px solid #e4e8f0;background:#fff')">
            <div :style="'width:8px;height:8px;border-radius:50%;background:'+ROLE_COLORS[r]"></div>
            <div style="flex:1"><div style="font-weight:600;font-size:13px">{{r}}</div><div style="font-size:11.5px;color:#868e96">{{ROLE_DESC[r]}}</div></div>
            <div v-if="editRole===r" style="color:#2563eb">✓</div>
          </div>
        </div>
        <div class="nim-footer"><button class="nim-btn" @click="editUser=null">Cancel</button><button class="nim-btn nim-btn-primary" @click="changeRole">Save Role</button></div>
      </div>
    </div>

    <div v-if="showRemoveConfirm" class="nim-overlay" @click.self="showRemoveConfirm=null">
      <div class="nim-dialog" style="width:400px">
        <div class="nim-header"><span style="font-weight:700;color:#C92A2A">Remove Member</span><button class="nim-close" @click="showRemoveConfirm=null">✕</button></div>
        <div class="nim-body"><p style="color:#4a5568;font-size:13.5px;line-height:1.6">Are you sure you want to remove <strong>{{showRemoveConfirm.full_name||showRemoveConfirm.name}}</strong>? Their account will be deactivated and they will lose access to company data.</p></div>
        <div class="nim-footer"><button class="nim-btn" @click="showRemoveConfirm=null">Cancel</button><button class="nim-btn" style="background:#C92A2A;color:#fff;border-color:#C92A2A" @click="confirmRemove(showRemoveConfirm)">Remove Member</button></div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiGET, apiPOST } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { fmtDate } from "../utils/format.js";
import { icon } from "../utils/icons.js";

const { toast } = useToast();

const MODULES = [
  { key: "invoices",  label: "Sales Invoices" },
  { key: "bills",     label: "Bills & Purchases" },
  { key: "payments",  label: "Payments" },
  { key: "banking",   label: "Banking" },
  { key: "inventory", label: "Inventory" },
  { key: "accounts",  label: "Chart of Accounts" },
  { key: "reports",   label: "Reports" },
  { key: "customers", label: "Customers & Suppliers" },
  { key: "taxes",     label: "Taxes & GST" },
  { key: "admin",     label: "Admin / Settings" },
];

// "Custom" sits at the bottom — same shape as a built-in role for picker UX,
// but on save it maps to "Books Viewer" (least Frappe privilege) with whatever
// module flags the admin actually ticked. No backend change required.
const ROLES = ["Books Admin", "Accountant", "Books Manager", "Books Viewer", "Custom"];
const CHANGEABLE_ROLES = ["Books Admin", "Accountant", "Books Manager", "Books Viewer"];

const ROLE_COLORS = {
  "Books Admin":   "#2563eb",
  "Accountant":    "#1971C2",
  "Books Manager": "#2F9E44",
  "Books Viewer":  "#868E96",
  "Custom":        "#E67700",
};
const ROLE_BG = {
  "Books Admin":   "#F3F0FF",
  "Accountant":    "#E7F5FF",
  "Books Manager": "#EBFBEE",
  "Books Viewer":  "#F8F9FA",
  "Custom":        "#FFF3BF",
};
const ROLE_DESC = {
  "Books Admin":   "Full access — manage users, settings, all data",
  "Accountant":    "Create & edit invoices, bills, payments, reports",
  "Books Manager": "Create & edit transactions; no admin functions",
  "Books Viewer":  "Read-only access to all records",
  "Custom":        "Pick exact module access — nothing granted by default",
};

const DEFAULT_MODULES_BY_ROLE = {
  "Books Admin":   Object.fromEntries(MODULES.map((m) => [m.key, true])),
  "Books Manager": { invoices: true, bills: true, payments: true, banking: true, inventory: true, accounts: true, reports: true, customers: true, taxes: false, admin: false },
  "Accountant":    { invoices: true, bills: true, payments: true, banking: true, inventory: false, accounts: true, reports: true, customers: true, taxes: true, admin: false },
  "Books Viewer":  { invoices: true, bills: true, payments: true, banking: false, inventory: false, accounts: false, reports: true, customers: true, taxes: false, admin: false },
  "Custom":        Object.fromEntries(MODULES.map((m) => [m.key, false])),  // everything off until admin ticks it
};
function defaultModulesFor(role) { return { ...(DEFAULT_MODULES_BY_ROLE[role] || {}) }; }

const users    = ref([]);
const loading  = ref(false);
const saving   = ref(false);
const accessDenied = ref(false);
const showInvite = ref(false);
const step     = ref(1);
const editUser = ref(null);
const editRole = ref("");
const showRemoveConfirm = ref(null);

const inviteForm = reactive({
  email: "", first_name: "", last_name: "",
  role: "Books Viewer", password: "", confirm_password: "",
  modules: defaultModulesFor("Books Viewer"),
});
const inviteError = ref("");

const permsUser = ref(null);
const permsDraft = reactive(defaultModulesFor("Books Viewer"));
const permsSaving = ref(false);

// Books Admin role gives full perms automatically, so the module-access step
// is skipped. Custom and the others all show all three steps.
const stepsForRole = computed(() => inviteForm.role === "Books Admin" ? [1, 3] : [1, 2, 3]);
const totalSteps   = computed(() => stepsForRole.value.length);
const stepIndex    = computed(() => stepsForRole.value.indexOf(step.value) + 1);
const nextLabel    = computed(() => {
  if (step.value === 1) return inviteForm.role === "Books Admin" ? "Next: Set Credentials →" : "Next: Module Access →";
  return "Next: Set Credentials →";
});

// On the table, show "Custom" for any Books Viewer whose module flags don't
// match the Books Viewer defaults — that's the signature of a Custom invite.
function displayRole(u) {
  if (u.books_role !== "Books Viewer") return u.books_role;
  if (!u.modules) return u.books_role;
  const def = DEFAULT_MODULES_BY_ROLE["Books Viewer"];
  for (const m of MODULES) if (!!u.modules[m.key] !== !!def[m.key]) return "Custom";
  return u.books_role;
}

async function load() {
  loading.value = true;
  accessDenied.value = false;
  try {
    users.value = await apiGET("zoho_books_clone.api.admin.get_company_members") || [];
  } catch (e) {
    const msg = e.message || String(e);
    if (msg.includes("permission") || msg.includes("admin") || msg.includes("linked")) {
      accessDenied.value = true;
    } else {
      toast("Could not load members: " + msg, "error");
    }
  }
  loading.value = false;
}

function openInvite() {
  Object.assign(inviteForm, {
    email: "", first_name: "", last_name: "",
    role: "Books Viewer", password: "", confirm_password: "",
    modules: defaultModulesFor("Books Viewer"),
  });
  inviteError.value = "";
  step.value = 1;
  showInvite.value = true;
}

function selectRole(role) {
  inviteForm.role = role;
  inviteForm.modules = defaultModulesFor(role);
}

function nextStep() {
  inviteError.value = "";
  if (step.value === 1) {
    if (!inviteForm.role) { inviteError.value = "Please select a role."; return; }
    step.value = inviteForm.role === "Books Admin" ? 3 : 2;
    return;
  }
  if (step.value === 2) { step.value = 3; return; }
}

function prevStep() {
  if (step.value === 3) { step.value = inviteForm.role === "Books Admin" ? 1 : 2; return; }
  if (step.value === 2) { step.value = 1; return; }
}

async function sendInvite() {
  inviteError.value = "";
  if (!inviteForm.email || !inviteForm.first_name) { inviteError.value = "Email and first name are required."; return; }
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(inviteForm.email)) { inviteError.value = "Please enter a valid email address."; return; }
  if (inviteForm.password) {
    if (inviteForm.password.length < 8) { inviteError.value = "Password must be at least 8 characters."; return; }
    if (inviteForm.password !== inviteForm.confirm_password) { inviteError.value = "Passwords do not match."; return; }
  }
  saving.value = true;
  try {
    const modulePayload = Object.fromEntries(MODULES.map((m) => [m.key, inviteForm.modules[m.key] ? 1 : 0]));
    // "Custom" is a UI affordance only — the server gets "Books Viewer" + the user's hand-picked module flags.
    const serverRole = inviteForm.role === "Custom" ? "Books Viewer" : inviteForm.role;
    await apiPOST("zoho_books_clone.api.admin.invite_member", {
      email: inviteForm.email, first_name: inviteForm.first_name,
      last_name: inviteForm.last_name, role: serverRole,
      password: inviteForm.password || "",
      modules: modulePayload,
    });
    toast("Invite sent — " + inviteForm.email + " will receive an email with sign-in details.");
    showInvite.value = false;
    load();
  } catch (e) { inviteError.value = e.message || "Failed to add member."; }
  saving.value = false;
}

function openPerms(u) {
  if (u.is_company_admin) { toast("Admins always have full module access.", "info"); return; }
  permsUser.value = u;
  const current = u.modules || defaultModulesFor(u.books_role);
  for (const m of MODULES) permsDraft[m.key] = !!current[m.key];
}

async function savePerms() {
  if (!permsUser.value) return;
  permsSaving.value = true;
  try {
    const modulePayload = Object.fromEntries(MODULES.map((m) => [m.key, permsDraft[m.key] ? 1 : 0]));
    await apiPOST("zoho_books_clone.api.admin.set_user_permissions", {
      user: permsUser.value.email || permsUser.value.name,
      modules: modulePayload,
    });
    toast("Module access updated");
    permsUser.value = null;
    load();
  } catch (e) { toast(e.message || "Failed to update access", "error"); }
  permsSaving.value = false;
}

async function changeRole() {
  try {
    await apiPOST("zoho_books_clone.api.admin.update_user_role", { user: editUser.value.name, role: editRole.value });
    toast("Role updated"); editUser.value = null; load();
  } catch (e) { toast(e.message, "error"); }
}

async function toggleActive(u) {
  try {
    await apiPOST("zoho_books_clone.api.admin.toggle_user_active", { user: u.name, enabled: u.enabled ? 0 : 1 });
    toast(u.enabled ? "Member deactivated" : "Member activated"); load();
  } catch (e) { toast(e.message, "error"); }
}

async function confirmRemove(u) {
  try {
    await apiPOST("zoho_books_clone.api.admin.remove_member", { user_email: u.name });
    toast("Member removed"); showRemoveConfirm.value = null; load();
  } catch (e) { toast(e.message, "error"); }
}

function userInitials(name) {
  return (name || "?").split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
}

onMounted(load);
</script>

<style>
.su-mobile-cards { display: none; }
.su-desktop-table { display: table; }

@media (max-width: 768px) {
  .su-desktop-table { display: none !important; }
  .su-mobile-cards { display: flex; flex-direction: column; gap: 0; background: #f8fafc; }
  .su-mobile-card { background: #fff; border-bottom: 1px solid #e5e7eb; padding: 12px 14px; }
  .su-mc-top { display: flex; align-items: center; justify-content: space-between; margin-bottom: 4px; }
  .su-mc-name { font-size: 13.5px; font-weight: 700; color: #1a1a2e; }
  .su-mc-mid { font-size: 12px; color: #6b7280; margin-bottom: 6px; }
  .su-mc-meta { display: flex; align-items: center; justify-content: space-between; font-size: 12px; color: #868e96; }
  .su-mc-empty { text-align: center; padding: 32px 16px; color: #868e96; font-size: 13px; }
}
@media (max-width: 480px) {
  .cust-page { padding: 12px !important; }
}
</style>
