<template>
  <div class="rec-page">
    <!-- ============================================================ TOOLBAR -->
    <div class="rec-actions">
      <div class="rec-search-wrap">
        <span v-html="icon('search',13)" style="color:#9ca3af;flex-shrink:0"></span>
        <input v-model="search" placeholder="Search recurring bills…" class="rec-search-input" />
      </div>
      <div class="rec-pills">
        <button v-for="t in tabs" :key="t.key" class="rec-pill" :class="{active:activeTab===t.key, ['pill-'+t.key]: t.key!=='all'}" @click="activeTab=t.key">
          {{ t.label }}
        </button>
      </div>
      <div style="display:flex;gap:8px;margin-left:auto">
        <button class="rec-btn-ghost" @click="load" :disabled="loading">
          <span v-html="icon('refresh',14)"></span>
        </button>
        <button class="rec-btn-primary" @click="openNew">
          <span v-html="icon('plus',13)"></span> New Recurring Bill
        </button>
      </div>
    </div>

    <!-- ── KPI Cards ── -->
    <div class="bk-kpi-grid bk-kpi-grid-4">
      <div class="bk-kpi-card"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dbeafe"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="1.8"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Total Schedules</div><div class="bk-kpi-value">{{ list.length }}</div><div class="bk-kpi-trend bk-trend-neutral">all recurring bills</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-success clickable" @click="activeTab='Active'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#dcfce7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none"><circle cx="12" cy="12" r="10" stroke="#16a34a" stroke-width="1.8"/><polyline points="7 12.5 10.5 16 17 9" stroke="#16a34a" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Active</div><div class="bk-kpi-value bk-kpi-green">{{ counts.active }}</div><div class="bk-kpi-trend bk-trend-neutral">running</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-warn clickable" @click="activeTab='Paused'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#fef3c7"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#d97706" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="10" y1="15" x2="10" y2="9"/><line x1="14" y1="15" x2="14" y2="9"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Paused</div><div class="bk-kpi-value bk-kpi-amber">{{ counts.paused }}</div><div class="bk-kpi-trend bk-trend-neutral">on hold</div></div></div></div>
      <div class="bk-kpi-card bk-kpi-danger clickable" @click="activeTab='Cancelled'"><div class="bk-kpi-inner"><div class="bk-kpi-icon" style="background:#fee2e2"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#dc2626" stroke-width="1.8"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></div><div class="bk-kpi-body"><div class="bk-kpi-label">Cancelled</div><div class="bk-kpi-value bk-kpi-red">{{ counts.cancelled }}</div><div class="bk-kpi-trend bk-trend-neutral">stopped</div></div></div></div>
    </div>
    <div class="bk-stat-grid">
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Active Rate</div><div class="bk-stat-value bk-kpi-green">{{ list.length ? Math.round(counts.active/list.length*100) : 0 }}%</div></div><div class="bk-stat-icon" style="background:#dcfce7;color:#16a34a"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Weekly Bills</div><div class="bk-stat-value">{{ list.filter(r=>r.frequency==='Weekly').length }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Monthly Bills</div><div class="bk-stat-value">{{ list.filter(r=>r.frequency==='Monthly').length }}</div></div><div class="bk-stat-icon" style="background:#dbeafe;color:#2563eb"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg></div></div></div>
      <div class="bk-stat-card"><div class="bk-stat-content"><div><div class="bk-stat-label">Annual Bills</div><div class="bk-stat-value">{{ list.filter(r=>r.frequency==='Yearly').length }}</div></div><div class="bk-stat-icon" style="background:#e5e7eb;color:#6b7280"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="17 1 21 5 17 9"/><path d="M3 11V9a4 4 0 0 1 4-4h14"/><polyline points="7 23 3 19 7 15"/><path d="M21 13v2a4 4 0 0 1-4 4H3"/></svg></div></div></div>
    </div>

    <!-- ============================================================ TABLE -->
    <div class="rec-card">
      <table class="rec-table">
        <thead>
          <tr>
            <th style="width:32px"><input type="checkbox" :checked="allSelected" @change="toggleAll" /></th>
            <th @click="sort('name')" class="sortable">Subscription # <span v-html="sortArrow('name')"></span></th>
            <th @click="sort('reference_document')" class="sortable">Reference Bill <span v-html="sortArrow('reference_document')"></span></th>
            <th @click="sort('frequency')" class="sortable">Frequency <span v-html="sortArrow('frequency')"></span></th>
            <th @click="sort('start_date')" class="sortable">Start Date <span v-html="sortArrow('start_date')"></span></th>
            <th @click="sort('next_schedule_date')" class="sortable">Next Run <span v-html="sortArrow('next_schedule_date')"></span></th>
            <th>Status</th>
            <th style="width:120px;text-align:right">Actions</th>
          </tr>
        </thead>
        <tbody>
          <template v-if="loading">
            <tr v-for="n in 6" :key="n"><td colspan="8"><div class="rec-shimmer"></div></td></tr>
          </template>
          <template v-else>
            <tr v-for="r in paged" :key="r.name" class="rec-row" :class="{selected:selected.includes(r.name)}" @click="openView(r)">
              <td @click.stop><input type="checkbox" :checked="selected.includes(r.name)" @change="toggleOne(r.name)" /></td>
              <td><span class="rec-num">{{ r.name }}</span></td>
              <td><span class="rec-ref">{{ r.reference_document||'—' }}</span></td>
              <td>{{ r.frequency||'—' }}</td>
              <td class="text-muted mono-sm">{{ fmtDate(r.start_date) }}</td>
              <td class="mono-sm" :class="isDue(r)?'text-accent':''">{{ fmtDate(r.next_schedule_date)||'—' }}</td>
              <td><span class="rec-badge" :class="statusClass(r.status)">{{ r.status||'Active' }}</span></td>
              <td @click.stop style="text-align:right">
                <button class="rec-act-btn" @click="openView(r)" title="View"><span v-html="icon('eye',13)"></span></button>
                <button v-if="(r.ui_status||r.status||'Active')==='Active'" class="rec-act-btn" @click="quickAction(r,'pause')" title="Pause"><span v-html="icon('pause',13)"></span></button>
                <button v-else-if="(r.ui_status||r.status||'Active')==='Paused'" class="rec-act-btn" @click="quickAction(r,'resume')" title="Resume"><span v-html="icon('play',13)"></span></button>
                <button class="rec-act-btn rec-act-danger" @click="quickAction(r,'delete')" title="Delete"><span v-html="icon('trash',13)"></span></button>
              </td>
            </tr>
            <tr v-if="!sorted.length">
              <td colspan="8" class="rec-empty">
                <div class="rec-empty-wrap">
                  <div class="rec-empty-icon" v-html="icon('repeat',32)"></div>
                  <div class="rec-empty-title">No recurring bills found</div>
                  <div class="rec-empty-sub">Create a recurring bill to auto-generate purchase orders on a schedule.</div>
                  <button class="rec-btn-primary" @click="openNew" style="margin-top:12px">
                    <span v-html="icon('plus',13)"></span> Create your first recurring bill
                  </button>
                </div>
              </td>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

    <!-- ── Pagination ── -->
    <div v-if="!loading && sorted.length" style="padding:12px 4px 4px">
      <Pagination v-model:page="page" v-model:page-size="pageSize" :total-items="sorted.length" />
    </div>

    <!-- ============================================================ CREATE DRAWER -->
    <div v-if="drawerOpen" class="rec-overlay" @click.self="drawerOpen=false"></div>
    <div class="rec-drawer" :class="{open:drawerOpen}">
      <div class="rec-dheader" :class="editMode?'edit':''">
        <div class="rec-dheader-left">
          <div class="rec-dheader-ico" :class="editMode?'edit':''">
            <span v-html="icon(editMode?'edit':'repeat',18)"></span>
          </div>
          <div>
            <div class="rec-dheader-title">{{ editMode ? 'Edit Recurring Bill' : 'New Recurring Bill' }}</div>
            <div class="rec-dheader-sub">{{ editMode ? form._name : 'Automatically generate vendor bills on a schedule' }}</div>
          </div>
        </div>
        <button class="rec-dclose" @click="onOverlayClose"><span v-html="icon('x',16)"></span></button>
      </div>

      <div class="rec-dbody">
        <!-- Section: Reference -->
        <div class="rec-section">
          <div class="rec-section-hdr">
            <span v-html="icon('folder',13)"></span>
            <span>Reference Document</span>
          </div>
          <div class="rec-fields-grid">
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Reference Bill <span class="req">*</span></label>
              <SearchableSelect v-model="form.reference_document" :options="refDocs" placeholder="Search a saved bill…" @search="fetchRefDocs" />
              <div class="rec-field-help" v-if="!form.reference_document">
                Pick an existing bill to use as the template for this recurring schedule.
              </div>
            </div>
          </div>
        </div>

        <!-- Section: Schedule -->
        <div class="rec-section">
          <div class="rec-section-hdr">
            <span v-html="icon('refresh',13)"></span>
            <span>Schedule</span>
          </div>
          <div class="rec-fields-grid">
            <div class="rec-field">
              <label class="rec-label">Frequency <span class="req">*</span></label>
              <select v-model="form.frequency" class="rec-select">
                <option value="Daily">Daily</option>
                <option value="Weekly">Weekly</option>
                <option value="Monthly">Monthly</option>
                <option value="Quarterly">Quarterly</option>
                <option value="Half-Yearly">Half-Yearly</option>
                <option value="Yearly">Yearly</option>
              </select>
            </div>
            <div class="rec-field">
              <label class="rec-label">Submit on Creation</label>
              <select v-model="form.submit_on_creation" class="rec-select">
                <option :value="1">Yes — auto-submit</option>
                <option :value="0">No — save as draft</option>
              </select>
            </div>
            <div class="rec-field">
              <label class="rec-label">Start Date <span class="req">*</span></label>
              <input v-model="form.start_date" type="date" class="rec-input" :disabled="editMode" />
            </div>
            <div class="rec-field">
              <label class="rec-label">End Date <span class="rec-hint">(optional)</span></label>
              <input v-model="form.end_date" type="date" class="rec-input" :min="form.start_date" />
            </div>
          </div>
        </div>

        <!-- Section: Notification -->
        <div class="rec-section">
          <div class="rec-section-hdr">
            <span v-html="icon('mail',13)"></span>
            <span>Notification</span>
            <label class="rec-toggle">
              <input type="checkbox" v-model="form._notify" />
              <span class="rec-toggle-slider"></span>
            </label>
          </div>
          <div v-if="!form._notify" class="rec-section-empty">
            Email notifications are off. Toggle to email someone every time a document is generated.
          </div>
          <div v-else class="rec-fields-grid">
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Recipients <span class="rec-hint">(comma separated)</span></label>
              <input v-model="form.recipients" type="text" class="rec-input" :class="{'field-error': recipientError}" placeholder="finance@company.com, owner@company.com" @blur="validateRecipients" @input="recipientError=''" />
              <div v-if="form.recipients.trim()" style="display:flex;flex-wrap:wrap;gap:4px;margin-top:6px">
                <span v-for="em in form.recipients.split(',').map(s=>s.trim()).filter(Boolean)" :key="em"
                  :style="{
                    display:'inline-flex', alignItems:'center', gap:'4px',
                    padding:'2px 8px', borderRadius:'999px', fontSize:'12px', fontWeight:'500',
                    background: /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em) ? '#dcfce7' : '#fee2e2',
                    color:    /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em) ? '#15803d' : '#b91c1c',
                    border:  '1px solid ' + (/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em) ? '#86efac' : '#fca5a5')
                  }">
                  <svg v-if="/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(em)" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><polyline points="20 6 9 17 4 12"/></svg>
                  <svg v-else width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
                  {{ em }}
                </span>
              </div>
              <div v-if="recipientError" class="exp-field-hint exp-field-hint-err" style="margin-top:4px">⚠ Fix invalid email addresses above before saving</div>
            </div>
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Email Subject</label>
              <input v-model="form.subject" type="text" class="rec-input" :class="{'field-error': form.subject.length > 100}" maxlength="100" placeholder="Your recurring bill is ready" />
              <div class="exp-field-hint" :class="{'exp-field-hint-err': form.subject.length >= 100}" style="margin-top:4px;text-align:right">{{ form.subject.length }}/100</div>
            </div>
            <div class="rec-field" style="grid-column:1/-1">
              <label class="rec-label">Email Message</label>
              <textarea v-model="form.message" class="rec-input" rows="3" placeholder="Hello, please find your latest purchase order attached…"></textarea>
            </div>
          </div>
        </div>
      </div>

      <div class="rec-dfooter">
        <button class="rec-btn-ghost" @click="onOverlayClose" :disabled="drawerSaving">Cancel</button>
        <button class="rec-btn-primary" :disabled="drawerSaving" @click="saveRec">
          <span v-html="icon('check',13)"></span>
          {{ drawerSaving ? 'Saving…' : (editMode ? 'Save Changes' : 'Create Recurring Bill') }}
        </button>
      </div>
    </div>

    <!-- ============================================================ VIEW DRAWER -->
    <div v-if="viewOpen" class="rec-overlay" @click.self="viewOpen=false"></div>
    <div class="rec-drawer rec-view-drawer" :class="{open:viewOpen}">
      <template v-if="viewDoc">
        <div class="rec-view-head" :class="viewDoc.status==='Paused'?'paused':viewDoc.status==='Cancelled'?'completed':''">
          <div class="rec-view-head-row">
            <div>
              <div class="rec-view-num">{{ viewDoc.name }}</div>
              <div class="rec-view-sub">Reference Bill · {{ viewDoc.frequency }}</div>
            </div>
            <div style="display:flex;align-items:center;gap:8px">
              <span class="rec-badge rec-badge-lg" :class="statusClass(viewDoc.status)">{{ viewDoc.status||'Active' }}</span>
              <button class="rec-dclose" @click="viewOpen=false"><span v-html="icon('x',16)"></span></button>
            </div>
          </div>
          <div class="rec-view-stats">
            <div>
              <div class="vh-lbl">Start Date</div>
              <div class="vh-val">{{ fmtDate(viewDoc.start_date)||'—' }}</div>
            </div>
            <div>
              <div class="vh-lbl">Next Run</div>
              <div class="vh-val" :class="isDue(viewDoc)?'text-accent':''">{{ fmtDate(viewDoc.next_schedule_date)||'—' }}</div>
            </div>
            <div>
              <div class="vh-lbl">End Date</div>
              <div class="vh-val">{{ fmtDate(viewDoc.end_date)||'No end' }}</div>
            </div>
          </div>
        </div>

        <!-- action bar -->
        <div class="rec-view-actbar">
          <button class="rec-va-btn" @click="openEdit(viewDoc)" :disabled="(viewDoc.ui_status||viewDoc.status)==='Cancelled'"><span v-html="icon('edit',13)"></span> Edit</button>
          <button class="rec-va-btn" @click="runNow(viewDoc)" :disabled="(viewDoc.ui_status||viewDoc.status||'Active')!=='Active' || actionLoading"><span v-html="icon('play',13)"></span> Run Now</button>
          <button v-if="(viewDoc.ui_status||viewDoc.status||'Active')==='Active'" class="rec-va-btn" @click="actionOn(viewDoc,'pause')" :disabled="actionLoading"><span v-html="icon('pause',13)"></span> Pause</button>
          <button v-else-if="(viewDoc.ui_status||viewDoc.status)==='Paused'" class="rec-va-btn" @click="actionOn(viewDoc,'resume')" :disabled="actionLoading"><span v-html="icon('play',13)"></span> Resume</button>
          <button class="rec-va-btn rec-va-warn" @click="actionOn(viewDoc,'cancel')" :disabled="actionLoading || (viewDoc.ui_status||viewDoc.status)==='Cancelled'"><span v-html="icon('x',13)"></span> Cancel</button>
          <button class="rec-va-btn rec-va-danger" @click="actionOn(viewDoc,'delete')" :disabled="actionLoading"><span v-html="icon('trash',13)"></span> Delete</button>
        </div>

        <!-- timeline -->
        <div class="rec-timeline">
          <div class="rec-tl-step" :class="{done:true}">
            <div class="rec-tl-dot"></div>
            <div class="rec-tl-lbl">Created<br/><span class="rec-tl-sub">{{ fmtDate(viewDoc.creation) }}</span></div>
          </div>
          <div class="rec-tl-line" :class="{done:(viewDoc.ui_status||viewDoc.status)!=='Paused'}"></div>
          <div class="rec-tl-step" :class="{done:(viewDoc.ui_status||viewDoc.status||'Active')==='Active' || viewDoc.runs_count>0, current:(viewDoc.ui_status||viewDoc.status||'Active')==='Active'}">
            <div class="rec-tl-dot"></div>
            <div class="rec-tl-lbl">{{ (viewDoc.ui_status||viewDoc.status)==='Paused'?'Paused':'Active' }}<br/><span class="rec-tl-sub">{{ fmtDate(viewDoc.start_date) }}</span></div>
          </div>
          <div class="rec-tl-line" :class="{done:viewDoc.runs_count>0}"></div>
          <div class="rec-tl-step" :class="{done:viewDoc.runs_count>0}">
            <div class="rec-tl-dot"></div>
            <div class="rec-tl-lbl">Last Run<br/><span class="rec-tl-sub">{{ viewDoc.runs&&viewDoc.runs.length?fmtDate(viewDoc.runs[0].creation):'—' }}</span></div>
          </div>
          <div class="rec-tl-line" :class="{done:(viewDoc.ui_status||viewDoc.status)==='Cancelled'}"></div>
          <div class="rec-tl-step" :class="{done:(viewDoc.ui_status||viewDoc.status)==='Cancelled' || (viewDoc.ui_status||viewDoc.status)==='Completed'}">
            <div class="rec-tl-dot"></div>
            <div class="rec-tl-lbl">{{ viewDoc.end_date?'Ends':'Open-ended' }}<br/><span class="rec-tl-sub">{{ fmtDate(viewDoc.end_date)||'No end' }}</span></div>
          </div>
        </div>

        <!-- tabs -->
        <div class="rec-view-tabs">
          <button v-for="t in viewTabs" :key="t.key" class="rec-vt-btn" :class="{active:viewTab===t.key}" @click="viewTab=t.key">
            {{ t.label }}<span v-if="t.count!=null" class="rec-vt-count">{{ t.count }}</span>
          </button>
        </div>

        <div class="rec-dbody">
          <!-- Details tab -->
          <div v-if="viewTab==='details'">
            <div class="rec-section">
              <div class="rec-section-hdr"><span v-html="icon('folder',13)"></span><span>Details</span></div>
              <div class="rec-meta-grid">
                <div><div class="rec-meta-lbl">Reference Bill</div><div class="mono-sm">{{ viewDoc.reference_document||'—' }}</div></div>
                <div><div class="rec-meta-lbl">Frequency</div><div>{{ viewDoc.frequency }}</div></div>
                <div><div class="rec-meta-lbl">Start Date</div><div class="mono-sm">{{ fmtDate(viewDoc.start_date) }}</div></div>
                <div><div class="rec-meta-lbl">End Date</div><div class="mono-sm">{{ fmtDate(viewDoc.end_date)||'No end' }}</div></div>
                <div><div class="rec-meta-lbl">Next Run</div><div class="mono-sm" :class="isDue(viewDoc)?'text-accent':''">{{ fmtDate(viewDoc.next_schedule_date)||'—' }}</div></div>
                <div><div class="rec-meta-lbl">Submit on Creation</div><div>{{ viewDoc.submit_on_creation?'Yes':'No (Draft)' }}</div></div>
              </div>
            </div>
            <div v-if="viewDoc.recipients" class="rec-section" style="margin-top:12px">
              <div class="rec-section-hdr"><span v-html="icon('mail',13)"></span><span>Notification</span></div>
              <div class="rec-meta-grid">
                <div style="grid-column:1/-1"><div class="rec-meta-lbl">Recipients</div><div class="mono-sm" style="word-break:break-all">{{ viewDoc.recipients }}</div></div>
                <div v-if="viewDoc.subject" style="grid-column:1/-1"><div class="rec-meta-lbl">Subject</div><div>{{ viewDoc.subject }}</div></div>
                <div v-if="viewDoc.message" style="grid-column:1/-1"><div class="rec-meta-lbl">Message</div><div style="font-size:13px;white-space:pre-wrap">{{ viewDoc.message }}</div></div>
              </div>
            </div>
          </div>

          <!-- Generated tab -->
          <div v-else-if="viewTab==='generated'">
            <div v-if="!viewDoc.runs||!viewDoc.runs.length" class="rec-tab-empty">No documents generated yet.</div>
            <table v-else class="rec-table rec-table-inner">
              <thead><tr><th>Document</th><th>Created</th><th>Status</th></tr></thead>
              <tbody>
                <tr v-for="d in viewDoc.runs" :key="d.name">
                  <td class="rec-num">{{ d.name }}</td>
                  <td class="text-muted mono-sm">{{ fmtDate(d.creation) }}</td>
                  <td><span class="rec-badge" :class="d.docstatus===1?'badge-green':d.docstatus===2?'badge-red':'badge-grey'">{{ d.docstatus===1?'Submitted':d.docstatus===2?'Cancelled':'Draft' }}</span></td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- Upcoming tab -->
          <div v-else-if="viewTab==='upcoming'">
            <div v-if="!viewDoc.upcoming||!viewDoc.upcoming.length" class="rec-tab-empty">No upcoming runs scheduled.</div>
            <ol v-else class="rec-upcoming-list">
              <li v-for="(u,i) in viewDoc.upcoming" :key="i">
                <span class="rec-upcoming-idx">#{{ i+1 }}</span>
                <span class="mono-sm">{{ fmtDate(u.date) }}</span>
                <span class="text-muted">— {{ u.frequency }}</span>
              </li>
            </ol>
          </div>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from "vue";
