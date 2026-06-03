<template>
<div>

  <!-- ── FLAT TABLE VIEW (default, nothing selected) ── -->
  <div v-if="!selectedVendor" class="b-page cust-page">
    <div class="cust-toolbar">
      <div class="cust-toolbar-left">
        <div class="cust-filters">
          <button class="zb-inv-pill" :class="{'zb-inv-pill-active':activeFilter==='all'}" @click="activeFilter='all'">All <span class="zb-pill-cnt" :class="activeFilter==='all'?'':'zb-pc-muted'">{{counts.all}}</span></button>
          <button class="zb-inv-pill" :class="{'zb-inv-pill-active':activeFilter==='active'}" @click="activeFilter='active'">Active <span class="zb-pill-cnt" :class="activeFilter==='active'?'':'zb-pc-muted'">{{counts.active}}</span></button>
          <button class="zb-inv-pill" :class="{'zb-inv-pill-active':activeFilter==='disabled'}" @click="activeFilter='disabled'">Disabled <span class="zb-pill-cnt" :class="activeFilter==='disabled'?'':'zb-pc-muted'">{{counts.disabled}}</span></button>
        </div>
      </div>
      <div class="cust-toolbar-right">
        <div class="cust-search">
          <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
          <input v-model="search" placeholder="Search vendors…" class="cust-search-input" autocomplete="off"/>
        </div>
        <button class="zb-tb-btn" @click="load" title="Refresh"><span v-html="icon('refresh',13)"></span> Refresh</button>
        <button class="zb-tb-btn" @click="exportCSV" title="Export CSV"><span v-html="icon('download',13)"></span> CSV</button>
        <button class="zb-tb-btn zb-tb-primary" @click="openAdd"><span v-html="icon('plus',13)"></span> New Vendor</button>
      </div>
    </div>

    <!-- ── Summary Cards ── -->
    <div class="kpi-grid" style="margin-bottom:18px">
      <div v-for="kpi in vendorKpiCards" :key="kpi.key" class="books-card kpi-card">
        <div class="kpi-icon" :style="{ background: kpi.iconBg }">
          <span v-html="kpi.icon"></span>
        </div>
        <div class="kpi-body">
          <div class="kpi-label">{{ kpi.label }}</div>
          <div class="kpi-value" :class="kpi.valueClass">
            <template v-if="loading">
              <div class="b-shimmer" style="width:64px;height:20px;margin-top:4px;border-radius:4px"></div>
            </template>
            <template v-else>
              {{ kpi.format === 'currency' ? fmtCur(kpi.value) : kpi.value }}
            </template>
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
      <button class="inv-bulk-clear" @click="clearSelection">✕ Clear</button>
    </div>

    <div class="vt-table-card">
      <div class="vt-table-wrap">
        <table class="vt-table">
          <thead>
            <tr>
              <th class="vt-th vt-th-check">
                <input type="checkbox" class="vt-checkbox" :checked="filtered.length>0 && filtered.every(v=>selectedRows.has(v.name))" @change="e=>e.target.checked ? selectedRows=new Set(filtered.map(v=>v.name)) : clearSelection()" />
              </th>
              <th class="vt-th">Vendor Name</th>
              <th class="vt-th">Type</th>
              <!-- <th class="vt-th vt-th-num">Outstanding</th> -->
              <th class="vt-th">GSTIN</th>
              <!-- <th class="vt-th">Email</th> -->
              <th class="vt-th">Mobile</th>
              <th class="vt-th">City / State</th>
              <th class="vt-th">Status</th>
              <th class="vt-th vt-th-actions">Actions</th>
            </tr>
          </thead>
          <tbody>
            <template v-if="loading">
              <tr v-for="n in 6" :key="n" class="vt-row-shimmer">
                <td colspan="10"><div class="b-shimmer" style="height:12px;border-radius:3px;width:65%"></div></td>
              </tr>
            </template>
            <tr v-else-if="!filtered.length">
              <td colspan="10" class="vt-empty">
                <div class="vt-empty-icon">
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.3"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
                </div>
                <div class="vt-empty-title">{{search ? 'No results found' : 'No vendors yet'}}</div>
                <div class="vt-empty-sub">{{search ? 'Try adjusting your search or filter' : 'Add your first vendor to get started'}}</div>
                <button v-if="!search" class="nim-btn nim-btn-primary" style="margin-top:14px" @click="openAdd"><span v-html="icon('plus',13)"></span> New Vendor</button>
              </td>
            </tr>
            <tr v-else v-for="v in filtered" :key="v.name"
              class="vt-row"
              :class="[v.disabled ? 'vt-row-disabled' : '', selectedRows.has(v.name) ? 'vt-row-selected' : '']"
              @click="selectVendor(v)">
              <td class="vt-td vt-td-check" @click.stop>
                <input type="checkbox" class="vt-checkbox" :checked="selectedRows.has(v.name)" @change="toggleRow(v.name)" />
              </td>
              <td class="vt-td vt-td-vendor">
                <div class="vt-vendor-cell">
                  <div class="vt-avatar" :class="v.disabled ? 'vt-avatar-disabled' : ''">{{vendorInitials(v.supplier_name)}}</div>
                  <div>
                    <div class="vt-vendor-name">{{v.supplier_name||v.name}}</div>
                    <div class="vt-vendor-id">{{v.name}}</div>
                  </div>
                </div>
              </td>
              <td class="vt-td">
                <span class="vt-badge" :class="v.supplier_type==='Company' ? 'vt-badge-blue' : 'vt-badge-gray'">{{v.supplier_type||'—'}}</span>
              </td>
              <!-- <td class="vt-td vt-td-num">
                <span :class="balancesByVendor[v.name]>0 ? 'vt-amount-due' : 'vt-amount-nil'">
                  {{ balancesByVendor[v.name]>0 ? fmtCur(balancesByVendor[v.name]) : '—' }}
                </span>
              </td> -->
              <td class="vt-td vt-td-mono">{{v.tax_id||'—'}}</td>
              <!-- <td class="vt-td vt-td-secondary">{{v.email_id||'—'}}</td> -->
              <td class="vt-td vt-td-secondary">{{v.mobile_no||'—'}}</td>
              <td class="vt-td vt-td-secondary">{{v.city ? (v.city + (v.state ? ', '+v.state : '')) : '—'}}</td>
              <td class="vt-td">
                <span class="vt-badge" :class="v.disabled ? 'vt-badge-red' : 'vt-badge-green'">
                  <span class="vt-badge-dot"></span>{{v.disabled ? 'Disabled' : 'Active'}}
                </span>
              </td>
              <td class="vt-td vt-td-actions" @click.stop>
                <div class="vt-actions">
                  <button class="vt-act-btn vt-act-edit" @click="openEdit(v.name)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                  <button class="vt-act-btn vt-act-del" @click="confirmDelete(v)" title="Delete"><span v-html="icon('trash',13)"></span></button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div v-if="!loading && filtered.length" class="vt-footer">
        <span>Showing <strong>{{filtered.length}}</strong> of <strong>{{list.length}}</strong> vendors</span>
      </div>
    </div>
  </div>

  <!-- ── TWO-PANEL DETAIL VIEW (when vendor selected) ── -->
  <div v-else class="zb-master-detail" style="height:calc(100vh - 56px)">

    <!-- LEFT PANEL -->
    <div class="zb-list-pane" style="width:320px;min-width:260px;border-right:1px solid #e4e8f0;display:flex;flex-direction:column;overflow:hidden">

      <div style="padding:16px 16px 10px;border-bottom:1px solid #f0f2f5;flex-shrink:0">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px">
          <span style="font-size:14px;font-weight:700;color:#111827">Vendors</span>
          <button class="nim-btn nim-btn-primary" style="padding:5px 10px;font-size:12px" @click="openAdd">
            <span v-html="icon('plus',12)"></span> New Vendor
          </button>
        </div>
        <div class="cust-search" style="width:100%">
          <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
          <input v-model="search" placeholder="Search vendors…" class="cust-search-input" autocomplete="off"/>
        </div>
        <div style="display:flex;gap:4px;margin-top:8px;flex-wrap:wrap">
          <button class="zb-inv-pill" :class="{'zb-inv-pill-active':activeFilter==='all'}" @click="activeFilter='all'" style="font-size:11.5px">All <span class="zb-pill-cnt" :class="activeFilter==='all'?'':'zb-pc-muted'">{{counts.all}}</span></button>
          <button class="zb-inv-pill" :class="{'zb-inv-pill-active':activeFilter==='active'}" @click="activeFilter='active'" style="font-size:11.5px">Active <span class="zb-pill-cnt" :class="activeFilter==='active'?'':'zb-pc-muted'">{{counts.active}}</span></button>
          <button class="zb-inv-pill" :class="{'zb-inv-pill-active':activeFilter==='disabled'}" @click="activeFilter='disabled'" style="font-size:11.5px">Disabled <span class="zb-pill-cnt" :class="activeFilter==='disabled'?'':'zb-pc-muted'">{{counts.disabled}}</span></button>
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
          <svg width="34" height="34" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.5" style="margin:0 auto 10px;display:block"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
          <div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:4px">{{search?'No matches':'No vendors yet'}}</div>
          <div style="font-size:12px;color:#9ca3af">{{search?'Try different keywords':'Add your first vendor'}}</div>
          <button v-if="!search" class="nim-btn nim-btn-primary" style="margin-top:12px;font-size:12px" @click="openAdd">New Vendor</button>
        </div>
        <div v-else v-for="v in filtered" :key="v.name"
          @click="selectVendor(v)"
          :style="{
            padding:'12px 16px',
            borderBottom:'1px solid #f0f2f5',
            cursor:'pointer',
            background: selectedVendor && selectedVendor.name===v.name ? '#FFF7ED' : 'transparent',
            borderLeft: selectedVendor && selectedVendor.name===v.name ? '3px solid #E67700' : '3px solid transparent',
            transition:'background 0.15s',
          }">
          <div style="display:flex;align-items:center;gap:10px">
            <div :style="{
              width:'34px',height:'34px',borderRadius:'50%',flexShrink:0,
              display:'flex',alignItems:'center',justifyContent:'center',
              fontWeight:700,fontSize:'12px',color:'#fff',
              background: v.disabled ? '#9CA3AF' : 'linear-gradient(135deg,#E67700,#C96200)'
            }">{{vendorInitials(v.supplier_name)}}</div>
            <div style="flex:1;min-width:0">
              <div style="font-size:13px;font-weight:700;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">
                {{v.supplier_name||v.name}}
              </div>
              <div style="font-size:11.5px;color:#6B7280;margin-top:2px">
                <span :style="balancesByVendor[v.name]>0?'color:#E67700;font-weight:600':''">{{ fmtCur(balancesByVendor[v.name] || 0) }}</span> outstanding
                <span v-if="v.disabled" style="margin-left:6px;font-size:10px;font-weight:600;color:#6B7280;background:#F3F4F6;padding:1px 5px;border-radius:10px">Disabled</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="!loading && filtered.length" style="padding:8px 16px;border-top:1px solid #f0f2f5;font-size:11.5px;color:#9ca3af;display:flex;justify-content:space-between;flex-shrink:0">
        <span>{{filtered.length}} of {{list.length}} vendors</span>
        <button @click="load" style="background:none;border:none;cursor:pointer;color:#6B7280;font-size:11.5px;display:flex;align-items:center;gap:3px"><span v-html="icon('refresh',11)"></span> Refresh</button>
      </div>
    </div>

    <!-- RIGHT PANEL -->
    <div style="flex:1;overflow-y:auto;background:#F9FAFB">

      <div style="max-width:960px;margin:0 auto;padding:24px">

        <!-- Header -->
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
          <div style="display:flex;align-items:center;gap:12px">
            <div :style="{
              width:'46px',height:'46px',borderRadius:'50%',flexShrink:0,
              display:'flex',alignItems:'center',justifyContent:'center',
              fontWeight:700,fontSize:'16px',color:'#fff',
              background: selectedVendor.disabled ? '#9CA3AF' : 'linear-gradient(135deg,#E67700,#C96200)'
            }">{{vendorInitials(selectedVendor.supplier_name)}}</div>
            <div>
              <div style="font-size:19px;font-weight:700;color:#111827">{{selectedVendor.supplier_name}}</div>
              <div style="font-size:12px;color:#6B7280">{{selectedVendor.name}}</div>
            </div>
          </div>
          <div style="display:flex;align-items:center;gap:8px">
            <button class="nim-btn" style="background:#fff;color:#374151;border:1px solid #E5E7EB;font-size:13px" @click="openEdit(selectedVendor.name)">
              <span v-html="icon('edit',13)"></span> Edit
            </button>
            <!-- <button class="nim-btn nim-btn-primary" style="font-size:13px;background:#E67700;border-color:#E67700" @click="openAdd">
              <span v-html="icon('plus',13)"></span> New Transaction
            </button> -->
            <button class="nim-btn" style="background:none;color:#9CA3AF;border:1px solid #E5E7EB;width:32px;height:32px;padding:0;display:grid;place-items:center" @click="closeVendor" title="Close">
              <span v-html="icon('x',14)"></span>
            </button>
          </div>
        </div>

        <!-- Tabs -->
        <div style="display:flex;border-bottom:2px solid #E5E7EB;margin-bottom:22px;gap:0">
          <button @click="activeVendorTab='overview'"
            :style="{padding:'8px 16px',fontSize:'13.5px',fontWeight:600,border:'none',background:'none',cursor:'pointer',
              color:activeVendorTab==='overview'?'#E67700':'#6B7280',
              borderBottom:activeVendorTab==='overview'?'2px solid #E67700':'2px solid transparent',marginBottom:'-2px'}">
            Overview
          </button>
          <button @click="activeVendorTab='transactions'"
            :style="{padding:'8px 16px',fontSize:'13.5px',fontWeight:600,border:'none',background:'none',cursor:'pointer',
              color:activeVendorTab==='transactions'?'#E67700':'#6B7280',
              borderBottom:activeVendorTab==='transactions'?'2px solid #E67700':'2px solid transparent',marginBottom:'-2px'}">
            Transactions
            <span v-if="vendorTxns.length" style="background:#E67700;color:#fff;padding:1px 7px;border-radius:999px;font-size:11px;margin-left:4px">{{vendorTxns.length}}</span>
          </button>
          <button @click="activeVendorTab='statement'; loadStatement()"
            :style="{padding:'8px 16px',fontSize:'13.5px',fontWeight:600,border:'none',background:'none',cursor:'pointer',
              color:activeVendorTab==='statement'?'#E67700':'#6B7280',
              borderBottom:activeVendorTab==='statement'?'2px solid #E67700':'2px solid transparent',marginBottom:'-2px'}">
            Statement
          </button>
        </div>

        <!-- Overview tab -->
        <div v-if="activeVendorTab==='overview'" style="display:flex;gap:20px;align-items:flex-start">

          <!-- Left column ~55% -->
          <div style="flex:0 0 55%;min-width:0;display:flex;flex-direction:column;gap:14px">

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:18px">
              <div style="display:flex;align-items:center;gap:12px;margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #F3F4F6">
                <div :style="{
                  width:'44px',height:'44px',borderRadius:'50%',flexShrink:0,
                  display:'flex',alignItems:'center',justifyContent:'center',
                  fontWeight:700,fontSize:'16px',color:'#fff',
                  background: selectedVendor.disabled ? '#9CA3AF' : 'linear-gradient(135deg,#E67700,#C96200)'
                }">{{vendorInitials(selectedVendor.supplier_name)}}</div>
                <div>
                  <div style="font-size:14px;font-weight:700;color:#111827">{{selectedVendor.supplier_name}}</div>
                  <div v-if="selectedVendor.email_id" style="font-size:12px;color:#6B7280;margin-top:2px">{{selectedVendor.email_id}}</div>
                </div>
                <div style="margin-left:auto">
                  <a href="#" style="font-size:12px;color:#E67700;text-decoration:none">Invite to Portal</a>
                </div>
              </div>
              <div style="display:flex;flex-direction:column;gap:7px">
                <div v-if="selectedVendor.mobile_no" style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:#374151">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.63 3.18 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.6A16 16 0 0 0 15.4 16.1l.97-.97a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  <span>{{selectedVendor.mobile_no}}</span>
                </div>
                <div v-else style="display:flex;align-items:center;gap:8px;font-size:12.5px;color:#9CA3AF">
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.63 3.18 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.6A16 16 0 0 0 15.4 16.1l.97-.97a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                  <span>No phone number</span>
                </div>
              </div>
            </div>

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
              <div style="padding:12px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #F3F4F6">
                <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">ADDRESS</span>
                <span style="font-size:12px;color:#9CA3AF">▲</span>
              </div>
              <div style="padding:14px 16px;display:flex;flex-direction:column;gap:14px">
                <div>
                  <div style="font-size:11.5px;font-weight:600;color:#6B7280;margin-bottom:6px">Billing Address</div>
                  <div v-if="selectedVendor.city||selectedVendor.address_line1" style="font-size:13px;color:#374151;line-height:1.6">
                    <div v-if="selectedVendor.address_line1">{{selectedVendor.address_line1}}</div>
                    <div v-if="selectedVendor.address_line2">{{selectedVendor.address_line2}}</div>
                    <div>{{[selectedVendor.city,selectedVendor.state,selectedVendor.pincode].filter(Boolean).join(', ')}}</div>
                    <div>{{selectedVendor.country||'India'}}</div>
                  </div>
                  <div v-else style="font-size:12.5px;color:#9CA3AF">
                    No Billing Address — <a href="#" @click.prevent="openEdit(selectedVendor.name)" style="color:#E67700;text-decoration:none">New Address</a>
                  </div>
                </div>
                <div>
                  <div style="font-size:11.5px;font-weight:600;color:#6B7280;margin-bottom:6px">Shipping Address</div>
                  <div style="font-size:12.5px;color:#9CA3AF">No Shipping Address — <a href="#" @click.prevent="openEdit(selectedVendor.name)" style="color:#E67700;text-decoration:none">New Address</a></div>
                </div>
              </div>
            </div>

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
              <div style="padding:12px 16px;display:flex;justify-content:space-between;align-items:center;border-bottom:1px solid #F3F4F6">
                <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">OTHER DETAILS</span>
                <span style="font-size:12px;color:#9CA3AF">▲</span>
              </div>
              <div style="padding:14px 16px;display:flex;flex-direction:column;gap:10px">
                <div style="display:flex;justify-content:space-between;font-size:12.5px">
                  <span style="color:#6B7280">Default Currency</span>
                  <span style="font-weight:600;color:#111827">{{selectedVendor.default_currency||'INR'}}</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12.5px;align-items:center">
                  <span style="color:#6B7280">Portal Status</span>
                  <span style="font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px;background:#F3F4F6;color:#6B7280">● Disabled</span>
                </div>
                <div style="display:flex;justify-content:space-between;font-size:12.5px">
                  <span style="color:#6B7280">Vendor Type</span>
                  <span style="font-weight:600;color:#111827">{{selectedVendor.supplier_type||'Company'}}</span>
                </div>
                <div v-if="selectedVendor.tax_id" style="display:flex;justify-content:space-between;font-size:12.5px">
                  <span style="color:#6B7280">GSTIN / Tax ID</span>
                  <span style="font-weight:600;color:#111827;font-family:monospace">{{selectedVendor.tax_id}}</span>
                </div>
              </div>
            </div>

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
              <div style="padding:12px 16px;display:flex;justify-content:space-between;align-items:center">
                <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">CONTACT PERSONS</span>
                <button @click="openEdit(selectedVendor.name)" style="background:none;border:none;cursor:pointer;color:#E67700;font-size:12px">+ Add</button>
              </div>
              <div style="padding:10px 16px 14px;font-size:12.5px;color:#9CA3AF">No contacts added yet.</div>
            </div>
          </div>

          <!-- Right column ~45% -->
          <div style="flex:1;min-width:0;display:flex;flex-direction:column;gap:14px">

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:16px">
              <div style="font-size:11.5px;color:#6B7280;margin-bottom:4px">Payment due period</div>
              <div style="font-size:14px;font-weight:600;color:#111827">{{selectedVendor.payment_terms||'Due on Receipt'}}</div>
            </div>

            <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
              <div style="padding:12px 16px;border-bottom:1px solid #F3F4F6">
                <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">PAYABLES</span>
              </div>
              <table style="width:100%;border-collapse:collapse">
                <thead>
                  <tr style="border-bottom:1px solid #F3F4F6">
                    <th style="text-align:left;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:8px 16px">CURRENCY</th>
                    <th style="text-align:right;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:8px 12px">OUTSTANDING PAYABLES</th>
                    <th style="text-align:right;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:8px 16px">UNUSED CREDITS</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td style="font-size:13px;font-weight:600;color:#374151;padding:10px 16px">{{ selectedVendor.default_currency || "INR" }}</td>
                    <td style="font-size:13px;font-weight:600;color:#E67700;text-align:right;padding:10px 12px;font-family:monospace">{{ fmtCur(vendorSummary.outstanding || 0) }}</td>
                    <td style="font-size:13px;font-weight:600;color:#059669;text-align:right;padding:10px 16px;font-family:monospace">{{ fmtCur(vendorSummary.dn_credit || 0) }}</td>
                  </tr>
                </tbody>
              </table>
              <div style="padding:10px 16px">
                <a href="#" style="font-size:12.5px;color:#2563EB;text-decoration:none">Enter Opening Balance</a>
              </div>
            </div>

            <div style="padding:4px 0">
              <button @click="confirmDelete(selectedVendor)" style="background:none;border:none;cursor:pointer;color:#DC2626;font-size:12.5px;display:flex;align-items:center;gap:6px">
                <span v-html="icon('trash',13)"></span> Delete Vendor
              </button>
            </div>
          </div>
        </div>

        <!-- Transactions tab -->
        <div v-else-if="activeVendorTab==='transactions'">
          <div v-if="detailLoading" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:24px;text-align:center;color:#9CA3AF">Loading transactions…</div>
          <div v-else-if="!vendorTxns.length" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:24px;text-align:center;color:#9CA3AF">
            <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#D1D5DB" stroke-width="1.5" style="margin:0 auto 12px;display:block"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/></svg>
            <div style="font-size:14px;font-weight:600;color:#374151;margin-bottom:6px">No transactions yet</div>
            <div style="font-size:12.5px;color:#9CA3AF">Bills and payments for {{selectedVendor.supplier_name}} will appear here.</div>
          </div>
          <div v-else style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
            <div style="display:grid;grid-template-columns:90px 1fr 120px 130px 130px 100px;gap:8px;background:#F9FAFB;padding:10px 14px;font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;border-bottom:1px solid #E5E7EB">
              <span>Type</span><span>Reference</span><span>Date</span><span style="text-align:right">Amount</span><span style="text-align:right">Outstanding</span><span>Status</span>
            </div>
            <div v-for="t in vendorTxns" :key="t.type+'-'+t.name"
              style="display:grid;grid-template-columns:90px 1fr 120px 130px 130px 100px;gap:8px;padding:9px 14px;border-bottom:1px solid #F3F4F6;font-size:12.5px;align-items:center">
              <span :style="{
                fontSize:'10.5px',fontWeight:700,padding:'2px 8px',borderRadius:'10px',display:'inline-block',width:'fit-content',
                background: t.type==='Bill' ? '#FEF3C7' : t.type==='Payment' ? '#D1FAE5' : '#FEE2E2',
                color: t.type==='Bill' ? '#92400E' : t.type==='Payment' ? '#059669' : '#991B1B'
              }">{{t.type}}</span>
              <span style="font-family:monospace;color:#2563EB;font-weight:600">{{t.name}}</span>
              <span style="font-family:monospace;color:#6B7280">{{fmtDate(t.date)}}</span>
              <span style="text-align:right;font-family:monospace;font-weight:600" :style="{color: t.amount<0 ? '#059669' : '#374151'}">{{fmtCur(Math.abs(t.amount))}}</span>
              <span style="text-align:right;font-family:monospace" :style="{color: t.outstanding>0 ? '#E67700' : '#9CA3AF'}">{{t.outstanding>0?fmtCur(t.outstanding):'—'}}</span>
              <span style="font-size:11.5px;color:#6B7280">{{t.status||(t.docstatus===2?'Cancelled':'Submitted')}}</span>
            </div>
          </div>
        </div>

        <!-- Statement tab -->
        <div v-else-if="activeVendorTab==='statement'">
          <div style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:14px 18px;display:flex;align-items:center;gap:12px;margin-bottom:14px;flex-wrap:wrap">
            <span style="font-size:12px;font-weight:600;color:#6B7280">FROM</span>
            <input v-model="stmtRange.from" type="date" class="nim-input" style="width:160px"/>
            <span style="font-size:12px;font-weight:600;color:#6B7280">TO</span>
            <input v-model="stmtRange.to" type="date" class="nim-input" style="width:160px"/>
            <button class="nim-btn" style="border:1px solid #E5E7EB" @click="loadStatement">Refresh</button>
            <div style="margin-left:auto;display:flex;gap:8px">
              <button class="nim-btn" style="border:1px solid #E5E7EB" @click="emailVendorStatement">📧 Email Statement</button>
            </div>
          </div>
          <div v-if="detailLoading" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:24px;text-align:center;color:#9CA3AF">Loading statement…</div>
          <div v-else style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
            <div style="display:grid;grid-template-columns:110px 1fr 100px 110px 110px 130px;gap:8px;background:#F9FAFB;padding:10px 14px;font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;border-bottom:1px solid #E5E7EB">
              <span>Date</span><span>Reference</span><span>Type</span><span style="text-align:right">Debit</span><span style="text-align:right">Credit</span><span style="text-align:right">Balance</span>
            </div>
            <div v-if="!vendorStatement.rows?.length" style="padding:24px;text-align:center;color:#9CA3AF;font-size:13px">No statement rows for this period.</div>
            <div v-for="(r,i) in (vendorStatement.rows || [])" :key="r.ref+'-'+i"
              style="display:grid;grid-template-columns:110px 1fr 100px 110px 110px 130px;gap:8px;padding:8px 14px;border-bottom:1px solid #F3F4F6;font-size:12.5px;font-family:monospace;align-items:center">
              <span style="color:#6B7280">{{fmtDate(r.date)}}</span>
              <span style="color:#2563EB;font-weight:600">{{r.ref}}</span>
              <span style="font-size:11px;color:#6B7280">{{r.type}}</span>
              <span style="text-align:right;color:#059669">{{r.debit>0?fmtCur(r.debit):'—'}}</span>
              <span style="text-align:right;color:#E67700">{{r.credit>0?fmtCur(r.credit):'—'}}</span>
              <span style="text-align:right;font-weight:700;color:#111827">{{fmtCur(r.balance)}}</span>
            </div>
            <div v-if="vendorStatement.rows?.length" style="background:#F9FAFB;padding:12px 14px;border-top:2px solid #E5E7EB;display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:14px;font-size:12.5px">
              <div><span style="color:#6B7280">Billed:</span> <strong style="font-family:monospace;color:#E67700">{{fmtCur(vendorStatement.totals?.billed || 0)}}</strong></div>
              <div><span style="color:#6B7280">Paid:</span> <strong style="font-family:monospace;color:#059669">{{fmtCur(vendorStatement.totals?.paid || 0)}}</strong></div>
              <div><span style="color:#6B7280">Debit Notes:</span> <strong style="font-family:monospace;color:#059669">{{fmtCur(vendorStatement.totals?.debit_notes || 0)}}</strong></div>
              <div style="text-align:right"><span style="color:#6B7280">Closing Balance:</span> <strong style="font-family:monospace;color:#111827">{{fmtCur(vendorStatement.totals?.closing_balance || 0)}}</strong></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>

  <!-- Drawer -->
  <Teleport to="body">
    <div v-if="showDrawer" class="cust-backdrop" @click.self="showDrawer=false">
      <div class="cust-drawer" style="width:min(600px,96vw)">

        <div class="cust-drawer-header" style="background:linear-gradient(135deg,#E67700,#C96200);padding:18px 24px">
          <div class="cust-drawer-header-left">
            <div class="cust-drawer-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>
            </div>
            <div>
              <div class="cust-drawer-title">{{drawerMode==='add'?'New Vendor':'Edit Vendor'}}</div>
              <div class="cust-drawer-sub">{{drawerMode==='edit'?form.name:'Fill in vendor details'}}</div>
            </div>
          </div>
          <button class="nim-close" @click="showDrawer=false" v-html="icon('x',15)"></button>
        </div>

        <div v-if="drawerLoading" style="flex:1;display:grid;place-items:center;color:#9ca3af;font-size:13px">
          <div>Loading vendor…</div>
        </div>

        <div v-else class="cust-drawer-body" style="padding:24px;overflow-y:auto;flex:1">

          <div class="cust-sec-label">Basic Information</div>
          <div class="nim-grid-2 nim-mb">
            <div class="nim-field" style="grid-column:span 2">
              <label class="nim-label">Vendor Name <span class="nim-req">*</span></label>
              <input v-model="form.supplier_name" class="nim-input"
                :style="formErrors.supplier_name?'border-color:#dc2626;background:#fff5f5':''"
                placeholder="Company or individual name"
                @input="form.supplier_name=form.supplier_name.replace(/[^a-zA-Z\s.'&-]/g,''); delete formErrors.supplier_name"
                @blur="validateField('supplier_name')"/>
              <div v-if="formErrors.supplier_name" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.supplier_name}}
              </div>
            </div>
            <div class="nim-field">
              <label class="nim-label">Vendor Type</label>
              <select v-model="form.supplier_type" class="nim-select">
                <option>Company</option><option>Individual</option>
              </select>
            </div>
            <div class="nim-field">
              <label class="nim-label">GSTIN / Tax ID</label>
              <input v-model="form.tax_id" class="nim-input"
                :style="formErrors.tax_id?'border-color:#dc2626;background:#fff5f5':form.tax_id&&!formErrors.tax_id&&form.country==='India'&&GSTIN_REGEX.test(form.tax_id)?'border-color:#2f9e44':''"
                placeholder="27AAPFU0939F1ZV"
                @input="form.tax_id=form.tax_id.toUpperCase(); delete formErrors.tax_id"
                @blur="validateField('tax_id')"/>
              <div v-if="formErrors.tax_id" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.tax_id}}
              </div>
              <div v-else-if="form.tax_id&&form.country==='India'&&GSTIN_REGEX.test(form.tax_id)" style="margin-top:4px;font-size:12px;color:#2f9e44;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>
                Valid GSTIN
              </div>
            </div>
            <div class="nim-field">
              <label class="nim-label">Currency</label>
              <select v-model="form.default_currency" class="nim-select">
                <option>INR</option><option>USD</option><option>EUR</option><option>GBP</option><option>AED</option><option>SGD</option>
              </select>
            </div>
            <div class="nim-field">
              <label class="nim-label">Payment Terms</label>
              <select v-model="form.payment_terms" class="nim-select">
                <option value="">Select</option>
                <option>Net 30</option><option>Net 15</option><option>Net 7</option>
                <option>Due on Receipt</option><option>End of Month</option>
              </select>
            </div>
          </div>

          <div class="cust-sec-label">Contact</div>
          <div class="nim-grid-2 nim-mb">
            <div class="nim-field">
              <label class="nim-label">Email</label>
              <input v-model="form.email_id" type="email" class="nim-input"
                :style="formErrors.email_id?'border-color:#dc2626;background:#fff5f5':form.email_id&&EMAIL_REGEX.test(form.email_id)?'border-color:#2f9e44':''"
                placeholder="email@vendor.com"
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
            <div class="nim-field">
              <label class="nim-label">Mobile</label>
              <div style="display:flex">
                <select v-model="form.mobile_code" style="width:85px;border-right:none;border-top-right-radius:0;border-bottom-right-radius:0;text-align:center;background:#f9fafb;padding:0 5px" class="nim-input"
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
                <input v-model="form.mobile_no" class="nim-input"
                  style="border-top-left-radius:0;border-bottom-left-radius:0;flex:1"
                  :style="formErrors.mobile_no?'border-color:#dc2626;background:#fff5f5':form.mobile_no&&!formErrors.mobile_no?'border-color:#2f9e44':''"
                  placeholder="Mobile number"
                  @input="form.mobile_no=form.mobile_no.replace(/\D/g,''); delete formErrors.mobile_no"
                  @blur="validateField('mobile_no')"/>
              </div>
              <div v-if="formErrors.mobile_no" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.mobile_no}}
              </div>
            </div>
            <div class="nim-field">
              <label class="nim-label">Phone</label>
              <input v-model="form.phone" class="nim-input" placeholder="Landline"
                :style="formErrors.phone?'border-color:#dc2626;background:#fff5f5':''"
                @input="form.phone=form.phone.replace(/[^\d+\-\s()]/g,''); delete formErrors.phone"
                @blur="validateField('phone')"/>
              <div v-if="formErrors.phone" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.phone}}
              </div>
            </div>
            <div class="nim-field">
              <label class="nim-label">Website</label>
              <input v-model="form.website" class="nim-input" placeholder="https://"
                :style="formErrors.website?'border-color:#dc2626;background:#fff5f5':form.website&&URL_REGEX.test(form.website)?'border-color:#2f9e44':''"
                @input="delete formErrors.website"
                @blur="validateField('website')"/>
              <div v-if="formErrors.website" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.website}}
              </div>
            </div>
          </div>

          <div class="cust-sec-label">Address</div>
          <div class="nim-grid-2 nim-mb">
            <div class="nim-field" style="grid-column:span 2">
              <label class="nim-label">Address Line 1</label>
              <input v-model="form.address_line1" class="nim-input" placeholder="Street, building no."/>
            </div>
            <div class="nim-field" style="grid-column:span 2">
              <label class="nim-label">Address Line 2</label>
              <input v-model="form.address_line2" class="nim-input" placeholder="Area, landmark"/>
            </div>
            <div class="nim-field">
              <label class="nim-label">City</label>
              <input v-model="form.city" class="nim-input" placeholder="Mumbai"
                @input="form.city=form.city.replace(/[^a-zA-Z\s]/g,'')"/>
            </div>
            <div class="nim-field">
              <label class="nim-label">Country</label>
              <select v-model="form.country" class="nim-select" @change="form.state=''; delete formErrors.pincode; if(form.pincode) validateField('pincode')">
                <option value="">— Select Country —</option>
                <option v-for="c in COUNTRIES" :key="c">{{c}}</option>
              </select>
            </div>
            <div class="nim-field">
              <label class="nim-label">State / Province</label>
              <select v-if="statesFor(form.country).length" v-model="form.state" class="nim-select">
                <option value="">— Select State —</option>
                <option v-for="s in statesFor(form.country)" :key="s" :value="s">{{s}}</option>
              </select>
              <input v-else v-model="form.state" class="nim-input" placeholder="Enter state / province"/>
            </div>
            <div class="nim-field">
              <label class="nim-label">Pincode / ZIP</label>
              <input v-model="form.pincode" class="nim-input"
                :placeholder="pincodePlaceholder(form.country)"
                :style="formErrors.pincode?'border-color:#dc2626;background:#fff5f5':form.pincode&&!formErrors.pincode?'border-color:#2f9e44':''"
                @input="form.pincode=sanitizePincode(form.pincode, form.country); delete formErrors.pincode"
                @blur="validateField('pincode')"/>
              <div v-if="formErrors.pincode" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.pincode}}
              </div>
              <div v-else-if="form.pincode&&!formErrors.pincode" style="margin-top:4px;font-size:11px;color:#9ca3af">{{pincodeHint(form.country)}}</div>
            </div>
          </div>

          <!-- Shipping Address -->
          <template v-if="drawerMode==='edit' && form.name">
            <div class="cust-sec-label" style="margin-top:4px">Shipping Addresses</div>
            <AddressManager
              :partyDoctype="'Supplier'"
              :partyName="form.name"
              @addressSaved="load"
              @addressDeleted="load"
            />
          </template>
          <template v-else>
            <div class="cust-sec-label" style="margin-top:4px">Shipping Address
              <span style="font-size:11px;font-weight:400;color:#9ca3af;margin-left:6px">— leave blank to use billing</span>
            </div>
            <div style="margin-bottom:10px">
              <label style="display:flex;align-items:center;gap:8px;font-size:13px;cursor:pointer">
                <input type="checkbox" v-model="shipSameAsBilling" @change="onShipSameChange" style="accent-color:#3B5BDB"/>
                Use same address as billing
              </label>
            </div>
            <div v-if="!shipSameAsBilling" class="nim-grid-2 nim-mb">
              <div class="nim-field" style="grid-column:span 2">
                <label class="nim-label">Address Line 1</label>
                <input v-model="form.ship_address_line1" class="nim-input" placeholder="Street, building no."/>
              </div>
              <div class="nim-field" style="grid-column:span 2">
                <label class="nim-label">Address Line 2</label>
                <input v-model="form.ship_address_line2" class="nim-input" placeholder="Area, landmark"/>
              </div>
              <div class="nim-field">
                <label class="nim-label">City</label>
                <input v-model="form.ship_city" class="nim-input" placeholder="City"/>
              </div>
              <div class="nim-field">
                <label class="nim-label">Country</label>
                <select v-model="form.ship_country" class="nim-select">
                  <option value="">— Select Country —</option>
                  <option v-for="c in COUNTRIES" :key="c">{{c}}</option>
                </select>
              </div>
              <div class="nim-field">
                <label class="nim-label">State</label>
                <select v-if="statesFor(form.ship_country).length" v-model="form.ship_state" class="nim-select">
                  <option value="">— Select State —</option>
                  <option v-for="s in statesFor(form.ship_country)" :key="s" :value="s">{{s}}</option>
                </select>
                <input v-else v-model="form.ship_state" class="nim-input" placeholder="State"/>
              </div>
              <div class="nim-field">
                <label class="nim-label">Pincode</label>
                <input v-model="form.ship_pincode" class="nim-input" placeholder="Pincode"/>
              </div>
            </div>
          </template>

          <div class="cust-sec-label">Account Settings</div>
          <div class="nim-grid-1 nim-mb">
            <div class="nim-field">
              <label class="nim-label">Default Payable Account</label>
              <select v-model="form.default_payable_account" class="nim-select">
                <option value="">Select</option>
                <option v-for="a in accounts" :key="a.name" :value="a.name">{{a.name}}</option>
              </select>
            </div>
          </div>

          <div v-if="drawerMode==='edit'" class="cust-disable-box" @click="form.disabled=form.disabled?0:1">
            <input type="checkbox" :checked="!!form.disabled" @click.stop="form.disabled=form.disabled?0:1" style="width:16px;height:16px;accent-color:#dc2626;cursor:pointer"/>
            <label style="font-size:13px;color:#dc2626;cursor:pointer">Disable this vendor (won't appear in bill dropdowns)</label>
          </div>

        </div>

        <div class="nim-footer">
          <button class="nim-btn nim-btn-ghost" @click="showDrawer=false">Cancel</button>
          <button class="nim-btn nim-btn-primary" @click="saveVendor" :disabled="saving">
            <span v-if="saving" v-html="icon('refresh',13)" style="animation:spin 1s linear infinite"></span>
            {{saving ? 'Saving…' : (drawerMode==='add' ? 'Create Vendor' : 'Save Changes')}}
          </button>
        </div>

      </div>
    </div>
  </Teleport>

  <!-- Delete Confirm -->
  <Teleport to="body">
    <div v-if="showDelete" class="nim-overlay" @click.self="showDelete=false">
      <div class="nim-dialog" style="max-width:420px">
        <div class="nim-header" style="background:linear-gradient(135deg,#dc2626,#b91c1c)">
          <div class="nim-header-left">
            <div class="nim-header-icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14H6L5 6"/><path d="M10 11v6M14 11v6"/><path d="M9 6V4h6v2"/></svg>
            </div>
            <div class="nim-header-title">Delete Vendor?</div>
          </div>
          <button class="nim-close" @click="showDelete=false" v-html="icon('x',15)"></button>
        </div>
        <div class="nim-body" style="padding:20px 24px">
          <p style="font-size:14px;color:#374151;line-height:1.6">
            Are you sure you want to delete <strong>{{deleteTarget?.supplier_name}}</strong>?
            This action cannot be undone.
          </p>
        </div>
        <div class="nim-footer">
          <button class="nim-btn nim-btn-ghost" @click="showDelete=false">Cancel</button>
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
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiGET, apiSave, apiDelete } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import AddressManager from "../components/AddressManager.vue";
import { fmt, fmtDate } from "../utils/format.js";
import { icon } from "../utils/icons.js";
import { COUNTRIES, statesFor } from "../composables/useCountryState.js";
import {
  EMAIL_REGEX, GSTIN_REGEX, URL_REGEX,
  validateMobile, validatePhone, validatePincode, sanitizePincode, pincodePlaceholder, pincodeHint,
} from "../composables/useValidation.js";


