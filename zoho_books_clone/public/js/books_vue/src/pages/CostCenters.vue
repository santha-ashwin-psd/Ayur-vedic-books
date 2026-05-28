<template>
<div style="display:flex;flex-direction:column;height:calc(100vh - 56px);overflow:hidden">
  <div style="display:flex;flex:1;gap:0;overflow:hidden">

    <div style="width:340px;flex-shrink:0;display:flex;flex-direction:column;border-right:1px solid #E2E8F0;background:#fff">
      <div style="padding:12px 16px;border-bottom:1px solid #E2E8F0;background:#F8F9FC;display:flex;align-items:center;justify-content:space-between;flex-shrink:0">
        <span style="font-size:12px;font-weight:700;letter-spacing:.4px;text-transform:uppercase;color:#868E96">{{loading?"Loading...":allCC.length+" cost centers"}}</span>
        <div style="display:flex;gap:6px">
          <button style="border:1px solid #E2E8F0;border-radius:5px;padding:4px 7px;background:#fff;cursor:pointer;color:#868E96;font-size:12px;display:inline-flex;align-items:center" @click="expandAll(true)" title="Expand all"><span v-html="icon('chevD',13)"></span></button>
          <button style="border:1px solid #E2E8F0;border-radius:5px;padding:4px 7px;background:#fff;cursor:pointer;color:#868E96;font-size:12px;display:inline-flex;align-items:center" @click="expandAll(false)" title="Collapse all"><span v-html="icon('chevU',13)"></span></button>
          <button class="b-btn b-btn-primary" style="font-size:12px;padding:5px 10px" @click="openAdd()"><span v-html="icon('plus',12)"></span> New</button>
        </div>
      </div>
      <div style="padding:8px 12px;border-bottom:1px solid #F1F3F5;flex-shrink:0">
        <input v-model="ccSearch" type="text" placeholder="Search cost centers..." style="width:100%;border:1px solid #E2E8F0;border-radius:6px;padding:6px 10px;font-size:13px;outline:none;font-family:inherit"/>
      </div>
      <div style="overflow-y:auto;flex:1">
        <div v-if="loading" style="padding:20px;text-align:center;color:#868E96">Loading...</div>
        <template v-else>
          <div v-for="node in visibleNodes" :key="node.name"
            style="display:flex;align-items:center;border-bottom:1px solid #F8F9FC;cursor:pointer;transition:background .12s;user-select:none"
            :style="{background:selected===node.name?'rgba(59,91,219,.07)':'',borderLeft:selected===node.name?'3px solid #3B5BDB':'3px solid transparent'}"
            @click="selectCC(node.name)">
            <div style="width:20px;height:36px;display:flex;align-items:center;justify-content:center;flex-shrink:0;color:#868E96;cursor:pointer;margin-left:4px"
              v-if="node.hasChildren" @click.stop="toggleCC(node.name)">
              <span style="display:inline-block;transition:transform .15s;font-size:10px" :style="{transform:node.isOpen?'rotate(90deg)':'rotate(0deg)'}">&#9654;</span>
            </div>
            <div v-else style="width:24px;flex-shrink:0"></div>
            <div style="width:22px;height:22px;border-radius:5px;display:flex;align-items:center;justify-content:center;font-size:11px;flex-shrink:0;margin-right:8px;margin-left:4px" :style="{background:node.color+'22',color:node.color,marginLeft:(node.depth*18+4)+'px'}">
              {{CC_TYPE_ICONS[node.type]||"🏢"}}
            </div>
            <div style="flex:1;padding:8px 4px 8px 0;min-width:0">
              <div style="font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis" :style="{fontWeight:node.is_group?600:400,color:selected===node.name?'#3B5BDB':'#1A1D23'}">{{node.name}}</div>
              <div v-if="node.code" style="font-size:10.5px;color:#868E96;padding-left:0">{{node.code}}</div>
            </div>
            <span v-if="node.status==='Inactive'" style="font-size:10.5px;font-weight:600;padding:1px 7px;border-radius:10px;background:#F1F3F5;color:#868E96;margin-right:8px;flex-shrink:0">Off</span>
          </div>
          <div v-if="!visibleNodes.length" style="padding:20px;text-align:center;color:#868E96;font-size:13px">No cost centers found</div>
        </template>
      </div>
    </div>

    <div style="flex:1;overflow-y:auto;padding:20px;background:#F3F4F6">
      <div v-if="!selectedCC" style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:100%;text-align:center;color:#868E96;padding:40px">
        <div style="font-size:40px;margin-bottom:12px">🏢</div>
        <div style="font-size:15px;font-weight:600;color:#1A1D23;margin-bottom:6px">Select a cost center</div>
        <div style="font-size:13px;margin-bottom:20px;max-width:280px;line-height:1.5">Click any cost center in the tree to see its budget, expenses, and breakdown</div>
        <button class="b-btn b-btn-primary" @click="openAdd()"><span v-html="icon('plus',13)"></span>Add First Cost Center</button>
      </div>

      <template v-else>
        <div class="b-card" style="padding:0;overflow:hidden;margin-bottom:16px">
          <div style="padding:14px 20px;border-bottom:1px solid #E2E8F0;display:flex;align-items:center;justify-content:space-between">
            <div style="display:flex;align-items:center;gap:10px">
              <div style="width:36px;height:36px;border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:18px" :style="{background:selectedCC.color+'22',color:selectedCC.color}">{{CC_TYPE_ICONS[selectedCC.type]||"🏢"}}</div>
              <div>
                <div style="font-size:15px;font-weight:700;color:#1A1D23">{{selectedCC.name}}</div>
                <div style="font-size:12px;color:#868E96">{{selectedCC.type}}{{selectedCC.code?" · "+selectedCC.code:""}}{{selectedCC.parent?" · under "+selectedCC.parent:""}}</div>
              </div>
            </div>
            <div style="display:flex;gap:8px">
              <button class="b-btn b-btn-ghost" @click="openEdit(selectedCC.name)"><span v-html="icon('edit',13)"></span>Edit</button>
              <button v-if="selectedCC.source!=='frappe'" style="border:1px solid rgba(201,42,42,.3);border-radius:5px;cursor:pointer;padding:5px 7px;display:inline-flex;color:#C92A2A;background:none" @click="confirmDel(selectedCC.name)"><span v-html="icon('trash',14)"></span></button>
            </div>
          </div>
          <div style="padding:20px">
            <div v-if="selectedCC.desc" style="font-size:13px;color:#868E96;margin-bottom:16px;line-height:1.5">{{selectedCC.desc}}</div>

            <template v-if="!selectedCC.is_group">
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px">
                <div style="background:#F8F9FC;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px">
                  <div style="font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:#868E96;margin-bottom:4px">Annual Budget</div>
                  <div style="font-size:17px;font-weight:700;font-family:var(--mono);color:#3B5BDB">{{fmtINR(selectedCC.budget)||"—"}}</div>
                </div>
                <div style="background:#F8F9FC;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px">
                  <div style="font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:#868E96;margin-bottom:4px">Spent (YTD)</div>
                  <div style="font-size:17px;font-weight:700;font-family:var(--mono)" :style="{color:pct(spend[selectedCC.name]||0,selectedCC.budget)>=100?'#C92A2A':pct(spend[selectedCC.name]||0,selectedCC.budget)>=80?'#E67700':'#1A1D23'}">{{fmtINR(spend[selectedCC.name]||0)}}</div>
                </div>
                <div style="background:#F8F9FC;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px">
                  <div style="font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:#868E96;margin-bottom:4px">{{selectedCC.budget-(spend[selectedCC.name]||0)>=0?"Remaining":"Over Budget"}}</div>
                  <div style="font-size:17px;font-weight:700;font-family:var(--mono)" :style="{color:selectedCC.budget-(spend[selectedCC.name]||0)>=0?'#2F9E44':'#C92A2A'}">{{fmtINR(Math.abs(selectedCC.budget-(spend[selectedCC.name]||0)))}}</div>
                </div>
              </div>
              <div v-if="selectedCC.budget" style="margin-bottom:20px">
                <div style="display:flex;justify-content:space-between;font-size:12px;color:#868E96;margin-bottom:6px">
                  <span>Budget utilisation</span>
                  <span style="font-weight:700" :style="{color:pct(spend[selectedCC.name]||0,selectedCC.budget)>=100?'#C92A2A':pct(spend[selectedCC.name]||0,selectedCC.budget)>=80?'#E67700':'#1A1D23'}">{{pct(spend[selectedCC.name]||0,selectedCC.budget)}}%</span>
                </div>
                <div style="background:#E8ECF0;border-radius:20px;height:8px;overflow:hidden">
                  <div style="height:100%;border-radius:20px;transition:width .4s ease" :style="{width:pct(spend[selectedCC.name]||0,selectedCC.budget)+'%',background:pct(spend[selectedCC.name]||0,selectedCC.budget)>=100?'#C92A2A':pct(spend[selectedCC.name]||0,selectedCC.budget)>=80?'#E67700':'#2F9E44'}"></div>
                </div>
              </div>
            </template>

            <template v-if="selectedCC.is_group">
              <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px">
                <div style="background:#F8F9FC;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px"><div style="font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:#868E96;margin-bottom:4px">Child Centers</div><div style="font-size:17px;font-weight:700;font-family:var(--mono)">{{ccChildren.length}}</div></div>
                <div style="background:#F8F9FC;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px"><div style="font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:#868E96;margin-bottom:4px">Total Budget</div><div style="font-size:17px;font-weight:700;font-family:var(--mono);color:#3B5BDB">{{fmtINR(ccChildren.reduce((s,c)=>s+Number(c.budget||0),0))}}</div></div>
                <div style="background:#F8F9FC;border:1px solid #E2E8F0;border-radius:8px;padding:12px 14px"><div style="font-size:10.5px;font-weight:600;text-transform:uppercase;letter-spacing:.4px;color:#868E96;margin-bottom:4px">Total Spent</div><div style="font-size:17px;font-weight:700;font-family:var(--mono)">{{fmtINR(ccChildren.reduce((s,c)=>s+(spend[c.name]||0),0))}}</div></div>
              </div>
              <div v-if="ccChildren.length">
                <div style="font-size:11px;font-weight:700;letter-spacing:.5px;text-transform:uppercase;color:#868E96;margin-bottom:10px">Sub-centers expense allocation</div>
                <div v-for="c in ccChildren" :key="c.name" style="display:flex;align-items:center;gap:10px;margin-bottom:8px">
                  <span style="font-size:12.5px;width:120px;flex-shrink:0;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{{c.name}}</span>
                  <div style="flex:1;background:#E8ECF0;border-radius:10px;height:6px;overflow:hidden">
                    <div style="height:100%;border-radius:10px;transition:width .4s" :style="{width:Math.round((spend[c.name]||0)/Math.max(1,...ccChildren.map(x=>spend[x.name]||0))*100)+'%',background:c.color}"></div>
                  </div>
                  <span style="font-size:12px;font-family:var(--mono);color:#868E96;width:70px;text-align:right;flex-shrink:0">{{fmtINR(spend[c.name]||0)}}</span>
                </div>
              </div>
            </template>
          </div>
        </div>

        <div v-if="!selectedCC.is_group" class="b-card" style="padding:0;overflow:hidden">
          <div style="padding:12px 20px;border-bottom:1px solid #E2E8F0"><span style="font-size:13px;font-weight:600">Budget Settings</span></div>
          <div style="padding:14px 20px;display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;font-size:13px">
            <div><div style="color:#868E96;font-size:11.5px;margin-bottom:3px">Period</div><div style="font-weight:500">{{selectedCC.budget_period||"Annual"}}</div></div>
            <div><div style="color:#868E96;font-size:11.5px;margin-bottom:3px">Alert at</div><div style="font-weight:500">{{selectedCC.alert_pct||80}}%</div></div>
            <div><div style="color:#868E96;font-size:11.5px;margin-bottom:3px">Action</div><div style="font-weight:500">{{selectedCC.budget_action||"Warn"}}</div></div>
          </div>
        </div>
      </template>
    </div>
  </div>

  <Teleport to="body">
    <div v-if="showDrawer" class="cc-drawer-open" style="position:fixed;inset:0;z-index:9000;background:rgba(15,23,42,.45);display:flex;justify-content:flex-end;backdrop-filter:blur(2px)" @click.self="closeDrawer">
      <div style="width:480px;max-width:95vw;height:100%;background:#fff;display:flex;flex-direction:column;box-shadow:-20px 0 60px rgba(0,0,0,.15)">
        <div style="background:linear-gradient(135deg,#2563eb,#4f46e5);padding:18px 24px;display:flex;align-items:center;justify-content:space-between;flex-shrink:0">
          <div>
            <div style="color:#fff;font-size:16px;font-weight:700">{{editing?"Edit Cost Center":"New Cost Center"}}</div>
            <div style="color:rgba(255,255,255,.7);font-size:12px;margin-top:2px">Track expenses by department or project</div>
          </div>
          <button @click="closeDrawer" style="background:rgba(255,255,255,.2);border:none;cursor:pointer;width:30px;height:30px;border-radius:6px;color:#fff;display:flex;align-items:center;justify-content:center"><span v-html="icon('x',16)"></span></button>
        </div>
        <div style="flex:1;overflow-y:auto;padding:24px">
          <div style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#868E96;margin-bottom:10px">Details</div>
          <div style="display:grid;gap:14px;margin-bottom:14px">
            <div>
              <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Cost Center Name <span style="color:#C92A2A">*</span></label>
              <input v-model="fForm.name" class="b-input" placeholder="e.g. Engineering, Sales, Project Alpha" :disabled="!!editing"/>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
              <div>
                <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Cost Center Code</label>
                <input v-model="fForm.code" class="b-input" placeholder="e.g. ENG, SLS"/>
              </div>
              <div>
                <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Parent Cost Center</label>
                <select v-model="fForm.parent" class="b-input">
                  <option value="">— Root level —</option>
                  <option v-for="c in allCC.filter(c=>c.name!==fForm.name)" :key="c.name" :value="c.name">{{c.name}}</option>
                </select>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
              <div>
                <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Type</label>
                <select v-model="fForm.type" class="b-input">
                  <option value="Department">Department</option>
                  <option value="Project">Project</option>
                  <option value="Product">Product Line</option>
                  <option value="Region">Region / Branch</option>
                  <option value="Group">Group (parent only)</option>
                </select>
              </div>
              <div>
                <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Colour Tag</label>
                <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:6px">
                  <div v-for="c in CC_COLORS" :key="c" @click="fForm.color=c" style="width:22px;height:22px;border-radius:50%;cursor:pointer;transition:all .15s;flex-shrink:0"
                    :style="{background:c,outline:fForm.color===c?'2px solid '+c:'none',border:fForm.color===c?'2px solid #fff':'2px solid transparent'}"></div>
                </div>
              </div>
            </div>
            <div>
              <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Description</label>
              <textarea v-model="fForm.desc" class="b-input" rows="2" style="resize:vertical" placeholder="What this cost center tracks..."></textarea>
            </div>
          </div>
          <div style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#868E96;margin-bottom:10px;margin-top:20px;padding-top:20px;border-top:1px solid #E2E8F0">Budget</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
            <div>
              <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Annual Budget (₹)</label>
              <input v-model="fForm.budget" class="b-input" type="number" min="0" step="1000" placeholder="0" style="font-family:var(--mono)"/>
            </div>
            <div>
              <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Budget Period</label>
              <select v-model="fForm.budget_period" class="b-input">
                <option value="Annual">Annual</option>
                <option value="Quarterly">Quarterly</option>
                <option value="Monthly">Monthly</option>
              </select>
            </div>
          </div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:12px">
            <div>
              <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Budget Alert At (%)</label>
              <input v-model="fForm.alert_pct" class="b-input" type="number" min="0" max="100" style="font-family:var(--mono)"/>
            </div>
            <div>
              <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Budget Action</label>
              <select v-model="fForm.budget_action" class="b-input">
                <option value="Warn">Warn only</option>
                <option value="Stop">Stop and warn</option>
                <option value="None">No action</option>
              </select>
            </div>
          </div>
          <div style="font-size:11px;font-weight:700;letter-spacing:.6px;text-transform:uppercase;color:#868E96;margin-bottom:10px;margin-top:20px;padding-top:20px;border-top:1px solid #E2E8F0">Settings</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px">
            <div>
              <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Is Group?</label>
              <div style="display:flex;align-items:center;gap:12px;margin-top:6px">
                <label style="display:flex;align-items:center;gap:5px;cursor:pointer;font-size:13px"><input type="radio" v-model="fForm.is_group" :value="1" style="accent-color:#3B5BDB"/> Yes</label>
                <label style="display:flex;align-items:center;gap:5px;cursor:pointer;font-size:13px"><input type="radio" v-model="fForm.is_group" :value="0" style="accent-color:#3B5BDB"/> No</label>
              </div>
            </div>
            <div>
              <label style="display:block;font-size:11.5px;font-weight:600;color:#495057;margin-bottom:4px">Status</label>
              <select v-model="fForm.status" class="b-input"><option value="Active">Active</option><option value="Inactive">Inactive</option></select>
            </div>
          </div>
        </div>
        <div style="padding:16px 24px;border-top:1px solid #E2E8F0;display:flex;justify-content:flex-end;gap:10px;background:#F8F9FC;flex-shrink:0">
          <button class="b-btn b-btn-ghost" @click="closeDrawer">Cancel</button>
          <button class="b-btn b-btn-primary" @click="saveCC" :disabled="saving" style="min-width:120px">{{saving?"Saving...":editing?"Update":"Create"}}</button>
        </div>
      </div>
    </div>

    <div v-if="showDelModal" style="position:fixed;inset:0;z-index:9100;background:rgba(15,23,42,.5);display:flex;align-items:center;justify-content:center;padding:20px;backdrop-filter:blur(3px)" @click.self="closeDelModal">
      <div style="background:#fff;border-radius:12px;padding:28px 32px;max-width:420px;width:100%">
        <div style="font-size:17px;font-weight:700;margin-bottom:8px">Delete Cost Center?</div>
        <div style="font-size:14px;color:#868E96;margin-bottom:24px;line-height:1.5">"<strong>{{deleteTarget}}</strong>" will be permanently removed. This cannot be undone.</div>
        <div style="display:flex;gap:10px;justify-content:flex-end">
          <button class="b-btn b-btn-ghost" @click="closeDelModal">Keep It</button>
          <button class="b-btn" style="background:#C92A2A;color:#fff;border-color:#C92A2A" @click="doDelete">Yes, Delete</button>
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

