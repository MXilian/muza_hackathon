import os
import csv
import pandas as pd
from sqlalchemy import text

from src.db.db_helper import DbHelper

class InterestsLoader:
    def __init__(self):
        self.db_helper = DbHelper()
        self.interests_data = None


    def _load_interests_from_csv(self):
        """Загружает интересы из всех CSV-файлов в директории."""
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
        interests_dir = os.path.join(root_dir, 'assets', 'interests')

        if not os.path.exists(interests_dir):
            raise FileNotFoundError(f"Директория не найдена: {interests_dir}")

        all_interests = []

        for filename in os.listdir(interests_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(interests_dir, filename)

                # Читаем CSV файл
                with open(file_path, mode='r', encoding='utf-8') as file:
                    reader = csv.reader(file)
                    rows = list(reader)  # Считываем все строки

                    # Игнорируем первую строку (название колонки) и вторую строку (название категории)
                    interests = [row[0] for row in rows[2:]]  # Берем только значения из оставшихся строк
                    all_interests.extend(interests)

        # Преобразуем список интересов в DataFrame
        if all_interests:
            self.interests_data = pd.DataFrame(all_interests, columns=['interest_name'])
        else:
            raise ValueError("Не найдены интересы в CSV-файлах")


    def _save_interests_to_db(self):
        """Сохраняет интересы в базу данных."""
        if self.interests_data is None:
            raise ValueError("Данные не загружены. Сначала вызовите _load_interests_from_csv.")

        try:
            # Преобразуем DataFrame в список словарей для вставки
            data_to_insert = self.interests_data.to_dict(orient='records')

            # Генерируем SQL-запрос для вставки
            columns = ", ".join(data_to_insert[0].keys())
            placeholders = ", ".join([f":{key}" for key in data_to_insert[0].keys()])
            query = f"INSERT INTO museum.interest ({columns}) VALUES ({placeholders})"

            # Выполняем запрос через DbHelper
            with self.db_helper.engine.connect() as connection:
                transaction = connection.begin()  # Начало транзакции
                try:
                    for record in data_to_insert:
                        connection.execute(text(query), record)
                    transaction.commit()  # Фиксация изменений
                    print("Интересы успешно добавлены в базу данных!")
                except Exception as e:
                    transaction.rollback()  # Откат транзакции при ошибке
                    print(f"Возникла ошибка при добавлении интересов в базу данных: {e}")
                    raise
        except Exception as e:
            print(f"Ошибка при сохранении интересов в базу данных: {e}")


    def load_interests(self):
        """Основной метод для загрузки интересов из CSV и сохранения в БД."""
        try:
            self._load_interests_from_csv()
            self._save_interests_to_db()
        except Exception as e:
            print(f"Ошибка при загрузке интересов: {e}")
        finally:
            self.db_helper.close_connection()