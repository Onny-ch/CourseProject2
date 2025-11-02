import os
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.fileworker import JSONFileWorker
from src.hh_api import HeadHunterAPI
from src.vacancy import Vacancy


@pytest.fixture(autouse=True)
def cleanup_test_files():
    """Удаляет тестовые файлы после выполнения тестов."""
    test_files = ["data/hh_test.json"]
    for f in test_files:
        if os.path.exists(f):
            os.remove(f)


@pytest.fixture
def hh_parser():
    """Создаёт экземпляр HeadHunterAPI с тестовым JSONFileWorker."""
    file_worker = JSONFileWorker("data/hh_test.json")
    return HeadHunterAPI(file_worker)


@patch("requests.get")
def test_load_vacancies_success(mock_get, hh_parser):
    """Проверяет загрузку вакансий при успешном ответе API."""
    mock_responses = [
        MagicMock(
            status_code=200,
            json=lambda: {
                "items": [
                    {"id": "1", "name": "Dev", "salary": {"from": 100000}},
                    {"id": "2", "name": "QA", "salary": {"from": 80000}},
                ]
            },
        ),
        MagicMock(status_code=200, json=lambda: {"items": []}),
    ]
    mock_get.side_effect = mock_responses

    hh_parser.load_vacancies("python")

    vacancies = hh_parser.get_vacancies()
    assert len(vacancies) == 2
    assert vacancies[0].title == "Dev"
    assert vacancies[1].salary_from == 80000


@patch("requests.get")
def test_load_vacancies_empty(mock_get, hh_parser):
    """Проверяет обработку пустого ответа API (нет вакансий)."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"items": []}
    mock_get.return_value = mock_response

    hh_parser.load_vacancies("python")
    assert len(hh_parser.get_vacancies()) == 0


@patch("requests.get", side_effect=requests.RequestException("Network error"))
def test_load_vacancies_network_error(mock_get, hh_parser, capsys):
    """Проверяет обработку сетевой ошибки при загрузке вакансий."""
    hh_parser.load_vacancies("python")
    captured = capsys.readouterr()
    assert "Ошибка при загрузке вакансий" in captured.out
    assert len(hh_parser.get_vacancies()) == 0


@patch("requests.get")
def test_load_vacancies_http_error(mock_get, hh_parser, capsys):
    """Проверяет обработку HTTP‑ошибки (например, 404)."""
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    hh_parser.load_vacancies("python")
    captured = capsys.readouterr()
    assert "Не удалось подключиться к API" in captured.out
    assert len(hh_parser.get_vacancies()) == 0


def test_get_vacancies(hh_parser):
    """Проверяет получение списка загруженных вакансий."""
    hh_parser._HeadHunterAPI__vacancies = [
        Vacancy({"id": "1", "name": "Test", "salary": {"from": 50000}})
    ]
    vacancies = hh_parser.get_vacancies()
    assert len(vacancies) == 1
    assert vacancies[0].title == "Test"


def test_save_vacancies_empty(hh_parser, capsys):
    """Проверяет сохранение, когда вакансий для сохранения нет."""
    hh_parser.clear_vacancies()
    hh_parser.save_vacancies("data/hh_test.json")
    captured = capsys.readouterr()
    assert "Нет вакансий для сохранения" in captured.out


def test_clear_vacancies(hh_parser):
    """Проверяет очистку списка загруженных вакансий."""
    hh_parser._HeadHunterAPI__vacancies = [Vacancy({"id": "1", "name": "Test"})]
    hh_parser.clear_vacancies()
    assert len(hh_parser.get_vacancies()) == 0


@patch("requests.get")
def test_connect_to_api_success(mock_get):
    """Проверяет успешное подключение к API."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    parser = HeadHunterAPI(JSONFileWorker("dummy.json"))
    response = parser._HeadHunterAPI__connect_to_api()
    assert response.status_code == 200


@patch("requests.get", side_effect=[MagicMock(status_code=500)] * 3)
def test_connect_to_api_retries_fail(mock_get):
    """Проверяет отказ после трёх попыток подключения к API."""
    parser = HeadHunterAPI(JSONFileWorker("dummy.json"))
    with pytest.raises(requests.HTTPError):
        parser._HeadHunterAPI__connect_to_api()


def test_save_vacancies_file_content(hh_parser):
    """Проверяет содержимое файла после сохранения вакансий."""
    hh_parser._HeadHunterAPI__vacancies = [
        Vacancy(
            {
                "id": "1",
                "name": "Python Dev",
                "salary": {"from": 150000, "to": 200000, "currency": "RUB"},
                "address": {"city": "Москва"},
            }
        )
    ]

    hh_parser.save_vacancies("data/hh_test.json")
    loaded = hh_parser._HeadHunterAPI__file_worker.load_data()

    assert len(loaded) == 1
    assert loaded[0]["title"] == "Python Dev"
    assert loaded[0]["salary_from"] == 150000.0
    assert loaded[0]["city"] == "Москва"
