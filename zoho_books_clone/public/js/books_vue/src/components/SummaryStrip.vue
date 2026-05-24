<template>
  <div class="ssm-strip">
    <div
      v-for="(card, i) in cards"
      :key="i"
      class="ssm-card"
      :style="card.accent ? `border-left:3px solid ${card.accent}` : ''"
    >
      <div class="ssm-lbl" :style="card.accent ? `color:${card.accent}` : ''">{{ card.label }}</div>
      <div class="ssm-val" :style="card.accent ? `color:${card.accent}` : ''">{{ card.value }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  cards: { type: Array, required: true },
  // Each card: { label, value, accent?: hex }
});
</script>

<style scoped>
.ssm-strip {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 12px; padding: 16px 24px 0;
}
.ssm-card {
  background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  padding: 14px 16px; display: flex; flex-direction: column; gap: 4px;
  transition: box-shadow .15s;
}
.ssm-card:hover { box-shadow: 0 2px 8px rgba(15,23,42,.06); }
.ssm-lbl { font-size: 12px; font-weight: 600; color: #6b7280; }
.ssm-val { font-size: 22px; font-weight: 700; color: #111827; font-family: 'Plus Jakarta Sans', 'Lato', sans-serif; }
</style>
