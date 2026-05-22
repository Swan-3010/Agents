"""State Core Contracts (T-020)."""
from dataclasses import dataclass, field
from typing import Protocol, Dict, Any, Optional
from datetime import datetime

@dataclass
class AgentState:
    agent_id: str
    status: str
    data: Dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class StateSnapshot:
    state: AgentState
    version: int
    timestamp: datetime

class IStateManager(Protocol):
    def save_state(self, state: AgentState) -> bool: ...
    def load_state(self, agent_id: str) -> Optional[AgentState]: ...
    def create_snapshot(self, agent_id: str) -> StateSnapshot: ...
