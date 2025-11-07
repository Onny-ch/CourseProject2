from decimal import Decimal

import pytest

from src.services import clean_html, extract_probation_period
from src.vacancy import Vacancy


def test_vacancy_init_minimal_data():
    """Тестирование инициализации с минимально необходимыми данными."""
    data = {"name": "Test Job", "alternate_url": ""}
    vacancy = Vacancy(data)
    assert vacancy.title == "Test Job"
    assert vacancy.salary_from == Decimal("0")
    assert vacancy.city == "Не указан"


def test_vacancy_init_empty_name():
    """Проверка обработки пустого названия вакансии (возвращает значение по умолчанию)."""
    data = {"name": "", "alternate_url": ""}
    vacancy = Vacancy(data)
    assert vacancy.title == "Вакансия без названия"


def test_vacancy_init_whitespace_name():
    """Проверка обрезки пробелов в названии."""
    data = {"name": "  Python Dev  ", "alternate_url": ""}
    vacancy = Vacancy(data)
    assert vacancy.title == "Python Dev"


def test_vacancy_init_invalid_url():
    """Проверка валидации URL."""
    data = {"name": "Job", "alternate_url": "ftp://invalid"}
    with pytest.raises(ValueError, match="Некорректный URL"):
        Vacancy(data)

    data = {"name": "Job", "alternate_url": ""}
    vacancy = Vacancy(data)
    assert vacancy.url == ""


def test_vacancy_validate_salary():
    """Тестирование обработки зарплаты (метод удален, но функциональность работает в __init__)."""
    # Тестируем что зарплата правильно обрабатывается в конструкторе
    data1 = {"name": "Test", "alternate_url": "", "salary": {"from": 100000, "to": 150000}}
    vacancy1 = Vacancy(data1)
    assert vacancy1.salary_from == Decimal("100000")
    assert vacancy1.salary_to == Decimal("150000")

    data2 = {"name": "Test", "alternate_url": "", "salary": None}
    vacancy2 = Vacancy(data2)
    assert vacancy2.salary_from == Decimal("0")
    assert vacancy2.salary_to == Decimal("0")


def test_vacancy_clean_html():
    """Тестирование функции очистки HTML из модуля services."""
    text = "<p>Требуется <b>Python</b> разработчик</p>"
    cleaned = clean_html(text)
    assert cleaned == "Требуется Python разработчик"
    assert clean_html("") == ""
    assert clean_html(None) == ""


def test_vacancy_extract_probation():
    """Тестирование функции извлечения испытательного срока из модуля services."""
    text1 = "Испытательный срок 3 месяца"
    assert extract_probation_period(text1) == "3 месяца"


def test_vacancy_salary_info():
    """Тестирование свойства salary_info."""
    vacancy1 = Vacancy({"name": "No Salary", "alternate_url": ""})
    assert vacancy1.salary_info == "Зарплата не указана"

    data2 = {
        "name": "Fixed",
        "alternate_url": "",
        "salary": {"from": 100000, "to": 100000, "currency": "USD", "gross": False},
    }
    vacancy2 = Vacancy(data2)
    assert vacancy2.salary_info == "100,000 USD (net)"

    data3 = {
        "name": "Range",
        "alternate_url": "",
        "salary": {"from": 80000, "to": 120000, "currency": "RUB", "gross": True},
    }
    vacancy3 = Vacancy(data3)
    assert vacancy3.salary_info == "от 80,000 до 120,000 RUB (gross)"


def test_vacancy_average_salary():
    vacancy1 = Vacancy({"name": "No Salary", "alternate_url": ""})
    assert vacancy1.average_salary() == Decimal("0")

    data2 = {"name": "Fixed", "alternate_url": "", "salary": {"from": 100000, "to": 100000}}
    vacancy2 = Vacancy(data2)
    assert vacancy2.average_salary() == Decimal("100000")

    data3 = {"name": "Range", "alternate_url": "", "salary": {"from": 80000, "to": 120000}}
    vacancy3 = Vacancy(data3)
    assert vacancy3.average_salary() == Decimal("100000")


