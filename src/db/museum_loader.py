import os

import pandas as pd
from sqlalchemy import text

from src.db.db_helper import DbHelper
from src.utils.logger import log


class MuseumLoader:
    def __init__(self):
        self.db_helper = DbHelper()
        self.museums_df = None
        self.interests_dict = None

    @staticmethod
    def _clear_str(str_):
        """Очистка строки от HTML-тегов и лишних пробелов."""
        res_str = str_.replace('<p>', '')
        res_str = res_str.lstrip()
        res_str = res_str.lstrip('<span>')
        return res_str

    def _load_data_from_csv(self):
        """Загрузка данных из CSV-файла museums.csv в директории assets."""

        # Определяем путь к файлу museums.csv
        current_dir = os.path.dirname(os.path.abspath(__file__))
        root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
        assets_dir = os.path.join(root_dir, 'assets')
        csv_path = os.path.join(assets_dir, 'museums.csv')

        # Проверяем существование файла
        if not os.path.exists(csv_path):
            raise FileNotFoundError(f"Файл museums.csv не найден в директории {assets_dir}")

        """Загрузка данных из CSV."""
        self.museums_df = pd.read_csv(
            csv_path,
            sep=',',
            usecols=["Название", "Описание", "Местоположение", "Улица"]
        )
        log("Данные из CSV успешно загружены.")

    def _clean_data(self):
        """Очистка и предобработка данных."""
        if self.museums_df is None:
            raise ValueError("Данные не загружены. Сначала нужно вызвать _load_data_from_csv.")

        # Удаляем строки с пустыми значениями в ключевых колонках
        self.museums_df = self.museums_df.dropna(subset=["Название", "Описание", "Местоположение", "Улица"])

        # Переименовываем колонки
        self.museums_df = self.museums_df.rename(columns={
            "Название": "name",
            "Описание": "description",
            "Местоположение": "city",
            "Улица": "street"
        })

        # Очищаем строки от HTML-тегов и лишних пробелов
        self.museums_df["name"] = self.museums_df["name"].apply(self._clear_str)
        self.museums_df["description"] = self.museums_df["description"].apply(self._clear_str)
        self.museums_df["city"] = self.museums_df["city"].apply(self._clear_str)
        self.museums_df["street"] = self.museums_df["street"].apply(self._clear_str)

        # Формируем колонку address
        self.museums_df["address"] = self.museums_df["city"] + ", " + self.museums_df["street"]

        # Удаляем ненужную колонку
        self.museums_df = self.museums_df.drop(columns=["street"])

        # Создаем пустую колонку relative_interests (без заполнения значений)
        self.museums_df["relative_interests"] = None

        log("Данные успешно очищены и подготовлены.")

    def _save_data_to_db(self):
        """Сохранение данных в базу данных."""
        if self.museums_df is None:
            raise ValueError("Данные не загружены. Сначала нужно вызвать _load_data_from_csv.")

        try:
            # Подготовка данных для вставки
            data_to_insert = self.museums_df.to_dict(orient='records')

            # Генерация SQL-запроса для вставки
            columns = ", ".join(data_to_insert[0].keys())
            placeholders = ", ".join([f":{key}" for key in data_to_insert[0].keys()])
            query = f"INSERT INTO museum.museum ({columns}) VALUES ({placeholders})"

            # Выполнение запросов через SQLAlchemy
            with self.db_helper.engine.connect() as connection:
                transaction = connection.begin()  # Начало транзакции
                try:
                    for record in data_to_insert:
                        connection.execute(text(query), record)
                    transaction.commit()  # Фиксация изменений
                    log("Данные успешно сохранены в базу данных.")
                except Exception as e:
                    transaction.rollback()  # Откат транзакции при ошибке
                    log(f"Ошибка при сохранении музеев в БД: {e}")
                    raise
        except Exception as e:
            log(f"Ошибка при обработке данных: {e}")
            raise

    def load_museums(self):
        """Основной метод для загрузки музеев из CSV и сохранения в БД."""
        try:
            self._load_data_from_csv()
            self._clean_data()
            self._save_data_to_db()
            log("Музеи успешно загружены и сохранены в базу данных.")
        except Exception as e:
            log(f"Ошибка при загрузке музеев: {e}")
            if self.db_helper.engine:
                with self.db_helper.engine.connect() as connection:
                    transaction = connection.begin()
                    transaction.rollback()
        finally:
            self.db_helper.close_connection()
