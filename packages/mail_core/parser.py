"""mail_core.parser - Receipt URL extractor + mail filters.

Takes a ParsedEmail and enriches it with:
  - receipt_url   : first matching OFD/receipt URL found in body_text or body_html
  - receipt_sender: normalised sender address

Also provides stateless helpers:
  - subject_matches_receipt(subject) -> bool
  - is_within_date_range(dt, since, until) -> bool
  - should_process(msg, since, until) -> bool

Task: T-037 (mail parsing under TZ)
Epic: E-05 - Automated Tests Baseline
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from .models import ParsedEmail

# ---------------------------------------------------------------------------
# Known OFD / receipt URL patterns (ordered by specificity)
# ---------------------------------------------------------------------------
_RECEIPT_PATTERNS: list[str] = [
    r"https?://ofd\.ru/r/[\w\-]+",
    r"https?://check\.ofd\.ru/[\w\-/]+",
    r"https?://consumer\.rnko\.ru/[\w\-/]+",
    r"https?://1k\.platformaofd\.ru/[\w\-/]+",
    r"https?://[\w\.\-]+/[\w\-/]*(?:check|receipt|\u0447\u0435\u043a)[\w\-/]*",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in _RECEIPT_PATTERNS]

# ---------------------------------------------------------------------------
# Subject keywords that indicate a receipt/payment email
# ---------------------------------------------------------------------------
_SUBJECT_KEYWORDS: list[str] = [
    r"\u0447\u0435\u043a",          # чек
    r"\u043a\u0430\u0441\u0441\u043e\u0432\u044b\u0439",    # кассовый
    r"\u043f\u043e\u043a\u0443\u043f\u043a\u0430",    # покупка
    r"\u043e\u043f\u043b\u0430\u0442\u0430",       # оплата
    r"\u043f\u043b\u0430\u0442\u0435\u0436",       # плат\u0435\u0436
    r"receipt",
    r"invoice",
    r"payment",
    r"purchase",
    r"order",
]

_SUBJECT_RE = re.compile(
    "|".join(_SUBJECT_KEYWORDS), re.IGNORECASE
)


class ReceiptParser:
    """Stateless parser: enriches a ParsedEmail with receipt metadata."""

    # ------------------------------------------------------------------
    # OFD URL extraction
    # ------------------------------------------------------------------

    def enrich(self, msg: ParsedEmail) -> ParsedEmail:
        """Return a copy of *msg* with receipt_url and receipt_sender filled."""
        url = None
        for source in (msg.body_text, msg.body_html):
            if source:
                url = self._extract_url(source)
                if url:
                    break

        sender = (
            msg.from_address.email
            if msg.from_address and msg.from_address.email
            else None
        )

        return msg.model_copy(
            update={"receipt_url": url, "receipt_sender": sender}
        )

    @staticmethod
    def _extract_url(text: str) -> Optional[str]:
        """Return first OFD/receipt URL found in *text*, or None."""
        for pattern in _COMPILED:
            m = pattern.search(text)
            if m:
                return m.group(0)
        return None

    @classmethod
    def extract_from_text(cls, text: str) -> Optional[str]:
        """One-shot: extract receipt URL from arbitrary text."""
        return cls._extract_url(text)

    # ------------------------------------------------------------------
    # Subject filter
    # ------------------------------------------------------------------

    @staticmethod
    def subject_matches_receipt(subject: str) -> bool:
        """Return True if *subject* contains a receipt-related keyword."""
        if not subject:
            return False
        return bool(_SUBJECT_RE.search(subject))

    # ------------------------------------------------------------------
    # Date range filter
    # ------------------------------------------------------------------

    @staticmethod
    def is_within_date_range(
        dt: datetime,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> bool:
        """Return True if *dt* falls within [since, until] (both inclusive, both optional).

        Naive datetimes are treated as UTC.
        """
        def _utc(d: datetime) -> datetime:
            if d.tzinfo is None:
                return d.replace(tzinfo=timezone.utc)
            return d

        dt = _utc(dt)
        if since and dt < _utc(since):
            return False
        if until and dt > _utc(until):
            return False
        return True

    # ------------------------------------------------------------------
    # Combined gate: should this email be processed?
    # ------------------------------------------------------------------

    def should_process(
        self,
        msg: ParsedEmail,
        since: Optional[datetime] = None,
        until: Optional[datetime] = None,
    ) -> bool:
        """Return True if *msg* passes subject filter AND date range filter.

        Used by the dispatcher to decide whether to hand a message
        to the receipt extraction pipeline.
        """
        if not self.subject_matches_receipt(msg.subject or ""):
            return False
        if msg.date and not self.is_within_date_range(msg.date, since, until):
            return False
        return True
