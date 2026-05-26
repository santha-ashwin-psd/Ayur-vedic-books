<template>
<div>
  <!-- ── FLAT TABLE VIEW (default) ── -->
  <div v-if="!selectedCustomer" class="b-page cust-page">

    <div class="cust-toolbar">
      <div class="cust-toolbar-left">
        <div class="cust-filters">
          <button v-for="f in [{k:'all',l:'All'},{k:'active',l:'Active'},{k:'disabled',l:'Disabled'}]"
            :key="f.k" class="zb-inv-pill" :class="{'zb-inv-pill-active': activeFilter===f.k}"
            @click="activeFilter=f.k">
            {{f.l}}
            <span class="zb-pill-cnt" :class="activeFilter===f.k?'':'zb-pc-muted'">{{counts[f.k]}}</span>
          </button>
        </div>
      </div>
      <div class="cust-toolbar-right">
        <div class="cust-search">
          <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
          <input v-model="search" placeholder="Search customers…" class="cust-search-input" autocomplete="off"/>
        </div>
        <button class="zb-tb-btn" @click="load" title="Refresh"><span v-html="icon('refresh',13)"></span> Refresh</button>
        <button class="zb-tb-btn zb-tb-primary" @click="openAdd"><span v-html="icon('plus',13)"></span> New Customer</button>
      </div>
    </div>

    <!-- ── Summary Cards ── -->
    <div class="kpi-grid" style="margin-bottom:18px">
      <div v-for="kpi in custKpiCards" :key="kpi.key" class="books-card kpi-card">
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
              {{ kpi.format === 'currency' ? fmt(kpi.value) : kpi.value }}
            </template>
          </div>
        </div>
      </div>
    </div>
    <div class="vt-table-card">
      <div class="vt-table-wrap">
        <table class="vt-table">
          <thead>
            <tr>
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
                <td colspan="8"><div class="b-shimmer" style="height:12px;border-radius:3px;width:65%"></div></td>
              </tr>
            </template>
            <tr v-else-if="!filtered.length">
              <td colspan="8" class="vt-empty">
                <div class="vt-empty-icon">
                  <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="#d1d5db" stroke-width="1.3"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
                </div>
                <div class="vt-empty-title">{{search ? 'No results found' : 'No customers yet'}}</div>
                <div class="vt-empty-sub">{{search ? 'Try adjusting your search or filter' : 'Add your first customer to get started'}}</div>
                <button v-if="!search" class="nim-btn nim-btn-primary" style="margin-top:14px" @click="openAdd"><span v-html="icon('plus',13)"></span> New Customer</button>
              </td>
            </tr>
            <tr v-else v-for="c in filtered" :key="c.name"
              class="vt-row"
              :class="c.disabled ? 'vt-row-disabled' : ''"
              @click="selectCustomer(c)">
              <td class="vt-td vt-td-customer">
                <div class="vt-vendor-cell">
                  <div class="vt-avatar" :class="c.disabled ? 'vt-avatar-disabled' : ''">{{custInitials(c.customer_name)}}</div>
                  <div>
                    <div class="vt-vendor-name">{{c.customer_name}}</div>
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
                <span class="vt-badge" :class="c.disabled ? 'vt-badge-red' : 'vt-badge-green'">
                  <span class="vt-badge-dot"></span>{{c.disabled ? 'Disabled' : 'Active'}}
                </span>
              </td>
              <td class="vt-td vt-td-actions" @click.stop>
                <div class="vt-actions">
                  <button class="vt-act-btn vt-act-edit" @click="openEdit(c.name)" title="Edit"><span v-html="icon('edit',13)"></span></button>
                  <button class="vt-act-btn vt-act-del" @click="confirmDelete(c)" title="Delete"><span v-html="icon('trash',13)"></span></button>
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
          <span style="font-size:14px;font-weight:700;color:#111827">Active Customers ▾</span>
          <button class="zb-tb-btn zb-tb-primary" style="padding:5px 10px;font-size:12px" @click="openAdd"><span v-html="icon('plus',12)"></span> New</button>
        </div>
        <div class="cust-search" style="width:100%">
          <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
          <input v-model="search" placeholder="Search customers…" class="cust-search-input" autocomplete="off"/>
        </div>
      </div>
      <div style="flex:1;overflow-y:auto">
        <div v-for="c in filtered" :key="c.name"
          @click="selectCustomer(c)"
          :style="{padding:'12px 16px',borderBottom:'1px solid #f0f2f5',cursor:'pointer',
            background:selectedCustomer.name===c.name?'#EFF6FF':'transparent',
            borderLeft:selectedCustomer.name===c.name?'3px solid #2563EB':'3px solid transparent'}">
          <div style="display:flex;align-items:center;justify-content:space-between">
            <div style="flex:1;min-width:0">
              <div style="font-size:13px;font-weight:700;color:#111827;white-space:nowrap;overflow:hidden;text-overflow:ellipsis">{{c.customer_name}}</div>
              <div style="font-size:12px;margin-top:2px;font-family:monospace" :style="{color: c.outstanding>0 ? '#dc2626' : '#6B7280'}">{{ c.outstanding > 0 ? fmt(c.outstanding) : '₹0.00' }}</div>
            </div>
            <span class="b-badge" :class="c.disabled?'b-badge-red':'b-badge-green'" style="font-size:10px">{{c.disabled?'Disabled':'Active'}}</span>
          </div>
        </div>
      </div>
      <div style="padding:8px 16px;border-top:1px solid #f0f2f5;font-size:11.5px;color:#9ca3af;flex-shrink:0">{{filtered.length}} customers</div>
    </div>

    <!-- Right panel: customer detail -->
    <div style="flex:1;overflow-y:auto;background:#fff">
      <!-- Header action bar -->
      <div style="display:flex;align-items:center;justify-content:space-between;padding:14px 24px;border-bottom:1px solid #F3F4F6;position:sticky;top:0;background:#fff;z-index:10">
        <h2 style="font-size:20px;font-weight:700;color:#111827;margin:0">{{selectedCustomer.customer_name}}</h2>
        <div style="display:flex;gap:8px;align-items:center">
          <button class="nim-btn" style="background:#fff;border:1px solid #E5E7EB;color:#374151;font-size:13px" @click="openEdit(selectedCustomer.name)">Edit</button>
          <button style="background:none;border:none;cursor:pointer;padding:6px;border:1px solid #E5E7EB;border-radius:6px;display:grid;place-items:center"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6B7280" stroke-width="2"><path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/></svg></button>
          <button class="nim-btn nim-btn-primary" style="font-size:13px">New Transaction ▾</button>
          <button class="nim-btn" style="background:#fff;border:1px solid #E5E7EB;color:#374151;font-size:13px">More ▾</button>
          <button @click="closeCustomer" style="background:none;border:1px solid #E5E7EB;border-radius:6px;width:32px;height:32px;cursor:pointer;display:grid;place-items:center;color:#9CA3AF"><span v-html="icon('x',14)"></span></button>
        </div>
      </div>

      <!-- Tabs -->
      <div style="display:flex;border-bottom:2px solid #E5E7EB;padding:0 24px;gap:0">
        <button v-for="t in ['Overview','Comments','Transactions','Mails','Statement']" :key="t"
          @click="activeCustomerTab=t.toLowerCase()"
          :style="{padding:'10px 16px',fontSize:'13.5px',fontWeight:600,border:'none',background:'none',cursor:'pointer',
            color:activeCustomerTab===t.toLowerCase()?'#2563EB':'#6B7280',
            borderBottom:activeCustomerTab===t.toLowerCase()?'2px solid #2563EB':'2px solid transparent',marginBottom:'-2px'}">
          {{t}}
        </button>
      </div>

      <!-- Overview tab content -->
      <div v-if="activeCustomerTab==='overview'" style="display:flex;gap:0;align-items:flex-start">

        <!-- Left column: contact + sections -->
        <div style="flex:0 0 55%;border-right:1px solid #F3F4F6;padding:20px 24px;display:flex;flex-direction:column;gap:16px;min-height:500px">

          <div v-if="selectedCustomer.company_name||'PSD'" style="font-size:12px;font-weight:600;color:#6B7280">{{selectedCustomer.company_name||'PSD'}}</div>

          <div style="display:flex;align-items:flex-start;gap:12px;padding:14px;border:1px solid #F3F4F6;border-radius:10px;background:#FAFAFA">
            <div :style="{width:'44px',height:'44px',borderRadius:'50%',background:'#E5E7EB',display:'flex',alignItems:'center',justifyContent:'center',color:'#6B7280',fontSize:'16px',fontWeight:700,flexShrink:0}">
              {{custInitials(selectedCustomer.customer_name)}}
            </div>
            <div style="flex:1">
              <div style="font-size:14px;font-weight:700;color:#111827;margin-bottom:4px">{{ selectedCustomer.salutation ? selectedCustomer.salutation + ' ' : '' }}{{selectedCustomer.customer_name}}</div>
              <div v-if="selectedCustomer.email_id" style="font-size:12.5px;color:#6B7280;margin-bottom:3px">{{selectedCustomer.email_id}}</div>
              <div v-if="selectedCustomer.mobile_no" style="display:flex;align-items:center;gap:5px;font-size:12.5px;color:#374151;margin-bottom:3px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07A19.5 19.5 0 0 1 4.69 12 19.79 19.79 0 0 1 1.63 3.18 2 2 0 0 1 3.6 1h3a2 2 0 0 1 2 1.72c.127.96.361 1.903.7 2.81a2 2 0 0 1-.45 2.11L7.91 8.6A16 16 0 0 0 15.4 16.1l.97-.97a2 2 0 0 1 2.11-.45c.907.339 1.85.573 2.81.7A2 2 0 0 1 22 16.92z"/></svg>
                {{selectedCustomer.mobile_no}}
              </div>
              <div style="font-size:12px;color:#DC2626;margin-top:4px">Portal invitation not accepted</div>
              <button style="background:none;border:none;cursor:pointer;color:#2563EB;font-size:12px;padding:0;margin-top:2px">Re-invite</button>
            </div>
          </div>

          <div style="border:1px solid #F3F4F6;border-radius:10px;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:#FAFAFA;border-bottom:1px solid #F3F4F6">
              <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">ADDRESS</span>
              <span style="color:#9CA3AF;font-size:13px">▲</span>
            </div>
            <div style="padding:14px;display:flex;flex-direction:column;gap:12px">
              <div>
                <div style="font-size:12px;font-weight:600;color:#374151;margin-bottom:4px">Billing Address</div>
                <div v-if="selectedCustomer.city||selectedCustomer.address_line1" style="font-size:12.5px;color:#374151;line-height:1.6">
                  <div v-if="selectedCustomer.address_line1">{{selectedCustomer.address_line1}}</div>
                  <div>{{[selectedCustomer.city,selectedCustomer.state].filter(Boolean).join(', ')}}</div>
                </div>
                <div v-else style="font-size:12.5px;color:#9CA3AF">No Billing Address - <a href="#" @click.prevent="openEdit(selectedCustomer.name)" style="color:#2563EB;text-decoration:none">New Address</a></div>
              </div>
              <div>
                <div style="font-size:12px;font-weight:600;color:#374151;margin-bottom:4px">Shipping Address</div>
                <div style="font-size:12.5px;color:#9CA3AF">No Shipping Address - <a href="#" @click.prevent="openEdit(selectedCustomer.name)" style="color:#2563EB;text-decoration:none">New Address</a></div>
              </div>
            </div>
          </div>

          <div style="border:1px solid #F3F4F6;border-radius:10px;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:#FAFAFA;border-bottom:1px solid #F3F4F6">
              <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">OTHER DETAILS</span>
              <span style="color:#9CA3AF;font-size:13px">▲</span>
            </div>
            <div style="padding:14px;display:flex;flex-direction:column;gap:10px">
              <div style="display:flex;justify-content:space-between;font-size:12.5px">
                <span style="color:#6B7280">Customer Type</span><span style="font-weight:600;color:#111827">{{selectedCustomer.customer_type||'Business'}}</span>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:12.5px">
                <span style="color:#6B7280">Default Currency</span><span style="font-weight:600;color:#111827">{{selectedCustomer.default_currency||'INR'}}</span>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:12.5px;align-items:center">
                <span style="color:#6B7280">Portal Status</span>
                <span style="font-size:11px;font-weight:700;padding:2px 8px;border-radius:20px;background:#ECFDF5;color:#059669">● Enabled (1 of 1 Contacts)</span>
              </div>
              <div style="display:flex;justify-content:space-between;font-size:12.5px">
                <span style="color:#6B7280">Customer Language</span><span style="font-weight:600;color:#111827">English</span>
              </div>
            </div>
          </div>

          <div style="border:1px solid #F3F4F6;border-radius:10px;overflow:hidden">
            <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 14px;background:#FAFAFA">
              <span style="font-size:11px;font-weight:700;color:#9CA3AF;letter-spacing:0.8px">CONTACT PERSONS</span>
              <div style="display:flex;gap:6px">
                <button style="background:none;border:none;cursor:pointer;color:#2563EB;font-size:12px">+</button>
                <span style="color:#9CA3AF;font-size:13px">▲</span>
              </div>
            </div>
            <div style="padding:14px;font-size:12.5px;color:#9CA3AF">No contact persons found.</div>
          </div>
        </div>

        <div style="flex:1;padding:20px 24px;display:flex;flex-direction:column;gap:16px">
          <div>
            <div style="font-size:12px;color:#6B7280;margin-bottom:4px">Payment due period</div>
            <div style="font-size:14px;font-weight:600;color:#111827">Due on Receipt</div>
          </div>

          <div>
            <div style="font-size:16px;font-weight:700;color:#111827;margin-bottom:12px">Receivables</div>
            <table style="width:100%;border-collapse:collapse">
              <thead>
                <tr style="border-bottom:1px solid #F3F4F6">
                  <th style="text-align:left;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:0 0 8px">CURRENCY</th>
                  <th style="text-align:right;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:0 0 8px">OUTSTANDING RECEIVABLES</th>
                  <th style="text-align:right;font-size:10.5px;font-weight:600;color:#9CA3AF;padding:0 0 8px">UNUSED CREDITS</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td style="font-size:13px;font-weight:600;color:#374151;padding:10px 0">{{ selectedCustomer.default_currency || 'INR' }}</td>
                  <td style="text-align:right;font-size:13px;font-weight:700;color:#2563EB;padding:10px 0;font-family:monospace">{{fmt(selectedCustomer.credit_limit||0)}}</td>
                  <td style="text-align:right;font-size:13px;font-weight:700;padding:10px 0;font-family:monospace" :style="{color: selectedCustomer.outstanding>0?'#dc2626':'#111827'}">{{ fmt(selectedCustomer.outstanding||0) }}</td>
                </tr>
              </tbody>
            </table>
            <button style="background:none;border:none;cursor:pointer;color:#2563EB;font-size:12.5px;padding:6px 0">View Opening Balance</button>
          </div>

          <div style="margin-top:8px">
            <div style="font-size:12.5px;font-weight:700;color:#111827;margin-bottom:12px;display:flex;align-items:center;gap:8px">
              Recent Activity
            </div>
            <div style="text-align:center;padding:24px;color:#9CA3AF;border:1px dashed #E5E7EB;border-radius:8px;font-size:12.5px">
              No recent activity. Transactions will appear here.
            </div>
          </div>
        </div>
      </div>

      <!-- Statement Tab -->
      <div v-if="activeCustomerTab==='statement'" style="padding:24px">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
          <div>
            <div style="font-size:15px;font-weight:700;color:#111827">Account Statement</div>
            <div style="font-size:12px;color:#6B7280;margin-top:2px">Outstanding invoices for {{selectedCustomer.customer_name}}</div>
          </div>
          <div style="display:flex;gap:8px">
            <button class="nim-btn" style="font-size:12.5px;background:#EBFBEE;color:#2F9E44;border-color:#8CE99A" @click="loadStatement" :disabled="stmtLoading">
              <span v-if="stmtLoading">Loading…</span>
              <span v-else>Refresh</span>
            </button>
            <button v-if="stmt && stmt.email" class="nim-btn nim-btn-primary" style="font-size:12.5px" @click="sendStatement" :disabled="sendingStmt">
              {{sendingStmt ? 'Sending…' : '📧 Send to Customer'}}
            </button>
          </div>
        </div>

        <div v-if="stmtLoading" style="padding:40px;text-align:center;color:#9CA3AF">Loading statement…</div>
        <div v-else-if="!stmt" style="padding:40px;text-align:center;color:#9CA3AF">
          <div style="font-size:32px;margin-bottom:8px">📄</div>
          <div style="font-size:13.5px;font-weight:600;color:#374151;margin-bottom:4px">No statement loaded</div>
          <button class="nim-btn nim-btn-primary" @click="loadStatement">Load Statement</button>
        </div>
        <template v-else>
          <!-- Summary cards -->
          <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px">
            <div style="background:#FFF5F5;border:1px solid #FFC9C9;border-radius:10px;padding:14px 16px">
              <div style="font-size:11px;color:#C92A2A;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Total Outstanding</div>
              <div style="font-size:20px;font-weight:700;font-family:monospace;color:#C92A2A">₹{{fmtStmt(stmt.total_outstanding)}}</div>
            </div>
            <div style="background:#FFF9DB;border:1px solid #FFD43B;border-radius:10px;padding:14px 16px">
              <div style="font-size:11px;color:#E67700;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Overdue</div>
              <div style="font-size:20px;font-weight:700;font-family:monospace;color:#E67700">₹{{fmtStmt(stmt.overdue_amount)}}</div>
            </div>
            <div style="background:#F3F4F6;border:1px solid #E5E7EB;border-radius:10px;padding:14px 16px">
              <div style="font-size:11px;color:#6B7280;text-transform:uppercase;letter-spacing:.05em;margin-bottom:4px">Open Invoices</div>
              <div style="font-size:20px;font-weight:700;font-family:monospace;color:#111827">{{stmt.invoices.length}}</div>
            </div>
          </div>

          <!-- Outstanding invoices -->
          <div v-if="stmt.invoices.length" style="margin-bottom:16px">
            <div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em">Outstanding Invoices</div>
            <table style="width:100%;border-collapse:collapse;font-size:12.5px">
              <thead style="background:#F9FAFB">
                <tr>
                  <th style="padding:8px 12px;text-align:left;font-weight:600;color:#374151;border-bottom:1px solid #E5E7EB">Invoice</th>
                  <th style="padding:8px 12px;text-align:left;font-weight:600;color:#374151;border-bottom:1px solid #E5E7EB">Date</th>
                  <th style="padding:8px 12px;text-align:left;font-weight:600;color:#374151;border-bottom:1px solid #E5E7EB">Due Date</th>
                  <th style="padding:8px 12px;text-align:right;font-weight:600;color:#374151;border-bottom:1px solid #E5E7EB">Outstanding</th>
                  <th style="padding:8px 12px;text-align:center;font-weight:600;color:#374151;border-bottom:1px solid #E5E7EB">Status</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="inv in stmt.invoices" :key="inv.name" style="border-bottom:1px solid #F3F4F6">
                  <td style="padding:8px 12px;font-family:monospace;color:#3B5BDB;font-size:12px">{{inv.name}}</td>
                  <td style="padding:8px 12px;color:#6B7280">{{inv.posting_date}}</td>
                  <td style="padding:8px 12px;color:#6B7280">{{inv.due_date}}</td>
                  <td style="padding:8px 12px;text-align:right;font-family:monospace;font-weight:600">₹{{fmtStmt(inv.outstanding_amount)}}</td>
                  <td style="padding:8px 12px;text-align:center">
                    <span :style="'padding:2px 8px;border-radius:10px;font-size:11px;font-weight:600;'+(inv.is_overdue?'background:#FFF5F5;color:#C92A2A':'background:#EBFBEE;color:#2F9E44')">
                      {{inv.is_overdue ? 'Overdue' : 'Due'}}
                    </span>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div v-else style="padding:20px;text-align:center;color:#9CA3AF;background:#F9FAFB;border-radius:8px">No outstanding invoices</div>

          <!-- Recent payments -->
          <div v-if="stmt.payments.length" style="margin-top:16px">
            <div style="font-size:12px;font-weight:700;color:#374151;margin-bottom:8px;text-transform:uppercase;letter-spacing:.04em">Recent Payments</div>
            <table style="width:100%;border-collapse:collapse;font-size:12.5px">
              <thead style="background:#F9FAFB">
                <tr>
                  <th style="padding:8px 12px;text-align:left;font-weight:600;border-bottom:1px solid #E5E7EB">Payment</th>
                  <th style="padding:8px 12px;text-align:left;font-weight:600;border-bottom:1px solid #E5E7EB">Date</th>
                  <th style="padding:8px 12px;text-align:left;font-weight:600;border-bottom:1px solid #E5E7EB">Mode</th>
                  <th style="padding:8px 12px;text-align:right;font-weight:600;border-bottom:1px solid #E5E7EB">Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="p in stmt.payments" :key="p.name" style="border-bottom:1px solid #F3F4F6">
                  <td style="padding:8px 12px;font-family:monospace;color:#3B5BDB;font-size:12px">{{p.name}}</td>
                  <td style="padding:8px 12px;color:#6B7280">{{p.payment_date}}</td>
                  <td style="padding:8px 12px;color:#6B7280">{{p.mode_of_payment||'—'}}</td>
                  <td style="padding:8px 12px;text-align:right;font-family:monospace;font-weight:600;color:#2F9E44">₹{{fmtStmt(p.paid_amount)}}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <div v-if="!stmt.email" style="margin-top:12px;padding:10px 14px;background:#FFF9DB;border:1px solid #FFD43B;border-radius:8px;font-size:12.5px;color:#876800">
            ⚠️ No email on file — add an email to enable sending this statement.
          </div>
        </template>
      </div>

      <!-- Transactions tab -->
      <div v-if="activeCustomerTab==='transactions'" style="padding:24px">
        <div v-if="custTxnsLoading" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:24px;text-align:center;color:#9CA3AF">Loading transactions…</div>
        <div v-else-if="!custTxns.length" style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;padding:24px;text-align:center;color:#9CA3AF">
          <div style="font-size:14px;font-weight:600;color:#374151;margin-bottom:6px">No transactions yet</div>
          <div style="font-size:12.5px">Invoices, payments, and credit notes for {{selectedCustomer.customer_name}} will appear here.</div>
        </div>
        <div v-else style="background:#fff;border:1px solid #E5E7EB;border-radius:10px;overflow:hidden">
          <div style="display:grid;grid-template-columns:100px 1fr 110px 130px 130px 100px;gap:8px;background:#F9FAFB;padding:10px 14px;font-size:11px;font-weight:700;color:#6B7280;text-transform:uppercase;border-bottom:1px solid #E5E7EB">
            <span>Type</span><span>Reference</span><span>Date</span><span style="text-align:right">Amount</span><span style="text-align:right">Outstanding</span><span>Status</span>
          </div>
          <div v-for="t in custTxns" :key="t.type+'-'+t.name"
            style="display:grid;grid-template-columns:100px 1fr 110px 130px 130px 100px;gap:8px;padding:9px 14px;border-bottom:1px solid #F3F4F6;font-size:12.5px;align-items:center">
            <span :style="{
              fontSize:'10.5px',fontWeight:700,padding:'2px 8px',borderRadius:'10px',display:'inline-block',width:'fit-content',
              background: t.type==='Invoice' ? '#DBEAFE' : t.type==='Payment' ? '#D1FAE5' : '#FEE2E2',
              color: t.type==='Invoice' ? '#1E40AF' : t.type==='Payment' ? '#059669' : '#991B1B'
            }">{{t.type}}</span>
            <span style="font-family:monospace;color:#2563EB;font-weight:600">{{t.name}}</span>
            <span style="font-family:monospace;color:#6B7280">{{fmtDate(t.date)}}</span>
            <span style="text-align:right;font-family:monospace;font-weight:600" :style="{color: t.amount<0 ? '#059669' : '#374151'}">{{fmt(Math.abs(t.amount))}}</span>
            <span style="text-align:right;font-family:monospace" :style="{color: t.outstanding>0 ? '#dc2626' : '#9CA3AF'}">{{t.outstanding>0?fmt(t.outstanding):'—'}}</span>
            <span style="font-size:11.5px;color:#6B7280">{{t.status||(t.docstatus===2?'Cancelled':'Submitted')}}</span>
          </div>
        </div>
      </div>

      <!-- Comments / Mails — kept generic for now -->
      <div v-if="activeCustomerTab==='comments' || activeCustomerTab==='mails'" style="padding:32px 24px;text-align:center;color:#9CA3AF">
        <div style="font-size:14px;font-weight:600;color:#374151;margin-bottom:6px;text-transform:capitalize">{{activeCustomerTab}}</div>
        <div style="font-size:12.5px">No {{activeCustomerTab}} data available for {{selectedCustomer.customer_name}}.</div>
      </div>
    </div>
  </div>

  <!-- Drawer -->
  <Teleport to="body">
    <div v-if="showDrawer" class="cust-backdrop" @click.self="showDrawer=false">
      <div class="cust-drawer" style="width:680px;max-width:98vw">

        <div class="cust-drawer-header" style="background:linear-gradient(135deg,#3B5BDB,#2244b8);padding:18px 24px">
          <div style="display:flex;align-items:center;gap:12px;flex:1;min-width:0">
            <div style="width:40px;height:40px;border-radius:10px;background:rgba(255,255,255,.18);display:flex;align-items:center;justify-content:center;flex-shrink:0">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>
            </div>
            <div style="min-width:0">
              <div style="font-size:16px;font-weight:700;color:#fff">{{drawerMode==='add'?'New Customer':'Edit Customer'}}</div>
              <div style="font-size:12px;color:rgba(255,255,255,.7);margin-top:1px">{{drawerMode==='edit'?form.name:'Fill in customer details'}}</div>
            </div>
          </div>
          <button @click="showDrawer=false" style="background:rgba(255,255,255,.15);border:none;border-radius:6px;width:30px;height:30px;cursor:pointer;display:flex;align-items:center;justify-content:center;color:#fff;flex-shrink:0" v-html="icon('x',14)"></button>
        </div>

        <div style="display:flex;gap:0;border-bottom:2px solid #e8ecf0;background:#fff;padding:0 24px">
          <button v-for="t in [{k:'overview',l:'Overview'},{k:'address',l:'Address'},{k:'other',l:'Other Details'},{k:'bank',l:'Bank Details'},{k:'remarks',l:'Remarks'}]"
            :key="t.k" @click="drawerTab=t.k"
            :style="'padding:11px 16px;border:none;border-bottom:2px solid '+(drawerTab===t.k?'#3B5BDB':'transparent')+';margin-bottom:-2px;background:none;font-size:13px;font-weight:'+(drawerTab===t.k?'600':'500')+';color:'+(drawerTab===t.k?'#3B5BDB':'#6b7280')+';cursor:pointer;font-family:inherit;transition:all .15s'">
            {{t.l}}
          </button>
        </div>

        <div v-if="drawerLoading" style="flex:1;display:grid;place-items:center;color:#9ca3af;font-size:13px;padding:40px">
          Loading customer…
        </div>

        <div v-else class="cust-drawer-body" style="padding:24px;overflow-y:auto;flex:1">

          <!-- Overview Tab -->
          <template v-if="drawerTab==='overview'">

            <div style="margin-bottom:20px">
              <label class="nim-label" style="margin-bottom:8px;display:block">Customer Type</label>
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
              <label class="nim-label" style="margin-bottom:8px;display:block">GST Treatment</label>
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
              <label class="nim-label" style="margin-bottom:8px;display:block">Primary Contact</label>
              <div style="display:grid;grid-template-columns:140px 1fr 1fr;gap:10px">
                <select v-model="form.salutation" class="nim-input" style="cursor:pointer">
                  <option value="">Salutation</option>
                  <option>Mr.</option><option>Ms.</option><option>Mrs.</option><option>Dr.</option><option>Prof.</option>
                </select>
                <div style="position:relative">
                  <input v-model="form.first_name" class="nim-input" placeholder="First Name"
                    :style="formErrors.first_name?'border-color:#dc2626;background:#fff5f5':''"
                    @input="form.first_name=form.first_name.replace(/[^a-zA-Z\s.']/g,''); delete formErrors.first_name"
                    @blur="validateField('first_name')"/>
                  <div v-if="formErrors.first_name" style="position:absolute;left:0;top:100%;margin-top:3px;font-size:11.5px;color:#dc2626;white-space:nowrap">{{formErrors.first_name}}</div>
                </div>
                <div style="position:relative">
                  <input v-model="form.last_name" class="nim-input" placeholder="Last Name"
                    :style="formErrors.last_name?'border-color:#dc2626;background:#fff5f5':''"
                    @input="form.last_name=form.last_name.replace(/[^a-zA-Z\s.']/g,''); delete formErrors.last_name"
                    @blur="validateField('last_name')"/>
                  <div v-if="formErrors.last_name" style="position:absolute;left:0;top:100%;margin-top:3px;font-size:11.5px;color:#dc2626;white-space:nowrap">{{formErrors.last_name}}</div>
                </div>
              </div>
            </div>

            <div style="margin-bottom:16px">
              <label class="nim-label">Company Name <span v-if="form.customer_type==='Company'" class="nim-req">*</span></label>
              <input v-model="form.company_name" class="nim-input" placeholder="Company name"
                :style="formErrors.company_name?'border-color:#dc2626;background:#fff5f5':''"
                @input="delete formErrors.company_name"
                @blur="validateField('company_name')"/>
              <div v-if="formErrors.company_name" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                {{formErrors.company_name}}
              </div>
            </div>

            <div style="margin-bottom:16px">
              <label class="nim-label" style="display:flex;justify-content:space-between">
                <span>Display Name <span class="nim-req">*</span></span>
                <span :style="{fontSize:'11px',color:form.customer_name.length>90?'#dc2626':form.customer_name.length>0?'#9ca3af':'transparent'}">{{form.customer_name.length}}/100</span>
              </label>
              <input v-model="form.customer_name" class="nim-input" maxlength="100"
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
                  <label class="nim-label">
                    GSTIN / Tax ID
                    <span v-if="activeRule.requireGstin" class="nim-req">*</span>
                    <span v-else style="font-size:11px;font-weight:400;color:#9ca3af;margin-left:4px">(optional)</span>
                  </label>
                  <input v-model="form.tax_id" class="nim-input"
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
                  <label class="nim-label">PAN Number <span style="font-size:11px;font-weight:400;color:#9ca3af">(optional)</span></label>
                  <input v-model="form.pan_no" class="nim-input" placeholder="ABCDE1234F" maxlength="10"
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
                <label class="nim-label">Email Address</label>
                <input v-model="form.email_id" class="nim-input" placeholder="name@company.com"
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
                <label class="nim-label">Work Phone</label>
                <input v-model="form.phone" class="nim-input" placeholder="022-12345678"
                  :style="formErrors.phone?'border-color:#dc2626;background:#fff5f5':''"
                  @input="form.phone=form.phone.replace(/[^\d+\-\s()]/g,''); delete formErrors.phone"
                  @blur="validateField('phone')"/>
                <div v-if="formErrors.phone" style="margin-top:4px;font-size:12px;color:#dc2626;display:flex;align-items:center;gap:4px">
                  <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12" y2="16"/></svg>
                  {{formErrors.phone}}
                </div>
              </div>
              <div>
                <label class="nim-label">Mobile</label>
                <div style="display:flex;gap:0">
                  <select v-model="form.mobile_code" class="nim-input" style="width:90px;border-right:none;border-radius:8px 0 0 8px;background:#f8f9fc;cursor:pointer;flex-shrink:0;padding:0 6px"
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
                  <input v-model="form.mobile_no" class="nim-input" style="border-radius:0 8px 8px 0;flex:1" placeholder="98765 43210"
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
                <label class="nim-label">Website</label>
                <input v-model="form.website" class="nim-input" placeholder="https://company.com"
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

            <div class="cust-sec-label" style="margin-top:0">Billing Preferences</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:14px;margin-bottom:20px">
              <div>
                <label class="nim-label">Currency</label>
                <select v-model="form.default_currency" class="nim-input" style="cursor:pointer">
                  <option>INR</option><option>USD</option><option>EUR</option><option>GBP</option><option>AED</option><option>SGD</option><option>JPY</option><option>CAD</option><option>AUD</option>
                </select>
              </div>
              <div>
                <label class="nim-label">Payment Terms</label>
                <select v-model="form.payment_terms" class="nim-input" style="cursor:pointer">
                  <option value="">— Select —</option>
                  <option>Net 7</option><option>Net 15</option><option>Net 30</option><option>Net 45</option><option>Net 60</option>
                  <option>Due on Receipt</option><option>End of Month</option>
                </select>
              </div>
              <div>
                <label class="nim-label">Credit Limit ({{ currencySymbol }})</label>
                <input v-model.number="form.credit_limit" type="number" min="0" class="nim-input" placeholder="0 = unlimited"
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
            <div class="cust-sec-label" style="margin-top:0">Billing Address</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px">
              <div style="grid-column:span 2">
                <label class="nim-label">Address Line 1</label>
                <input v-model="form.address_line1" class="nim-input" placeholder="Street, building no., floor"/>
              </div>
              <div style="grid-column:span 2">
                <label class="nim-label">Address Line 2</label>
                <input v-model="form.address_line2" class="nim-input" placeholder="Area, landmark, district"/>
              </div>
              <div>
                <label class="nim-label">City</label>
                <input v-model="form.city" class="nim-input" placeholder="Mumbai"
                  @input="form.city=form.city.replace(/[^a-zA-Z\s]/g,'')"/>
              </div>
              <div>
                <label class="nim-label">Country</label>
                <select v-model="form.country" class="nim-input" style="cursor:pointer" @change="form.state=''; delete formErrors.pincode; if(form.pincode) validateField('pincode')">
                  <option value="">— Select Country —</option>
                  <option v-for="c in COUNTRIES" :key="c">{{c}}</option>
                </select>
              </div>
              <div>
                <label class="nim-label">State / Province</label>
                <select v-if="statesFor(form.country).length" v-model="form.state" class="nim-input" style="cursor:pointer">
                  <option value="">— Select State —</option>
                  <option v-for="s in statesFor(form.country)" :key="s" :value="s">{{s}}</option>
                </select>
                <input v-else v-model="form.state" class="nim-input" placeholder="Enter state / province"/>
              </div>
              <div>
                <label class="nim-label">Pincode</label>
                <input v-model="form.pincode" class="nim-input"
                  :placeholder="pincodePlaceholder(form.country)"
                  :style="formErrors.pincode?'border-color:#dc2626;background:#fff5f5':form.pincode&&!formErrors.pincode?'border-color:#2f9e44':''"
                  @input="form.pincode=sanitizePincode(form.pincode, form.country); delete formErrors.pincode"
                  @blur="validateField('pincode')"/>
                <div v-if="formErrors.pincode" style="margin-top:4px;font-size:12px;color:#dc2626">{{formErrors.pincode}}</div>
                <div v-else-if="form.pincode&&!formErrors.pincode" style="margin-top:4px;font-size:11px;color:#9ca3af">{{pincodeHint(form.country)}}</div>
              </div>
            </div>

            <div class="cust-sec-label">Shipping Address <span style="font-size:11px;font-weight:400;color:#9ca3af;margin-left:6px">— leave blank to use billing address</span></div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
              <div style="grid-column:span 2">
                <label class="nim-label">Address Line 1</label>
                <input v-model="form.ship_address_line1" class="nim-input" placeholder="Street, building no., floor"/>
              </div>
              <div style="grid-column:span 2">
                <label class="nim-label">Address Line 2</label>
                <input v-model="form.ship_address_line2" class="nim-input" placeholder="Area, landmark, district"/>
              </div>
              <div>
                <label class="nim-label">City</label>
                <input v-model="form.ship_city" class="nim-input" placeholder="Mumbai"
                  @input="form.ship_city=form.ship_city.replace(/[^a-zA-Z\s]/g,'')"/>
              </div>
              <div>
                <label class="nim-label">Country</label>
                <select v-model="form.ship_country" class="nim-input" style="cursor:pointer" @change="form.ship_state=''; delete formErrors.ship_pincode; if(form.ship_pincode) validateField('ship_pincode')">
                  <option value="">— Select Country —</option>
                  <option v-for="c in COUNTRIES" :key="c">{{c}}</option>
                </select>
              </div>
              <div>
                <label class="nim-label">State / Province</label>
                <select v-if="statesFor(form.ship_country).length" v-model="form.ship_state" class="nim-input" style="cursor:pointer">
                  <option value="">— Select State —</option>
                  <option v-for="s in statesFor(form.ship_country)" :key="s" :value="s">{{s}}</option>
                </select>
                <input v-else v-model="form.ship_state" class="nim-input" placeholder="Enter state / province"/>
              </div>
              <div>
                <label class="nim-label">Pincode</label>
                <input v-model="form.ship_pincode" class="nim-input"
                  :placeholder="pincodePlaceholder(form.ship_country)"
                  :style="formErrors.ship_pincode?'border-color:#dc2626;background:#fff5f5':form.ship_pincode&&!formErrors.ship_pincode?'border-color:#2f9e44':''"
                  @input="form.ship_pincode=sanitizePincode(form.ship_pincode, form.ship_country); delete formErrors.ship_pincode"
                  @blur="validateField('ship_pincode')"/>
                <div v-if="formErrors.ship_pincode" style="margin-top:4px;font-size:12px;color:#dc2626">{{formErrors.ship_pincode}}</div>
                <div v-else-if="form.ship_pincode&&!formErrors.ship_pincode" style="margin-top:4px;font-size:11px;color:#9ca3af">{{pincodeHint(form.ship_country)}}</div>
              </div>
            </div>
          </template>

          <!-- Other Details Tab -->
          <template v-else-if="drawerTab==='other'">
            <div class="cust-sec-label" style="margin-top:0">Tax &amp; Compliance</div>

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
                  <label class="nim-label">
                    Place of Supply
                    <span v-if="activeRule.requirePlaceOfSupply" class="nim-req">*</span>
                  </label>
                  <select v-model="form.place_of_supply" class="nim-input" style="cursor:pointer"
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
                <label class="nim-label">Customer Source</label>
                <select v-model="form.source" class="nim-input" style="cursor:pointer">
                  <option value="">— Select —</option>
                  <option>Cold Calling</option><option>Email</option><option>Existing Customer</option>
                  <option>Partner</option><option>Campaign</option><option>Website</option><option>Referral</option><option>Word of Mouth</option><option>Other</option>
                </select>
              </div>
            </div>

            <div class="cust-sec-label">Opening Balance</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:18px">
              <div>
                <label class="nim-label">Opening Balance (₹)</label>
                <input v-model.number="form.opening_balance" type="number" min="0" class="nim-input" placeholder="0.00"
                  :style="formErrors.opening_balance?'border-color:#dc2626;background:#fff5f5':''"
                  @input="delete formErrors.opening_balance"
                  @blur="validateField('opening_balance')"/>
                <div v-if="formErrors.opening_balance" style="margin-top:4px;font-size:12px;color:#dc2626">{{formErrors.opening_balance}}</div>
              </div>
            </div>
          </template>

          <!-- Bank Tab -->
          <template v-else-if="drawerTab==='bank'">
            <div class="cust-sec-label" style="margin-top:0">Bank Account</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px">
              <div style="grid-column:span 2">
                <label class="nim-label">Bank Name</label>
                <input v-model="form.bank_name" class="nim-input" placeholder="HDFC Bank, SBI, ICICI…"/>
              </div>
              <div>
                <label class="nim-label">Account Number <span style="font-size:11px;font-weight:400;color:#9ca3af">(9–18 digits)</span></label>
                <input v-model="form.bank_account_no" class="nim-input" placeholder="XXXXXXXXXXXXXXXX" maxlength="18" style="font-family:var(--mono)"
                  :style="formErrors.bank_account_no?'border-color:#dc2626;background:#fff5f5':form.bank_account_no&&!formErrors.bank_account_no&&/^\d{9,18}$/.test(form.bank_account_no)?'border-color:#2f9e44':''"
                  @input="form.bank_account_no=form.bank_account_no.replace(/\D/g,''); delete formErrors.bank_account_no"
                  @blur="validateField('bank_account_no')"/>
                <div v-if="formErrors.bank_account_no" style="margin-top:4px;font-size:12px;color:#dc2626">{{formErrors.bank_account_no}}</div>
                <div v-else-if="form.bank_account_no&&/^\d{9,18}$/.test(form.bank_account_no)" style="margin-top:4px;font-size:12px;color:#2f9e44">Valid account number</div>
              </div>
              <div>
                <label class="nim-label">IFSC Code <span style="font-size:11px;font-weight:400;color:#9ca3af">(AAAA0XXXXXX)</span></label>
                <input v-model="form.bank_ifsc" class="nim-input" placeholder="HDFC0001234" maxlength="11" style="font-family:var(--mono)"
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
            <div class="cust-sec-label" style="margin-top:0">Internal Notes</div>
            <textarea v-model="form.notes" class="nim-input" rows="14" style="resize:vertical;line-height:1.6;min-height:280px" placeholder="Add any internal notes about this customer — payment behaviour, communication preferences, account history…"></textarea>
          </template>

        </div>

        <!-- Footer -->
        <div class="nim-footer" style="border-top:1px solid #e8ecf0;padding:14px 24px;background:#fafbfd">
          <button class="nim-btn nim-btn-ghost" @click="showDrawer=false">Cancel</button>
          <button class="nim-btn nim-btn-primary" @click="saveCustomer" :disabled="saving" style="background:#3B5BDB;border-color:#3B5BDB;min-width:140px;position:relative">
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
import { ref, reactive, computed, watch, onMounted } from "vue";
import { apiList, apiGET, apiSave, apiDelete, apiPOST } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
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
    value: counts.value.all,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2" stroke-linecap="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>`,
    iconBg: "rgba(37,99,235,.1)", valueClass: "kv-blue",
  },
  {
    key: "active", label: "Active", format: "number",
    value: counts.value.active,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#16a34a" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><polyline points="16 11 18 13 22 9"/></svg>`,
    iconBg: "rgba(22,163,74,.1)", valueClass: "kv-green",
  },
  {
    key: "disabled", label: "Disabled", format: "number",
    value: counts.value.disabled,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="2" stroke-linecap="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/><line x1="18" y1="8" x2="23" y2="13"/><line x1="23" y1="8" x2="18" y2="13"/></svg>`,
    iconBg: "rgba(220,38,38,.1)", valueClass: "kv-red",
  },
  {
    key: "outstanding", label: "Total Outstanding", format: "currency",
    value: totalOutstanding.value,
    icon: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="2" stroke-linecap="round"><line x1="12" y1="1" x2="12" y2="23"/><path d="M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>`,
    iconBg: "rgba(217,119,6,.1)", valueClass: "kv-amber",
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
    const [rows, balances] = await Promise.all([
      apiList("Customer", {
        fields: ["name","customer_name","customer_type","email_id","mobile_no",
          "tax_id","city","state","disabled","default_currency","credit_limit","salutation","gst_treatment"],
        order: "customer_name asc", limit: 300,
      }),
      apiGET("zoho_books_clone.api.books_data.get_customer_outstanding").catch(() => ({})),
    ]);
    list.value = (rows || []).map(c => ({ ...c, outstanding: balances[c.name] || 0 }));
  } catch (e) {
    toast("Failed to load customers: " + (e.message || e), "error");
  } finally { loading.value = false; }
}

