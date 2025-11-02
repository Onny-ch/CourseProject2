import csv
import json
import os
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List


class AbstractFileWorker(ABC):
    """
    Абстрактный базовый класс для работы с файлами.
    Задаёт интерфейс для чтения, записи и удаления данных.
    """

    @abstractmethod
    def load_data(self) -> List[Dict[str, Any]]:
        """Загрузить данные из файла."""
        pass

    @abstractmethod
    def save_data(self, data: List[Dict[str, Any]]) -> None:
        """Сохранить данные в файл (без дублирования)."""
        pass

    @abstractmethod
    def remove_data(self, condition: Callable[[Dict[str, Any]], bool]) -> None:
        """Удалить данные по условию."""
        pass

    @abstractmethod
    def clear_file(self) -> None:
        """Полностью очистить файл."""
        pass


class JSONFileWorker(AbstractFileWorker):
    """
    Класс для работы с JSON-файлами.
    - Не перезаписывает файл при каждом запуске.
    - Избегает дублирования вакансий.
    - Использует приватный атрибут filename.
    """

    def __init__(self, filename: str = "data/vacancies.json"):
        self.__filename = filename  # приватный атрибут

    @property
    def filename(self) -> str:
        """Геттер для приватного атрибута filename."""

        return self.__filename

    def load_data(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.__filename):
            return []
        try:
            with open(self.__filename, "r", encoding="utf-8") as f:
                data = json.load(f)

            print(f"[DEBUG] Загружено {len(data)} записей. Типы:")
            for i, item in enumerate(data):
                print(f"  [{i}] type={type(item).__name__}, id={item.get('id', 'нет')}")

            if not isinstance(data, list):
                print(f"[ERROR] Корневой элемент не список: {type(data)}")
                return []
            return data
        except (json.JSONDecodeError, IOError) as e:
            print(f"[ERROR] Чтение файла {self.__filename}: {e}")
            return []

    def save_data(self, data: List[Dict[str, Any]]) -> None:
        # Проверка: все элементы должны быть словарями
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                print(f"[ERROR] Запись №{i} не словарь: type={type(item)}, value={repr(item)}")
                raise ValueError("Данные для сохранения должны быть словарями")

        try:
            if os.path.exists(self.__filename):
                with open(self.__filename, 'r', encoding='utf-8') as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []
            else:
                existing_data = []

            existing_ids = {item.get('id') for item in existing_data if item.get('id')}
            unique_new = [item for item in data if item.get('id') not in existing_ids]

            combined_data = existing_data + unique_new

            with open(self.__filename, 'w', encoding='utf-8') as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=4)

        except IOError as e:
            print(f"[ERROR] Запись в файл {self.__filename}: {e}")

    def remove_data(self, condition: Callable[[Dict[str, Any]], bool]) -> None:
        """Удалить данные, удовлетворяющие условию."""

        data = self.load_data()
        filtered_data = [item for item in data if not condition(item)]
        try:
            with open(self.__filename, "w", encoding="utf-8") as f:
                json.dump(filtered_data, f, ensure_ascii=False)
        except IOError as e:
            print(f"Ошибка удаления данных из {self.__filename}: {e}")

    def clear_file(self) -> None:
        """Полностью очищает файл, записывая пустой список."""
        try:
            with open(self.__filename, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=4)
            print(f"Файл {self.__filename} успешно очищен!")
        except IOError as e:
            print(f"Ошибка при очистке файла {self.__filename}: {e}")
        except Exception as e:
            print(f"Неожиданная ошибка при очистке: {e}")

    def __remove_duplicates(
        self, existing: List[Dict[str, Any]], new: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Удалить дубликаты между существующими и новыми данными.
        Дубликаты определяются по полю 'id' вакансии.
        """

        existing_ids = {item.get("id") for item in existing if item.get("id")}
        unique_new = [item for item in new if item.get("id") not in existing_ids]
        return existing + unique_new


class CSVFileWorker(AbstractFileWorker):
    def __init__(self, filename: str = "data/vacancies.csv"):
        self.__filename = filename

    def load_data(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.__filename):
            return []
        with open(self.__filename, "r", newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))

    def save_data(self, data: List[Dict[str, Any]]) -> None:
        try:
            with open(self.__filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=data[0].keys())
                writer.writeheader()
                writer.writerows(data)
        except IOError as e:
            print(f"Ошибка записи в файл {self.__filename}: {e}")

    def remove_data(self, condition: Callable[[Dict[str, Any]], bool]) -> None:
        data = self.load_data()
        filtered = [row for row in data if not condition(row)]
        self.save_data(filtered)

    def clear_file(self) -> None:
        """Полностью очищает CSV-файл, удаляя все строки (кроме заголовка, если есть)."""

        try:
            sample_data = self.load_data()
            if sample_data:
                fieldnames = sample_data[0].keys()
                with open(self.__filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
            else:
                open(self.__filename, "w").close()
            print(f"Файл {self.__filename} успешно очищен!")
        except IOError as e:
            print(f"Ошибка при очистке файла {self.__filename}: {e}")
