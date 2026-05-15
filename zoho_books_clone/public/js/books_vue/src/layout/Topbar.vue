<template>
  <header class="bv-topbar">
    <div class="bv-topbar-title">{{ title }}</div>

    <div class="bv-topbar-search">
      <IconSvg name="search" :size="14" />
      <input
        v-model="query"
        placeholder="Search invoices, customers, items…"
        @keydown.enter="doSearch"
      />
    </div>

    <button class="bv-topbar-icon-btn" :title="'AI Assistant'" @click="$emit('toggle-ai')">
      <IconSvg name="sparkle" :size="18" />
    </button>

    <NotificationsBell />

    <div class="bv-topbar-user" @click.stop="userOpen = !userOpen">
      <div class="bv-topbar-avatar">{{ initials }}</div>
      <span class="bv-topbar-username">{{ session.fullname || session.user }}</span>
      <div v-if="userOpen" class="bv-topbar-user-menu">
        <a href="#" @click.prevent="router.push('/settings/profile'); userOpen=false">My Profile</a>
        <a href="#" v-if="isAdmin" @click.prevent="router.push('/settings/users'); userOpen=false">Users</a>
        <hr />
        <a href="#" @click.prevent="doLogout">Sign out</a>
      </div>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute, useRouter } from "vue-router";
import IconSvg from "../components/IconSvg.vue";
import NotificationsBell from "./NotificationsBell.vue";
import { titleFor } from "./nav.js";
import { session } from "../api/session.js";
import { usePermissions } from "../composables/usePermissions.js";

defineEmits(["toggle-ai"]);

const route   = useRoute();
const router  = useRouter();
const query   = ref("");
const userOpen = ref(false);
const { isAdmin } = usePermissions();

const title = computed(() => titleFor(route.path));

const initials = computed(() => {
  const n = (session.fullname || session.user || "?").trim();
  const parts = n.split(/\s+/).filter(Boolean);
  if (!parts.length) return "?";
  return ((parts[0][0] || "") + (parts[1]?.[0] || "")).toUpperCase();
});

async function doLogout() {
  userOpen.value = false;
  try {
    await fetch("/api/method/logout", { method: "POST", credentials: "same-origin" });
  } catch {}
  window.location.href = "/login";
}

function doSearch() {
  // Topbar search is preserved as a feature stub — the legacy SPA never built
  // a real Cmd+K palette. Hand off to the Frappe-native search until we wire
  // an in-SPA result page in a later phase.
  if (!query.value.trim()) return;
  window.open(`/app/search?q=${encodeURIComponent(query.value)}`, "_blank");
}

function onDocClick(e) {
  if (!e.target.closest(".bv-topbar-user")) userOpen.value = false;
}
onMounted(()   => document.addEventListener("click", onDocClick));
onUnmounted(() => document.removeEventListener("click", onDocClick));
</script>
