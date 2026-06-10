"""T-041: Integration tests — ReceiptBrowserDriver on real URLs.

Test strategy:
  Layer 1 (always runs): Driver init, context manager, Chrome detection —
    no network required, validates local Playwright/Chrome setup.
  Layer 2 (requires network): open_receipt_url() on stable public pages —
    uses example.com and httpbin as proxy for real browser stack validation.
  Layer 3 (requires real OFD URL): marked with pytest.mark.ofd_live —
    skipped by default, activated with -m ofd_live + env OFD_TEST_URL.
    This is where the true receipt page validation will run once a real
    OFD URL is injected from the corpus or a live IMAP fetch.

Artifact contract:
  - HTML content: non-empty string, len > 0
  - Screenshot: file exists on disk, size > 0 bytes
  - Page title: non-empty string
  - receipt_url preserved end-to-end through ParsedEmail.receipt_url

No unittest.mock, no patch, no MagicMock.

Task: T-041
Epic: E-10 — Real Browser Extraction
"""
import os
import tempfile
import pytest
from pathlib import Path

from packages.browser_core.driver import ReceiptBrowserDriver
from packages.mail_core.tests.fixtures.corpus import CORPUS_POSITIVE


# ---------------------------------------------------------------------------
# Marks
# ---------------------------------------------------------------------------

# ofd_live: tests that require a real live OFD receipt URL
# Run with: pytest -m ofd_live
ofd_live = pytest.mark.ofd_live

# browser_smoke: tests that require Playwright + Chrome installed
# Skipped automatically if playwright is not available
browser_smoke = pytest.mark.browser_smoke


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_ofd_test_url() -> str:
    """Read OFD_TEST_URL from environment. Fail clearly if absent."""
    url = os.environ.get("OFD_TEST_URL", "")
    if not url:
        pytest.skip("OFD_TEST_URL env var not set — skipping live OFD test")
    return url


# ---------------------------------------------------------------------------
# Layer 1: Driver init — no network, validates local Playwright setup
# ---------------------------------------------------------------------------

class TestReceiptBrowserDriverInit:

    def test_driver_instantiates_headless(self):
        """ReceiptBrowserDriver can be instantiated without errors."""
        driver = ReceiptBrowserDriver(headless=True)
        assert driver is not None
        assert driver.headless is True

    def test_driver_instantiates_headed(self):
        """ReceiptBrowserDriver can be instantiated in headed mode."""
        driver = ReceiptBrowserDriver(headless=False)
        assert driver.headless is False

    def test_driver_initial_state_is_not_started(self):
        """Before start(), browser and page must be None."""
        driver = ReceiptBrowserDriver(headless=True)
        assert driver.browser is None
        assert driver.page is None

    def test_driver_find_chrome_returns_string_or_none(self):
        """_find_chrome() must return either str path or None — never raise."""
        driver = ReceiptBrowserDriver(headless=True)
        result = driver._find_chrome()
        assert result is None or isinstance(result, str)


# ---------------------------------------------------------------------------
# Layer 2: Real browser smoke on public stable URLs
# ---------------------------------------------------------------------------

