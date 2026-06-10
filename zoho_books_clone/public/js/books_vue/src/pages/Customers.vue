<template>
<div>
  <!-- ── FLAT TABLE VIEW (default) ── -->
  <div v-if="!selectedCustomer" class="list-page">

    <div class="sales-toolbar">
      <div class="cust-toolbar-left">
        <div class="sales-pills">
          <button v-for="f in [{k:'all',l:'All'},{k:'active',l:'Active'},{k:'disabled',l:'Disabled'}]"
            :key="f.k" class="sales-pill" :class="{'active': activeFilter===f.k}"
            @click="activeFilter=f.k">
            {{f.l}}
            <span class="sales-pill-count" :class="activeFilter===f.k?'':'zb-pc-muted'">{{counts[f.k]}}</span>
          </button>
        </div>
      </div>
      <div class="cust-toolbar-right">
        <div class="sales-search">
          <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
          <input v-model="search" placeholder="Search customers…" class="sales-search-input" autocomplete="off"/>
        </div>
        <button class="sales-btn-ghost" @click="exportCSV" title="Export CSV"><span v-html="icon('download',13)"></span> CSV</button>
        <button class="sales-btn-ghost" @click="load" title="Refresh"><span v-html="icon('refresh',13)"></span> Refresh</button>
        <button class="sales-btn-primary" @click="openAdd"><span v-html="icon('plus',13)"></span> New Customer</button>
      </div>
    </div>

    <!-- ── KPI Cards ── -->
    <div class="bk-kpi-grid bk-kpi-grid-4" style="margin-bottom:18px">
      <div v-for="kpi in custKpiCards" :key="kpi.key" class="bk-kpi-card" :class="kpi.route?'clickable':''">
        <div class="bk-kpi-inner">
          <div class="bk-kpi-icon" :style="{ background: kpi.iconBg }"><span v-html="kpi.icon"></span></div>
          <div class="bk-kpi-body">
            <div class="bk-kpi-label">{{ kpi.label }}</div>
            <div class="bk-kpi-value" :class="kpi.valueClass">
              <template v-if="loading"><div class="b-shimmer" style="width:64px;height:22px;margin-top:2px;border-radius:4px"></div></template>
              <template v-else>{{ kpi.format === 'currency' ? fmt(kpi.value) : kpi.value }}</template>
            </div>
            <div class="bk-kpi-trend bk-trend-neutral">{{ kpi.sub || '—' }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- Bulk action bar -->
    <div v-if="selectedRows.size" class="inv-bulk-bar" style="margin: 0 24px 12px">
      <span class="inv-bulk-count">{{ selectedRows.size }} selected</span>
      <button class="inv-bulk-btn" @click="bulkSetDisabled(false)" :disabled="bulkBusy">Enable</button>
      <button class="inv-bulk-btn inv-bulk-danger" @click="bulkSetDisabled(true)" :disabled="bulkBusy">Disable</button>
      <button class="inv-bulk-btn" @click="exportCSV" :disabled="bulkBusy">
        <span v-html="icon('download',13)"></span> Export CSV
      </button>
      <button class="inv-bulk-btn" @click="bulkEmail" :disabled="bulkBusy">
        <span v-html="icon('mail',13)"></span> Send Email
      </button>
      <button class="inv-bulk-clear" @click="clearSelection">✕ Clear</button>
    </div>

    <div class="inv-table-wrap">
      <div class="inv-table-wrap">
        <table class="inv-table">
          <thead>
            <tr>
              <th class="vt-th vt-th-check">
                <input type="checkbox" class="vt-checkbox"
                  :checked="filtered.length>0 && filtered.every(c=>selectedRows.has(c.name))"
                  @change="e=>e.target.checked ? selectedRows=new Set(filtered.map(c=>c.name)) : clearSelection()" />
              </th>
              <th class="vt-th">Customer Name</th>
              <th class="vt-th">Type</th>
              <th class="vt-th">GSTIN</th>
              <th class="vt-th">Mobile</th>
              <th class="vt-th">City / State</th>
              <th class="vt-th">Status</th>
              <th class="vt-th vt-th-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="n in 6" :key="n" class="vt-row-shimmer">
                <td colspan="9"><div class="shimmer" style="height:12px;border-radius:3px;width:65%"></div></td>
              </tr>
            </template>
            <tr v-else-if="!filtered.length">
              <td colspan="9" class="vt-empty">
                <div class="vt-empty-icon">
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.3"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </div>
                <div class="vt-empty-title">{{search ? 'No results found' : 'No customers yet'}}</div>
                <div class="vt-empty-sub">{{search ? 'Try adjusting your search or filter' : 'Add your first customer to get started'}}</div>
                <button v-if="!search" class="nim-btn nim-btn-primary" style="margin-top:14px" @click="openAdd"><span v-html="icon('plus',13)"></span> New Customer</button>
              </td>
            </tr>
            <tr v-else v-for="c in filtered" :key="c.name"
              class="inv-row"
              :class="[c.disabled ? 'vt-row-disabled' : '', selectedRows.has(c.name) ? 'vt-row-selected' : '']"
              @click="selectCustomer(c)">
              <td class="vt-td vt-td-check" @click.stop>
                <input type="checkbox" class="vt-checkbox" :checked="selectedRows.has(c.name)" @change="toggleRow(c.name)" />
              </td>
              <td class="vt-td vt-td-customer">
                <div class="vt-vendor-cell">
                  <div class="vt-avatar" :class="c.disabled ? 'vt-avatar-disabled' : ''">{{custInitials(c.customer_name)}}</div>
                  <div>
                    <div class="vt-vendor-name inv-customer">{{c.customer_name}}</div>
                    <div class="vt-vendor-id">{{c.name}}</div>
                  </div>
                </div>
              </td>
              <td class="vt-td">
                <span class="vt-badge" :class="c.customer_type==='Company' ? 'vt-badge-blue' : 'vt-badge-gray'">{{c.customer_type||'—'}}</span>
              </td>
              <td class="vt-td vt-td-mono">{{c.tax_id||'—'}}</td>
              <td class="vt-td vt-td-secondary">{{c.mobile_no||'—'}}</td>
              <td class="vt-td vt-td-secondary">{{c.city ? (c.city + (c.state ? ', '+c.state : '')) : '—'}}</td>
              <td class="vt-td">
                <span class="inv-status-badge" :class="c.disabled ? 'vt-badge-red' : 'vt-badge-green'">
                  <span class="vt-badge-dot"></span>{{c.disabled ? 'Disabled' : 'Active'}}
                </span>
              </td>
              <td class="vt-td vt-td-actions" @click.stop>
                <div class="vt-actions">
                  <button class="inv-act-btn vt-act-edit" @click="openEdit(c.name)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                  <button class="inv-act-btn vt-act-del" @click="confirmDelete(c)" title="Delete"><span v-html="icon('trash',13)"></span></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="!loading && filtered.length" class="vt-footer">
        <span>Showing <strong>{{filtered.length}}</strong> of <strong>{{list.length}}</strong> customers</span>
      </div>
    </div>
  </div>

  <!-- ── TWO-PANEL DETAIL VIEW (when customer selected) ── -->
  <div v-else class="zb-master-detail" style="height:calc(100vh - 56px)">
    <!-- Left panel: customer list -->
    <div class="zb-list-pane" style="width:320px;min-width:260px;border-right:1px solid #e4e8f0;display:flex;flex-direction:column;overflow:hidden">
      <div style="padding:16px 16px 10px;border-bottom:1px solid #f0f2f5;flex-shrink:0">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
          <span style="font-size:14px;font-weight:700;color:#111827">Customers</span>
          <button class="nim-btn nim-btn-primary" style="padding:5px 10px;font-size:12px" @click="openAdd">
            <span v-html="icon('plus',12)"></span> New Customer
          </button>
        </div>
        <div class="sales-search" style="width:100%">
          <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
          <input v-model="search" placeholder="Search customers…" class="sales-search-input" autocomplete="off"/>
        </div>
        <div style="display:flex;gap:4px;margin-top:8px;flex-wrap:wrap">
          <button class="sales-pill" :class="{'active':activeFilter==='all'}" @click="activeFilter='all'" style="font-size:11.5px">All <span class="sales-pill-count" :class="activeFilter==='all'?'':'zb-pc-muted'">{{counts.all}}</span></button>
          <button class="sales-pill" :class="{'active':activeFilter==='active'}" @click="activeFilter='active'" style="font-size:11.5px">Active <span class="sales-pill-count" :class="activeFilter==='active'?'':'zb-pc-muted'">{{counts.active}}</span></button>
          <button class="sales-pill" :class="{'active':activeFilter==='disabled'}" @click="activeFilter='disabled'" style="font-size:11.5px">Disabled <span class="sales-pill-count" :class="activeFilter==='disabled'?'':'zb-pc-muted'">{{counts.disabled}}</span></button>
        </div>
      </div>
      <div style="flex:1;overflow-y:auto">
        <template v-if="loading">
          <div v-for="n in 6" :key="n" style="padding:14px 16px;border-bottom:1px solid #f0f2f5">
            <div class="b-shimmer" style="height:12px;border-radius:4px;width:70%;margin-bottom:6px"></div>
            <div class="b-shimmer" style="height:10px;border-radius:4px;width:40%"></div>
          </div>
        </template>
        <div v-else-if="!filtered.length" style="text-align:center;padding:40px 16px">
          <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5" style="margin:0 auto 10px;display:block"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
          <div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:4px">{{search?'No matches':'No customers yet'}}</div>
          <div style="font-size:12px;color:#9ca3af">{{search?'Try different keywords':'Add your first customer'}}</div>
          <button v-if="!search" class="nim-btn nim-btn-primary" style="margin-top:12px;font-size:12px" @click="openAdd">New Customer</button>
        </div>
        <div v-else v-for="c in filtered" :key="c.name"
          @click="selectCustomer(c)"
          :style="{
            padding:'12px 16px',
            borderBottom:'1px solid #f0f2f5',
            cursor:'pointer',
            background: selectedCustomer && selectedCustomer.name===c.name ? '#FFF7ED' : 'transparent',
            borderLeft: selectedCustomer && selectedCustomer.name===c.name ? '3px solid #E67700' : '3px solid transparent',
            transition:'background 0.15s',
          }">
          <div style="display:flex;align-items:center;gap:10px">
            <div :style="{
              width:'34px',height:'34px',borderRadius:'50%',flexShrink:0,
              display:'flex',alignItems:'center',justifyContent:'center',
              fontWeight:700,fontSize:'12px',color:'#fff',
              background: c.disabled ? '#9CA3AF' : 'linear-gradient(135deg,#16a34a,#15803d)'
            }">{{custInitials(c.customer_name)}}</div>
            <div style="flex:1;min-width:0">
              <div style="font-size:13px;font-weight:700;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                {{c.customer_name}}
              </div>
              <div style="font-size:11.5px;color:#6B7280;margin-top:2px">
                <span :style="c.outstanding>0?'color:#E67700;font-weight:600':''">{{ fmt(c.outstanding || 0) }}</span> outstanding
                <span v-if="c.disabled" style="margin-left:6px;font-size:10px;font-weight:600;color:#6B7280;background:#F3F4F6;padding:1px 5px;border-radius:10px">Disabled</span>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div v-if="!loading && filtered.length" style="padding:8px 16px;border-top:1px solid #f0f2f5;font-size:11.5px;color:#9ca3af;display:flex;justify-content:space-between;flex-shrink:0">
        <span>{{filtered.length}} of {{list.length}} customers</span>
        <button @click="load" style="background:none;border:none;cursor:pointer;color:#6B7280;font-size:11.5px;display:flex;align-items:center;gap:3px"><span v-html="icon('refresh',11)"></span> Refresh</button>
      </div>
    </div>

    <!-- Right panel -->
    <div style="flex:1;overflow-y:auto;background:#F9FAFB">
      <div style="max-width:960px;margin:0 auto;padding:24px">

        <!-- Header -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
          <div style="display:flex;align-items:center;gap:12px">
            <div :style="{
              width:'46px',height:'46px',borderRadius:'50%',flexShrink:0,
              display:'flex',alignItems:'center',justifyContent:'center',
              fontWeight:700,fontSize:'16px',color:'#fff',
              background: selectedCustomer.disabled ? '#9CA3AF' : 'linear-gradient(135deg,#16a34a,#15803d)'
            }">{{custInitials(selectedCustomer.customer_name)}}</div>
            <div>
              <div style="font-size:19px;font-weight:700;color:#111827">{{selectedCustomer.customer_name}}</div>
              <div style="font-size:12px;color:#6B7280">{{selectedCustomer.name}}</div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <button class="nim-btn" style="background:#fff;color:#374151;border:1px solid #E5E7EB;font-size:13px" @click="openEdit(selectedCustomer.name)">
              <span v-html="icon('edit',13)"></span> Edit
            </button>
            <button class="nim-btn" style="background:none;color:#9CA3AF;border:1px solid #E5E7EB;width:32px;height:32px;padding:0;display:grid;place-items:center" @click="closeCustomer" title="Close">
              <span v-html="icon('x',14)"></span>
            </button>
          </div>
        </div>

        <!-- Tabs -->
        <div style="display:flex;border-bottom:2px solid #E5E7EB;margin-bottom:22px;gap:0">
          <button @click="activeCustomerTab='overview'"
            :style="{padding:'8px 16px',fontSize:'13.5px',fontWeight:600,border:'none',background:'none',cursor:'pointer',
              color:activeCustomerTab==='overview'?'#16a34a':'#6B7280',
              borderBottom:activeCustomerTab==='overview'?'2px solid #16a34a':'2px solid transparent',marginBottom:'-2px'}">
            Overview
          </button>
          <button @click="activeCustomerTab='transactions'"
            :style="{padding:'8px 16px',fontSize:'13.5px',fontWeight:600,border:'none',background:'none',cursor:'pointer',
              color:activeCustomerTab==='transactions'?'#16a34a':'#6B7280',
              borderBottom:activeCustomerTab==='transactions'?'2px solid #16a34a':'2px solid transparent',marginBottom:'-2px'}">
            Transactions
            <span v-if="custTxns.length" style="background:#16a34a;color:#fff;padding:1px 7px;border-radius:999px;font-size:11px;margin-left:4px">{{custTxns.length}}</span>
          </button>
          <button @click="activeCustomerTab='statement'; loadStatement()"
            :style="{padding:'8px 16px',fontSize:'13.5px',fontWeight:600,border:'none',background:'none',cursor:'pointer',
              color:activeCustomerTab==='statement'?'#16a34a':'#6B7280',
              borderBottom:activeCustomerTab==='statement'?'2px solid #16a34a':'2px solid transparent',marginBottom:'-2px'}">
            Statement
          </button>
        </div>
        <!-- Overview tab -->
        <div v-if="activeCustomerTab==='overview'" style="display:flex;gap:20px;align-items:flex-start">

          <!-- Left column ~55% -->
          <div style="flex:0 0 55%;min-width:0;display:flex;flex-direction:column;gap:14px">

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:18px">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #F3F4F6">
                <div :style="{
                  width:'44px',height:'44px',borderRadius:'50%',flexShrink:0,
                  display:'flex',alignItems:'center',justifyContent:'center',
                  fontWeight:700,fontSize:'16px',color:'#fff',
                  background: selectedCustomer.disabled ? '#9CA3AF' : 'linear-gradient(135deg,#16a34a,#15803d)'
                }">{{custInitials(selectedCustomer.customer_name)}}</div>
                <div>
                  <div style="font-size:14px;font-weight:700;color:#111827">{{ selectedCustomer.salutation ? selectedCustomer.salutation + ' ' : '' }}{{selectedCustomer.customer_name}}</div>
                  <div v-if="selectedCustomer.email_id" style="font-size:12px;color:#6B7280;margin-top:2px">{{selectedCustomer.email_id}}</div>
                </div>
                <div style="margin-left:auto;display:none;">
                  <a href="#" style="font-size:12px;color:#16a34a;text-decoration:none">Invite to Portal</a>
                </div>
              </div>
              <div style="display:flex;flex-direction:column;gap:7px">
                <div v-if="selectedCustomer.mobile_no" style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:#374151">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.63 3.18 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.6A16 16 0 0 0 15.4 16.1l.97-.97a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  <span>{{selectedCustomer.mobile_no}}</span>
                </div>
                <div v-else style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:#9CA3AF">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.63 3.18 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.6A16 16 0 0 0 15.4 16.1l.97-.97a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  <span>No phone number</span>
                </div>
              </div>
            </div>

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
              <div style="padding:12px 16px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;user-select:none" :style="!custSectionCollapsed.address?'border-bottom:1px solid #F3F4F6':''" @click="custSectionCollapsed.address=!custSectionCollapsed.address">
                <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">ADDRESS</span>
                <svg :style="{transition:'transform 0.2s',transform:custSectionCollapsed.address?'rotate(-90deg)':'rotate(0deg)'}" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2.5" stroke-linecap="round"><polyline points="18 15 12 9 6 15"/></svg>
              </div>
              <div v-show="!custSectionCollapsed.address" style="padding:14px 16px">
                <AddressManager
                  v-if="selectedCustomer.name"
                  :partyDoctype="'Customer'"
                  :partyName="selectedCustomer.name"
                  :readonly="true"
                />
              </div>
            </div>

            

          </div>

          <!-- Right column ~45% -->
          <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:14px">

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:16px">
              <div style="font-size:11.5px;color:#6B7280;margin-bottom:4px">Payment due period</div>
              <div style="font-size:14px;font-weight:600;color:#111827">{{selectedCustomer.payment_terms||'Due on Receipt'}}</div>
            </div>

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
              <div style="padding:12px 16px;border-bottom:1px solid #F3F4F6">
                <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">RECEIVABLES</span>
              </div>
              <table style="width:100%;border-collapse:collapse">
                <thead>
                  <tr style="border-bottom:1px solid #F3F4F6">
                    <th style="text-align:left;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:8px 16px">CURRENCY</th>
                    <th style="text-align:right;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:8px 12px">OUTSTANDING RECEIVABLES</th>
                    <th style="text-align:right;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:8px 16px">UNUSED CREDITS</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style="font-size:13px;font-weight:600;color:#374151;padding:10px 16px">{{ selectedCustomer.default_currency || "INR" }}</td>
                    <td style="font-size:13px;font-weight:600;text-align:right;padding:10px 12px;" :style="{color: selectedCustomer.outstanding>0?'#dc2626':'#111827'}">{{fmt(selectedCustomer.outstanding||0)}}</td>
                    <td style="font-size:13px;font-weight:600;color:#059669;text-align:right;padding:10px 16px;">{{ fmt(selectedCustomer.unused_credits||0) }}</td>
                  </tr>
                </tbody>
              </table>
              <div style="padding:10px 16px ;display:none;">
                <a href="#" style="font-size:12.5px;color:#2563EB;text-decoration:none">Enter Opening Balance</a>
              </div>
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
              <div style="padding:12px 16px;display:flex;justify-content:space-between;align-items:center;cursor:pointer;user-select:none" :style="!custSectionCollapsed.otherDetails?'border-bottom:1px solid #F3F4F6':''" @click="custSectionCollapsed.otherDetails=!custSectionCollapsed.otherDetails">
                <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">OTHER DETAILS</span>
                <svg :style="{transition:'transform 0.2s',transform:custSectionCollapsed.otherDetails?'rotate(-90deg)':'rotate(0deg)'}" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2.5" stroke-linecap="round"><polyline points="18 15 12 9 6 15"/></svg>
              </div>
              <div v-show="!custSectionCollapsed.otherDetails" style="padding:14px 16px;display:flex;flex-direction:column;gap:10px">
                <div style="display:flex;justify-content:space-between;font-size:12.5px">
                  <span style="color:#6B7280">Default Currency</span>
                  <span style="font-weight:600;color:#111827">{{selectedCustomer.default_currency||'INR'}}</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12.5px;align-items:center">
                  <span style="color:#6B7280">Portal Status</span>
                  <span style="font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px;background:#F3F4F6;color:#6B7280">● Disabled</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12.5px">
                  <span style="color:#6B7280">Customer Type</span>
                  <span style="font-weight:600;color:#111827">{{selectedCustomer.customer_type||'Company'}}</span>
                </div>
                <div v-if="selectedCustomer.tax_id" style="display:flex;justify-content:space-between;font-size:12.5px">
                  <span style="color:#6B7280">GSTIN / Tax ID</span>
                  <span style="font-weight:600;color:#111827">{{selectedCustomer.tax_id}}</span>
                </div>
              </div>
            </div>

            <div style="padding:4px 0">
              <button @click="confirmDelete(selectedCustomer)" style="background:none;border:none;cursor:pointer;color:#DC2626;font-size:12.5px;display:flex;align-items:center;gap:6px">
                <span v-html="icon('trash',13)"></span> Delete Customer
              </button>
            </div>

          </div>
        </div>

        <!-- Transactions tab -->
        <div v-else-if="activeCustomerTab==='transactions'">
          <div v-if="custTxnsLoading" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:24px;text-align:center;color:#9CA3AF">Loading transactions…</div>
          <div v-else-if="!custTxns.length" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:24px;text-align:center;color:#9CA3AF">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" stroke-width="1.5" style="margin:0 auto 12px;display:block"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <div style="font-size:14px;font-weight:600;color:#374151;margin-bottom:6px">No transactions yet</div>
            <div style="font-size:12.5px;color:#9CA3AF">Invoices and payments for {{selectedCustomer.customer_name}} will appear here.</div>
          </div>
          <div v-else style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:scroll">
            <div style="display:grid;grid-template-columns:100px 160px 100px 130px 130px auto;gap:8px;background:#F9FAFB;padding:10px 14px;font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;border-bottom:1px solid #E5E7EB">
              <span>Type</span><span>Reference</span><span>Date</span><span style="text-align:right">Amount</span><span style="text-align:right">Outstanding</span>
            </div>
            <div v-for="t in custTxns" :key="t.type+'-'+t.name"
              style="display:grid;grid-template-columns:100px 160px 100px 130px 130px auto;gap:8px;padding:9px 14px;border-bottom:1px solid #F3F4F6;font-size:12.5px;align-items:center">
              <span :style="{
                fontSize:'10.5px',fontWeight:700,padding:'2px 8px',borderRadius:'10px',display:'inline-block',width:'fit-content',
                background: t.type==='Invoice' ? '#DBEAFE' : t.type==='Payment' ? '#D1FAE5' : '#FEE2E2',
                color: t.type==='Invoice' ? '#1E40AF' : t.type==='Payment' ? '#059669' : '#991B1B'
              }">{{t.type}}</span>
              <span style="color:#2563EB;font-weight:600">{{t.name}}</span>
              <span style="color:#6B7280">{{fmtDate(t.date)}}</span>
              <span style="text-align:right;font-weight:600" :style="{color: t.amount<0 ? '#059669' : '#374151'}">{{fmt(Math.abs(t.amount))}}</span>
              <span style="text-align:right;" :style="{color: t.outstanding>0 ? '#dc2626' : '#9CA3AF'}">{{t.outstanding>0?fmt(t.outstanding):''}}</span>
             
            </div>
          </div>
        </div>

        <!-- Statement tab -->
        <div v-else-if="activeCustomerTab==='statement'">
          <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 18px;display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap">
            <button class="nim-btn" style="border:1px solid #E5E7EB" @click="loadStatement" :disabled="stmtLoading">
              <span v-if="stmtLoading">Loading…</span><span v-else>Refresh</span>
            </button>
            <div style="margin-left:auto;display:flex;gap:8px">
              <button v-if="stmt && stmt.email" class="nim-btn" style="border:1px solid #E5E7EB" @click="sendStatement" :disabled="sendingStmt">
                {{sendingStmt ? 'Sending…' : '📧 Send Statement'}}
              </button>
            </div>
          </div>
          <div v-if="stmtLoading" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:24px;text-align:center;color:#9CA3AF">Loading statement…</div>
          <div v-else-if="!stmt" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:40px;text-align:center;color:#9CA3AF">
            <div style="font-size:32px;margin-bottom:8px">📄</div>
            <div style="font-size:13.5px;font-weight:600;color:#374151;margin-bottom:4px">No statement loaded</div>
            <button class="nim-btn nim-btn-primary" @click="loadStatement">Load Statement</button>
          </div>
          <template v-else>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:14px">
              <div style="background:#FFF5F5;border:1px solid #FFC9C9;border-radius:10px;padding:14px 16px">
                <div style="font-size:11px;color:#C92A2A;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Total Outstanding</div>
                <div style="font-size:20px;font-weight:700;color:#C92A2A">₹{{fmtStmt(stmt.total_outstanding)}}</div>
              </div>
              <div style="background:#FFF9DB;border:1px solid #FFD43B;border-radius:10px;padding:14px 16px">
                <div style="font-size:11px;color:#E67700;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Overdue</div>
                <div style="font-size:20px;font-weight:700;color:#E67700">₹{{fmtStmt(stmt.overdue_amount)}}</div>
              </div>
              <div style="background:#F3F4F6;border:1px solid #E5E7EB;border-radius:10px;padding:14px 16px">
                <div style="font-size:11px;color:#6B7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Open Invoices</div>
                <div style="font-size:20px;font-weight:700;color:#111827">{{stmt.invoices.length}}</div>
              </div>
            </div>
            <div v-if="!stmt.email" style="margin-bottom:12px;padding:10px 14px;background:#FFF9DB;border:1px solid #FFD43B;border-radius:8px;font-size:12.5px;color:#876800">
              ⚠️ No email on file — add an email to enable sending this statement.
            </div>
            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
              <div v-if="!stmt.invoices.length" style="padding:24px;text-align:center;color:#9CA3AF;font-size:13px">No outstanding invoices</div>
              <template v-else>
                <div style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px;padding:12px 14px;background:#F9FAFB;border-bottom:1px solid #E5E7EB">OUTSTANDING INVOICES</div>
                <div v-for="inv in stmt.invoices" :key="inv.name"
                  style="display:grid;grid-template-columns:160px 100px 100px auto 80px;gap:8px;padding:8px 14px;border-bottom:1px solid #F3F4F6;font-size:12.5px;align-items:center">
                  <span style="color:#2563EB;font-weight:600">{{inv.name}}</span>
                  <span style="color:#6B7280">{{inv.posting_date}}</span>
                  <span style="color:#6B7280">{{inv.due_date}}</span>
                  <span style="text-align:right;font-weight:600">₹{{fmtStmt(inv.outstanding_amount)}}</span>
                  <span :style="'padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;text-align:center;'+(inv.is_overdue?'background:#FFF5F5;color:#C92A2A':'background:#EBFBEE;color:#2F9E44')">
                    {{inv.is_overdue ? 'Overdue' : 'Due'}}
                  </span>
                </div>
              </template>
            </div>
          </template>
        </div>

      </div>
    </div>
  </div>

  <!-- Drawer -->
  <Teleport to="body">
    <div v-if="showDrawer" class="inv-drawer-bg" @click.self="showDrawer=false">
      <div class="inv-drawer-panel" :class="{open:showDrawer}" style="width:680px;max-width:98vw">

        <div class="inv-dh" style="background:linear-gradient(135deg,#16a34a,#15803d);padding:18px 24px">
          <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
            <div style="width:40px;height:40px;border-radius:10px;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;flex-shrink:0">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <div style="min-width:0">
              <div class="inv-dh-title">{{drawerMode==='add'?'New Customer':'Edit Customer'}}</div>
              <div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:1px">{{drawerMode==='edit'?form.name:'Fill in customer details'}}</div>
            </div>
          </div>
          <button class="inv-dclose" @click="showDrawer=false" v-html="icon('x',14)"></button>
        </div>

        <div class="inv-view-tabs">
          <button v-for="t in [{k:'overview',l:'Overview'},{k:'address',l:'Address'},{k:'other',l:'Other Details'},{k:'bank',l:'Bank Details'},{k:'remarks',l:'Remarks'}]"
            :key="t.k" @click="drawerTab=t.k"
            class="inv-vtab" :class="{active: drawerTab===t.k}">
            {{t.l}}
          </button>
        </div>

        <div v-if="drawerLoading" style="flex:1;display:grid;place-items:center;color:#9ca3af;font-size:13px;padding:40px">
          Loading customer…
        </div>

        <div v-else class="inv-dbody" style="padding:24px;overflow-y:auto;flex:1">

          <!-- Overview Tab -->
          <template v-if="drawerTab==='overview'">

            <div style="margin-bottom:20px">
              <label class="inv-lbl" style="margin-bottom:8px;display:block">Customer Type</label>
              <div style="display:flex;gap:24px">
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13.5px;font-weight:500;color:#374151">
                  <input type="radio" v-model="form.customer_type" value="Company" style="width:16px;height:16px;accent-color:#3B5BDB;cursor:pointer"/>
                  Business
                </label>
                <label style="display:flex;align-items:center;gap:8px;cursor:pointer;font-size:13.5px;font-weight:500;color:#374151">
                  <input type="radio" v-model="form.customer_type" value="Individual" style="width:16px;height:16px;accent-color:#3B5BDB;cursor:pointer"/>
                  Individual
                </label>
              </div>
            </div>

            <div style="margin-bottom:20px">
              <label class="inv-lbl" style="margin-bottom:8px;display:block">GST Treatment</label>
              <div style="display:flex;flex-wrap:wrap;gap:8px">
                <button v-for="opt in GST_TREATMENT_OPTIONS" :key="opt" @click="form.gst_treatment=opt" type="button"
                  :style="'padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;cursor:pointer;font-family:inherit;transition:all .15s;border:1.5px solid '+(form.gst_treatment===opt?GST_RULES[opt].badge.color:'#e2e8f0')+';background:'+(form.gst_treatment===opt?GST_RULES[opt].badge.bg:'#fff')+';color:'+(form.gst_treatment===opt?GST_RULES[opt].badge.color:'#6b7280')">
                  {{opt}}
                </button>
              </div>
              <div v-if="activeRule.hint" style="margin-top:8px;padding:8px 12px;background:#f8f9fc;border-left:3px solid;border-radius:0 6px 6px 0;font-size:12px;color:#6b7280;line-height:1.5"
                :style="{borderColor: activeRule.badge.color}">
                <span :style="{color:activeRule.badge.color,fontWeight:'600'}">{{activeRule.badge.label}}:</span> {{activeRule.hint}}
                <span v-if="activeRule.taxType"> · Tax: <strong>{{activeRule.taxType}}</strong></span>
              </div>
            </div>

            <div style="margin-bottom:16px">
              <label class="inv-lbl" style="margin-bottom:8px;display:block">Primary Contact</label>
              <div style="display:grid;grid-template-columns:140px 1fr 1fr;gap:10px">
                <select v-model="form.salutation" class="inv-fi" style="cursor:pointer">
                  <option value="">Salutation</option>
                  <option>Mr.</option><option>Ms.</option><option>Mrs.</option><option>Dr.</option><option>Prof.</option>
                </select>
                <div style="position:relative">
                  <input v-model="form.first_name" class="inv-fi" placeholder="First Name"
                    :style="formErrors.first_name?'border-color:#dc2626;background:#fff5f5':''"
                    @input="form.first_name=form.first_name.replace(/[^a-zA-Z\s.']/g,''); delete formErrors.first_name"
                    @blur="validateField('first_name')"/>
                  <div v-if="formErrors.first_name" style="position:absolute;left:0;top:100%;margin-top:3px;font-size:11.5px;color:#dc2626;white-space:nowrap">{{formErrors.first_name}}</div>
                </div>
                <div style="position:relative">
                  <input v-model="form.last_name" class="inv-fi" placeholder="Last Name"
                    :style="formErrors.last_name?'border-color:#dc2626;background:#fff5f5':''"
                    @input="form.last_name=form.last_name.replace(/[^a-zA-Z\s.']/g,''); delete formErrors.last_name"
                    @blur="validateField('last_name')"/>
                  <div v-if="formErrors.last_name" style="position:absolute;left:0;top:100%;margin-top:3px;font-size:11.5px;color:#dc2626;white-space:nowrap">{{formErrors.last_name}}</div>
                </div>
              </div>
            </div>

            <div style="margin-bottom:16px">
              <label class="inv-lbl">Company Name <span v-if="form.customer_type==='Company'" class="nim-req">*</span></label>
              <input v-model="form.company_name" class="inv-fi" placeholder="Company name"
                :style="formErrors.company_name?'border-color:#dc2626;background:#fff5f5':''"
                @input="delete formErrors.company_name"
                @blur="validateField('company_name')"/>
              <div v-if="formErrors.company_name" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.company_name}}
              </div>
            </div>

            <div style="margin-bottom:16px">
              <label class="inv-lbl" style="display:flex;justify-content:space-between">
                <span>Display Name <span class="nim-req">*</span></span>
                <span :style="{fontSize:'11px',color:form.customer_name.length>90?'#dc2626':form.customer_name.length>0?'#9ca3af':'transparent'}">{{form.customer_name.length}}/100</span>
              </label>
              <input v-model="form.customer_name" class="inv-fi" maxlength="100"
                :style="formErrors.customer_name?'border-color:#dc2626;background:#fff5f5':''"
                placeholder="Name shown on invoices and orders"
                @input="form.customer_name=form.customer_name.replace(/[^a-zA-Z\s.'-]/g,''); delete formErrors.customer_name"
                @blur="validateField('customer_name')"/>
              <div v-if="formErrors.customer_name" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.customer_name}}
              </div>
            </div>

            <transition name="gst-field">
              <div v-if="activeRule.showGstin || activeRule.showPan"
                style="display:grid;gap:14px;margin-bottom:16px"
                :style="{gridTemplateColumns: (activeRule.showGstin && activeRule.showPan) ? '1fr 1fr' : '1fr'}">
                <div v-if="activeRule.showGstin">
                  <label class="inv-lbl">
                    GSTIN / Tax ID
                    <span v-if="activeRule.requireGstin" class="nim-req">*</span>
                    <span v-else style="font-size:11px;font-weight:400;color:#9ca3af;margin-left:4px">(optional)</span>
                  </label>
                  <input v-model="form.tax_id" class="inv-fi"
                    :style="formErrors.tax_id?'border-color:#dc2626;background:#fff5f5':''"
                    :placeholder="activeRule.gstinPlaceholder||'27AAPFU0939F1ZV'"
                    style="font-family:var(--mono);letter-spacing:.04em"
                    @input="form.tax_id=form.tax_id.toUpperCase();delete formErrors.tax_id"/>
                  <div v-if="formErrors.tax_id" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                    {{formErrors.tax_id}}
                  </div>
                  <div v-else-if="form.tax_id && !formErrors.tax_id && GSTIN_REGEX.test(form.tax_id)"
                    style="margin-top:4px;font-size:12px;color:#2f9e44;display:flex;align-items:center;gap:4px">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                    Valid GSTIN
                  </div>
                </div>
                <div v-if="activeRule.showPan">
                  <label class="inv-lbl">PAN Number <span style="font-size:11px;font-weight:400;color:#9ca3af">(optional)</span></label>
                  <input v-model="form.pan_no" class="inv-fi" placeholder="ABCDE1234F" maxlength="10"
                    style="font-family:var(--mono);letter-spacing:.04em"
                    :style="formErrors.pan_no?'border-color:#dc2626;background:#fff5f5':''"
                    @input="form.pan_no=form.pan_no.toUpperCase().replace(/[^A-Z0-9]/g,''); delete formErrors.pan_no"
                    @blur="validateField('pan_no')"/>
                  <div v-if="formErrors.pan_no" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                    {{formErrors.pan_no}}
                  </div>
                  <div v-else-if="form.pan_no && PAN_REGEX.test(form.pan_no)" style="margin-top:4px;font-size:12px;color:#2f9e44;display:flex;align-items:center;gap:4px">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                    Valid PAN
                  </div>
                </div>
              </div>
            </transition>

            <div style="height:1px;background:#e8ecf0;margin-bottom:20px"></div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:16px">
              <div>
                <label class="inv-lbl">Email Address</label>
                <input v-model="form.email_id" class="inv-fi" placeholder="name@company.com"
                  :style="formErrors.email_id?'border-color:#dc2626;background:#fff5f5':form.email_id&&EMAIL_REGEX.test(form.email_id)?'border-color:#2f9e44':''"
                  @input="delete formErrors.email_id"
                  @blur="validateField('email_id')"/>
                <div v-if="formErrors.email_id" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                  {{formErrors.email_id}}
                </div>
                <div v-else-if="form.email_id&&EMAIL_REGEX.test(form.email_id)" style="margin-top:4px;font-size:12px;color:#2f9e44;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Valid email
                </div>
              </div>
              <div>
                <label class="inv-lbl">Work Phone</label>
                <input v-model="form.phone" class="inv-fi" placeholder="022-12345678"
                  :style="formErrors.phone?'border-color:#dc2626;background:#fff5f5':''"
                  @input="form.phone=form.phone.replace(/[^\d+\-\s()]/g,''); delete formErrors.phone"
                  @blur="validateField('phone')"/>
                <div v-if="formErrors.phone" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                  {{formErrors.phone}}
                </div>
              </div>
              <div>
                <label class="inv-lbl">Mobile</label>
                <div style="display:flex;gap:0">
                  <select v-model="form.mobile_code" class="inv-fi" style="width:90px;border-right:none;border-radius:8px 0 0 8px;background:#f8f9fc;cursor:pointer;flex-shrink:0;padding:0 6px"
                    @change="delete formErrors.mobile_no; if(form.mobile_no) validateField('mobile_no')">
                    <option value="+91">🇮🇳 +91</option>
                    <option value="+1">🇺🇸 +1</option>
                    <option value="+44">🇬🇧 +44</option>
                    <option value="+61">🇦🇺 +61</option>
                    <option value="+971">🇦🇪 +971</option>
                    <option value="+65">🇸🇬 +65</option>
                    <option value="+49">🇩🇪 +49</option>
                    <option value="+33">🇫🇷 +33</option>
                    <option value="+60">🇲🇾 +60</option>
                    <option value="+94">🇱🇰 +94</option>
                    <option value="+966">🇸🇦 +966</option>
                    <option value="+92">🇵🇰 +92</option>
                    <option value="+880">🇧🇩 +880</option>
                    <option value="+977">🇳🇵 +977</option>
                    <option value="+27">🇿🇦 +27</option>
                    <option value="+55">🇧🇷 +55</option>
                    <option value="+86">🇨🇳 +86</option>
                    <option value="+81">🇯🇵 +81</option>
                  </select>
                  <input v-model="form.mobile_no" class="inv-fi" style="border-radius:0 8px 8px 0;flex:1" placeholder="98765 43210"
                    :style="formErrors.mobile_no?'border-color:#dc2626;background:#fff5f5':form.mobile_no&&!formErrors.mobile_no&&form.mobile_no.replace(/\D/g,'').length>6?'border-color:#2f9e44':''"
                    @input="form.mobile_no=form.mobile_no.replace(/\D/g,''); delete formErrors.mobile_no"
                    @blur="validateField('mobile_no')"/>
                </div>
                <div v-if="formErrors.mobile_no" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                  {{formErrors.mobile_no}}
                </div>
                <div v-else-if="form.mobile_no&&!formErrors.mobile_no&&(form.mobile_code==='+91'?form.mobile_no.replace(/\D/g,'').length===10:form.mobile_no.replace(/\D/g,'').length>=7)" style="margin-top:4px;font-size:12px;color:#2f9e44;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Valid mobile number
                </div>
              </div>
              <div>
                <label class="inv-lbl">Website</label>
                <input v-model="form.website" class="inv-fi" placeholder="https://company.com"
                  :style="formErrors.website?'border-color:#dc2626;background:#fff5f5':form.website&&URL_REGEX.test(form.website)?'border-color:#2f9e44':''"
                  @input="delete formErrors.website"
                  @blur="validateField('website')"/>
                <div v-if="formErrors.website" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                  {{formErrors.website}}
                </div>
                <div v-else-if="form.website&&URL_REGEX.test(form.website)" style="margin-top:4px;font-size:12px;color:#2f9e44;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                  Valid URL
                </div>
              </div>
            </div>

            <div style="height:1px;background:#e8ecf0;margin-bottom:20px"></div>

            <div class="inv-sec-lbl" style="margin-top:0">Billing Preferences</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:20px">
              <div>
                <label class="inv-lbl">Currency</label>
                <select v-model="form.default_currency" class="inv-fi" style="cursor:pointer">
                  <option>INR</option><option>USD</option><option>EUR</option><option>GBP</option><option>AED</option><option>SGD</option><option>JPY</option><option>CAD</option><option>AUD</option>
                </select>
              </div>
              <div>
                <label class="inv-lbl">Payment Terms</label>
                <select v-model="form.payment_terms" class="inv-fi" style="cursor:pointer">
                  <option value="">— Select —</option>
                  <option>Net 7</option><option>Net 15</option><option>Net 30</option><option>Net 45</option><option>Net 60</option>
                  <option>Due on Receipt</option><option>End of Month</option>
                </select>
              </div>
              <div>
                <label class="inv-lbl">Credit Limit ({{ currencySymbol }})</label>
                <input v-model.number="form.credit_limit" type="number" min="0" class="inv-fi" placeholder="0 = unlimited"
                  :style="formErrors.credit_limit?'border-color:#dc2626;background:#fff5f5':''"
                  @input="delete formErrors.credit_limit"
                  @blur="validateField('credit_limit')"/>
                <div v-if="formErrors.credit_limit" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                  {{formErrors.credit_limit}}
                </div>
              </div>
            </div>

            <div v-if="drawerMode==='edit'" style="padding:14px 16px;background:#fff5f5;border-radius:8px;border:1px solid #fecaca;display:flex;align-items:center;gap:10px;cursor:pointer" @click="form.disabled=form.disabled?0:1">
              <input type="checkbox" :checked="!!form.disabled" @click.stop="form.disabled=form.disabled?0:1" style="width:16px;height:16px;accent-color:#dc2626;cursor:pointer;flex-shrink:0"/>
              <div>
                <div style="font-size:13px;font-weight:600;color:#dc2626">Disable Customer</div>
                <div style="font-size:12px;color:#9ca3af;margin-top:1px">Disabled customers won't appear in invoice and order dropdowns</div>
              </div>
            </div>
          </template>

          <!-- Address Tab -->
          <template v-else-if="drawerTab==='address'">
            <AddressManager
              partyDoctype="Customer"
              :partyName="drawerMode==='edit' ? form.name : ''"
              v-model="pendingAddresses"
              @addressSaved="load"
              @addressDeleted="load"
            />
          </template>

          <!-- Other Details Tab -->
          <template v-else-if="drawerTab==='other'">
            <div class="inv-sec-lbl" style="margin-top:0">Tax &amp; Compliance</div>

            <div style="display:flex;align-items:center;gap:8px;margin-bottom:16px;padding:10px 14px;border-radius:8px;border:1px solid #e8ecf0;background:#fafbfd">
              <span style="font-size:12px;color:#6b7280;font-weight:500">Current GST Treatment:</span>
              <span :style="'padding:3px 10px;border-radius:12px;font-size:12px;font-weight:700;background:'+activeRule.badge.bg+';color:'+activeRule.badge.color">
                {{form.gst_treatment}}
              </span>
              <span style="font-size:12px;color:#9ca3af">·</span>
              <span style="font-size:12px;font-weight:600;color:#374151">Tax: {{activeRule.taxType}}</span>
              <button @click="drawerTab='overview'" style="margin-left:auto;font-size:12px;color:#3B5BDB;background:none;border:none;cursor:pointer;font-weight:600;font-family:inherit">Change →</button>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px">
              <transition name="gst-field">
                <div v-if="activeRule.showPlaceOfSupply">
                  <label class="inv-lbl">
                    Place of Supply
                    <span v-if="activeRule.requirePlaceOfSupply" class="nim-req">*</span>
                  </label>
                  <select v-model="form.place_of_supply" class="inv-fi" style="cursor:pointer"
                    :style="formErrors.place_of_supply?'border-color:#dc2626;background:#fff5f5':''"
                    @change="delete formErrors.place_of_supply">
                    <option value="">— Select State —</option>
                    <option v-for="s in PLACE_OF_SUPPLY" :key="s" :value="s">{{s}}</option>
                  </select>
                  <div v-if="formErrors.place_of_supply" style="margin-top:4px;font-size:12px;color:#dc2626">{{formErrors.place_of_supply}}</div>
                </div>
              </transition>
              <div v-if="!activeRule.showPlaceOfSupply" style="padding:12px 14px;border-radius:8px;background:#f0f9ff;border:1px solid #bae6fd;font-size:12.5px;color:#0369a1;line-height:1.5;display:flex;align-items:flex-start;gap:8px">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0;margin-top:1px"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                Place of Supply not applicable for <strong>{{form.gst_treatment}}</strong> customers.
              </div>
              <div>
                <label class="inv-lbl">Customer Source</label>
                <select v-model="form.source" class="inv-fi" style="cursor:pointer">
                  <option value="">— Select —</option>
                  <option>Cold Calling</option><option>Email</option><option>Existing Customer</option>
                  <option>Partner</option><option>Campaign</option><option>Website</option><option>Referral</option><option>Word of Mouth</option><option>Other</option>
                </select>
              </div>
            </div>

            <div class="inv-sec-lbl">Opening Balance</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px">
              <div>
                <label class="inv-lbl">Opening Balance (₹)</label>
                <input v-model.number="form.opening_balance" type="number" min="0" class="inv-fi" placeholder="0.00"
                  :style="formErrors.opening_balance?'border-color:#dc2626;background:#fff5f5':''"
                  @input="delete formErrors.opening_balance"
                  @blur="validateField('opening_balance')"/>
                <div v-if="formErrors.opening_balance" style="margin-top:4px;font-size:12px;color:#dc2626">{{formErrors.opening_balance}}</div>
              </div>
            </div>
          </template>

          <!-- Bank Tab -->
          <template v-else-if="drawerTab==='bank'">
            <div class="inv-sec-lbl" style="margin-top:0">Bank Account</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
              <div style="grid-column:span 2">
                <label class="inv-lbl">Bank Name</label>
                <input v-model="form.bank_name" class="inv-fi" placeholder="HDFC Bank, SBI, ICICI…"/>
              </div>
              <div>
                <label class="inv-lbl">Account Number <span style="font-size:11px;font-weight:400;color:#9ca3af">(9–18 digits)</span></label>
                <input v-model="form.bank_account_no" class="inv-fi" placeholder="XXXXXXXXXXXXXXXX" maxlength="18" style="font-family:var(--mono)"
                  :style="formErrors.bank_account_no?'border-color:#dc2626;background:#fff5f5':form.bank_account_no&&!formErrors.bank_account_no&&/^\d{9,18}$/.test(form.bank_account_no)?'border-color:#2f9e44':''"
                  @input="form.bank_account_no=form.bank_account_no.replace(/\D/g,''); delete formErrors.bank_account_no"
                  @blur="validateField('bank_account_no')"/>
                <div v-if="formErrors.bank_account_no" style="margin-top:4px;font-size:12px;color:#dc2626">{{formErrors.bank_account_no}}</div>
                <div v-else-if="form.bank_account_no&&/^\d{9,18}$/.test(form.bank_account_no)" style="margin-top:4px;font-size:12px;color:#2f9e44">Valid account number</div>
              </div>
              <div>
                <label class="inv-lbl">IFSC Code <span style="font-size:11px;font-weight:400;color:#9ca3af">(AAAA0XXXXXX)</span></label>
                <input v-model="form.bank_ifsc" class="inv-fi" placeholder="HDFC0001234" maxlength="11" style="font-family:var(--mono)"
                  :style="formErrors.bank_ifsc?'border-color:#dc2626;background:#fff5f5':form.bank_ifsc&&IFSC_REGEX.test(form.bank_ifsc)?'border-color:#2f9e44':''"
                  @input="form.bank_ifsc=form.bank_ifsc.toUpperCase().replace(/[^A-Z0-9]/g,''); delete formErrors.bank_ifsc"
                  @blur="validateField('bank_ifsc')"/>
                <div v-if="formErrors.bank_ifsc" style="margin-top:4px;font-size:12px;color:#dc2626">{{formErrors.bank_ifsc}}</div>
                <div v-else-if="form.bank_ifsc&&IFSC_REGEX.test(form.bank_ifsc)" style="margin-top:4px;font-size:12px;color:#2f9e44">Valid IFSC</div>
              </div>
            </div>
          </template>

          <!-- Remarks Tab -->
          <template v-else-if="drawerTab==='remarks'">
            <div class="inv-sec-lbl" style="margin-top:0">Internal Notes</div>
            <textarea v-model="form.notes" class="inv-fi" rows="14" style="resize:vertical;line-height:1.6;min-height:280px" placeholder="Add any internal notes about this customer — payment behaviour, communication preferences, account history…"></textarea>
          </template>

        </div>

        <!-- Footer -->
        <div class="inv-dfooter" style="border-top:1px solid #e8ecf0;padding:14px 24px;background:#fafbfd">
          <button class="form-btn form-btn-outline" @click="showDrawer=false">Cancel</button>
          <button class="form-btn form-btn-primary" @click="saveCustomer" :disabled="saving" style="background:#16a34a;border-color:#16a34a;min-width:140px;position:relative">
            <span v-if="saving" v-html="icon('refresh',13)" style="animation:spin 1s linear infinite"></span>
            {{saving ? 'Saving…' : (drawerMode==='add' ? 'Create Customer' : 'Save Changes')}}
            <span v-if="Object.keys(formErrors).length && !saving"
              style="position:absolute;top:-6px;right:-6px;background:#dc2626;color:#fff;border-radius:10px;font-size:10px;font-weight:700;padding:1px 5px;min-width:16px;text-align:center;line-height:16px">
              {{Object.keys(formErrors).length}}
            </span>
          </button>
        </div>

      </div>
    </div>
  </Teleport>

  <!-- Delete Confirm Modal -->
  <Teleport to="body">
    <div v-if="showDelete" class="nim-overlay" @click.self="showDelete=false">
      <div class="nim-dialog" style="max-width:420px">
        <div class="nim-header" style="background:linear-gradient(135deg,#dc2626,#b91c1c)">
          <div class="nim-header-left">
            <div class="nim-header-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
            </div>
            <div class="nim-header-title">Delete Customer?</div>
          </div>
          <button class="nim-close" @click="showDelete=false" v-html="icon('x',15)"></button>
        </div>
        <div class="nim-body" style="padding:20px 24px">
          <p style="font-size:14px;color:#374151;line-height:1.6">
            Are you sure you want to delete <strong>{{deleteTarget?.customer_name}}</strong>?
            This action cannot be undone.
          </p>
        </div>
        <div class="inv-dfooter">
          <button class="form-btn form-btn-outline" @click="showDelete=false">Cancel</button>
          <button @click="doDelete" :disabled="deleting"
            style="height:37px;padding:0 18px;border-radius:8px;font-size:13.5px;font-weight:600;cursor:pointer;font-family:inherit;border:none;background:#dc2626;color:#fff;display:inline-flex;align-items:center;gap:7px">
            <span v-if="deleting" v-html="icon('refresh',13)" style="animation:spin 1s linear infinite"></span>
            {{deleting ? 'Deleting…' : 'Yes, Delete'}}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

