"""E2E stubs: daily agent run.

Test categories:
- e2e/TC-301: Полный цикл агента завершается без ошибок
- e2e/TC-302: XLSX-файл создан после цикла
- e2e/TC-303: Отчёт отправлен по SMTP
- e2e/TC-304: Агент не падает при ошибке парсинга одного чека
"""

import pytest


# e2e/TC-301
def test_full_agent_run_no_errors() -> None:
    """STUB: Полный цикл агента завершается с AgentRunResult.errors == []."""
    pytest.skip("stub — requires full environment")


# e2e/TC-302
def test_xlsx_file_created_after_run() -> None:
    """STUB: XLSX-файл создан после цикла."""
    pytest.skip("stub — requires full environment")


# e2e/TC-303
def test_smtp_report_sent() -> None:
    """STUB: Отчёт отправлен по SMTP."""
    pytest.skip("stub — requires full environment")


# e2e/TC-304
def test_agent_survives_parse_error() -> None:
    """STUB: Агент не падает при ошибке парсинга одного чека."""
    pytest.skip("stub — requires full environment")
