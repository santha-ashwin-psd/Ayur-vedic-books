<template>
<div class="b-page coa-page">

  <div class="coa-type-strip">
    <div v-for="s in typeStats" :key="s.type"
      class="coa-type-card"
      :class="{active: typeFilter===s.type}"
      :style="'border-left-color:'+s.meta.color+(typeFilter===s.type?';background:'+s.meta.bg:'')"
      @click="typeFilter = typeFilter===s.type?'':s.type">
      <div class="coa-type-lbl" :style="'color:'+s.meta.color">{{s.type}}</div>
      <div class="coa-type-val" :style="'color:'+s.meta.color">{{s.count}}</div>
      <div class="coa-type-sub">{{s.meta.dr?'Normally Dr':'Normally Cr'}} · {{s.total?fmtINR(s.total):'No opening'}}</div>
    </div>
  </div>

  <div class="b-action-bar" style="margin-bottom:14px">
    <div style="display:flex;gap:8px;align-items:center;flex-wrap:wrap">
      <div class="b-search" style="border-radius:20px;padding:6px 12px">
        <span v-html="icon('search',13)"></span>
        <input v-model="searchQ" placeholder="Search account name or code..." style="border:none;outline:none;font-size:13px;background:transparent;width:220px"/>
      </div>
      <button class="b-btn b-btn-ghost" @click="expandAll"><span v-html="icon('chevD',13)"></span> Expand All</button>
      <button class="b-btn b-btn-ghost" @click="collapseAll"><span v-html="icon('chevR',13)"></span> Collapse All</button>
      <button class="b-btn b-btn-ghost" @click="load"><span v-html="icon('refresh',13)"></span> Refresh</button>
    </div>
    <button class="b-btn b-btn-primary" @click="openAdd()"><span v-html="icon('plus',13)"></span> Add Account</button>
  </div>

  <div class="b-card" style="padding:0;overflow:hidden">
    <table class="b-table coa-tbl">
      <thead>
        <tr>
          <th style="width:44%">Account Name</th>
          <th>Type</th>
          <th>Account No.</th>
          <th class="ta-r">Opening Balance</th>
          <th class="ta-r">Balance Type</th>
          <th style="text-align:center;width:90px">Actions</th>
        </tr>
      </thead>
      <tbody>
        <template v-if="loading">
          <tr v-for="n in 8" :key="n">
            <td colspan="6" style="padding:12px 14px"><div class="b-shimmer" style="height:12px"></div></td>
          </tr>
        </template>
        <template v-else-if="flatTree.length===0">
          <tr><td colspan="6" class="b-empty">No accounts found</td></tr>
        </template>
        <template v-else>
          <tr v-for="row in flatTree" :key="row.name"
            class="coa-row"
            :class="row.is_group?'coa-group-row':'coa-leaf-row'"
            @click="openEdit(row.name)">
            <td>
              <div class="coa-tree-cell" :style="'padding-left:'+(14+row.depth*22)+'px'">
                <button v-if="row.is_group && hasChildren(row.name)"
                  class="coa-toggle" :class="{open: expandedGroups.has(row.name)}"
                  @click.stop="toggleGroup(row.name)">
                  <span v-html="icon('chevR',12)"></span>
                </button>
                <span v-else style="width:18px;flex-shrink:0;display:inline-block"></span>
                <span class="coa-dot" :style="'background:'+(TYPE_META_COA[row.root_type]||TYPE_META_COA.Asset).color+';margin-left:6px'"></span>
                <span class="coa-acct-name" :class="{'fw-700':row.is_group}">{{row.account_name||row.name}}</span>
                <span v-if="row.is_group" class="coa-group-chip" :style="'background:'+(TYPE_META_COA[row.root_type]||TYPE_META_COA.Asset).bg+';color:'+(TYPE_META_COA[row.root_type]||TYPE_META_COA.Asset).color">Group</span>
                <span v-if="row.account_type" class="coa-acct-type">{{row.account_type}}</span>
              </div>
            </td>
            <td style="padding:9px 14px">
              <span class="b-badge" :style="'background:'+(TYPE_META_COA[row.root_type]||TYPE_META_COA.Asset).bg+';color:'+(TYPE_META_COA[row.root_type]||TYPE_META_COA.Asset).color">{{row.root_type}}</span>
            </td>
            <td style="padding:9px 14px;font-family:monospace;font-size:12px;color:#868e96">{{row.code||'—'}}</td>
            <td class="ta-r" style="padding:9px 14px;font-family:monospace;font-weight:600" :class="row.opening>0?(row.bal_type==='Debit'?'coa-dr':'coa-cr'):'c-muted'">{{fmtINR(row.opening)}}</td>
            <td class="ta-r" style="padding:9px 14px;font-size:12px;color:#868e96">{{row.opening?row.bal_type:'—'}}</td>
            <td style="text-align:center;padding:8px 14px">
              <div style="display:flex;gap:4px;justify-content:center">
                <button class="b-icon-btn" @click.stop="openEdit(row.name)" title="Edit"><span v-html="icon('edit',14)"></span></button>
                <button v-if="row.source!=='frappe'" class="b-icon-btn danger" @click.stop="confirmDelete(row.name)" title="Delete"><span v-html="icon('trash',14)"></span></button>
              </div>
            </td>
          </tr>
        </template>
      </tbody>
    </table>
  </div>
  <div style="text-align:right;font-size:12px;color:#868e96;padding:6px 4px">{{flatTree.length}} account(s)</div>

  <Teleport to="body">
    <div v-if="drawerOpen" class="coa-drawer-bg" @click.self="drawerOpen=false">
      <div class="coa-drawer-panel">
        <div class="coa-dh">
          <div><div class="coa-dh-title">{{editingName?'Edit Account':'Add Account'}}</div>
          <div class="coa-dh-sub">{{editingName?'Update account details':'Create a new account in the chart'}}</div></div>
          <button class="coa-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="coa-dbody">
          <div class="coa-info-box">
            <span v-html="icon('info',14)"></span>
            <span>Group accounts can have child accounts. Ledger accounts record actual transactions.</span>
          </div>

          <span class="coa-sec-lbl">Account Details</span>
          <div class="coa-fg coa-fg2">
            <div style="grid-column:1/3">
              <label class="coa-lbl">Account Name <span style="color:#c92a2a">*</span></label>
              <input v-model="form.name" class="coa-fi" placeholder="e.g. Cash in Hand, Sales Revenue"/>
            </div>
            <div>
              <label class="coa-lbl">Account Number</label>
              <input v-model="form.code" class="coa-fi" placeholder="e.g. 1001, 4001"/>
            </div>
            <div>
              <label class="coa-lbl">Root Type <span style="color:#c92a2a">*</span></label>
              <select v-model="form.root_type" class="coa-fi" @change="form.account_type=''">
                <option value="">— Select —</option>
                <option value="Asset">Asset</option>
                <option value="Liability">Liability</option>
                <option value="Equity">Equity</option>
                <option value="Income">Income</option>
                <option value="Expense">Expense</option>
              </select>
            </div>
            <div>
              <label class="coa-lbl">Account Type</label>
              <select v-model="form.account_type" class="coa-fi">
                <option value="">— General —</option>
                <option v-for="t in accountTypeOptions" :key="t" :value="t">{{t}}</option>
              </select>
            </div>
            <div>
              <label class="coa-lbl">Parent Account</label>
              <SearchableSelect v-model="form.parent" :options="parentOptions" value-key="name" label-key="account_name" placeholder="— Root level —"/>
            </div>
          </div>

          <div class="coa-fg coa-fg2" style="margin-top:0">
            <div>
              <label class="coa-lbl">Is Group Account?</label>
              <div style="display:flex;align-items:center;gap:14px;margin-top:8px">
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px">
                  <input type="radio" v-model="form.is_group" :value="1" style="accent-color:#3b5bdb"/> Yes
                </label>
                <label style="display:flex;align-items:center;gap:6px;cursor:pointer;font-size:13px">
                  <input type="radio" v-model="form.is_group" :value="0" style="accent-color:#3b5bdb"/> No
                </label>
              </div>
            </div>
            <div>
              <label class="coa-lbl">Balance Sheet Item?</label>
              <select v-model="form.bs_item" class="coa-fi">
                <option :value="1">Yes (Balance Sheet)</option>
                <option :value="0">No (P&amp;L)</option>
              </select>
            </div>
          </div>

          <span class="coa-sec-lbl">Opening Balance</span>
          <div class="coa-fg coa-fg2">
            <div>
              <label class="coa-lbl">Opening Balance (₹)</label>
              <input v-model="form.opening" type="number" min="0" step="0.01" class="coa-fi" placeholder="0.00" style="font-family:monospace"/>
            </div>
            <div>
              <label class="coa-lbl">Balance Type</label>
              <select v-model="form.bal_type" class="coa-fi">
                <option value="Debit">Debit (Dr)</option>
                <option value="Credit">Credit (Cr)</option>
              </select>
            </div>
          </div>

          <div>
            <label class="coa-lbl">Description / Notes</label>
            <textarea v-model="form.notes" class="coa-fi" rows="2" style="resize:vertical" placeholder="Optional description..."></textarea>
          </div>
        </div>
        <div class="coa-dfooter">
          <button class="b-btn b-btn-ghost" @click="drawerOpen=false">Cancel</button>
          <button class="b-btn b-btn-primary" @click="saveAccount" :disabled="drawerSaving" style="min-width:130px">
            {{drawerSaving?'Saving…':'Save Account'}}
          </button>
        </div>
      </div>
    </div>

    <div v-if="showDel" class="coa-drawer-bg" @click.self="showDel=false" style="justify-content:center;align-items:center">
      <div style="background:#fff;border-radius:12px;padding:28px 32px;max-width:420px;width:100%;border:1px solid #e2e8f0">
        <div style="font-size:17px;font-weight:700;margin-bottom:8px">Delete Account?</div>
        <div style="font-size:14px;color:#868e96;margin-bottom:24px;line-height:1.5">
          <strong>{{deleteTarget}}</strong> and all its child accounts will be permanently removed from local data.
        </div>
        <div style="display:flex;gap:10px;justify-content:flex-end">
          <button @click="showDel=false" class="b-btn b-btn-ghost">Keep It</button>
          <button @click="doDelete" class="b-btn" style="background:#c92a2a;color:#fff;border-color:#c92a2a">Yes, Delete</button>
        </div>
      </div>
    </div>
  </Teleport>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiGET, apiPOST, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { fmt, flt } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();

