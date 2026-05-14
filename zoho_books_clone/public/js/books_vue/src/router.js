// Vue router for the new bundle. Only routes the Vue bundle owns are listed
// here; everything else is handled by the legacy SPA via the cutover loader
// in books.html. New phases append routes to this table and to
// window.BOOKS_VUE_ROUTES.

import { createRouter, createWebHashHistory } from "vue-router";
import PhaseAHome           from "./pages/PhaseAHome.vue";
import Customers            from "./pages/Customers.vue";
import Vendors              from "./pages/Vendors.vue";
import InventoryItems       from "./pages/InventoryItems.vue";
import InventoryItemGroups  from "./pages/InventoryItemGroups.vue";
import InventoryWarehouses  from "./pages/InventoryWarehouses.vue";
import SettingsProfile       from "./pages/SettingsProfile.vue";
import SettingsCompany       from "./pages/SettingsCompany.vue";
import SettingsNumberSeries  from "./pages/SettingsNumberSeries.vue";
import SettingsPaymentTerms  from "./pages/SettingsPaymentTerms.vue";
import SettingsUsers         from "./pages/SettingsUsers.vue";
import SettingsEmail         from "./pages/SettingsEmail.vue";
import SettingsEmailTemplates from "./pages/SettingsEmailTemplates.vue";
import SettingsRoles         from "./pages/SettingsRoles.vue";
import SettingsAuditLog      from "./pages/SettingsAuditLog.vue";
import SettingsOrganization  from "./pages/SettingsOrganization.vue";
import SettingsSecurity      from "./pages/SettingsSecurity.vue";
import SettingsIntegrations  from "./pages/SettingsIntegrations.vue";
import SettingsCurrencyExchange from "./pages/SettingsCurrencyExchange.vue";
import ChartOfAccounts        from "./pages/ChartOfAccounts.vue";
import JournalEntries         from "./pages/JournalEntries.vue";
import OpeningBalances        from "./pages/OpeningBalances.vue";
import CostCenters            from "./pages/CostCenters.vue";
import FiscalYears            from "./pages/FiscalYears.vue";
import Invoices               from "./pages/Invoices.vue";

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
  {
    path: "/customers",
    name: "customers",
    component: Customers,
    meta: { module: "customers" },
  },
  {
    path: "/vendors",
    name: "vendors",
    component: Vendors,
    meta: { module: "customers" },  // Vendors share the customers module flag in Books Company Member
  },
  {
    path: "/inventory/items",
    name: "inventory-items",
    component: InventoryItems,
    meta: { module: "inventory" },
  },
  {
    path: "/inventory/item-groups",
    name: "inventory-item-groups",
    component: InventoryItemGroups,
    meta: { module: "inventory" },
  },
  {
    path: "/inventory/warehouses",
    name: "inventory-warehouses",
    component: InventoryWarehouses,
    meta: { module: "inventory" },
  },
  {
    path: "/settings/profile",
    name: "settings-profile",
    component: SettingsProfile,
    meta: { module: null },  // every user can edit their own profile
  },
  {
    path: "/settings/company",
    name: "settings-company",
    component: SettingsCompany,
    meta: { module: "admin" },
  },
  {
    path: "/settings/number-series",
    name: "settings-number-series",
    component: SettingsNumberSeries,
    meta: { module: "admin" },
  },
  {
    path: "/settings/payment-terms",
    name: "settings-payment-terms",
    component: SettingsPaymentTerms,
    meta: { module: "admin" },
  },
  {
    path: "/settings/users",
    name: "settings-users",
    component: SettingsUsers,
    meta: { module: "admin" },
  },
  {
    path: "/settings/email",
    name: "settings-email",
    component: SettingsEmail,
    meta: { module: "admin" },
  },
  {
    path: "/settings/email-templates",
    name: "settings-email-templates",
    component: SettingsEmailTemplates,
    meta: { module: "admin" },
  },
  { path: "/settings/roles",             name: "settings-roles",        component: SettingsRoles,         meta: { module: "admin" } },
  { path: "/settings/audit-log",         name: "settings-audit-log",    component: SettingsAuditLog,      meta: { module: "admin" } },
  { path: "/settings/organization",      name: "settings-organization", component: SettingsOrganization,  meta: { module: "admin" } },
  { path: "/settings/security",          name: "settings-security",     component: SettingsSecurity,      meta: { module: null    } },
  { path: "/settings/integrations",      name: "settings-integrations", component: SettingsIntegrations,  meta: { module: "admin" } },
  { path: "/settings/currency-exchange", name: "settings-currency",     component: SettingsCurrencyExchange, meta: { module: "admin" } },
  { path: "/accounting/chart-of-accounts", name: "chart-of-accounts", component: ChartOfAccounts,  meta: { module: "accounts" } },
  { path: "/accounting/journal-entries",   name: "journal-entries",   component: JournalEntries,   meta: { module: "accounts" } },
  { path: "/accounting/opening-balances",  name: "opening-balances",  component: OpeningBalances,  meta: { module: "accounts" } },
  { path: "/accounting/cost-centers",      name: "cost-centers",      component: CostCenters,      meta: { module: "accounts" } },
  { path: "/accounting/fiscal-years",      name: "fiscal-years",      component: FiscalYears,      meta: { module: "accounts" } },
  { path: "/invoices",                     name: "invoices",          component: Invoices,         meta: { module: "invoices" } },
  // Future phases append entries here.
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