</div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from "vue";
import { apiList, apiGET, apiSave, apiDelete, apiPOST, resolveCompany } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import AddressManager from "../components/AddressManager.vue";
import { fmt, fmtDate } from "../utils/format.js";
import { icon } from "../utils/icons.js";
import { COUNTRIES, statesFor } from "../composables/useCountryState.js";
import {
  EMAIL_REGEX, GSTIN_REGEX, PAN_REGEX, IFSC_REGEX, URL_REGEX,
  validateMobile, validatePhone, validatePincode, sanitizePincode, pincodePlaceholder, pincodeHint,
} from "../composables/useValidation.js";

const { toast } = useToast();

// ── Static option lists, factored out of inline template arrays in legacy ──
// COUNTRIES and statesFor() imported from useCountryState.js
const PLACE_OF_SUPPLY = [
  "01-Jammu and Kashmir","02-Himachal Pradesh","03-Punjab","04-Chandigarh","05-Uttarakhand",
  "06-Haryana","07-Delhi","08-Rajasthan","09-Uttar Pradesh","10-Bihar","11-Sikkim","12-Arunachal Pradesh",
  "13-Nagaland","14-Manipur","15-Mizoram","16-Tripura","17-Meghalaya","18-Assam","19-West Bengal",
  "20-Jharkhand","21-Odisha","22-Chhattisgarh","23-Madhya Pradesh","24-Gujarat","25-Daman and Diu",
  "26-Dadra and Nagar Haveli","27-Maharashtra","28-Andhra Pradesh","29-Karnataka","30-Goa","31-Lakshadweep",
  "32-Kerala","33-Tamil Nadu","34-Puducherry","35-Andaman and Nicobar Islands","36-Telangana",
  "37-Andhra Pradesh (New)","38-Ladakh",
];

