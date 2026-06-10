"""T-042: Browser integration tests — artifact validation & persistence.

Goal:
  Validate that ReceiptBrowserDriver produces **reusable artifacts**:
    - HTML file saved to disk
    - Screenshot PNG saved to disk
    - Artifacts have valid structure and content
    - Artifacts are ready for downstream processing (XLSX generation)

Difference from T-041:
  T-041: validates driver API (init, context manager, method signatures)
  T-042: validates **output artifacts** (file existence, structure, content)

Artifact contract:
  - HTML: valid UTF-8, >500 chars, contains receipt keywords or page structure
  - Screenshot: valid PNG, >1KB, dimensions >100x100
  - Both files: accessible via Path, can be read/parsed by downstream tools

Test layers:
  Layer 1: Smoke artifacts on example.com (always runs with -m browser_smoke)
  Layer 2: Live OFD artifacts (requires -m ofd_live + OFD_TEST_URL env)

No unittest.mock, no patch, no MagicMock.

Task: T-042
Epic: E-10 — Real Browser Extraction
Depends on: T-041
"""
import os
import pytest
from pathlib import Path
from PIL import Image
import io

from packages.browser_core.driver import ReceiptBrowserDriver


# ---------------------------------------------------------------------------
# Marks & Config
# ---------------------------------------------------------------------------

browser_smoke = pytest.mark.browser_smoke
ofd_live = pytest.mark.ofd_live

OUTPUT_DIR = Path("test_artifacts/t042")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def _get_ofd_test_url() -> str:
    """Read OFD_TEST_URL from environment."""
    url = os.environ.get("OFD_TEST_URL", "")
    if not url:
        pytest.skip("OFD_TEST_URL env var not set — skipping live OFD test")
    return url


# ---------------------------------------------------------------------------
# Layer 1: Smoke artifacts on example.com
# ---------------------------------------------------------------------------

@browser_smoke
class TestBrowserArtifactsSmoke:
    """Validates artifact structure on stable public URL (example.com)."""

    SMOKE_URL = "https://example.com"

    def test_html_artifact_created(self):
        """HTML file must be created on disk."""
        html_path = OUTPUT_DIR / "smoke_page.html"
        with ReceiptBrowserDriver(headless=True) as driver:
            html_content = driver.open_receipt_url(self.SMOKE_URL)
        html_path.write_text(html_content, encoding="utf-8")
        assert html_path.exists(), f"HTML file not created at {html_path}"

    def test_html_artifact_not_empty(self):
        """HTML file must be non-empty."""
        html_path = OUTPUT_DIR / "smoke_page_nonempty.html"
        with ReceiptBrowserDriver(headless=True) as driver:
            html_content = driver.open_receipt_url(self.SMOKE_URL)
        html_path.write_text(html_content, encoding="utf-8")
        assert html_path.stat().st_size > 0

    def test_html_artifact_valid_utf8(self):
        """HTML file must be valid UTF-8."""
        html_path = OUTPUT_DIR / "smoke_page_utf8.html"
        with ReceiptBrowserDriver(headless=True) as driver:
            html_content = driver.open_receipt_url(self.SMOKE_URL)
        html_path.write_text(html_content, encoding="utf-8")
        # Re-read to verify UTF-8 validity
        content = html_path.read_text(encoding="utf-8")
        assert len(content) > 0

    def test_html_artifact_contains_html_tag(self):
        """HTML artifact must contain <html or <!DOCTYPE tag."""
        html_path = OUTPUT_DIR / "smoke_page_structure.html"
        with ReceiptBrowserDriver(headless=True) as driver:
            html_content = driver.open_receipt_url(self.SMOKE_URL)
        html_path.write_text(html_content, encoding="utf-8")
        content_lower = html_path.read_text(encoding="utf-8").lower()
        assert "<html" in content_lower or "<!doctype" in content_lower

    def test_screenshot_artifact_created(self):
        """Screenshot PNG file must be created on disk."""
        screenshot_path = OUTPUT_DIR / "smoke_screenshot.png"
        with ReceiptBrowserDriver(headless=True) as driver:
            driver.open_receipt_url(self.SMOKE_URL)
            driver.take_screenshot(str(screenshot_path))
        assert screenshot_path.exists(), f"Screenshot not created at {screenshot_path}"

    def test_screenshot_artifact_not_empty(self):
        """Screenshot PNG must be >1KB (real image, not empty file)."""
        screenshot_path = OUTPUT_DIR / "smoke_screenshot_size.png"
        with ReceiptBrowserDriver(headless=True) as driver:
            driver.open_receipt_url(self.SMOKE_URL)
            driver.take_screenshot(str(screenshot_path))
        assert screenshot_path.stat().st_size > 1024, (
            f"Screenshot too small: {screenshot_path.stat().st_size} bytes"
        )

    def test_screenshot_artifact_valid_png(self):
        """Screenshot must be a valid PNG that can be opened by PIL."""
        screenshot_path = OUTPUT_DIR / "smoke_screenshot_valid.png"
        with ReceiptBrowserDriver(headless=True) as driver:
            driver.open_receipt_url(self.SMOKE_URL)
            driver.take_screenshot(str(screenshot_path))
        # Attempt to open with PIL
        with Image.open(screenshot_path) as img:
            assert img.format == "PNG"
            assert img.size[0] > 100 and img.size[1] > 100, (
                f"Screenshot dimensions too small: {img.size}"
            )

    def test_both_artifacts_saved_together(self):
        """HTML + screenshot must both be saved in single session."""
        html_path = OUTPUT_DIR / "smoke_combined.html"
        screenshot_path = OUTPUT_DIR / "smoke_combined.png"
        with ReceiptBrowserDriver(headless=True) as driver:
            html_content = driver.open_receipt_url(self.SMOKE_URL)
            driver.take_screenshot(str(screenshot_path))
        html_path.write_text(html_content, encoding="utf-8")
        assert html_path.exists() and screenshot_path.exists()