def test_vacancy_comparison_operators():
    v1 = Vacancy({"name": "A", "alternate_url": "", "salary": {"from": 50000}})
    v2 = Vacancy({"name": "B", "alternate_url": "", "salary": {"from": 100000}})
    v3 = Vacancy({"name": "C", "alternate_url": "", "salary": {"from": 100000}})

    assert v1 < v2
    assert v2 > v1
    assert v2 >= v3
    assert v2 <= v3
    assert v2 == v3
    assert v1 != v2

    assert not (v1 == "not a vacancy")
    assert (v1 == "not a vacancy") is not NotImplemented


def test_vacancy_str_and_repr():
    data = {
        "name": "Python Dev",
        "alternate_url": "https://hh.ru/vacancy/1",
        "salary": {"from": 100000, "to": 100000},
        "address": {"city": "Москва"},
    }
    vacancy = Vacancy(data)
    assert str(vacancy) == "Python Dev | 100,000 RUB (gross) | Москва"
    assert "Vacancy(title='Python Dev'" in repr(vacancy)
    assert "salary_from=100000" in repr(vacancy)


def test_vacancy_to_dict_full():
    """Тестирование to_dict с полными данными."""
    sample_data = {
        "id": "1",
        "name": "Python Developer",
        "alternate_url": "https://hh.ru/vacancy/123",
        "employer": {"name": "TechCo", "alternate_url": "https://hh.ru/employer/456"},
        "salary": {"from": 100000, "to": 150000, "currency": "RUB", "gross": True},
        "snippet": {
            "responsibility": "<p>Разработка API на <b>Django</b></p>",
            "requirement": "Опыт работы с <i>PostgreSQL</i>",
        },
        "experience": {"name": "1-3 года"},
        "address": {"city": "Москва", "street": "Ленина", "building": "10"},
    }

    vacancy = Vacancy(sample_data)
    result = vacancy.to_dict()

    assert result["id"] == "1"
    assert result["title"] == "Python Developer"
    assert result["salary_from"] == 100000
    assert result["salary_to"] == 150000
    assert result["currency"] == "RUB"
    assert result["gross"] is True

    assert "Django" in result["responsibilities"]
    assert "PostgreSQL" in result["requirements"]

    assert result["average_salary"] == 125000

    assert result["city"] == "Москва"
    assert result["street"] == "Ленина"
    assert result["building"] == "10"

    assert result["professional_roles"] == []


def test_vacancy_to_dict_no_salary():
    """Тестирование to_dict когда зарплата не указана."""
    data = {"name": "No Salary Job", "alternate_url": "", "salary": None}
    vacancy = Vacancy(data)
    result = vacancy.to_dict()

    assert result["salary_from"] is None
    assert result["salary_to"] is None
    assert result["average_salary"] is None
    assert result["salary_info"] == "Зарплата не указана"


def test_vacancy_to_dict_gross_false():
    """Тестирование to_dict с net-зарплатой."""
    data = {"name": "Net Job", "alternate_url": "", "salary": {"from": 80000, "to": 120000, "gross": False}}
    vacancy = Vacancy(data)
    result = vacancy.to_dict()

    assert "net" in result["salary_info"]
    assert result["gross"] is False


def test_vacancy_professional_roles():
    """Тестирование обработки профессиональных ролей."""
    data = {
        "name": "Dev",
        "alternate_url": "",
        "professional_roles": [{"name": "Разработчик ПО"}, {"name": "Team Lead"}],
    }
    vacancy = Vacancy(data)
    assert vacancy.professional_roles == ["Разработчик ПО", "Team Lead"]

    data_empty = {"name": "Simple", "alternate_url": "", "professional_roles": []}
    vacancy_empty = Vacancy(data_empty)
    assert vacancy_empty.professional_roles == []


