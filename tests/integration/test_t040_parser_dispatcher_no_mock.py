"""T-040: Integration tests — ReceiptParser + Dispatcher without mocks.

Tests that the real ReceiptParser + Dispatcher pipeline:
  - Enriches ParsedEmail with receipt_url from body_text
  - Enriches ParsedEmail with receipt_url from body_html (fallback)
  - Returns should_process=True for all CORPUS_POSITIVE fixtures
  - Returns should_process=False for CORPUS_NEGATIVE fixtures
    (excluding sender-based exclusion which requires from_addr)
  - Prefers body_text URL over body_html URL
  - Corpus covers 12 distinct cases (7 positive, 5 negative)

No unittest.mock, no patch, no MagicMock.
All assertions use real ReceiptParser and real Dispatcher instances.

Task: T-040
Epic: E-09 — Parsing Baseline to Production
"""
import pytest
from datetime import datetime, timezone

from packages.mail_core.parser import ReceiptParser
from packages.yandex_mail_agent.dispatcher import Dispatcher
from packages.mail_core.tests.fixtures.corpus import (
    CORPUS_POSITIVE,
    CORPUS_NEGATIVE,
    CORPUS_SENDER_EXCLUDED_UIDS,
    BASE_DATE,
)


# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def parser() -> ReceiptParser:
    """Real ReceiptParser instance — no mocks."""
    return ReceiptParser()


@pytest.fixture(scope="module")
def dispatcher(parser) -> Dispatcher:
    """Real Dispatcher with real ReceiptParser injected."""
    return Dispatcher(receipt_parser=parser)


# ---------------------------------------------------------------------------
# T-040-01: ReceiptParser enriches positive corpus
# ---------------------------------------------------------------------------

class TestReceiptParserEnriches:

    def test_corpus_positive_all_have_receipt_url(self, parser):
        """All positive fixtures must yield a non-None receipt_url after enrichment."""
        for msg in CORPUS_POSITIVE:
            enriched = parser.enrich(msg)
            assert enriched.receipt_url is not None, (
                f"uid={msg.uid}: expected receipt_url, got None. "
                f"subject={msg.subject!r} body_text={msg.body_text[:60]!r}"
            )

    def test_corpus_positive_url001_is_ofd_ru(self, parser):
        """uid=001: URL must be from ofd.ru."""
        msg = next(m for m in CORPUS_POSITIVE if m.uid == "001")
        enriched = parser.enrich(msg)
        assert "ofd.ru/r/aaa111bbb222" in enriched.receipt_url

    def test_corpus_positive_url002_html_fallback(self, parser):
        """uid=002: body_text has no URL, must fall back to body_html."""
        msg = next(m for m in CORPUS_POSITIVE if m.uid == "002")
        enriched = parser.enrich(msg)
        assert "check.ofd.ru" in enriched.receipt_url

    def test_corpus_positive_url003_consumer_rnko(self, parser):
        """uid=003: consumer.rnko.ru URL must be extracted."""
        msg = next(m for m in CORPUS_POSITIVE if m.uid == "003")
        enriched = parser.enrich(msg)
        assert "consumer.rnko.ru" in enriched.receipt_url

    def test_corpus_positive_url004_platformaofd(self, parser):
        """uid=004: 1k.platformaofd.ru URL must be extracted."""
        msg = next(m for m in CORPUS_POSITIVE if m.uid == "004")
        enriched = parser.enrich(msg)
        assert "platformaofd.ru" in enriched.receipt_url

    def test_corpus_positive_url007_prefers_text_over_html(self, parser):
        """uid=007: when both text and html have URLs, body_text URL wins."""
        msg = next(m for m in CORPUS_POSITIVE if m.uid == "007")
        enriched = parser.enrich(msg)
        assert "text-url-mmm333" in enriched.receipt_url
        assert "html-url-nnn444" not in enriched.receipt_url

    def test_corpus_negative_008_no_url(self, parser):
        """uid=008: receipt subject but no OFD URL — receipt_url must be None."""
        msg = next(m for m in CORPUS_NEGATIVE if m.uid == "008")
        enriched = parser.enrich(msg)
        assert enriched.receipt_url is None

    def test_corpus_negative_012_unrelated(self, parser):
        """uid=012: unrelated email — receipt_url must be None."""
        msg = next(m for m in CORPUS_NEGATIVE if m.uid == "012")
        enriched = parser.enrich(msg)
        assert enriched.receipt_url is None