// ── State ──
const list = ref([]);
const loading = ref(true);
const search = ref("");
const selectedRows = ref(new Set());
const bulkBusy = ref(false);

function toggleRow(name) {
  const s = new Set(selectedRows.value);
  s.has(name) ? s.delete(name) : s.add(name);
  selectedRows.value = s;
}
function clearSelection() { selectedRows.value = new Set(); }
const activeFilter = ref("all");
const showDrawer = ref(false);
const drawerMode = ref("add");
const drawerLoading = ref(false);
const saving = ref(false);
const showDelete = ref(false);
const deleteTarget = ref(null);
const deleting = ref(false);
const drawerTab = ref("overview");
const formErrors = reactive({});
const shipSameAsBilling = ref(false);
const pendingAddresses = ref([]);

// ── GST Treatment rules ──
const GST_RULES = {
  "Registered Business": {
    badge: { label: "Registered", bg: "#EBFBEE", color: "#2F9E44" },
    showGstin: true, requireGstin: true,
    showPan: true, requirePan: false,
    showPlaceOfSupply: true, requirePlaceOfSupply: true,
    requireIndiaCountry: false,
    taxType: "GST",
    hint: "GSTIN is mandatory for Registered Businesses.",
    gstinPlaceholder: "27AAPFU0939F1ZV",
  },
  "Unregistered Business": {
    badge: { label: "Unregistered", bg: "#FFF3BF", color: "#E67700" },
    showGstin: false, requireGstin: false,
    showPan: true, requirePan: false,
    showPlaceOfSupply: true, requirePlaceOfSupply: true,
    requireIndiaCountry: false,
    taxType: "GST",
    hint: "No GSTIN required. Tax will be applied based on Place of Supply.",
  },
  "Overseas": {
    badge: { label: "Overseas", bg: "#E7F5FF", color: "#1971C2" },
    showGstin: false, requireGstin: false,
    showPan: false, requirePan: false,
    showPlaceOfSupply: false, requirePlaceOfSupply: false,
    requireIndiaCountry: false,
    taxType: "Zero Rated (Export/LUT)",
    hint: "Exports are zero-rated under GST. Raise invoices under LUT/Bond without charging IGST, or charge IGST and claim refund. No Indian GSTIN required.",
    countryNote: "Set country to the customer's country (outside India).",
  },
  "SEZ": {
    badge: { label: "SEZ", bg: "#F3F0FF", color: "#2563eb" },
    showGstin: true, requireGstin: true,
    showPan: true, requirePan: false,
    showPlaceOfSupply: true, requirePlaceOfSupply: true,
    requireIndiaCountry: false,
    taxType: "GST 0%",
    hint: "Supplies to SEZ are zero-rated. GSTIN is mandatory.",
    gstinPlaceholder: "SEZ unit GSTIN",
  },
  "Consumer": {
    badge: { label: "Consumer", bg: "#F8F9FA", color: "#495057" },
    showGstin: false, requireGstin: false,
    showPan: false, requirePan: false,
    showPlaceOfSupply: false, requirePlaceOfSupply: false,
    requireIndiaCountry: false,
    taxType: "GST",
    hint: "B2C customer. No GSTIN required.",
  },
};
const GST_TREATMENT_OPTIONS = Object.keys(GST_RULES);

