"""Unit-тесты Dispatcher — T-038.

Обновлено для работы с ParsedEmail + реальным ReceiptParser.should_process().
Обратная совместимость с MailMessage сохранена.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from packages.mail_core.models import ParsedEmail, Address
from packages.mail_core.parser import ReceiptParser
from packages.yandex_mail_agent.dispatcher import Dispatcher, DispatchRule


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_parsed(
    subject: str = "Test",
    sender: str = "user@example.com",
    body_text: str = "Hello",
    date: datetime | None = None,
) -> ParsedEmail:
    return ParsedEmail(
        uid="uid-001",
        subject=subject,
        from_address=Address(name="Test", email=sender),
        body_text=body_text,
        date=date or datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc),
    )


# ---------------------------------------------------------------------------
# TestDispatcherWithRealParser
# ---------------------------------------------------------------------------

class TestDispatcherWithRealParser:
    """Dispatcher с настоящим ReceiptParser — без моков."""

    def setup_method(self):
        self.parser = ReceiptParser()
        self.dispatcher = Dispatcher(receipt_parser=self.parser)

    def test_receipt_subject_ru_approved(self):
        msg = _make_parsed(subject="Чек от Ozon")
        decision = self.dispatcher.dispatch(msg)
        assert decision.should_process is True
        assert decision.reason == "approved_by_receipt_parser"

    def test_receipt_subject_en_approved(self):
        msg = _make_parsed(subject="Your receipt #12345")
        decision = self.dispatcher.dispatch(msg)
        assert decision.should_process is True

    def test_payment_subject_approved(self):
        msg = _make_parsed(subject="Оплата принята")
        decision = self.dispatcher.dispatch(msg)
        assert decision.should_process is True

    def test_unrelated_subject_filtered(self):
        msg = _make_parsed(subject="Новости недели")
        decision = self.dispatcher.dispatch(msg)
        assert decision.should_process is False
        assert decision.reason == "filtered_by_receipt_parser"

    def test_empty_subject_filtered(self):
        msg = _make_parsed(subject="")
        decision = self.dispatcher.dispatch(msg)
        assert decision.should_process is False

    def test_receipt_within_date_range_approved(self):
        msg = _make_parsed(
            subject="Чек",
            date=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        decision = self.dispatcher.dispatch(
            msg,
            since=datetime(2026, 6, 1, tzinfo=timezone.utc),
            until=datetime(2026, 6, 30, tzinfo=timezone.utc),
        )
        assert decision.should_process is True

    def test_receipt_out_of_date_range_filtered(self):
        msg = _make_parsed(
            subject="Invoice #99",
            date=datetime(2026, 7, 5, tzinfo=timezone.utc),
        )
        decision = self.dispatcher.dispatch(
            msg,
            since=datetime(2026, 6, 1, tzinfo=timezone.utc),
            until=datetime(2026, 6, 30, tzinfo=timezone.utc),
        )
        assert decision.should_process is False

    def test_no_parser_raises_or_skips(self):
        """Dispatcher без парсера — должен вызывать AttributeError или обрабатывать корректно."""
        dispatcher_no_parser = Dispatcher(receipt_parser=None)
        msg = _make_parsed(subject="Чек")
        with pytest.raises((AttributeError, TypeError)):
            dispatcher_no_parser.dispatch(msg)


# ---------------------------------------------------------------------------
# TestDispatcherCustomRule (legacy — обратная совместимость)
# ---------------------------------------------------------------------------

class TestDispatcherCustomRule:
    """Custom DispatchRule API — проверка обратной совместимости."""

    def test_add_custom_rule(self):
        parser = ReceiptParser()
        dispatcher = Dispatcher(receipt_parser=parser)
        vip_rule = DispatchRule(
            name="vip",
            predicate=lambda msg: "VIP" in (msg.subject or ""),
            action="process_vip",
        )
        dispatcher.add_rule(vip_rule)
        msg = _make_parsed(subject="VIP Order")
        decision = dispatcher.dispatch(msg)
        assert decision.should_process is True

    def test_broken_predicate_does_not_raise(self):
        parser = ReceiptParser()
        dispatcher = Dispatcher(receipt_parser=parser)
        broken_rule = DispatchRule(
            name="broken",
            predicate=lambda msg: 1 / 0,  # ZeroDivisionError
            action="process",
        )
        dispatcher.add_rule(broken_rule)
        msg = _make_parsed(subject="Чек")
        # Не должен падать, даже если предикат падает
        try:
            decision = dispatcher.dispatch(msg)
        except Exception:
            pytest.fail("Dispatcher выбросил исключение при broken predicate")
