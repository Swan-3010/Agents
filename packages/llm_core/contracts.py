"""LLM Core Contracts (T-019)."""
from dataclasses import dataclass, field
from typing import Protocol, List, Dict, Any, Optional

@dataclass
class LLMPrompt:
    text: str
    context: Dict[str, Any] = field(default_factory=dict)
    max_tokens: int = 1000

@dataclass
class LLMResponse:
    text: str
    tokens_used: int
    model: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ExtractionResult:
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    error: Optional[str] = None

class ILLMProvider(Protocol):
    def generate(self, prompt: LLMPrompt) -> LLMResponse: ...
    def extract_structured(self, prompt: LLMPrompt, schema: Dict) -> ExtractionResult: ...
