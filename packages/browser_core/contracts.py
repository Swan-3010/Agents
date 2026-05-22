"""Browser Core Contracts - DTO and Protocols for browser automation.

Task: T-017 - Реализовать browser_core interfaces
Epic: E-04 - Core Interfaces
"""

from dataclasses import dataclass, field
from typing import Protocol, List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class BrowserType(Enum):
    CHROME = "chrome"
    FIREFOX = "firefox"
    EDGE = "edge"


@dataclass
class BrowserConfig:
    """Browser configuration."""
    browser_type: BrowserType = BrowserType.CHROME
    headless: bool = True
    window_width: int = 1920
    window_height: int = 1080
    timeout_seconds: int = 30
    user_agent: Optional[str] = None
    proxy: Optional[str] = None


@dataclass
class PageSnapshot:
    """Snapshot of a web page."""
    url: str
    title: str
    html_content: str
    screenshot_base64: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    cookies: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BrowserAction:
    """Browser action representation."""
    action_type: str  # click, type, navigate, scroll
    target: str  # CSS selector or URL
    value: Optional[str] = None
    wait_after: float = 0.5


@dataclass
class BrowserSession:
    """Browser session info."""
    session_id: str
    config: BrowserConfig
    started_at: datetime
    current_url: Optional[str] = None
    is_active: bool = True


class IBrowserDriver(Protocol):
    """Protocol for browser driver."""
    
    def start(self, config: BrowserConfig) -> BrowserSession:
        """Start browser session."""
        ...
    
    def stop(self) -> None:
        """Stop browser session."""
        ...
    
    def navigate(self, url: str) -> bool:
        """Navigate to URL."""
        ...
    
    def execute_action(self, action: BrowserAction) -> bool:
        """Execute browser action."""
        ...
    
    def capture_snapshot(self) -> PageSnapshot:
        """Capture page snapshot."""
        ...