const { toast } = useToast();

const CC_COLORS = ["#3B5BDB","#0C8599","#2F9E44","#E67700","#C92A2A","#2563eb","#D4537E","#1098AD","#495057"];
const CC_TYPE_ICONS = { Department: "🏢", Project: "📄", Product: "📦", Region: "🌍", Group: "📁" };
const CC_DEFAULTS = [
  { name: "Main",        code: "MAIN", parent: "",     type: "Group",      color: "#495057", budget: 0,       budget_period: "Annual", alert_pct: 80, budget_action: "Warn", is_group: 1, status: "Active", desc: "Root cost center" },
  { name: "Engineering", code: "ENG",  parent: "Main", type: "Department", color: "#3B5BDB", budget: 5000000, budget_period: "Annual", alert_pct: 80, budget_action: "Warn", is_group: 0, status: "Active", desc: "Product engineering team" },
  { name: "Sales",       code: "SLS",  parent: "Main", type: "Department", color: "#2F9E44", budget: 3000000, budget_period: "Annual", alert_pct: 80, budget_action: "Warn", is_group: 0, status: "Active", desc: "Sales and business development" },
  { name: "Marketing",   code: "MKT",  parent: "Main", type: "Department", color: "#E67700", budget: 2000000, budget_period: "Annual", alert_pct: 80, budget_action: "Warn", is_group: 0, status: "Active", desc: "Brand and demand generation" },
  { name: "Operations",  code: "OPS",  parent: "Main", type: "Department", color: "#0C8599", budget: 1500000, budget_period: "Annual", alert_pct: 80, budget_action: "Warn", is_group: 0, status: "Active", desc: "Infrastructure and ops" },
];
// Real actual-spend per cost center, summed from posted GL entries (keyed by
// the cost center's document name). Loaded from the backend on mount.
const spend = ref({});

