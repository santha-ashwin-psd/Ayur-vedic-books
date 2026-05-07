// Permission gating. Reads from the reactive session populated by
// bootstrapSession() at boot time; no extra round trip needed.

import { computed } from "vue";
import { session } from "../api/session.js";

export function usePermissions() {
  const flags    = computed(() => session.permissions || {});
  const role     = computed(() => session.permissions?.books_role || "");
  const isAdmin  = computed(() => !!session.permissions?.is_company_admin);

  function can(module) {
    if (!module) return true;       // routes without a module gate (e.g. dashboard) pass through.
    if (isAdmin.value) return true; // admins get everything; backend mirrors this.
    const key = module.startsWith("mod_") ? module : `mod_${module}`;
    return !!flags.value[key];
  }

  return { flags, role, isAdmin, can };
}
