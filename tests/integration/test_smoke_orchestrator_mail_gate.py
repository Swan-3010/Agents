"""Модуль yandex_mail_agent.smoke_test_orchestrator - оркестратор для smoke-теста.

Используется для выполнения задачи T-031 / E-06:
- Координация всех компонентов Batch 9
- Полный цикл: IMAP → Playwright → XLSX → SMTP
- Создание сквозного smoke-теста
- Фильтрация писем через Dispatcher + ReceiptParser.should_process()
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

# Импорт компонентов Batch 9
try:
    from packages.mail_core.fetcher import ImapReceiptFetcher
    from packages.browser_core.driver import ReceiptBrowserDriver
    from packages.report_core.generator import ReceiptReportGenerator
    from packages.mail_core.sender import EmailSender
    from packages.yandex_mail_agent.dispatcher import Dispatcher
except ImportError:
    # Для разработки - относительный импорт
    from ..mail_core.fetcher import ImapReceiptFetcher
    from ..browser_core.driver import ReceiptBrowserDriver
    from ..report_core.generator import ReceiptReportGenerator
    from ..mail_core.sender import EmailSender
    from .dispatcher import Dispatcher

logger = logging.getLogger(__name__)


class SmokeTestOrchestrator:
    """Оркестратор для smoke-теста всей системы.

    Координирует:
    1. Получение писем с чеками (IMAP)
    2. Фильтрацию писем через Dispatcher / ReceiptParser
    3. Открытие чеков (Playwright)
    4. Генерацию отчета (XLSX)
    5. Отправку отчета (SMTP)
    """

    def __init__(self, dispatcher: Optional[Dispatcher] = None):
        """Инициализация оркестратора."""
        self.results: List[Dict[str, Any]] = []
        self.dispatcher = dispatcher or Dispatcher()
        logger.info("Инициализирован SmokeTestOrchestrator")

    def run_smoke_test(
        self,
        recipient_email: str,
        max_receipts: int = 5
    ) -> Dict[str, Any]:
        """Запуск полного smoke-теста.

        Args:
            recipient_email: Email для отправки отчета
            max_receipts: Максимальное количество чеков для обработки

        Returns:
            Результат выполнения: success, steps, errors
        """
        logger.info(f"Запуск smoke-теста для {recipient_email}")

        result = {
            "success": False,
            "start_time": datetime.now().isoformat(),
            "steps": [],
            "errors": []
        }

        try:
            logger.info("Шаг 1: Получение чеков из IMAP")
            receipts = self._fetch_receipts(max_receipts)
            result["steps"].append({
                "name": "fetch_receipts",
                "success": len(receipts) > 0,
                "count": len(receipts)
            })

            if not receipts:
                result["errors"].append("Не найдено чеков в IMAP после parser/dispatcher фильтрации")
                return result

            logger.info("Шаг 2: Открытие чеков через Playwright")
            receipt_details = self._process_receipts_with_browser(receipts)
            result["steps"].append({
                "name": "process_receipts",
                "success": len(receipt_details) > 0,
                "count": len(receipt_details)
            })

            if not receipt_details:
                result["errors"].append("Не удалось обработать ни одного чека в браузере")
                return result

            logger.info("Шаг 3: Генерация XLSX отчета")
            report_bytes = self._generate_xlsx_report(receipt_details)
            result["steps"].append({
                "name": "generate_report",
                "success": report_bytes is not None,
                "size_bytes": len(report_bytes) if report_bytes else 0
            })

            if not report_bytes:
                result["errors"].append("Ошибка генерации отчета")
                return result

            logger.info("Шаг 4: Отправка отчета по email")
            email_sent = self._send_report_email(recipient_email, report_bytes)
            result["steps"].append({
                "name": "send_email",
                "success": email_sent,
                "recipient": recipient_email
            })

            result["success"] = all(step["success"] for step in result["steps"])

        except Exception as e:
            logger.error(f"Ошибка выполнения smoke-теста: {e}")
            result["errors"].append(str(e))
        finally:
            result["end_time"] = datetime.now().isoformat()

        logger.info(f"Smoke-тест завершен: success={result['success']}")
        return result

    def _fetch_receipts(self, max_count: int) -> List[Dict[str, Any]]:
        """Получение чеков из IMAP с фильтрацией через Dispatcher / ReceiptParser."""
        try:
            fetcher = ImapReceiptFetcher()
            messages = fetcher.fetch_recent_messages(max_count)
            receipts = []

            for 
