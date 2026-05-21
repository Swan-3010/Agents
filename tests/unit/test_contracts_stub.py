"""UNIT stubs: contracts validation.

Test categories:
- unit/TC-001: MailMessage создаётся с корректными полями
- unit/TC-002: Receipt создаётся с currency=RUB по умолчанию
- unit/TC-003: AgentRunResult.errors по умолчанию пустой список
- unit/TC-004: MailMessage валидация отсутствующего uid
"""

import pytest
from datetime import datetime
from packages.yandex_mail_agent.contracts import MailMessage, Receipt, AgentRunResult


# unit/TC-001
def test_mail_message_creation() -> None:
    """STUB: MailMessage создаётся с корректными полями."""
    pytest.skip("stub — not implemented yet")


# unit/TC-002
def test_receipt_default_currency() -> None:
    """STUB: Receipt.currency == 'RUB' по умолчанию."""
    pytest.skip("stub — not implemented yet")


# unit/TC-003
def test_agent_run_result_errors_default() -> None:
    """STUB: AgentRunResult.errors по умолчанию []"""
    pytest.skip("stub — not implemented yet")


# unit/TC-004
def test_mail_message_missing_uid_raises() -> None:
    """STUB: MailMessage без uid вызывает ValidationError."""
    pytest.skip("stub — not implemented yet")
