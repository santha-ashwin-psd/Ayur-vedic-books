<template>
<div class="b-page" style="display:grid;grid-template-columns:280px 1fr;gap:16px;align-items:start">
  <!-- Left: Tree panel -->
  <div class="b-card" style="padding:0;overflow:hidden;position:sticky;top:0">
    <div style="padding:12px 16px;border-bottom:1px solid #E2E8F0;display:flex;align-items:center;justify-content:space-between;background:#F8FAFC">
      <span style="font-size:13px;font-weight:700;color:#1a1d23">Item Groups</span>
      <button class="b-btn b-btn-primary" style="padding:5px 10px;font-size:12px" @click="newGroup('All Item Groups')">
        <span v-html="icon('plus',12)"></span> New
      </button>
    </div>
    <div v-if="loading" style="padding:20px"><div class="b-shimmer" style="height:12px;margin-bottom:8px"></div><div class="b-shimmer" style="height:12px;width:70%"></div></div>
    <div v-else style="padding:6px 0;max-height:calc(100vh - 200px);overflow-y:auto">
      <template v-for="node in tree" :key="node.name">
        <div @click="selectGroup(node)" style="display:flex;align-items:center;gap:6px;padding:7px 14px;cursor:pointer;transition:background .1s;border-left:3px solid transparent"
          :style="selected===node.name?{background:'#EEF2FF',borderLeftColor:'#3B5BDB',color:'#3B5BDB'}:{color:'#374151'}">
          <span v-if="node.children&&node.children.length" @click.stop="toggleExpand(node.name)"
            style="font-size:10px;color:#868E96;width:14px;text-align:center">{{expanded.has(node.name)?'▼':'▶'}}</span>
          <span v-else style="width:14px"></span>
          <span v-html="icon(node.is_group?'folder':'file',13)" style="flex-shrink:0;opacity:.7"></span>
          <span style="font-size:13px;font-weight:600;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{node.name}}</span>
          <span v-if="node.children&&node.children.length" style="font-size:10px;color:#ADB5BD;background:#F1F3F5;padding:1px 6px;border-radius:8px">{{node.children.length}}</span>
        </div>
        <template v-if="expanded.has(node.name)">
          <div v-for="child in (node.children||[])" :key="child.name"
            @click="selectGroup(child)" style="display:flex;align-items:center;gap:6px;padding:6px 14px 6px 36px;cursor:pointer;transition:background .1s;border-left:3px solid transparent"
            :style="selected===child.name?{background:'#EEF2FF',borderLeftColor:'#3B5BDB',color:'#3B5BDB'}:{color:'#495057'}">
            <span v-html="icon('file',12)" style="flex-shrink:0;opacity:.6"></span>
            <span style="font-size:12.5px;flex:1;min-width:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{child.name}}</span>
            <button @click.stop="newGroup(child.name)" style="background:none;border:none;cursor:pointer;color:#3B5BDB;font-size:10px;padding:2px 4px" title="Add child group">+</button>
          </div>
        </template>
      </template>
    </div>
  </div>

  <!-- Right: Detail panel -->
  <div class="b-card b-card-body">
    <div v-if="!formActive" style="text-align:center;padding:60px 20px;color:#868E96">
      <div style="font-size:40px;margin-bottom:12px">📁</div>
      <div style="font-size:14px;font-weight:600;margin-bottom:4px">Select a group to edit</div>
      <div style="font-size:13px">or click <strong>+ New</strong> to create one</div>
    </div>
    <template v-else>
      <div style="font-size:15px;font-weight:700;margin-bottom:18px;color:#1a1d23">
        {{drawerMode==='edit'?'Edit Group':'New Item Group'}}
      </div>
      <div style="display:grid;gap:14px;max-width:480px">
        <div>
          <label class="nim-label">Group Name <span style="color:#C92A2A">*</span></label>
          <input class="nim-input" v-model="form.name" :disabled="drawerMode==='edit'" placeholder="e.g. Electronics"/>
        </div>
        <div>
          <label class="nim-label">Parent Group</label>
          <select class="nim-input" v-model="form.parent_item_group">
            <option value="">— None (Root) —</option>
            <option v-for="g in allGroups" :key="g.name" :value="g.name">{{g.name}}</option>
          </select>
        </div>
        <div>
          <label class="nim-label">Description</label>
          <textarea class="nim-input" v-model="form.description" rows="3" placeholder="Optional description..." style="resize:vertical"></textarea>
        </div>
        <div style="display:flex;align-items:center;gap:10px;padding:12px;background:#F8FAFC;border-radius:8px;border:1px solid #E2E8F0">
          <input type="checkbox" :checked="!!form.is_group" @change="form.is_group=($event.target.checked?1:0)" style="width:16px;height:16px;accent-color:#3B5BDB"/>
          <div><div style="font-size:13px;font-weight:600;color:#374151">Is a Group</div><div style="font-size:11.5px;color:#868E96">Group nodes can have child item groups</div></div>
        </div>
      </div>
      <div style="display:flex;gap:8px;margin-top:22px">
        <button class="b-btn b-btn-primary" :disabled="saving" @click="saveGroup">{{saving?'Saving…':(drawerMode==='edit'?'Update Group':'Create Group')}}</button>
        <button v-if="drawerMode==='edit'" class="b-btn b-btn-ghost" style="border-color:rgba(201,42,42,.4);color:#C92A2A" @click="deleteGroup">Delete</button>
        <button class="b-btn b-btn-ghost" @click="newGroup(form.parent_item_group||'All Item Groups')">+ New Child Group</button>
      </div>
    </template>
  </div>