const { toast } = useToast();

const list          = ref([]);
const loading       = ref(true);
const search        = ref("");
const activeFilter  = ref("all");
const showDrawer    = ref(false);
const drawerMode    = ref("add");
const drawerLoading = ref(false);
const saving        = ref(false);
const showDelete    = ref(false);
const deleteTarget  = ref(null);
const deleting      = ref(false);
const accounts      = ref([]);

const form = reactive({
  name: "",
  supplier_name: "", supplier_type: "Company",
  tax_id: "", default_currency: "INR", payment_terms: "",
  email_id: "", mobile_code: "+91", mobile_no: "", phone: "", website: "",
  address_line1: "", address_line2: "",
  city: "", state: "", pincode: "", country: "India",
  ship_address_line1: "", ship_address_line2: "",
  ship_city: "", ship_state: "", ship_pincode: "", ship_country: "India",
  default_payable_account: "", disabled: 0,
});

const formErrors = reactive({});
const shipSameAsBilling = ref(false);

const counts = computed(() => ({
  all:      list.value.length,
  active:   list.value.filter((v) => !v.disabled).length,
  disabled: list.value.filter((v) =>  v.disabled).length,
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeFilter.value === "active")   r = r.filter((v) => !v.disabled);
  if (activeFilter.value === "disabled") r = r.filter((v) =>  v.disabled);
  const q = search.value.toLowerCase().trim();
  if (q) r = r.filter((v) =>
    (v.supplier_name || "").toLowerCase().includes(q) ||
    (v.name          || "").toLowerCase().includes(q) ||
    (v.email_id      || "").toLowerCase().includes(q) ||
    (v.mobile_no     || "").toLowerCase().includes(q) ||
    (v.tax_id        || "").toLowerCase().includes(q)
  );
  return r;
});

