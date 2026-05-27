<template>
  <div class="ba-page">
    <div class="ba-actions">
      <div class="ba-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search bank accounts…" class="ba-search-input" />
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="ba-btn-ghost" @click="load"><span v-html="icon('refresh',14)"></span></button>
        <button class="ba-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> New Account</button>
      </div>
    </div>

    <div class="ba-grid" v-if="!loading && filtered.length">
      <div v-for="acc in filtered" :key="acc.name" class="ba-card" @click="openView(acc)">
        <div class="ba-card-top">
          <div class="ba-card-icon"><span v-html="icon('bank',20)"></span></div>
          <span class="ba-badge" :class="acc.is_default?'badge-blue':'badge-grey'">{{ acc.is_default?'Default':acc.account_type||'Bank' }}</span>
        </div>
        <div class="ba-card-name">{{ acc.account_name||acc.name }}</div>
        <div class="ba-card-bank text-muted">{{ acc.bank_name||'—' }}</div>
        <div class="ba-card-num mono-sm">{{ acc.account_number ? maskAcct(acc.account_number) : '—' }}</div>
        <div class="ba-card-footer">
          <span class="text-muted" style="font-size:11px">{{ acc.ifsc_code||'' }}</span>
          <button class="ba-edit-btn" @click.stop="openEdit(acc)"><span v-html="icon('edit',12)"></span></button>
        </div>
      </div>
    </div>
    <div v-else-if="!loading" class="ba-empty-wrap">
      <div class="ba-empty-card">
        <span v-html="icon('bank',32)" style="color:#d1d5db;display:block;margin:0 auto 12px"></span>
        <div style="font-weight:600;color:#374151;margin-bottom:4px">No bank accounts yet</div>
        <div style="color:#9ca3af;font-size:12.5px;margin-bottom:16px">Add your first bank account to get started</div>
        <button class="ba-btn-primary" @click="openNew"><span v-html="icon('plus',13)"></span> Add Account</button>
      </div>
    </div>
    <div v-else class="ba-grid">
      <div v-for="n in 4" :key="n" class="ba-card-skeleton"><div class="ba-shimmer" style="height:120px"></div></div>
    </div>

    <!-- Create / Edit Drawer -->
    <div v-if="drawerOpen" class="ba-overlay" @click.self="drawerOpen=false"></div>
    <div class="ba-drawer" :class="{open:drawerOpen}">
      <div class="ba-dheader">
        <div class="ba-dheader-title">{{ editingName?'Edit Bank Account':'New Bank Account' }}</div>
        <button class="ba-dclose" @click="drawerOpen=false"><span v-html="icon('x',16)"></span></button>
      </div>
      <div class="ba-dbody">
        <div class="ba-fields-grid">
          <div class="ba-field" style="grid-column:1/-1">
            <label class="ba-label">Account Name <span class="req">*</span></label>
            <input v-model="form.account_name" class="ba-input" placeholder="e.g. HDFC Current Account" />
          </div>
          <div class="ba-field">
            <label class="ba-label">Bank <span class="req">*</span></label>
            <input v-model="form.bank_name" class="ba-input" placeholder="e.g. HDFC Bank" />
          </div>
          <div class="ba-field">
            <label class="ba-label">Account Type</label>
            <select v-model="form.account_type" class="ba-select">
              <option value="Savings">Savings</option>
              <option value="Current">Current</option>
              <option value="Cash">Cash</option>
              <option value="Overdraft">Overdraft</option>
              <option value="Credit Card">Credit Card</option>
            </select>
          </div>
          <div class="ba-field">
            <label class="ba-label">Account Number</label>
            <input v-model="form.account_number" class="ba-input" placeholder="Account number" />
          </div>
          <div class="ba-field">
            <label class="ba-label">IFSC Code</label>
            <input v-model="form.ifsc_code" class="ba-input" placeholder="e.g. HDFC0001234" />
          </div>
          <div class="ba-field" style="grid-column:1/-1">
            <label class="ba-label">GL Account</label>
            <SearchableSelect v-model="form.gl_account" :options="glAccounts" placeholder="Link to chart of accounts…" @search="fetchGLAccounts" />
          </div>
          <div class="ba-field">
            <label class="ba-label" style="display:flex;align-items:center;gap:8px;cursor:pointer">
              <input type="checkbox" v-model="form.is_default" style="width:14px;height:14px" /> Set as default account
            </label>
          </div>
        </div>
      </div>
      <div class="ba-dfooter">
        <button class="ba-btn-ghost" @click="drawerOpen=false">Cancel</button>
        <button class="ba-btn-primary" :disabled="drawerSaving" @click="saveAccount">
          <span v-html="icon('save',13)"></span> {{ drawerSaving?'Saving…':'Save' }}
        </button>
      </div>
    </div>

    <!-- View Drawer -->
    <div v-if="viewOpen" class="ba-overlay" @click.self="viewOpen=false"></div>
    <div class="ba-drawer ba-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="ba-view-head">
          <div class="ba-view-icon"><span v-html="icon('bank',24)"></span></div>
          <div>
            <div class="ba-view-name">{{ viewDoc.account_name||viewDoc.name }}</div>
            <div class="text-muted" style="font-size:12px">{{ viewDoc.bank_name }}</div>
          </div>
          <button class="ba-dclose ba-vclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
        </div>
        <div class="ba-dbody">
          <div class="ba-meta-grid">
            <div><div class="ba-meta-lbl">Account Type</div><div>{{ viewDoc.account_type||'—' }}</div></div>
            <div><div class="ba-meta-lbl">Account No</div><div class="mono-sm">{{ viewDoc.account_number||'—' }}</div></div>
            <div><div class="ba-meta-lbl">IFSC</div><div class="mono-sm">{{ viewDoc.ifsc_code||'—' }}</div></div>
            <div><div class="ba-meta-lbl">GL Account</div><div>{{ viewDoc.gl_account||'—' }}</div></div>
            <div><div class="ba-meta-lbl">Default</div><div>{{ viewDoc.is_default?'Yes':'No' }}</div></div>
          </div>
        </div>
        <div class="ba-dfooter">
          <button class="ba-btn-ghost" @click="viewOpen=false">Close</button>
          <button class="ba-btn-primary" @click="openEdit(viewDoc);viewOpen=false"><span v-html="icon('edit',13)"></span> Edit</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import SearchableSelect from "../components/SearchableSelect.vue";

