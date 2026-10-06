import smtplib
from abc import ABC, abstractmethod
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from html import escape

from flask import current_app


class EmailService(ABC):
    """Interface every mail backend implements.

    Swapping to a real provider (SES, SendGrid, SMTP) later only means
    adding a new subclass and pointing MAIL_BACKEND at it in config —
    nothing in the auth flow needs to change.
    """

    @abstractmethod
    def send_verification_email(self, to_email: str, full_name: str, raw_token: str) -> None: ...

    @abstractmethod
    def send_password_reset_email(self, to_email: str, full_name: str, raw_token: str) -> None: ...


class ConsoleEmailService(EmailService):
    """Dev-mode backend: logs the email content/links instead of sending them."""

    def send_verification_email(self, to_email: str, full_name: str, raw_token: str) -> None:
        link = f"{current_app.config['FRONTEND_BASE_URL']}/verify-email?token={raw_token}"
        current_app.logger.info(
            "[email:verification] to=%s name=%s link=%s", to_email, full_name, link
        )

    def send_password_reset_email(self, to_email: str, full_name: str, raw_token: str) -> None:
        link = f"{current_app.config['FRONTEND_BASE_URL']}/reset-password?token={raw_token}"
        current_app.logger.info(
            "[email:password-reset] to=%s name=%s link=%s", to_email, full_name, link
        )


def _branded_html(title: str, intro: str, button_label: str, link: str, footnote: str) -> str:
    """Every value here is either a hardcoded string or a config-driven URL —
    the one user-controlled value callers pass in (the recipient's name) is
    never interpolated into this template, so there's no HTML-injection
    surface from account data."""
    return f"""\
<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#0b1220;font-family:Segoe UI,Helvetica,Arial,sans-serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#0b1220;padding:32px 0;">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="background:#111a2e;border-radius:12px;overflow:hidden;">
            <tr>
              <td style="padding:28px 32px 0 32px;">
                <span style="font-size:20px;font-weight:700;color:#22d3ee;">CyberShield</span>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px 0 32px;">
                <h1 style="margin:0;font-size:20px;color:#f8fafc;">{escape(title)}</h1>
                <p style="margin:16px 0 0 0;font-size:14px;line-height:1.6;color:#cbd5e1;">{escape(intro)}</p>
              </td>
            </tr>
            <tr>
              <td style="padding:28px 32px 0 32px;">
                <a href="{escape(link)}" style="display:inline-block;background:#22d3ee;color:#0b1220;font-weight:600;font-size:14px;text-decoration:none;padding:12px 24px;border-radius:8px;">{escape(button_label)}</a>
              </td>
            </tr>
            <tr>
              <td style="padding:20px 32px 0 32px;">
                <p style="margin:0;font-size:12px;line-height:1.6;color:#64748b;word-break:break-all;">
                  Or copy this link into your browser:<br />{escape(link)}
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:24px 32px 32px 32px;">
                <p style="margin:0;font-size:12px;color:#64748b;">{escape(footnote)}</p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>
"""


class SMTPEmailService(EmailService):
    """Real email delivery over SMTP (e.g. Gmail, SendGrid SMTP relay, SES
    SMTP interface, self-hosted Postfix). Configured entirely via env vars —
    see MAIL_SERVER/MAIL_PORT/MAIL_USERNAME/MAIL_PASSWORD/MAIL_USE_TLS/MAIL_FROM
    in app/config.py. Activated by setting MAIL_BACKEND=smtp.
    """

    def _send(self, to_email: str, subject: str, text_body: str, html_body: str) -> None:
        config = current_app.config
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = config["MAIL_FROM"]
        message["To"] = to_email
        message.attach(MIMEText(text_body, "plain"))
        message.attach(MIMEText(html_body, "html"))

        with smtplib.SMTP(config["MAIL_SERVER"], config["MAIL_PORT"], timeout=10) as server:
            if config.get("MAIL_USE_TLS", True):
                server.starttls()
            if config.get("MAIL_USERNAME"):
                server.login(config["MAIL_USERNAME"], config["MAIL_PASSWORD"])
            server.sendmail(config["MAIL_FROM"], [to_email], message.as_string())

    def send_verification_email(self, to_email: str, full_name: str, raw_token: str) -> None:
        link = f"{current_app.config['FRONTEND_BASE_URL']}/verify-email?token={raw_token}"
        ttl_hours = current_app.config["EMAIL_VERIFICATION_TOKEN_TTL_HOURS"]
        html_body = _branded_html(
            title="Verify your email address",
            intro=(
                f"Welcome to CyberShield, {full_name}! Thank you for creating your account. "
                "Please verify your email address to activate full account protection."
            ),
            button_label="Verify Email Address",
            link=link,
            footnote=(
                f"This verification link will expire in {ttl_hours} hours. "
                "If you did not create this account, you can safely ignore this email."
            ),
        )
        text_body = (
            f"Welcome to CyberShield, {full_name}!\n\n"
            "Please verify your email address by opening this link:\n"
            f"{link}\n\n"
            f"This link will expire in {ttl_hours} hours. "
            "If you did not create this account, you can safely ignore this email."
        )
        self._send(to_email, "Verify your CyberShield account", text_body, html_body)

    def send_password_reset_email(self, to_email: str, full_name: str, raw_token: str) -> None:
        link = f"{current_app.config['FRONTEND_BASE_URL']}/reset-password?token={raw_token}"
        ttl_minutes = current_app.config["PASSWORD_RESET_TOKEN_TTL_MINUTES"]
        html_body = _branded_html(
            title="Reset your password",
            intro=f"Hi {full_name}, we received a request to reset your CyberShield account password.",
            button_label="Reset Password",
            link=link,
            footnote=(
                f"This link will expire in {ttl_minutes} minutes. "
                "If you did not request this, you can safely ignore this email."
            ),
        )
        text_body = (
            f"Hi {full_name},\n\n"
            "We received a request to reset your CyberShield account password. "
            "Open this link to choose a new password:\n"
            f"{link}\n\n"
            f"This link will expire in {ttl_minutes} minutes. "
            "If you did not request this, you can safely ignore this email."
        )
        self._send(to_email, "Reset your CyberShield password", text_body, html_body)


_BACKENDS = {
    "console": ConsoleEmailService,
    "smtp": SMTPEmailService,
}


def get_email_service() -> EmailService:
    backend_name = current_app.config.get("MAIL_BACKEND", "console")
    backend_cls = _BACKENDS.get(backend_name, ConsoleEmailService)
    return backend_cls()