const loading      = ref(true);
const allCC        = ref([]);
const selected     = ref(null);
const editing      = ref(null);
const deleteTarget = ref(null);
const expandedCC   = ref([]);
const ccSearch     = ref("");
const showDrawer   = ref(false);
const showDelModal = ref(false);
const saving       = ref(false);
const fromFrappe   = ref(false);

const fForm = reactive({ name: "", code: "", parent: "", type: "Department", color: CC_COLORS[0], budget: "", budget_period: "Annual", alert_pct: 80, budget_action: "Warn", is_group: 0, status: "Active", desc: "" });

function r2(v) { return Math.round(Number(v || 0) * 100) / 100; }
function fmtINR(v) { const n = Number(v || 0); if (n === 0) return "₹0"; return "₹" + Math.abs(n).toLocaleString("en-IN", { minimumFractionDigits: 0 }); }
function pct(spent, budget) { if (!budget) return 0; return Math.min(100, Math.round(spent / budget * 100)); }
function saveLocal() { try { localStorage.setItem("books_cost_centers", JSON.stringify(allCC.value)); } catch {} }
function loadLocal() { try { return JSON.parse(localStorage.getItem("books_cost_centers") || "null"); } catch { return null; } }

async function load() {
  loading.value = true;
  try {
    const ccs = await apiGET("frappe.client.get_list", {
      doctype: "Cost Center",
      fields: JSON.stringify(["name", "cost_center_name", "cost_center_number", "parent_cost_center", "is_group", "disabled", "description", "budget"]),
      order_by: "name asc", limit_page_length: 200,
    }) || [];
    if (ccs.length) {
      allCC.value = ccs.map((c) => ({
        name: c.name, code: c.cost_center_number || "", parent: c.parent_cost_center || "",
        type: "Department", color: "#3B5BDB", budget: Number(c.budget) || 0, budget_period: "Annual",
        alert_pct: 80, budget_action: "Warn", is_group: c.is_group ? 1 : 0,
        status: c.disabled ? "Inactive" : "Active", desc: c.description || "", source: "frappe",
      }));
      fromFrappe.value = true;
      // Real actual spend per cost center, summed from posted GL entries.
      try {
        const company = await resolveCompany();
        const map = await apiGET("zoho_books_clone.api.books_data.get_cost_center_spend", { company });
        spend.value = map && typeof map === "object" ? map : {};
      } catch { spend.value = {}; }
    } else throw new Error("none");
  } catch {
    const saved = loadLocal();
    allCC.value = saved || CC_DEFAULTS.map((c) => ({ ...c, source: "local" }));
    if (!saved) saveLocal();
  }
  allCC.value.filter((c) => c.is_group).forEach((c) => { if (!expandedCC.value.includes(c.name)) expandedCC.value.push(c.name); });
  loading.value = false;
}

