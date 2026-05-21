# Pattern Spec: Yandex Mail Agent

**Version:** 0.1.0  
**Status:** Draft  
**Owner:** Swan-3010

---

## Назначение

Агент ежедневно обрабатывает входящие чеки из Yandex Mail (отправитель `noreply@check.yandex.ru`), извлекает данные, формирует XLSX-отчёт и отправляет его по SMTP.

---

## Паттерн запуска

```
Триггер (cron / ручной запуск)
        |
        v
[1] IMAP Fetch
    - подключиться к imap.yandex.ru:993 (SSL)
    - выбрать папку INBOX
    - найти непрочитанные письма от noreply@check.yandex.ru
    - вернуть список MailMessage
        |
        v
[2] Receipt Parser
    - для каждого MailMessage:
        - попытаться извлечь данные из body_text
        - если нет — открыть receipt_url через Playwright
        - распарсить: store_name, total_amount, currency
    - вернуть список Receipt
        |
        v
[3] Report Builder
    - сгруппировать Receipt по дате и магазину
    - записать в XLSX (openpyxl)
    - сгенерировать Markdown-отчёт об ошибках
        |
        v
[4] Notifier
    - отправить XLSX + Markdown по SMTP (aiosmtplib)
    - вернуть AgentRunResult
```

---

## Контракты (reusable)

| Контракт | Описание |
|---|---|
| `MailMessage` | Письмо из IMAP |
| `Receipt` | Парсенный чек |
| `AgentRunResult` | Результат цикла агента |

---

## Ограничения

- Только письма от `noreply@check.yandex.ru`
- Максимально 100 писем за цикл (защита от IMAP rate limit)
- Playwright запускается только если body_text пустой или receipt_url не None
- Все ошибки пишутся в AgentRunResult.errors, агент не падает

---

## Правило: test-first

До любой новой функции обязательно:
1. Описать test cases по категориям unit / integration / contract / e2e
2. Сохранить тестовую документацию в `docs/`
3. Создать stub-тесты в `tests/`
4. Только потом писать имплементацию
