"""Unit tests for ReceiptParser - T-037.

Covers:
  - OFD URL extraction from text/html body
  - subject_matches_receipt()
  - is_within_date_range()
  - should_process()
"""

import pytest
from datetime import datetime, timezone, timedelta

from packages.mail_core.parser import ReceiptParser
from packages.mail_core.models import ParsedEmail, Address


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_email(
    subject: str = "",
    body_text: str = "",
    body_html: str | None = None,
    date: datetime | None = None,
) -> ParsedEmail:
    return ParsedEmail(
        uid="test-uid-001",
        subject=subject,
        from_address=Address(name="Test", email="test@example.com"),
        body_text=body_text,
        body_html=body_html,
        date=date or datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc),
    )


parser = ReceiptParser()


# ===========================================================================
# OFD URL extraction
# ===========================================================================

class TestExtractFromText:
    def test_ofd_ru_url_found(self):
        text = "Your receipt: https://ofd.ru/r/abc123-xyz"
        assert ReceiptParser.extract_from_text(text) == "https://ofd.ru/r/abc123-xyz"

    def test_check_ofd_ru_found(self):
        text = "See: https://check.ofd.ru/some/path/here"
        assert ReceiptParser.extract_from_text(text) == "https://check.ofd.ru/some/path/here"

    def test_consumer_rnko_found(self):
        text = "Link: https://consumer.rnko.ru/receipt/99"
        assert ReceiptParser.extract_from_text(text) == "https://consumer.rnko.ru/receipt/99"

    def test_no_url_returns_none(self):
        assert ReceiptParser.extract_from_text("Hello, no links here.") is None

    def test_empty_string_returns_none(self):
        assert ReceiptParser.extract_from_text("") is None

    def test_prefers_body_text_over_html(self):
        msg = _make_email(
            body_text="text: https://ofd.ru/r/from-text",
            body_html="<a href='https://ofd.ru/r/from-html'>link</a>",
        )
        enriched = parser.enrich(msg)
        assert enriched.receipt_url == "https://ofd.ru/r/from-text"

    def test_falls_back_to_html_if_text_has_no_url(self):
        msg = _make_email(
            body_text="No URL here.",
            body_html="check: https://check.ofd.ru/html-path",
        )
        enriched = parser.enrich(msg)
        assert enriched.receipt_url == "https://check.ofd.ru/html-path"

    def test_enrich_sets_receipt_sender(self):
        msg = _make_email(body_text="https://ofd.ru/r/x")
        enriched = parser.enrich(msg)
        assert enriched.receipt_sender == "test@example.com"

    def test_enrich_no_url_receipt_url_is_none(self):
        msg = _make_email(body_text="nothing useful")
        enriched = parser.enrich(msg)
        assert enriched.receipt_url is None


# ===========================================================================
# subject_matches_receipt
# ===========================================================================

class TestSubjectMatchesReceipt:
    def test_russian_chek(self):
        assert ReceiptParser.subject_matches_receipt("Чек от Wildberries")

    def test_russian_oplata(self):
        assert ReceiptParser.subject_matches_receipt("Оплата принята")

    def test_russian_pokupka(self):
        assert ReceiptParser.subject_matches_receipt("Ваша покупка оформлена")

    def test_english_receipt(self):
        assert ReceiptParser.subject_matches_receipt("Your receipt from Amazon")

    def test_english_invoice(self):
        assert ReceiptParser.subject_matches_receipt("Invoice #12345")

    def test_english_payment(self):
        assert ReceiptParser.subject_matches_receipt("Payment confirmation")

    def test_unrelated_subject_returns_false(self):
        assert not ReceiptParser.subject_matches_receipt("Новости недели")

    def test_empty_subject_returns_false(self):
        assert not ReceiptParser.subject_matches_receipt("")

    def test_case_insensitive(self):
        assert ReceiptParser.subject_matches_receipt("RECEIPT from store")


# ===========================================================================
# is_within_date_range
# ===========================================================================

class TestIsWithinDateRange:
    BASE = datetime(2026, 6, 10, 12, 0, 0, tzinfo=timezone.utc)
    BEFORE = BASE - timedelta(days=1)
    AFTER = BASE + timedelta(days=1)

    def test_no_bounds_always_true(self):
        assert ReceiptParser.is_within_date_range(self.BASE)

    def test_within_since_and_until(self):
        assert ReceiptParser.is_within_date_range(
            self.BASE, since=self.BEFORE, until=self.AFTER
        )

    def test_before_since_returns_false(self):
        assert not ReceiptParser.is_within_date_range(
            self.BEFORE, since=self.BASE
        )

    def test_after_until_returns_false(self):
        assert not ReceiptParser.is_within_date_range(
            self.AFTER, until=self.BASE
        )

    def test_exactly_on_since_boundary(self):
        assert ReceiptParser.is_within_date_range(
            self.BASE, since=self.BASE
        )

    def test_exactly_on_until_boundary(self):
        assert ReceiptParser.is_within_date_range(
            self.BASE, until=self.BASE
        )

    def test_naive_datetime_treated_as_utc(self):
        naive = datetime(2026, 6, 10, 12, 0, 0)  # no tzinfo
        assert ReceiptParser.is_within_date_range(
            naive,
            since=datetime(2026, 6, 9, tzinfo=timezone.utc),
            until=datetime(2026, 6, 11, tzinfo=timezone.utc),
        )


# ===========================================================================
# should_process
# ===========================================================================

class TestShouldProcess:
    SINCE = datetime(2026, 6, 1, tzinfo=timezone.utc)
    UNTIL = datetime(2026, 6, 30, tzinfo=timezone.utc)

    def test_receipt_subject_in_range_returns_true(self):
        msg = _make_email(
            subject="Чек от магазина",
            date=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        assert parser.should_process(msg, since=self.SINCE, until=self.UNTIL)

    def test_unrelated_subject_returns_false(self):
        msg = _make_email(
            subject="Рассылка новостей",
            date=datetime(2026, 6, 15, tzinfo=timezone.utc),
        )
        assert not parser.should_process(msg, since=self.SINCE, until=self.UNTIL)

    def test_receipt_subject_out_of_range_returns_false(self):
        msg = _make_email(
            subject="Оплата принята",
            date=datetime(2026, 7, 5, tzinfo=timezone.utc),  # after UNTIL
        )
        assert not parser.should_process(msg, since=self.SINCE, until=self.UNTIL)

    def test_no_date_bounds_only_subject_matters(self):
        msg = _make_email(subject="Receipt #999")
        assert parser.should_process(msg)

    def test_no_date_on_msg_passes_date_check(self):
        msg = ParsedEmail(
            uid="no-date",
            subject="Чек",
            from_address=Address(name="X", email="x@x.com"),
            body_text="",
            date=None,
        )
        assert parser.should_process(msg, since=self.SINCE, until=self.UNTIL)
