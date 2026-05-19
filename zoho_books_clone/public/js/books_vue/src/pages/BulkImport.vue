<template>
<div class="b-page">
  <!-- Toolbar -->
  <div class="b-action-bar">
    <div style="display:flex;gap:8px">
      <button v-for="t in TYPES" :key="t.key"
        class="b-pill" :class="{active: dtype===t.key}"
        @click="switchType(t.key)">
        {{t.label}}
      </button>
    </div>
    <div style="margin-left:auto;display:flex;gap:6px">
      <button class="b-btn b-btn-ghost" @click="downloadSample" title="Download sample CSV">
        <span v-html="icon('arrow-down',13)" style="vertical-align:-1px;margin-right:4px"></span> Sample CSV
      </button>
    </div>
  </div>

  <!-- Info banner -->
  <div style="background:linear-gradient(135deg,#EDF2FF,#DBE4FF);border:1px solid #BAC8FF;border-radius:10px;padding:14px 18px;display:flex;gap:12px;align-items:center">
    <span style="font-size:22px">📥</span>
    <div style="font-size:12.5px;color:#3B5BDB">
      <b>Import {{currentType.label}}</b> from a CSV file.
      Download the <button @click="downloadSample" style="background:none;border:none;padding:0;color:#3B5BDB;cursor:pointer;font-weight:700;text-decoration:underline;font-size:12.5px">sample CSV</button>
      for the exact column format. Rows with missing required fields are skipped.
    </div>
  </div>

  <!-- Step 1: Upload -->
  <div v-if="step===1" class="b-card b-card-body">
    <div style="font-size:13.5px;font-weight:700;margin-bottom:14px;color:#1a1a2e">Step 1 — Upload CSV File</div>
    <div
      class="imp-dropzone"
      :class="{dragging}"
      @dragover.prevent="dragging=true"
      @dragleave="dragging=false"
      @drop.prevent="onDrop"
      @click="$refs.fileInput.click()"
    >
      <div style="font-size:32px;margin-bottom:8px">📂</div>
      <div style="font-size:13.5px;font-weight:600;color:#374151;margin-bottom:4px">Click to select or drag &amp; drop CSV</div>
      <div style="font-size:12px;color:#868E96">Only .csv files, UTF-8 encoded</div>
      <input ref="fileInput" type="file" accept=".csv" style="display:none" @change="onFileChange"/>
    </div>
    <div v-if="fileName" style="margin-top:10px;font-size:12.5px;color:#374151">
      Selected: <b>{{fileName}}</b>
      <button @click="clearFile" style="margin-left:8px;background:none;border:none;color:#C92A2A;cursor:pointer;font-size:12px">Remove</button>
    </div>
    <div v-if="parseError" style="margin-top:10px;color:#C92A2A;font-size:12.5px">{{parseError}}</div>
    <div style="margin-top:16px;display:flex;justify-content:flex-end">
      <button class="b-btn b-btn-primary" :disabled="!parsedRows.length" @click="step=2">
        Preview {{parsedRows.length}} row{{parsedRows.length!==1?'s':''}} →
      </button>
    </div>
  </div>

  <!-- Step 2: Preview -->
  <div v-if="step===2" class="b-card" style="padding:0;overflow:hidden">
    <div style="padding:14px 18px;border-bottom:1px solid #F1F3F5;display:flex;align-items:center;justify-content:space-between">
      <div style="font-size:13.5px;font-weight:700;color:#1a1a2e">Step 2 — Preview ({{parsedRows.length}} rows)</div>
      <button class="b-btn b-btn-ghost" @click="step=1" style="font-size:12px">← Back</button>
    </div>
    <div style="overflow-x:auto;max-height:360px;overflow-y:auto">
      <table class="b-table">
        <thead>
          <tr><th v-for="h in headers" :key="h">{{h}}</th></tr>
        </thead>
        <tbody>
          <tr v-for="(row,i) in parsedRows.slice(0,50)" :key="i">
            <td v-for="h in headers" :key="h" style="font-size:12px;white-space:nowrap">{{row[h]||'—'}}</td>
          </tr>
          <tr v-if="parsedRows.length>50">
            <td :colspan="headers.length" style="text-align:center;color:#868E96;font-size:12px;padding:10px">
              … and {{parsedRows.length-50}} more rows (not shown in preview)
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div style="padding:14px 18px;border-top:1px solid #F1F3F5;display:flex;align-items:center;justify-content:space-between">
      <div style="font-size:12.5px;color:#868E96">Importing into: <b>{{dtype}}</b></div>
      <button class="b-btn b-btn-primary" @click="runImport" :disabled="importing">
        <span v-if="importing">Importing…</span>
        <span v-else><span v-html="icon('check',13)" style="vertical-align:-1px;margin-right:4px"></span> Import {{parsedRows.length}} Records</span>
      </button>
    </div>
  </div>

  <!-- Step 3: Results -->
  <div v-if="step===3" class="b-card b-card-body">
    <div style="font-size:13.5px;font-weight:700;margin-bottom:16px;color:#1a1a2e">Step 3 — Import Results</div>
    <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px">
      <div style="background:#EBFBEE;border:1px solid #8CE99A;border-radius:10px;padding:16px;text-align:center">
        <div style="font-size:28px;font-weight:700;color:#2F9E44;font-family:monospace">{{result.created}}</div>
        <div style="font-size:12px;color:#2F9E44;font-weight:600;margin-top:4px">Created</div>
      </div>
      <div style="background:#FFF9DB;border:1px solid #FFD43B;border-radius:10px;padding:16px;text-align:center">
        <div style="font-size:28px;font-weight:700;color:#E67700;font-family:monospace">{{result.skipped}}</div>
        <div style="font-size:12px;color:#E67700;font-weight:600;margin-top:4px">Skipped</div>
      </div>
      <div style="background:#FFF5F5;border:1px solid #FFC9C9;border-radius:10px;padding:16px;text-align:center">
        <div style="font-size:28px;font-weight:700;color:#C92A2A;font-family:monospace">{{result.errors.length}}</div>
        <div style="font-size:12px;color:#C92A2A;font-weight:600;margin-top:4px">Errors</div>
      </div>
    </div>

    <div v-if="result.errors.length" style="margin-bottom:16px">
      <div style="font-size:12.5px;font-weight:700;color:#C92A2A;margin-bottom:8px">Errors ({{result.errors.length}}):</div>
      <div style="max-height:200px;overflow-y:auto;border:1px solid #FFC9C9;border-radius:8px">
        <div v-for="e in result.errors" :key="e.row"
          style="padding:8px 12px;font-size:12px;border-bottom:1px solid #FFF5F5;display:flex;gap:10px">
          <span style="font-weight:600;color:#868E96;flex-shrink:0">Row {{e.row}}:</span>
          <span style="color:#C92A2A">{{e.error}}</span>
        </div>
      </div>
    </div>

    <div style="display:flex;gap:8px;justify-content:flex-end">
      <button class="b-btn b-btn-ghost" @click="resetImport">Import Another File</button>
      <button v-if="result.created>0" class="b-btn b-btn-primary" @click="goToList">
        View {{currentType.label}} →
      </button>
    </div>
  </div>