const TYPE_META_COA = {
  Asset:     { color: "#0C8599", bg: "#E0F7FA", dr: true  },
  Liability: { color: "#C92A2A", bg: "#FFE3E3", dr: false },
  Equity:    { color: "#7048E8", bg: "#F3F0FF", dr: false },
  Income:    { color: "#2F9E44", bg: "#EBFBEE", dr: false },
  Expense:   { color: "#E67700", bg: "#FFF3BF", dr: true  },
};
const ACCOUNT_TYPES_COA = {
  Asset:     ["Asset","Bank","Cash","Receivable","Tax"],
  Liability: ["Liability","Payable","Tax"],
  Equity:    ["Equity"],
  Income:    ["Income"],
  Expense:   ["Expense"],
};
const STANDARD_COA_DATA = [
  {name:"Current Assets",code:"1000",root_type:"Asset",account_type:"",is_group:1,parent:"",opening:0,bal_type:"Debit"},
  {name:"Cash in Hand",code:"1001",root_type:"Asset",account_type:"Cash",is_group:0,parent:"Current Assets",opening:50000,bal_type:"Debit"},
  {name:"Bank Accounts",code:"1010",root_type:"Asset",account_type:"Bank",is_group:1,parent:"Current Assets",opening:0,bal_type:"Debit"},
  {name:"HDFC Current Account",code:"1011",root_type:"Asset",account_type:"Bank",is_group:0,parent:"Bank Accounts",opening:500000,bal_type:"Debit"},
  {name:"Accounts Receivable",code:"1100",root_type:"Asset",account_type:"Receivable",is_group:0,parent:"Current Assets",opening:0,bal_type:"Debit"},
  {name:"Fixed Assets",code:"1500",root_type:"Asset",account_type:"",is_group:1,parent:"",opening:0,bal_type:"Debit"},
  {name:"Current Liabilities",code:"2000",root_type:"Liability",account_type:"",is_group:1,parent:"",opening:0,bal_type:"Credit"},
  {name:"Accounts Payable",code:"2100",root_type:"Liability",account_type:"Payable",is_group:0,parent:"Current Liabilities",opening:0,bal_type:"Credit"},
  {name:"Share Capital",code:"3000",root_type:"Equity",account_type:"Equity",is_group:0,parent:"",opening:1000000,bal_type:"Credit"},
  {name:"Retained Earnings",code:"3100",root_type:"Equity",account_type:"Retained Earnings",is_group:0,parent:"",opening:0,bal_type:"Credit"},
  {name:"Revenue",code:"4000",root_type:"Income",account_type:"",is_group:1,parent:"",opening:0,bal_type:"Credit"},
  {name:"Sales Revenue",code:"4001",root_type:"Income",account_type:"Income Account",is_group:0,parent:"Revenue",opening:0,bal_type:"Credit"},
  {name:"Operating Expenses",code:"5100",root_type:"Expense",account_type:"",is_group:1,parent:"",opening:0,bal_type:"Debit"},
  {name:"Salaries & Wages",code:"5101",root_type:"Expense",account_type:"Expense Account",is_group:0,parent:"Operating Expenses",opening:0,bal_type:"Debit"},
];