# ---------------------------------------------------------------------------
# T-040-02: Dispatcher.dispatch() with real ReceiptParser
# ---------------------------------------------------------------------------

class TestDispatcherWithRealParser:

    def test_positive_corpus_all_should_process(self, dispatcher):
        """All 7 positive fixtures must produce should_process=True."""
        since = datetime(2026, 6, 1, tzinfo=timezone.utc)
        until = datetime(2026, 6, 30, tzinfo=timezone.utc)
        failures = []
        for msg in CORPUS_POSITIVE:
            decision = dispatcher.dispatch(msg, since=since, until=until)
            if not decision.should_process:
                failures.append(f"uid={msg.uid} subject={msg.subject!r} reason={decision.reason!r}")
        assert not failures, "Positive fixtures failed dispatch:\n" + "\n".join(failures)

    def test_negative_corpus_no_url_not_processed(self, dispatcher):
        """uid=008 (receipt subject, no URL) — should_process=False."""
        since = datetime(2026, 6, 1, tzinfo=timezone.utc)
        until = datetime(2026, 6, 30, tzinfo=timezone.utc)
        msg = next(m for m in CORPUS_NEGATIVE if m.uid == "008")
        decision = dispatcher.dispatch(msg, since=since, until=until)
        assert not decision.should_process

    def test_negative_corpus_newsletter_not_processed(self, dispatcher):
        """uid=010 (newsletter) — should_process=False."""
        since = datetime(2026, 6, 1, tzinfo=timezone.utc)
        until = datetime(2026, 6, 30, tzinfo=timezone.utc)
        msg = next(m for m in CORPUS_NEGATIVE if m.uid == "010")
        decision = dispatcher.dispatch(msg, since=since, until=until)
        assert not decision.should_process

    def test_negative_corpus_unrelated_not_processed(self, dispatcher):
        """uid=012 (unrelated) — should_process=False."""
        since = datetime(2026, 6, 1, tzinfo=timezone.utc)
        until = datetime(2026, 6, 30, tzinfo=timezone.utc)
        msg = next(m for m in CORPUS_NEGATIVE if m.uid == "012")
        decision = dispatcher.dispatch(msg, since=since, until=until)
        assert not decision.should_process

    def test_out_of_date_range_not_processed(self, dispatcher):
        """Positive fixture outside date window — should_process=False."""
        since = datetime(2025, 1, 1, tzinfo=timezone.utc)
        until = datetime(2025, 12, 31, tzinfo=timezone.utc)
        msg = CORPUS_POSITIVE[0]  # uid=001, date=2026-06-10
        decision = dispatcher.dispatch(msg, since=since, until=until)
        assert not decision.should_process

    def test_dispatch_decision_has_reason_string(self, dispatcher):
        """DispatchDecision.reason must be a non-empty string."""
        since = datetime(2026, 6, 1, tzinfo=timezone.utc)
        until = datetime(2026, 6, 30, tzinfo=timezone.utc)
        msg = CORPUS_POSITIVE[0]
        decision = dispatcher.dispatch(msg, since=since, until=until)
        assert isinstance(decision.reason, str) and len(decision.reason) > 0


# ---------------------------------------------------------------------------
# T-040-03: Corpus coverage sanity check
# ---------------------------------------------------------------------------

class TestCorpusCoverage:

    def test_positive_corpus_size(self):
        """Must have at least 7 positive fixtures."""
        assert len(CORPUS_POSITIVE) >= 7

    def test_negative_corpus_size(self):
        """Must have at least 4 negative fixtures (excluding sender-only)."""
        non_sender = [m for m in CORPUS_NEGATIVE if m.uid not in CORPUS_SENDER_EXCLUDED_UIDS]
        assert len(non_sender) >= 4

    def test_all_uids_unique(self):
        """All fixture UIDs must be unique across the corpus."""
        from packages.mail_core.tests.fixtures.corpus import CORPUS_ALL
        uids = [m.uid for m in CORPUS_ALL]
        assert len(uids) == len(set(uids)), "Duplicate UIDs found in corpus"

    def test_all_fixtures_have_date(self):
        """All corpus fixtures must have a non-None date."""
        from packages.mail_core.tests.fixtures.corpus import CORPUS_ALL
        for msg in CORPUS_ALL:
            assert msg.date is not None, f"uid={msg.uid} has no date"
