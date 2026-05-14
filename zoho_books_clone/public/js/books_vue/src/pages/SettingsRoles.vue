<template>
<div class="cust-page">
  <div class="cust-toolbar">
    <span style="font-size:18px;font-weight:700;color:#1a1a2e">Roles &amp; Permissions</span>
    <span style="background:#fff8f0;color:#e67700;padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600;border:1px solid #ffe8a3">Custom roles — Coming Soon (P2)</span>
  </div>
  <div style="display:grid;gap:14px;max-width:800px">
    <div v-for="role in BUILTIN" :key="role.name" style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:20px">
      <div style="display:flex;align-items:flex-start;justify-content:space-between;margin-bottom:14px">
        <div style="display:flex;align-items:center;gap:12px">
          <span :style="'background:'+role.bg+';color:'+role.color+';padding:4px 12px;border-radius:20px;font-size:12.5px;font-weight:700'">{{role.name}}</span>
          <span style="font-size:12.5px;color:#4a5568">{{role.desc}}</span>
        </div>
        <span style="font-size:11px;color:#868e96;background:#f8f9fa;padding:2px 8px;border-radius:6px">Built-in</span>
      </div>
      <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px">
        <div v-for="m in MODULES" :key="m.key" :style="'display:flex;align-items:center;gap:6px;padding:6px 10px;border-radius:6px;font-size:12px;'+(role.perms[m.key]?'background:#ebfbee;color:#2f9e44':'background:#f8f9fa;color:#868e96')">
          <span>{{role.perms[m.key]?'✅':'🔒'}}</span> {{m.lbl}}
        </div>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
const BUILTIN = [
  { name: "Books Admin",   desc: "Full access — can manage users, settings, all transactions", color: "#7048E8", bg: "#F3F0FF",
    perms: { sales: true,  purchases: true,  banking: true,  reports: true, settings: true,  users: true } },
  { name: "Accountant",    desc: "Create & edit transactions, view reports. Cannot manage users or settings", color: "#1971C2", bg: "#E7F5FF",
    perms: { sales: true,  purchases: true,  banking: true,  reports: true, settings: false, users: false } },
  { name: "Books Manager", desc: "Read-only access to all modules", color: "#2F9E44", bg: "#EBFBEE",
    perms: { sales: false, purchases: false, banking: false, reports: true, settings: false, users: false } },
  { name: "Books Viewer",  desc: "View reports and read documents only", color: "#868E96", bg: "#F8F9FA",
    perms: { sales: false, purchases: false, banking: false, reports: true, settings: false, users: false } },
];

const MODULES = [
  { key: "sales",     lbl: "Sales & Invoicing" },
  { key: "purchases", lbl: "Purchases & Expenses" },
  { key: "banking",   lbl: "Banking" },
  { key: "reports",   lbl: "Reports" },
  { key: "settings",  lbl: "Settings" },
  { key: "users",     lbl: "User Management" },
];
</script>
