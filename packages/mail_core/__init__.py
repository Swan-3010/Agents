"""mail_core - IMAP/SMTP layer built on imap-tools.

Public API:
    MailClient        - unified IMAP client (imap-tools-based)
    ParsedEmail       - normalized email model (Pydantic)
    ReceiptParser     - receipt-link extractor
    EmailSender       - SMTP sender (aiosmtplib)

Backward-compat aliases:
    YandexMailFetcher / ImapReceiptFetcher -> MailClient
"""

from .mail_client import MailClient
from .models import Address, Attachment, FetchConfig, ParsedEmail
from .parser import ReceiptParser
from .rules import MailSelectionRules, load_mail_selection_rules

# Backward-compat aliases (Batch 9 contracts)
YandexMailFetcher = MailClient
ImapReceiptFetcher = MailClient

__all__ = [
    "MailClient",
    "ParsedEmail",
    "Attachment",
    "Address",
    "FetchConfig",
    "ReceiptParser",
    "MailSelectionRules",
    "load_mail_selection_rules",
]
