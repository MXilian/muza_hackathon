from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import os

from src.utils.logger import log


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
            return engine
        except Exception as e:
            log(f"Ошибка подключения к базе данных: {e}")
            raise


    def close_connection(self):
        """Закрывает соединение с базой данных."""
        if self.engine:
            self.engine.dispose()


    # Выполнение SQL-запроса
    def execute_query(self, query, params: dict = None):
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
                return result  # Возвращаем результат выполнения запроса
            except SQLAlchemyError as e:
                transaction.rollback()  # Откат транзакции при ошибке
                log(f"Ошибка при выполнении запроса: {e}")
                raise
            finally:
                connection.close()


    def insert_data(self, query: str, params: dict):
        """
        Выполняет вставку данных в базу.

        :param query: SQL-запрос с плейсхолдерами.
        :param params: Кортеж значений для подстановки.
        """
        with self.engine.connect() as connection:
            transaction = connection.begin()
            try:
                connection.execute(text(query), params)
                transaction.commit()
            except SQLAlchemyError as e:
                transaction.rollback()
                log(f"Ошибка при вставке данных: {e}")
                raise
            finally:
                connection.close()


    def read_query(self, query, params: dict = None):
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
                return df
        except SQLAlchemyError as e:
            log(f"Ошибка при чтении данных: {e}")
            raise

