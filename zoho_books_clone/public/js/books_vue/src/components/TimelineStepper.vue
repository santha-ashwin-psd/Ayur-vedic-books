<template>
  <div class="tls-wrap">
    <template v-for="(step, i) in steps" :key="step.key">
      <div
        class="tls-step"
        :class="{ done: step.done, danger: step.danger, current: step.current }"
      >
        <div class="tls-dot">
          <span v-if="step.danger">!</span>
          <span v-else-if="step.done">✓</span>
          <span v-else>{{ i + 1 }}</span>
        </div>
        <div class="tls-lbl">{{ step.label }}</div>
      </div>
      <div
        v-if="i < steps.length - 1"
        class="tls-line"
        :class="{
          done: steps[i + 1].done || steps[i + 1].current,
          danger: steps[i + 1].danger,
        }"
      ></div>
    </template>
  </div>
</template>

<script setup>
defineProps({
  steps: { type: Array, required: true },
  // Each step: { key, label, done?, danger?, current? }
});
</script>

<style scoped>
.tls-wrap {
  display: flex; align-items: center; gap: 4px;
  padding: 18px 24px; background: rgba(255,255,255,.08);
}
.tls-step { display: flex; align-items: center; gap: 8px; }
.tls-dot {
  width: 26px; height: 26px; border-radius: 50%;
  background: rgba(255,255,255,.22); color: rgba(255,255,255,.7);
  display: grid; place-items: center; font-size: 12px; font-weight: 700;
  border: 2px solid transparent; transition: all .2s;
  font-family: 'Inter', sans-serif;
}
.tls-step.done .tls-dot { background: #059669; color: #fff; }
.tls-step.danger .tls-dot { background: #dc2626; color: #fff; }
.tls-step.current .tls-dot { background: #fff; color: #1e3a5f; border-color: rgba(255,255,255,.4); }
.tls-lbl {
  font-size: 12px; font-weight: 600;
  color: rgba(255,255,255,.75); white-space: nowrap;
}
.tls-step.done .tls-lbl, .tls-step.current .tls-lbl { color: #fff; }
.tls-step.danger .tls-lbl { color: #fecaca; }
.tls-line {
  flex: 1; height: 2px; min-width: 24px;
  background: rgba(255,255,255,.22); transition: background .2s;
}
.tls-line.done { background: #059669; }
.tls-line.danger { background: #dc2626; }
</style>
