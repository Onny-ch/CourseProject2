"""
Тесты для модуля вспомогательных функций services.
"""
import pytest

from src.services import (
    clean_html,
    extract_probation_period,
    validate_title,
    validate_url,
)


def test_validate_title_empty():
    """Тестирование validate_title с пустой строкой."""
    assert validate_title("") == "Вакансия без названия"
    assert validate_title("   ") == "Вакансия без названия"
    assert validate_title(None) == "Вакансия без названия"


def test_validate_title_whitespace():
    """Тестирование validate_title с пробелами."""
    assert validate_title("  Python Developer  ") == "Python Developer"
    assert validate_title("  Test  Job  ") == "Test  Job"


def test_validate_title_normal():
    """Тестирование validate_title с нормальным названием."""
    assert validate_title("Python Developer") == "Python Developer"
    assert validate_title("Software Engineer") == "Software Engineer"


def test_validate_url_valid():
    """Тестирование validate_url с валидными URL."""
    assert validate_url("https://hh.ru/vacancy/123") == "https://hh.ru/vacancy/123"
    assert validate_url("http://example.com") == "http://example.com"
    assert validate_url("https://example.com/vacancy") == "https://example.com/vacancy"


def test_validate_url_empty():
    """Тестирование validate_url с пустой строкой."""
    assert validate_url("") == ""
    assert validate_url("   ") == ""


def test_validate_url_invalid():
    """Тестирование validate_url с невалидными URL."""
    with pytest.raises(ValueError, match="Некорректный URL"):
        validate_url("ftp://invalid")
    with pytest.raises(ValueError, match="Некорректный URL"):
        validate_url("invalid-url")
    with pytest.raises(ValueError, match="Некорректный URL"):
        validate_url("just text")


def test_validate_url_with_whitespace():
    """Тестирование validate_url с пробелами."""
    assert validate_url("  https://hh.ru/vacancy/123  ") == "https://hh.ru/vacancy/123"


def test_clean_html_normal():
    """Тестирование clean_html с нормальным HTML."""
    assert clean_html("<p>Text</p>") == "Text"
    assert clean_html("<b>Bold</b> text") == "Bold text"
    assert clean_html("<p>Text <b>bold</b> and <i>italic</i></p>") == "Text bold and italic"


def test_clean_html_empty():
    """Тестирование clean_html с пустой строкой."""
    assert clean_html("") == ""
    assert clean_html(None) == ""


def test_clean_html_no_tags():
    """Тестирование clean_html без тегов."""
    assert clean_html("Plain text") == "Plain text"
    assert clean_html("Text without tags") == "Text without tags"


def test_extract_probation_period_months():
    """Тестирование extract_probation_period с месяцами."""
    assert extract_probation_period("Испытательный срок 3 месяца") == "3 месяца"
    assert extract_probation_period("Срок 6 месяц") == "6 месяца"
    assert extract_probation_period("1 месяц испытания") == "1 месяца"


def test_extract_probation_period_weeks():
    """Тестирование extract_probation_period с неделями."""
    assert extract_probation_period("Испытательный срок 2 недели") == "2 недели"
    assert extract_probation_period("Срок 4 недели") == "4 недели"


def test_extract_probation_period_days():
    """Тестирование extract_probation_period с днями."""
    assert extract_probation_period("Испытательный срок 7 день") == "7 дня"
    assert extract_probation_period("Срок 14 день") == "14 дня"


def test_extract_probation_period_years():
    """Тестирование extract_probation_period с годами."""
    assert extract_probation_period("Испытательный срок 1 год") == "1 года"
    assert extract_probation_period("Срок 2 года") == "2 года"


def test_extract_probation_period_not_found():
    """Тестирование extract_probation_period когда не найдено."""
    assert extract_probation_period("Нет испытательного срока") is None
    assert extract_probation_period("") is None
    assert extract_probation_period("Просто текст") is None


def test_extract_probation_period_case_insensitive():
    """Тестирование extract_probation_period без учета регистра."""
    # Тест проверяет что функция работает с разными вариантами написания
    assert extract_probation_period("Испытательный срок 3 месяц") == "3 месяца"
    assert extract_probation_period("Испытательный срок 2 недел") == "2 недели"

