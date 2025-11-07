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
                # Преобразуем данные в список Vacancy объектов
                vacancies = []
                for item in data:
                    try:
                        if not isinstance(item, dict):
                            continue
                        # Проверяем наличие id и хотя бы одного из полей title или name
                        if 'id' not in item or (not item.get('title') and not item.get('name')):
                            continue
                        vacancy = Vacancy(item)
                        vacancies.append(vacancy)
                    except (ValueError, KeyError, TypeError, AttributeError):
                        continue

                if not vacancies:
                    print("Не удалось загрузить вакансии из файла.\n")
                    continue

                # Подменю для просмотра вакансий
                print("\nВыберите способ просмотра вакансий:")
                print("1 — Показать все вакансии")
                print("2 — Показать топ N вакансий по зарплате")
                print("3 — Поиск по ключевому слову в описании")
                view_choice = input("Введите номер (1–3): ").strip()

                if view_choice == "1":
                    # Показать все вакансии
                    print(f"\nСохранённые вакансии ({len(vacancies)} шт.):")
                    for i, vacancy in enumerate(vacancies, 1):
                        # Отображаем профессиональную роль вместо названия
                        professional_role = ", ".join(
                            vacancy.professional_roles) if vacancy.professional_roles else "Не указано"
                        salary_part = vacancy.salary_info
                        city_part = vacancy.city if vacancy.city != "Не указан" else ""
                        parts = [professional_role, salary_part, city_part]
                        print(f"{i}. {' | '.join(filter(None, parts))}")
                    print()

                elif view_choice == "2":
                    # Показать топ N вакансий по зарплате
                    while True:
                        try:
                            n_input = input("Введите количество вакансий для отображения (N): ").strip()
                            n = int(n_input)
                            if n <= 0:
                                print("Количество должно быть положительным числом.\n")
                                continue
                            break
                        except ValueError:
                            print("Некорректный ввод. Пожалуйста, введите целое число.\n")

                    # Сортируем по средней зарплате (по убыванию)
                    sorted_vacancies = sorted(vacancies, key=lambda v: v.average_salary(), reverse=True)
                    top_n = sorted_vacancies[:n]

                    print(f"\nТоп {len(top_n)} вакансий по зарплате:")
                    for i, vacancy in enumerate(top_n, 1):
                        avg_salary = int(vacancy.average_salary())
                        salary_str = f"{avg_salary:,} {vacancy.currency}" if avg_salary > 0 else "Зарплата не указана"
                        # Отображаем профессиональную роль вместо названия
                        professional_role = ", ".join(
                            vacancy.professional_roles) if vacancy.professional_roles else "Не указано"
                        print(
                            f"{i}. {professional_role} | {salary_str} | {vacancy.city if vacancy.city != 'Не указан' else ''}")
                    print()

                elif view_choice == "3":
                    # Поиск по ключевому слову в описании
                    keyword = input("Введите ключевое слово для поиска в описании: ").strip().lower()
                    if not keyword:
                        print("Ключевое слово не может быть пустым.\n")
                        continue

                    # Ищем вакансии, содержащие ключевое слово в responsibilities или requirements
                    matching_vacancies = []
                    for vacancy in vacancies:
                        description = (vacancy.responsibilities + " " + vacancy.requirements).lower()
                        if keyword in description:
                            matching_vacancies.append(vacancy)

                    if matching_vacancies:
                        print(f"\nНайдено вакансий с ключевым словом «{keyword}»: {len(matching_vacancies)}")
                        for i, vacancy in enumerate(matching_vacancies, 1):
                            # Отображаем профессиональную роль вместо названия
                            professional_role = ", ".join(
                                vacancy.professional_roles) if vacancy.professional_roles else "Не указано"
                            salary_part = vacancy.salary_info
                            city_part = vacancy.city if vacancy.city != "Не указан" else ""
                            parts = [professional_role, salary_part, city_part]
                            print(f"{i}. {' | '.join(filter(None, parts))}")
                        print()
                    else:
                        print(f"\nВакансии с ключевым словом «{keyword}» не найдены.\n")

                else:
                    print("Некорректный ввод. Пожалуйста, выберите действие от 1 до 3.\n")

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
