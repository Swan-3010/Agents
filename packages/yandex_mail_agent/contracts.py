"""Reusable Pydantic contracts for Yandex Mail Agent."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, HttpUrl


class MailMessage(BaseModel):
    """Represents a single email message fetched via IMAP."""

    uid: str
    subject: str
    sender: str
    received_at: datetime
    body_text: Optional[str] = None
    body_html: Optional[str] = None


class Receipt(BaseModel):
    """Parsed receipt extracted from a mail message."""

    uid: str
    sender: str
    received_at: datetime
    store_name: Optional[str] = None
    total_amount: Optional[float] = None
    currency: str = "RUB"
    receipt_url: Optional[HttpUrl] = None
    raw_text: Optional[str] = None


class AgentRunResult(BaseModel):
    """Result of a single agent execution cycle."""

    run_id: str
    started_at: datetime
    finished_at: datetime
    messages_fetched: int
    receipts_parsed: int
    errors: list[str] = []
    xlsx_path: Optional[str] = None
    report_path: Optional[str] = None