const allAccounts    = ref([]);
const loading        = ref(true);
const expandedGroups = ref(new Set());
const typeFilter     = ref("");
const searchQ        = ref("");
const expandTick     = ref(0);
const drawerOpen     = ref(false);
const editingName    = ref(null);
const drawerSaving   = ref(false);
const showDel        = ref(false);
const deleteTarget   = ref(null);

const form = reactive({
  name: "", code: "", root_type: "", account_type: "", parent: "",
  is_group: 0, bs_item: 1, opening: "", bal_type: "Debit", notes: "",
});

const typeStats = computed(() =>
  ["Asset","Liability","Equity","Income","Expense"].map((t) => {
    const accts = allAccounts.value.filter((a) => a.root_type === t && !a.is_group);
    const tot = accts.reduce((s, a) => s + Number(a.opening || 0), 0);
    return { type: t, count: accts.length, total: tot, meta: TYPE_META_COA[t] };
  })
);

const accountTypeOptions = computed(() => ACCOUNT_TYPES_COA[form.root_type] || []);
const parentOptions      = computed(() => allAccounts.value.filter((a) => a.is_group));

const flatTree = computed(() => {
  // eslint-disable-next-line no-unused-expressions
  expandTick.value;
  const q = searchQ.value.toLowerCase().trim();
  const tf = typeFilter.value;
  if (q) {
    return allAccounts.value
      .filter((a) => {
        const nm = (a.account_name || a.name).toLowerCase();
        const cd = (a.code || "").toLowerCase();
        return (!tf || a.root_type === tf) && (nm.includes(q) || cd.includes(q));
      })
      .map((a) => ({ ...a, depth: 0 }));
  }
  function walk(parent, depth) {
    const children = allAccounts.value.filter((a) => {
      const par = a.parent || "";
      return par === parent && (!tf || a.root_type === tf);
    });
    const rows = [];
    children.forEach((a) => {
      rows.push({ ...a, depth });
      const has = allAccounts.value.some((c) => (c.parent || "") === a.name);
      if (a.is_group && has && expandedGroups.value.has(a.name)) {
        rows.push(...walk(a.name, depth + 1));
      }
    });
    return rows;
  }
  return walk("", 0);
});

