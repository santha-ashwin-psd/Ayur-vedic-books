<template>
  <div class="ss-wrap">
    <div
      ref="trigEl" class="ss-trigger"
      :class="{ open, 'ss-disabled': disabled, 'ss-compact': compact }"
      tabindex="0"
      @click="openDD"
      @keydown.enter.prevent="openDD"
      @keydown.space.prevent="openDD"
    >
      <span class="ss-display" :class="{ 'ss-ph': !modelValue && modelValue !== 0 }">
        {{ (modelValue || modelValue === 0) ? displayLabel : placeholder }}
      </span>
      <span v-if="normalized.length > 1" class="ss-caret">
        <IconSvg name="chevD" :size="11" />
      </span>
    </div>

    <Teleport to="body">
      <div v-if="open" class="ss-drop ss-drop-teleport" :style="dropStyle">
        <div class="ss-search-row">
          <input
            ref="inputEl" v-model="q"
            class="ss-search-input"
            placeholder="Type to search…"
            @keydown.escape="open = false"
            @keydown.enter.prevent="filtered.length ? pick(filtered[0]) : (showCreate && onClickCreate())"
          />
        </div>
        <div class="ss-opts">
          <div v-if="!filtered.length && !showCreate" class="ss-no-match">
            {{ normalized.length ? `No matches for "${q}"` : "No options available" }}
          </div>
          <div
            v-for="o in filtered" :key="o.value"
            class="ss-opt"
            :class="{ 'ss-opt-sel': String(o.value) === String(modelValue) }"
            @mousedown.prevent="pick(o)"
          >{{ o.label }}</div>
          <div
            v-if="showCreate"
            class="ss-opt ss-opt-create"
            @mousedown.prevent="onClickCreate"
          >
            <IconSvg name="plus" :size="13" />
            Create <strong style="margin-left:4px">"{{ q.trim() }}"</strong>
          </div>
        </div>
      </div>
    </Teleport>

    <Teleport to="body">
      <div v-if="qcOpen" class="ss-qc-overlay" @mousedown.self="qcOpen = false">
        <div class="ss-qc-modal">
          <div class="ss-qc-header">
            <span>Create New {{ createLabel || createDoctype }}</span>
            <button class="ss-qc-close" @click="qcOpen = false">✕</button>
          </div>
          <div class="ss-qc-body">
            <div v-for="fd in qcFields" :key="fd.f" class="ss-qc-field">
              <label class="ss-qc-label">
                {{ fd.l }}<span v-if="fd.req" style="color:#ef4444;margin-left:2px">*</span>
              </label>
              <input
                :type="fd.type || 'text'"
                v-model="qcForm[fd.f]"
                :placeholder="fd.placeholder || fd.l"
                class="ss-qc-input"
              />
            </div>
          </div>
          <div class="ss-qc-footer">
            <button class="nim-btn" @click="qcOpen = false">Cancel</button>
            <button
              class="nim-btn nim-btn-primary"
              :disabled="qcSaving"
              @click="qcSubmit"
            >
              <span v-if="qcSaving">Saving…</span>
              <span v-else>Create &amp; Select</span>
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmounted } from "vue";
import IconSvg from "./IconSvg.vue";
import { apiSave } from "../api/client.js";
import { useToast } from "../composables/useToast.js";

const { toast } = useToast();

const props = defineProps({
  modelValue:    { default: "" },
  options:       { type: Array,   default: () => [] },
  valueKey:      { type: String,  default: "" },
  labelKey:      { type: String,  default: "" },
  placeholder:   { type: String,  default: "— Select —" },
  compact:       { type: Boolean, default: false },
  disabled:      { type: Boolean, default: false },
  createable:    { type: Boolean, default: false },
  createDoctype: { type: String,  default: "" },
  createLabel:   { type: String,  default: "" },
});
const emit = defineEmits(["update:modelValue", "create"]);

// Field configs for built-in quick-create. Mirrors books.js:389-409.
const SS_CREATE_FIELDS = {
  Item: [
    { f: "item_name",     l: "Item Name",  req: true,  type: "text" },
    { f: "item_group",    l: "Item Group", req: false, type: "text" },
    { f: "standard_rate", l: "Rate (₹)",   req: false, type: "number" },
    { f: "stock_uom",     l: "UOM",        req: false, type: "text", placeholder: "Nos" },
  ],
  Customer: [
    { f: "customer_name",  l: "Customer Name", req: true,  type: "text" },
    { f: "customer_group", l: "Group",         req: false, type: "text", placeholder: "All Customer Groups" },
    { f: "mobile_no",      l: "Mobile",        req: false, type: "text" },
  ],
  Supplier: [
    { f: "supplier_name",  l: "Supplier Name", req: true,  type: "text" },
    { f: "supplier_group", l: "Group",         req: false, type: "text", placeholder: "All Supplier Groups" },
  ],
  Warehouse: [
    { f: "warehouse_name", l: "Warehouse Name", req: true,  type: "text" },
    { f: "warehouse_type", l: "Type",           req: false, type: "text", placeholder: "Stores" },
  ],
};

