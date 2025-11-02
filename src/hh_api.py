import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List

import requests

from src.vacancy import Vacancy


class Parser(ABC):
    """Абстрактный базовый класс для парсеров вакансий."""

    @abstractmethod
    def load_vacancies(self, keyword: str) -> None:
        """Загрузить вакансии по ключевому слову."""
        pass

    @abstractmethod
    def get_vacancies(self) -> List[Dict[str, Any]]:
        """Вернуть список собранных вакансий."""
        pass


class HeadHunterAPI(Parser):
    """Класс для работы с API HeadHunter"""

    def __init__(self, file_worker):
        self.__file_worker = file_worker
        self.__url = "https://api.hh.ru/vacancies"
        self.__headers = {"User-Agent": "HH-User-Agent"}
        self.__params = {"text": "", "page": 0, "per_page": 1}
        self.__vacancies = []

    def load_vacancies(self, keyword: str):
        self.__params["text"] = keyword
        page = 0
        while page < 1:
            self.__params["page"] = page
            try:
                response = requests.get(self.__url, params=self.__params)
                if response.status_code != 200:
                    print("Не удалось подключиться к API")
                    break

                data = response.json()
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    # Проверка: item должен быть словарем
                    if not isinstance(item, dict):
                        print(f"Пропущена некорректная запись (не словарь): {repr(item)}")
                        continue

                    vacancy = Vacancy(item)  # Теперь безопасно
                    self.__vacancies.append(vacancy)

                page += 1
            except requests.RequestException as e:
                print(f"Ошибка при загрузке вакансий: {e}")
                break

    def get_vacancies(self) -> List[Dict[str, Any]]:
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

    def __connect_to_api(self) -> requests.Response:
        """Приватный метод подключения к API. Проверяет статус-код ответа."""
        for attempt in range(3):  # 3 попытки
            try:
                response = requests.get(
                    self.__url, headers=self.__headers, params=self.__params, timeout=10
                )

                if response.status_code == 200:
                    return response
            except requests.RequestException:
                pass
            time.sleep(1)  # Пауза между попытками
        raise requests.HTTPError("Не удалось подключиться к API после 3 попыток")