function toggleGroup(name) {
  if (expandedGroups.value.has(name)) expandedGroups.value.delete(name);
  else expandedGroups.value.add(name);
  expandTick.value++;
}

function expandAll() {
  allAccounts.value.filter((a) => a.is_group).forEach((a) => expandedGroups.value.add(a.name));
  expandTick.value++;
}

function collapseAll() {
  expandedGroups.value.clear();
  expandTick.value++;
}

function hasChildren(name) {
  return allAccounts.value.some((c) => (c.parent || "") === name);
}

function fmtINR(v) {
  if (!v && v !== 0) return "—";
  const n = Number(v);
  if (n === 0) return "—";
  return "₹" + Math.abs(n).toLocaleString("en-IN", { minimumFractionDigits: 2 });
}

async function load() {
  loading.value = true;
  try {
    let frappeAccts = [];
    try {
      const company = await resolveCompany();
      const res = await apiGET("zoho_books_clone.api.books_data.get_chart_of_accounts", { company });
      frappeAccts = Array.isArray(res) ? res : [];
      if (company) {
        const nameSet = new Set(frappeAccts.map((a) => a.account_name || a.name));
        frappeAccts = frappeAccts.filter((a) => {
          const nm = a.account_name || a.name;
          return nm.endsWith(" - " + company) || !nameSet.has(nm + " - " + company);
        });
      }
    } catch {}

    if (frappeAccts && frappeAccts.length) {
      const guessRootType = (a) => {
        if (a.root_type) return a.root_type;
        const t = (a.account_type || "").toLowerCase().trim();
        if (t === "income" || t === "other income" || t.includes("income account")) return "Income";
        if (t === "expense" || t === "other expense" || t.includes("expense account") || t === "cost of goods sold" || t === "depreciation") return "Expense";
        if (t === "payable" || t === "liability" || t === "other liability" || t === "credit card" || t === "current liability") return "Liability";
        if (t === "equity" || t === "retained earnings") return "Equity";
        return "Asset";
      };
      allAccounts.value = frappeAccts.map((a) => ({
        name: a.name,
        account_name: a.account_name || a.name,
        code: a.account_number || "",
        root_type: guessRootType(a),
        account_type: a.account_type || "",
        is_group: a.is_group ? 1 : 0,
        parent: a.parent_account || "",
        opening: Number(a.opening_balance || 0),
        bal_type: a.balance_must_be || "Debit",
        source: "frappe",
      }));
      try { localStorage.removeItem("books_coa"); } catch {}
    } else {
      const saved = (() => { try { const s = localStorage.getItem("books_coa"); return s ? JSON.parse(s) : null; } catch { return null; } })();
      if (saved && saved.length) {
        allAccounts.value = saved;
      } else {
        allAccounts.value = STANDARD_COA_DATA.map((a) => ({ ...a, account_name: a.name, source: "local" }));
        try { localStorage.setItem("books_coa", JSON.stringify(allAccounts.value)); } catch {}
      }
    }
    allAccounts.value.filter((a) => a.is_group && !a.parent).forEach((a) => expandedGroups.value.add(a.name));
    expandTick.value++;
  } finally {
    loading.value = false;
  }
}

