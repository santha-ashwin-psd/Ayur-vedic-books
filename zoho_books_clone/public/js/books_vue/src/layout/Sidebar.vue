<template>
  <aside class="bv-sidebar" :class="{ 'bv-sidebar-collapsed': collapsed }">

    <!-- Brand row -->
    <div class="bv-sidebar-brand">
      <span
        class="bv-sidebar-brand-mark"
        @click.stop="collapsed && $emit('toggle')"
        :style="collapsed ? 'cursor:pointer' : ''"
      >B</span>
      <span v-if="!collapsed" class="bv-sidebar-brand-text">Books</span>
      <button class="bv-sidebar-collapse" @click.stop="$emit('toggle')" :title="collapsed ? 'Expand' : 'Collapse'">
        <IconSvg :name="collapsed ? 'chevR' : 'chevL'" :size="13" />
      </button>
    </div>

    <!-- Nav items -->
    <nav class="bv-sidebar-nav">
      <template v-for="group in navGroups" :key="group.section ?? '__root__'">

        <!-- Section header (only shown when sidebar is expanded) -->
        <div
          v-if="group.section && !collapsed"
          class="bv-sidebar-section"
          @click="toggleSection(group.section)"
        >
          <span>{{ group.section }}</span>
          <IconSvg
            :name="isSectionOpen(group.section) ? 'chevU' : 'chevD'"
            :size="10"
            class="bv-section-chev"
          />
        </div>

        <!-- Items — always show in collapsed mode (icons only), or when section is open -->
        <template v-if="collapsed || !group.section || isSectionOpen(group.section)">
          <a
            v-for="item in group.items"
            :key="item.path"
            :href="`#${item.path}`"
            class="bv-sidebar-item"
            :class="{ 'bv-sidebar-item-active': isActive(item.path) }"
            :title="collapsed ? item.label : ''"
            @click.prevent="goTo(item)"
          >
            <span class="bv-sidebar-icon"><IconSvg :name="item.icon" :size="15" /></span>
            <span v-if="!collapsed" class="bv-sidebar-label">{{ item.label }}</span>
          </a>
        </template>

      </template>
    </nav>

    <!-- User footer -->
    <div
      class="bv-sidebar-user"
      @click="goTo({ path: '/settings/profile' })"
      :title="collapsed ? (session.fullname || session.user) : ''"
    >
      <div class="bv-sidebar-avatar">{{ initials }}</div>
      <div v-if="!collapsed" class="bv-sidebar-user-info">
        <div class="bv-sidebar-user-name">{{ session.fullname || session.user }}</div>
        <div class="bv-sidebar-user-role">{{ role || 'Member' }}</div>
      </div>
    </div>

    <button class="bv-sidebar-logout" @click.stop="doLogout" :title="collapsed ? 'Sign out' : ''">
      <IconSvg name="logout" :size="14" />
      <span v-if="!collapsed">Sign out</span>
    </button>

  </aside>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
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

// ── Collapsed sections ────────────────────────────────────────────────
const SECTION_KEY = "books_sidebar_sections";
const collapsedSections = ref(new Set());

onMounted(() => {
  try {
    const saved = JSON.parse(localStorage.getItem(SECTION_KEY) || "[]");
    collapsedSections.value = new Set(saved);
  } catch {}
});

function toggleSection(section) {
  const s = new Set(collapsedSections.value);
  if (s.has(section)) s.delete(section);
  else s.add(section);
  collapsedSections.value = s;
  try { localStorage.setItem(SECTION_KEY, JSON.stringify([...s])); } catch {}
}

function isSectionOpen(section) {
  return !collapsedSections.value.has(section);
}

// ── Initials ──────────────────────────────────────────────────────────
const initials = computed(() => {
  const n = (session.fullname || session.user || "?").trim();
  const parts = n.split(/\s+/).filter(Boolean);
  return ((parts[0]?.[0] || "") + (parts[1]?.[0] || "")).toUpperCase() || "?";
});

// ── Logout ────────────────────────────────────────────────────────────
async function doLogout() {
  try {
    const csrf = window.frappe?.csrf_token ||
      document.cookie.match(/csrf_token=([^;]+)/)?.[1] || "";
    await fetch("/api/method/logout", {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Frappe-CSRF-Token": csrf,
      },
      body: csrf ? "csrf_token=" + encodeURIComponent(csrf) : "",
    });
  } catch {}
  window.location.replace("/login");
}

// ── Visible nav grouped by section ───────────────────────────────────
const navGroups = computed(() => {
  const groups = [];
  let current = null;
  for (const item of NAV) {
    if (item.section) {
      if (current) groups.push(current);
      current = { section: item.section, items: [] };
      continue;
    }
    if (!can(item.module)) continue;
    if (!current) current = { section: null, items: [] };
    current.items.push(item);
  }
  if (current && current.items.length) groups.push(current);
  return groups.filter(g => g.items.length);
});

// ── Routing ───────────────────────────────────────────────────────────
function isActive(path) {
  if (path === "/") return route.path === "/";
  return route.path === path || route.path.startsWith(path + "/");
}

function goTo(item) {
  router.push(item.path);
}
</script>
