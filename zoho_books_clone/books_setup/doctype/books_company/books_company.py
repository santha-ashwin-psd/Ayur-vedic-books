from __future__ import annotations

import frappe
from frappe import _
from frappe.model.document import Document


class BooksCompany(Document):
    def validate(self):
        self.company_name = (self.company_name or "").strip()
        if not self.company_name:
            frappe.throw(_("Company Name is required."))

        if not self.company_abbr:
            self.company_abbr = self._derive_abbr(self.company_name)

        if self.smtp_enabled:
            for f in ("smtp_server", "smtp_login", "smtp_password"):
                if not self.get(f):
                    frappe.throw(_("SMTP {0} is required when company SMTP is enabled.").format(f))
            if not self.smtp_from_email:
                self.smtp_from_email = self.smtp_login

    @staticmethod
    def _derive_abbr(name: str) -> str:
        parts = [p for p in name.replace("&", " ").split() if p]
        if not parts:
            return ""
        if len(parts) == 1:
            return parts[0][:3].upper()
        return "".join(p[0] for p in parts[:4]).upper()

    def get_smtp_config(self) -> dict | None:
        """Return decrypted SMTP config dict, or None if not enabled/complete."""
        if not self.smtp_enabled:
            return None
        try:
            password = self.get_password("smtp_password", raise_exception=False)
        except Exception:
            password = None
        if not (self.smtp_server and self.smtp_login and password):
            return None
        return {
            "server": self.smtp_server,
            "port": int(self.smtp_port or 587),
            "login": self.smtp_login,
            "password": password,
            "use_tls": bool(self.smtp_use_tls),
            "use_ssl": bool(self.smtp_use_ssl),
            "from_email": self.smtp_from_email or self.smtp_login,
            "from_name": self.smtp_from_name or self.company_name,
        }
