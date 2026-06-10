from __future__ import annotations

from dataclasses import dataclass

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


class SequentialReceiptParser:
    def __init__(self, results: list[bool]) -> None:
        self.results = results
        self.index = 0

    def should_process(self, *, msg, since=None, until=None) -> bool:
        if self.index >= len(self.results):
            return False
        value = self.results[self.index]
        self.index += 1
        return value


def test_orchestrator_processes_only_parser_approved_messages():
    parser = SequentialReceiptParser([True, False, True])
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

    original_fetch_receipts = orchestrator._fetch_receipts

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
    finally:
        orchestrator._fetch_receipts = original_fetch_receipts