async function load() {
  loading.value = true;
  try {
    const rows = await apiList("Supplier", {
      fields: ["name","supplier_name","supplier_type","email_id","mobile_no",
        "tax_id","city","state","disabled","default_currency"],
      order: "supplier_name asc", limit: 300,
    });
    list.value = rows || [];
  } catch (e) {
    toast("Failed to load vendors: " + (e.message || e), "error");
  } finally { loading.value = false; }
}

async function loadAccounts() {
  try {
    const rows = await apiList("Account", {
      fields: ["name"],
      filters: [["account_type", "=", "Payable"], ["is_group", "=", 0]],
      limit: 50,
    });
    accounts.value = rows || [];
  } catch { accounts.value = []; }
}

function resetForm() {
  shipSameAsBilling.value = false;
  Object.assign(form, {
    name: "", supplier_name: "", supplier_type: "Company",
    tax_id: "", default_currency: "INR", payment_terms: "",
    email_id: "", mobile_code: "+91", mobile_no: "", phone: "", website: "",
    address_line1: "", address_line2: "",
    city: "", state: "", pincode: "", country: "India",
    ship_address_line1: "", ship_address_line2: "",
    ship_city: "", ship_state: "", ship_pincode: "", ship_country: "India",
    default_payable_account: "", disabled: 0,
  });
  Object.keys(formErrors).forEach(k => delete formErrors[k]);
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
    const doc = await apiGET("zoho_books_clone.api.docs.get_doc", { doctype: "Supplier", name });
    const mno = doc.mobile_no || "";
    Object.assign(form, {
      name: doc.name,
      supplier_name: doc.supplier_name || "",
      supplier_type: doc.supplier_type || "Company",
      tax_id: doc.tax_id || "",
      default_currency: doc.default_currency || "INR",
      payment_terms: doc.payment_terms || "",
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
      default_payable_account: doc.default_payable_account || "",
      disabled: doc.disabled || 0,
    });
  } catch (e) {
    toast("Could not load vendor: " + (e.message || e), "error");
    showDrawer.value = false;
  } finally { drawerLoading.value = false; }
}

