// Vue router for the new bundle. Only routes the Vue bundle owns are listed
// here; everything else is handled by the legacy SPA via the cutover loader
// in books.html. New phases append routes to this table and to
// window.BOOKS_VUE_ROUTES.

import { createRouter, createWebHashHistory } from "vue-router";
import PhaseAHome from "./pages/PhaseAHome.vue";

import { useToast } from "./composables/useToast.js";
import { usePermissions } from "./composables/usePermissions.js";
import { session } from "./api/session.js";

const routes = [
  {
    path: "/",
    name: "dashboard",
    component: PhaseAHome,
    meta: { module: null },
  },
  // Phase B and beyond append entries here.
  {
    path: "/:pathMatch(.*)*",
    name: "not-found",
    component: PhaseAHome,
    meta: { module: null, fallback: true },
  },
];

const router = createRouter({
  history: createWebHashHistory(),
  routes,
});

router.beforeEach((to) => {
  // Auth: bootstrapSession() either populated session.ready or redirected.
  if (!session.ready) return false;

  const { can } = usePermissions();
  if (to.meta?.module && !can(to.meta.module)) {
    useToast().error(`You don't have access to "${to.name || to.path}".`);
    return { path: "/" };
  }
  return true;
});

export default router;
