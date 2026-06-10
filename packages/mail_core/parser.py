"""mail_core.parser - Receipt URL extractor.

Takes a ParsedEmail and enriches it with:
  - receipt_url  : first matching OFD/receipt URL found in body_text or body_html
  - receipt_sender: normalised sender address

Task: T-031 (imap-tools refactor)
Epic: E-04 - Core Interfaces
"""

from __future__ import annotations

import re
from typing import Optional

from .models import ParsedEmail

# ---------------------------------------------------------------------------
# Known OFD / receipt URL patterns (ordered by specificity)
# ---------------------------------------------------------------------------
_RECEIPT_PATTERNS: list[str] = [
    r"https?://ofd\.ru/r/[\w\-]+",
    r"https?://check\.ofd\.ru/[\w\-/]+",
    r"https?://consumer\.rnko\.ru/[\w\-/]+",
    r"https?://lk\.platformaofd\.ru/[\w\-/]+",
    r"https?://[\w\.-]+/[\w\-/]*(?:check|receipt|\u0447\u0435\u043a)[\w\-/]*",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _RECEIPT_PATTERNS]


class ReceiptParser:
    """Stateless parser: enriches a ParsedEmail with receipt metadata."""

    def enrich(self, msg: ParsedEmail) -> ParsedEmail:
        """Return the same ParsedEmail object with receipt_url / receipt_sender filled.

        Args:
            msg: ParsedEmail produced by MailClient.

        Returns:
            The same object, mutated in-place (receipt_url, receipt_sender set).
        """
        msg.receipt_url = self._extract_url(msg.body_text) or self._extract_url(
            msg.body_html
        )
        if msg.from_addr:
            msg.receipt_sender = msg.from_addr.email.lower()
        return msg

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_url(text: str) -> Optional[str]:
        """Scan *text* and return the first receipt URL found, or None."""
        if not text:
            return None
        for pattern in _COMPILED:
            m = pattern.search(text)
            if m:
                return m.group(0)
        return None

    # Convenience class-method for one-shot use
    @classmethod
    def extract_from_text(cls, text: str) -> Optional[str]:
        """Extract a receipt URL directly from a text string (no ParsedEmail needed)."""
        return cls._extract_url(text)
