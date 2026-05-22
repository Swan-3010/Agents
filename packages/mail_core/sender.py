"""Модуль mail_core.sender - SMTP отправитель писем с отчетами.

Используется для выполнения задачи T-030:
- Отправка писем через SMTP
- Прикрепление XLSX файлов
- Поддержка HTML и текстовых сообщений
"""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from typing import List, Optional, Dict, Any
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class EmailSender:
    """Отправитель писем через SMTP.
    
    Attributes:
        smtp_host: Адрес SMTP сервера
        smtp_port: Порт SMTP сервера
        username: Имя пользователя для авторизации
        password: Пароль для авторизации
        use_tls: Использовать TLS
    """
    
    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        use_tls: bool = True
    ):
        """Инициализация отправителя.
        
        Args:
            smtp_host: SMTP сервер (или из SMTP_HOST env)
            smtp_port: SMTP порт (или из SMTP_PORT env, по умолчанию 587)
            username: Имя пользователя (или из SMTP_USERNAME env)
            password: Пароль (или из SMTP_PASSWORD env)
            use_tls: Использовать TLS (по умолчанию True)
        """
        self.smtp_host = smtp_host or os.getenv("SMTP_HOST", "smtp.yandex.ru")
        self.smtp_port = smtp_port or int(os.getenv("SMTP_PORT", "587"))
        self.username = username or os.getenv("SMTP_USERNAME")
        self.password = password or os.getenv("SMTP_PASSWORD")
        self.use_tls = use_tls
        
        logger.info(f"Инициализирован EmailSender: {self.smtp_host}:{self.smtp_port}")
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
        html: bool = False
    ) -> bool:
        """Отправить письмо по email.
        
        Args:
            to_email: Адрес получателя
            subject: Тема письма
            body: Текст письма
            from_email: Адрес отправителя (по умолчанию username)
            attachments: Список вложений [{'filename': '...', 'content': bytes}, ...]
            html: Использовать HTML формат
            
        Returns:
            True если письмо отправлено успешно
        """
        if not self.username or not self.password:
            logger.error("Не указаны SMTP креденшалы (username/password)")
            return False
        
        from_email = from_email or self.username
        
        # Создание сообщения
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Добавление текста письма
        content_type = 'html' if html else 'plain'
        msg.attach(MIMEText(body, content_type, 'utf-8'))
        
        # Добавление вложений
        if attachments:
            for attachment in attachments:
                filename = attachment.get('filename', 'attachment')
                content = attachment.get('content', b'')
                
                part = MIMEApplication(content, Name=filename)
                part['Content-Disposition'] = f'attachment; filename="{filename}"'
                msg.attach(part)
                logger.info(f"Добавлено вложение: {filename}")
        
        try:
            # Подключение к SMTP
            logger.info(f"Подключение к SMTP {self.smtp_host}:{self.smtp_port}")
            server = smtplib.SMTP(self.smtp_host, self.smtp_port)
            
            if self.use_tls:
                server.starttls()
                logger.info("TLS включен")
            
            # Авторизация
            server.login(self.username, self.password)
            logger.info(f"Авторизация успешна: {self.username}")
            
            # Отправка
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Письмо успешно отправлено: {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"Ошибка авторизации SMTP: {e}")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"Ошибка SMTP: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке письма: {e}")
            return False
    
    def send_report(
        self,
        to_email: str,
        subject: str,
        report_content: bytes,
        report_filename: str = "receipt_report.xlsx",
        message_body: Optional[str] = None
    ) -> bool:
        """Отправить отчет по email.
        
        Args:
            to_email: Адрес получателя
            subject: Тема письма
            report_content: Содержимое отчета (bytes)
            report_filename: Имя файла отчета
            message_body: Текст сообщения (опционально)
            
        Returns:
            True если отправлено успешно
        """
        if message_body is None:
            message_body = f"В приложении отчет о чеках ({report_filename})."
        
        attachments = [
            {
                'filename': report_filename,
                'content': report_content
            }
        ]
        
        return self.send_email(
            to_email=to_email,
            subject=subject,
            body=message_body,
            attachments=attachments
        )


def send_receipt_report_email(
    to_email: str,
    report_content: bytes,
    subject: str = "Отчет о чеках",
    report_filename: str = "receipts.xlsx",
    smtp_host: Optional[str] = None,
    smtp_port: Optional[int] = None,
    username: Optional[str] = None,
    password: Optional[str] = None
) -> bool:
    """Вспомогательная функция для отправки отчета.
    
    Args:
        to_email: Адрес получателя
        report_content: Содержимое XLSX отчета
        subject: Тема письма
        report_filename: Имя файла
        smtp_host: SMTP сервер
        smtp_port: SMTP порт
        username: Имя пользователя
        password: Пароль
    
    Returns:
        True если отправлено успешно
    """
    sender = EmailSender(
        smtp_host=smtp_host,
        smtp_port=smtp_port,
        username=username,
        password=password
    )
    
    return sender.send_report(
        to_email=to_email,
        subject=subject,
        report_content=report_content,
        report_filename=report_filename
    )
