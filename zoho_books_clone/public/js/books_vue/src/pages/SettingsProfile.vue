<template>
<div class="cust-page">
  <div class="cust-toolbar">
    <span style="font-size:18px;font-weight:700;color:#1a1a2e">My Account</span>
  </div>

  <div style="display:flex;gap:0;border-bottom:2px solid #e4e8f0;margin-bottom:24px">
    <button v-for="t in [{k:'profile',l:'Profile'},{k:'security',l:'Security'}]" :key="t.k"
      @click="activeTab=t.k"
      :style="'padding:10px 20px;border:none;background:none;cursor:pointer;font-size:13px;font-weight:600;'+(activeTab===t.k?'color:#2563eb;border-bottom:2px solid #2563eb;margin-bottom:-2px':'color:#868E96')">
      {{t.l}}
    </button>
  </div>

  <div v-if="activeTab==='profile'" style="max-width:600px">
    <div style="display:flex;align-items:center;gap:20px;margin-bottom:28px;padding:20px;background:#f8f9fc;border-radius:12px;border:1px solid #e4e8f0">
      <div style="width:64px;height:64px;border-radius:50%;background:linear-gradient(135deg,#2563eb,#5e3dc7);display:flex;align-items:center;justify-content:center;color:#fff;font-size:22px;font-weight:700;flex-shrink:0">{{initials}}</div>
      <div>
        <div style="font-size:16px;font-weight:700;color:#1a1a2e">{{profile.first_name}} {{profile.last_name}}</div>
        <div style="font-size:13px;color:#868e96;margin-top:2px">{{profile.email}}</div>
      </div>
    </div>
    <div class="sp-form-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
      <div class="nim-field"><label class="nim-label">First Name</label><input class="nim-input" v-model="profile.first_name"/></div>
      <div class="nim-field"><label class="nim-label">Last Name</label><input class="nim-input" v-model="profile.last_name"/></div>
      <div class="nim-field"><label class="nim-label">Email</label><input class="nim-input" :value="profile.email" disabled style="background:#f8f9fc;color:#868e96"/></div>
      <div class="nim-field"><label class="nim-label">Phone</label><input class="nim-input" v-model="profile.phone"/></div>
      <div class="nim-field"><label class="nim-label">Mobile</label><input class="nim-input" v-model="profile.mobile_no"/></div>
    </div>
    <div style="margin-top:20px">
      <button class="nim-btn nim-btn-primary" @click="saveProfile" :disabled="saving">{{saving?'Saving…':'Save Profile'}}</button>
    </div>
  </div>

  <div v-else style="max-width:480px">
    <div style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:24px;margin-bottom:20px">
      <div style="font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:4px">Change Password</div>
      <div style="font-size:12.5px;color:#868e96;margin-bottom:20px">Use at least 8 characters with a mix of letters and numbers.</div>
      <div style="display:grid;gap:14px">
        <div class="nim-field"><label class="nim-label">Current Password</label><input class="nim-input" type="password" v-model="pwForm.old_password"/></div>
        <div class="nim-field"><label class="nim-label">New Password</label><input class="nim-input" type="password" v-model="pwForm.new_password"/></div>
        <div class="nim-field"><label class="nim-label">Confirm New Password</label><input class="nim-input" type="password" v-model="pwForm.confirm_password"/></div>
      </div>
      <div style="margin-top:18px">
        <button class="nim-btn nim-btn-primary" @click="changePassword" :disabled="savingPw">{{savingPw?'Changing…':'Change Password'}}</button>
      </div>
    </div>
    <div style="background:#f0f4ff;border:1px solid #c5d0fa;border-radius:12px;padding:20px">
      <div style="font-size:14px;font-weight:700;color:#3b4a7a;margin-bottom:8px">Two-Factor Authentication</div>
      <div style="font-size:12.5px;color:#4a5568;margin-bottom:12px">Add an extra layer of security to your account using an authenticator app.</div>
      <span style="background:#fff8f0;color:#e67700;padding:3px 10px;border-radius:20px;font-size:11.5px;font-weight:600;border:1px solid #ffe8a3">Coming Soon (P2)</span>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiGET, apiPOST } from "../api/client.js";
import { useToast } from "../composables/useToast.js";

const { toast } = useToast();

const profile = reactive({ email: "", first_name: "", last_name: "", phone: "", mobile_no: "", user_image: "" });
const pwForm  = reactive({ old_password: "", new_password: "", confirm_password: "" });
const saving    = ref(false);
const savingPw  = ref(false);
const activeTab = ref("profile");

async function loadProfile() {
  try {
    const p = await apiGET("zoho_books_clone.api.admin.get_profile");
    Object.assign(profile, p);
  } catch (e) { toast("Could not load profile", "error"); }
}

async function saveProfile() {
  saving.value = true;
  try {
    const r = await apiPOST("zoho_books_clone.api.admin.update_profile", {
      first_name: profile.first_name, last_name: profile.last_name,
      phone: profile.phone, mobile_no: profile.mobile_no,
    });
    if (r?.full_name) window.frappe.session.user_fullname = r.full_name;
    toast("Profile updated");
  } catch (e) { toast(e.message, "error"); }
  saving.value = false;
}

async function changePassword() {
  if (!pwForm.old_password || !pwForm.new_password)        return toast("All fields required", "error");
  if (pwForm.new_password !== pwForm.confirm_password)     return toast("New passwords do not match", "error");
  if (pwForm.new_password.length < 8)                      return toast("Password must be at least 8 characters", "error");
  savingPw.value = true;
  try {
    await apiPOST("zoho_books_clone.api.admin.change_password", {
      old_password: pwForm.old_password, new_password: pwForm.new_password,
    });
    toast("Password changed successfully");
    Object.assign(pwForm, { old_password: "", new_password: "", confirm_password: "" });
  } catch (e) { toast(e.message, "error"); }
  savingPw.value = false;
}

const initials = computed(() => {
  const base = ((profile.first_name || "") + " " + (profile.last_name || "")).trim() || profile.email || "U";
  return base.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
});

onMounted(loadProfile);
</script>

<style>
@media (max-width: 480px) {
  .sp-form-grid { grid-template-columns: 1fr !important; }
  .cust-page { padding: 12px !important; }
}
</style>
