<template>
  <aside class="bv-sidebar" :class="{ 'bv-sidebar-collapsed': collapsed }">
    <div class="bv-sidebar-brand">
      <span class="bv-sidebar-brand-mark">B</span>
      <span v-if="!collapsed" class="bv-sidebar-brand-text">Books</span>
      <button class="bv-sidebar-collapse" @click.stop="$emit('toggle')" style="position:relative;bottom:auto;right:auto;margin-left:auto">
        <IconSvg :name="collapsed ? 'chevR' : 'chevL'" :size="14" />
      </button>
    </div>

    <nav class="bv-sidebar-nav">
      <template v-for="(item, i) in visibleNav" :key="i">
        <div v-if="item.section" class="bv-sidebar-section">
          <span v-if="!collapsed">{{ item.section }}</span>
        </div>
        <a
          v-else
          :href="`#${item.path}`"
          class="bv-sidebar-item"
          :class="{ 'bv-sidebar-item-active': isActive(item.path) }"
          :title="collapsed ? item.label : ''"
          @click.prevent="goTo(item)"
        >
          <span class="bv-sidebar-icon"><IconSvg :name="item.icon" :size="16" /></span>
          <span v-if="!collapsed" class="bv-sidebar-label">{{ item.label }}</span>
        </a>
      </template>
    </nav>

    <!-- User footer -->
    <div class="bv-sidebar-user" @click="goTo({ path: '/settings/profile' })">
      <div class="bv-sidebar-avatar">{{ initials }}</div>
      <div v-if="!collapsed" class="bv-sidebar-user-info">
        <div class="bv-sidebar-user-name">{{ session.fullname || session.user }}</div>
        <div class="bv-sidebar-user-role">{{ role || 'Member' }}</div>
      </div>
    </div>
    <button class="bv-sidebar-logout" @click.stop="doLogout" :title="collapsed ? 'Sign out' : ''">
      <IconSvg name="logout" :size="15" />
      <span v-if="!collapsed">Logout</span>
    </button>

  </aside>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import IconSvg from "../components/IconSvg.vue";
import { NAV } from "./nav.js";
import { usePermissions } from "../composables/usePermissions.js";
import { session } from "../api/session.js";

defineProps({ collapsed: { type: Boolean, default: false } });
defineEmits(["toggle"]);

const route  = useRoute();
const router = useRouter();
const { can, role } = usePermissions();

const initials = computed(() => {
  const n = (session.fullname || session.user || "?").trim();
  const parts = n.split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] || "") + (parts[1]?.[0] || "")).toUpperCase() || "?";
});

async function doLogout() {
  try { await fetch("/api/method/logout", { method: "POST", credentials: "same-origin" }); } catch {}
  window.location.href = "/login";
}

// Hold the latest section header until we see an item that passes the
// permission filter; then flush it once. Sections with no visible
// children never appear.
const visibleNav = computed(() => {
  const out = [];
  let pendingSection = null;
  for (const item of NAV) {
    if (item.section) { pendingSection = item; continue; }
    if (!can(item.module)) continue;
    if (pendingSection) { out.push(pendingSection); pendingSection = null; }
    out.push(item);
  }
  return out;
});

function isActive(path) {
  if (path === "/") return route.path === "/";
  return route.path === path || route.path.startsWith(path + "/");
}

function goTo(item) {
  router.push(item.path);
}
</script>
