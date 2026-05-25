"""Browser automation driver для работы с чеками через Playwright."""

import logging
import os
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page

logger = logging.getLogger(__name__)


class ReceiptBrowserDriver:
    """Драйвер для автоматизации браузера при работе с чеками.
    
    Поддерживает Google Chrome, Chromium и Playwright-браузеры.
    """
    
    def __init__(self, headless: bool = True):
        """Инициализация драйвера.
        
        Args:
            headless: Запускать браузер в headless режиме
        """
        self.headless = headless
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        logger.info(f"ReceiptBrowserDriver initialized (headless={headless})")
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop()
    
    def start(self):
        """Запускает Playwright и браузер."""
        try:
            self.playwright = sync_playwright().start()
            
            # Пытаемся найти установленный браузер
            chrome_path = self._find_chrome()
            
            if chrome_path:
                logger.info(f"Используем Google Chrome/Chromium: {chrome_path}")
                self.browser = self.playwright.chromium.launch(
                    headless=self.headless,
                    executable_path=chrome_path,
                    args=[
                        '--disable-gpu',
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-setuid-sandbox',
                        '--disable-blink-features=AutomationControlled'
                    ]
                )
            else:
                # Fallback на Playwright браузер
                logger.info("Используем Playwright Chromium")
                self.browser = self.playwright.chromium.launch(headless=self.headless)
            
            self.page = self.browser.new_page()
            logger.info("Браузер успешно запущен")
            
        except Exception as e:
            logger.error(f"Ошибка запуска браузера: {e}")
            self.stop()
            raise
    
    def stop(self):
        """Останавливает браузер и Playwright."""
        try:
            if self.page:
                self.page.close()
                self.page = None
            
            if self.browser:
                self.browser.close()
                self.browser = None
            
            if self.playwright:
                self.playwright.stop()
                self.playwright = None
            
            logger.info("Браузер остановлен")
        except Exception as e:
            logger.error(f"Ошибка при остановке браузера: {e}")
    
    def open_receipt_url(self, url: str, wait_for_load: bool = True) -> str:
        """Открывает URL чека в браузере.
        
        Args:
            url: URL чека для открытия
            wait_for_load: Ждать полной загрузки страницы
        
        Returns:
            HTML содержимое страницы
        """
        if not self.page:
            raise RuntimeError("Браузер не запущен. Вызовите start() сначала.")
        
        try:
            logger.info(f"Открываем URL: {url}")
            
            if wait_for_load:
                self.page.goto(url, wait_until='networkidle', timeout=30000)
            else:
                self.page.goto(url, timeout=30000)
            
            html_content = self.page.content()
            logger.info(f"Страница загружена, размер HTML: {len(html_content)} bytes")
            
            return html_content
            
        except Exception as e:
            logger.error(f"Ошибка при открытии URL {url}: {e}")
            raise
    
    def take_screenshot(self, output_path: str) -> str:
        """Делает скриншот текущей страницы.
        
        Args:
            output_path: Путь для сохранения скриншота
        
        Returns:
            Путь к сохраненному скриншоту
        """
        if not self.page:
            raise RuntimeError("Браузер не запущен или страница не открыта.")
        
        try:
            logger.info(f"Создаем скриншот: {output_path}")
            self.page.screenshot(path=output_path, full_page=True)
            logger.info(f"Скриншот сохранен: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Ошибка при создании скриншота: {e}")
            raise
    
    def _find_chrome(self) -> Optional[str]:
        """Находит путь к Google Chrome или Chromium.
        
        Returns:
            Путь к исполняемому файлу или None
        """
        possible_paths = [
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            '/opt/google/chrome/chrome',
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/snap/bin/chromium',
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                logger.info(f"Найден браузер: {path}")
                return path
        
        logger.warning("Системный браузер не найден, используем Playwright")
        return None
