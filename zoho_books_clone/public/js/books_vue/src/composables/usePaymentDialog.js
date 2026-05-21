// Generic payment recording dialog. Works for both customer-side (Invoice) and
// vendor-side (Bill) by passing a different sendEndpoint.
//
// Usage:
//   const { openPayment } = usePaymentDialog();
//   const paymentName = await openPayment({
//     direction: "receive",                // "receive" (from customer) or "pay" (to vendor)
//     doctype: "Sales Invoice",
//     name: "INV-001",
//     party: "Acme Corp",
//     partyLabel: "Acme Corp",
//     balance: 5000,
//     getDefaultsEndpoint: "zoho_books_clone.api.books_data.get_payment_defaults",
//     sendEndpoint: "zoho_books_clone.api.books_data.record_payment",
//     paramKey: "invoice_name",
//   });

import { reactive } from "vue";

const state = reactive({
  open: false,
  direction: "receive",
  doctype: "",
  name: "",
  party: "",
  partyLabel: "",
  balance: 0,
  getDefaultsEndpoint: "",
  sendEndpoint: "",
  paramKey: "name",
  resolve: null,
});

export function usePaymentDialog() {
  function openPayment(opts) {
    return new Promise((resolve) => {
      Object.assign(state, {
        open: true,
        direction: "receive",
        doctype: "",
        name: "",
        party: "",
        partyLabel: "",
        balance: 0,
        getDefaultsEndpoint: "",
        sendEndpoint: "",
        paramKey: "name",
        ...opts,
        resolve,
      });
    });
  }
  function complete(paymentName) {
    state.open = false;
    const r = state.resolve; state.resolve = null;
    r?.(paymentName);
  }
  function cancel() {
    state.open = false;
    const r = state.resolve; state.resolve = null;
    r?.(null);
  }
  return { state, openPayment, complete, cancel };
}
