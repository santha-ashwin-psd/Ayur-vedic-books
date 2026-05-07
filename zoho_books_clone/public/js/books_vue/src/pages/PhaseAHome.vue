<template>
  <div class="bv-phase-a">
    <h1>Phase A — Foundation Online</h1>
    <p class="bv-phase-a-lede">
      The new Vue/Vite shell is mounted. Cross-cutting infra (API client, session bootstrap,
      permissions, toast/modal/drawer/confirm primitives, layout shell, AI panel,
      notifications, tutorial overlay) is wired up. No user-facing modules are routed
      through this bundle yet — the legacy SPA still owns every route.
    </p>

    <div class="bv-phase-a-grid">
      <div class="bv-phase-a-card">
        <div class="bv-phase-a-card-label">Signed in as</div>
        <div class="bv-phase-a-card-value">{{ session.fullname || session.user || "—" }}</div>
        <div class="bv-phase-a-card-sub">{{ session.permissions.books_role || "No role" }}</div>
      </div>
      <div class="bv-phase-a-card">
        <div class="bv-phase-a-card-label">Active company</div>
        <div class="bv-phase-a-card-value">{{ session.company || "—" }}</div>
      </div>
      <div class="bv-phase-a-card">
        <div class="bv-phase-a-card-label">Module access</div>
        <div class="bv-phase-a-card-value">{{ moduleSummary }}</div>
      </div>
    </div>

    <p class="bv-phase-a-next">
      Next phase: pilot port of <code>/customers</code> from <code>public/books.js</code>
      to <code>src/pages/Customers.vue</code>.
    </p>
  </div>
</template>

<script setup>
import { computed } from "vue";
import { session } from "../api/session.js";

const moduleSummary = computed(() => {
  const flags = session.permissions || {};
  const enabled = Object.keys(flags)
    .filter((k) => k.startsWith("mod_") && flags[k])
    .map((k) => k.replace("mod_", ""));
  if (!enabled.length) return "No modules enabled";
  return enabled.join(", ");
});
</script>

<style>
.bv-phase-a { padding: 32px; max-width: 880px; }
.bv-phase-a h1 { font-size: 22px; font-weight: 700; margin-bottom: 12px; color: #111827; }
.bv-phase-a-lede { font-size: 13px; line-height: 1.6; color: #4b5563; margin-bottom: 28px; }
.bv-phase-a-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; margin-bottom: 28px; }
.bv-phase-a-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 12px;
  padding: 16px; box-shadow: 0 1px 2px rgba(0,0,0,.04);
}
.bv-phase-a-card-label { font-size: 11px; text-transform: uppercase; letter-spacing: .04em; color: #6b7280; margin-bottom: 6px; }
.bv-phase-a-card-value { font-size: 16px; font-weight: 600; color: #111827; word-break: break-word; }
.bv-phase-a-card-sub   { font-size: 12px; color: #6b7280; margin-top: 4px; }
.bv-phase-a-next { font-size: 12px; color: #6b7280; }
.bv-phase-a-next code { font-family: 'JetBrains Mono', monospace; background: #f3f4f6; padding: 1px 5px; border-radius: 3px; font-size: 11px; }
</style>
