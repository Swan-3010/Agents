"""Responder — генерация ответа через LLM + отправка через SMTP."""
from __future__ import annotations

import json
import logging
import smtplib
from email.mime.text import MIMEText
from typing import TYPE_CHECKING, Any, Dict

import urllib.request

if TYPE_CHECKING:
    from .agent import AgentConfig

from .contracts import MailMessage

logger = logging.getLogger(__name__)


class Responder:
    """Генерирует ответ через Ollama LLM и отправляет через SMTP."""

    def __init__(self, config: "AgentConfig") -> None:
        self._cfg = config

    # ------------------------------------------------------------------
    # Public
    # ------------------------------------------------------------------

    def respond(self, msg: MailMessage, action: str) -> None:
        """Сгенерировать и отправить ответ на письмо."""
        prompt = self._build_prompt(msg, action)
        reply_text = self._call_llm(prompt)
        if reply_text:
            self._send_smtp(msg, reply_text)
        else:
            logger.warning("[Responder] empty LLM reply for message_id=%s", msg.message_id)

    # ------------------------------------------------------------------
    # LLM
    # ------------------------------------------------------------------

    def _call_llm(self, prompt: str) -> str:
        url = f"{self._cfg.llm_endpoint}/api/generate"
        payload = json.dumps({
            "model": self._cfg.llm_model,
            "prompt": prompt,
            "stream": False,
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                data: Dict[str, Any] = json.loads(resp.read())
                return data.get("response", "").strip()
        except Exception as exc:  # noqa: BLE001
            logger.error("[Responder] LLM error: %s", exc)
            return ""

    # ------------------------------------------------------------------
    # SMTP
    # ------------------------------------------------------------------

    def _send_smtp(self, original: MailMessage, reply_text: str) -> None:
        mime = MIMEText(reply_text, "plain", "utf-8")
        mime["Subject"] = f"Re: {original.subject}"
        mime["From"] = self._cfg.email
        mime["To"] = original.sender
        try:
            with smtplib.SMTP_SSL(
                self._cfg.smtp_host, self._cfg.smtp_port
            ) as server:
                server.login(self._cfg.email, self._cfg.app_password)
                server.sendmail(
                    self._cfg.email,
                    [original.sender],
                    mime.as_string(),
                )
            logger.info(
                "[Responder] sent reply to=%s subject=%r",
                original.sender,
                original.subject,
            )
        except smtplib.SMTPException as exc:
            logger.error("[Responder] SMTP error: %s", exc)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _build_prompt(msg: MailMessage, action: str) -> str:
        return (
            f"Ты ассистент по обработке електронной почты.\n"
            f"Действие: {action}\n"
            f"Отправитель: {msg.sender}\n"
            f"Тема: {msg.subject}\n\n"
            f"Тело письма:\n{msg.body[:2000]}\n\n"
            f"Напиши короткий вежливый ответ на русском языке."
        )
