"""MailParser — преобразование сырых MIME-сообщений в MailMessage."""
from __future__ import annotations

import email
import logging
import uuid
from datetime import datetime, timezone
from email.header import decode_header
from email.message import Message
from email.utils import parsedate_to_datetime
from typing import Optional

from .contracts import MailMessage

logger = logging.getLogger(__name__)


class MailParser:
    """Парсит RFC822-байты в структурированный MailMessage."""

    def parse(self, raw: bytes) -> MailMessage:
        msg: Message = email.message_from_bytes(raw)
        subject = self._decode_str(msg.get("Subject", ""))
        sender = msg.get("From", "")
        uid = msg.get("Message-ID") or str(uuid.uuid4())
        received_at = self._parse_date(msg.get("Date", ""))
        body_text = self._extract_text(msg)
        body_html = self._extract_html(msg)
        logger.debug("[Parser] parsed uid=%s subject=%r", uid, subject)
        return MailMessage(
            uid=uid,
            subject=subject,
            sender=sender,
            received_at=received_at,
            body_text=body_text,
            body_html=body_html,
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

    @staticmethod
    def _parse_date(date_str: str) -> datetime:
        try:
            return parsedate_to_datetime(date_str)
        except Exception:  # noqa: BLE001
            return datetime.now(tz=timezone.utc)

    def _extract_text(self, msg: Message) -> Optional[str]:
        return self._extract_part(msg, "text/plain")

    def _extract_html(self, msg: Message) -> Optional[str]:
        return self._extract_part(msg, "text/html")

    @staticmethod
    def _extract_part(msg: Message, content_type: str) -> Optional[str]:
        if msg.is_multipart():
            for part in msg.walk():
                if part.get_content_type() == content_type:
                    payload = part.get_payload(decode=True)
                    if payload:
                        charset = part.get_content_charset() or "utf-8"
                        return payload.decode(charset, errors="replace")
            return None
        if msg.get_content_type() == content_type:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                return payload.decode(charset, errors="replace")
        return None
