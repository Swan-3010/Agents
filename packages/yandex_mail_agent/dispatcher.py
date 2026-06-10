"""Dispatcher — маршрутизация писем по правилам."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from packages.mail_core.parser import ReceiptParser


@dataclass(slots=True)
class DispatchDecision:
    should_process: bool
    reason: str
    message_id: str | None = None


@dataclass(slots=True)
class Dispatcher:
    receipt_parser: ReceiptParser | None = None

    def __post_init__(self) -> None:
        if self.receipt_parser is None:
            self.receipt_parser = ReceiptParser()

    def should_process(
        self,
        msg: Any,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> bool:
        return self.receipt_parser.should_process(
            msg=msg,
            since=since,
            until=until,
        )

    def dispatch(
        self,
        msg: Any,
        *,
        since: datetime | None = None,
        until: datetime | None = None,
    ) -> DispatchDecision:
        approved = self.should_process(
            msg,
            since=since,
            until=until,
        )

        if not approved:
            return DispatchDecision(
                should_process=False,
                reason="filtered_by_receipt_parser",
                message_id=getattr(msg, "uid", None) or getattr(msg, "message_id", None),
            )

        return DispatchDecision(
            should_process=True,
            reason="approved_by_receipt_parser",
            message_id=getattr(msg, "uid", None) or getattr(msg, "message_id", None),
        )
