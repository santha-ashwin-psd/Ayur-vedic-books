<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="nim-overlay"
      @mousedown.self="closeOnBackdrop && $emit('close')"
    >
      <div class="nim-dialog" :style="{ maxWidth: width }">
        <div v-if="$slots.header || title" class="nim-dialog-header">
          <slot name="header">
            <h3>{{ title }}</h3>
            <button v-if="closable" class="nim-dialog-close" @click="$emit('close')">✕</button>
          </slot>
        </div>
        <div class="nim-dialog-body">
          <slot />
        </div>
        <div v-if="$slots.footer" class="nim-dialog-footer">
          <slot name="footer" />
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
defineProps({
  show:            { type: Boolean, required: true },
  title:           { type: String,  default: "" },
  width:           { type: String,  default: "560px" },
  closable:        { type: Boolean, default: true },
  closeOnBackdrop: { type: Boolean, default: true },
});
defineEmits(["close"]);
</script>
