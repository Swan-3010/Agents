from dataclasses import dataclass, field
from typing import Optional


@dataclass(slots=True)
class ReceiptParseRequest:
    message_text: str
    message_subject: Optional[str] = None
    message_from: Optional[str] = None


@dataclass(slots=True)
class ReceiptParseResult:
    store_name: Optional[str] = None
    total_amount: Optional[str] = None
    currency: Optional[str] = None
    receipt_url: Optional[str] = None
    confidence: float = 0.0
    raw_llm_response: Optional[str] = None
    errors: list[str] = field(default_factory=list)
