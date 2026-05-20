# Setup

## 1. Подготовка окружения

Скопировать шаблон переменных:
cp .env.example .env

Заполнить в .env:
- EMAIL_ADDRESS
- EMAIL_APP_PASSWORD
- REPORT_TO_EMAIL
- REPORT_FROM_EMAIL

## 2. Старт контейнеров

docker compose up -d

## 3. Установка Python-зависимостей

docker compose exec app bash
pip install -r requirements.txt

## 4. Установка Playwright

playwright install chromium

Playwright требует отдельной установки браузеров после установки Python-пакета.

## 5. Smoke-проверки

План первого smoke-цикла:
1. Подключение к IMAP.
2. Чтение одного письма.
3. Извлечение ссылки на чек.
4. Открытие ссылки в Playwright.
5. Сохранение тестового отчета.
