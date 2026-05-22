"""Модуль yandex_mail_agent.smoke_test_orchestrator - оркестратор для smoke-теста.

Используется для выполнения задачи T-031:
- Координация всех компонентов Batch 9
- Полный цикл: IMAP → Playwright → XLSX → SMTP
- Создание сквозного smoke-теста
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

# Импорт компонентов Batch 9
try:
    from packages.mail_core.fetcher import ImapReceiptFetcher
    from packages.browser_core.driver import ReceiptBrowserDriver
    from packages.report_core.generator import ReceiptReportGenerator
    from packages.mail_core.sender import EmailSender
except ImportError:
    # Для разработки - относительный импорт
    from ..mail_core.fetcher import ImapReceiptFetcher
    from ..browser_core.driver import ReceiptBrowserDriver
    from ..report_core.generator import ReceiptReportGenerator
    from ..mail_core.sender import EmailSender

logger = logging.getLogger(__name__)


class SmokeTestOrchestrator:
    """Оркестратор для smoke-теста всей системы.
    
    Координирует:
    1. Получение писем с чеками (IMAP)
    2. Открытие чеков (Playwright)
    3. Генерацию отчета (XLSX)
    4. Отправку отчета (SMTP)
    """
    
    def __init__(self):
        """Инициализация оркестратора."""
        self.results: List[Dict[str, Any]] = []
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
            # Шаг 1: Получение чеков из IMAP
            logger.info("Шаг 1: Получение чеков из IMAP")
            receipts = self._fetch_receipts(max_receipts)
            result["steps"].append({
                "name": "fetch_receipts",
                "success": len(receipts) > 0,
                "count": len(receipts)
            })
            
            if not receipts:
                result["errors"].append("Не найдено чеков в IMAP")
                return result
            
            # Шаг 2: Открытие чеков через Playwright
            logger.info("Шаг 2: Открытие чеков через Playwright")
            receipt_details = self._process_receipts_with_browser(receipts)
            result["steps"].append({
                "name": "process_receipts",
                "success": len(receipt_details) > 0,
                "count": len(receipt_details)
            })
            
            # Шаг 3: Генерация XLSX отчета
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
            
            # Шаг 4: Отправка отчета по email
            logger.info("Шаг 4: Отправка отчета по email")
            email_sent = self._send_report_email(recipient_email, report_bytes)
            result["steps"].append({
                "name": "send_email",
                "success": email_sent,
                "recipient": recipient_email
            })
            
            # Успех только если все шаги пройдены
            result["success"] = all(step["success"] for step in result["steps"])
            
        except Exception as e:
            logger.error(f"Ошибка выполнения smoke-теста: {e}")
            result["errors"].append(str(e))
        finally:
            result["end_time"] = datetime.now().isoformat()
        
        logger.info(f"Smoke-тест завершен: success={result['success']}")
        return result
    
    def _fetch_receipts(self, max_count: int) -> List[Dict[str, Any]]:
        """Получение чеков из IMAP."""
        try:
            fetcher = ImapReceiptFetcher()
            messages = fetcher.fetch_recent_messages(max_count)
            receipts = []
            
            for msg in messages:
                receipt_url = fetcher.extract_receipt_link(msg)
                if receipt_url:
                    receipts.append({
                        "url": receipt_url,
                        "subject": msg.get("subject", "")
                    })
            
            logger.info(f"Получено {len(receipts)} чеков")
            return receipts
        except Exception as e:
            logger.error(f"Ошибка получения чеков: {e}")
            return []
    
    def _process_receipts_with_browser(self, receipts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Обработка чеков через Playwright."""
        details = []
        
        try:
            with ReceiptBrowserDriver(headless=True) as driver:
                for receipt in receipts:
                    try:
                        result = driver.open_receipt(receipt["url"])
                        if result["success"]:
                            details.append({
                                "Тема": receipt.get("subject", ""),
                                "URL": receipt["url"],
                                "Заголовок": result.get("title", ""),
                                "Статус": "Успех"
                            })
                        else:
                            details.append({
                                "Тема": receipt.get("subject", ""),
                                "URL": receipt["url"],
                                "Статус": "Ошибка",
                                "Описание": result.get("error", "")
                            })
                    except Exception as e:
                        logger.error(f"Ошибка обработки чека {receipt['url']}: {e}")
                        details.append({
                            "Тема": receipt.get("subject", ""),
                            "URL": receipt["url"],
                            "Статус": "Ошибка",
                            "Описание": str(e)
                        })
            
            logger.info(f"Обработано {len(details)} чеков")
        except Exception as e:
            logger.error(f"Ошибка инициализации браузера: {e}")
        
        return details
    
    def _generate_xlsx_report(self, receipt_details: List[Dict[str, Any]]) -> Optional[bytes]:
        """Генерация XLSX отчета."""
        try:
            generator = ReceiptReportGenerator(sheet_name="Smoke Test")
            generator.add_multiple_receipts(receipt_details)
            report_bytes = generator.save_to_bytes()
            logger.info(f"Отчет сгенерирован: {len(report_bytes)} bytes")
            return report_bytes
        except Exception as e:
            logger.error(f"Ошибка генерации отчета: {e}")
            return None
    
    def _send_report_email(self, recipient: str, report_bytes: bytes) -> bool:
        """Отправка отчета по email."""
        try:
            sender = EmailSender()
            success = sender.send_report(
                to_email=recipient,
                subject="Smoke Test: Отчет о чеках",
                report_content=report_bytes,
                report_filename="smoke_test_receipts.xlsx"
            )
            return success
        except Exception as e:
            logger.error(f"Ошибка отправки email: {e}")
            return False


def run_smoke_test(recipient_email: str, max_receipts: int = 5) -> Dict[str, Any]:
    """Вспомогательная функция для запуска smoke-теста.
    
    Args:
        recipient_email: Email для отправки отчета
        max_receipts: Максимальное количество чеков
    
    Returns:
        Результат выполнения
    """
    orchestrator = SmokeTestOrchestrator()
    return orchestrator.run_smoke_test(recipient_email, max_receipts)
