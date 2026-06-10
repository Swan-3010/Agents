from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class MailSelectionRules:
    version: int = 1
    subject_include: list[str] = field(default_factory=list)
    subject_exclude: list[str] = field(default_factory=list)
    sender_exclude: list[str] = field(default_factory=list)
    body_domains: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MailSelectionRules":
        return cls(
            version=int(data.get("version", 1)),
            subject_include=list(data.get("subject_include", [])),
            subject_exclude=list(data.get("subject_exclude", [])),
            sender_exclude=list(data.get("sender_exclude", [])),
            body_domains=list(data.get("body_domains", [])),
        )


def default_rules_path() -> Path:
    return Path(__file__).resolve().parent / "resources" / "mail_selection_rules.yaml"


def load_mail_selection_rules(path: str | Path | None = None) -> MailSelectionRules:
    target = Path(path) if path else default_rules_path()
    with target.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return MailSelectionRules.from_dict(raw)


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def body_contains_known_domain(body_text: str | None, body_html: str | None, domains: list[str]) -> bool:
    haystack = f"{_normalize(body_text)}\n{_normalize(body_html)}"
    return any(domain.lower() in haystack for domain in domains)


def sender_is_excluded(sender: str | None, rules: MailSelectionRules) -> bool:
    sender_norm = _normalize(sender)
    return any(token.lower() in sender_norm for token in rules.sender_exclude)


def subject_matches(subject: str | None, rules: MailSelectionRules) -> bool:
    subject_norm = _normalize(subject)

    if any(token.lower() in subject_norm for token in rules.subject_exclude):
        return False

    return any(token.lower() in subject_norm for token in rules.subject_include)


def is_receipt_candidate(
    *,
    subject: str | None,
    sender: str | None,
    body_text: str | None,
    body_html: str | None,
    rules: MailSelectionRules,
) -> bool:
    if sender_is_excluded(sender, rules):
        return False

    if subject_matches(subject, rules):
        return True

    return body_contains_known_domain(body_text, body_html, rules.body_domains)
