"""
Модуль вспомогательных функций для работы с вакансиями.

Содержит функции для валидации данных, очистки HTML,
извлечения информации и других общих операций.
"""
import re
from typing import Optional


def validate_title(title: str) -> str:
    """
    Валидирует и очищает название вакансии.
    
    Args:
        title: Название вакансии
        
    Returns:
        Очищенное название или значение по умолчанию, если название пустое
    """
    if not title or not title.strip():
        return "Вакансия без названия"
    return title.strip()


def validate_url(url: str) -> str:
    """
    Валидирует URL вакансии.
    
    Args:
        url: URL вакансии
        
    Returns:
        Валидный URL или пустую строку
        
    Raises:
        ValueError: Если URL имеет недопустимый формат
    """
    if not url or not url.strip():
        return ""
    url = url.strip()
    if not re.match(r"^https?://", url):
        raise ValueError(f"Некорректный URL: {url}")
    return url


def clean_html(text: str) -> str:
    """
    Удаляет HTML-теги из текста.
    
    Args:
        text: Текст с HTML-тегами
        
    Returns:
        Текст без HTML-тегов
    """
    if not text:
        return ""
    return re.sub(r"<[^>]+>", "", text).strip()


def extract_probation_period(text: str) -> Optional[str]:
    """
    Извлекает информацию об испытательном сроке из текста.
    
    Ищет шаблоны вида "3 месяца", "2 недели", "1 день" и т.п.
    
    Args:
        text: Текст для поиска информации об испытательном сроке
        
    Returns:
        Строка с информацией об испытательном сроке или None, если не найдено
    """
    pattern = r'(\d+)\s*(месяц|недел|день|год)а?'
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        count = match.group(1)
        unit = match.group(2)
        # Корректируем окончание
        if unit == "месяц":
            return f"{count} месяца"
        elif unit == "недел":
            return f"{count} недели"
        elif unit == "день":
            return f"{count} дня"
        elif unit == "год":
            return f"{count} года"
    return None

