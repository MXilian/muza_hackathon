import logging

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

logger = logging.getLogger(__name__)

# Класс для работы с базой данных
class DbHelper:
    def __init__(self):
        self.engine = self._connect_to_db()


    # Подключение к базе данных
    def _connect_to_db(self): # noqa
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise EnvironmentError("Переменная окружения DATABASE_URL не установлена.")
        try:
            engine = create_engine(database_url)
            logger.info("Успешное подключение к базе данных через SQLAlchemy.")
            return engine
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise


    def close_connection(self):
        """Закрывает соединение с базой данных."""
        if self.engine:
            self.engine.dispose()
            logger.info("Соединение с базой данных закрыто.")


    # Выполнение SQL-запроса
    def execute_query(self, query, params=None):
        """
        Выполняет произвольный SQL-запрос.

        :param query: SQL-запрос (строка).
        :param params: Параметры для запроса (словарь или кортеж).
        """
        with self.engine.connect() as connection:
            transaction = connection.begin()  # Начало транзакции
            try:
                if params:
                    result = connection.execute(text(query), params)
                else:
                    result = connection.execute(text(query))
                transaction.commit()  # Фиксация изменений
                logger.info(f"Запрос выполнен успешно: {query}")
                return result  # Возвращаем результат выполнения запроса
            except SQLAlchemyError as e:
                transaction.rollback()  # Откат транзакции при ошибке
                logger.error(f"Ошибка при выполнении запроса: {e}")
                raise
            finally:
                connection.close()


    def insert_data(self, table_name, data):
        """
        Вставляет данные в таблицу.

        :param table_name: Имя таблицы (строка).
        :param data: Данные для вставки (словарь или список словарей).
        """
        if isinstance(data, dict):  # Если передан один словарь
            data = [data]

        # Генерируем SQL-запрос для вставки
        columns = ", ".join(data[0].keys())
        placeholders = ", ".join([f":{key}" for key in data[0].keys()])
        query = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"

        with self.engine.connect() as connection:
            transaction = connection.begin()  # Начало транзакции
            try:
                for row in data:
                    connection.execute(text(query), row)
                transaction.commit()  # Фиксация изменений
                logger.info(f"Данные успешно вставлены в таблицу {table_name}.")
            except SQLAlchemyError as e:
                transaction.rollback()  # Откат транзакции при ошибке
                logger.error(f"Ошибка при вставке данных: {e}")
                raise
            finally:
                connection.close()


    def read_query(self, query, params=None):
        """
        Читает данные из базы данных и возвращает их как DataFrame.

        :param query: SQL-запрос (строка).
        :param params: Параметры для запроса (словарь или кортеж).
        :return: DataFrame с результатами запроса.
        """
        import pandas as pd
        try:
            with self.engine.connect() as connection:
                if params:
                    df = pd.read_sql_query(text(query), connection, params=params)
                else:
                    df = pd.read_sql_query(text(query), connection)
                logger.info(f"Данные прочитаны успешно: {query}")
                return df
        except SQLAlchemyError as e:
            logger.error(f"Ошибка при чтении данных: {e}")
            raise