function validateField(field) {
  delete formErrors[field];
  const v = form[field];
  const s = typeof v === "string" ? v.trim() : v;

  if (field === "supplier_name") {
    if (!s) formErrors.supplier_name = "Vendor name is required";
    else if (s.length < 2) formErrors.supplier_name = "Name must be at least 2 characters";
    else if (s.length > 140) formErrors.supplier_name = "Name must not exceed 140 characters";
  }
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
  if (field === "tax_id" && s && form.country === "India" && !GSTIN_REGEX.test(s))
    formErrors.tax_id = "Invalid GSTIN format (e.g. 27AAPFU0939F1ZV)";
  if (field === "pincode" && s) {
    const err = validatePincode(s, form.country);
    if (err) formErrors.pincode = err;
  }
}

function validateVendorForm() {
  Object.keys(formErrors).forEach((k) => delete formErrors[k]);
  if (!form.supplier_name.trim()) formErrors.supplier_name = "Vendor name is required";
  else if (form.supplier_name.trim().length < 2) formErrors.supplier_name = "Name must be at least 2 characters";
  if (form.email_id && !EMAIL_REGEX.test(form.email_id.trim())) formErrors.email_id = "Invalid email address";
  if (form.mobile_no) {
    const err = validateMobile(form.mobile_no.replace(/\D/g, ""), form.mobile_code);
    if (err) formErrors.mobile_no = err;
  }
  if (form.phone) { const err = validatePhone(form.phone); if (err) formErrors.phone = err; }
  if (form.website && !URL_REGEX.test(form.website.trim())) formErrors.website = "Website must start with http:// or https://";
  if (form.tax_id && form.country === "India" && !GSTIN_REGEX.test(form.tax_id.trim()))
    formErrors.tax_id = "Invalid GSTIN format (e.g. 27AAPFU0939F1ZV)";
  if (form.pincode) { const err = validatePincode(form.pincode, form.country); if (err) formErrors.pincode = err; }
  return Object.keys(formErrors).length === 0;
}