const { toast } = useToast();
const list=ref([]),loading=ref(false),search=ref("");
const drawerOpen=ref(false),drawerSaving=ref(false),editingName=ref("");
const viewOpen=ref(false),viewDoc=ref(null);
const glAccounts=ref([]);
const form=reactive({account_name:"",bank_name:"",account_type:"Current",account_number:"",ifsc_code:"",gl_account:"",is_default:false});

async function load(){loading.value=true;try{const co=await resolveCompany();list.value=await apiList("Bank Account",{fields:["name","account_name","bank_name","account_type","account_number","ifsc_code","gl_account","is_default","company"],filters:[["company","=",co]],limit:100,order:"account_name asc"});}catch(e){toast.error(e.message||"Failed to load bank accounts");}finally{loading.value=false;}}
const filtered=computed(()=>{if(!search.value.trim())return list.value;const q=search.value.toLowerCase();return list.value.filter(a=>(a.account_name||a.name||"").toLowerCase().includes(q)||(a.bank_name||"").toLowerCase().includes(q));});
function maskAcct(n){if(!n||n.length<4)return n;return"•".repeat(Math.max(0,n.length-4))+n.slice(-4);}
function openNew(){editingName.value="";Object.assign(form,{account_name:"",bank_name:"",account_type:"Current",account_number:"",ifsc_code:"",gl_account:"",is_default:false});glAccounts.value=[];drawerOpen.value=true;}
function openEdit(a){editingName.value=a.name;Object.assign(form,{account_name:a.account_name||"",bank_name:a.bank_name||"",account_type:a.account_type||"Current",account_number:a.account_number||"",ifsc_code:a.ifsc_code||"",gl_account:a.gl_account||"",is_default:!!a.is_default});glAccounts.value=[];drawerOpen.value=true;}
function openView(a){viewDoc.value=a;viewOpen.value=true;}
async function fetchGLAccounts(q=""){try{const co=await resolveCompany();const r=await apiList("Account",{fields:["name"],filters:[["account_type","in",["Bank","Cash"]],["company","=",co],["is_group","=",0],...(q?[["name","like",`%${q}%`]]:[])],limit:20});glAccounts.value=r.map(x=>({label:x.name,value:x.name}));}catch{glAccounts.value=[];}}
async function saveAccount(){if(!form.account_name)return toast.error("Account name is required");if(!form.bank_name)return toast.error("Bank name is required");drawerSaving.value=true;try{const co=await resolveCompany();const doc={doctype:"Bank Account",company:co,account_name:form.account_name,bank_name:form.bank_name,account_type:form.account_type,account_number:form.account_number||"",ifsc_code:form.ifsc_code||"",gl_account:form.gl_account||"",is_default:form.is_default?1:0};if(editingName.value)doc.name=editingName.value;const saved=await apiSave(doc);toast.success(`Bank account ${saved?.name||""} saved`);drawerOpen.value=false;await load();}catch(e){toast.error(e.message||"Failed to save bank account");}finally{drawerSaving.value=false;}}
onMounted(load);
</script>

