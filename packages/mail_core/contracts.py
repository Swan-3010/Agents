"""Mail Core Contracts - DTO and Protocols for email operations.

This module defines data transfer objects and protocol interfaces
for working with email services (IMAP/SMTP).

Task: T-016 - Реализовать mail_core interfaces
Epic: E-04 - Core Interfaces
"""

from dataclasses import dataclass, field
from typing import Protocol, List, Optional
from datetime import datetime


# ============================================================================
# DTO: Mail Message Structures
# ============================================================================

@dataclass
class MailAttachment:
    """Email attachment representation."""
    filename: str
    content_type: str
    size_bytes: int
    data: bytes
    

@dataclass
class MailAddress:
    """Email address with name."""
    email: str
    name: Optional[str] = None
    
    def __str__(self) -> str:
        if self.name:
            return f"{self.name} <{self.email}>"
        return self.email


@dataclass
class MailMessage:
    """Complete email message representation."""
    message_id: str
    subject: str
    from_addr: MailAddress
    to_addrs: List[MailAddress]
    cc_addrs: List[MailAddress] = field(default_factory=list)
    bcc_addrs: List[MailAddress] = field(default_factory=list)
    date: datetime
    body_text: str = ""
    body_html: str = ""
    attachments: List[MailAttachment] = field(default_factory=list)
    headers: dict = field(default_factory=dict)
    is_read: bool = False
    is_flagged: bool = False
    folder: str = "INBOX"


@dataclass
class MailSearchCriteria:
    """Search criteria for filtering emails."""
    unseen_only: bool = True
    from_addr: Optional[str] = None
    subject_contains: Optional[str] = None
    since_date: Optional[datetime] = None
    folder: str = "INBOX"
    max_results: Optional[int] = None


@dataclass
class MailSendRequest:
    """Request to send an email."""
    to_addrs: List[MailAddress]
    subject: str
    body_text: str = ""
    body_html: str = ""
    cc_addrs: List[MailAddress] = field(default_factory=list)
    bcc_addrs: List[MailAddress] = field(default_factory=list)
    attachments: List[MailAttachment] = field(default_factory=list)
    reply_to: Optional[MailAddress] = None


@dataclass
class MailOperationResult:
    """Result of mail operation (send, fetch, etc)."""
    success: bool
    message_count: int = 0
    messages: List[MailMessage] = field(default_factory=list)
    error_message: Optional[str] = None
    operation_time: Optional[datetime] = None


# ============================================================================
# Protocols: Mail Service Interfaces
# ============================================================================

class IMailFetcher(Protocol):
    """Protocol for fetching emails from server."""
    
    def connect(self, host: str, email: str, password: str, use_ssl: bool = True) -> bool:
        """Connect to mail server."""
        ...
    
    def disconnect(self) -> None:
        """Disconnect from mail server."""
        ...
    
    def fetch_messages(self, criteria: MailSearchCriteria) -> MailOperationResult:
        """Fetch messages matching criteria."""
        ...
    
    def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read."""
        ...
    
    def move_message(self, message_id: str, target_folder: str) -> bool:
        """Move message to another folder."""
        ...


class IMailSender(Protocol):
    """Protocol for sending emails."""
    
    def connect(self, host: str, email: str, password: str, port: int = 587) -> bool:
        """Connect to SMTP server."""
        ...
    
    def disconnect(self) -> None:
        """Disconnect from SMTP server."""
        ...
    
    def send_message(self, request: MailSendRequest) -> MailOperationResult:
        """Send email message."""
        ...


class IMailParser(Protocol):
    """Protocol for parsing email content."""
    
    def parse_message(self, raw_message: bytes) -> MailMessage:
        """Parse raw email bytes into MailMessage."""
        ...
    
    def extract_attachments(self, message: MailMessage) -> List[MailAttachment]:
        """Extract attachments from message."""
        ...
    
    def extract_text(self, message: MailMessage) -> str:
        """Extract plain text from message (prefer text over html)."""
        ...
