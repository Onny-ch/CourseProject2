import re
from decimal import Decimal
from typing import Any, Dict, Optional, Union


class Vacancy:
    __slots__ = (
        "id",
        "title",
        "url",
        "employer_name",
        "employer_url",
        "salary_from",
        "salary_to",
        "currency",
        "gross",
        "responsibilities",
        "requirements",
        "professional_roles",
        "experience",
        "probation_period",
        "city",
        "street",
        "building",
    )

    def __init__(self, data: Dict[str, Any]):
        """Инициализация из JSON-объекта вакансий с HH.ru."""

        if not isinstance(data, dict):
            raise TypeError(f"Ожидался словарь, получено: {type(data)} (значение: {repr(data)})")

        self.id = data.get("id", "")
        self.title = self.__validate_title(data.get("title", ""))
        self.url = self.__validate_url(data.get("alternate_url", ""))

        # Работодатель
        employer = data.get("employer", {})
        self.employer_name = employer.get("name", "Не указано")
        self.employer_url = employer.get("alternate_url", None)

        # Зарплата
        salary = data.get("salary")
        if salary is None:
            salary = {}
        elif not isinstance(salary, dict):
            salary = {}

        # Обработка salary_from
        value_from = salary.get("from")
        if value_from is None:
            value_from = 0
        elif isinstance(value_from, float):
            value_from = int(value_from)
        self.salary_from = Decimal(str(value_from))

        # Аналогично для salary_to
        value_to = salary.get("to")
        if value_to is None:
            value_to = 0
        elif isinstance(value_to, float):
            value_to = int(value_to)
        self.salary_to = Decimal(str(value_to))

        self.currency = salary.get("currency", "RUB")
        self.gross = salary.get("gross", True)

        # Адрес
        address = data.get("address")
        if address is None:
            address = {}
        elif not isinstance(address, dict):
            address = {}

        self.city = address.get("city", "Не указан")
        self.street = address.get("street", "")
        self.building = address.get("building", "")

        # Обязанности и требования
        snippet = data.get("snippet", {})
        self.responsibilities = self.__clean_html(snippet.get("responsibility", ""))
        self.requirements = self.__clean_html(snippet.get("requirement", ""))

        # Профессиональные роли
        roles = data.get("professional_roles", [])
        self.professional_roles = [role["name"] for role in roles] if roles else []

        # Опыт работы
        experience = data.get("experience", {})
        self.experience = experience.get("name", "Не указан")

        # Испытательный срок
        self.probation_period = self.__extract_probation(
            self.responsibilities + " " + self.requirements
        )

    def __validate_title(self, title: str) -> str:
        if not title or not title.strip():
            return "Вакансия без названия"
        return title.strip()

    def __validate_url(self, url: str) -> str:
        if url and not re.match(r"^https?://", url):
            raise ValueError(f"Некорректный URL: {url}")
        return url or ""

    def __validate_salary(self, value: Optional[Union[int, float]]) -> Decimal:
        if value is None:
            return Decimal("0")
        try:
            return Decimal(str(value))
        except:
            return Decimal("0")

    def __clean_html(self, text: str) -> str:
        """Удаляет HTML-теги из текста"""
        if not text:
            return ""
        return re.sub(r"<[^>]+>", "", text).strip()

    def _Vacancy__extract_probation(self, text: str) -> Optional[str]:
        import re
        # Ищем шаблоны: "3 месяца", "2 недели", "1 день" и т.п.
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

    @property
    def salary_info(self) -> str:
        if self.salary_from == 0 and self.salary_to == 0:
            return "Зарплата не указана"

        if self.salary_from == self.salary_to:
            # Форматируем с разделителем тысяч
            amount = f"{self.salary_from:,.0f}"
            return f"{amount} {self.currency} ({'gross' if self.gross else 'net'})"
        else:
            from_amount = f"{self.salary_from:,.0f}"
            to_amount = f"{self.salary_to:,.0f}"
            return (
                f"от {from_amount} до {to_amount} "
                f"{self.currency} ({'gross' if self.gross else 'net'})"
            )

    def average_salary(self) -> Decimal:
        if self.salary_from == 0 and self.salary_to == 0:
            return Decimal("0")
        return (self.salary_from + self.salary_to) / 2

    def __eq__(self, other) -> bool:
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self.average_salary() == other.average_salary()

    def __lt__(self, other) -> bool:
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self.average_salary() < other.average_salary()

    def __le__(self, other) -> bool:
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self.average_salary() <= other.average_salary()

    def __gt__(self, other) -> bool:
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self.average_salary() > other.average_salary()

    def __ge__(self, other) -> bool:
        if not isinstance(other, Vacancy):
            return NotImplemented
        return self.average_salary() >= other.average_salary()

    def __str__(self) -> str:
        salary_part = self.salary_info
        city_part = self.city if self.city != "Не указан" else ""
        parts = [self.title, salary_part, city_part]
        return " | ".join(filter(None, parts))

    def __repr__(self) -> str:
        return (
            f"Vacancy(title='{self.title}', "
            f"salary_from={self.salary_from}, "
            f"salary_to={self.salary_to}, "
            f"city='{self.city}')"
        )

    def to_dict(self) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "employer_name": self.employer_name,
            "employer_url": self.employer_url,
            # Преобразуем Decimal в int (не float!)
            "salary_from": int(self.salary_from) if self.salary_from != Decimal("0") else None,
            "salary_to": int(self.salary_to) if self.salary_to != Decimal("0") else None,
            "currency": self.currency,
            "gross": self.gross,
            "responsibilities": self.responsibilities,
            "requirements": self.requirements,
            "professional_roles": self.professional_roles,
            "experience": self.experience,
            "probation_period": self.probation_period,
            "city": self.city,
            "street": self.street,
            "building": self.building,
            "salary_info": self.salary_info,
            "average_salary": int(self.average_salary()) if self.average_salary() != Decimal("0") else None
        }
        assert isinstance(data, dict), f"to_dict() вернул не словарь: {type(data)}"
        if not data["title"] or data["title"] == "Вакансия без названия":
            data["title"] = "Вакансия без названия"
        return data
