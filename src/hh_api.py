from abc import ABC, abstractmethod
from typing import List

import requests

from src.fileworker import JSONFileWorker, CSVFileWorker
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
        self.__params = {"text": "", "page": 0, "per_page": 100}  # Оптимизировано: больше вакансий за запрос
        self.__vacancies = []

    def __connect_to_api(self) -> requests.Response:
        """Приватный метод подключения к API. Проверяет статус-код ответа."""
        response = requests.get(
            self.__url,
            headers=self.__headers,
            params=self.__params,
            timeout=10
        )

        if response.status_code == 429:  # Too Many Requests
            raise requests.HTTPError("Превышен лимит запросов")
        elif response.status_code != 200:
            raise requests.HTTPError(f"Не удалось подключиться к API (код: {response.status_code})")

        return response

    def connect_to_api(self) -> requests.Response:
        """Подключиться к API и вернуть ответ."""
        return self.__connect_to_api()

    def load_vacancies(self, keyword: str):
        """Загрузить вакансии по ключевому слову."""
        self.__params["text"] = keyword
        self.__vacancies = []  # Очищаем предыдущие результаты
        page = 0
        max_pages = 20  # Ограничение для предотвращения чрезмерных запросов

        while page < max_pages:
            self.__params["page"] = page
            try:
                # Используем приватный метод подключения к API
                response = self.__connect_to_api()

                data = response.json()
                items = data.get("items", [])
                if not items:
                    break

                for item in items:
                    # Проверка: item должен быть словарем
                    if not isinstance(item, dict):
                        print(f"Пропущена некорректная запись (не словарь): {repr(item)}")
                        continue

                    try:
                        # Создаем объект Vacancy, который обработает сырые данные
                        vacancy = Vacancy(item)
                        self.__vacancies.append(vacancy)
                    except (ValueError, TypeError, KeyError) as e:
                        print(f"Пропущена некорректная вакансия: {e}")
                        continue

                # Проверяем, есть ли еще страницы
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
        """Сохранить вакансии в файл с помощью file_worker.

        Обрабатывает данные через класс Vacancy и сохраняет обработанные данные.
        """
        if not self.__vacancies:
            print("Нет вакансий для сохранения.")
            return

        # Преобразуем объекты Vacancy в словари через to_dict()
        processed_data = [vacancy.to_dict() for vacancy in self.__vacancies]

        # Если переданный filename отличается от текущего, создаем новый file_worker
        if filename != self.__file_worker.filename:
            # Определяем тип текущего file_worker и создаем новый экземпляр
            if isinstance(self.__file_worker, JSONFileWorker):
                file_worker = JSONFileWorker(filename)
            elif isinstance(self.__file_worker, CSVFileWorker):
                file_worker = CSVFileWorker(filename)
            else:
                # Если неизвестный тип, используем текущий file_worker
                file_worker = self.__file_worker
            file_worker.save_data(processed_data)
        else:
            self.__file_worker.save_data(processed_data)

    def clear_vacancies(self) -> None:
        """Очистить список вакансий."""
        self.__vacancies = []