async function saveVendor() {
  if (!validateVendorForm()) {
    const firstErr = Object.values(formErrors)[0];
    toast(firstErr || "Please fix the errors before saving", "error");
    return;
  }
  saving.value = true;
  try {
    const doc = {
      doctype: "Supplier",
      ...(drawerMode.value === "edit" ? { name: form.name } : { naming_series: "SUPP-.YYYY.-.#####" }),
      supplier_name: form.supplier_name.trim(),
      supplier_type: form.supplier_type,
      tax_id: form.tax_id.trim(),
      default_currency: form.default_currency,
      payment_terms: form.payment_terms,
      email_id: form.email_id.trim(),
      mobile_no: form.mobile_no.trim() ? (form.mobile_code + " " + form.mobile_no.trim()) : "",
      phone: form.phone.trim(),
      website: form.website.trim(),
      address_line1: form.address_line1.trim(),
      address_line2: form.address_line2.trim(),
      city: form.city.trim(),
      state: form.state.trim(),
      pincode: form.pincode.trim(),
      country: form.country.trim() || "India",
      ship_address_line1: form.ship_address_line1.trim(),
      ship_address_line2: form.ship_address_line2.trim(),
      ship_city: form.ship_city.trim(),
      ship_state: form.ship_state.trim(),
      ship_pincode: form.ship_pincode.trim(),
      ship_country: form.ship_country.trim() || "India",
      default_payable_account: form.default_payable_account,
      disabled: form.disabled ? 1 : 0,
    };
    let doc_to_save = doc;
    if (drawerMode.value === "edit") {
      const fresh = await apiGET("zoho_books_clone.api.docs.get_doc", { doctype: "Supplier", name: form.name });
      doc_to_save = { ...fresh, ...doc };
    }
    const savedDoc = await apiSave(doc_to_save);
    const savedName = savedDoc?.name || form.name;
    // Sync billing address to Address doctype
    if (savedName && form.address_line1.trim()) {
      try {
        const existing = await apiList("Address", {
          filters:[["Dynamic Link","link_name","=",savedName],["Dynamic Link","link_doctype","=","Supplier"],["address_type","=","Billing"]],
          fields:["name"], limit:1, order:"modified desc",
        });
        await apiSave({
          doctype:"Address", ...(existing[0]?{name:existing[0].name}:{}),
          address_title:`${savedName} - Billing`, address_type:"Billing",
          address_line1:form.address_line1.trim(), address_line2:form.address_line2.trim(),
          city:form.city.trim(), state:form.state.trim(),
          pincode:form.pincode.trim(), country:form.country.trim()||"India",
          links:[{link_doctype:"Supplier",link_name:savedName}],
        });
      } catch {}
    }
    // Sync shipping address (skip if same-as-billing or blank)
    if (savedName && !shipSameAsBilling.value && form.ship_address_line1.trim()) {
      try {
        const existing = await apiList("Address", {
          filters:[["Dynamic Link","link_name","=",savedName],["Dynamic Link","link_doctype","=","Supplier"],["address_type","=","Shipping"]],
          fields:["name"], limit:1, order:"modified desc",
        });
        await apiSave({
          doctype:"Address", ...(existing[0]?{name:existing[0].name}:{}),
          address_title:`${savedName} - Shipping`, address_type:"Shipping",
          address_line1:form.ship_address_line1.trim(), address_line2:form.ship_address_line2.trim(),
          city:form.ship_city.trim(), state:form.ship_state.trim(),
          pincode:form.ship_pincode.trim(), country:form.ship_country.trim()||"India",
          links:[{link_doctype:"Supplier",link_name:savedName}],
        });
      } catch {}
    }
    toast(drawerMode.value === "edit" ? "Vendor updated!" : "Vendor created!");
    showDrawer.value = false;
    await load();
  } catch (e) {
    toast(e.message || "Could not save vendor", "error");
  } finally { saving.value = false; }
}

