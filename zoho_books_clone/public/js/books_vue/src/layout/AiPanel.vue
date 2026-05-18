<template>
  <Teleport to="body">
    <div v-if="open" class="bv-ai-panel">

      <div class="bv-ai-header">
        <span class="bv-ai-header-title">
          <IconSvg name="sparkle" :size="15" /> Books AI
        </span>
        <button class="bv-ai-close" @click="$emit('close')">✕</button>
      </div>

      <!-- Proactive Alerts (Tier 5-B) -->
      <div v-if="alerts.length && showAlerts" class="bv-ai-alerts">
        <div class="bv-ai-alerts-title">
          <span>🔔 Alerts</span>
          <button class="bv-ai-alerts-dismiss" @click="dismissAlerts">Dismiss</button>
        </div>
        <div
          v-for="(a, i) in alerts" :key="i"
          class="bv-ai-alert-item"
          :class="`bv-ai-alert-${a.type}`"
          @click="a.action && handleAlertClick(a)"
          :style="a.action ? 'cursor:pointer' : ''"
        >
          {{ a.icon }} {{ a.text }}
          <span v-if="a.action" class="bv-ai-alert-arrow">→</span>
        </div>
      </div>

      <div ref="logEl" class="bv-ai-log">
        <div
          v-for="(m, i) in messages" :key="i"
          :class="`bv-ai-msg bv-ai-msg-${m.role}`"
        >
          <div class="bv-ai-msg-text" v-html="renderText(m.content)"></div>

          <!-- Confirm card for create_invoice_confirm (Tier 5-A) -->
          <div v-if="m.confirm" class="bv-ai-confirm-card">
            <div class="bv-ai-confirm-header">📄 Invoice Preview</div>
            <div class="bv-ai-confirm-row">
              <span class="bv-ai-confirm-label">Customer</span>
              <span>{{ m.confirm.customer || '—' }}</span>
            </div>
            <div v-for="(item, j) in (m.confirm.items || [])" :key="j" class="bv-ai-confirm-row">
              <span class="bv-ai-confirm-label">{{ item.item_name }}</span>
              <span>× {{ item.qty }} @ ₹{{ Number(item.rate || 0).toLocaleString() }}</span>
            </div>
            <div class="bv-ai-confirm-total" v-if="confirmTotal(m.confirm)">
              Total: ₹{{ confirmTotal(m.confirm).toLocaleString() }}
            </div>
            <div v-if="!m.confirmed" class="bv-ai-confirm-actions">
              <button class="bv-ai-confirm-yes" @click="doConfirmCreate(m)">✓ Confirm</button>
              <button class="bv-ai-confirm-no"  @click="doCancelCreate(m)">✕ Cancel</button>
            </div>
            <div v-else class="bv-ai-confirm-done">{{ m.confirmed }}</div>
          </div>

          <div v-if="m.action && m.action !== 'create_invoice_confirm'" class="bv-ai-action-chip">
            ✓ {{ actionLabel(m.action) }}
          </div>
        </div>

        <div v-if="busy" class="bv-ai-msg bv-ai-msg-assistant bv-ai-thinking">
          <span></span><span></span><span></span>
        </div>
      </div>

      <!-- Quick suggestions -->
      <div v-if="messages.length <= 1 && !busy" class="bv-ai-chips">
        <button class="bv-ai-chip" @click="sendQuick('Show overdue invoices')">⚠️ Overdue</button>
        <button class="bv-ai-chip" @click="sendQuick('Revenue this month')">📈 Revenue</button>
        <button class="bv-ai-chip" @click="sendQuick('Business summary')">📊 Summary</button>
        <button class="bv-ai-chip" @click="sendQuick('Top 5 customers')">🏆 Top customers</button>
        <button class="bv-ai-chip" @click="sendQuick('Create invoice')">📄 New invoice</button>
        <button class="bv-ai-chip" @click="sendQuick('help')">❓ Help</button>
      </div>

      <form class="bv-ai-input" @submit.prevent="send">
        <input
          ref="inputEl"
          v-model="draft"
          :disabled="busy"
          placeholder="Ask anything — invoices, revenue, customers…"
          @keydown.enter.prevent="send"
        />
        <button type="submit" :disabled="busy || !draft.trim()" class="bv-ai-send">→</button>
      </form>

    </div>
  </Teleport>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";
