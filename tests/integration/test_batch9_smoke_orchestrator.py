"""Интеграционный тест для Batch 9: Smoke Test Orchestrator.

Тестирует:
- T-027: IMAP Fetcher
- T-028: Playwright Driver
- T-029: XLSX Generator
- T-030: SMTP Sender
- T-031: Smoke Test Orchestrator

Полный цикл: IMAP → Playwright → XLSX → SMTP
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Импорт компонентов Batch 9
try:
    from packages.yandex_mail_agent.smoke_test_orchestrator import (
        SmokeTestOrchestrator,
        run_smoke_test
    )
    from packages.mail_core.fetcher import ImapReceiptFetcher
    from packages.browser_core.driver import ReceiptBrowserDriver
    from packages.report_core.generator import ReceiptReportGenerator
    from packages.mail_core.sender import EmailSender
except ImportError:
    pytest.skip("Модули Batch 9 не доступны", allow_module_level=True)


@pytest.mark.integration
class TestSmokeTestOrchestrator:
    """Интеграционные тесты для SmokeTestOrchestrator."""
    
    @pytest.fixture
    def orchestrator(self):
        """Создание экземпляра оркестратора."""
        return SmokeTestOrchestrator()
    
    @pytest.fixture
    def mock_receipts(self):
        """Тестовые данные чеков."""
        return [
            {
                "url": "https://check.ofd.ru/12345",
                "subject": "Чек от Магнит"
            },
            {
                "url": "https://check.ofd.ru/67890",
                "subject": "Чек от Пятерочка"
            }
        ]
    
    def test_orchestrator_initialization(self, orchestrator):
        """Тест инициализации оркестратора."""
        assert orchestrator is not None
        assert hasattr(orchestrator, 'results')
        assert isinstance(orchestrator.results, list)
    
    @patch('packages.mail_core.fetcher.ImapReceiptFetcher')
    def test_fetch_receipts_success(self, mock_fetcher_class, orchestrator, mock_receipts):
        """Тест успешного получения чеков."""
        # Настройка mock
        mock_fetcher = Mock()
        mock_fetcher.fetch_recent_messages.return_value = [
            {"subject": "Чек от Магнит"},
            {"subject": "Чек от Пятерочка"}
        ]
        mock_fetcher.extract_receipt_link.side_effect = [
            "https://check.ofd.ru/12345",
            "https://check.ofd.ru/67890"
        ]
        mock_fetcher_class.return_value = mock_fetcher
        
        # Выполнение
        receipts = orchestrator._fetch_receipts(5)
        
        # Проверка
        assert len(receipts) == 2
        assert receipts[0]["url"] == "https://check.ofd.ru/12345"
        assert receipts[1]["url"] == "https://check.ofd.ru/67890"
    
    @patch('packages.browser_core.driver.ReceiptBrowserDriver')
    def test_process_receipts_with_browser(self, mock_driver_class, orchestrator, mock_receipts):
        """Тест обработки чеков через браузер."""
        # Настройка mock
        mock_driver = MagicMock()
        mock_driver.__enter__.return_value = mock_driver
        mock_driver.__exit__.return_value = None
        mock_driver.open_receipt.return_value = {
            "success": True,
            "title": "Чек OFD",
            "content": "<html>...</html>"
        }
        mock_driver_class.return_value = mock_driver
        
        # Выполнение
        details = orchestrator._process_receipts_with_browser(mock_receipts)
        
        # Проверка
        assert len(details) == 2
        assert details[0]["Статус"] == "Успех"
        assert mock_driver.open_receipt.call_count == 2
    
    @patch('packages.report_core.generator.ReceiptReportGenerator')
    def test_generate_xlsx_report(self, mock_generator_class, orchestrator):
        """Тест генерации XLSX отчета."""
        # Настройка mock
        mock_generator = Mock()
        mock_generator.save_to_bytes.return_value = b'fake_xlsx_content'
        mock_generator_class.return_value = mock_generator
        
        receipt_details = [
            {"Тема": "Чек", "URL": "https://check.ofd.ru/12345", "Статус": "Успех"}
        ]
        
        # Выполнение
        report_bytes = orchestrator._generate_xlsx_report(receipt_details)
        
        # Проверка
        assert report_bytes == b'fake_xlsx_content'
        mock_generator.add_multiple_receipts.assert_called_once_with(receipt_details)
    
    @patch('packages.mail_core.sender.EmailSender')
    def test_send_report_email(self, mock_sender_class, orchestrator):
        """Тест отправки отчета по email."""
        # Настройка mock
        mock_sender = Mock()
        mock_sender.send_report.return_value = True
        mock_sender_class.return_value = mock_sender
        
        # Выполнение
        success = orchestrator._send_report_email("test@example.com", b'report_content')
        
        # Проверка
        assert success is True
        mock_sender.send_report.assert_called_once()
    
    @patch('packages.mail_core.sender.EmailSender')
    @patch('packages.report_core.generator.ReceiptReportGenerator')
    @patch('packages.browser_core.driver.ReceiptBrowserDriver')
    @patch('packages.mail_core.fetcher.ImapReceiptFetcher')
    def test_run_smoke_test_full_flow(
        self,
        mock_fetcher_class,
        mock_driver_class,
        mock_generator_class,
        mock_sender_class,
        orchestrator
    ):
        """Тест полного цикла smoke-теста."""
        # Настройка mocks
        # IMAP Fetcher
        mock_fetcher = Mock()
        mock_fetcher.fetch_recent_messages.return_value = [
            {"subject": "Чек 1"}
        ]
        mock_fetcher.extract_receipt_link.return_value = "https://check.ofd.ru/12345"
        mock_fetcher_class.return_value = mock_fetcher
        
        # Browser Driver
        mock_driver = MagicMock()
        mock_driver.__enter__.return_value = mock_driver
        mock_driver.__exit__.return_value = None
        mock_driver.open_receipt.return_value = {
            "success": True,
            "title": "Чек OFD"
        }
        mock_driver_class.return_value = mock_driver
        
        # XLSX Generator
        mock_generator = Mock()
        mock_generator.save_to_bytes.return_value = b'xlsx_content'
        mock_generator_class.return_value = mock_generator
        
        # Email Sender
        mock_sender = Mock()
        mock_sender.send_report.return_value = True
        mock_sender_class.return_value = mock_sender
        
        # Выполнение
        result = orchestrator.run_smoke_test("test@example.com", max_receipts=5)
        
        # Проверка
        assert result["success"] is True
        assert len(result["steps"]) == 4
        assert result["steps"][0]["name"] == "fetch_receipts"
        assert result["steps"][1]["name"] == "process_receipts"
        assert result["steps"][2]["name"] == "generate_report"
        assert result["steps"][3]["name"] == "send_email"
        assert all(step["success"] for step in result["steps"])
    
    @patch('packages.mail_core.fetcher.ImapReceiptFetcher')
    def test_run_smoke_test_no_receipts(
        self,
        mock_fetcher_class,
        orchestrator
    ):
        """Тест обработки сценария без чеков."""
        # Настройка mock
        mock_fetcher = Mock()
        mock_fetcher.fetch_recent_messages.return_value = []
        mock_fetcher_class.return_value = mock_fetcher
        
        # Выполнение
        result = orchestrator.run_smoke_test("test@example.com", max_receipts=5)
        
        # Проверка
        assert result["success"] is False
        assert len(result["errors"]) > 0
        assert "не найдено" in result["errors"][0].lower()


@pytest.mark.integration
def test_run_smoke_test_helper_function():
    """Тест вспомогательной функции run_smoke_test."""
    with patch('packages.yandex_mail_agent.smoke_test_orchestrator.SmokeTestOrchestrator') as mock_orch:
        mock_instance = Mock()
        mock_instance.run_smoke_test.return_value = {
            "success": True,
            "steps": []
        }
        mock_orch.return_value = mock_instance
        
        result = run_smoke_test("test@example.com", max_receipts=3)
        
        assert result["success"] is True
        mock_instance.run_smoke_test.assert_called_once_with("test@example.com", 3)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