import { apiList, apiSave, apiLinkValues, apiGET, apiPOST } from "../api/client.js";
import { useToast } from "../composables/useToast.js";
import { icon } from "../utils/icons.js";
import { fmtDate } from "../utils/format.js";
import SearchableSelect from "../components/SearchableSelect.vue";
import SummaryStrip from "../components/SummaryStrip.vue";
import Pagination from "../components/Pagination.vue";
import { usePagination } from "../composables/usePagination.js";

const { toast } = useToast();
function confirm({ title, body, okLabel }) {
  return Promise.resolve(window.confirm(`${title}\n\n${body || ""}`));
}
const activeTab = ref("all");
const tabs = [
  { key: "all", label: "All" },
  { key: "Active", label: "Active" },
  { key: "Paused", label: "Paused" },
  { key: "Cancelled", label: "Cancelled" },
];
const list = ref([]), loading = ref(false), search = ref("");
const selected = ref([]);
const drawerOpen = ref(false), drawerSaving = ref(false), editMode = ref(false);
const recipientError = ref("");
const viewOpen = ref(false), viewDoc = ref(null), viewTab = ref("details");
const actionLoading = ref(false);
const refDocs = ref([]);
const sortCol = ref("next_schedule_date"), sortDir = ref("asc");
const form = reactive({
  _name: "",
  reference_document: "",
  frequency: "Monthly",
  start_date: new Date().toISOString().slice(0, 10),
  end_date: "",
  submit_on_creation: 1,
  _notify: false,
  recipients: "",
  subject: "",
  message: "",
});

