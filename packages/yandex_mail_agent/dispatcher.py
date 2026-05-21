"""Dispatcher — маршрутизация писем по правилам."""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from .contracts import MailMessage

logger = logging.getLogger(__name__)

Action = str


@dataclass
class DispatchRule:
    """Rule: если predicate(письмо) == True → вернуть action."""
    name: str
    predicate: Callable[[MailMessage], bool]
    action: Action
    priority: int = 0


class Dispatcher:
    """Проходит по правилам и возвращает action для письма."""

    def __init__(self) -> None:
        self._rules: List[DispatchRule] = self._default_rules()

    def dispatch(self, msg: MailMessage) -> Action:
        for rule in sorted(self._rules, key=lambda r: -r.priority):
            try:
                if rule.predicate(msg):
                    logger.debug(
                        "[Dispatcher] rule=%s action=%s subject=%r",
                        rule.name, rule.action, msg.subject,
                    )
                    return rule.action
            except Exception as exc:  # noqa: BLE001
                logger.warning("[Dispatcher] rule=%s error: %s", rule.name, exc)
        return "skip"

    def add_rule(self, rule: DispatchRule) -> None:
        self._rules.append(rule)

    @staticmethod
    def _default_rules() -> List[DispatchRule]:
        return [
            DispatchRule(
                name="receipt_subject",
                predicate=lambda m: bool(
                    re.search(
                        r"чек|receipt|order|заказ",
                        m.subject,
                        re.IGNORECASE,
                    )
                ),
                action="process_receipt",
                priority=10,
            ),
            DispatchRule(
                name="receipt_sender",
                predicate=lambda m: bool(
                    re.search(r"check\.yandex\.ru|noreply@check", m.sender, re.IGNORECASE)
                ),
                action="process_receipt",
                priority=15,
            ),
            DispatchRule(
                name="no_reply",
                predicate=lambda m: "no-reply" in m.sender.lower()
                or "noreply" in m.sender.lower(),
                action="skip",
                priority=5,
            ),
            DispatchRule(
                name="empty_body",
                predicate=lambda m: not (m.body_text or "").strip(),
                action="skip",
                priority=1,
            ),
        ]
