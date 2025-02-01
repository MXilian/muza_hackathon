import os
import psycopg2
from psycopg2 import sql

# Подключение к базе данных, используем переменную окружения DATABASE_URL
def connect_to_db():
    # Получаем адрес БД из переменной окружения
    database_url = os.getenv("DATABASE_URL")
    connection = psycopg2.connect(database_url)
    return connection

# Проверка: имеется ли таблица 'tg_users', если нет - создать её
def setup_database():
    try:
        # Создаем соединение с базой данных
        conn = connect_to_db()
        cursor = conn.cursor()

        # Проверяем, существует ли таблица 'tg_users'
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tg_users (
                id SERIAL PRIMARY KEY,
                user_id BIGINT UNIQUE NOT NULL,
                username VARCHAR(255),
                created_at TIMESTAMPTZ DEFAULT NOW()
            )
        """)

        # Сохраняем изменения (создание таблицы)
        conn.commit()
        cursor.close()
        conn.close()

        print("База данных и таблица tg_users успешно проверены/созданы.")
    except Exception as e:
        print(f"Ошибка при настройке базы данных: {e}")