async function load() {
  loading.value = true;
  try {
    list.value = await apiList("Auto Repeat", {
      fields: ["name","reference_doctype","reference_document","frequency","start_date","end_date","next_schedule_date","status"],
      filters: [["reference_doctype","=","Purchase Invoice"]],
      limit: 500, order: "next_schedule_date asc",
    }) || [];
  } catch (e) {
    console.warn("Auto Repeat load failed:", e.message);
    list.value = [];
  } finally { loading.value = false; }
}

const today = new Date().toISOString().slice(0, 10);
function isDue(r) { return r.next_schedule_date && r.next_schedule_date <= today && (r.status||"Active") === "Active"; }
function statusClass(s) { if (s==="Cancelled") return "badge-grey"; if (s==="Paused") return "badge-orange"; return "badge-green"; }

const counts = computed(() => ({
  active:    list.value.filter(r => (r.status||"Active") === "Active").length,
  paused:    list.value.filter(r => r.status === "Paused").length,
  cancelled: list.value.filter(r => r.status === "Cancelled").length,
}));

const filtered = computed(() => {
  let r = list.value;
  if (activeTab.value !== "all") r = r.filter(x => (x.status||"Active") === activeTab.value);
  if (search.value.trim()) {
    const q = search.value.toLowerCase();
    r = r.filter(x => (x.name||"").toLowerCase().includes(q) || (x.reference_document||"").toLowerCase().includes(q));
  }
  return r;
});

