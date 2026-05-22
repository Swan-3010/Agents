"""IMAP Mail Fetcher - реализация получения писем из Yandex Mail.

T-027 (Batch 9, E-06): Smoke test - прочитать 1 письмо с чеком из IMAP.

Компонент отвечает за:
- Подключение к IMAP серверу Yandex
- Поиск писем от noreply@check.yandex.ru
- Извлечение тела письма и ссылки на чек
- Возврат данных для дальнейшей обработки

Использование:
    fetcher = YandexMailFetcher()
    receipt_link = fetcher.fetch_one_receipt_link()
"""

import imaplib
import email
import os
import re
from typing import Optional, List
from email.header import decode_header


class YandexMailFetcher:
    """IMAP адаптер для получения писем с чеками из Yandex Mail."""

    def __init__(self):
        """Инициализация с параметрами из .env."""
        self.host = os.getenv('TEST_IMAP_HOST', 'imap.yandex.com')
        self.port = int(os.getenv('TEST_IMAP_PORT', 993))
        self.user = os.getenv('TEST_EMAIL_ADDRESS')
        self.password = os.getenv('TEST_EMAIL_PASSWORD')
        self.receipt_sender = os.getenv('RECEIPT_SENDER', 'noreply@check.yandex.ru')
        self.imap: Optional[imaplib.IMAP4_SSL] = None

    def connect(self) -> bool:
        """Подключение к IMAP серверу.
        
        Returns:
            bool: True если подключение успешно
        
        Raises:
            Exception: При ошибке подключения или аутентификации
        """
        try:
            print(f"[INFO] Подключаюсь к {self.host}:{self.port}...")
            self.imap = imaplib.IMAP4_SSL(self.host, self.port)
            
            status, response = self.imap.login(self.user, self.password)
            if status != 'OK':
                raise Exception(f"Ошибка аутентификации: {response}")
            
            print(f"[INFO] ✅ Успешно подключён как {self.user}")
            return True
        except Exception as e:
            print(f"[ERROR] Ошибка подключения к IMAP: {e}")
            raise

    def fetch_one_receipt_link(self) -> Optional[str]:
        """Получить ссылку на чек из первого письма от Yandex.
        
        Smoke test метод - читает только 1 письмо для проверки.
        
        Returns:
            str: Ссылка на чек (например, https://ofd.ru/r/12345)
            None: Если письма не найдены
        """
        if not self.imap:
            self.connect()
        
        try:
            # Выбираем INBOX в readonly режиме (безопасно)
            readonly = os.getenv('TESTS_READONLY_MODE', 'true').lower() == 'true'
            status, messages = self.imap.select('INBOX', readonly=readonly)
            
            if status != 'OK':
                raise Exception(f"Не удалось выбрать INBOX: {messages}")
            
            total_messages = int(messages[0].decode())
            print(f"[INFO] Всего писем в ящике: {total_messages}")
            
            # Поиск писем от отправителя чеков
            print(f"[INFO] Ищу письма от {self.receipt_sender}...")
            status, data = self.imap.search(None, 'FROM', self.receipt_sender)
            
            if status != 'OK':
                raise Exception(f"Ошибка поиска: {data}")
            
            receipt_ids = data[0].split()
            if not receipt_ids:
                print(f"[WARNING] Письма от {self.receipt_sender} не найдены")
                return None
            
            print(f"[INFO] Найдено {len(receipt_ids)} писем с чеками")
            
            # Читаем ПОСЛЕДНЕЕ письмо (самое свежее)
            latest_msg_id = receipt_ids[-1]
            print(f"[INFO] Читаю письмо ID: {latest_msg_id.decode()}...")
            
            status, msg_data = self.imap.fetch(latest_msg_id, '(RFC822)')
            if status != 'OK':
                raise Exception(f"Ошибка получения письма: {msg_data}")
            
            # Парсинг email
            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            # Извлечение subject (для логов)
            subject = self._decode_header(msg.get('Subject', ''))
            print(f"[INFO] Тема: {subject}")
            
            # Извлечение тела письма
            body = self._get_email_body(msg)
            
            # Поиск ссылки на чек в теле письма
            receipt_link = self._extract_receipt_link(body)
            
            if receipt_link:
                print(f"[INFO] ✅ Найдена ссылка на чек: {receipt_link}")
            else:
                print(f"[WARNING] Ссылка на чек не найдена в письме")
            
            return receipt_link
            
        except Exception as e:
            print(f"[ERROR] Ошибка при получении письма: {e}")
            raise
        finally:
            if self.imap:
                self.imap.close()

    def _decode_header(self, header_value: str) -> str:
        """Декодирование заголовка email (Subject, From, etc).
        
        Args:
            header_value: Закодированное значение заголовка
        
        Returns:
            str: Декодированная строка
        """
        decoded_parts = decode_header(header_value)
        decoded_str = ""
        
        for part, encoding in decoded_parts:
            if isinstance(part, bytes):
                decoded_str += part.decode(encoding or 'utf-8', errors='ignore')
            else:
                decoded_str += part
        
        return decoded_str

    def _get_email_body(self, msg: email.message.Message) -> str:
        """Извлечение текстового тела письма.
        
        Args:
            msg: Объект email.message.Message
        
        Returns:
            str: Текст письма
        """
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get('Content-Disposition', ''))
                
                # Ищем text/plain или text/html части
                if content_type == 'text/plain' and 'attachment' not in disposition:
                    try:
                        payload = part.get_payload(decode=True)
                        charset = part.get_content_charset() or 'utf-8'
                        body += payload.decode(charset, errors='ignore')
                    except Exception as e:
                        print(f"[WARNING] Ошибка декодирования части письма: {e}")
        else:
            try:
                payload = msg.get_payload(decode=True)
                charset = msg.get_content_charset() or 'utf-8'
                body = payload.decode(charset, errors='ignore')
            except Exception as e:
                print(f"[WARNING] Ошибка декодирования письма: {e}")
        
        return body

    def _extract_receipt_link(self, body: str) -> Optional[str]:
        """Извлечение ссылки на чек из тела письма.
        
        Ищет URL вида:
        - https://ofd.ru/r/...
        - https://check.ofd.ru/...
        - https://consumer.rnko.ru/...
        
        Args:
            body: Текст письма
        
        Returns:
            str: URL чека или None
        """
        # Паттерны для известных ОФД
        patterns = [
            r'https?://ofd\.ru/r/[\w\-]+',
            r'https?://check\.ofd\.ru/[\w\-/]+',
            r'https?://consumer\.rnko\.ru/[\w\-/]+',
            r'https?://lk\.platformaofd\.ru/[\w\-/]+',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body)
            if match:
                return match.group(0)
        
        # Если не нашли специфичную ссылку, ищем любую с ключевыми словами
        generic_pattern = r'https?://[\w\.-]+/[\w\-/]*(?:check|receipt|чек)[\w\-/]*'
        match = re.search(generic_pattern, body, re.IGNORECASE)
        if match:
            return match.group(0)
        
        return None

    def disconnect(self):
        """Закрытие соединения с IMAP."""
        if self.imap:
            try:
                self.imap.logout()
                print("[INFO] Отключен от IMAP сервера")
            except Exception as e:
                print(f"[WARNING] Ошибка при отключении: {e}")

    def __enter__(self):
        """Context manager support."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager support."""
        self.disconnect()


if __name__ == '__main__':
    # Smoke test - быстрая проверка
    from dotenv import load_dotenv
    load_dotenv()
    
    print("=" * 60)
    print("SMOKE TEST: T-027 - Получение 1 чека из IMAP")
    print("=" * 60)
    
    with YandexMailFetcher() as fetcher:
        link = fetcher.fetch_one_receipt_link()
        
        if link:
            print("\n" + "=" * 60)
            print("✅ SMOKE TEST PASSED")
            print(f"Ссылка на чек: {link}")
            print("=" * 60)
        else:
            print("\n" + "=" * 60)
            print("❌ SMOKE TEST FAILED: Ссылка не найдена")
            print("=" * 60)
