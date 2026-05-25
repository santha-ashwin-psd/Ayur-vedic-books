<template>
  <router-link v-if="to" :to="to" class="doc-link" :class="{ mono: monoStyle }" @click.stop>
    <slot>{{ name }}</slot>
  </router-link>
  <span v-else class="doc-link-disabled" :class="{ mono: monoStyle }">
    <slot>{{ name }}</slot>
  </span>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  /** Frappe doctype name, e.g. "Sales Invoice" */
  doctype: { type: String, required: true },
  /** Record name, e.g. "INV-2026-00072" */
  name:    { type: String, default: "" },
  /** Style toggle — true → monospace blue (default); false → inherit parent style */
  monoStyle: { type: Boolean, default: true },
});

/**
 * Central mapping of Frappe doctypes → SPA routes. Anywhere a clickable ID
 * appears in a drawer, this is the one source of truth for where it goes.
 * Returns null for doctypes we don't have a list page for — the link is
 * rendered as plain text in that case.
 */
const DOCTYPE_ROUTE = {
  "Sales Invoice":     "/invoices",
  "Purchase Invoice":  "/purchases",
  "Quotation":         "/quotes",
  "Sales Order":       "/sales-orders",
  "Purchase Order":    "/purchase-orders",
  "Payment Entry":     "/payments-received",
  "Credit Note":       "/credit-notes",
  "Debit Note":        "/debit-notes",
  "Delivery Note":     "/delivery-challans",
  "Purchase Receipt":  "/purchase-receipts",
  "Auto Repeat":       "/recurring",
  "E Way Bill":        "/eway-bills",
  "Customer":          "/customers",
  "Supplier":          "/vendors",
  "Item":              "/inventory/items",
  "Journal Entry":     "/accounting/journal-entries",
  "Expense":           "/expenses",
};

const to = computed(() => {
  const base = DOCTYPE_ROUTE[props.doctype];
  if (!base || !props.name) return null;
  return { path: base, query: { open: props.name } };
});
</script>

<style scoped>
.doc-link {
  color: #2563eb;
  font-weight: 600;
  text-decoration: none;
  border-bottom: 1px dashed transparent;
  cursor: pointer;
  transition: color .15s, border-color .15s;
}
.doc-link:hover { color: #1d4ed8; border-bottom-color: #2563eb; }
.doc-link.mono { font-family: monospace; font-size: 12.5px; }

.doc-link-disabled {
  color: #0f172a;
  font-weight: 600;
}
.doc-link-disabled.mono { font-family: monospace; font-size: 12.5px; }
</style>
