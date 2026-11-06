"""SMTP delivery for document broadcasts."""

from __future__ import annotations

import logging
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from email.utils import formatdate, make_msgid

from app.config import settings
from app.core.errors import MailDeliveryError
from app.db.models import User
from app.services.catalog import SMTP_SERVER_LABELS

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SmtpServer:
    key: str
    label: str
    host: str
    port: int
    starttls: bool


def get_server(key: str) -> SmtpServer:
    servers = {
        "sharp": SmtpServer(
            key="sharp",
            label=SMTP_SERVER_LABELS["sharp"],
            host=settings.sharp_smtp_host,
            port=settings.sharp_smtp_port,
            starttls=settings.sharp_smtp_starttls,
        ),
        "office": SmtpServer(
            key="office",
            label=SMTP_SERVER_LABELS["office"],
            host=settings.office_smtp_host,
            port=settings.office_smtp_port,
            starttls=settings.office_smtp_starttls,
        ),
    }
    try:
        return servers[key]
    except KeyError as exc:
        raise MailDeliveryError(f"Unknown SMTP server '{key}'") from exc


def resolve_sender(user: User) -> tuple[str, str]:
    """Prefer the signed-in user's mailbox, fall back to the configured account."""
    user_email = (user.email or "").strip()
    user_password = (user.mail_password or "").strip()
    if user_email and user_password and user_password.lower() not in {"string", "changeme"}:
        return user_email, user_password
    return settings.smtp_sender_email, settings.smtp_sender_password


def send_broadcast(
    *,
    server_key: str,
    sender_email: str,
    sender_password: str,
    to: list[str],
    cc: list[str],
    subject: str,
    body: str,
) -> None:
    if not sender_email:
        raise MailDeliveryError("No sender account is configured")
    if not to:
        raise MailDeliveryError("There are no direct recipients for this document")

    server = get_server(server_key)
    message = EmailMessage()
    message["From"] = sender_email
    message["To"] = ", ".join(to)
    if cc:
        message["Cc"] = ", ".join(cc)
    message["Subject"] = subject
    message["Date"] = formatdate(localtime=True)
    message["Message-ID"] = make_msgid(domain=sender_email.split("@")[-1] or None)
    message.set_content(body)

    recipients = list(dict.fromkeys([*to, *cc]))

    try:
        with smtplib.SMTP(server.host, server.port, timeout=settings.smtp_timeout_seconds) as smtp:
            smtp.ehlo()
            if server.starttls:
                smtp.starttls()
                smtp.ehlo()
            if sender_password:
                smtp.login(sender_email, sender_password)
            smtp.send_message(message, from_addr=sender_email, to_addrs=recipients)
    except smtplib.SMTPAuthenticationError as exc:
        logger.warning("SMTP authentication failed for %s: %s", sender_email, exc)
        raise MailDeliveryError("The mail server rejected the sender credentials") from exc
    except (smtplib.SMTPException, OSError) as exc:
        logger.warning("SMTP delivery through %s failed: %s", server.host, exc)
        raise MailDeliveryError(f"Could not deliver the mail through {server.label}: {exc}") from exc