const visibleNodes = computed(() => {
  const q = ccSearch.value.toLowerCase();
  const result = [];
  if (q) {
    allCC.value.filter((c) => (c.name || "").toLowerCase().includes(q) || (c.code || "").toLowerCase().includes(q)).forEach((c) => {
      result.push({ ...c, depth: 0, hasChildren: allCC.value.some((x) => x.parent === c.name), isOpen: false });
    });
  } else {
    function walk(parent, depth) {
      allCC.value.filter((c) => (c.parent || "") === (parent || "")).forEach((c) => {
        const hasChildren = allCC.value.some((x) => x.parent === c.name);
        const isOpen = expandedCC.value.includes(c.name);
        result.push({ ...c, depth, hasChildren, isOpen });
        if (isOpen && hasChildren) walk(c.name, depth + 1);
      });
    }
    walk("", 0);
  }
  return result;
});

function toggleCC(name) { const i = expandedCC.value.indexOf(name); if (i >= 0) expandedCC.value.splice(i, 1); else expandedCC.value.push(name); }
function expandAll(open) { if (open) allCC.value.forEach((c) => { if (!expandedCC.value.includes(c.name)) expandedCC.value.push(c.name); }); else expandedCC.value = []; }

function selectCC(name) { selected.value = name; }

const selectedCC = computed(() => allCC.value.find((c) => c.name === selected.value) || null);
const ccChildren = computed(() => selectedCC.value ? allCC.value.filter((c) => c.parent === selectedCC.value.name) : []);

