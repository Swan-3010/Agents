"""mail_core.mail_client - Unified IMAP client built on imap-tools.

Replaces the raw imaplib-based YandexMailFetcher (fetcher.py) with a
higher-level client that:
  - uses imap_tools.MailBox as the IMAP transport
  - returns ParsedEmail objects (not raw strings)
  - supports FetchConfig-driven filtering
  - exposes fetch_one_receipt_link() for backward compatibility

Task: T-031 (imap-tools refactor)
Epic: E-04 - Core Interfaces
"""

from __future__ import annotations

import os
from typing import Generator, List, Optional

from imap_tools import MailBox, AND, MailMessage as ImapMessage

from .models import Address, Attachment, FetchConfig, ParsedEmail
from .parser import ReceiptParser


class MailClient:
    """High-level IMAP client built on imap-tools.

    Usage (context manager - recommended)::

        with MailClient() as client:
            emails = client.fetch_messages(FetchConfig(sender_filter='noreply@check.yandex.ru'))

    Usage (one-shot helper)::

        client = MailClient()
        link = client.fetch_one_receipt_link()
    """

    def __init__(
        self,
        host: Optional[str] = None,
        port: int = 993,
        user: Optional[str] = None,
        password: Optional[str] = None,
    ) -> None:
        self.host = host or os.getenv("TEST_IMAP_HOST", "imap.yandex.com")
        self.port = port or int(os.getenv("TEST_IMAP_PORT", "993"))
        self.user = user or os.getenv("TEST_EMAIL_ADDRESS", "")
        self.password = password or os.getenv("TEST_EMAIL_PASSWORD", "")
        self._receipt_sender = os.getenv("RECEIPT_SENDER", "noreply@check.yandex.ru")
        self._mailbox: Optional[MailBox] = None
        self._parser = ReceiptParser()

    # ------------------------------------------------------------------
    # Context manager
    # ------------------------------------------------------------------

    def __enter__(self) -> "MailClient":
        self._mailbox = MailBox(self.host, self.port).login(
            self.user, self.password
        )
        return self

    def __exit__(self, *args: object) -> None:
        if self._mailbox:
            self._mailbox.logout()
            self._mailbox = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def fetch_messages(
        self,
        config: Optional[FetchConfig] = None,
    ) -> List[ParsedEmail]:
        """Fetch messages matching *config* and return ParsedEmail list.

        If used outside a context manager, a temporary connection is opened
        and closed automatically.
        """
        cfg = config or FetchConfig()
        if self._mailbox:
            return list(self._fetch_with_mailbox(self._mailbox, cfg))
        with MailBox(self.host, self.port).login(self.user, self.password) as mb:
            return list(self._fetch_with_mailbox(mb, cfg))

    def fetch_one_receipt_link(self) -> Optional[str]:
        """Backward-compat helper: return the receipt URL from the latest
        email sent by the configured RECEIPT_SENDER, or None.
        """
        cfg = FetchConfig(
            sender_filter=self._receipt_sender,
            max_count=1,
            readonly=True,
        )
        messages = self.fetch_messages(cfg)
        if not messages:
            return None
        return messages[-1].receipt_url

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _fetch_with_mailbox(
        self,
        mb: MailBox,
        cfg: FetchConfig,
    ) -> Generator[ParsedEmail, None, None]:
        """Iterate imap_tools messages and yield ParsedEmail objects."""
        mb.folder.set(cfg.folder)

        # Build imap-tools AND() criteria
        criteria_parts: list = []
        if cfg.sender_filter:
            criteria_parts.append(AND(from_=cfg.sender_filter))
        if cfg.unseen_only:
            criteria_parts.append(AND(seen=False))

        criteria = AND(*criteria_parts) if criteria_parts else AND(all=True)

        fetched = 0
        for imap_msg in mb.fetch(
            criteria,
            readonly=cfg.readonly,
            mark_seen=cfg.mark_seen,
        ):
            parsed = self._to_parsed_email(imap_msg, cfg.folder)
            self._parser.enrich(parsed)
            yield parsed
            fetched += 1
            if cfg.max_count and fetched >= cfg.max_count:
                break

    @staticmethod
    def _to_parsed_email(msg: ImapMessage, folder: str) -> ParsedEmail:
        """Convert an imap_tools.MailMessage to ParsedEmail."""
        from_addr = None
        if msg.from_:
            from_addr = Address(email=msg.from_, name=None)

        to_addrs = [Address(email=addr) for addr in (msg.to or [])]
        cc_addrs = [Address(email=addr) for addr in (msg.cc or [])]

        attachments = [
            Attachment(
                filename=att.filename or "",
                content_type=att.content_type,
                size_bytes=len(att.payload),
                data=att.payload,
            )
            for att in msg.attachments
        ]

        return ParsedEmail(
            uid=str(msg.uid),
            message_id=msg.headers.get("message-id", [""])[0],
            subject=msg.subject or "",
            from_addr=from_addr,
            to_addrs=to_addrs,
            cc_addrs=cc_addrs,
            date=msg.date,
            body_text=msg.text or "",
            body_html=msg.html or "",
            attachments=attachments,
            folder=folder,
            is_seen="\\Seen" in (msg.flags or []),
            flags=list(msg.flags or []),
        )
