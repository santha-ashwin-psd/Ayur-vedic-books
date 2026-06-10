<template>
  <Teleport to="body">
    <div v-if="state.open" class="rnd-backdrop" @click.self="onCancel">
      <div class="rnd-dialog">
        <div class="rnd-header" :style="`background:${headerBg}`">
          <span class="rnd-title">
            {{ state.kind === "debit" ? "Debit Note" : "Credit Note" }} — {{ state.parentName }}
          </span>
          <button class="rnd-close" @click="onCancel" :disabled="saving">✕</button>
        </div>
        <div class="rnd-body">
          <div v-if="existing.length" class="rnd-warn">
            <strong>⚠ Existing {{ state.kind === "debit" ? "debit" : "credit" }} notes:</strong>
            <span v-for="n in existing" :key="n.name" class="rnd-warn-tag">
              {{ n.name }} ({{ fmt(Math.abs(n.grand_total)) }})
            </span>
            <div class="rnd-warn-sub">
              Creating another will further reduce the {{ state.kind === "debit" ? "bill" : "invoice" }} balance.
            </div>
          </div>

          <div class="rnd-grid">
            <div class="rnd-field">
              <label class="rnd-lbl">Date <span class="rnd-req">*</span></label>
              <input v-model="form.date" type="date" class="rnd-input" />
            </div>
            <div class="rnd-field">
              <label class="rnd-lbl">Reason <span class="rnd-req">*</span></label>
              <select v-model="form.reason" class="rnd-input">
                <option>Price Adjustment</option>
                <option>Goods Returned</option>
                <option>Damaged Goods</option>
                <option v-if="state.kind === 'credit'">Duplicate Invoice</option>
                <option v-if="state.kind === 'debit'">Vendor Overcharge</option>
                <option>Other</option>
              </select>
            </div>
          </div>

          <div>
            <label class="rnd-lbl rnd-section">Items to {{ state.kind === "debit" ? "Debit" : "Credit" }}</label>
            <div class="rnd-table">
              <div class="rnd-th">
                <span>Item</span>
                <span style="text-align:center">Qty</span>
                <span style="text-align:right">Rate</span>
                <span style="text-align:right">Amount</span>
              </div>
              <div v-for="(line, i) in lines" :key="i" class="rnd-tr">
                <span class="rnd-item">{{ line.item_name || line.item_code }}</span>
                <input
                  v-model.number="line.qty" type="number" :max="line.maxQty" min="0" step="0.001"
                  class="rnd-qty" @input="recalc(line)"
                />
                <span class="rnd-num">{{ fmt(line.rate) }}</span>
                <span class="rnd-num rnd-amt">{{ fmt(line.amount) }}</span>
              </div>
            </div>
            <div class="rnd-total">
              {{ state.kind === "debit" ? "Debit" : "Credit" }} Total:
              <strong :style="`color:${state.kind === 'debit' ? '#7c2d12' : '#dc2626'}`">{{ fmt(grandTotal) }}</strong>
            </div>
          </div>

          <div class="rnd-field">
            <label class="rnd-lbl">Notes <span class="rnd-opt">(optional)</span></label>
            <input v-model="form.notes" class="rnd-input" placeholder="Internal note or message…" />
          </div>
        </div>
        <div class="rnd-footer">
          <button class="rnd-btn rnd-btn-ghost" @click="onCancel" :disabled="saving">Cancel</button>
          <button
            class="rnd-btn rnd-btn-danger"
            :disabled="saving || grandTotal <= 0"
            @click="onSave"
          >
            {{ saving ? "Creating…" : `Issue ${state.kind === "debit" ? "Debit" : "Credit"} Note  ${fmt(grandTotal)}` }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { reactive, ref, computed, watch } from "vue";
import { apiGET, apiPOST } from "../api/client.js";
import { useReturnNote } from "../composables/useReturnNote.js";
import { useToast } from "../composables/useToast.js";

const { state, complete, cancel } = useReturnNote();
const { toast } = useToast();

const saving = ref(false);
const existing = ref([]);
const lines = ref([]);
const form = reactive({ date: "", reason: "Price Adjustment", notes: "" });

const headerBg = computed(() =>
  state.kind === "debit"
    ? "linear-gradient(135deg,#7c2d12,#ea580c)"
    : "linear-gradient(135deg,#7f1d1d,#dc2626)"
);
const grandTotal = computed(() => lines.value.reduce((s, l) => s + Number(l.amount || 0), 0));

function fmt(v) {
  return "₹" + Number(v || 0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
function recalc(line) {
  line.amount = Math.round(Number(line.qty || 0) * Number(line.rate || 0) * 100) / 100;
}

watch(() => state.open, async (open) => {
  if (!open) return;
  Object.assign(form, {
    date: new Date().toISOString().slice(0, 10),
    reason: state.kind === "debit" ? "Vendor Overcharge" : "Price Adjustment",
    notes: "",
  });
  lines.value = (state.items || []).map((it) => ({
    item_code: it.item_code || "",
    item_name: it.item_name || it.item_code || "",
    description: it.description || "",
    maxQty: Number(it.qty || 0),
    qty: Number(it.qty || 0),
    rate: Number(it.rate || 0),
    amount: Math.round(Number(it.qty || 0) * Number(it.rate || 0) * 100) / 100,
  }));
  existing.value = [];
  if (state.existingEndpoint && state.parentName) {
    try {
      const params = { [state.paramKey]: state.parentName };
      const r = await apiGET(state.existingEndpoint, params);
      existing.value = r || [];
    } catch { existing.value = []; }
  }
});

async function onSave() {
  if (!form.date) { toast("Please pick a date", "error"); return; }
  const valid = lines.value.filter((l) => Number(l.qty) > 0);
  if (!valid.length) { toast("At least one item must have qty > 0", "error"); return; }

  saving.value = true;
  try {
    const items = valid.map((l) => ({
      item_code: l.item_code,
      item_name: l.item_name,
      description: l.description,
      qty: Number(l.qty),
      rate: Number(l.rate),
      amount: Number(l.amount),
    }));
    const payload = {
      [state.partyKey]: state.party,
      [state.parentKey]: state.parentName,
      date: form.date,
      reason: form.reason,
      notes: form.notes || "",
      items: JSON.stringify(items),
      taxes: "[]",
    };
    const r = await apiPOST(state.createEndpoint, payload);
    const noteName = r?.credit_note || r?.debit_note || r?.name || "";
    toast((state.kind === "debit" ? "Debit Note" : "Credit Note") + " created: " + noteName, "success");
    complete({ noteName });
  } catch (e) {
    toast("Failed: " + (e.message || ""), "error");
  }
  saving.value = false;
}
function onCancel() { if (saving.value) return; cancel(); }
</script>

<style scoped>
.rnd-backdrop {
  position: fixed; inset: 0; background: rgba(15,23,42,.5);
  z-index: 10000; display: flex; align-items: center; justify-content: center;
}
.rnd-dialog {
  background: #fff; border-radius: 12px; width: 580px; max-width: 96vw;
  max-height: 92vh; display: flex; flex-direction: column;
  box-shadow: 0 12px 40px rgba(0,0,0,.2); overflow: hidden;
  animation: rnd-in .2s cubic-bezier(.34,1.56,.64,1);
  font-family: 'Inter', 'Lato', system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
@keyframes rnd-in { from { opacity: 0; transform: scale(.96) translateY(8px); } to { opacity: 1; transform: none; } }
.rnd-header {
  display: flex; align-items: center; justify-content: space-between;
  padding: 14px 18px; flex-shrink: 0;
}
.rnd-title { font-size: 15px; font-weight: 700; color: #fff; font-family: inherit; }
.rnd-close {
  background: rgba(255,255,255,.18); border: none; cursor: pointer; font-size: 14px; color: #fff;
  width: 28px; height: 28px; border-radius: 6px;
}
.rnd-close:hover { background: rgba(255,255,255,.28); }
.rnd-close:disabled { opacity: .4; cursor: not-allowed; }
.rnd-body { padding: 16px 18px; flex: 1; overflow-y: auto; display: flex; flex-direction: column; gap: 12px; }
.rnd-warn {
  background: #fef3c7; border: 1px solid #fcd34d; border-radius: 6px;
  padding: 10px 12px; font-size: 12.5px; color: #92400e;
}
.rnd-warn-tag { margin-left: 6px; font-size: 12px; }
.rnd-warn-sub { margin-top: 4px; font-size: 11.5px; }
.rnd-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.rnd-field { display: flex; flex-direction: column; gap: 4px; }
.rnd-lbl { font-size: 12px; font-weight: 600; color: #374151; }
.rnd-section { margin-bottom: 6px; display: block; }
.rnd-opt { color: #9ca3af; font-weight: 400; }
.rnd-req { color: #ef4444; }
.rnd-input {
  border: 1px solid #e2e8f0; border-radius: 6px; padding: 7px 10px;
  font-size: 13px; outline: none; background: #fff; font-family: inherit;
  width: 100%; box-sizing: border-box;
}
.rnd-input:focus { border-color: #2563eb; box-shadow: 0 0 0 2px rgba(37,99,235,.08); }
.rnd-table {
  border: 1px solid #e2e8f0; border-radius: 6px; overflow: hidden;
}
.rnd-th {
  display: grid; grid-template-columns: 2fr 80px 80px 90px; gap: 8px;
  padding: 7px 12px; background: #f8fafc; font-size: 11px;
  font-weight: 700; text-transform: uppercase; color: #6b7280;
}
.rnd-tr {
  display: grid; grid-template-columns: 2fr 80px 80px 90px; gap: 8px;
  padding: 7px 12px; border-top: 1px solid #f0f2f5; align-items: center; font-size: 13px;
}
.rnd-item { color: #374151; }
.rnd-qty {
  border: 1px solid #e2e8f0; border-radius: 4px; padding: 3px 6px;
  font-size: 12px; text-align: center; outline: none; font-family: inherit;
}
.rnd-qty:focus { border-color: #2563eb; }
.rnd-num { text-align: right;color: #6b7280; }
.rnd-amt { font-weight: 600; color: #111827; }
.rnd-total {
  text-align: right; padding: 8px 12px 0; font-size: 13px;
}
.rnd-footer {
  display: flex; justify-content: flex-end; gap: 8px;
  padding: 12px 18px; border-top: 1px solid #e5e7eb; flex-shrink: 0;
}
.rnd-btn { font: inherit; font-size: 13px; padding: 8px 16px; border-radius: 8px; border: 1px solid transparent; cursor: pointer; font-weight: 600; }
.rnd-btn:disabled { opacity: .5; cursor: not-allowed; }
.rnd-btn-ghost { background: #fff; border-color: #e5e7eb; color: #374151; }
.rnd-btn-ghost:hover:not(:disabled) { background: #f9fafb; }
.rnd-btn-danger { background: #dc2626; color: #fff; border-color: #dc2626; }
.rnd-btn-danger:hover:not(:disabled) { background: #b91c1c; }
</style>
