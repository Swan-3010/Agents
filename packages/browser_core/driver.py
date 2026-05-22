"""Модуль browser_core.driver - драйвер Playwright для открытия чека.

Используется для выполнения задачи T-028:
- Открытие URL чека через Playwright
- Ожидание загрузки страницы
- Возврат контента или скриншота страницы
"""

from playwright.sync_api import sync_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError
from typing import Optional, Dict, Any
import logging
import os

logger = logging.getLogger(__name__)


class ReceiptBrowserDriver:
    """Драйвер для открытия чека через Playwright.
    
    Attributes:
        headless: Запуск браузера в headless режиме
        timeout: Таймаут для операций (мс)
        browser: Экземпляр браузера Playwright
        page: Текущая страница браузера
    """
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """Инициализация драйвера.
        
        Args:
            headless: Запуск в headless режиме (по умолчанию True)
            timeout: Таймаут операций в миллисекундах (по умолчанию 30000)
        """
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self._playwright = None
    
    def start(self) -> None:
        """Запуск браузера Playwright."""
        try:
            self._playwright = sync_playwright().start()
            self.browser = self._playwright.chromium.launch(headless=self.headless)
            self.page = self.browser.new_page()
            self.page.set_default_timeout(self.timeout)
            logger.info(f"Браузер запущен (headless={self.headless}, timeout={self.timeout}ms)")
        except Exception as e:
            logger.error(f"Ошибка запуска браузера: {e}")
            raise
    
    def open_receipt(self, url: str) -> Dict[str, Any]:
        """Открыть чек по URL и дождаться загрузки.
        
        Args:
            url: URL чека для открытия
            
        Returns:
            Словарь с данными:
            - success: bool - успешность операции
            - url: str - открытый URL
            - title: str - заголовок страницы
            - content: str - HTML контент страницы (опционально)
            - screenshot: bytes - скриншот страницы (опционально)
            - error: str - описание ошибки (если есть)
        """
        if not self.page:
            raise RuntimeError("Браузер не запущен. Вызовите start() сначала.")
        
        result: Dict[str, Any] = {
            "success": False,
            "url": url
        }
        
        try:
            logger.info(f"Открытие URL чека: {url}")
            response = self.page.goto(url, wait_until="networkidle")
            
            if response and response.ok:
                result["success"] = True
                result["title"] = self.page.title()
                result["content"] = self.page.content()
                logger.info(f"Чек успешно открыт: {result['title']}")
            else:
                status = response.status if response else "unknown"
                result["error"] = f"Ошибка загрузки страницы: статус {status}"
                logger.error(result["error"])
                
        except PlaywrightTimeoutError as e:
            result["error"] = f"Таймаут загрузки чека: {e}"
            logger.error(result["error"])
        except Exception as e:
            result["error"] = f"Неожиданная ошибка при открытии чека: {e}"
            logger.error(result["error"])
        
        return result
    
    def take_screenshot(self, path: Optional[str] = None) -> bytes:
        """Сделать скриншот текущей страницы.
        
        Args:
            path: Путь для сохранения скриншота (опционально)
            
        Returns:
            Скриншот в виде bytes
        """
        if not self.page:
            raise RuntimeError("Браузер не запущен или страница не открыта.")
        
        screenshot = self.page.screenshot(full_page=True, path=path)
        logger.info(f"Скриншот сделан{' и сохранен: ' + path if path else ''}")
        return screenshot
    
    def stop(self) -> None:
        """Остановка браузера и очистка ресурсов."""
        try:
            if self.page:
                self.page.close()
                self.page = None
            if self.browser:
                self.browser.close()
                self.browser = None
            if self._playwright:
                self._playwright.stop()
                self._playwright = None
            logger.info("Браузер остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке браузера: {e}")
    
    def __enter__(self):
        """Контекстный менеджер: вход."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Контекстный менеджер: выход."""
        self.stop()


def open_receipt_url(url: str, headless: bool = True, screenshot_path: Optional[str] = None) -> Dict[str, Any]:
    """Вспомогательная функция для быстрого открытия чека.
    
    Args:
        url: URL чека
        headless: Режим headless
        screenshot_path: Путь для сохранения скриншота (опционально)
    
    Returns:
        Результат открытия чека
    """
    with ReceiptBrowserDriver(headless=headless) as driver:
        result = driver.open_receipt(url)
        if result["success"] and screenshot_path:
            result["screenshot"] = driver.take_screenshot(screenshot_path)
        return result