function openAdd(parentName) {
  editingName.value = null;
  Object.assign(form, { name: "", code: "", root_type: "", account_type: "", parent: parentName || "", is_group: 0, bs_item: 1, opening: "", bal_type: "Debit", notes: "" });
  drawerOpen.value = true;
}

function openEdit(acctName) {
  const a = allAccounts.value.find((x) => x.name === acctName);
  if (!a) return;
  editingName.value = acctName;
  Object.assign(form, {
    name: a.account_name || a.name,
    code: a.code || "",
    root_type: a.root_type || "",
    account_type: a.account_type || "",
    parent: a.parent || "",
    is_group: a.is_group ? 1 : 0,
    bs_item: ["Asset", "Liability", "Equity"].includes(a.root_type) ? 1 : 0,
    opening: a.opening || "",
    bal_type: a.bal_type || "Debit",
    notes: a.notes || "",
  });
  drawerOpen.value = true;
}

async function saveAccount() {
  if (!form.name.trim())  { toast("Account name is required", "error"); return; }
  if (!form.root_type)    { toast("Root Type is required", "error");    return; }
  drawerSaving.value = true;
  try {
    const payload = {
      account_name: form.name.trim(),
      account_number: form.code.trim(),
      root_type: form.root_type,
      account_type: form.account_type,
      parent_account: form.parent || "",
      is_group: form.is_group ? 1 : 0,
      opening_balance: flt(form.opening),
      balance_must_be: form.bal_type,
    };
    if (editingName.value) {
      try {
        await apiPOST("zoho_books_clone.api.books_data.save_account", { op: "update", name: editingName.value, ...payload });
      } catch (e) { toast(e.message || "Frappe update failed", "error"); }
      const idx = allAccounts.value.findIndex((x) => x.name === editingName.value);
      if (idx >= 0) {
        allAccounts.value[idx] = { ...allAccounts.value[idx], account_name: form.name.trim(), code: form.code.trim(), root_type: form.root_type, account_type: form.account_type, parent: form.parent, is_group: form.is_group ? 1 : 0, opening: flt(form.opening), bal_type: form.bal_type, notes: form.notes };
      }
      toast("Account updated", "success");
    } else {
      let newName = form.name.trim();
      try {
        const res = await apiPOST("zoho_books_clone.api.books_data.save_account", { op: "create", ...payload });
        if (res && res.name) newName = res.name;
      } catch (e) { toast(e.message || "Frappe create failed", "error"); }
      allAccounts.value.push({ name: newName, account_name: form.name.trim(), code: form.code.trim(), root_type: form.root_type, account_type: form.account_type, parent: form.parent, is_group: form.is_group ? 1 : 0, opening: flt(form.opening), bal_type: form.bal_type, notes: form.notes, source: "frappe" });
      if (form.is_group) { expandedGroups.value.add(newName); expandTick.value++; }
      toast("Account created", "success");
    }
    drawerOpen.value = false;
    await load();
  } catch (e) {
    toast(e.message || "Save failed", "error");
  } finally {
    drawerSaving.value = false;
  }
}

function confirmDelete(name) { deleteTarget.value = name; showDel.value = true; }

async function doDelete() {
  const name = deleteTarget.value;
  try {
    await apiPOST("zoho_books_clone.api.books_data.save_account", { op: "delete", name });
  } catch (e) {
    toast(e.message || "Delete failed in Frappe", "error");
  }
  allAccounts.value = allAccounts.value.filter((a) => a.name !== name && a.parent !== name);
  expandTick.value++;
  showDel.value = false;
  deleteTarget.value = null;
  toast("Account deleted", "success");
  await load();
}

onMounted(load);
</script>
