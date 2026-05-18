<template>
  <div class="bv-app" :class="{ 'bv-app-sidebar-collapsed': collapsed }">
    <Sidebar :collapsed="collapsed" @toggle="collapsed = !collapsed" />
    <div class="bv-app-main">
      <Topbar @toggle-ai="aiOpen = !aiOpen" :alert-count="alertCount" />
      <main class="bv-app-content">
        <router-view />
      </main>
    </div>

    <Toast />
    <Confirm />
    <AiPanel :open="aiOpen" :alerts="aiAlerts" @close="aiOpen = false" @alerts-seen="alertCount = 0" />
    <TutorialOverlay />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from "vue";
import { useRouter } from "vue-router";
import Sidebar          from "./Sidebar.vue";
import Topbar           from "./Topbar.vue";
import AiPanel          from "./AiPanel.vue";
import TutorialOverlay  from "./TutorialOverlay.vue";
import Toast            from "../components/Toast.vue";
import Confirm          from "../components/Confirm.vue";
import { useAiActions } from "../composables/useAiActions.js";
import { apiGET }       from "../api/client.js";

const COLLAPSE_KEY = "books_sidebar_collapsed";

const collapsed  = ref(false);
const aiOpen     = ref(false);
const alertCount = ref(0);
const aiAlerts   = ref([]);
const router     = useRouter();
const { register } = useAiActions();

onMounted(async () => {
  try { collapsed.value = localStorage.getItem(COLLAPSE_KEY) === "1"; } catch {}
  try {
    const res = await apiGET("zoho_books_clone.api.books_data.get_ai_alerts");
    aiAlerts.value   = res?.alerts || [];
    alertCount.value = aiAlerts.value.length;
  } catch { /* alerts are non-critical */ }

  // Global AI navigation handlers — always active since AppShell is always mounted.
  // Pages can override specific actions (e.g. Invoices overrides show_overdue to
  // apply the filter in-place instead of navigating away).
  register("show_overdue",         () => router.push("/invoices?ai_filter=Overdue"));
  register("show_unpaid",          () => router.push("/invoices?ai_filter=Unpaid"));
  register("show_all_invoices",    () => router.push("/invoices"));
  register("find_invoices",        (p) => router.push("/invoices?ai_search=" + encodeURIComponent(p.customer || "")));
  register("create_invoice",       (p) => {
    const q = new URLSearchParams({ ai_create: "1" });
    if (p.customer)    q.set("ai_customer", p.customer);
    if (p.items?.[0]) {
      const it = p.items[0];
      if (it.item_name) q.set("ai_item",   it.item_name);
      if (it.qty)       q.set("ai_qty",    String(it.qty));
      if (it.rate)      q.set("ai_rate",   String(it.rate));
      if (it.amount)    q.set("ai_amount", String(it.amount));
    }
    router.push("/invoices?" + q.toString());
  });
  register("show_outstanding",     () => router.push("/"));
  register("show_bills",           () => router.push("/bills"));
  register("show_quotes",          () => router.push("/quotes"));
  register("show_customers",       () => router.push("/customers"));
  register("show_dashboard",       () => router.push("/"));
  register("show_sales_orders",    () => router.push("/sales-orders"));
  register("show_purchase_orders", () => router.push("/purchase-orders"));
  register("navigate",             (p) => { if (p.path) router.push(p.path); });
});

watch(collapsed, (v) => {
  try { localStorage.setItem(COLLAPSE_KEY, v ? "1" : "0"); } catch {}
});
</script>