const sorted = computed(() => {
  const col = sortCol.value;
  return [...filtered.value].sort((a, b) => {
    const c = String(a[col]??"").localeCompare(String(b[col]??""));
    return sortDir.value === "asc" ? c : -c;
  });
});
const { page, pageSize, paged } = usePagination(sorted, { storageKey: "recurring-bills" });

function sort(col) { if (sortCol.value===col) sortDir.value=sortDir.value==="asc"?"desc":"asc"; else { sortCol.value=col; sortDir.value="asc"; } }
function sortArrow(col) { if (sortCol.value!==col) return '<span style="color:#d1d5db">⇅</span>'; return sortDir.value==="asc"?"↑":"↓"; }

const viewTabs = computed(() => [
  { key: "details", label: "Details" },
  { key: "generated", label: "Generated", count: viewDoc.value?.runs_count ?? 0 },
  { key: "upcoming", label: "Upcoming", count: viewDoc.value?.upcoming?.length ?? 0 },
]);
const allSelected = computed(() => sorted.value.length > 0 && sorted.value.every(r => selected.value.includes(r.name)));
function toggleAll() { selected.value = allSelected.value ? [] : sorted.value.map(r => r.name); }
function toggleOne(n) { selected.value = selected.value.includes(n) ? selected.value.filter(x => x !== n) : [...selected.value, n]; }

