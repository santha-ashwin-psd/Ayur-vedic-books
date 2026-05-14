<template>
<div class="cust-page">
  <div class="cust-toolbar"><span style="font-size:18px;font-weight:700;color:#1a1a2e">Integrations</span></div>
  <div style="max-width:700px;display:grid;gap:14px">
    <div v-for="intg in integrations" :key="intg.name" style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:20px;display:flex;align-items:center;gap:16px">
      <div style="width:48px;height:48px;border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:24px;flex-shrink:0" :style="'background:'+intg.bg">{{intg.icon}}</div>
      <div style="flex:1"><div style="font-size:14px;font-weight:700;color:#1a1a2e">{{intg.name}}</div><div style="font-size:12.5px;color:#868e96;margin-top:2px">{{intg.desc}}</div></div>
      <span :style="'padding:3px 12px;border-radius:20px;font-size:12px;font-weight:600;border:1px solid;'+intg.badgeStyle">{{intg.status}}</span>
    </div>
  </div>
</div>
</template>

<script setup>
const integrations = [
  { name: "Google Sign-In (SSO)", icon: "🔑", bg: "#FFF3BF", desc: "Allow users to log in with their Google account",                    status: "P3 — Planned", badgeStyle: "background:#e7f5ff;color:#1971c2;border-color:#a5d8ff" },
  { name: "Slack Notifications",  icon: "💬", bg: "#F3F0FF", desc: "Send invoice and payment events to Slack channels via webhook",        status: "P3 — Planned", badgeStyle: "background:#e7f5ff;color:#1971c2;border-color:#a5d8ff" },
  { name: "Webhooks",              icon: "🔗", bg: "#EBFBEE", desc: "Push real-time events to any HTTP endpoint when invoices, payments, or expenses are created", status: "P3 — Planned", badgeStyle: "background:#e7f5ff;color:#1971c2;border-color:#a5d8ff" },
  { name: "Client Portal",         icon: "🌐", bg: "#FFF5F5", desc: "Let customers log in to view their invoices and make payments online", status: "P3 — Planned", badgeStyle: "background:#e7f5ff;color:#1971c2;border-color:#a5d8ff" },
  { name: "Microsoft SSO",         icon: "🏢", bg: "#F8F9FA", desc: "Azure Active Directory single sign-on for enterprise users",           status: "P3 — Planned", badgeStyle: "background:#e7f5ff;color:#1971c2;border-color:#a5d8ff" },
];
</script>
