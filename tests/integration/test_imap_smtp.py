"""Integration-тесты для IMAP/SMTP внешних адаптеров.

Тесты проверяют:
- Подключение к IMAP серверу Yandex
- Получение писем через IMAP
- Отправку писем через SMTP
- Аутентификацию по app password

TC-024 (Batch 8, E-05)
Требует: включённый IMAP в настройках Yandex Mail
Реальные credentials из .env: TEST_EMAIL_ADDRESS, TEST_EMAIL_PASSWORD
"""

import pytest
import imaplib
import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class TestIMAPConnection:
    """Интеграционные тесты IMAP-подключения."""

    def test_imap_ssl_connection(self):
        """TC-024-01: Проверка SSL-подключения к imap.yandex.ru:993."""
        host = os.getenv('TEST_IMAP_HOST', 'imap.yandex.com')
        port = int(os.getenv('TEST_IMAP_PORT', 993))
        
        # Подключение через SSL
        imap = imaplib.IMAP4_SSL(host, port)
        assert imap is not None
        imap.logout()

    def test_imap_authentication(self):
        """TC-024-02: Проверка аутентификации с app password."""
        host = os.getenv('TEST_IMAP_HOST', 'imap.yandex.com')
        port = int(os.getenv('TEST_IMAP_PORT', 993))
        user = os.getenv('TEST_EMAIL_ADDRESS')
        password = os.getenv('TEST_EMAIL_PASSWORD')
        
        assert user, "TEST_EMAIL_ADDRESS не установлен в .env"
        assert password, "TEST_EMAIL_PASSWORD не установлен в .env"
        
        imap = imaplib.IMAP4_SSL(host, port)
        status, response = imap.login(user, password)
        assert status == 'OK'
        imap.logout()

    def test_imap_select_inbox(self):
        """TC-024-03: Проверка выбора INBOX папки."""
        host = os.getenv('TEST_IMAP_HOST', 'imap.yandex.com')
        port = int(os.getenv('TEST_IMAP_PORT', 993))
        user = os.getenv('TEST_EMAIL_ADDRESS')
        password = os.getenv('TEST_EMAIL_PASSWORD')
        
        imap = imaplib.IMAP4_SSL(host, port)
        imap.login(user, password)
        
        # Выбор INBOX в readonly режиме (безопасно)
        readonly = os.getenv('TESTS_READONLY_MODE', 'true').lower() == 'true'
        status, messages = imap.select('INBOX', readonly=readonly)
        
        assert status == 'OK'
        total_messages = int(messages[0].decode())
        assert total_messages >= 0
        
        imap.close()
        imap.logout()

    def test_imap_fetch_unseen(self):
        """TC-024-04: Проверка получения UNSEEN писем."""
        host = os.getenv('TEST_IMAP_HOST', 'imap.yandex.com')
        port = int(os.getenv('TEST_IMAP_PORT', 993))
        user = os.getenv('TEST_EMAIL_ADDRESS')
        password = os.getenv('TEST_EMAIL_PASSWORD')
        
        imap = imaplib.IMAP4_SSL(host, port)
        imap.login(user, password)
        imap.select('INBOX', readonly=True)
        
        # Поиск чеков от Yandex
        status, data = imap.search(None, 'FROM', 'noreply@check.yandex.ru')
        assert status == 'OK'
        
        receipt_ids = data[0].split()
        # Проверяем, что найдено хотя бы 1 письмо (у нас 194)
        assert len(receipt_ids) > 0, "Не найдено писем от noreply@check.yandex.ru"
        
        imap.close()
        imap.logout()


class TestSMTPConnection:
    """Интеграционные тесты SMTP-отправки."""

    def test_smtp_tls_connection(self):
        """TC-024-05: Проверка TLS-подключения к smtp.yandex.ru:465."""
        host = os.getenv('TEST_SMTP_HOST', 'smtp.yandex.com')
        port = int(os.getenv('TEST_SMTP_PORT', 465))
        user = os.getenv('TEST_EMAIL_ADDRESS')
        password = os.getenv('TEST_EMAIL_PASSWORD')
        
        assert user, "TEST_EMAIL_ADDRESS не установлен в .env"
        assert password, "TEST_EMAIL_PASSWORD не установлен в .env"
        
        # Подключение через SSL (465 порт)
        smtp = smtplib.SMTP_SSL(host, port)
        status, _ = smtp.login(user, password)
        assert status == 235  # 235 = Authentication successful
        smtp.quit()

    @pytest.mark.skip("Пропускаем - отправка реальных писем не нужна в CI")
    def test_smtp_send_mail(self):
        """TC-024-06: Проверка отправки тестового email."""
        host = os.getenv('TEST_SMTP_HOST', 'smtp.yandex.com')
        port = int(os.getenv('TEST_SMTP_PORT', 465))
        user = os.getenv('TEST_EMAIL_ADDRESS')
        password = os.getenv('TEST_EMAIL_PASSWORD')
        recipient = os.getenv('TEST_REPORT_TO_EMAIL', user)  # Отправляем самому себе
        
        msg = MIMEMultipart()
        msg['From'] = user
        msg['To'] = recipient
        msg['Subject'] = '[TEST] Тестовое письмо от pytest'
        msg.attach(MIMEText('Это автоматическое тестовое письмо.', 'plain', 'utf-8'))
        
        smtp = smtplib.SMTP_SSL(host, port)
        smtp.login(user, password)
        smtp.send_message(msg)
        smtp.quit()
