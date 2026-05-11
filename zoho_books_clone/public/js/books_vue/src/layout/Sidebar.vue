<template>
  <aside class="bv-sidebar" :class="{ 'bv-sidebar-collapsed': collapsed }">
    <div class="bv-sidebar-brand">
      <span class="bv-sidebar-brand-mark">B</span>
      <span v-if="!collapsed" class="bv-sidebar-brand-text">Books</span>
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

    <button class="bv-sidebar-collapse" @click="$emit('toggle')">
      <IconSvg :name="collapsed ? 'chevR' : 'chevL'" :size="14" />
    </button>
  </aside>
</template>

<script setup>
import { computed } from "vue";
import { useRoute, useRouter } from "vue-router";
import IconSvg from "../components/IconSvg.vue";
import { NAV, isVueOwned } from "./nav.js";
import { usePermissions } from "../composables/usePermissions.js";

defineProps({ collapsed: { type: Boolean, default: false } });
defineEmits(["toggle"]);

const route  = useRoute();
const router = useRouter();
const { can } = usePermissions();

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
  // Vue-owned routes: stay in-app via router-push.
  // Legacy routes: full navigation so books.html's loader picks the legacy bundle.
  if (isVueOwned(item.path)) {
    router.push(item.path);
  } else {
    window.location.href = `/books#${item.path}`;
  }
}
</script>