const FIELD_TAB = {
  customer_name: "overview", first_name: "overview", last_name: "overview",
  company_name: "overview", email_id: "overview", mobile_no: "overview",
  phone: "overview", website: "overview", credit_limit: "overview",
  tax_id: "overview", pan_no: "overview",
  place_of_supply: "other", opening_balance: "other",
  pincode: "address", ship_pincode: "address",
  bank_account_no: "bank", bank_ifsc: "bank",
};

// ── Form state ──
const form = reactive({
  name: "",
  customer_name: "", customer_type: "Company", salutation: "",
  first_name: "", last_name: "", company_name: "",
  gst_treatment: "Registered Business",
  tax_id: "", default_currency: "INR", credit_limit: 0,
  email_id: "", mobile_code: "+91", mobile_no: "", phone: "", website: "",
  address_line1: "", address_line2: "",
  city: "", state: "", pincode: "", country: "India",
  ship_address_line1: "", ship_address_line2: "",
  ship_city: "", ship_state: "", ship_pincode: "", ship_country: "India",
  payment_terms: "", place_of_supply: "", source: "",
  pan_no: "", opening_balance: 0,
  bank_name: "", bank_account_no: "", bank_ifsc: "",
  notes: "", disabled: 0,
});

const activeRule = computed(() => GST_RULES[form.gst_treatment] || GST_RULES["Registered Business"]);