</div>
</template>

<script setup>
import { ref, computed } from "vue";
import { useRouter } from "vue-router";
import { apiPOST, apiGET } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";

const { toast } = useToast();
const router = useRouter();

const TYPES = [
  { key: "Customer", label: "Customers", route: "/customers" },
  { key: "Supplier", label: "Vendors",   route: "/vendors"   },
  { key: "Item",     label: "Items",     route: "/inventory/items" },
];

const dtype     = ref("Customer");
const step      = ref(1);
const dragging  = ref(false);
const fileName  = ref("");
const parsedRows = ref([]);
const headers   = ref([]);
const parseError = ref("");
const importing  = ref(false);
const result     = ref({ created: 0, skipped: 0, errors: [] });

const currentType = computed(() => TYPES.find(t => t.key === dtype.value));

function switchType(k) {
  dtype.value = k;
  resetImport();
}

function resetImport() {
  step.value = 1;
  fileName.value = "";
  parsedRows.value = [];
  headers.value = [];
  parseError.value = "";
  result.value = { created: 0, skipped: 0, errors: [] };
}

function clearFile() {
  fileName.value = "";
  parsedRows.value = [];
  headers.value = [];
  parseError.value = "";
}

function onDrop(e) {
  dragging.value = false;
  const file = e.dataTransfer.files[0];
  if (file) readFile(file);
}

function onFileChange(e) {
  const file = e.target.files[0];
  if (file) readFile(file);
  e.target.value = "";
}

function readFile(file) {
  if (!file.name.endsWith(".csv")) {
    parseError.value = "Only .csv files are supported";
    return;
  }
  fileName.value = file.name;
  parseError.value = "";
  const reader = new FileReader();
  reader.onload = (e) => parseCSV(e.target.result);
  reader.readAsText(file, "UTF-8");
}

function parseCSV(text) {
  const lines = text.trim().split(/\r?\n/);
  if (lines.length < 2) {
    parseError.value = "CSV must have a header row and at least one data row";
    parsedRows.value = [];
    return;
  }
  const hdrs = lines[0].split(",").map(h => h.trim().replace(/^"|"$/g, ""));
  headers.value = hdrs;
  const rows = [];
  for (let i = 1; i < lines.length; i++) {
    const line = lines[i].trim();
    if (!line) continue;
    const vals = splitCSVLine(line);
    const row = {};
    hdrs.forEach((h, idx) => { row[h] = (vals[idx] || "").trim().replace(/^"|"$/g, ""); });
    rows.push(row);
  }
  if (!rows.length) {
    parseError.value = "No data rows found in CSV";
    parsedRows.value = [];
    return;
  }
  parsedRows.value = rows;
  parseError.value = "";
}

function splitCSVLine(line) {
  const result = [];
  let cur = "", inQuotes = false;
  for (let i = 0; i < line.length; i++) {
    const ch = line[i];
    if (ch === '"') { inQuotes = !inQuotes; }
    else if (ch === "," && !inQuotes) { result.push(cur); cur = ""; }
    else { cur += ch; }
  }
  result.push(cur);
  return result;
}

async function downloadSample() {
  try {
    const csv = await apiGET("zoho_books_clone.api.import_data.get_sample_csv", { doctype: dtype.value });
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `sample_${dtype.value.toLowerCase()}_import.csv`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (e) { toast.error("Could not download sample: " + e.message); }
}

async function runImport() {
  if (!parsedRows.value.length) return;
  importing.value = true;
  try {
    const res = await apiPOST("zoho_books_clone.api.import_data.bulk_import", {
      doctype: dtype.value,
      rows_json: JSON.stringify(parsedRows.value),
    });
    result.value = res;
    step.value = 3;
  } catch (e) { toast.error(e.message || "Import failed"); }
  finally { importing.value = false; }
}

function goToList() {
  router.push(currentType.value.route);
}
</script>

<style scoped>
.imp-dropzone {
  border: 2px dashed #BAC8FF;
  border-radius: 12px;
  padding: 40px 20px;
  text-align: center;
  cursor: pointer;
  transition: background .15s, border-color .15s;
  background: #F8F9FF;
}
.imp-dropzone:hover, .imp-dropzone.dragging {
  background: #EDF2FF;
  border-color: #4C6EF5;
}
</style>
