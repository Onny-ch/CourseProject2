import ast
import json
from decimal import Decimal
from typing import Any, Dict, Optional

from src.services import (clean_html, extract_probation_period, validate_title,
                          validate_url)


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
        """Инициализация из словаря данных вакансии."""

        if not isinstance(data, dict):
            raise TypeError(
                f"Ожидался словарь, получено: {type(data)} (значение: {repr(data)})"
            )

        # ID
        id_val = data.get("id")
        self.id = str(id_val) if id_val is not None else ""

        # Название вакансии (может быть в "title" или "name")
        title_val = data.get("title") or data.get("name")
        if title_val is None or (
            isinstance(title_val, str) and title_val.lower() in ("none", "null", "")
        ):
            title_val = ""
        else:
            title_val = str(title_val).strip()
        self.title = validate_title(title_val)

        # URL (может быть в "url" или "alternate_url")
        url_val = data.get("url") or data.get("alternate_url", "")
        self.url = validate_url(url_val if url_val else "")

        # Работодатель (может быть в "employer_name" или вложенном объекте "employer")
        employer_obj = data.get("employer")
        if employer_obj and isinstance(employer_obj, dict):
            employer_name_val = employer_obj.get("name")
            self.employer_url = employer_obj.get("url")
        else:
            employer_name_val = data.get("employer_name")
            self.employer_url = data.get("employer_url")

        if employer_name_val is None or (
            isinstance(employer_name_val, str)
            and employer_name_val.lower() in ("none", "null", "not specified")
        ):
            self.employer_name = "Не указано"
        else:
            self.employer_name = str(employer_name_val)

        # Зарплата (может быть в плоских полях или вложенном объекте "salary")
        salary_obj = data.get("salary")
        if salary_obj and isinstance(salary_obj, dict):
            salary_from_raw = salary_obj.get("from")
            salary_to_raw = salary_obj.get("to")
            currency_val = salary_obj.get("currency")
            self.currency = (
                str(currency_val)
                if currency_val and str(currency_val).lower() not in ("none", "null")
                else "RUB"
            )
            gross_val = salary_obj.get("gross")
            if gross_val is None:
                self.gross = True
            elif isinstance(gross_val, str):
                self.gross = gross_val.lower().strip() in ("true", "1", "yes", "да")
            else:
                self.gross = bool(gross_val)
        else:
            # Плоские поля (для обратной совместимости)
            salary_from_raw = data.get("salary_from")
            salary_to_raw = data.get("salary_to")
            currency_val = data.get("currency")
            self.currency = (
                str(currency_val)
                if currency_val and str(currency_val).lower() not in ("none", "null")
                else "RUB"
            )
            gross_val = data.get("gross")
            if gross_val is None:
                self.gross = True
            elif isinstance(gross_val, str):
                self.gross = gross_val.lower().strip() in ("true", "1", "yes", "да")
            else:
                self.gross = bool(gross_val)

        # Преобразуем зарплату в Decimal при инициализации
        self.salary_from = self._normalize_salary_value(salary_from_raw)
        self.salary_to = self._normalize_salary_value(salary_to_raw)

        # Обязанности и требования (могут быть в плоских полях или вложенном объекте "snippet")
        snippet_obj = data.get("snippet")
        if snippet_obj and isinstance(snippet_obj, dict):
            responsibilities_val = snippet_obj.get("responsibility", "")
            requirements_val = snippet_obj.get("requirement", "")
        else:
            responsibilities_val = data.get("responsibilities", "")
            requirements_val = data.get("requirements", "")

        self.responsibilities = clean_html(
            str(responsibilities_val) if responsibilities_val else ""
        )
        self.requirements = clean_html(
            str(requirements_val) if requirements_val else ""
        )

        # Профессиональные роли
        # Формат: список строк вида "{'id': '156', 'name': 'BI Analyst, Data Analyst'}"
        # или строка вида "['Разработчик', 'Backend']"
        roles = data.get("professional_roles", [])
        self.professional_roles = []
        if isinstance(roles, str):
            # Если roles это строка, пытаемся распарсить как список
            try:
                roles = ast.literal_eval(roles)
            except (ValueError, SyntaxError):
                roles = []

        if roles and isinstance(roles, list):
            for role in roles:
                if isinstance(role, str):
                    # Пытаемся распарсить строку как словарь
                    try:
                        # Заменяем одинарные кавычки на двойные для JSON
                        role_str = role.replace("'", '"')
                        role_dict = json.loads(role_str)
                        if isinstance(role_dict, dict) and "name" in role_dict:
                            self.professional_roles.append(role_dict["name"])
                        else:
                            self.professional_roles.append(role)
                    except (json.JSONDecodeError, ValueError, SyntaxError):
                        # Если не получилось распарсить, пытаемся через ast.literal_eval
                        try:
                            role_dict = ast.literal_eval(role)
                            if isinstance(role_dict, dict) and "name" in role_dict:
                                self.professional_roles.append(role_dict["name"])
                            else:
                                self.professional_roles.append(role)
                        except (ValueError, SyntaxError):
                            # Если всё равно не получилось, используем строку как есть
                            self.professional_roles.append(role)
                elif isinstance(role, dict):
                    # Если это уже словарь
                    if "name" in role:
                        self.professional_roles.append(role["name"])
                    else:
                        self.professional_roles.append(str(role))
                else:
                    self.professional_roles.append(str(role))

        # Опыт работы
        # Формат: словарь с ключами "id" и "name"
        experience_val = data.get("experience")
        if experience_val is None:
            self.experience = "Не указан"
        elif isinstance(experience_val, dict):
            self.experience = experience_val.get("name", "Не указан")
        elif isinstance(experience_val, str):
            # Если это строка, проверяем валидность
            if experience_val.lower() in ("none", "null"):
                self.experience = "Не указан"
            else:
                # Если это не валидная строка (например, "not a dict"), считаем невалидным
                self.experience = "Не указан"
        else:
            # Если experience не словарь и не None, считаем его невалидным
            self.experience = "Не указан"

        # Испытательный срок
        probation_val = data.get("probation_period")
        if probation_val is None or (
            isinstance(probation_val, str)
            and probation_val.lower() in ("none", "null", "")
        ):
            # Пытаемся извлечь из описания
            self.probation_period = extract_probation_period(
                self.responsibilities + " " + self.requirements
            )
        else:
            self.probation_period = str(probation_val)

        # Адрес (может быть в плоских полях или вложенном объекте "address")
        address_obj = data.get("address")
        if address_obj and isinstance(address_obj, dict):
            city_val = address_obj.get("city")
            street_val = address_obj.get("street")
            building_val = address_obj.get("building")
        else:
            city_val = data.get("city")
            street_val = data.get("street")
            building_val = data.get("building")

        if city_val is None or (
            isinstance(city_val, str)
            and city_val.lower() in ("none", "null", "not specified")
        ):
            self.city = "Не указан"
        else:
            self.city = str(city_val)

        self.street = (
            str(street_val)
            if street_val and str(street_val).lower() not in ("none", "null")
            else ""
        )
        self.building = (
            str(building_val)
            if building_val and str(building_val).lower() not in ("none", "null")
            else ""
        )

    def _normalize_salary_value(self, salary_val) -> Optional[Decimal]:
        """Нормализует значение зарплаты: преобразует в Decimal или возвращает None."""
        if salary_val is None:
            return Decimal("0")
        if isinstance(salary_val, (int, float)):
            return Decimal(
                str(int(salary_val))
            )  # Преобразуем float в int, затем в Decimal
        if isinstance(salary_val, str):
            salary_str = salary_val.strip()
            if salary_str in ("none", "null", ""):
                return Decimal("0")
            try:
                # Пытаемся преобразовать строку в число
                num_val = float(salary_str)
                return Decimal(str(int(num_val)))
            except (ValueError, TypeError):
                return Decimal("0")
        try:
            return Decimal(str(int(salary_val)))
        except (ValueError, TypeError):
            return Decimal("0")

    def _get_numeric_salary(self, salary_val) -> Decimal:
        """Преобразует значение зарплаты в Decimal для вычислений."""
        if salary_val is None:
            return Decimal("0")
        if isinstance(salary_val, (int, float)):
            return Decimal(str(salary_val))
        if isinstance(salary_val, str):
            salary_str = salary_val.strip().lower()
            if salary_str in ("none", "null", ""):
                return Decimal("0")
            try:
                return Decimal(salary_str)
            except (ValueError, TypeError):
                return Decimal("0")
        try:
            return Decimal(str(salary_val))
        except (ValueError, TypeError):
            return Decimal("0")

    @property
    def salary_info(self) -> str:
        """Возвращает строковое представление зарплаты."""
        salary_from_num = self._get_numeric_salary(self.salary_from)
        salary_to_num = self._get_numeric_salary(self.salary_to)

        # Если оба значения равны 0 или None, зарплата не указана
        if salary_from_num == Decimal("0") and salary_to_num == Decimal("0"):
            return "Зарплата не указана"

        # Если from и to равны, показываем одну сумму
        if salary_from_num == salary_to_num and salary_from_num > 0:
            amount = f"{salary_from_num:,.0f}"
            return f"{amount} {self.currency} ({'gross' if self.gross else 'net'})"
        else:
            from_amount = f"{salary_from_num:,.0f}" if salary_from_num > 0 else None
            to_amount = f"{salary_to_num:,.0f}" if salary_to_num > 0 else None

            if from_amount and to_amount:
                return f"от {from_amount} до {to_amount} {self.currency} ({'gross' if self.gross else 'net'})"
            elif from_amount:
                return f"от {from_amount} {self.currency} ({'gross' if self.gross else 'net'})"
            elif to_amount:
                return f"до {to_amount} {self.currency} ({'gross' if self.gross else 'net'})"
            else:
                return "зарплата не указана"

    def average_salary(self) -> Decimal:
        """Вычисляет среднюю зарплату."""
        salary_from_num = self._get_numeric_salary(self.salary_from)
        salary_to_num = self._get_numeric_salary(self.salary_to)

        if salary_from_num == Decimal("0") and salary_to_num == Decimal("0"):
            return Decimal("0")
        return (salary_from_num + salary_to_num) / 2

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
        # Преобразуем Decimal зарплату в int или None (если 0)
        salary_from_dict = (
            int(self.salary_from) if self.salary_from != Decimal("0") else None
        )
        salary_to_dict = int(self.salary_to) if self.salary_to != Decimal("0") else None

        data = {
            "id": self.id,
            "title": self.title,
            "url": self.url,
            "employer_name": self.employer_name,
            "employer_url": self.employer_url,
            "salary_from": salary_from_dict,
            "salary_to": salary_to_dict,
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
