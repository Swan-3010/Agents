"""Integration: SmokeTestOrchestrator + Dispatcher + ReceiptParser — T-038.

Тесты проверяют:
  1. Мок-режим (обратная совместимость с SequentialReceiptParser)
  2. Реальный режим — ParsedEmail через настоящий ReceiptParser
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from packages.mail_core.models import ParsedEmail, Address
from packages.mail_core.parser import ReceiptParser
from packages.yandex_mail_agent.dispatcher import Dispatcher
from packages.yandex_mail_agent.smoke_test_orchestrator import SmokeTestOrchestrator


# ---------------------------------------------------------------------------
# Legacy DummyMessage (обратная совместимость)
# ---------------------------------------------------------------------------

@dataclass
class DummyMessage:
    subject: str
    uid: str
    message_id: str | None = None
    from_: str | None = None
    text: str | None = None
    html: str | None = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parsed(
    subject: str,
    uid: str,
    body_text: str = "",
    date: datetime | None = None,
) -> ParsedEmail:
    return ParsedEmail(
        uid=uid,
        subject=subject,
        from_address=Address(name="Shop", email="shop@example.com"),
        body_text=body_text,
        date=date or datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# Legacy smoke — мок SequentialReceiptParser (без изменений)
# ---------------------------------------------------------------------------

class SequentialReceiptParser:
    """Mock: возвращает заранее заданный список True/False."""

    def __init__(self, results: list[bool]):
        self._results = iter(results)

    def should_process(self, msg, **kwargs) -> bool:
        return next(self._results, False)


def test_orchestrator_processes_only_parser_approved_messages():
    parser = SequentialReceiptParser([True, False, True])
    dispatcher = Dispatcher(receipt_parser=parser)
    orchestrator = SmokeTestOrchestrator(dispatcher=dispatcher)
    messages = [
        DummyMessage(subject="Чек 1", uid="1", text="https://ofd.ru/1"),
        DummyMessage(subject="Письмо 2", uid="2", text="hello"),
        DummyMessage(subject="Чек 3", uid="3", text="https://ofd.ru/3"),
    ]
    results = orchestrator.run(messages)
    processed_uids = [r.uid for r in results if r.processed]
    assert processed_uids == ["1", "3"]


# ---------------------------------------------------------------------------
# Реальный smoke — ParsedEmail + настоящий ReceiptParser (T-038)
# ---------------------------------------------------------------------------

def test_orchestrator_with_real_parser_filters_correctly():
    """SmokeTestOrchestrator с настоящим ReceiptParser:
    пропускает письма с подходящей темой, фильтрует все остальные.
    """
    parser = ReceiptParser()
    dispatcher = Dispatcher(receipt_parser=parser)
    orchestrator = SmokeTestOrchestrator(dispatcher=dispatcher)

    messages = [
        _make_parsed(subject="Чек от Wildberries", uid="w1", body_text="https://ofd.ru/r/abc"),
        _make_parsed(subject="Новостная рассылка", uid="n1", body_text="hello world"),
        _make_parsed(subject="Invoice #555", uid="i1", body_text="https://check.ofd.ru/path"),
        _make_parsed(subject="Объявление от магазина", uid="s1", body_text="sale!"),
    ]
    results = orchestrator.run(messages)
    processed_uids = {r.uid for r in results if r.processed}
    assert "w1" in processed_uids   # чек → пропускаем
    assert "i1" in processed_uids   # invoice → пропускаем
    assert "n1" not in processed_uids  # новости → фильтруем
    assert "s1" not in processed_uids  # объявление → фильтруем


def test_orchestrator_real_parser_date_filter():
    """SmokeTestOrchestrator с date-фильтром — чек вне диапазона должен быть отфильтрован."""
    parser = ReceiptParser()
    dispatcher = Dispatcher(receipt_parser=parser)
    orchestrator = SmokeTestOrchestrator(dispatcher=dispatcher)

    since = datetime(2026, 6, 1, tzinfo=timezone.utc)
    until = datetime(2026, 6, 30, tzinfo=timezone.utc)

    messages = [
        _make_parsed(
            subject="Чек в диапазоне",
            uid="in_range",
            date=datetime(2026, 6, 15, tzinfo=timezone.utc),
        ),
        _make_parsed(
            subject="Оплата вне диапазона",
            uid="out_range",
            date=datetime(2026, 7, 10, tzinfo=timezone.utc),
        ),
    ]
    results = orchestrator.run(messages, since=since, until=until)
    processed_uids = {r.uid for r in results if r.processed}
    assert "in_range" in processed_uids
    assert "out_range" not in processed_uids