</div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiDelete } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { useConfirm } from "../composables/useConfirm.js";
import { icon } from "../utils/icons.js";

const { toast }   = useToast();
const { confirm } = useConfirm();

const allGroups = ref([]);
const loading   = ref(true);
const saving    = ref(false);
const selected  = ref(null);
const expanded  = ref(new Set(["All Item Groups"]));

const form       = reactive({ name: "", parent_item_group: "All Item Groups", is_group: 0, description: "" });
const drawerMode = ref("add");
const formActive = ref(false);

const GROUP_DEFAULTS = [
  { name: "All Item Groups",  parent_item_group: "",                is_group: 1, description: "Root" },
  { name: "Products",         parent_item_group: "All Item Groups", is_group: 0, description: "" },
  { name: "Services",         parent_item_group: "All Item Groups", is_group: 0, description: "" },
  { name: "Raw Materials",    parent_item_group: "All Item Groups", is_group: 0, description: "" },
  { name: "Finished Goods",   parent_item_group: "All Item Groups", is_group: 0, description: "" },
];

async function load() {
  loading.value = true;
  try {
    const rows = await apiList("Item Group", {
      fields: ["name", "parent_item_group", "is_group", "description"],
      order: "name asc", limit: 200,
    });
    allGroups.value = rows && rows.length ? rows : GROUP_DEFAULTS;
  } catch { allGroups.value = GROUP_DEFAULTS; }
  loading.value = false;
}

const tree = computed(() => {
  const map = {};
  allGroups.value.forEach((g) => { map[g.name] = { ...g, children: [] }; });
  const roots = [];
  allGroups.value.forEach((g) => {
    if (!g.parent_item_group || !map[g.parent_item_group]) roots.push(map[g.name]);
    else map[g.parent_item_group].children.push(map[g.name]);
  });
  return roots;
});

function toggleExpand(name) {
  const s = new Set(expanded.value);
  s.has(name) ? s.delete(name) : s.add(name);
  expanded.value = s;
}

function selectGroup(g) {
  selected.value = g.name;
  drawerMode.value = "edit";
  formActive.value = true;
  Object.assign(form, {
    name: g.name,
    parent_item_group: g.parent_item_group || "",
    is_group: g.is_group ? 1 : 0,
    description: g.description || "",
  });
}

function newGroup(parentName) {
  selected.value = null;
  drawerMode.value = "add";
  formActive.value = true;
  Object.assign(form, { name: "", parent_item_group: parentName || "All Item Groups", is_group: 0, description: "" });
}

async function saveGroup() {
  if (!form.name.trim()) { toast("Group name is required", "error"); return; }
  saving.value = true;
  try {
    const doc = {
      doctype: "Item Group",
      name: form.name,
      parent_item_group: form.parent_item_group,
      is_group: form.is_group ? 1 : 0,
      description: form.description,
    };
    if (drawerMode.value === "edit") doc.name = form.name;
    await apiSave(doc);
    await load();
    selected.value = form.name;
    // Expand the parent so the newly-created child becomes visible in the tree.
    if (form.parent_item_group) {
      const s = new Set(expanded.value);
      s.add(form.parent_item_group);
      expanded.value = s;
    }
    toast(drawerMode.value === "edit" ? "Group updated" : "Group created");
  } catch (e) { toast("Save failed: " + e.message, "error"); }
  finally { saving.value = false; }
}

async function deleteGroup() {
  if (!form.name) return;
  if (!(await confirm({ title: "Delete group?", body: `Delete "${form.name}"? This cannot be undone.`, okLabel: "Delete" }))) return;
  try {
    await apiDelete("Item Group", form.name);
    await load();
    selected.value = null;
    formActive.value = false;
    toast("Group deleted");
  } catch (e) { toast("Delete failed: " + e.message, "error"); }
}

onMounted(load);
</script>
