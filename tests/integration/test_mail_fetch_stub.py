"""INTEGRATION stubs: IMAP mail fetch.

Test categories:
- integration/TC-101: IMAP подключение успешно
- integration/TC-102: Получение писем от noreply@check.yandex.ru
- integration/TC-103: Пустой INBOX возвращает пустой список
"""

import pytest


# integration/TC-101
def test_imap_connect_success() -> None:
    """STUB: IMAP подключение к imap.yandex.ru:993 успешно."""
    pytest.skip("stub — requires live IMAP credentials")


# integration/TC-102
def test_imap_fetch_receipts() -> None:
    """STUB: Получение писем от noreply@check.yandex.ru."""
    pytest.skip("stub — requires live IMAP credentials")


# integration/TC-103
def test_imap_empty_inbox_returns_empty_list() -> None:
    """STUB: Пустой INBOX возвращает []."""
    pytest.skip("stub — requires live IMAP credentials")