import IconSvg from "../components/IconSvg.vue";
import { apiPOST } from "../api/client.js";
import { useAiActions } from "../composables/useAiActions.js";

const props = defineProps({
  open:   { type: Boolean, default: false },
  alerts: { type: Array,   default: () => [] },
});
const emit = defineEmits(["close", "alerts-seen"]);

const draft      = ref("");
const busy       = ref(false);
const messages   = ref([]);
const logEl      = ref(null);
const inputEl    = ref(null);
const showAlerts = ref(true);
const { dispatch } = useAiActions();

const ACTION_LABELS = {
  show_overdue:          "Filtered to overdue invoices",
  show_unpaid:           "Filtered to unpaid invoices",
  show_all_invoices:     "Showing all invoices",
  find_invoices:         "Filtered by customer",
  create_invoice:        "Opened new invoice",
  show_outstanding:      "Navigated to dashboard",
  show_bills:            "Navigated to bills",
  show_quotes:           "Navigated to quotes",
  show_customers:        "Navigated to customers",
  show_dashboard:        "Navigated to dashboard",
  show_sales_orders:     "Navigated to sales orders",
  show_purchase_orders:  "Navigated to purchase orders",
  navigate:              "Navigated",
};

function actionLabel(a) { return ACTION_LABELS[a] || a; }

function renderText(text) {
  return (text || "")
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/\n/g, "<br>");
}

function confirmTotal(confirm) {
  const items = confirm.items || [];
  const t = items.reduce((s, it) => s + (Number(it.rate || 0) * Number(it.qty || 1)), 0);
  return t || 0;
}

function dismissAlerts() {
  showAlerts.value = false;
  emit("alerts-seen");
}

function handleAlertClick(alert) {
  if (alert.action) dispatch(alert.action, {});
  dismissAlerts();
  emit("close");
}

async function doConfirmCreate(msg) {
  msg.confirmed = "✓ Creating invoice…";
  dispatch("create_invoice", msg.confirm);
  await nextTick();
  emit("close");
}

function doCancelCreate(msg) {
  msg.confirmed = "Cancelled.";
  messages.value.push({ role: "assistant", content: "No problem — invoice creation cancelled." });
  scroll();
}

async function send() {
  const content = draft.value.trim();
  if (!content || busy.value) return;
  draft.value = "";
  messages.value.push({ role: "user", content });
  busy.value = true;
  await scroll();
  try {
    const res = await apiPOST("zoho_books_clone.api.books_data.ai_chat", {
      messages: JSON.stringify(messages.value),
    });
    const reply  = res?.reply || res?.message || (typeof res === "string" ? res : "…");
    const action = res?.action || null;

    const msgObj = { role: "assistant", content: reply, action };

    if (action === "create_invoice_confirm") {
      msgObj.confirm = { customer: res.customer, items: res.items };
    } else if (action) {
      dispatch(action, res);
    }

    messages.value.push(msgObj);
  } catch (e) {
    messages.value.push({ role: "assistant", content: "Sorry — " + (e?.message || "something went wrong.") });
  } finally {
    busy.value = false;
    await scroll();
  }
}

function sendQuick(text) { draft.value = text; send(); }

async function scroll() {
  await nextTick();
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight;
}

watch(() => props.open, (v) => {
  if (v) {
    showAlerts.value = true;
    if (!messages.value.length) {
      messages.value.push({
        role: "assistant",
        content: "Hi! I'm your Books AI assistant.\n\nI can show overdue invoices, query revenue, summarise your business health, guide you through creating invoices step-by-step, and navigate the app.\n\nUse the quick actions below or just type naturally.",
      });
    }
    nextTick(() => inputEl.value?.focus());
  }
});
</script>
