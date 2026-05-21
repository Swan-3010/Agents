"""YandexMailAgent — точка входа агента обработки почты."""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
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

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(self) -> AgentRunResult:
        """Один цикл обработки: fetch → parse → dispatch → respond."""
        logger.info("[Agent] run() started — mailbox=%s", self.config.mailbox)

        raw_messages = self._fetcher.fetch(limit=self.config.max_fetch)
        logger.info("[Agent] fetched %d raw messages", len(raw_messages))

        messages: List[MailMessage] = [
            self._parser.parse(raw) for raw in raw_messages
        ]

        processed: List[MailMessage] = []
        skipped: List[MailMessage] = []

        for msg in messages:
            action = self._dispatcher.dispatch(msg)
            if action == "skip":
                skipped.append(msg)
                continue
            if not self.config.dry_run:
                self._responder.respond(msg, action)
            processed.append(msg)

        result = AgentRunResult(
            total=len(messages),
            processed=len(processed),
            skipped=len(skipped),
            errors=[],
        )
        logger.info("[Agent] run() finished — %s", result)
        return result

    def run_once(self) -> AgentRunResult:
        """Алиас run() для CLI/cron."""
        return self.run()
