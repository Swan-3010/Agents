"""Unit-тесты MailParser (T-022)."""
import email
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pytest

from packages.yandex_mail_agent.parser import MailParser
from packages.yandex_mail_agent.contracts import MailMessage


def _make_raw(subject: str, sender: str, body: str, date: str = "Thu, 01 Jan 2026 12:00:00 +0300") -> bytes:
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = "agent@yandex.ru"
    msg["Date"] = date
    msg["Message-ID"] = "<test-001@test>"
    return msg.as_bytes()


@pytest.fixture
def parser() -> MailParser:
    return MailParser()


class TestMailParserParse:
    def test_returns_mail_message(self, parser: MailParser) -> None:
        raw = _make_raw("Hello", "user@example.com", "Test body")
        result = parser.parse(raw)
        assert isinstance(result, MailMessage)

    def test_subject_decoded(self, parser: MailParser) -> None:
        raw = _make_raw("Hello World", "user@example.com", "Body")
        result = parser.parse(raw)
        assert result.subject == "Hello World"

    def test_sender_extracted(self, parser: MailParser) -> None:
        raw = _make_raw("Subj", "Ivan <ivan@yandex.ru>", "Body")
        result = parser.parse(raw)
        assert "ivan@yandex.ru" in result.sender

    def test_uid_from_message_id(self, parser: MailParser) -> None:
        raw = _make_raw("Subj", "a@b.com", "Body")
        result = parser.parse(raw)
        assert result.uid == "<test-001@test>"

    def test_uid_fallback_uuid_if_no_message_id(self, parser: MailParser) -> None:
        msg = MIMEText("Body", "plain", "utf-8")
        msg["Subject"] = "No ID"
        msg["From"] = "a@b.com"
        msg["Date"] = "Thu, 01 Jan 2026 12:00:00 +0300"
        result = parser.parse(msg.as_bytes())
        assert result.uid  # должен быть непустым

    def test_received_at_is_datetime(self, parser: MailParser) -> None:
        raw = _make_raw("Subj", "a@b.com", "Body")
        result = parser.parse(raw)
        assert isinstance(result.received_at, datetime)

    def test_body_text_extracted(self, parser: MailParser) -> None:
        raw = _make_raw("Subj", "a@b.com", "Hello from body")
        result = parser.parse(raw)
        assert result.body_text is not None
        assert "Hello from body" in result.body_text

    def test_body_html_none_for_plain(self, parser: MailParser) -> None:
        raw = _make_raw("Subj", "a@b.com", "Body")
        result = parser.parse(raw)
        assert result.body_html is None

    def test_multipart_extracts_text_and_html(self, parser: MailParser) -> None:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Multi"
        msg["From"] = "a@b.com"
        msg["Date"] = "Thu, 01 Jan 2026 12:00:00 +0300"
        msg["Message-ID"] = "<multi-001>"
        msg.attach(MIMEText("Plain body", "plain", "utf-8"))
        msg.attach(MIMEText("<b>HTML body</b>", "html", "utf-8"))
        result = parser.parse(msg.as_bytes())
        assert result.body_text is not None
        assert result.body_html is not None
        assert "Plain body" in result.body_text
        assert "HTML body" in result.body_html

    def test_bad_date_fallback(self, parser: MailParser) -> None:
        raw = _make_raw("Subj", "a@b.com", "Body", date="not-a-date")
        result = parser.parse(raw)
        assert isinstance(result.received_at, datetime)
