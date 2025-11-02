import ast
from decimal import Decimal
from typing import Any, Dict

from src.services import (
    clean_html,
    extract_probation_period,
    validate_title,
    validate_url,
)


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
        """Инициализация из JSON-объекта вакансий с HH.ru или из сохраненных данных."""

        if not isinstance(data, dict):
            raise TypeError(
                f"Ожидался словарь, получено: {type(data)} (значение: {repr(data)})"
            )

        is_saved_format = "url" in data or "employer_name" in data

        self.id = str(data.get("id", "")) if data.get("id") else ""
        title_value = (
            data.get("title")
            if is_saved_format
            else data.get("name", data.get("title", ""))
        )
        self.title = validate_title(title_value)

        if is_saved_format:
            self.url = validate_url(data.get("url", ""))
            self.employer_name = data.get("employer_name", "Не указано")
            self.employer_url = data.get("employer_url")

            value_from = data.get("salary_from")
            if value_from is None or value_from == "":
                value_from = 0
            else:
                try:
                    value_from = int(float(str(value_from)))
                except (ValueError, TypeError):
                    value_from = 0
            self.salary_from = Decimal(str(value_from))

            value_to = data.get("salary_to")
            if value_to is None or value_to == "":
                value_to = 0
            else:
                try:
                    value_to = int(float(str(value_to)))
                except (ValueError, TypeError):
                    value_to = 0
            self.salary_to = Decimal(str(value_to))

            self.currency = data.get("currency", "RUB")
            gross_val = data.get("gross")
            if isinstance(gross_val, str):
                self.gross = gross_val.lower() in ("true", "1", "yes", "да")
            else:
                self.gross = bool(gross_val) if gross_val is not None else True

            self.city = data.get("city", "Не указан")
            self.street = data.get("street", "")
            self.building = data.get("building", "")

            self.responsibilities = clean_html(data.get("responsibilities", ""))
            self.requirements = clean_html(data.get("requirements", ""))

            roles = data.get("professional_roles", [])
            if isinstance(roles, str):
                try:
                    roles = ast.literal_eval(roles)
                except (ValueError, SyntaxError):
                    roles = []
            if roles and isinstance(roles, list):
                self.professional_roles = [
                    role if isinstance(role, str) else str(role) for role in roles
                ]
            else:
                self.professional_roles = []

            self.experience = data.get("experience", "Не указан")

            probation = data.get("probation_period")
            if probation:
                self.probation_period = str(probation)
            else:
                self.probation_period = extract_probation_period(
                    self.responsibilities + " " + self.requirements
                )
        else:
            self.url = validate_url(data.get("alternate_url", ""))

            employer = data.get("employer")
            if employer and isinstance(employer, dict):
                self.employer_name = employer.get("name", "Не указано")
                self.employer_url = employer.get("alternate_url", None)
            else:
                self.employer_name = "Не указано"
                self.employer_url = None

            salary = data.get("salary")
            if salary and isinstance(salary, dict):
                value_from = salary.get("from")
                if value_from is None:
                    value_from = 0
                elif isinstance(value_from, float):
                    value_from = int(value_from)
                else:
                    try:
                        value_from = int(float(str(value_from)))
                    except (ValueError, TypeError):
                        value_from = 0
                self.salary_from = Decimal(str(value_from))

                value_to = salary.get("to")
                if value_to is None:
                    value_to = 0
                elif isinstance(value_to, float):
                    value_to = int(value_to)
                else:
                    try:
                        value_to = int(float(str(value_to)))
                    except (ValueError, TypeError):
                        value_to = 0
                self.salary_to = Decimal(str(value_to))

                self.currency = salary.get("currency", "RUB")
                self.gross = salary.get("gross", True)
            else:
                self.salary_from = Decimal("0")
                self.salary_to = Decimal("0")
                self.currency = "RUB"
                self.gross = True

            address = data.get("address")
            if address and isinstance(address, dict):
                self.city = address.get("city", "Не указан")
                self.street = address.get("street", "")
                self.building = address.get("building", "")
            else:
                self.city = "Не указан"
                self.street = ""
                self.building = ""

            snippet = data.get("snippet", {})
            if snippet and isinstance(snippet, dict):
                self.responsibilities = clean_html(snippet.get("responsibility", ""))
                self.requirements = clean_html(snippet.get("requirement", ""))
            else:
                self.responsibilities = ""
                self.requirements = ""

            roles = data.get("professional_roles", [])
            if roles and isinstance(roles, list):
                self.professional_roles = [
                    role.get("name", "") if isinstance(role, dict) else str(role)
                    for role in roles
                ]
            else:
                self.professional_roles = []

            experience = data.get("experience", {})
            if experience and isinstance(experience, dict):
                self.experience = experience.get("name", "Не указан")
            else:
                self.experience = "Не указан"

            self.probation_period = extract_probation_period(
                self.responsibilities + " " + self.requirements
            )

    @property
    def salary_info(self) -> str:
        if self.salary_from == 0 and self.salary_to == 0:
            return "Зарплата не указана"

        if self.salary_from == self.salary_to:
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
            "salary_from": (
                int(self.salary_from) if self.salary_from != Decimal("0") else None
            ),
            "salary_to": (
                int(self.salary_to) if self.salary_to != Decimal("0") else None
            ),
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
            "average_salary": (
                int(self.average_salary())
                if self.average_salary() != Decimal("0")
                else None
            ),
        }
        assert isinstance(data, dict), f"to_dict() вернул не словарь: {type(data)}"
        if not data["title"] or data["title"] == "Вакансия без названия":
            data["title"] = "Вакансия без названия"
        return data
