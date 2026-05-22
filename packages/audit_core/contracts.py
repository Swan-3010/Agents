"""Audit Core Contracts (T-021)."""
from dataclasses import dataclass, field
from typing import Protocol, Dict, Any, List
from datetime import datetime
from enum import Enum

class AuditLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

@dataclass
class AuditEvent:
    event_id: str
    level: AuditLevel
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AuditLog:
    log_id: str
    events: List[AuditEvent] = field(default_factory=list)

class IAuditLogger(Protocol):
    def log_event(self, event: AuditEvent) -> bool: ...
    def query_events(self, filters: Dict[str, Any]) -> List[AuditEvent]: ...
