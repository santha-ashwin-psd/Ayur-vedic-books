// Permission gating. Reads from the reactive session populated by
// bootstrapSession() at boot time; no extra round trip needed.

import { computed } from "vue";
import { session } from "../api/session.js";

export function usePermissions() {
  const flags      = computed(() => session.permissions || {});
  const role       = computed(() => session.permissions?.books_role || "");
  const isAdmin    = computed(() => !!session.permissions?.is_company_admin);
  // "Books Viewer" is read-only everywhere (mirrors the backend).
  const isReadonly = computed(() => session.permissions?.books_role === "Books Viewer");

  function can(module) {
    if (!module) return true;       // routes without a module gate (e.g. dashboard) pass through.
    if (isAdmin.value) return true; // admins get everything; backend mirrors this.
    const key = module.startsWith("mod_") ? module : `mod_${module}`;
    return !!flags.value[key];
  }

  // Whether the user may create/edit/delete in `module`. Admins → yes; read-only
  // roles → no; everyone else needs the module flag. Backend enforces the same,
  // so this is for UX (disable/grey out) only.
  function canWrite(module) {
    if (isAdmin.value) return true;
    if (isReadonly.value) return false;
    return can(module);
  }

  return { flags, role, isAdmin, isReadonly, can, canWrite };
}
