<template>
<div class="cust-page">
  <div class="cust-toolbar"><span style="font-size:18px;font-weight:700;color:#1a1a2e">Security</span></div>
  <div style="max-width:600px;display:grid;gap:16px">
    <div style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:24px">
      <div style="font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:4px">Two-Factor Authentication (2FA)</div>
      <div style="font-size:12.5px;color:#868e96;margin-bottom:16px">Require a one-time code from an authenticator app on every login.</div>
      <div style="display:flex;align-items:center;gap:14px;padding:14px;background:#f8f9fc;border-radius:8px;margin-bottom:12px">
        <span style="font-size:28px">🔐</span>
        <div><div style="font-size:13px;font-weight:600;color:#1a1a2e">Authenticator App (TOTP)</div><div style="font-size:12px;color:#868e96">Google Authenticator, Authy, 1Password</div></div>
        <span style="background:#fff8f0;color:#e67700;padding:2px 10px;border-radius:20px;font-size:11.5px;font-weight:600;border:1px solid #ffe8a3;margin-left:auto">Coming Soon</span>
      </div>
      <div style="display:flex;align-items:center;gap:14px;padding:14px;background:#f8f9fc;border-radius:8px">
        <span style="font-size:28px">📱</span>
        <div><div style="font-size:13px;font-weight:600;color:#1a1a2e">SMS OTP</div><div style="font-size:12px;color:#868e96">One-time code sent to your mobile number</div></div>
        <span style="background:#fff8f0;color:#e67700;padding:2px 10px;border-radius:20px;font-size:11.5px;font-weight:600;border:1px solid #ffe8a3;margin-left:auto">Coming Soon</span>
      </div>
    </div>
    <div style="background:#fff;border:1px solid #e4e8f0;border-radius:12px;padding:24px">
      <div style="font-size:15px;font-weight:700;color:#1a1a2e;margin-bottom:4px">Active Sessions</div>
      <div style="font-size:12.5px;color:#868e96;margin-bottom:12px">Devices currently logged into your account.</div>
      <div style="padding:14px;background:#f8f9fc;border-radius:8px;display:flex;align-items:center;gap:12px">
        <span style="font-size:22px">💻</span>
        <div><div style="font-size:13px;font-weight:600">This device</div><div style="font-size:12px;color:#868e96">Current session · Browser</div></div>
        <span style="background:#ebfbee;color:#2f9e44;padding:2px 10px;border-radius:20px;font-size:11.5px;font-weight:600;margin-left:auto">Active</span>
      </div>
    </div>
  </div>
</div>
</template>

<script setup>
// Pure presentational stub — Coming Soon markers for 2FA and SMS OTP per legacy.
</script>
