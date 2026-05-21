<template>
  <transition name="bab-slide">
    <div v-if="count > 0" class="bab-bar">
      <span class="bab-count">{{ count }} selected</span>
      <slot />
      <button class="bab-clear" @click="$emit('clear')">✕ Clear</button>
    </div>
  </transition>
</template>

<script setup>
defineProps({ count: { type: Number, default: 0 } });
defineEmits(["clear"]);
</script>

<style scoped>
.bab-bar {
  display: flex; align-items: center; gap: 10px;
  margin: 12px 24px 0; padding: 10px 16px;
  background: #1e3a5f; color: #fff; border-radius: 10px;
  box-shadow: 0 4px 14px rgba(15,23,42,.18);
  font-size: 13px;
}
.bab-count {
  background: rgba(255,255,255,.18); padding: 3px 10px; border-radius: 999px;
  font-size: 12px; font-weight: 600;
}
.bab-clear {
  margin-left: auto; background: transparent; border: none; color: rgba(255,255,255,.78);
  font: inherit; cursor: pointer; font-size: 12px; padding: 4px 8px; border-radius: 6px;
}
.bab-clear:hover { color: #fff; background: rgba(255,255,255,.1); }
.bab-bar :deep(button:not(.bab-clear)) {
  background: rgba(255,255,255,.12); border: 1px solid rgba(255,255,255,.18);
  color: #fff; font: inherit; font-size: 12px; padding: 6px 12px; border-radius: 6px;
  cursor: pointer; transition: background .12s;
  display: inline-flex; align-items: center; gap: 6px;
}
.bab-bar :deep(button:not(.bab-clear):hover) { background: rgba(255,255,255,.2); }
.bab-bar :deep(button.bab-danger) {
  background: #dc2626; border-color: #b91c1c;
}
.bab-bar :deep(button.bab-danger:hover) { background: #b91c1c; }
.bab-slide-enter-active, .bab-slide-leave-active { transition: all .18s; }
.bab-slide-enter-from, .bab-slide-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
