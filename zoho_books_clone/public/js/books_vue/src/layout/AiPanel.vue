<template>
  <Teleport to="body">
    <div v-if="open" class="bv-ai-panel">
      <div class="bv-ai-header">
        <span><IconSvg name="sparkle" :size="16" /> AI Assistant</span>
        <button class="bv-ai-close" @click="$emit('close')">✕</button>
      </div>
      <div ref="logEl" class="bv-ai-log">
        <div v-for="(m, i) in messages" :key="i" :class="`bv-ai-msg bv-ai-msg-${m.role}`">
          <div class="bv-ai-msg-text">{{ m.content }}</div>
        </div>
        <div v-if="busy" class="bv-ai-msg bv-ai-msg-assistant"><em>Thinking…</em></div>
      </div>
      <form class="bv-ai-input" @submit.prevent="send">
        <input
          v-model="draft" :disabled="busy"
          placeholder="Ask me to create an invoice, find overdue dues, …"
        />
        <button type="submit" :disabled="busy || !draft.trim()">Send</button>
      </form>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, nextTick, watch } from "vue";
import IconSvg from "../components/IconSvg.vue";
import { apiPOST } from "../api/client.js";
import { useAiActions } from "../composables/useAiActions.js";

const props = defineProps({ open: { type: Boolean, default: false } });
defineEmits(["close"]);

const draft    = ref("");
const busy     = ref(false);
const messages = ref([]);
const logEl    = ref(null);
const { dispatch } = useAiActions();

async function send() {
  const content = draft.value.trim();
  if (!content) return;
  messages.value.push({ role: "user", content });
  draft.value = "";
  busy.value = true;
  await scroll();
  try {
    const payload = { messages: JSON.stringify(messages.value) };
    const res = await apiPOST("zoho_books_clone.api.books_data.ai_chat", payload);
    const reply = res?.reply || res?.message || (typeof res === "string" ? res : "");
    let action = res?.action || null;
    // If the server returned a JSON-in-string with an action, try to parse.
    if (!action && typeof reply === "string") {
      const m = reply.match(/\{[\s\S]*\}/);
      if (m) {
        try { const j = JSON.parse(m[0]); if (j.action) action = j; }
        catch {}
      }
    }
    if (action?.action) dispatch(action.action, action);
    messages.value.push({ role: "assistant", content: typeof reply === "string" ? reply : JSON.stringify(reply) });
  } catch (e) {
    messages.value.push({ role: "assistant", content: "Sorry — " + (e?.message || "something broke.") });
  } finally {
    busy.value = false;
    await scroll();
  }
}

async function scroll() {
  await nextTick();
  if (logEl.value) logEl.value.scrollTop = logEl.value.scrollHeight;
}

watch(() => props.open, (v) => { if (v && !messages.value.length) {
  messages.value.push({ role: "assistant", content: "Hi! I can create invoices, find overdue dues, and look up customers. What can I help with?" });
}});
</script>
