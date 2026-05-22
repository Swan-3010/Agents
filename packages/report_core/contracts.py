"""Report Core Contracts (T-018)."""
from dataclasses import dataclass, field
from typing import Protocol, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class ReportFormat(Enum):
    PDF = "pdf"
    HTML = "html"
    JSON = "json"

@dataclass
class ReportRequest:
    report_type: str
    format: ReportFormat
    parameters: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ReportArtifact:
    artifact_id: str
    content: bytes
    file_name: str
    generated_at: datetime

@dataclass
class ReportResult:
    success: bool
    artifact: Optional[ReportArtifact] = None
    error: Optional[str] = None

class IReportGenerator(Protocol):
    def generate(self, req: ReportRequest) -> ReportResult: ...
