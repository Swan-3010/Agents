from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from packages.yandex_mail_agent.dispatcher import Dispatcher


@dataclass
class DummyMessage:
    subject: str
    from_: str
    text: str | None = None
    html: str | None = None
    date: datetime | None = None
    uid: str | None = None


class StubReceiptParser:
    def __init__(self, result: bool) -> None:
        self.result = result
        self.calls = []

    def should_process(self, *, msg, since=None, until=None) -> bool:
        self.calls.append((msg, since, until))
        return self.result


def test_dispatcher_uses_receipt_parser_gate():
    parser = StubReceiptParser(result=True)
    dispatcher = Dispatcher(receipt_parser=parser)

    msg = DummyMessage(
        subject="Ваш чек",
        from_="shop@example.com",
        text="https://ofd.ru/receipt/1",
        uid="42",
    )

    decision = dispatcher.dispatch(msg)

    assert decision.should_process is True
    assert decision.reason == "approved_by_receipt_parser"
    assert len(parser.calls) == 1


def test_dispatcher_skips_message_when_parser_rejects():
    parser = StubReceiptParser(result=False)
    dispatcher = Dispatcher(receipt_parser=parser)

    msg = DummyMessage(
        subject="Newsletter",
        from_="news@example.com",
        text="hello",
        uid="43",
    )

    decision = dispatcher.dispatch(msg)

    assert decision.should_process is False
    assert decision.reason == "filtered_by_receipt_parser"
    assert len(parser.calls) == 1
