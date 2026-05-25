<template>
  <div class="pg-wrap" v-if="totalItems > 0">
    <!-- Left: count summary -->
    <div class="pg-summary">
      Showing <strong>{{ rangeStart }}</strong>–<strong>{{ rangeEnd }}</strong>
      of <strong>{{ totalItems }}</strong>
    </div>

    <!-- Middle: page nav -->
    <div class="pg-nav">
      <button class="pg-btn" :disabled="page === 1" @click="$emit('update:page', 1)" title="First page">«</button>
      <button class="pg-btn" :disabled="page === 1" @click="$emit('update:page', page - 1)" title="Previous">‹</button>

      <span v-for="p in pageList" :key="p.k" class="pg-page-cell">
        <button
          v-if="p.kind === 'page'"
          class="pg-btn pg-page"
          :class="{ active: p.n === page }"
          @click="$emit('update:page', p.n)"
        >{{ p.n }}</button>
        <span v-else class="pg-ellipsis">…</span>
      </span>

      <button class="pg-btn" :disabled="page === totalPages" @click="$emit('update:page', page + 1)" title="Next">›</button>
      <button class="pg-btn" :disabled="page === totalPages" @click="$emit('update:page', totalPages)" title="Last page">»</button>
    </div>

    <!-- Right: page size -->
    <div class="pg-size">
      <span class="pg-size-lbl">Rows</span>
      <select :value="pageSize" @change="$emit('update:pageSize', Number($event.target.value))" class="pg-select">
        <option v-for="s in sizeOptions" :key="s" :value="s">{{ s }}</option>
      </select>
    </div>
  </div>
</template>

<script setup>
import { computed } from "vue";

const props = defineProps({
  page:        { type: Number, required: true },
  pageSize:    { type: Number, required: true },
  totalItems:  { type: Number, required: true },
  sizeOptions: { type: Array, default: () => [10, 25, 50, 100] },
});

defineEmits(["update:page", "update:pageSize"]);

const totalPages = computed(() => Math.max(1, Math.ceil(props.totalItems / props.pageSize)));
const rangeStart = computed(() => props.totalItems === 0 ? 0 : (props.page - 1) * props.pageSize + 1);
const rangeEnd   = computed(() => Math.min(props.totalItems, props.page * props.pageSize));

/**
 * Builds a list like: [1, …, 4, 5, 6, …, 12]
 * Keeps the current page surrounded by a 1-page neighborhood + first/last anchors.
 */
const pageList = computed(() => {
  const cur = props.page;
  const max = totalPages.value;
  if (max <= 7) {
    return Array.from({ length: max }, (_, i) => ({ kind: "page", n: i + 1, k: `p${i + 1}` }));
  }
  const out = [];
  const push = (n) => out.push({ kind: "page", n, k: `p${n}` });
  const gap = (id) => out.push({ kind: "gap", k: `g${id}` });

  push(1);
  if (cur > 4) gap("L");
  for (let n = Math.max(2, cur - 1); n <= Math.min(max - 1, cur + 1); n++) push(n);
  if (cur < max - 3) gap("R");
  push(max);
  return out;
});
</script>

<style scoped>
.pg-wrap {
  display: flex; align-items: center; justify-content: space-between; gap: 16px;
  padding: 12px 16px; background: #fff; border: 1px solid #e5e7eb; border-radius: 10px;
  font-size: 13px; color: #374151;
}
.pg-summary { font-size: 12.5px; color: #6b7280; }
.pg-summary strong { color: #111827; font-weight: 700; }

.pg-nav { display: flex; align-items: center; gap: 2px; }
.pg-page-cell { display: inline-flex; align-items: center; }
.pg-btn {
  min-width: 30px; height: 30px; padding: 0 8px;
  background: #fff; border: 1px solid #e2e8f0; border-radius: 6px;
  font: inherit; font-size: 12.5px; font-weight: 600; color: #374151;
  cursor: pointer; transition: border-color .15s, background .15s, color .15s;
  display: inline-flex; align-items: center; justify-content: center;
}
.pg-btn:hover:not(:disabled) { background: #f1f5f9; border-color: #1a6ef7; color: #1a6ef7; }
.pg-btn:disabled { opacity: .35; cursor: not-allowed; }
.pg-btn.pg-page.active {
  background: #1a6ef7; color: #fff; border-color: #1a6ef7;
}
.pg-btn.pg-page.active:hover { background: #1d4ed8; }
.pg-ellipsis { padding: 0 4px; color: #9ca3af; font-weight: 600; user-select: none; }

.pg-size { display: flex; align-items: center; gap: 6px; }
.pg-size-lbl { font-size: 12px; color: #6b7280; font-weight: 500; }
.pg-select {
  border: 1px solid #e2e8f0; border-radius: 6px; padding: 4px 8px;
  font: inherit; font-size: 12.5px; color: #374151; outline: none; cursor: pointer; background: #fff;
}
.pg-select:focus { border-color: #1a6ef7; box-shadow: 0 0 0 2px rgba(26,110,247,.15); }

@media (max-width: 720px) {
  .pg-wrap { flex-direction: column; align-items: stretch; gap: 10px; }
  .pg-nav { justify-content: center; }
  .pg-summary, .pg-size { text-align: center; justify-content: center; }
}
</style>
