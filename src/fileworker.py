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
        # Создаем директорию, если её нет
        dir_path = os.path.dirname(filename)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

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
                print(
                    f"[ERROR] Запись №{i} не словарь: type={type(item)}, value={repr(item)}"
                )
                raise ValueError("Данные для сохранения должны быть словарями")

        try:
            if os.path.exists(self.__filename):
                with open(self.__filename, "r", encoding="utf-8") as f:
                    try:
                        existing_data = json.load(f)
                    except json.JSONDecodeError:
                        existing_data = []
            else:
                existing_data = []

            existing_ids = {item.get("id") for item in existing_data if item.get("id")}
            unique_new = [item for item in data if item.get("id") not in existing_ids]

            combined_data = existing_data + unique_new

            with open(self.__filename, "w", encoding="utf-8") as f:
                json.dump(combined_data, f, ensure_ascii=False, indent=4)

        except IOError as e:
            print(f"[ERROR] Запись в файл {self.__filename}: {e}")

    def remove_data(self, condition: Callable[[Dict[str, Any]], bool]) -> None:
        """Удалить данные, удовлетворяющие условию."""

        data = self.load_data()
        filtered_data = [item for item in data if not condition(item)]
        try:
            with open(self.__filename, "w", encoding="utf-8") as f:
                json.dump(filtered_data, f, ensure_ascii=False, indent=4)
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


class CSVFileWorker(AbstractFileWorker):
    def __init__(self, filename: str = "data/vacancies.csv"):
        self.__filename = filename  # приватный атрибут
        # Создаем директорию, если её нет
        dir_path = os.path.dirname(filename)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)

    @property
    def filename(self) -> str:
        """Геттер для приватного атрибута filename."""
        return self.__filename

    def load_data(self) -> List[Dict[str, Any]]:
        if not os.path.exists(self.__filename):
            return []
        try:
            with open(self.__filename, "r", newline="", encoding="utf-8") as f:
                return list(csv.DictReader(f))
        except (IOError, csv.Error) as e:
            print(f"[ERROR] Чтение CSV файла {self.__filename}: {e}")
            return []

    def save_data(self, data: List[Dict[str, Any]]) -> None:
        """Сохранить данные в CSV-файл (без дублирования по id)."""
        if not data:
            return

        # Проверка: все элементы должны быть словарями
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                print(
                    f"[ERROR] Запись №{i} не словарь: type={type(item)}, value={repr(item)}"
                )
                raise ValueError("Данные для сохранения должны быть словарями")

        try:
            # Загружаем существующие данные
            if os.path.exists(self.__filename):
                existing_data = self.load_data()
                existing_ids = {
                    item.get("id") for item in existing_data if item.get("id")
                }
                unique_new = [
                    item for item in data if item.get("id") not in existing_ids
                ]
                combined_data = existing_data + unique_new
            else:
                combined_data = data

            if not combined_data:
                return

            # Определяем все возможные поля из всех записей
            all_fieldnames = set()
            for item in combined_data:
                all_fieldnames.update(item.keys())
            fieldnames = sorted(all_fieldnames)

            with open(self.__filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(combined_data)
        except (IOError, csv.Error) as e:
            print(f"Ошибка записи в файл {self.__filename}: {e}")

    def remove_data(self, condition: Callable[[Dict[str, Any]], bool]) -> None:
        """Удалить данные, удовлетворяющие условию."""
        data = self.load_data()
        filtered = [row for row in data if not condition(row)]

        if not filtered:
            # Если после фильтрации ничего не осталось, очищаем файл
            self.clear_file()
            return

        try:
            # Определяем все возможные поля из всех записей
            all_fieldnames = set()
            for item in filtered:
                all_fieldnames.update(item.keys())
            fieldnames = sorted(all_fieldnames)

            with open(self.__filename, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(filtered)
        except (IOError, csv.Error) as e:
            print(f"Ошибка удаления данных из {self.__filename}: {e}")

    def clear_file(self) -> None:
        """Полностью очищает CSV-файл, удаляя все строки (кроме заголовка, если есть)."""
        try:
            if os.path.exists(self.__filename):
                sample_data = self.load_data()
                if sample_data and len(sample_data) > 0:
                    fieldnames = list(sample_data[0].keys())
                    with open(self.__filename, "w", newline="", encoding="utf-8") as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                else:
                    # Если файл пустой или не существует, просто создаем пустой файл
                    with open(self.__filename, "w", newline="", encoding="utf-8") as f:
                        pass
            else:
                # Файл не существует, создаем пустой
                with open(self.__filename, "w", newline="", encoding="utf-8") as f:
                    pass
            print(f"Файл {self.__filename} успешно очищен!")
        except IOError as e:
            print(f"Ошибка при очистке файла {self.__filename}: {e}")
