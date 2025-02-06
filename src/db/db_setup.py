import os
import pandas as pd
import csv

from src.db.db_helper import DbHelper


def init_db():
    """Инициализация базы данных"""
    db_helper = DbHelper()
    try:
        # Получаем список существующих схем
        schemes_df = db_helper.read_query('''
            SELECT distinct table_schema
            FROM information_schema.tables 
            ORDER BY table_schema
        ''')
        print(schemes_df)

        # Создаем схему museum если её нет
        if 'museum' not in schemes_df['table_schema'].values:
            db_helper.execute_query('CREATE SCHEMA museum')

        # Создаем необходимые последовательности
        db_helper.execute_query('''
            CREATE SEQUENCE IF NOT EXISTS museum.seq_recommendation
            INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
            
            CREATE SEQUENCE IF NOT EXISTS museum.seq_user
            INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
            
            CREATE SEQUENCE IF NOT EXISTS museum.seq_interest
            INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
        ''')

        # Создаем таблицы если их нет
        db_helper.execute_query('''
            CREATE TABLE IF NOT EXISTS museum.interest (
                interest_id bigint default nextval('museum.seq_interest'),
                interest_name text,
                PRIMARY KEY (interest_id)
            );
            
            CREATE TABLE IF NOT EXISTS museum."user" (
                tg_id bigint default nextval('museum.seq_user'),
                login text,
                email text,
                PRIMARY KEY (tg_id)
            );
            
            CREATE TABLE IF NOT EXISTS museum.user_detail (
                tg_id bigint REFERENCES museum."user"(tg_id),
                first_name text,
                last_name text,
                patronymic text,
                bd_date date,
                phone_number int,
                PRIMARY KEY (tg_id)
            );
            
            CREATE TABLE IF NOT EXISTS museum.recommendation (
                recommendation_id bigint default nextval('museum.seq_recommendation'),
                tg_id bigint REFERENCES museum."user"(tg_id),
                interest_id bigint REFERENCES museum.interest(interest_id),
                PRIMARY KEY (recommendation_id)
            );
        ''')
    finally:
        db_helper.close_connection()

def drop_all_tables():
    """Удаление всех таблиц и последовательностей"""
    db_helper = DbHelper()
    try:
        db_helper.execute_query('''
            DROP TABLE IF EXISTS museum.recommendation;
            DROP TABLE IF EXISTS museum.user_detail;
            DROP TABLE IF EXISTS museum."user";
            DROP TABLE IF EXISTS museum.interest;
            DROP SEQUENCE IF EXISTS museum.seq_interest;
            DROP SEQUENCE IF EXISTS museum.seq_user;
            DROP SEQUENCE IF EXISTS museum.seq_recommendation;
        ''')
    finally:
        db_helper.close_connection()

def clear_all_tables():
    """Очистка всех таблиц"""
    db_helper = DbHelper()
    try:
        db_helper.execute_query('''
            TRUNCATE TABLE museum.recommendation;
            TRUNCATE TABLE museum.user_detail;
            TRUNCATE TABLE museum."user";
            TRUNCATE TABLE museum.interest;
        ''')
    finally:
        db_helper.close_connection()

def load_interests():
    """Загрузка интересов из всех CSV файлов в директории /assets/interests/"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.abspath(os.path.join(current_dir, '..', '..'))
    interests_dir = os.path.join(root_dir, 'assets', 'interests')

    # Проверяем существование директории
    if not os.path.exists(interests_dir):
        raise FileNotFoundError(f"Директория не найдена: {interests_dir}")

    # Собираем данные из всех CSV файлов в директории
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
        interests_data = pd.DataFrame(all_interests, columns=['interest_name'])
    else:
        raise ValueError("Не найдены интересы в CSV-файлах")

    # Сохраняем данные в базу данных
    db_helper = DbHelper()
    try:
        columns = ",".join(list(interests_data.columns))
        values = "VALUES({})".format(",".join(["%s" for _ in interests_data.columns]))
        insert_stmt = f"INSERT INTO museum.interest ({columns}) {values}"
        cursor = db_helper.connection.cursor()
        cursor.executemany(insert_stmt, interests_data.values.tolist())
        db_helper.connection.commit()
        cursor.close()
        print("Интересы успешно добавлены в базу данных!")
    except Exception as e:
        print(f"Возникла ошибка при добавлении интересов в базу данных: {e}")
        db_helper.connection.rollback()
    finally:
        db_helper.close_connection()


# Полный сброс состояния базы данных (удаление старой и создание новой)
def reinit_db():
    print("Запускаем развертывание чистой базы данных...")

    try:
        # 1. Удаление существующей базы данных
        print("Удаляем существующую БД...")
        drop_all_tables()

        # 2. Создание новой базы данных
        print("Инициализируем новую БД...")
        init_db()

        # 3. Загрузка интересов из CSV-файла
        load_interests()

        print("Инициализация базы данных успешно завершена!")

    except Exception as e:
        print(f"Ошибка в ходе инициализации базы данных: {e}")
