#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Playwright с системным Google Chrome.
Проверяет базовую функциональность браузера и навигации.
"""

import sys
from playwright.sync_api import sync_playwright


def test_playwright_with_chrome():
    """
    Тест Playwright с использованием системного Google Chrome.
    """
    print("🚀 Запуск теста Playwright с Google Chrome...")
    
    with sync_playwright() as p:
        # Запускаем Chrome с указанием пути к системному бинарнику
        browser = p.chromium.launch(
            executable_path='/usr/bin/google-chrome',
            headless=True,
            args=[
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage'
            ]
        )
        
        try:
            print("✅ Браузер запущен успешно")
            
            # Создаём контекст и страницу
            context = browser.new_context()
            page = context.new_page()
            
            print("📄 Создана новая страница")
            
            # Навигация на тестовую страницу
            print("🌐 Переход на example.com...")
            page.goto('https://example.com', wait_until='networkidle')
            
            # Проверяем заголовок
            title = page.title()
            print(f"📋 Заголовок страницы: {title}")
            
            # Проверяем, что на странице есть ожидаемый текст
            content = page.content()
            assert 'Example Domain' in content, "Ожидаемый текст не найден"
            
            print("✅ Тест навигации пройден успешно")
            
            # Проверяем h1 элемент
            h1_element = page.locator('h1').first
            h1_text = h1_element.inner_text()
            print(f"📌 H1 текст: {h1_text}")
            
            assert h1_text == 'Example Domain', f"Неожиданный текст H1: {h1_text}"
            
            print("✅ Проверка элементов пройдена")
            
            # Закрываем страницу и контекст
            page.close()
            context.close()
            
            print("✅ Все проверки пройдены успешно!")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка при выполнении теста: {e}")
            return False
            
        finally:
            browser.close()
            print("🔒 Браузер закрыт")


if __name__ == '__main__':
    print("="*50)
    print("Тест Playwright + Google Chrome (Ubuntu 26.04)")
    print("="*50)
    
    success = test_playwright_with_chrome()
    
    print("="*50)
    if success:
        print("✅ РЕЗУЛЬТАТ: Тест завершён успешно")
        sys.exit(0)
    else:
        print("❌ РЕЗУЛЬТАТ: Тест завершён с ошибками")
        sys.exit(1)
