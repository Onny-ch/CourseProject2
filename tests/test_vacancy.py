from decimal import Decimal

import pytest

from src.vacancy import Vacancy


def test_vacancy_init_minimal_data():
    """Тестирование инициализации с минимально необходимыми данными."""
    data = {"name": "Test Job"}
    vacancy = Vacancy(data)
    assert vacancy.title == "Test Job"
    assert vacancy.salary_from == Decimal("0")
    assert vacancy.city == "Не указан"


def test_vacancy_init_empty_name():
    """Проверка исключения при пустом названии вакансии."""
    data = {"name": ""}
    with pytest.raises(ValueError, match="Название вакансии не может быть пустым"):
        Vacancy(data)


def test_vacancy_init_whitespace_name():
    """Проверка обрезки пробелов в названии."""
    data = {"name": "  Python Dev  "}
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
    vacancy = Vacancy({"name": "Test"})
    assert vacancy._Vacancy__validate_salary(100000) == Decimal("100000")
    assert vacancy._Vacancy__validate_salary(None) == Decimal("0")
    assert vacancy._Vacancy__validate_salary("50000.50") == Decimal("50000.50")
    assert vacancy._Vacancy__validate_salary("") == Decimal("0")


def test_vacancy_clean_html():
    vacancy = Vacancy({"name": "Test"})
    text = "<p>Требуется <b>Python</b> разработчик</p>"
    cleaned = vacancy._Vacancy__clean_html(text)
    assert cleaned == "Требуется Python разработчик"
    assert vacancy._Vacancy__clean_html("") == ""
    assert vacancy._Vacancy__clean_html(None) == ""


def test_vacancy_extract_probation():
    vacancy = Vacancy({"name": "Test"})
    text1 = "Испытательный срок 3 месяца"
    assert vacancy._Vacancy__extract_probation(text1) == "3 месяца"


def test_vacancy_salary_info():
    """Тестирование свойства salary_info."""
    vacancy1 = Vacancy({"name": "No Salary"})
    assert vacancy1.salary_info == "Зарплата не указана"

    data2 = {
        "name": "Fixed",
        "salary": {"from": 100000, "to": 100000, "currency": "USD", "gross": False},
    }
    vacancy2 = Vacancy(data2)
    assert vacancy2.salary_info == "100,000 USD (net)"

    data3 = {
        "name": "Range",
        "salary": {"from": 80000, "to": 120000, "currency": "RUB", "gross": True},
    }
    vacancy3 = Vacancy(data3)
    assert vacancy3.salary_info == "от 80,000 до 120,000 RUB (gross)"


def test_vacancy_average_salary():
    vacancy1 = Vacancy({"name": "No Salary"})
    assert vacancy1.average_salary() == Decimal("0")

    data2 = {"name": "Fixed", "salary": {"from": 100000, "to": 100000}}
    vacancy2 = Vacancy(data2)
    assert vacancy2.average_salary() == Decimal("100000")

    data3 = {"name": "Range", "salary": {"from": 80000, "to": 120000}}
    vacancy3 = Vacancy(data3)
    assert vacancy3.average_salary() == Decimal("100000")


def test_vacancy_comparison_operators():
    v1 = Vacancy({"name": "A", "salary": {"from": 50000}})
    v2 = Vacancy({"name": "B", "salary": {"from": 100000}})
    v3 = Vacancy({"name": "C", "salary": {"from": 100000}})

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
    assert result["salary_from"] == 100000.0
    assert result["salary_to"] == 150000.0
    assert result["currency"] == "RUB"
    assert result["gross"] is True

    assert "Django" in result["responsibilities"]
    assert "PostgreSQL" in result["requirements"]

    assert result["average_salary"] == 125000.0

    assert result["city"] == "Москва"
    assert result["street"] == "Ленина"
    assert result["building"] == "10"

    assert result["professional_roles"] == []


def test_vacancy_to_dict_no_salary():
    """Тестирование to_dict когда зарплата не указана."""
    data = {"name": "No Salary Job", "salary": None}
    vacancy = Vacancy(data)
    result = vacancy.to_dict()

    assert result["salary_from"] is None
    assert result["salary_to"] is None
    assert result["average_salary"] is None
    assert result["salary_info"] == "Зарплата не указана"


def test_vacancy_to_dict_gross_false():
    """Тестирование to_dict с net-зарплатой."""
    data = {"name": "Net Job", "salary": {"from": 80000, "to": 120000, "gross": False}}
    vacancy = Vacancy(data)
    result = vacancy.to_dict()

    assert "net" in result["salary_info"]
    assert result["gross"] is False


def test_vacancy_professional_roles():
    """Тестирование обработки профессиональных ролей."""
    data = {
        "name": "Dev",
        "professional_roles": [{"name": "Разработчик ПО"}, {"name": "Team Lead"}],
    }
    vacancy = Vacancy(data)
    assert vacancy.professional_roles == ["Разработчик ПО", "Team Lead"]

    data_empty = {"name": "Simple", "professional_roles": []}
    vacancy_empty = Vacancy(data_empty)
    assert vacancy_empty.professional_roles == []


def test_vacancy_experience():
    """Тестирование поля опыта работы."""
    data = {"name": "Job", "experience": {"name": "Более 6 лет"}}
    vacancy = Vacancy(data)
    assert vacancy.experience == "Более 6 лет"

    data_no_exp = {"name": "Junior", "experience": {}}
    vacancy_no_exp = Vacancy(data_no_exp)
    assert vacancy_no_exp.experience == "Не указан"


def test_vacancy_address_fields():
    """Тестирование полей адреса."""
    data = {
        "name": "Job",
        "address": {"city": "Санкт-Петербург", "street": "Невская", "building": "5А"},
    }
    vacancy = Vacancy(data)
    assert vacancy.city == "Санкт-Петербург"
    assert vacancy.street == "Невская"
    assert vacancy.building == "5А"

    data_partial = {"name": "Job", "address": {"city": "Казань"}}
    vacancy_partial = Vacancy(data_partial)
    assert vacancy_partial.city == "Казань"
    assert vacancy_partial.street == ""
    assert vacancy_partial.building == ""


def test_vacancy_employer_url_optional():
    """Тестирование необязательного поля employer_url."""
    data = {"name": "Job", "employer": {"name": "Company", "alternate_url": None}}
    vacancy = Vacancy(data)
    assert vacancy.employer_url is None

    data_without = {"name": "Job", "employer": {"name": "Company"}}
    vacancy_without = Vacancy(data_without)
    assert vacancy_without.employer_url is None
