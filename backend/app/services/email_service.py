"""
Transactional email service via Resend.

Sends verification and password-reset emails. All provider errors are caught
and surfaced to the caller so the API never claims an email was sent when
delivery failed. API keys and tokens are never logged.
"""
import logging
from typing import Optional

import httpx

from app.config import settings

logger = logging.getLogger("ats_resume_checker")

RESEND_API_URL = "https://api.resend.com/emails"


# ---------------------------------------------------------------------------
# Templates
# ---------------------------------------------------------------------------

def _html_template(title: str, body: str, cta_text: str, cta_url: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f4f4f5; margin: 0; padding: 0; }}
    .container {{ max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }}
    .header {{ background: #4f46e5; color: #ffffff; padding: 24px; text-align: center; }}
    .content {{ padding: 32px 24px; color: #1f2937; line-height: 1.6; }}
    .cta {{ display: inline-block; background: #4f46e5; color: #ffffff; text-decoration: none; padding: 12px 28px; border-radius: 8px; font-weight: 600; margin: 16px 0; }}
    .footer {{ padding: 16px 24px; background: #f9fafb; color: #6b7280; font-size: 12px; text-align: center; }}
    a {{ color: #4f46e5; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header"><h1 style="margin:0;font-size:24px;">{title}</h1></div>
    <div class="content">
      {body}
      <p><a href="{cta_url}" class="cta">{cta_text}</a></p>
    </div>
    <div class="footer">
      <p>If you did not request this email, you can safely ignore it.</p>
      <p>ATS Resume Score Checker</p>
    </div>
  </div>
</body>
</html>"""


def _text_template(title: str, body: str, cta_text: str, cta_url: str) -> str:
    return f"""{title}

{body}

{cta_text}:
{cta_url}

If you did not request this email, you can safely ignore it.

ATS Resume Score Checker
"""


def verification_email_html(verify_url: str) -> str:
    return _html_template(
        "Verify your email address",
        "<p>Thank you for creating an account. Please verify your email address by clicking the button below.</p>"
        "<p>This link will expire in 30 minutes.</p>",
        "Verify Email",
        verify_url,
    )


def verification_email_text(verify_url: str) -> str:
    return _text_template(
        "Verify your email address",
        "Thank you for creating an account. Please verify your email address by clicking the link below.\n\n"
        "This link will expire in 30 minutes.",
        "Verify Email",
        verify_url,
    )


def password_reset_email_html(reset_url: str) -> str:
    return _html_template(
        "Reset your password",
        "<p>We received a request to reset the password for your account.</p>"
        "<p>If you made this request, click the button below to choose a new password.</p>"
        "<p>This link will expire in 60 minutes.</p>",
        "Reset Password",
        reset_url,
    )


def password_reset_email_text(reset_url: str) -> str:
    return _text_template(
        "Reset your password",
        "We received a request to reset the password for your account.\n\n"
        "If you made this request, click the link below to choose a new password.\n\n"
        "This link will expire in 60 minutes.",
        "Reset Password",
        reset_url,
    )


# ---------------------------------------------------------------------------
# Sender
# ---------------------------------------------------------------------------

async def send_email(
    to: str,
    subject: str,
    html_body: str,
    text_body: str,
) -> bool:
    """Send an email via Resend. Returns True on success, False on failure.

    Never raises — all provider errors are caught and logged without secrets.
    """
    if not settings.RESEND_API_KEY:
        logger.warning("RESEND_API_KEY not configured; skipping email to %s", _mask_email(to))
        return False

    payload = {
        "from": settings.EMAIL_FROM,
        "to": [to],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    headers = {
        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
        "Content-Type": "application/json",
    }

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(RESEND_API_URL, json=payload, headers=headers)
    except Exception as exc:
        logger.error("Email provider request failed: %s", exc)
        return False

    if response.status_code >= 400:
        logger.error(
            "Email provider rejected request (status=%s) for subject=%r",
            response.status_code,
            subject,
        )
        return False

    logger.info("Email sent successfully (subject=%r)", subject)
    return True


def _mask_email(email: str) -> str:
    """Mask an email address for safe logging."""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[0]}***@{domain}"


async def send_verification_email(to: str, verify_url: str) -> bool:
    return await send_email(
        to=to,
        subject="Verify your email address",
        html_body=verification_email_html(verify_url),
        text_body=verification_email_text(verify_url),
    )


async def send_password_reset_email(to: str, reset_url: str) -> bool:
    return await send_email(
        to=to,
        subject="Reset your password",
        html_body=password_reset_email_html(reset_url),
        text_body=password_reset_email_text(reset_url),
    )