def test_vacancy_experience():
    """Тестирование поля опыта работы."""
    data = {"name": "Job", "alternate_url": "", "experience": {"name": "Более 6 лет"}}
    vacancy = Vacancy(data)
    assert vacancy.experience == "Более 6 лет"

    data_no_exp = {"name": "Junior", "alternate_url": "", "experience": {}}
    vacancy_no_exp = Vacancy(data_no_exp)
    assert vacancy_no_exp.experience == "Не указан"


def test_vacancy_address_fields():
    """Тестирование полей адреса."""
    data = {
        "name": "Job",
        "alternate_url": "",
        "address": {"city": "Санкт-Петербург", "street": "Невская", "building": "5А"},
    }
    vacancy = Vacancy(data)
    assert vacancy.city == "Санкт-Петербург"
    assert vacancy.street == "Невская"
    assert vacancy.building == "5А"

    data_partial = {"name": "Job", "alternate_url": "", "address": {"city": "Казань"}}
    vacancy_partial = Vacancy(data_partial)
    assert vacancy_partial.city == "Казань"
    assert vacancy_partial.street == ""
    assert vacancy_partial.building == ""


def test_vacancy_employer_url_optional():
    """Тестирование необязательного поля employer_url."""
    data = {"name": "Job", "alternate_url": "", "employer": {"name": "Company", "alternate_url": None}}
    vacancy = Vacancy(data)
    assert vacancy.employer_url is None

    data_without = {"name": "Job", "alternate_url": "", "employer": {"name": "Company"}}
    vacancy_without = Vacancy(data_without)
    assert vacancy_without.employer_url is None


