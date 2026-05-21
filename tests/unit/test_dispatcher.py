"""Unit-тесты Dispatcher (T-023)."""
from datetime import datetime, timezone

import pytest

from packages.yandex_mail_agent.dispatcher import Dispatcher, DispatchRule
from packages.yandex_mail_agent.contracts import MailMessage


def _make_msg(
    subject: str = "Test",
    sender: str = "user@example.com",
    body_text: str = "Hello",
) -> MailMessage:
    return MailMessage(
        uid="<uid-001>",
        subject=subject,
        sender=sender,
        received_at=datetime.now(tz=timezone.utc),
        body_text=body_text,
    )


@pytest.fixture
def dispatcher() -> Dispatcher:
    return Dispatcher()


class TestDispatcherDefaults:
    def test_receipt_subject_returns_process_receipt(self, dispatcher: Dispatcher) -> None:
        msg = _make_msg(subject="Ваш чек от Ozon")
        assert dispatcher.dispatch(msg) == "process_receipt"

    def test_receipt_subject_english(self, dispatcher: Dispatcher) -> None:
        msg = _make_msg(subject="Your receipt #12345")
        assert dispatcher.dispatch(msg) == "process_receipt"

    def test_noreply_sender_skipped(self, dispatcher: Dispatcher) -> None:
        msg = _make_msg(sender="no-reply@shop.com")
        assert dispatcher.dispatch(msg) == "skip"

    def test_noreply_without_dash_skipped(self, dispatcher: Dispatcher) -> None:
        msg = _make_msg(sender="noreply@notifications.com")
        assert dispatcher.dispatch(msg) == "skip"

    def test_empty_body_skipped(self, dispatcher: Dispatcher) -> None:
        msg = _make_msg(body_text="   ")
        assert dispatcher.dispatch(msg) == "skip"

    def test_regular_message_skipped_by_default(self, dispatcher: Dispatcher) -> None:
        msg = _make_msg(subject="Hello there", sender="friend@gmail.com", body_text="Let's meet")
        assert dispatcher.dispatch(msg) == "skip"

    def test_receipt_priority_over_noreply(self, dispatcher: Dispatcher) -> None:
        # receipt_subject priority=10 > no_reply priority=5
        msg = _make_msg(subject="Чек за order", sender="no-reply@shop.com", body_text="Body")
        assert dispatcher.dispatch(msg) == "process_receipt"


class TestDispatcherCustomRule:
    def test_add_custom_rule(self, dispatcher: Dispatcher) -> None:
        rule = DispatchRule(
            name="vip",
            predicate=lambda m: "VIP" in m.subject,
            action="vip_handle",
            priority=20,
        )
        dispatcher.add_rule(rule)
        msg = _make_msg(subject="VIP offer for you")
        assert dispatcher.dispatch(msg) == "vip_handle"

    def test_broken_predicate_does_not_raise(self, dispatcher: Dispatcher) -> None:
        rule = DispatchRule(
            name="broken",
            predicate=lambda m: 1 / 0,  # выбросит ZeroDivisionError
            action="crash",
            priority=100,
        )
        dispatcher.add_rule(rule)
        msg = _make_msg()
        # должно вернуть skip без исключений
        result = dispatcher.dispatch(msg)
        assert isinstance(result, str)
