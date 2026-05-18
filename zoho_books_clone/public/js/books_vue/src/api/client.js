// Frappe API client. Ported from public/books.js:67-271 with the same
// function names + signatures so module ports remain mechanical.

function _parseResponse(json, status) {
  if (status === 401) {
    const dest = window.location.pathname + window.location.hash;
    window.location.href = "/login?redirect-to=" + encodeURIComponent(dest || "/books");
    throw new Error("Session expired");
  }
  if (
    status === 403 && json &&
    (json.exc_type === "CSRFTokenError" || (json.exc || "").includes("CSRFToken"))
  ) {
    fetch("/api/method/zoho_books_clone.api.session.get_books_session", {
      method: "GET", credentials: "same-origin",
    })
      .then(r => r.json())
      .then(d => { if (d.message?.csrf_token) window.frappe.csrf_token = d.message.csrf_token; })
      .catch(() => {});
  }
  if (json.exc || json.exc_type) {
    const excStr = (json.exc || "").replace(/\\n/g, "\n").replace(/\\"/g, '"');
    const match = excStr.match(/frappe\.exceptions\.\w+:\s*([^\n]+)/);
    if (match && match[1].trim()) {
      throw new Error(match[1].trim());
    }
    if (json._server_messages) {
      try {
        const msgs = JSON.parse(json._server_messages);
        const first = Array.isArray(msgs) ? msgs[0] : msgs;
        const text = (typeof first === "object" ? first.message : String(first) || "")
          .replace(/\\n/g, "").replace(/\\"/g, '"').replace(/^\s+|\s+$/g, "");
        if (text) throw new Error(text);
      } catch (inner) {
        if (inner instanceof Error && !inner.message.startsWith("{")) throw inner;
      }
    }
    throw new Error(json.exc_type || json.message || "Server error " + status);
  }
  return json.message;
}

export async function apiGET(method, params) {
  const qs = new URLSearchParams();
  for (const [k, v] of Object.entries(params || {})) {
    qs.append(k, typeof v === "string" ? v : JSON.stringify(v));
  }
  const r = await fetch("/api/method/" + method + "?" + qs.toString(), {
    method: "GET",
    credentials: "same-origin",
    headers: { Accept: "application/json" },
  });
  let json;
  try { json = await r.json(); }
  catch { throw new Error("Non-JSON response (" + r.status + ")"); }
  return _parseResponse(json, r.status);
}

export async function refreshCsrfToken() {
  const meta = document.querySelector("meta[name='csrf-token']");
  if (meta) {
    const t = meta.getAttribute("content");
    if (t && t !== "None" && t !== "{{ csrf_token }}") {
      if (window.frappe) window.frappe.csrf_token = t;
      return t;
    }
  }
  if (
    window.frappe?.csrf_token &&
    window.frappe.csrf_token !== "None" &&
    window.frappe.csrf_token !== "{{ csrf_token }}"
  ) {
    return window.frappe.csrf_token;
  }
  const ck = document.cookie.split(";").map(c => c.trim()).find(c => c.startsWith("csrf_token="));
  if (ck) {
    const t = decodeURIComponent(ck.split("=").slice(1).join("="));
    if (t && t !== "None") {
      if (window.frappe) window.frappe.csrf_token = t;
      return t;
    }
  }
  try {
    const r = await fetch("/api/method/zoho_books_clone.api.session.get_books_session", {
      method: "GET", credentials: "same-origin",
      headers: { Accept: "application/json" },
    });
    const data = await r.json();
    const token = data?.message?.csrf_token;
    if (token && token !== "None") {
      if (window.frappe) window.frappe.csrf_token = token;
      return token;
    }
  } catch {}
  return "";
}

export async function apiPOST(method, args) {
  const csrfToken = await refreshCsrfToken();
  const body = new URLSearchParams();
  for (const [k, v] of Object.entries(args || {})) {
    body.append(k, typeof v === "string" ? v : JSON.stringify(v));
  }
  if (csrfToken) body.append("csrf_token", csrfToken);

  const r = await fetch("/api/method/" + method, {
    method: "POST",
    credentials: "same-origin",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
      "X-Frappe-CSRF-Token": csrfToken || "",
      "Accept": "application/json",
    },
    body: body.toString(),
  });
  let json;
  try { json = await r.json(); }
  catch { throw new Error("Non-JSON response (" + r.status + ")"); }
  return _parseResponse(json, r.status);
}

export async function apiGet(doctype, name) {
  return await apiGET("zoho_books_clone.api.docs.get_doc", { doctype, name });
}

export async function apiSave(doc) {
  return await apiPOST("zoho_books_clone.api.docs.save_doc", { doc: JSON.stringify(doc) });
}

export async function apiSubmit(doctype, name) {
  return await apiPOST("zoho_books_clone.api.docs.submit_doc", { doctype, name });
}

export async function apiDelete(doctype, name) {
  return await apiPOST("zoho_books_clone.api.docs.delete_doc", { doctype, name });
}

export async function apiCancel(doctype, name) {
  return await apiPOST("zoho_books_clone.api.docs.cancel_doc", { doctype, name });
}

// Doctypes with a native `company` field — filter by the current company.
const _CO_SCOPED = new Set([
  "Sales Invoice", "Purchase Invoice", "Quotation", "Sales Order", "Purchase Order",
  "Payment Entry", "Stock Entry", "Journal Entry", "Account", "Warehouse", "Cost Center",
  "Bank Account", "Expense Claim",
]);

// Master types with no native company field — filtered by `books_company` custom field
// so all members of the same company share the same pool of records.
const _BOOKS_CO_SCOPED = new Set([
  "Customer", "Supplier", "Item", "Contact",
]);

export async function apiList(dt, opts = {}) {
  const filters = [...(opts.filters || [])];
  const co = window.__booksCompany || "";

  if (co && _CO_SCOPED.has(dt)) {
    if (!filters.some(f => Array.isArray(f) && f[0] === "company"))
      filters.push(["company", "=", co]);
  }

  if (co && _BOOKS_CO_SCOPED.has(dt)) {
    if (!filters.some(f => Array.isArray(f) && f[0] === "books_company"))
      filters.push(["books_company", "=", co]);
  }

  return await apiGET("frappe.client.get_list", {
    doctype:           dt,
    fields:            JSON.stringify(opts.fields || ["name"]),
    filters:           JSON.stringify(filters),
    order_by:          opts.order || "modified desc",
    limit_page_length: opts.limit || 50,
  }) || [];
}

export async function apiLinkValues(doctype, txt, filters) {
  const f = filters
    ? [...filters, ["name", "like", "%" + txt + "%"]]
    : [["name", "like", "%" + txt + "%"]];
  const co = window.__booksCompany || "";
  if (co && _BOOKS_CO_SCOPED.has(doctype)) {
    if (!f.some(x => Array.isArray(x) && x[0] === "books_company"))
      f.push(["books_company", "=", co]);
  }
  return await apiGET("frappe.client.get_list", {
    doctype,
    fields:            JSON.stringify(["name"]),
    filters:           JSON.stringify(f),
    limit_page_length: 10,
  }) || [];
}

// Legacy alias kept for any direct api() calls still in ported code.
export async function api(method, args) { return await apiGET(method, args); }

// Resolves the current company. Mirrors books.js:258-271.
export async function resolveCompany() {
  if (window.__booksCompany) return window.__booksCompany;
  try {
    const r = await apiGET("frappe.client.get_value", {
      doctype:   "Books Settings",
      filters:   JSON.stringify({ name: "Books Settings" }),
      fieldname: JSON.stringify(["default_company"]),
    });
    const c = r?.default_company || "";
    window.__booksCompany = c;
    if (window.frappe?.boot?.sysdefaults) window.frappe.boot.sysdefaults.company = c;
    return c;
  } catch { return window.__booksCompany || ""; }
}
