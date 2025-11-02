import csv
import json
import os
from unittest.mock import patch

import pytest

from src.fileworker import CSVFileWorker, JSONFileWorker


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Очистка тестовых файлов после выполнения тестов."""
    test_files = [
        "data/test_vacancies.json",
        "data/test_vacancies.csv",
        "data/test_vacancies_empty.json",
        "data/test_vacancies_corrupted.json",
    ]
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)


def test_json_load_data_file_not_exists():
    """Проверка загрузки из несуществующего JSON‑файла."""
    worker = JSONFileWorker("data/nonexistent.json")
    data = worker.load_data()
    assert data == []


def test_json_load_data_empty_file():
    """Проверка загрузки пустого JSON‑файла."""
    with open("data/test_vacancies_empty.json", "w", encoding="utf-8") as f:
        f.write("")
    worker = JSONFileWorker("data/test_vacancies_empty.json")
    data = worker.load_data()
    assert data == []


def test_json_load_data_corrupted_json():
    """Проверка загрузки некорректного JSON‑файла."""
    with open("data/test_vacancies_corrupted.json", "w", encoding="utf-8") as f:
        f.write("{invalid json}")
    worker = JSONFileWorker("data/test_vacancies_corrupted.json")
    data = worker.load_data()
    assert data == []


def test_json_save_data_new_file():
    """Проверка сохранения данных в новый JSON‑файл."""
    worker = JSONFileWorker("data/test_vacancies.json")
    worker.save_data([{"id": "1", "title": "New Job"}])

    with open("data/test_vacancies.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == 1
    assert data[0]["title"] == "New Job"


def test_json_save_data_no_duplicates():
    """Проверка отсутствия дубликатов при сохранении в JSON."""
    worker = JSONFileWorker("data/test_vacancies.json")
    worker.save_data([{"id": "1", "title": "Job 1"}])
    worker.save_data([{"id": "1", "title": "Duplicate"}])

    data = worker.load_data()
    assert len(data) == 1
    assert data[0]["title"] == "Job 1"


def test_json_remove_data():
    """Проверка удаления данных из JSON‑файла по условию."""
    worker = JSONFileWorker("data/test_vacancies.json")
    worker.save_data(
        [
            {"id": "1", "title": "Keep"},
            {"id": "2", "title": "Remove"},
        ]
    )
    worker.remove_data(lambda x: x["id"] == "2")
    data = worker.load_data()
    assert len(data) == 1
    assert data[0]["title"] == "Keep"


def test_json_clear_file():
    """Проверка очистки JSON‑файла."""
    worker = JSONFileWorker("data/test_vacancies.json")
    worker.save_data([{"id": "1", "title": "Test"}])
    worker.clear_file()
    data = worker.load_data()
    assert data == []


def test_json_remove_duplicates_private_method():
    """Проверка метода удаления дубликатов в JSON."""
    worker = JSONFileWorker("dummy.json")
    existing = [{"id": "1", "title": "Existing"}]
    new = [{"id": "1", "title": "New"}, {"id": "2", "title": "Unique"}]
    result = worker._JSONFileWorker__remove_duplicates(existing, new)
    assert len(result) == 2
    assert result[0]["id"] == "1"
    assert result[1]["id"] == "2"


def test_csv_load_data_file_not_exists():
    """Проверка загрузки из несуществующего CSV‑файла."""
    worker = CSVFileWorker("data/nonexistent.csv")
    data = worker.load_data()
    assert data == []


def test_csv_save_data_new_file():
    """Проверка сохранения данных в новый CSV‑файл."""
    worker = CSVFileWorker("data/test_vacancies.csv")
    worker.save_data([{"id": "1", "title": "CSV Job", "salary": "100000"}])

    with open("data/test_vacancies.csv", "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        data = list(reader)
    assert len(data) == 1
    assert data[0]["title"] == "CSV Job"
    assert data[0]["salary"] == "100000"


def test_csv_remove_data():
    """Проверка удаления данных из CSV‑файла по условию."""
    worker = CSVFileWorker("data/test_vacancies.csv")
    worker.save_data(
        [
            {"id": "1", "title": "Keep"},
            {"id": "2", "title": "Remove"},
        ]
    )
    worker.remove_data(lambda x: x["id"] == "2")
    data = worker.load_data()
    assert len(data) == 1
    assert data[0]["title"] == "Keep"


def test_csv_clear_file_with_data():
    """Проверка очистки CSV‑файла с данными."""
    worker = CSVFileWorker("data/test_vacancies.csv")
    worker.save_data([{"id": "1", "title": "Test"}])
    worker.clear_file()
    data = worker.load_data()
    assert data == []


def test_csv_clear_file_empty():
    """Проверка очистки пустого CSV‑файла."""
    worker = CSVFileWorker("data/test_vacancies.csv")
    worker.clear_file()
    assert os.path.exists("data/test_vacancies.csv")


@patch("builtins.open", side_effect=IOError("Disk error"))
def test_json_save_data_io_error(mock_open, capsys):
    """Проверка ошибки записи в JSON‑файл."""
    worker = JSONFileWorker("data/test.json")
    worker.save_data([{"id": "1"}])
    captured = capsys.readouterr()
    assert "Ошибка записи в файл data/test.json: Disk error" in captured.out


@patch("builtins.open", side_effect=IOError("Disk error"))
def test_json_clear_file_io_error(mock_open, capsys):
    """Проверка ошибки при очистке JSON‑файла."""
    worker = JSONFileWorker("data/test.json")
    worker.clear_file()
    captured = capsys.readouterr()
    assert "Ошибка при очистке файла data/test.json: Disk error" in captured.out


@patch("builtins.open", side_effect=IOError("Disk error"))
def test_csv_save_data_io_error(mock_open, capsys):
    """Проверка ошибки записи в CSV‑файл."""
    worker = CSVFileWorker("data/test.csv")
    worker.save_data([{"id": "1"}])
    captured = capsys.readouterr()
    assert "Ошибка записи в файл data/test.csv: Disk error" in captured.out


@patch("builtins.open", side_effect=IOError("Disk error"))
def test_csv_clear_file_io_error(mock_open, capsys):
    """Проверка ошибки при очистке CSV‑файла."""
    worker = CSVFileWorker("data/test.csv")
    worker.clear_file()
    captured = capsys.readouterr()
    assert "Ошибка при очистке файла data/test.csv: Disk error" in captured.out
