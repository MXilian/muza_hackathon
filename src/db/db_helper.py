import logging

import pandas as pd
import psycopg2 as bd
from urllib.parse import urlparse
import numpy as np
from psycopg2.extensions import register_adapter, AsIs
register_adapter(np.int64, AsIs)
import os

logger = logging.getLogger(__name__)

# Класс для работы с базой данных
class DbHelper:
    def __init__(self):
        self.connection = self._connect_to_db()

    # Подключение к базе данных
    def _connect_to_db(self): # noqa
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise EnvironmentError("Переменная окружения DATABASE_URL не установлена.")
        result = urlparse(database_url)
        try:
            connection = bd.connect(
                database=result.path[1:],
                user=result.username,
                password=result.password,
                host=result.hostname,
                port=result.port
            )
            logger.info("Успешное подключение к базе данных.")
            return connection
        except Exception as e:
            logger.error(f"Ошибка подключения к базе данных: {e}")
            raise

    # Закрытие соединения с базой данных
    def close_connection(self):
        if self.connection:
            self.connection.close()

    # Выполнение SQL-запроса
    def execute_query(self, query, params=None):
        cursor = None
        try:
            cursor = self.connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            self.connection.commit()
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()

    # Чтение данных из базы данных
    def read_query(self, query, params=None):
        cursor = None
        try:
            cursor = self.connection.cursor()
            df = pd.read_sql_query(query, self.connection, params=params)
            logger.info(f"Данные прочитаны успешно: {query}")
            return df
        except Exception as e:
            logger.error(f"Ошибка при чтении данных: {e}")
            raise
        finally:
            if cursor:
                cursor.close()

    # Вставка данных в таблицу
    def insert_data(self, query, record_to_insert):
        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(query, record_to_insert)
            self.connection.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"Ошибка при выполнении запроса: {e}")
            self.connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()

