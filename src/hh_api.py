from abc import ABC, abstractmethod
from typing import List

import requests

from src.vacancy import Vacancy


class Parser(ABC):
    """Абстрактный базовый класс для парсеров вакансий."""

    @abstractmethod
    def connect_to_api(self) -> requests.Response:
        """Подключиться к API и вернуть ответ."""
        pass

    @abstractmethod
    def load_vacancies(self, keyword: str) -> None:
        """Загрузить вакансии по ключевому слову."""
        pass

    @abstractmethod
    def get_vacancies(self) -> List[Vacancy]:
        """Вернуть список собранных вакансий."""
        pass


class HeadHunterAPI(Parser):
    """Класс для работы с API HeadHunter"""

    def __init__(self, file_worker):
        self.__file_worker = file_worker
        self.__url = "https://api.hh.ru/vacancies"
        self.__headers = {"User-Agent": "HH-User-Agent"}
        self.__params = {
            "text": "",
            "page": 0,
            "per_page": 100,
        }
        self.__vacancies = []

    def __connect_to_api(self) -> requests.Response:
        """Приватный метод подключения к API. Проверяет статус-код ответа."""
        response = requests.get(
            self.__url, headers=self.__headers, params=self.__params, timeout=10
        )

        if response.status_code == 429:
            raise requests.HTTPError("Превышен лимит запросов")
        elif response.status_code != 200:
            raise requests.HTTPError(
                f"Не удалось подключиться к API (код: {response.status_code})"
            )

        return response

    def connect_to_api(self) -> requests.Response:
        """Подключиться к API и вернуть ответ."""
        return self.__connect_to_api()

    def load_vacancies(self, keyword: str):
        """Загрузить вакансии по ключевому слову."""
        self.__params["text"] = keyword
        self.__vacancies = []
        page = 0
        max_pages = 20

        while page < max_pages:
            self.__params["page"] = page
            try:
                response = self.__connect_to_api()

                data = response.json()
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    if not isinstance(item, dict):
                        print(
                            f"Пропущена некорректная запись (не словарь): {repr(item)}"
                        )
                        continue

                    try:
                        vacancy = Vacancy(item)
                        self.__vacancies.append(vacancy)
                    except (ValueError, TypeError, KeyError) as e:
                        print(f"Пропущена некорректная вакансия: {e}")
                        continue

                pages = data.get("pages", 0)
                if page >= pages - 1:
                    break

                page += 1

            except requests.HTTPError as e:
                print(f"{e}")
                break
            except requests.Timeout:
                print("Превышено время ожидания ответа от API.")
                break
            except requests.RequestException as e:
                print(f"Ошибка при загрузке вакансий: {e}")
                break

    def get_vacancies(self) -> List[Vacancy]:
        """Вернуть список собранных вакансий."""
        return self.__vacancies

    def save_vacancies(self, filename: str) -> None:
        """Сохранить вакансии в файл с помощью file_worker."""
        raw_data = [vacancy.to_dict() for vacancy in self.__vacancies]
        if raw_data:
            self.__file_worker.save_data(raw_data)
        else:
            print("Нет вакансий для сохранения.")

    def clear_vacancies(self) -> None:
        """Очистить список вакансий."""
        self.__vacancies = []
