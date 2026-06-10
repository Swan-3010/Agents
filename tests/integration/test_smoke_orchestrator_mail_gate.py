from __future__ import annotations

from dataclasses import dataclass

from packages.yandex_mail_agent.dispatcher import Dispatcher
from packages.yandex_mail_agent.smoke_test_orchestrator import SmokeTestOrchestrator


@dataclass
class DummyMessage:
    subject: str
    uid: str


class SequentialReceiptParser:
    def __init__(self, results: list[bool]) -> None:
        self.results = results
        self.index = 0

    def should_process(self, *, msg, since=None, until=None) -> bool:
        value = self.results[self.index]
        self.index += 1
        return value


def test_orchestrator_processes_only_parser_approved_messages():
    parser = SequentialReceiptParser([True, False, True])
    dispatcher = Dispatcher(receipt_parser=parser)
    orchestrator = SmokeTestOrchestrator(dispatcher=dispatcher)

    messages = [
        DummyMessage(subject="msg-1", uid="1"),
        DummyMessage(subject="msg-2", uid="2"),
        DummyMessage(subject="msg-3", uid="3"),
    ]

    result = orchestrator.run_mail_gate(messages)

    assert result.total_messages == 3
    assert result.approved_messages == 2
    assert result.skipped_messages == 1
    assert [msg.uid for msg in result.approved_payloads] == ["1", "3"]