<style scoped>
.ba-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.ba-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.ba-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;}
.ba-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.ba-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;}
.ba-btn-primary:hover{background:#1d4ed8;}.ba-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.ba-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#fff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;}
.ba-btn-ghost:hover{background:#f9fafb;}
.ba-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(260px,1fr));gap:16px;}
.ba-card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:18px;cursor:pointer;transition:box-shadow .15s;}
.ba-card:hover{box-shadow:0 4px 16px rgba(0,0,0,.08);border-color:#2563eb;}
.ba-card-top{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px;}
.ba-card-icon{width:40px;height:40px;background:#eff6ff;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#2563eb;}
.ba-card-name{font-size:14px;font-weight:700;color:#111827;margin-bottom:2px;}
.ba-card-bank{font-size:12.5px;margin-bottom:4px;}
.ba-card-num{font-size:12.5px;color:#374151;margin-bottom:8px;}
.ba-card-footer{display:flex;align-items:center;justify-content:space-between;}
.ba-edit-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.ba-edit-btn:hover{background:#f3f4f6;color:#2563eb;}
.ba-card-skeleton{background:#fff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden;}
.ba-empty-wrap{display:flex;justify-content:center;padding:40px 0;}
.ba-empty-card{background:#fff;border:1px solid #e5e7eb;border-radius:12px;padding:32px;text-align:center;min-width:300px;}
.ba-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.badge-blue{background:#dbeafe;color:#2563eb;}.badge-grey{background:#f3f4f6;color:#6b7280;}
.text-muted{color:#6b7280;}.mono-sm{font-family:monospace;font-size:12.5px;}
.ba-shimmer{background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}
.ba-overlay{position:fixed;inset:0;background:rgba(0,0,0,.2);z-index:40;}
.ba-drawer{position:fixed;top:0;right:-480px;bottom:0;width:480px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-8px 0 24px rgba(0,0,0,.08);z-index:50;display:flex;flex-direction:column;transition:right .22s ease;}
.ba-drawer.open{right:0;}
.ba-view-drawer{width:400px;right:-400px;}.ba-view-drawer.open{right:0;}
.ba-dheader{display:flex;align-items:center;justify-content:space-between;padding:0 20px;height:60px;border-bottom:1px solid #e5e7eb;flex-shrink:0;}
.ba-dheader-title{font-size:15px;font-weight:600;color:#111827;}
.ba-dclose{background:transparent;border:none;cursor:pointer;color:#6b7280;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:6px;}
.ba-dclose:hover{background:#f3f4f6;color:#111827;}
.ba-dbody{flex:1;overflow-y:auto;padding:20px;display:flex;flex-direction:column;gap:14px;}
.ba-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.ba-field{display:flex;flex-direction:column;gap:4px;}
.ba-label{font-size:12px;font-weight:600;color:#374151;}.req{color:#dc2626;}
.ba-input{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;}
.ba-input:focus{border-color:#2563eb;box-shadow:0 0 0 2px rgba(37,99,235,.08);}
.ba-select{border:1px solid #e5e7eb;border-radius:6px;padding:7px 10px;font:inherit;font-size:13px;outline:none;background:#fff;color:#111827;cursor:pointer;}
.ba-select:focus{border-color:#2563eb;}
.ba-view-head{position:relative;display:flex;align-items:center;gap:14px;padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:#eff6ff;}
.ba-view-icon{width:44px;height:44px;background:#fff;border-radius:10px;display:flex;align-items:center;justify-content:center;color:#2563eb;flex-shrink:0;}
.ba-view-name{font-size:16px;font-weight:700;color:#111827;}
.ba-vclose{position:absolute;top:12px;right:12px;}
.ba-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.ba-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;}
.ba-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;}
</style>
