from src.db.db_helper import DbHelper
from src.db.interests_loader import InterestsLoader
from src.db.museum_loader import MuseumLoader

# Функция для инициализации базы данных
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

        # Создаем схему museum, если её нет
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
            
            CREATE SEQUENCE IF NOT EXISTS museum.seq_museum
            INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
        ''')

        # Создаем таблицы, если их нет
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

            CREATE TABLE IF NOT EXISTS museum.user_interest (
                tg_id bigint REFERENCES museum."user"(tg_id),
                interest_id bigint REFERENCES museum.interest(interest_id),
                PRIMARY KEY (tg_id, interest_id)
            );
            
            CREATE TABLE IF NOT EXISTS museum.museum (
                museum_id bigint default nextval('museum.seq_museum'),
                name text,
                description text,
                city text,
                address text,
                PRIMARY KEY (museum_id)
            );
            
            CREATE TABLE IF NOT EXISTS museum.museum_interest (
                museum_id bigint REFERENCES museum.museum(museum_id),
                interest_id bigint REFERENCES museum.interest(interest_id),
                PRIMARY KEY (museum_id, interest_id)
            );
        ''')

        # Проверяем, пуста ли таблица museum.interest
        interests_count = db_helper.read_query('SELECT COUNT(*) FROM museum.interest').iloc[0, 0]
        if interests_count == 0:
            print("Таблица museum.interest пуста. Загружаем интересы...")
            InterestsLoader().load_interests()
        else:
            print("Таблица museum.interest уже содержит данные. Пропускаем загрузку интересов.")

        # Проверяем, пуста ли таблица museum.museum
        museums_count = db_helper.read_query('SELECT COUNT(*) FROM museum.museum').iloc[0, 0]
        if museums_count == 0:
            print("Таблица museum.museum пуста. Загружаем музеи...")
            MuseumLoader().load_museums()
        else:
            print("Таблица museum.museum уже содержит данные. Пропускаем загрузку музеев.")
    finally:
        db_helper.close_connection()


# Функция для удаления БД
def drop_all_tables():
    """Удаление всех таблиц и последовательностей"""
    db_helper = DbHelper()
    try:
        db_helper.execute_query('''
            DROP TABLE IF EXISTS museum.recommendation CASCADE;
            DROP TABLE IF EXISTS museum.user_interest CASCADE;
            DROP TABLE IF EXISTS museum.museum_interest CASCADE;
            DROP TABLE IF EXISTS museum.museum CASCADE;
            DROP TABLE IF EXISTS museum.interest CASCADE;
            DROP TABLE IF EXISTS museum."user" CASCADE;
            DROP SEQUENCE IF EXISTS museum.seq_interest;
            DROP SEQUENCE IF EXISTS museum.seq_user;
            DROP SEQUENCE IF EXISTS museum.seq_recommendation;
            DROP SEQUENCE IF EXISTS museum.seq_museum;
        ''')
    finally:
        db_helper.close_connection()


# Функция для очистки всех данных без удаления БД
def clear_all_tables():
    """Очистка всех таблиц"""
    db_helper = DbHelper()
    try:
        db_helper.execute_query('''
            TRUNCATE TABLE museum.user_interest;
            TRUNCATE TABLE museum.museum_interest;
            TRUNCATE TABLE museum.museum;
            TRUNCATE TABLE museum.interest;
            TRUNCATE TABLE museum."user";
        ''')
    finally:
        db_helper.close_connection()


# Полный сброс состояния базы данных (удаление старой и создание новой)
def reinit_db():
    print("Запускаем развертывание чистой базы данных...")
    try:
        print("Удаляем существующую БД...")
        drop_all_tables()
        print("Инициализируем новую БД...")
        init_db()
        print("Инициализация базы данных успешно завершена!")
    except Exception as e:
        print(f"Ошибка в ходе инициализации базы данных: {e}")