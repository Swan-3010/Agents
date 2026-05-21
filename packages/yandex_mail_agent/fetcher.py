"""MailFetcher — получение писем через IMAP (Yandex Mail)."""
from __future__ import annotations

import email
import imaplib
import logging
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .agent import AgentConfig

logger = logging.getLogger(__name__)

# Тип для разрешения циркулярных импортов
RawMessage = bytes


class MailFetcher:
    """Подключается к Yandex IMAP, забирает непрочитанные письма (UNSEEN)."""

    def __init__(self, config: "AgentConfig") -> None:
        self._cfg = config

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def fetch(self, limit: int = 10) -> List[RawMessage]:
        """Возвращает список сырых MIME-сообщений (до `limit` шт.)."""
        try:
            with self._connect() as conn:
                conn.select(self._cfg.mailbox)
                _, data = conn.search(None, "UNSEEN")
                uids = data[0].split()
                logger.info("[Fetcher] UNSEEN count=%d", len(uids))
                return self._fetch_messages(conn, uids[-limit:])
        except imaplib.IMAP4.error as exc:
            logger.error("[Fetcher] IMAP error: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _connect(self) -> imaplib.IMAP4_SSL:
        logger.debug(
            "[Fetcher] connecting to %s:%d",
            self._cfg.imap_host,
            self._cfg.imap_port,
        )
        conn = imaplib.IMAP4_SSL(
            host=self._cfg.imap_host,
            port=self._cfg.imap_port,
        )
        conn.login(self._cfg.email, self._cfg.app_password)
        return conn

    @staticmethod
    def _fetch_messages(
        conn: imaplib.IMAP4_SSL,
        uids: List[bytes],
    ) -> List[RawMessage]:
        messages: List[RawMessage] = []
        for uid in uids:
            _, msg_data = conn.fetch(uid, "(RFC822)")
            if msg_data and msg_data[0]:
                raw = msg_data[0][1]  # type: ignore[index]
                messages.append(raw)
        return messages
