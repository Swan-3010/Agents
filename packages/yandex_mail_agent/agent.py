"""YandexMailAgent — точка входа агента обработки почты."""
from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List

from .contracts import AgentRunResult, MailMessage
from .fetcher import MailFetcher
from .parser import MailParser
from .dispatcher import Dispatcher
from .responder import Responder

logger = logging.getLogger(__name__)


@dataclass
class AgentConfig:
    """Runtime-конфигурация агента."""
    imap_host: str = "imap.yandex.ru"
    imap_port: int = 993
    smtp_host: str = "smtp.yandex.ru"
    smtp_port: int = 465
    email: str = ""
    app_password: str = ""
    mailbox: str = "INBOX"
    max_fetch: int = 10
    llm_endpoint: str = "http://localhost:11434"
    llm_model: str = "qwen2.5:7b-instruct"
    dry_run: bool = False


@dataclass
class YandexMailAgent:
    """Оркестратор: забирает письма, парсит, диспетчеризует, отвечает."""

    config: AgentConfig = field(default_factory=AgentConfig)
    _fetcher: MailFetcher = field(init=False)
    _parser: MailParser = field(init=False)
    _dispatcher: Dispatcher = field(init=False)
    _responder: Responder = field(init=False)

    def __post_init__(self) -> None:
        self._fetcher = MailFetcher(self.config)
        self._parser = MailParser()
        self._dispatcher = Dispatcher()
        self._responder = Responder(self.config)

    def run(self) -> AgentRunResult:
        """Один цикл: fetch → parse → dispatch → respond."""
        run_id = str(uuid.uuid4())
        started_at = datetime.now(tz=timezone.utc)
        logger.info("[Agent] run() started run_id=%s mailbox=%s", run_id, self.config.mailbox)

        errors: List[str] = []
        raw_messages = self._fetcher.fetch(limit=self.config.max_fetch)
        logger.info("[Agent] fetched %d raw messages", len(raw_messages))

        messages: List[MailMessage] = []
        for raw in raw_messages:
            try:
                messages.append(self._parser.parse(raw))
            except Exception as exc:  # noqa: BLE001
                logger.error("[Agent] parse error: %s", exc)
                errors.append(str(exc))

        receipts_parsed = 0
        for msg in messages:
            try:
                action = self._dispatcher.dispatch(msg)
                if action == "skip":
                    continue
                if action == "process_receipt":
                    receipts_parsed += 1
                if not self.config.dry_run:
                    self._responder.respond(msg, action)
            except Exception as exc:  # noqa: BLE001
                logger.error("[Agent] dispatch/respond error: %s", exc)
                errors.append(str(exc))

        finished_at = datetime.now(tz=timezone.utc)
        result = AgentRunResult(
            run_id=run_id,
            started_at=started_at,
            finished_at=finished_at,
            messages_fetched=len(raw_messages),
            receipts_parsed=receipts_parsed,
            errors=errors,
        )
        logger.info("[Agent] run() finished: %s", result)
        return result

    def run_once(self) -> AgentRunResult:
        return self.run()