function openNew() {
  editMode.value = false;
  Object.assign(form, {
    _name: "",
    reference_document: "",
    frequency: "Monthly",
    start_date: new Date().toISOString().slice(0, 10),
    end_date: "",
    submit_on_creation: 1,
    _notify: false,
    recipients: "",
    subject: "",
    message: "",
  });
  refDocs.value = [];
  drawerOpen.value = true;
  fetchRefDocs();
}
async function openView(r) {
  if (!r?.name) return;
  viewOpen.value = true;
  viewTab.value = "details";
  viewDoc.value = { ...r, runs: r.runs || [], upcoming: r.upcoming || [], runs_count: r.runs_count || 0 };
  try {
    const detail = await apiGET("zoho_books_clone.api.recurring.get_subscription", { name: r.name });
    const d = (detail && typeof detail === "object") ? detail : {};
    viewDoc.value = {
      ...viewDoc.value, ...d,
      runs: Array.isArray(d.runs) ? d.runs : (viewDoc.value.runs || []),
      upcoming: Array.isArray(d.upcoming) ? d.upcoming : (viewDoc.value.upcoming || []),
      runs_count: d.runs_count != null ? d.runs_count : (Array.isArray(d.runs) ? d.runs.length : (viewDoc.value.runs_count || 0)),
    };
  } catch (e) { toast.error(e.message || "Failed to load detail"); }
}

async function openEdit(doc) {
  if (!doc?.name) return;
  editMode.value = true;
  viewOpen.value = false;
  // Populate from what we have immediately so drawer opens fast
  Object.assign(form, {
    _name: doc.name,
    reference_document: doc.reference_document || "",
    frequency: doc.frequency || "Monthly",
    start_date: doc.start_date || "",
    end_date: doc.end_date || "",
    submit_on_creation: doc.submit_on_creation ? 1 : 0,
    _notify: !!(doc.recipients),
    recipients: doc.recipients || "",
    subject: doc.subject || "",
    message: doc.message || "",
  });
  refDocs.value = doc.reference_document ? [{ label: doc.reference_document, value: doc.reference_document }] : [];
  drawerOpen.value = true;
  // Fetch full detail to fill recipients/subject/message/submit_on_creation
  try {
    const detail = await apiGET("zoho_books_clone.api.recurring.get_subscription", { name: doc.name });
    const d = (detail && typeof detail === "object") ? detail : {};
    Object.assign(form, {
      frequency: d.frequency || form.frequency,
      end_date: d.end_date || "",
      submit_on_creation: d.submit_on_creation ? 1 : 0,
      _notify: !!(d.recipients || d.notify_by_email),
      recipients: d.recipients || "",
      subject: d.subject || "",
      message: d.message || "",
    });
  } catch { /* keep optimistic values */ }
}

function onOverlayClose() {
  if (drawerSaving.value) return;
  drawerOpen.value = false;
}

async function quickAction(r, action) {
  const messages = {
    pause:  { title: `Pause ${r.name}?`,  body: "It will stop generating documents until resumed.", okLabel: "Pause" },
    resume: { title: `Resume ${r.name}?`, body: "It will start generating documents on schedule.", okLabel: "Resume" },
    cancel: { title: `Cancel ${r.name}?`, body: "Subscription will be ended permanently.", okLabel: "Cancel Sub" },
    delete: { title: `Delete ${r.name}?`, body: "This cannot be undone.", okLabel: "Delete" },
  };
  if (!(await confirm(messages[action]))) return;
  await runLifecycle(r.name, action);
}