def test_vacancy_saved_format():
    """Тестирование загрузки вакансии из сохраненного формата."""
    saved_data = {
        "id": "123",
        "title": "Python Developer",
        "url": "https://hh.ru/vacancy/123",
        "employer_name": "TechCorp",
        "employer_url": "https://hh.ru/employer/456",
        "salary_from": 100000,
        "salary_to": 150000,
        "currency": "RUB",
        "gross": True,
        "city": "Москва",
        "street": "Ленина",
        "building": "10",
        "responsibilities": "Разработка приложений",
        "requirements": "Опыт Python",
        "professional_roles": ["Разработчик", "Backend"],
        "experience": "3-5 лет",
        "probation_period": "3 месяца",
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.id == "123"
    assert vacancy.title == "Python Developer"
    assert vacancy.url == "https://hh.ru/vacancy/123"
    assert vacancy.employer_name == "TechCorp"
    assert vacancy.salary_from == Decimal("100000")
    assert vacancy.salary_to == Decimal("150000")
    assert vacancy.city == "Москва"
    assert vacancy.professional_roles == ["Разработчик", "Backend"]


def test_vacancy_saved_format_string_salary():
    """Тестирование сохраненного формата со строковой зарплатой."""
    saved_data = {
        "id": "123",
        "title": "Dev",
        "url": "https://hh.ru/vacancy/123",
        "salary_from": "100000",
        "salary_to": "150000",
        "currency": "RUB",
        "gross": "true",
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.salary_from == Decimal("100000")
    assert vacancy.salary_to == Decimal("150000")
    assert vacancy.gross is True


def test_vacancy_saved_format_empty_salary():
    """Тестирование сохраненного формата с пустой зарплатой."""
    saved_data = {
        "id": "123",
        "title": "Dev",
        "url": "https://hh.ru/vacancy/123",
        "salary_from": "",
        "salary_to": None,
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.salary_from == Decimal("0")
    assert vacancy.salary_to == Decimal("0")


def test_vacancy_saved_format_professional_roles_string():
    """Тестирование сохраненного формата с профессиональными ролями как строкой."""
    saved_data = {
        "id": "123",
        "title": "Dev",
        "url": "https://hh.ru/vacancy/123",
        "professional_roles": "['Разработчик', 'Backend']",
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.professional_roles == ["Разработчик", "Backend"]


def test_vacancy_saved_format_professional_roles_invalid_string():
    """Тестирование сохраненного формата с невалидной строкой ролей."""
    saved_data = {
        "id": "123",
        "title": "Dev",
        "url": "https://hh.ru/vacancy/123",
        "professional_roles": "invalid string",
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.professional_roles == []


def test_vacancy_saved_format_without_probation():
    """Тестирование сохраненного формата без испытательного срока."""
    saved_data = {
        "id": "123",
        "title": "Dev",
        "url": "https://hh.ru/vacancy/123",
        "responsibilities": "Разработка",
        "requirements": "Испытательный срок 3 месяца",
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.probation_period == "3 месяца"


def test_vacancy_salary_conversion_error():
    """Тестирование обработки ошибок при конвертации зарплаты."""
    saved_data = {
        "id": "123",
        "title": "Dev",
        "url": "https://hh.ru/vacancy/123",
        "salary_from": "invalid",
        "salary_to": "also_invalid",
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.salary_from == Decimal("0")
    assert vacancy.salary_to == Decimal("0")


def test_vacancy_gross_false_string():
    """Тестирование gross как строки False."""
    saved_data = {
        "id": "123",
        "title": "Dev",
        "url": "https://hh.ru/vacancy/123",
        "gross": "false",
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.gross is False


def test_vacancy_gross_none():
    """Тестирование gross как None."""
    saved_data = {
        "id": "123",
        "title": "Dev",
        "url": "https://hh.ru/vacancy/123",
        "gross": None,
    }
    vacancy = Vacancy(saved_data)
    assert vacancy.gross is True


def test_vacancy_raw_format_no_salary():
    """Тестирование сырого формата без зарплаты."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "salary": None,
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.salary_from == Decimal("0")
    assert vacancy.salary_to == Decimal("0")
    assert vacancy.currency == "RUB"
    assert vacancy.gross is True


def test_vacancy_raw_format_salary_not_dict():
    """Тестирование сырого формата где salary не словарь."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "salary": "not a dict",
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.salary_from == Decimal("0")
    assert vacancy.salary_to == Decimal("0")


def test_vacancy_raw_format_float_salary():
    """Тестирование сырого формата с float зарплатой."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "salary": {"from": 100000.5, "to": 150000.7, "currency": "RUB"},
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.salary_from == Decimal("100000")
    assert vacancy.salary_to == Decimal("150000")


def test_vacancy_raw_format_no_address():
    """Тестирование сырого формата без адреса."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "address": None,
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.city == "Не указан"
    assert vacancy.street == ""
    assert vacancy.building == ""


def test_vacancy_raw_format_address_not_dict():
    """Тестирование сырого формата где address не словарь."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "address": "not a dict",
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.city == "Не указан"


def test_vacancy_raw_format_no_snippet():
    """Тестирование сырого формата без snippet."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "snippet": None,
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.responsibilities == ""
    assert vacancy.requirements == ""


def test_vacancy_raw_format_snippet_not_dict():
    """Тестирование сырого формата где snippet не словарь."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "snippet": "not a dict",
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.responsibilities == ""
    assert vacancy.requirements == ""


def test_vacancy_raw_format_no_experience():
    """Тестирование сырого формата без опыта."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "experience": None,
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.experience == "Не указан"


def test_vacancy_raw_format_experience_not_dict():
    """Тестирование сырого формата где experience не словарь."""
    raw_data = {
        "id": "123",
        "name": "Dev",
        "alternate_url": "https://hh.ru/vacancy/123",
        "experience": "not a dict",
    }
    vacancy = Vacancy(raw_data)
    assert vacancy.experience == "Не указан"


def test_vacancy_to_dict_with_zero_salary():
    """Тестирование to_dict с нулевой зарплатой."""
    data = {"name": "No Salary", "alternate_url": "", "salary": {"from": 0, "to": 0}}
    vacancy = Vacancy(data)
    result = vacancy.to_dict()
    assert result["salary_from"] is None
    assert result["salary_to"] is None
    assert result["average_salary"] is None