const currencySymbol = computed(() =>
  ({ INR: "₹", USD: "$", EUR: "€", GBP: "£", AED: "د.إ", SGD: "S$" }[form.default_currency] || "₹")
);

// Clear GSTIN/POS errors when treatment changes
watch(() => form.gst_treatment, () => {
  delete formErrors.tax_id;
  delete formErrors.place_of_supply;
  if (!activeRule.value.showGstin) form.tax_id = "";
  if (!activeRule.value.showPlaceOfSupply) form.place_of_supply = "";
});

function validateField(field) {
  delete formErrors[field];
  const rule = activeRule.value;
  const v = form[field];
  const s = typeof v === "string" ? v.trim() : v;

  if (field === "customer_name") {
    if (!s) formErrors.customer_name = "Display name is required";
    else if (s.length < 2) formErrors.customer_name = "Name must be at least 2 characters";
    else if (s.length > 100) formErrors.customer_name = "Name must not exceed 100 characters";
  }
  if (field === "first_name" && s && !/^[\p{L}\s.'\-]+$/u.test(s))
    formErrors.first_name = "First name must contain letters only";
  if (field === "last_name" && s && !/^[\p{L}\s.'\-]+$/u.test(s))
    formErrors.last_name = "Last name must contain letters only";
  if (field === "company_name" && form.customer_type === "Company" && !s)
    formErrors.company_name = "Company name is required for Business customers";
  if (field === "email_id" && s && !EMAIL_REGEX.test(s))
    formErrors.email_id = "Invalid email address";
  if (field === "mobile_no" && s) {
    const err = validateMobile(s.replace(/\D/g, ""), form.mobile_code);
    if (err) formErrors.mobile_no = err;
  }
  if (field === "phone" && s) {
    const err = validatePhone(s);
    if (err) formErrors.phone = err;
  }
  if (field === "website" && s && !URL_REGEX.test(s))
    formErrors.website = "Website must start with http:// or https://";
  if (field === "credit_limit" && v < 0)
    formErrors.credit_limit = "Credit limit cannot be negative";
  if (field === "tax_id") {
    if (rule.requireGstin && !s)
      formErrors.tax_id = "GSTIN is required for " + form.gst_treatment;
    else if (rule.showGstin && s && !GSTIN_REGEX.test(s))
      formErrors.tax_id = "Invalid GSTIN format (e.g. 27AAPFU0939F1ZV)";
  }
  if (field === "pan_no" && s && !PAN_REGEX.test(s))
    formErrors.pan_no = "Invalid PAN format (e.g. ABCDE1234F)";
  if (field === "place_of_supply" && rule.requirePlaceOfSupply && !v)
    formErrors.place_of_supply = "Place of Supply is required";
  if (field === "pincode" && s) {
    const err = validatePincode(s, form.country);
    if (err) formErrors.pincode = err;
  }
  if (field === "ship_pincode" && s) {
    const err = validatePincode(s, form.ship_country);
    if (err) formErrors.ship_pincode = err;
  }
  if (field === "opening_balance" && v < 0)
    formErrors.opening_balance = "Opening balance cannot be negative";
  if (field === "bank_account_no" && s && !/^\d{9,18}$/.test(s))
    formErrors.bank_account_no = "Account number must be 9–18 digits";
  if (field === "bank_ifsc" && s && !IFSC_REGEX.test(s))
    formErrors.bank_ifsc = "Invalid IFSC code (e.g. HDFC0001234)";
}

function validateCustomerForm() {
  Object.keys(formErrors).forEach((k) => delete formErrors[k]);
  const rule = activeRule.value;

  const cn = (form.customer_name || "").trim();
  if (!cn) formErrors.customer_name = "Display name is required";
  else if (cn.length < 2) formErrors.customer_name = "Name must be at least 2 characters";
  else if (cn.length > 100) formErrors.customer_name = "Name must not exceed 100 characters";
  if (form.customer_type === "Company" && !form.company_name.trim())
    formErrors.company_name = "Company name is required for Business customers";
  if (form.first_name && !/^[\p{L}\s.'\-]+$/u.test(form.first_name.trim()))
    formErrors.first_name = "First name must contain letters only";
  if (form.last_name && !/^[\p{L}\s.'\-]+$/u.test(form.last_name.trim()))
    formErrors.last_name = "Last name must contain letters only";
  if (form.email_id && !EMAIL_REGEX.test(form.email_id.trim()))
    formErrors.email_id = "Invalid email address";
  if (form.mobile_no) {
    const err = validateMobile(form.mobile_no.replace(/\D/g, ""), form.mobile_code);
    if (err) formErrors.mobile_no = err;
  }
  if (form.phone) {
    const err = validatePhone(form.phone);
    if (err) formErrors.phone = err;
  }
  if (form.website && !URL_REGEX.test(form.website.trim()))
    formErrors.website = "Website must start with http:// or https://";
  if (form.credit_limit < 0) formErrors.credit_limit = "Credit limit cannot be negative";
  if (rule.requireGstin && !form.tax_id.trim())
    formErrors.tax_id = "GSTIN is required for " + form.gst_treatment;
  else if (rule.showGstin && form.tax_id.trim() && !GSTIN_REGEX.test(form.tax_id.trim()))
    formErrors.tax_id = "Invalid GSTIN format (e.g. 27AAPFU0939F1ZV)";
  if (form.pan_no && !PAN_REGEX.test(form.pan_no.trim()))
    formErrors.pan_no = "Invalid PAN format (e.g. ABCDE1234F)";

  if (rule.requirePlaceOfSupply && !form.place_of_supply)
    formErrors.place_of_supply = "Place of Supply is required";
  if (form.opening_balance < 0) formErrors.opening_balance = "Opening balance cannot be negative";

  if (form.pincode) { const err = validatePincode(form.pincode, form.country); if (err) formErrors.pincode = err; }
  if (form.ship_pincode) { const err = validatePincode(form.ship_pincode, form.ship_country); if (err) formErrors.ship_pincode = err; }

  if (form.bank_account_no && !/^\d{9,18}$/.test(form.bank_account_no.replace(/\s/g, "")))
    formErrors.bank_account_no = "Account number must be 9–18 digits";
  if (form.bank_ifsc && !IFSC_REGEX.test(form.bank_ifsc.trim()))
    formErrors.bank_ifsc = "Invalid IFSC code (e.g. HDFC0001234)";

  return Object.keys(formErrors).length === 0;
}

const counts = computed(() => ({
  all:      list.value.length,
  active:   list.value.filter((c) => !c.disabled).length,
  disabled: list.value.filter((c) => c.disabled).length,
}));

const totalOutstanding = computed(() =>
  list.value.reduce((s, c) => s + (c.outstanding || 0), 0)
);

const custKpiCards = computed(() => [
  {
    key: "total", label: "Total Customers", format: "number",
    value: counts.value.all, sub: "all customers",
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    iconBg: "#eff6ff", valueClass: "bk-kpi-blue",
  },
  {
    key: "active", label: "Active", format: "number",
    value: counts.value.active,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>`,
    iconBg: "#f0fdf4", valueClass: "bk-kpi-green", sub: "enabled",
  },
  {
    key: "disabled", label: "Disabled", format: "number",
    value: counts.value.disabled, sub: "inactive",
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><line x1="18" y1="8" x2="23" y2="13"/><line x1="23" y1="8" x2="18" y2="13"/></svg>`,
    iconBg: "#fef2f2", valueClass: "bk-kpi-red",
  },
  {
    key: "outstanding", label: "Total Outstanding", format: "currency",
    value: totalOutstanding.value, sub: "receivable",
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 3h12"/><path d="M6 8h12"/><path d="m6 13 8.5 8"/><path d="M6 13h3"/><path d="M9 13c6.667 0 6.667-10 0-10"/></svg>`,
    iconBg: "#fff7ed", valueClass: "bk-kpi-amber",
  },
]);

const filtered = computed(() => {
  let r = list.value;
  if (activeFilter.value === "active")   r = r.filter((c) => !c.disabled);
  if (activeFilter.value === "disabled") r = r.filter((c) =>  c.disabled);
  const q = search.value.toLowerCase().trim();
  if (q) r = r.filter((c) =>
    (c.customer_name || "").toLowerCase().includes(q) ||
    (c.name          || "").toLowerCase().includes(q) ||
    (c.email_id      || "").toLowerCase().includes(q) ||
    (c.mobile_no     || "").toLowerCase().includes(q) ||
    (c.tax_id        || "").toLowerCase().includes(q)
  );
  return r;
});

async function load() {
  loading.value = true;
  try {
    const [rows, balances, credits] = await Promise.all([
      apiList("Customer", {
        fields: ["name","customer_name","customer_type","email_id","mobile_no",
          "tax_id","city","state","disabled","default_currency","credit_limit","salutation","gst_treatment"],
        order: "customer_name asc", limit: 300,
      }),
      apiGET("zoho_books_clone.api.books_data.get_customer_outstanding").catch(() => ({})),
      apiGET("zoho_books_clone.api.books_data.get_customer_unused_credits").catch(() => ({})),
    ]);
    list.value = (rows || []).map(c => ({ ...c, outstanding: balances[c.name] || 0, unused_credits: credits[c.name] || 0 }));
  } catch (e) {
    toast("Failed to load customers: " + (e.message || e), "error");
  } finally { loading.value = false; }
}

function resetForm() {
  drawerTab.value = "overview";
  shipSameAsBilling.value = false;
  pendingAddresses.value = [];
  Object.keys(formErrors).forEach((k) => delete formErrors[k]);
  Object.assign(form, {
    name: "", customer_name: "", customer_type: "Company", salutation: "",
    first_name: "", last_name: "", company_name: "",
    gst_treatment: "Registered Business",
    tax_id: "", default_currency: "INR", credit_limit: 0,
    email_id: "", mobile_code: "+91", mobile_no: "", phone: "", website: "",
    address_line1: "", address_line2: "", city: "", state: "", pincode: "", country: "India",
    ship_address_line1: "", ship_address_line2: "", ship_city: "", ship_state: "", ship_pincode: "", ship_country: "India",
    payment_terms: "", place_of_supply: "", source: "", pan_no: "", opening_balance: 0,
    bank_name: "", bank_account_no: "", bank_ifsc: "", notes: "", disabled: 0,
  });
}

function openAdd() {
  resetForm();
  drawerMode.value = "add";
  showDrawer.value = true;
}

async function openEdit(name) {
  resetForm();
  drawerMode.value = "edit";
  drawerLoading.value = true;
  showDrawer.value = true;
  try {
    const doc = await apiGET("zoho_books_clone.api.docs.get_doc", { doctype: "Customer", name });
    const mno = doc.mobile_no || "";
    Object.assign(form, {
      name: doc.name,
      customer_name: doc.customer_name || "",
      customer_type: doc.customer_type || "Company",
      salutation: doc.salutation || "",
      first_name: doc.first_name || "",
      last_name: doc.last_name || "",
      company_name: doc.company_name || "",
      gst_treatment: doc.gst_treatment || "Registered Business",
      tax_id: doc.tax_id || "",
      default_currency: doc.default_currency || "INR",
      credit_limit: doc.credit_limit || 0,
      email_id: doc.email_id || "",
      mobile_code: mno.startsWith("+") && mno.includes(" ") ? mno.split(" ")[0] : "+91",
      mobile_no:   mno.startsWith("+") && mno.includes(" ") ? mno.substring(mno.indexOf(" ") + 1) : mno,
      phone: doc.phone || "",
      website: doc.website || "",
      address_line1: doc.address_line1 || "",
      address_line2: doc.address_line2 || "",
      city: doc.city || "",
      state: doc.state || "",
      pincode: doc.pincode || "",
      country: doc.country || "India",
      ship_address_line1: doc.ship_address_line1 || "",
      ship_address_line2: doc.ship_address_line2 || "",
      ship_city: doc.ship_city || "",
      ship_state: doc.ship_state || "",
      ship_pincode: doc.ship_pincode || "",
      ship_country: doc.ship_country || "India",
      payment_terms: doc.payment_terms || "",
      place_of_supply: doc.place_of_supply || "",
      source: doc.source || "",
      pan_no: doc.pan_no || "",
      opening_balance: doc.opening_balance || 0,
      bank_name: doc.bank_name || "",
      bank_account_no: doc.bank_account_no || "",
      bank_ifsc: doc.bank_ifsc || "",
      notes: doc.notes || "",
      disabled: doc.disabled || 0,
    });
  } catch (e) {
    toast("Could not load customer: " + (e.message || e), "error");
    showDrawer.value = false;
  } finally { drawerLoading.value = false; }
}

function onShipSameChange() {
  if (shipSameAsBilling.value) {
    form.ship_address_line1 = form.address_line1;
    form.ship_address_line2 = form.address_line2;
    form.ship_city          = form.city;
    form.ship_state         = form.state;
    form.ship_pincode       = form.pincode;
    form.ship_country       = form.country;
  } else {
    form.ship_address_line1 = "";
    form.ship_address_line2 = "";
    form.ship_city          = "";
    form.ship_state         = "";
    form.ship_pincode       = "";
    form.ship_country       = "India";
  }
}

async function saveCustomer() {
  if (!validateCustomerForm()) {
    const firstErrField = Object.keys(formErrors)[0];
    if (firstErrField && FIELD_TAB[firstErrField]) drawerTab.value = FIELD_TAB[firstErrField];
    toast(Object.values(formErrors)[0], "error");
    return;
  }
  saving.value = true;
  try {
    const booksCompany = await resolveCompany();
    const doc = {
      doctype: "Customer",
      ...(drawerMode.value === "edit" ? { name: form.name } : { naming_series: "CUST-.YYYY.-.#####" }),
      books_company: booksCompany,
      customer_name: form.customer_name.trim(),
      customer_type: form.customer_type,
      salutation: form.salutation,
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      company_name: form.company_name.trim(),
      gst_treatment: form.gst_treatment,
      tax_id: form.tax_id.trim(),
      default_currency: form.default_currency,
      credit_limit: parseFloat(form.credit_limit) || 0,
      email_id: form.email_id.trim(),
      mobile_no: form.mobile_no.trim() ? (form.mobile_code + " " + form.mobile_no.trim()) : "",
      phone: form.phone.trim(),
      website: form.website.trim(),
      payment_terms: form.payment_terms,
      place_of_supply: form.place_of_supply,
      source: form.source,
      pan_no: form.pan_no.trim(),
      opening_balance: parseFloat(form.opening_balance) || 0,
      bank_name: form.bank_name.trim(),
      bank_account_no: form.bank_account_no.trim(),
      bank_ifsc: form.bank_ifsc.trim(),
      notes: form.notes.trim(),
      disabled: form.disabled ? 1 : 0,
    };
    let doc_to_save = doc;
    if (drawerMode.value === "edit") {
      const fresh = await apiGET("zoho_books_clone.api.docs.get_doc", { doctype: "Customer", name: form.name });
      doc_to_save = { ...fresh, ...doc };
    }
    const savedDoc = await apiSave(doc_to_save);
    const savedName = savedDoc?.name || form.name;

    // Flush pending addresses (add mode) → Address doctype
    if (drawerMode.value === "add" && savedName && pendingAddresses.value.length) {
      for (const addr of pendingAddresses.value) {
        try {
          await apiSave({
            doctype: "Address",
            address_title: `${savedName} - ${addr.address_type}`,
            address_type: addr.address_type,
            address_line1: addr.address_line1,
            address_line2: addr.address_line2 || "",
            city: addr.city || "", state: addr.state || "",
            pincode: addr.pincode || "", country: addr.country || "India",
            phone: addr.phone || "",
            links: [{ link_doctype: "Customer", link_name: savedName }],
          });
        } catch {}
      }
      // Sync first billing address fields onto the Customer doctype for the detail view
      const firstBilling = pendingAddresses.value.find(a => a.address_type === "Billing");
      if (firstBilling) {
        try {
          await apiSave({
            doctype: "Customer", name: savedName,
            address_line1: firstBilling.address_line1,
            address_line2: firstBilling.address_line2 || "",
            city: firstBilling.city || "", state: firstBilling.state || "",
            pincode: firstBilling.pincode || "", country: firstBilling.country || "India",
          });
        } catch {}
      }
    }

    toast(drawerMode.value === "edit" ? "Customer updated!" : "Customer created!");
    showDrawer.value = false;
    await load();
  } catch (e) {
    toast(e.message || "Could not save customer", "error");
  } finally { saving.value = false; }
}

function confirmDelete(c) {
  deleteTarget.value = c;
  showDelete.value = true;
}

async function doDelete() {
  if (!deleteTarget.value) return;
  deleting.value = true;
  try {
    await apiDelete("Customer", deleteTarget.value.name);
    toast("Customer deleted");
    showDelete.value = false;
    deleteTarget.value = null;
    await load();
  } catch (e) {
    toast(e.message || "Could not delete customer", "error");
  } finally { deleting.value = false; }
}

// ── Master-detail view ──
const selectedCustomer = ref(null);
const activeCustomerTab = ref("overview");
const custTxns = ref([]);
const custTxnsLoading = ref(false);
const custSectionCollapsed = reactive({ address: false, otherDetails: false });

async function selectCustomer(c) {
  selectedCustomer.value = c;
  activeCustomerTab.value = "overview";
  stmt.value = null;
  Object.assign(custSectionCollapsed, { address: false, otherDetails: false });
  custTxns.value = [];
  custTxnsLoading.value = true;
  try {
    const [txns, fullDoc] = await Promise.all([
      apiGET("zoho_books_clone.api.docs.get_customer_transactions", { customer: c.name, limit: 100 }).catch(() => []),
      apiGET("zoho_books_clone.api.docs.get_doc", { doctype: "Customer", name: c.name }).catch(() => null),
    ]);
    custTxns.value = txns || [];
    if (fullDoc) selectedCustomer.value = { ...c, ...fullDoc, outstanding: c.outstanding || 0, unused_credits: c.unused_credits || 0 };
  } catch (e) { /* keep panel open */ }
  custTxnsLoading.value = false;
}
function closeCustomer()   { selectedCustomer.value = null; }
function custInitials(name) {
  return (name || "?").split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
}

// ── Customer Statement ──
const stmt        = ref(null);
const stmtLoading = ref(false);
const sendingStmt = ref(false);
const fmtStmt = (v) => Number(v||0).toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });

async function loadStatement() {
  if (!selectedCustomer.value) return;
  stmtLoading.value = true;
  try {
    const co = await resolveCompany();
    stmt.value = await apiGET("zoho_books_clone.db.queries.get_customer_statement", {
      customer: selectedCustomer.value.name, company: co,
    });
  } catch (e) { toast("Could not load statement: " + e.message, "error"); }
  stmtLoading.value = false;
}

async function sendStatement() {
  if (!selectedCustomer.value || !stmt.value) return;
  sendingStmt.value = true;
  try {
    const co = await resolveCompany();
    await apiPOST("zoho_books_clone.db.queries.send_customer_statement", {
      customer: selectedCustomer.value.name, company: co,
    });
    toast("Statement sent to " + stmt.value.email);
  } catch (e) { toast(e.message || "Failed to send statement", "error"); }
  sendingStmt.value = false;
}

watch(activeCustomerTab, (t) => { if (t === "statement" && !stmt.value) loadStatement(); });

// ── Bulk actions ────────────────────────────────────────────────────────────
async function bulkSetDisabled(disable) {
  const names = [...selectedRows.value];
  if (!names.length) { toast("No customers selected", "info"); return; }
  bulkBusy.value = true;
  try {
    const { apiPOST } = await import("../api/client.js");
    await apiPOST("zoho_books_clone.api.docs.bulk_set_customer_disabled", {
      customer_names: JSON.stringify(names),
      disabled: disable ? 1 : 0,
    });
    toast(`${disable ? "Disabled" : "Enabled"} ${names.length} customer(s)`, "success");
    clearSelection();
    await load();
  } catch (e) { toast(e.message || "Bulk update failed", "error"); }
  finally { bulkBusy.value = false; }
}

function exportCSV() {
  const rows = selectedRows.value.size
    ? filtered.value.filter(c => selectedRows.value.has(c.name))
    : filtered.value;
  if (!rows.length) { toast("Nothing to export", "info"); return; }
  const headers = ["Customer","Name","Type","GSTIN","Email","Mobile","City","State","Status"];
  const data = rows.map(c => [
    c.name, c.customer_name || "", c.customer_type || "",
    c.tax_id || "", c.email_id || "", c.mobile_no || "",
    c.city || "", c.state || "",
    c.disabled ? "Disabled" : "Active",
  ]);
  const esc = v => { const s = v == null ? "" : String(v); return /[",\n]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; };
  const csv = "﻿" + [headers, ...data].map(r => r.map(esc).join(",")).join("\r\n");
  const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `customers-${new Date().toISOString().slice(0,10)}.csv`;
  a.click();
  URL.revokeObjectURL(url);
  toast(`${rows.length} row(s) exported`, "success");
}

function bulkEmail() {
  const rows = [...selectedRows.value]
    .map(n => list.value.find(c => c.name === n))
    .filter(c => c && c.email_id);
  if (!rows.length) { toast("No selected customers have an email address", "info"); return; }
  const emails = rows.map(c => c.email_id).join(",");
  // Compose a mailto: with all selected recipients
  window.location.href = `mailto:?bcc=${encodeURIComponent(emails)}`;
  toast(`Composing email to ${rows.length} customer(s)`, "info");
}

onMounted(load);
</script>

<style scoped>
/* ── Drawer slide-in animation ──────────────────────────── */
.inv-drawer-panel {
  width: 680px;
  max-width: 98vw;
  transform: translateX(100%);
  transition: transform 0.25s cubic-bezier(0.4, 0, 0.2, 1);
}
.inv-drawer-panel.open {
  transform: translateX(0);
}

/* ── Customer avatar circle ─────────────────────────────── */
.vt-vendor-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.vt-avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  flex-shrink: 0;
  background: linear-gradient(135deg, #16a34a, #15803d);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.03em;
}
.vt-avatar-disabled { background: #d1d5db; }
.vt-vendor-name {
  font-size: 13px;
  font-weight: 600;
  color: #111827;
  line-height: 1.3;
}
.vt-vendor-id {
  font-size: 11.5px;
  color: #9ca3af;
  margin-top: 1px;
}

/* ── Customer-specific column helpers ───────────────────── */
.vt-th {
  padding: 10px 14px;
  text-align: left;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
  white-space: nowrap;
  user-select: none;
}
.vt-th-actions { text-align: center; width: 88px; }
.vt-td {
  padding: 11px 14px;
  vertical-align: middle;
  color: #374151;
  white-space: nowrap;
}
.vt-td-mono      {font-size: 12px; color: #374151; }
.vt-td-secondary { color: #6b7280; font-size: 12.5px; }
.vt-td-actions   { text-align: center; width: 88px; }
.vt-checkbox { width: 15px; height: 15px; accent-color: #16a34a; cursor: pointer; border-radius: 3px; }
.vt-row-shimmer td { padding: 13px 14px; }
.vt-row-disabled   { opacity: 0.55; }
.vt-row-selected   { background: #f0fdf4 !important; }
.vt-actions {
  display: flex;
  gap: 3px;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.12s;
}
.inv-row:hover .vt-actions { opacity: 1; }
.vt-act-edit:hover { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
.vt-act-del:hover  { background: #fef2f2; color: #dc2626; border-color: #fecaca; }
.vt-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 2px 9px;
  border-radius: 20px;
  font-size: 11.5px;
  font-weight: 500;
  white-space: nowrap;
  line-height: 1.6;
}
.vt-badge-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.vt-badge-green             { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.vt-badge-green .vt-badge-dot { background: #22c55e; }
.vt-badge-red               { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.vt-badge-red   .vt-badge-dot { background: #ef4444; }
.vt-badge-blue  { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.vt-badge-gray  { background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; }
.vt-empty { padding: 52px 24px; text-align: center; }
.vt-empty-icon {
  margin: 0 auto 14px; width: 56px; height: 56px; border-radius: 14px;
  background: #f9fafb; border: 1px solid #e5e7eb;
  display: flex; align-items: center; justify-content: center;
}
.vt-empty-title { font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 5px; }
.vt-empty-sub   { font-size: 13px; color: #9ca3af; }
.vt-footer { padding: 9px 16px; border-top: 1px solid #f3f4f6; font-size: 12px; color: #9ca3af; background: #fafafa; }
.vt-footer strong { color: #6b7280; font-weight: 600; }
</style>