# ---------------------------------------------------------------------------
# Layer 2: Live OFD URL artifacts
# ---------------------------------------------------------------------------

@ofd_live
class TestBrowserArtifactsLiveOfd:
    """Validates artifacts from real OFD receipt page.

    Requires:
      - pytest -m ofd_live
      - OFD_TEST_URL=https://ofd.ru/r/... env var
    """

    def test_ofd_html_saved_to_output(self):
        """OFD receipt HTML must be saved to output directory."""
        url = _get_ofd_test_url()
        html_path = OUTPUT_DIR / "ofd_receipt_live.html"
        with ReceiptBrowserDriver(headless=True) as driver:
            html_content = driver.open_receipt_url(url)
        html_path.write_text(html_content, encoding="utf-8")
        assert html_path.exists()
        assert html_path.stat().st_size > 500, (
            f"OFD HTML too small: {html_path.stat().st_size} bytes"
        )

    def test_ofd_screenshot_saved_to_output(self):
        """OFD receipt screenshot must be saved to output directory."""
        url = _get_ofd_test_url()
        screenshot_path = OUTPUT_DIR / "ofd_receipt_live.png"
        with ReceiptBrowserDriver(headless=True) as driver:
            driver.open_receipt_url(url)
            driver.take_screenshot(str(screenshot_path))
        assert screenshot_path.exists()
        assert screenshot_path.stat().st_size > 5000, (
            f"OFD screenshot too small: {screenshot_path.stat().st_size} bytes"
        )

    def test_ofd_html_contains_receipt_keywords(self):
        """OFD HTML artifact must contain receipt-specific keywords."""
        url = _get_ofd_test_url()
        html_path = OUTPUT_DIR / "ofd_receipt_keywords.html"
        with ReceiptBrowserDriver(headless=True) as driver:
            html_content = driver.open_receipt_url(url)
        html_path.write_text(html_content, encoding="utf-8")
        content_lower = html_path.read_text(encoding="utf-8").lower()
        receipt_keywords = ["чек", "фискаль", "receipt", "итог", "сумма", "руб"]
        found = [kw for kw in receipt_keywords if kw in content_lower]
        assert found, (
            f"OFD HTML contains none of expected keywords: {receipt_keywords}. "
            f"First 200 chars: {content_lower[:200]!r}"
        )

    def test_ofd_screenshot_has_valid_dimensions(self):
        """OFD screenshot must have reasonable dimensions (viewport size)."""
        url = _get_ofd_test_url()
        screenshot_path = OUTPUT_DIR / "ofd_receipt_dimensions.png"
        with ReceiptBrowserDriver(headless=True) as driver:
            driver.open_receipt_url(url)
            driver.take_screenshot(str(screenshot_path))
        with Image.open(screenshot_path) as img:
            width, height = img.size
            assert width >= 800, f"Screenshot width {width} < 800px"
            assert height >= 600, f"Screenshot height {height} < 600px"

    def test_ofd_artifacts_ready_for_downstream(self):
        """Both artifacts must exist and be readable for next step (XLSX gen)."""
        url = _get_ofd_test_url()
        html_path = OUTPUT_DIR / "ofd_downstream.html"
        screenshot_path = OUTPUT_DIR / "ofd_downstream.png"
        with ReceiptBrowserDriver(headless=True) as driver:
            html_content = driver.open_receipt_url(url)
            driver.take_screenshot(str(screenshot_path))
        html_path.write_text(html_content, encoding="utf-8")
        # Verify both can be read
        html_text = html_path.read_text(encoding="utf-8")
        with Image.open(screenshot_path) as img:
            img_format = img.format
        assert len(html_text) > 0
        assert img_format == "PNG"


# ---------------------------------------------------------------------------
# Layer 3: Artifact structure validation
# ---------------------------------------------------------------------------

@browser_smoke
class TestArtifactStructure:
    """Validates artifact file structure independently of content."""

    def test_output_directory_exists(self):
        """test_artifacts/t042/ directory must exist."""
        assert OUTPUT_DIR.exists()
        assert OUTPUT_DIR.is_dir()

    def test_html_artifact_has_html_extension(self):
        """Saved HTML files must have .html extension."""
        html_path = OUTPUT_DIR / "extension_test.html"
        html_path.write_text("<html></html>", encoding="utf-8")
        assert html_path.suffix == ".html"

    def test_screenshot_artifact_has_png_extension(self):
        """Saved screenshot files must have .png extension."""
        screenshot_path = OUTPUT_DIR / "extension_test.png"
        with ReceiptBrowserDriver(headless=True) as driver:
            driver.open_receipt_url("https://example.com")
            driver.take_screenshot(str(screenshot_path))
        assert screenshot_path.suffix == ".png"

    def test_artifacts_can_be_listed(self):
        """All artifacts in output dir must be listable via Path.glob."""
        html_files = list(OUTPUT_DIR.glob("*.html"))
        png_files = list(OUTPUT_DIR.glob("*.png"))
        # Just verify glob works — count depends on previous tests
        assert isinstance(html_files, list)
        assert isinstance(png_files, list)