function openAdd(parentName) {
  editing.value = null;
  Object.assign(fForm, { name: "", code: "", parent: parentName || "", type: "Department", color: CC_COLORS[0], budget: "", budget_period: "Annual", alert_pct: 80, budget_action: "Warn", is_group: 0, status: "Active", desc: "" });
  showDrawer.value = true;
}
function openEdit(name) {
  const cc = allCC.value.find((c) => c.name === name);
  if (!cc) return;
  editing.value = name;
  Object.assign(fForm, { ...cc, budget: cc.budget || "" });
  showDrawer.value = true;
}
function closeDrawer() { showDrawer.value = false; editing.value = null; }

async function saveCC() {
  if (!fForm.name.trim()) { toast("Cost Center Name is required", "error"); return; }
  saving.value = true;
  const data = { ...fForm, budget: Number(fForm.budget) || 0 };
  const company = await resolveCompany();
  if (!company) { toast("No company configured. Please set a default company in Books Settings.", "error"); saving.value = false; return; }
  try {
    const doc = { doctype: "Cost Center", cost_center_name: data.name, cost_center_number: data.code, parent_cost_center: data.parent || "", is_group: data.is_group, company, budget: data.budget, description: data.desc || "" };
    if (editing.value) { doc.name = editing.value; await apiPOST("frappe.client.save", { doc: JSON.stringify(doc) }); }
    else await apiPOST("frappe.client.insert", { doc: JSON.stringify(doc) });
    fromFrappe.value = true;
    await load();
    toast(editing.value ? "Cost center updated" : "Cost center created");
    saving.value = false;
    closeDrawer();
  } catch (e) {
    toast("Error saving cost center: " + (e.message || e), "error");
    saving.value = false;
  }
}

function confirmDel(name) { deleteTarget.value = name; showDelModal.value = true; }
function closeDelModal() { showDelModal.value = false; deleteTarget.value = null; }

async function doDelete() {
  const name = deleteTarget.value;
  if (!name) return;
  if (fromFrappe.value) {
    try { await apiPOST("frappe.client.delete", { doctype: "Cost Center", name }); await load(); toast("Deleted"); }
    catch (e) { toast("Frappe error: " + e.message, "error"); }
  } else {
    allCC.value = allCC.value.filter((c) => c.name !== name);
    saveLocal();
    if (selected.value === name) selected.value = null;
    toast("Deleted");
  }
  closeDelModal();
}

onMounted(load);
</script>
