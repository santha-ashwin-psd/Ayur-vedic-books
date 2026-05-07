"""
System-level SMTP — used ONLY for pre-auth or cross-tenant emails:
  - signup verification OTP
  - password reset OTP
  - new-user invite (sent before the invitee has any company SMTP)

Reads credentials from common_site_config.json (mail_server / mail_login / mail_password / mail_port / use_tls).
Bypasses frappe.sendmail() and the Email Queue so it never accidentally
routes through a per-company Email Account.
"""
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr

import frappe


def _conf() -> dict:
    """Pull the system-level SMTP config from common_site_config.json."""
    c = frappe.conf
    return {
        "server":   c.get("mail_server"),
        "port":     int(c.get("mail_port") or 587),
        "login":    c.get("mail_login"),
        "password": c.get("mail_password"),
        "use_tls":  bool(c.get("use_tls", 1)),
        "use_ssl":  bool(c.get("use_ssl", 0)),
        "from_email": c.get("auto_email_id") or c.get("mail_login"),
        "from_name":  c.get("email_sender_name") or "Books",
    }


def is_configured() -> bool:
    cfg = _conf()
    return bool(cfg["server"] and cfg["login"] and cfg["password"])


def send_system_email(to: str, subject: str, html: str, text_fallback: str = "") -> bool:
    """Send a single email via the system SMTP. Returns True on success.
    Never raises — logs errors and returns False so callers can degrade gracefully."""
    cfg = _conf()
    if not is_configured():
        frappe.log_error(
            "System SMTP is not configured in common_site_config.json "
            "(mail_server / mail_login / mail_password). OTP emails will not be sent.",
            "Books System SMTP",
        )
        return False

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = formataddr((cfg["from_name"], cfg["from_email"]))
    msg["To"] = to

    if text_fallback:
        msg.attach(MIMEText(text_fallback, "plain", "utf-8"))
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        if cfg["use_ssl"]:
            ctx = ssl.create_default_context()
            with smtplib.SMTP_SSL(cfg["server"], cfg["port"], context=ctx, timeout=15) as server:
                server.login(cfg["login"], cfg["password"])
                server.sendmail(cfg["from_email"], [to], msg.as_string())
        else:
            with smtplib.SMTP(cfg["server"], cfg["port"], timeout=15) as server:
                server.ehlo()
                if cfg["use_tls"]:
                    server.starttls(context=ssl.create_default_context())
                    server.ehlo()
                server.login(cfg["login"], cfg["password"])
                server.sendmail(cfg["from_email"], [to], msg.as_string())
        return True
    except Exception as exc:
        frappe.log_error(f"System SMTP send failed for {to}: {exc}", "Books System SMTP")
        return False