function confirmDelete(v) {
  deleteTarget.value = v;
  showDelete.value = true;
}

async function doDelete() {
  if (!deleteTarget.value) return;
  deleting.value = true;
  try {
    await apiDelete("Supplier", deleteTarget.value.name);
    toast("Vendor deleted");
    showDelete.value = false;
    deleteTarget.value = null;
    await load();
  } catch (e) {
    toast(e.message || "Could not delete vendor", "error");
  } finally { deleting.value = false; }
}

const selectedVendor  = ref(null);
const activeVendorTab = ref("overview");

// ── Live vendor data wired to backend ──────────────────────────────────────
const vendorSummary      = ref({});       // {outstanding, dn_credit, open_bill_count, ...}
const vendorTxns         = ref([]);       // chronological transactions
const vendorStatement    = ref({ rows: [], totals: {} });
const balancesByVendor   = ref({});       // {vendor_name: outstanding} — for the list view
const detailLoading      = ref(false);
const stmtRange          = reactive({ from: "", to: "" });

// Bulk selection (for the flat table)
const selectedRows = ref(new Set());
const bulkBusy = ref(false);
function toggleRow(name) {
  const s = new Set(selectedRows.value);
  s.has(name) ? s.delete(name) : s.add(name);
  selectedRows.value = s;
}
function clearSelection() { selectedRows.value = new Set(); }