@pytest.mark.browser_smoke
class TestReceiptBrowserDriverPublicUrls:
    """Uses example.com as a stable proxy to verify browser stack works."""

    SMOKE_URL = "https://example.com"
    SMOKE_TITLE_FRAGMENT = "Example Domain"

    def test_context_manager_starts_and_stops(self):
        """Context manager must start/stop without exceptions."""
        with ReceiptBrowserDriver(headless=True) as driver:
            assert driver.browser is not None
            assert driver.page is not None
        # After exit, page may be None or closed — no exception is the goal

    def test_open_receipt_url_returns_html_string(self):
        """open_receipt_url() must return non-empty HTML string."""
        with ReceiptBrowserDriver(headless=True) as driver:
            html = driver.open_receipt_url(self.SMOKE_URL)
        assert isinstance(html, str)
        assert len(html) > 0

    def test_open_receipt_url_contains_html_tag(self):
        """Returned content must contain <html tag (real page rendered)."""
        with ReceiptBrowserDriver(headless=True) as driver:
            html = driver.open_receipt_url(self.SMOKE_URL)
        assert "<html" in html.lower() or "<!doctype" in html.lower()

    def test_open_receipt_url_title_present(self):
        """Page HTML must contain expected title fragment."""
        with ReceiptBrowserDriver(headless=True) as driver:
            html = driver.open_receipt_url(self.SMOKE_URL)
        assert self.SMOKE_TITLE_FRAGMENT in html

    def test_take_screenshot_creates_file(self):
        """take_screenshot() must create a non-empty file on disk."""
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = os.path.join(tmpdir, "smoke_screenshot.png")
            with ReceiptBrowserDriver(headless=True) as driver:
                driver.open_receipt_url(self.SMOKE_URL)
                result_path = driver.take_screenshot(screenshot_path)
            assert os.path.exists(result_path)
            assert os.path.getsize(result_path) > 0

    def test_take_screenshot_returns_path_string(self):
        """take_screenshot() must return a string path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            screenshot_path = os.path.join(tmpdir, "path_test.png")
            with ReceiptBrowserDriver(headless=True) as driver:
                driver.open_receipt_url(self.SMOKE_URL)
                result = driver.take_screenshot(screenshot_path)
            assert isinstance(result, str)

    def test_second_url_can_be_opened_in_same_session(self):
        """Two sequential open_receipt_url() calls must both succeed."""
        with ReceiptBrowserDriver(headless=True) as driver:
            html1 = driver.open_receipt_url("https://example.com")
            html2 = driver.open_receipt_url("https://example.org")
        assert len(html1) > 0
        assert len(html2) > 0


# ---------------------------------------------------------------------------
# Layer 3: Live OFD URL tests (skipped by default)
# ---------------------------------------------------------------------------

@ofd_live
class TestReceiptBrowserDriverLiveOfd:
    """Requires OFD_TEST_URL env var and -m ofd_live marker.

    These tests validate the complete receipt page extraction flow
    on a real OFD URL from a real receipt email.

    To run:
        OFD_TEST_URL=https://ofd.ru/r/... pytest -m ofd_live -v
    """

    def test_live_url_returns_html(self):
        """Real OFD URL must return non-empty HTML."""
        url = _get_ofd_test_url()
        with ReceiptBrowserDriver(headless=True) as driver:
            html = driver.open_receipt_url(url)
        assert isinstance(html, str) and len(html) > 500, (
            f"Expected substantial HTML from OFD page, got {len(html)} chars"
        )

    def test_live_url_screenshot_saved(self):
        """Real OFD URL screenshot must be saved to disk."""
        url = _get_ofd_test_url()
        output_dir = Path("test_artifacts/t041")
        output_dir.mkdir(parents=True, exist_ok=True)
        screenshot_path = str(output_dir / "ofd_receipt.png")
        with ReceiptBrowserDriver(headless=True) as driver:
            driver.open_receipt_url(url)
            result_path = driver.take_screenshot(screenshot_path)
        assert os.path.exists(result_path)
        assert os.path.getsize(result_path) > 1000, "Screenshot too small — page may not have rendered"

    def test_live_url_html_contains_receipt_keywords(self):
        """OFD receipt page HTML must contain at least one known receipt keyword."""
        url = _get_ofd_test_url()
        receipt_keywords = ["чек", "фискаль", "receipt", "итог", "сумма", "руб"]
        with ReceiptBrowserDriver(headless=True) as driver:
            html = driver.open_receipt_url(url)
        html_lower = html.lower()
        found = [kw for kw in receipt_keywords if kw in html_lower]
        assert found, (
            f"Receipt page HTML contains none of expected keywords: {receipt_keywords}. "
            f"First 200 chars: {html[:200]!r}"
        )

    def test_live_url_html_saved_to_artifact(self):
        """OFD receipt HTML must be saved as artifact file."""
        url = _get_ofd_test_url()
        output_dir = Path("test_artifacts/t041")
        output_dir.mkdir(parents=True, exist_ok=True)
        html_path = output_dir / "ofd_receipt.html"
        with ReceiptBrowserDriver(headless=True) as driver:
            html = driver.open_receipt_url(url)
        html_path.write_text(html, encoding="utf-8")
        assert html_path.exists()
        assert html_path.stat().st_size > 0


# ---------------------------------------------------------------------------
# Layer 3b: Corpus URL pipeline — receipt_url from CORPUS_POSITIVE[0]
# ---------------------------------------------------------------------------

@ofd_live
class TestReceiptBrowserDriverFromCorpus:
    """Validates the full pipeline: ParsedEmail.receipt_url → browser → HTML.

    Uses urls from CORPUS_POSITIVE that point to real OFD domains.
    Skipped unless -m ofd_live is passed (URLs in corpus are anonymized
    and do not resolve — replace with real URLs before running).
    """

    def test_corpus_url_001_opens_in_browser(self):
        """CORPUS_POSITIVE uid=001 receipt_url must open via driver."""
        from packages.mail_core.parser import ReceiptParser
        parser = ReceiptParser()
        msg = next(m for m in CORPUS_POSITIVE if m.uid == "001")
        enriched = parser.enrich(msg)
        assert enriched.receipt_url, "No receipt_url extracted from uid=001"
        pytest.skip(
            f"Corpus URL {enriched.receipt_url!r} is anonymized — "
            "replace with real OFD URL to run this test"
        )
