<template>
  <div class="bv-app" :class="{ 'bv-app-sidebar-collapsed': collapsed }">
    <Sidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />
    <div class="bv-app-main">
      <Topbar @toggle-ai="aiOpen = !aiOpen" />
      <main class="bv-app-content">
        <router-view />
      </main>
    </div>

    <Toast />
    <Confirm />
    <AiPanel :open="aiOpen" @close="aiOpen = false" />
    <TutorialOverlay />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import Sidebar          from "./Sidebar.vue";
import Topbar           from "./Topbar.vue";
import AiPanel          from "./AiPanel.vue";
import TutorialOverlay  from "./TutorialOverlay.vue";
import Toast            from "../components/Toast.vue";
import Confirm          from "../components/Confirm.vue";

const COLLAPSE_KEY = "books_sidebar_collapsed";

const collapsed = ref(false);
const aiOpen    = ref(false);

onMounted(() => {
  try { collapsed.value = localStorage.getItem(COLLAPSE_KEY) === "1"; } catch {}
});

watch(collapsed, (v) => {
  try { localStorage.setItem(COLLAPSE_KEY, v ? "1" : "0"); } catch {}
});
</script>
