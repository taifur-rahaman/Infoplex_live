"""Brevo transactional email with console/mock fallback."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_platform_email(to_email: str, subject: str, html_content: str, text_content: str = "") -> bool:
    """Send via Brevo API when BREVO_API_KEY is set; otherwise log/console."""
    api_key = getattr(settings, "BREVO_API_KEY", "") or ""
    sender = getattr(settings, "BREVO_SENDER_EMAIL", "noreply@infoplex.local")
    text = text_content or html_content

    if not api_key:
        logger.info(
            "Brevo mock: to=%s subject=%s body=%s",
            to_email,
            subject,
            text[:200],
        )
        send_mail(subject, text, sender, [to_email], fail_silently=True)
        return True

    payload = {
        "sender": {"email": sender, "name": "InfoPlex"},
        "to": [{"email": to_email}],
        "subject": subject,
        "htmlContent": html_content,
        "textContent": text,
    }
    req = urllib.request.Request(
        "https://api.brevo.com/v3/smtp/email",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return 200 <= resp.status < 300
    except urllib.error.URLError as exc:
        logger.warning("Brevo send failed (%s); falling back to console", exc)
        send_mail(subject, text, sender, [to_email], fail_silently=True)
        return False
