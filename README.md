# Agents

Проект агента для ежедневной обработки чеков из Yandex Mail.

## Назначение

Агент должен:
- читать письма из Yandex Mail по IMAP;
- находить чеки от noreply@check.yandex.ru;
- извлекать ссылки и данные чеков;
- при необходимости открывать страницы через Playwright;
- формировать XLSX-отчет и Markdown-отчет об ошибках;
- отправлять результат по SMTP.

## Быстрый старт

1. Создать локальный .env:
   cp .env.example .env

2. Поднять контейнеры:
   docker compose up -d

3. Войти в контейнер приложения:
   docker compose exec app bash

4. Установить зависимости:
   pip install -r requirements.txt

5. Установить браузер для Playwright:
   playwright install chromium

## Следующий этап

После инфраструктурного старта:
- проверить IMAP;
- проверить Playwright;
- сохранить тестовый XLSX;
- собрать первый smoke workflow.
