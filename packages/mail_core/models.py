"""mail_core.models - Pydantic-based normalized email structures.

Replaces the dataclass-based contracts.py DTO layer with Pydantic v2
models that provide validation, serialization and JSON schema export.

Task: T-031 (imap-tools refactor)
Epic: E-04 - Core Interfaces
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Primitive models
# ---------------------------------------------------------------------------

class Attachment(BaseModel):
    """A single email attachment."""

    filename: str
    content_type: str
    size_bytes: int = 0
    data: bytes = b""

    model_config = {"arbitrary_types_allowed": True}


class Address(BaseModel):
    """Email address optionally paired with a display name."""

    email: str
    name: Optional[str] = None

    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


# ---------------------------------------------------------------------------
# Core model: ParsedEmail
# ---------------------------------------------------------------------------

class ParsedEmail(BaseModel):
    """Normalized representation of a single email message.

    Built from an imap_tools.MailMessage object by MailClient.
    Serves as the single internal DTO that all downstream modules
    (parser, llm_core, report_core) consume.
    """

    uid: str = Field(..., description="IMAP UID as string")
    message_id: str = ""
    subject: str = ""
    from_addr: Optional[Address] = None
    to_addrs: List[Address] = Field(default_factory=list)
    cc_addrs: List[Address] = Field(default_factory=list)
    date: Optional[datetime] = None
    body_text: str = ""
    body_html: str = ""
    attachments: List[Attachment] = Field(default_factory=list)
    folder: str = "INBOX"
    is_seen: bool = False
    flags: List[str] = Field(default_factory=list)

    # Derived / enriched fields set by ReceiptParser
    receipt_url: Optional[str] = None
    receipt_sender: Optional[str] = None

    @field_validator("uid", mode="before")
    @classmethod
    def coerce_uid(cls, v: object) -> str:
        return str(v)

    @property
    def is_receipt(self) -> bool:
        """True when a receipt URL has been extracted."""
        return self.receipt_url is not None

    def __repr__(self) -> str:
        return (
            f"ParsedEmail(uid={self.uid!r}, "
            f"subject={self.subject!r}, "
            f"receipt_url={self.receipt_url!r})"
        )


# ---------------------------------------------------------------------------
# Search / fetch configuration
# ---------------------------------------------------------------------------

class FetchConfig(BaseModel):
    """Parameters that drive MailClient.fetch_messages()."""

    folder: str = "INBOX"
    sender_filter: Optional[str] = None          # e.g. 'noreply@check.yandex.ru'
    subject_filter: Optional[str] = None
    unseen_only: bool = False
    max_count: Optional[int] = None              # None = fetch all matching
    mark_seen: bool = False                      # write-mode flag
    readonly: bool = True
