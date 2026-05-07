// Global toast queue. <Toast /> mounts once at the AppShell level and renders
// from this shared list. Mirrors the legacy toast(msg,type) at books.js:274.

import { reactive } from "vue";

let _id = 0;
const state = reactive({ items: [] });

export function useToast() {
  function push(message, type = "success", ttl = 3500) {
    const id = ++_id;
    state.items.push({ id, message, type });
    setTimeout(() => {
      const i = state.items.findIndex(t => t.id === id);
      if (i !== -1) state.items.splice(i, 1);
    }, ttl);
  }

  return {
    items:   state.items,
    toast:   push,
    success: (m) => push(m, "success"),
    error:   (m) => push(m, "error"),
    warn:    (m) => push(m, "warning"),
    info:    (m) => push(m, "info"),
  };
}
