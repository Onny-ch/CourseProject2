# main.py
import os

from src.fileworker import JSONFileWorker, CSVFileWorker
from src.hh_api import HeadHunterAPI
from src.vacancy import Vacancy



def main():
    print("Добро пожаловать в систему поиска вакансий с HeadHunter!\n")

    # Выбор формата файла для сохранения
    while True:
        print("Выберите формат для сохранения данных:")
        print("1 — JSON")
        print("2 — CSV")
        choice = input("Введите номер (1 или 2): ").strip()
        if choice == "1":
            file_worker = JSONFileWorker("data/vacancies.json")
            print("Формат: JSON\n")
            break
        elif choice == "2":
            file_worker = CSVFileWorker("data/vacancies.csv")
            print("Формат: CSV\n")
            break
        else:
            print("Некорректный ввод. Пожалуйста, выберите 1 или 2.\n")

    # Создание парсера
    parser = HeadHunterAPI(file_worker)

    while True:
        print("Доступные действия:")
        print("1 — Загрузить вакансии по ключевому слову")
        print("2 — Просмотреть сохранённые вакансии")
        print("3 — Очистить файл с вакансиями")
        print("4 — Выйти из программы")
        action = input("\nВведите номер действия (1–4): ").strip()

        if action == "1":
            keyword = input("Введите ключевое слово для поиска вакансий: ").strip()
            if not keyword:
                print("Ключевое слово не может быть пустым!\n")
                continue

            print(f"\nЗагружаем вакансии по запросу «{keyword}»...")
            parser.load_vacancies(keyword)
            count = len(parser.get_vacancies())
            print(f"Найдено {count} вакансий.\n")

            if count > 0:
                save = input("Сохранить найденные вакансии в файл? (да/нет): ").strip().lower()
                if save in ("да", "yes", "y"):
                    parser.save_vacancies(file_worker.filename)
                    print(f"Вакансии сохранены в {file_worker.filename}\n")
                else:
                    print("Вакансии не сохранены.\n")

        elif action == "2":
            data = file_worker.load_data()
            if not data:
                print("В файле нет сохранённых вакансий.\n")
            else:
                print(f"\nСохранённые вакансии ({len(data)} шт.):")
                valid_count = 0
                for i, item in enumerate(data, 1):
                    try:
                        if not isinstance(item, dict):
                            print(f"{i}. ОШИБКА: НЕ словарь (тип: {type(item).__name__})")
                            print(f"   Значение: {repr(item)}")
                            continue

                        if 'id' not in item:
                            print(f"{i}. ОШИБКА: нет поля 'id'")
                            continue
                        if 'title' not in item:
                            print(f"{i}. ОШИБКА: нет поля 'title'")
                            continue

                        vacancy = Vacancy(item)
                        print(f"{i}. {vacancy}")
                        valid_count += 1

                    except (ValueError, KeyError, TypeError, AttributeError) as e:
                        print(f"{i}. ОШИБКА при обработке: {type(e).__name__}: {e}")
                print(f"\nУспешно отображено: {valid_count} из {len(data)} записей\n")

        elif action == "3":
            if os.path.exists(file_worker.filename):
                size = os.path.getsize(file_worker.filename)
                print(f"Текущий размер файла: {size} байт ({len(file_worker.load_data())} записей)")

            confirm = input("Вы уверены, что хотите очистить файл? (да/нет): ").strip().lower()
            if confirm in ("да", "yes", "y"):
                file_worker.clear_file()
                parser.clear_vacancies()
                after_clear = file_worker.load_data()
                print(f"После очистки: {len(after_clear)} записей")
            else:
                print("Очищение отменено.\n")

        elif action == "4":
            print("До свидания!")
            break

        else:
            print("Некорректный ввод. Пожалуйста, выберите действие от 1 до 4.\n")



if __name__ == "__main__":
    main()