function resetForm() {
  drawerTab.value = "overview";
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

async function saveCustomer() {
  if (!validateCustomerForm()) {
    const firstErrField = Object.keys(formErrors)[0];
    if (firstErrField && FIELD_TAB[firstErrField]) drawerTab.value = FIELD_TAB[firstErrField];
    toast(Object.values(formErrors)[0], "error");
    return;
  }
  saving.value = true;
  try {
    const doc = {
      doctype: "Customer",
      ...(drawerMode.value === "edit" ? { name: form.name } : { naming_series: "CUST-.YYYY.-.#####" }),
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
    await apiSave(doc_to_save);
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

async function selectCustomer(c) {
  selectedCustomer.value = c;
  activeCustomerTab.value = "overview";
  stmt.value = null;
  custTxns.value = [];
  custTxnsLoading.value = true;
  try {
    custTxns.value = await apiGET("zoho_books_clone.api.docs.get_customer_transactions",
      { customer: c.name, limit: 100 }) || [];
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
    const co = (await apiGET("frappe.client.get_value", {
      doctype: "Books Settings", filters: JSON.stringify({ name: "Books Settings" }),
      fieldname: JSON.stringify(["default_company"]),
    }))?.default_company || "";
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
    const co = stmt.value?.invoices?.[0]?.company || (await apiGET("frappe.client.get_value", {
      doctype: "Books Settings", filters: JSON.stringify({ name: "Books Settings" }),
      fieldname: JSON.stringify(["default_company"]),
    }))?.default_company || "";
    await apiPOST("zoho_books_clone.db.queries.send_customer_statement", {
      customer: selectedCustomer.value.name, company: co,
    });
    toast("Statement sent to " + stmt.value.email);
  } catch (e) { toast(e.message || "Failed to send statement", "error"); }
  sendingStmt.value = false;
}

watch(activeCustomerTab, (t) => { if (t === "statement" && !stmt.value) loadStatement(); });

onMounted(load);
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

/* ── Customer Table ─────────────────────────────────────── */
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
.vt-th-actions { text-align: center; width: 88px; }

/* Rows */
.vt-row {
  border-bottom: 1px solid #f3f4f6;
  cursor: pointer;
  transition: background 0.1s;
}
.vt-row:last-child { border-bottom: none; }
.vt-row:hover { background: #fafafa; }
.vt-row:hover .vt-actions { opacity: 1; }
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
.vt-td-mono      { font-family: 'SF Mono', 'Fira Code', monospace; font-size: 12px; color: #374151; }
.vt-td-secondary { color: #6b7280; font-size: 12.5px; }
.vt-td-actions   { text-align: center; width: 88px; }

/* Customer name cell */
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
  background: linear-gradient(135deg, #318cd0, #1d4ed8);
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