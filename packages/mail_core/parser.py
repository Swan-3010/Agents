from __future__ import annotations

import re
from dataclasses import dataclass

from .rules import MailSelectionRules, is_receipt_candidate, load_mail_selection_rules


OFD_URL_RE = re.compile(
    r"https?://[^\s\"'<>]+",
    re.IGNORECASE,
)


@dataclass(slots=True)
class ReceiptParser:
    rules: MailSelectionRules | None = None

    def __post_init__(self) -> None:
        if self.rules is None:
            self.rules = load_mail_selection_rules()

    def is_receipt_email(
        self,
        *,
        subject: str | None,
        sender: str | None,
        body_text: str | None,
        body_html: str | None,
    ) -> bool:
        return is_receipt_candidate(
            subject=subject,
            sender=sender,
            body_text=body_text,
            body_html=body_html,
            rules=self.rules,
        )

    def extract_first_receipt_link(self, content: str | None) -> str | None:
        if not content:
            return None

        for match in OFD_URL_RE.findall(content):
            if any(domain in match.lower() for domain in self.rules.body_domains):
                return match

        return None