const q         = ref("");
const open      = ref(false);
const inputEl   = ref(null);
const trigEl    = ref(null);
const dropStyle = ref({});

const qcOpen   = ref(false);
const qcSaving = ref(false);
const qcForm   = reactive({});

const normalized = computed(() => {
  const vk = props.valueKey, lk = props.labelKey;
  return (props.options || []).map((o) => {
    if (typeof o === "string") return { value: o, label: o };
    const v = vk ? o[vk] : (o.value !== undefined ? o.value : (o.name !== undefined ? o.name : String(o)));
    const l = lk ? o[lk] : (o.label !== undefined ? o.label : (o.name !== undefined ? o.name : String(o)));
    return { value: v ?? "", label: l ?? v ?? "" };
  });
});

const displayLabel = computed(() => {
  if (!props.modelValue && props.modelValue !== 0) return "";
  const found = normalized.value.find((o) => String(o.value) === String(props.modelValue));
  return found ? found.label : props.modelValue;
});

const filtered = computed(() => {
  const qv = q.value.toLowerCase().trim();
  if (!qv) return normalized.value.slice(0, 150);
  const pre = [], con = [];
  normalized.value.forEach((o) => {
    const l = String(o.label || "").toLowerCase();
    if (l.startsWith(qv)) pre.push(o);
    else if (l.includes(qv)) con.push(o);
  });
  return [...pre, ...con].slice(0, 100);
});

const showCreate = computed(() => {
  if (!props.createable) return false;
  const qv = q.value.trim();
  if (!qv) return false;
  return !normalized.value.some((o) => String(o.label).toLowerCase() === qv.toLowerCase());
});

const qcFields = computed(() =>
  SS_CREATE_FIELDS[props.createDoctype] || [
    { f: "name", l: props.createLabel || props.createDoctype || "Name", req: true, type: "text" },
  ]
);

function calcDropStyle() {
  if (!trigEl.value) return;
  const r = trigEl.value.getBoundingClientRect();
  const spaceBelow = window.innerHeight - r.bottom;
  const goUp = spaceBelow < 260 && r.top > 260;
  dropStyle.value = {
    position: "fixed",
    left:  r.left  + "px",
    width: r.width + "px",
    zIndex: 99999,
    ...(goUp
      ? { bottom: (window.innerHeight - r.top + 4) + "px" }
      : { top:    (r.bottom + 4) + "px" }),
  };
}

function openDD() {
  if (props.disabled) return;
  calcDropStyle();
  open.value = true;
  q.value = "";
  nextTick(() => inputEl.value && inputEl.value.focus());
}

function pick(opt) {
  emit("update:modelValue", opt.value);
  open.value = false;
  q.value = "";
}

function onClickCreate() {
  const typed = q.value.trim();
  open.value = false;
  if (props.createDoctype && SS_CREATE_FIELDS[props.createDoctype]) {
    qcFields.value.forEach((fd) => { qcForm[fd.f] = ""; });
    if (qcFields.value.length) qcForm[qcFields.value[0].f] = typed;
    qcOpen.value = true;
  } else {
    emit("create", typed);
  }
}

async function qcSubmit() {
  const firstReq = qcFields.value.find((fd) => fd.req);
  if (firstReq && !qcForm[firstReq.f]) {
    toast(`${firstReq.l} is required`, "error");
    return;
  }
  qcSaving.value = true;
  try {
    const doctype = props.createDoctype;
    const payload = { doctype };
    qcFields.value.forEach((fd) => {
      if (qcForm[fd.f] !== undefined && qcForm[fd.f] !== "") payload[fd.f] = qcForm[fd.f];
    });
    const res = await apiSave(payload);
    const newName = res?.name || res;
    pick({ value: newName, label: payload[qcFields.value[0].f] || newName });
    qcOpen.value = false;
    toast(`${props.createLabel || doctype} "${newName}" created`, "success");
  } catch (e) {
    toast("Create failed: " + (e?.message || e), "error");
  } finally {
    qcSaving.value = false;
  }
}

function onDoc(e) {
  if (!open.value) return;
  const trig = trigEl.value;
  const drop = document.querySelector(".ss-drop-teleport");
  if (trig && !trig.contains(e.target) && drop && !drop.contains(e.target)) {
    open.value = false;
  }
}

onMounted(()   => document.addEventListener("pointerdown", onDoc, true));
onUnmounted(() => document.removeEventListener("pointerdown", onDoc, true));
</script>