async function actionOn(doc, action) {
  if (!doc?.name) return;
  await quickAction(doc, action);
  if (action === "delete") { viewOpen.value = false; }
  else if (viewOpen.value) { await openView({ name: doc.name }); }
}

async function runLifecycle(name, action) {
  actionLoading.value = true;
  try {
    const res = await apiPOST(`zoho_books_clone.api.recurring.${action}_subscription`, { name });
    toast.success(res?.message?.message || res?.message || `${name} ${action}d`);
    await load();
  } catch (e) { toast.error(e.message || `Failed to ${action}`); }
  finally { actionLoading.value = false; }
}

async function runNow(doc) {
  if (!doc?.name) return;
  if (!(await confirm({ title: `Run ${doc.name} now?`, body: "A new document will be generated immediately, ignoring the schedule.", okLabel: "Run Now" }))) return;
  actionLoading.value = true;
  try {
    const res = await apiPOST("zoho_books_clone.api.recurring.run_subscription_now", { name: doc.name });
    const gen = res?.message?.generated || res?.generated;
    toast.success(gen ? `Generated ${gen}` : "Document generated");
    await load();
    await openView({ name: doc.name });
  } catch (e) { toast.error(e.message || "Failed to run subscription"); }
  finally { actionLoading.value = false; }
}

async function fetchRefDocs(q = "") {
  try {
    const r = await apiLinkValues("Purchase Invoice", q, [["docstatus","in",[0,1]],["is_return","=",0]]);
    refDocs.value = r.map(x => ({ label: x.name, value: x.name }));
  } catch { refDocs.value = []; }
}

function validateRecipients() {
  if (!form._notify || !form.recipients.trim()) { recipientError.value = ""; return true; }
  const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  const bad = form.recipients.split(",").map(s => s.trim()).filter(s => s && !emailRe.test(s));
  if (bad.length) { recipientError.value = `Invalid email${bad.length > 1 ? "s" : ""}: ${bad.join(", ")}`; return false; }
  recipientError.value = ""; return true;
}

async function saveRec() {
  if (!form.reference_document) return toast.error("Reference bill is required");
  if (!form.start_date) return toast.error("Start date is required");
  if (form.end_date && form.end_date < form.start_date) return toast.error("End date must be after start date");
  if (!validateRecipients()) return;
  drawerSaving.value = true;
  try {
    if (editMode.value) {
      await apiPOST("zoho_books_clone.api.recurring.update_subscription", {
        name: form._name,
        frequency: form.frequency,
        end_date: form.end_date || "",
        submit_on_creation: form.submit_on_creation,
        recipients: form.recipients,
        subject: form.subject,
        message: form.message,
      });
      toast.success(`${form._name} updated`);
    } else {
      const doc = {
        doctype: "Auto Repeat",
        reference_doctype: "Purchase Invoice",
        reference_document: form.reference_document,
        frequency: form.frequency,
        start_date: form.start_date,
        end_date: form.end_date || null,
        submit_on_creation: form.submit_on_creation,
        recipients: form._notify ? (form.recipients || "") : "",
        subject: form._notify ? (form.subject || "") : "",
        message: form._notify ? (form.message || "") : "",
      };
      const saved = await apiSave(doc);
      toast.success(`Recurring bill ${saved?.name || ""} created`);
    }
    drawerOpen.value = false;
    if (editMode.value && form._name) await openView({ name: form._name });
    await load();
  } catch (e) { toast.error(e.message || "Failed to save recurring bill"); }
  finally { drawerSaving.value = false; }
}

onMounted(load);
</script>