async function selectVendor(v) {
  selectedVendor.value = v;
  activeVendorTab.value = "overview";
  detailLoading.value = true;
  vendorSummary.value = {};
  vendorTxns.value = [];
  vendorStatement.value = { rows: [], totals: {} };
  try {
    const [sum, txns] = await Promise.all([
      apiGET("zoho_books_clone.api.docs.get_vendor_summary", { vendor: v.name }).catch(() => ({})),
      apiGET("zoho_books_clone.api.docs.get_vendor_transactions", { vendor: v.name, limit: 100 }).catch(() => []),
    ]);
    vendorSummary.value = sum || {};
    vendorTxns.value = txns || [];
  } catch (e) { /* keep panel open */ }
  detailLoading.value = false;
}
function closeVendor() { selectedVendor.value = null; }

async function loadStatement() {
  if (!selectedVendor.value) return;
  detailLoading.value = true;
  try {
    vendorStatement.value = await apiGET("zoho_books_clone.api.docs.get_vendor_statement", {
      vendor: selectedVendor.value.name,
      from_date: stmtRange.from || "",
      to_date:   stmtRange.to   || "",
    }) || { rows: [], totals: {} };
  } catch (e) { toast(e.message || "Failed to load statement", "error"); }
  detailLoading.value = false;
}

async function emailVendorStatement() {
  if (!selectedVendor.value) return;
  try {
    const d = await apiGET("zoho_books_clone.api.docs.get_vendor_email_defaults",
      { vendor: selectedVendor.value.name });
    const to = prompt(`Send statement to:`, d?.to || "");
    if (!to) return;
    await (await import("../api/client.js")).apiPOST("zoho_books_clone.api.docs.send_vendor_statement_email", {
      vendor: selectedVendor.value.name,
      to, subject: d?.subject || "Statement", body: d?.body || "",
    });
    toast(`Statement emailed to ${to}`, "success");
  } catch (e) { toast(e.message || "Email failed", "error"); }
}

