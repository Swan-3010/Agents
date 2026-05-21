# Маппинг тестов: Jenkins / Playwright / TestOps

> Справочник соответствий между тест-кейсами, автотестами и CI-конфигурацией.

---

## Структура маппинга

| TC-ID | Название | Тип | Playwright-файл | Jenkins job | TestOps ID | Статус |
|---|---|---|---|---|---|---|
| TC-001 | Пример теста | unit | tests/unit/test_example.py | agents-unit | - | stub |
| TC-002 | Пример интеграции | integration | tests/integration/test_example.py | agents-integration | - | stub |
| TC-003 | Пример контракта | contract | tests/contract/test_example.py | agents-contract | - | stub |
| TC-004 | Пример e2e | e2e | tests/e2e/test_example.py | agents-e2e | - | stub |

---

## Jenkins jobs

| Job | Триггер | Ветка | Команда |
|---|---|---|---|
| agents-unit | PR / push | feature/*, main | `pytest tests/unit` |
| agents-integration | PR / push | feature/*, main | `pytest tests/integration` |
| agents-contract | PR / push | feature/*, main | `pytest tests/contract` |
| agents-e2e | Merge to main | main | `pytest tests/e2e` |

---

## Playwright (будущее)

_Playwright используется для e2e UI-тестов. Конфигурация будет добавлена при внедрении UI-слоя._

---

## Allure TestOps

_Интеграция с TestOps настраивается через переменную окружения `TESTOPS_TOKEN`._
_TestOps ID проставляются после первого прогона на CI._