<style scoped>
/* ── Page & Toolbar ── */
.rec-page{display:flex;flex-direction:column;gap:16px;padding:24px;}
.rec-actions{display:flex;align-items:center;gap:10px;flex-wrap:wrap;}
.rec-search-wrap{display:flex;align-items:center;gap:8px;background:#ffffff;border-radius:8px;padding:6px 12px;min-width:220px;border:1px solid #e5e7eb;}
.rec-search-input{border:none;background:transparent;outline:none;font:inherit;color:#111827;width:100%;font-size:13px;}
.rec-pills{display:flex;gap:6px;}
.rec-pill{padding:6px 14px;border-radius:20px;font-size:12.5px;font-weight:600;border:1px solid #e5e7eb;background:#fff;color:#6b7280;cursor:pointer;font-family:inherit;}
.rec-pill.active{background:#eff6ff;border-color:#2563eb;color:#2563eb;}
.rec-btn-primary{display:inline-flex;align-items:center;gap:6px;background:#2563eb;color:#fff;border:none;border-radius:8px;padding:8px 14px;font-size:13px;font-weight:600;cursor:pointer;font-family:inherit;}
.rec-btn-primary:hover{background:#1d4ed8;}
.rec-btn-primary:disabled{opacity:.5;cursor:not-allowed;}
.rec-btn-ghost{display:inline-flex;align-items:center;gap:6px;background:#ffffff;border:1px solid #e5e7eb;border-radius:8px;padding:8px 12px;font-size:13px;color:#374151;cursor:pointer;font-family:inherit;}
.rec-btn-ghost:hover{background:#f9fafb;}
.rec-btn-ghost:disabled{opacity:.5;cursor:not-allowed;}

/* ── Table ── */
.green{color:#16a34a!important;}.orange{color:#ea580c!important;}.red{color:#dc2626!important;}
.rec-card{background:#fff;border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;}
.rec-table{width:100%;border-collapse:collapse;font-size:13px;}
.rec-table th{background:#f9fafb;border-bottom:1px solid #e5e7eb;padding:10px 12px;font-size:11.5px;font-weight:600;color:#374151;text-align:left;white-space:nowrap;text-transform:uppercase;}
.rec-table th.sortable{cursor:pointer;user-select:none;}.rec-table th.sortable:hover{color:#2563eb;}
.rec-row td{padding:10px 12px;border-bottom:1px solid #f3f4f6;vertical-align:middle;cursor:pointer;}
.rec-row:last-child td{border-bottom:none;}.rec-row:hover td{background:#f9fafb;}
.rec-num{font-size:13px;color:#2563eb;font-weight:600;}
.rec-ref{font-size:13px;color:#374151;}
.mono-sm{font-size:13px;}.text-muted{color:#6b7280;}.text-accent{color:#2563eb;font-weight:600;}
.rec-badge{display:inline-flex;align-items:center;padding:2px 8px;border-radius:10px;font-size:11.5px;font-weight:600;}
.rec-badge-lg{padding:4px 10px;font-size:12.5px;}
.badge-green{background:#dcfce7;color:#16a34a;}.badge-orange{background:#fef3c7;color:#ea580c;}.badge-grey{background:#e5e7eb;color:#6b7280;}
.rec-act-btn{background:transparent;border:1px solid #e5e7eb;border-radius:6px;width:26px;height:26px;display:inline-flex;align-items:center;justify-content:center;cursor:pointer;color:#6b7280;}
.rec-act-btn:hover{background:#e5e7eb;color:#2563eb;}
.rec-empty{text-align:center;color:#9ca3af;padding:48px!important;cursor:default!important;}
.rec-empty-wrap{display:flex;flex-direction:column;align-items:center;gap:6px;color:#9ca3af;}
.rec-empty-icon{color:#cbd5e1;margin-bottom:6px;}
.rec-empty-title{font-size:15px;font-weight:600;color:#374151;}
.rec-empty-sub{font-size:12.5px;max-width:380px;text-align:center;}
.rec-shimmer{height:13px;background:linear-gradient(90deg,#f3f4f6 25%,#e5e7eb 50%,#f3f4f6 75%);border-radius:4px;animation:shimmer 1.2s infinite;background-size:200% 100%;}
@keyframes shimmer{0%{background-position:200% 0}100%{background-position:-200% 0}}

/* ── Overlay & Drawer ── */
.rec-overlay{position:fixed;inset:0;background:rgba(15,23,42,.28);backdrop-filter:blur(2px);z-index:40;}
.rec-drawer{position:fixed;top:0;right:-560px;bottom:0;width:560px;background:#fff;border-left:1px solid #e5e7eb;box-shadow:-12px 0 32px rgba(15,23,42,.12);z-index:50;display:flex;flex-direction:column;transition:right .24s cubic-bezier(.32,.72,0,1);}
.rec-drawer.open{right:0;}
.rec-view-drawer{width:520px;right:-520px;}.rec-view-drawer.open{right:0;}

/* ── Drawer Header ── */
.rec-dheader{display:flex;align-items:flex-start;justify-content:space-between;padding:18px 20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.rec-dheader-left{display:flex;align-items:flex-start;gap:12px;}
.rec-dheader-ico{width:38px;height:38px;border-radius:10px;background:#fff;border:1px solid rgba(37,99,235,.18);display:inline-flex;align-items:center;justify-content:center;color:#2563eb;box-shadow:0 1px 3px rgba(15,23,42,.06);flex-shrink:0;}
.rec-dheader-title{font-size:15px;font-weight:700;color:#111827;letter-spacing:-0.01em;}
.rec-dheader-sub{font-size:12px;color:#475569;margin-top:3px;font-weight:500;}
.rec-dclose{background:rgba(255,255,255,.6);border:none;cursor:pointer;color:#475569;display:inline-flex;align-items:center;justify-content:center;width:32px;height:32px;border-radius:8px;transition:background .15s;}
.rec-dclose:hover{background:#fff;color:#111827;}

/* ── Drawer Body ── */
.rec-dbody{flex:1;overflow-y:auto;padding:18px 20px;display:flex;flex-direction:column;gap:18px;background:#f8fafc;}

/* ── Sections ── */
.rec-section{background:#fff;border:1px solid #e5e7eb;border-radius:10px;padding:14px 16px;display:flex;flex-direction:column;gap:12px;box-shadow:0 1px 2px rgba(15,23,42,.03);}
.rec-section-hdr{display:flex;align-items:center;gap:8px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:.04em;color:#0f172a;}
.rec-section-hdr svg{color:#2563eb;}
.rec-section-empty{font-size:12.5px;color:#6b7280;font-style:italic;line-height:1.5;}
.rec-field-help{font-size:11.5px;color:#9ca3af;margin-top:4px;}

/* ── Toggle ── */
.rec-toggle{position:relative;margin-left:auto;width:34px;height:18px;display:inline-block;cursor:pointer;}
.rec-toggle input{opacity:0;width:0;height:0;}
.rec-toggle-slider{position:absolute;inset:0;background:#cbd5e1;border-radius:18px;transition:background .18s;}
.rec-toggle-slider::before{content:"";position:absolute;width:14px;height:14px;left:2px;top:2px;background:#fff;border-radius:50%;transition:transform .18s;box-shadow:0 1px 3px rgba(0,0,0,.15);}
.rec-toggle input:checked + .rec-toggle-slider{background:#2563eb;}
.rec-toggle input:checked + .rec-toggle-slider::before{transform:translateX(16px);}

/* ── Fields ── */
.rec-fields-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;}
.rec-field{display:flex;flex-direction:column;gap:4px;}
.rec-label{font-size:12px;font-weight:600;color:#374151;}
.rec-hint{font-weight:400;color:#9ca3af;font-size:11px;}
.req{color:#dc2626;}
.rec-input,.rec-select{border:1px solid #e2e8f0;border-radius:8px;padding:8px 12px;font:inherit;font-size:13px;outline:none;background:#fff;color:#0f172a;transition:border-color .15s, box-shadow .15s;}
.rec-input:hover:not(:disabled),.rec-select:hover:not(:disabled){border-color:#cbd5e1;}
.rec-input:focus,.rec-select:focus{border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.12);}
.rec-input:disabled,.rec-select:disabled{background:#f1f5f9;color:#94a3b8;cursor:not-allowed;border-color:#e2e8f0;}
textarea.rec-input{resize:vertical;min-height:72px;}

/* ── Drawer Footer ── */
.rec-dfooter{display:flex;align-items:center;justify-content:flex-end;gap:8px;padding:14px 20px;border-top:1px solid #e5e7eb;flex-shrink:0;background:#fff;}

/* ── Selected row ── */
.rec-row.selected td{background:#eff6ff;}
.rec-act-danger:hover{color:#dc2626;background:#fef2f2;border-color:#fecaca;}

/* ── Edit mode drawer header ── */
.rec-dheader.edit{background:linear-gradient(135deg,#fef3c7 0%,#fde68a 100%);}
.rec-dheader-ico.edit{color:#ca8a04;border-color:rgba(202,138,4,.25);}

/* ── View action bar ── */
.rec-view-actbar{display:flex;flex-wrap:wrap;gap:6px;padding:10px 20px;border-bottom:1px solid #e5e7eb;background:#fff;flex-shrink:0;}
.rec-va-btn{display:inline-flex;align-items:center;gap:5px;border:1px solid #e5e7eb;background:#fff;color:#374151;border-radius:7px;padding:6px 11px;font-size:12.5px;font-weight:600;cursor:pointer;font-family:inherit;}
.rec-va-btn:hover:not(:disabled){background:#f9fafb;border-color:#cbd5e1;}
.rec-va-btn:disabled{opacity:.45;cursor:not-allowed;}
.rec-va-warn{color:#ea580c;border-color:#fed7aa;}.rec-va-warn:hover:not(:disabled){background:#fff7ed;}
.rec-va-danger{color:#dc2626;border-color:#fecaca;}.rec-va-danger:hover:not(:disabled){background:#fef2f2;}

/* ── Timeline ── */
.rec-timeline{display:flex;align-items:center;padding:14px 20px;background:#fff;border-bottom:1px solid #e5e7eb;gap:0;flex-shrink:0;}
.rec-tl-step{display:flex;flex-direction:column;align-items:center;flex-shrink:0;min-width:80px;}
.rec-tl-dot{width:12px;height:12px;border-radius:50%;background:#e5e7eb;border:2px solid #fff;box-shadow:0 0 0 2px #e5e7eb;}
.rec-tl-step.done .rec-tl-dot{background:#16a34a;box-shadow:0 0 0 2px #16a34a;}
.rec-tl-step.current .rec-tl-dot{background:#2563eb;box-shadow:0 0 0 3px #bfdbfe;}
.rec-tl-lbl{font-size:11px;color:#6b7280;text-align:center;margin-top:6px;font-weight:600;line-height:1.3;}
.rec-tl-sub{font-weight:400;color:#9ca3af;font-size:10.5px;}
.rec-tl-line{flex:1;height:2px;background:#e5e7eb;min-width:20px;}
.rec-tl-line.done{background:#16a34a;}
.rec-tl-line.danger{background:#dc2626;}

/* ── View tabs ── */
.rec-view-tabs{display:flex;border-bottom:1px solid #e5e7eb;padding:0 12px;background:#fff;flex-shrink:0;}
.rec-vt-btn{background:transparent;border:none;padding:10px 14px;font-size:13px;font-weight:600;color:#6b7280;cursor:pointer;border-bottom:2px solid transparent;display:inline-flex;align-items:center;gap:6px;font-family:inherit;}
.rec-vt-btn.active{color:#2563eb;border-bottom-color:#2563eb;}
.rec-vt-count{background:#e5e7eb;color:#374151;padding:1px 7px;border-radius:10px;font-size:11px;font-weight:700;}
.rec-vt-btn.active .rec-vt-count{background:#dbeafe;color:#1d4ed8;}

/* ── Generated / Upcoming tabs ── */
.badge-red{background:#fee2e2;color:#dc2626;}
.rec-table-inner{font-size:12.5px;}
.rec-table-inner th{background:#fafafa;}
.rec-tab-empty{padding:24px;text-align:center;color:#9ca3af;font-size:13px;}
.rec-upcoming-list{list-style:none;padding:0;margin:0;display:flex;flex-direction:column;gap:8px;}
.rec-upcoming-list li{background:#f9fafb;border:1px solid #f3f4f6;border-radius:8px;padding:10px 14px;display:flex;align-items:center;gap:12px;font-size:13px;}
.rec-upcoming-idx{background:#dbeafe;color:#1d4ed8;font-weight:700;padding:2px 8px;border-radius:8px;font-size:11.5px;}

/* ── View Drawer Header ── */
.rec-view-head{padding:20px;border-bottom:1px solid #e5e7eb;flex-shrink:0;background:linear-gradient(135deg,#eff6ff 0%,#dbeafe 100%);}
.rec-view-head.paused{background:linear-gradient(135deg,#fff7ed 0%,#fed7aa 100%);}
.rec-view-head.completed{background:linear-gradient(135deg,#f3f4f6 0%,#e5e7eb 100%);}
.rec-view-head-row{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;}
.rec-view-num{font-size:18px;font-weight:700;color:#111827;}
.rec-view-sub{font-size:12.5px;color:#475569;margin-top:2px;}
.rec-view-stats{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-top:16px;}
.rec-view-stats > div{background:rgba(255,255,255,.55);border-radius:8px;padding:8px 10px;}
.vh-lbl{font-size:10.5px;color:#475569;text-transform:uppercase;letter-spacing:.05em;font-weight:600;}
.vh-val{font-size:15px;font-weight:700;color:#0f172a;margin-top:2px;}
.rec-meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:14px;}
.rec-meta-lbl{font-size:11px;color:#9ca3af;text-transform:uppercase;letter-spacing:.05em;margin-bottom:2px;font-weight:600;}
</style>