"""MailParser — преобразование сырых MIME-сообщений в MailMessage."""
from __future__ import annotations

import email
import logging
import quopri
from email.header import decode_header
from email.message import Message
from typing import Optional

from .contracts import MailMessage

logger = logging.getLogger(__name__)


class MailParser:
    """Парсит RFC822-байты в структурированный MailMessage."""

    def parse(self, raw: bytes) -> MailMessage:
        msg: Message = email.message_from_bytes(raw)
        subject = self._decode_str(msg.get("Subject", ""))
        sender = msg.get("From", "")
        recipient = msg.get("To", "")
        date = msg.get("Date", "")
        message_id = msg.get("Message-ID", "")
        body = self._extract_body(msg)
        logger.debug("[Parser] parsed message_id=%s subject=%r", message_id, subject)
        return MailMessage(
            message_id=message_id,
            subject=subject,
            sender=sender,
            recipient=recipient,
            date=date,
            body=body,
            raw=raw,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _decode_str(value: str) -> str:
        parts = decode_header(value)
        decoded = []
        for part, charset in parts:
            if isinstance(part, bytes):
                decoded.append(part.decode(charset or "utf-8", errors="replace"))
            else:
                decoded.append(part)
        return "".join(decoded)

    def _extract_body(self, msg: Message) -> str:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == "text/plain":
                    return self._decode_payload(part)
        return self._decode_payload(msg)

    @staticmethod
    def _decode_payload(part: Message) -> str:
        payload = part.get_payload(decode=True)
        if payload is None:
            return ""
        charset = part.get_content_charset() or "utf-8"
        return payload.decode(charset, errors="replace")