async function bulkSetDisabled(disable) {
  const names = [...selectedRows.value];
  if (!names.length) { toast("No vendors selected", "info"); return; }
  bulkBusy.value = true;
  try {
    const { apiPOST } = await import("../api/client.js");
    await apiPOST("zoho_books_clone.api.docs.bulk_set_vendor_disabled", {
      vendor_names: JSON.stringify(names),
      disabled: disable ? 1 : 0,
    });
    toast(`${disable ? "Disabled" : "Enabled"} ${names.length} vendor(s)`, "success");
    clearSelection();
    await load();
  } catch (e) { toast(e.message || "Bulk update failed", "error"); }
  finally { bulkBusy.value = false; }
}

function exportCSV() {
  const rows = selectedRows.value.size
    ? filtered.value.filter(v => selectedRows.value.has(v.name))
    : filtered.value;
  if (!rows.length) return;
  const head = ["Vendor","Type","GSTIN","Email","Mobile","City","State","Outstanding","Status"];
  const esc = v => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const out = [head.map(esc).join(",")];
  for (const v of rows) {
    out.push([
      v.supplier_name || v.name, v.supplier_type || "", v.tax_id || "",
      v.email_id || "", v.mobile_no || "", v.city || "", v.state || "",
      Number(balancesByVendor.value[v.name] || 0).toFixed(2),
      v.disabled ? "Disabled" : "Active",
    ].map(esc).join(","));
  }
  const blob = new Blob(["﻿" + out.join("\n")], { type: "text/csv;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url; a.download = `vendors_${new Date().toISOString().slice(0,10)}.csv`;
  a.click(); URL.revokeObjectURL(url);
  toast(`Exported ${rows.length} vendor(s)`, "success");
}

const totalPayable = computed(() =>
  Object.values(balancesByVendor.value).reduce((s, x) => s + Number(x || 0), 0)
);
const vendorsWithBalance = computed(() =>
  Object.values(balancesByVendor.value).filter(x => Number(x) > 0).length
);

const vendorKpiCards = computed(() => [
  {
    key: "total", label: "Total Vendors", format: "number",
    value: list.value.length,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    iconBg: "rgba(37,99,235,.1)", valueClass: "kv-blue",
  },
  {
    key: "active", label: "Active", format: "number",
    value: list.value.filter(v => !v.disabled).length,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>`,
    iconBg: "rgba(22,163,74,.1)", valueClass: "kv-green",
  },
  {
    key: "with_balance", label: "With Open Balance", format: "number",
    value: vendorsWithBalance.value,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    iconBg: "rgba(217,119,6,.1)", valueClass: "kv-amber",
  },
  {
    key: "total_payable", label: "Total Payable", format: "currency",
    value: totalPayable.value,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
    iconBg: "rgba(220,38,38,.1)", valueClass: "kv-red",
  },
]);

function vendorInitials(name) {
  return (name || "?").split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2);
}
function fmtCur(v) {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", minimumFractionDigits: 2 }).format(Number(v || 0));
}

async function loadAllBalances() {
  // Pull outstanding for every vendor in parallel — bounded to avoid hammering server
  const names = list.value.map(v => v.name);
  if (!names.length) return;
  const chunks = [];
  for (let i = 0; i < names.length; i += 8) chunks.push(names.slice(i, i + 8));
  const map = {};
  for (const chunk of chunks) {
    const results = await Promise.all(chunk.map(n =>
      apiGET("zoho_books_clone.api.docs.get_vendor_summary", { vendor: n }).catch(() => null)
    ));
    chunk.forEach((n, i) => { if (results[i]) map[n] = results[i].outstanding || 0; });
  }
  balancesByVendor.value = map;
}

onMounted(async () => {
  await load();
  loadAccounts();
  loadAllBalances();
});
</script>

<style scoped>
/* ── KPI Cards (unchanged) ─────────────────────────────── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; }
@media (max-width: 1200px) { .kpi-grid { grid-template-columns: repeat(2, 1fr); } }
@media (max-width: 600px)  { .kpi-grid { grid-template-columns: 1fr 1fr; } }

.kpi-card  { display: flex; align-items: center; gap: 14px; padding: 16px 18px; }
.kpi-icon  { width: 42px; height: 42px; border-radius: 10px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }
.kpi-label { font-size: 11px; color: #6b7280; letter-spacing: .06em; text-transform: uppercase; }
.kpi-value { font-size: 19px; font-weight: 700; margin-top: 3px; letter-spacing: -.02em; color: #111827; }
.kv-blue  { color: #2563eb; }
.kv-green { color: #16a34a; }
.kv-red   { color: #dc2626; }
.kv-amber { color: #d97706; }

/* ── Vendor Table ───────────────────────────────────────── */
.vt-table-card {
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  overflow: hidden;
}

.vt-table-wrap {
  overflow-x: auto;
}

.vt-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

/* Header */
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
.vt-th-check  { width: 36px; padding-left: 16px; }
.vt-th-num    { text-align: right; }
.vt-th-actions{ text-align: center; width: 88px; }

/* Rows */
.vt-row {
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: background 0.1s;
}
.vt-row:last-child { border-bottom: none; }
.vt-row:hover { background: #fafafa; }
.vt-row:hover .vt-actions { opacity: 1; }
.vt-row-selected { background: #fff7ed !important; }
.vt-row-disabled { opacity: 0.55; }

.vt-row-shimmer td {
  padding: 13px 14px;
}

/* Cells */
.vt-td {
  padding: 11px 14px;
  vertical-align: middle;
  color: #374151;
  white-space: nowrap;
}
.vt-td-check  { padding-left: 16px; width: 36px; }
.vt-td-num    { text-align: right; }
.vt-td-mono   { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; color: #374151; }
.vt-td-secondary { color: #6b7280; font-size: 12.5px; }
.vt-td-actions { text-align: center; width: 88px; }

/* Checkbox */
.vt-checkbox {
  width: 15px;
  height: 15px;
  accent-color: #E67700;
  cursor: pointer;
  border-radius: 3px;
}

/* Vendor name cell */
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
  background: linear-gradient(135deg, #E67700, #C96200);
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

/* Amounts */
.vt-amount-due { font-weight: 600; color: #E67700; font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12.5px; }
.vt-amount-nil { color: #d1d5db; }

/* Badges */
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
.vt-badge-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.vt-badge-green             { background: #f0fdf4; color: #15803d; border: 1px solid #bbf7d0; }
.vt-badge-green .vt-badge-dot { background: #22c55e; }
.vt-badge-red               { background: #fef2f2; color: #b91c1c; border: 1px solid #fecaca; }
.vt-badge-red   .vt-badge-dot { background: #ef4444; }
.vt-badge-blue  { background: #eff6ff; color: #1d4ed8; border: 1px solid #bfdbfe; }
.vt-badge-gray  { background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; }

/* Action buttons — visible only on row hover */
.vt-actions {
  display: flex;
  gap: 3px;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.12s;
}
.vt-act-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  border: 1px solid #e5e7eb;
  background: #fff;
  cursor: pointer;
  color: #6b7280;
  transition: background 0.1s, color 0.1s, border-color 0.1s;
}
.vt-act-edit:hover { background: #eff6ff; color: #2563eb; border-color: #bfdbfe; }
.vt-act-del:hover  { background: #fef2f2; color: #dc2626; border-color: #fecaca; }

/* Empty state */
.vt-empty {
  padding: 52px 24px;
  text-align: center;
}
.vt-empty-icon {
  margin: 0 auto 14px;
  width: 56px;
  height: 56px;
  border-radius: 14px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: center;
}
.vt-empty-title { font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 5px; }
.vt-empty-sub   { font-size: 13px; color: #9ca3af; }

/* Footer */
.vt-footer {
  padding: 9px 16px;
  border-top: 1px solid #f3f4f6;
  font-size: 12px;
  color: #9ca3af;
  background: #fafafa;
}
.vt-footer strong { color: #6b7280; font-weight: 600; }
</style>