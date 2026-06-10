from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from packages.yandex_mail_agent.dispatcher import Dispatcher
from packages.yandex_mail_agent.smoke_test_orchestrator import SmokeTestOrchestrator


@dataclass
class DummyMessage:
    subject: str
    uid: str
    message_id: str | None = None
    from_: str | None = None
    text: str | None = None
    html: str | None = None
    date: datetime | None = None


class StubReceiptParser:
    def __init__(self, results: list[bool]) -> None:
        self.results = results
        self.calls = []
        self.index = 0

    def should_process(self, *, msg, since=None, until=None) -> bool:
        self.calls.append((msg, since, until))
        if self.index >= len(self.results):
            return False
        value = self.results[self.index]
        self.index += 1
        return value


def test_dispatcher_approves_message_when_parser_returns_true():
    parser = StubReceiptParser([True])
    dispatcher = Dispatcher(receipt_parser=parser)

    msg = DummyMessage(
        subject="Ваш чек",
        uid="42",
        message_id="msg-42",
        from_="shop@example.com",
        text="Ссылка на чек: https://ofd.ru/receipt/42",
    )

    decision = dispatcher.dispatch(msg)

    assert decision.should_process is True
    assert decision.reason == "approved_by_receipt_parser"
    assert decision.message_id == "42"
    assert len(parser.calls) == 1


def test_dispatcher_skips_message_when_parser_returns_false():
    parser = StubReceiptParser([False])
    dispatcher = Dispatcher(receipt_parser=parser)

    msg = DummyMessage(
        subject="Newsletter",
        uid="43",
        message_id="msg-43",
        from_="news@example.com",
        text="Обычное письмо без чека",
    )

    decision = dispatcher.dispatch(msg)

    assert decision.should_process is False
    assert decision.reason == "filtered_by_receipt_parser"
    assert decision.message_id == "43"
    assert len(parser.calls) == 1


def test_orchestrator_mail_gate_keeps_only_parser_approved_messages():
    parser = StubReceiptParser([True, False, True])
    dispatcher = Dispatcher(receipt_parser=parser)
    orchestrator = SmokeTestOrchestrator(dispatcher=dispatcher)

    messages = [
        DummyMessage(subject="Чек 1", uid="1", text="https://ofd.ru/1"),
        DummyMessage(subject="Письмо 2", uid="2", text="hello"),
        DummyMessage(subject="Чек 3", uid="3", text="https://ofd.ru/3"),
    ]

    class FakeFetcher:
        def fetch_recent_messages(self, max_count):
            return messages[:max_count]

        def extract_receipt_link(self, msg):
            if msg.uid == "1":
                return "https://ofd.ru/1"
            if msg.uid == "3":
                return "https://ofd.ru/3"
            return None

    orchestrator_fetch = orchestrator._fetch_receipts

    try:
        def patched_fetch_receipts(max_count: int):
            fetcher = FakeFetcher()
            fetched = fetcher.fetch_recent_messages(max_count)
            receipts = []

            for msg in fetched:
                decision = orchestrator.dispatcher.dispatch(msg)
                if not decision.should_process:
                    continue

                receipt_url = fetcher.extract_receipt_link(msg)
                if receipt_url:
                    receipts.append({
                        "url": receipt_url,
                        "subject": msg.subject,
                        "message_id": decision.message_id,
                    })

            return receipts

        orchestrator._fetch_receipts = patched_fetch_receipts

        receipts = orchestrator._fetch_receipts(5)

        assert len(receipts) == 2
        assert [item["message_id"] for item in receipts] == ["1", "3"]
        assert [item["url"] for item in receipts] == ["https://ofd.ru/1", "https://ofd.ru/3"]
        assert len(parser.calls) == 3
    finally:
        orchestrator._fetch_receipts = orchestrator_fetch
