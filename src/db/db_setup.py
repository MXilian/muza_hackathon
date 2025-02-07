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
            CREATE SEQUENCE IF NOT EXISTS museum.seq_user_interest
            INCREMENT BY 1 MINVALUE 1 MAXVALUE 9223372036854775807 START 1 CACHE 1 NO CYCLE;
            
            CREATE SEQUENCE IF NOT EXISTS museum.seq_telegram_user
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
            
            CREATE TABLE IF NOT EXISTS museum.telegram_user (
                tg_id bigint default nextval('museum.seq_telegram_user'),
                PRIMARY KEY (tg_id)
            );

            CREATE TABLE IF NOT EXISTS museum.user_interest (
                user_interest_id bigint default nextval('museum.seq_user_interest'),
                tg_id bigint REFERENCES museum.telegram_user(tg_id),
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
        # Получаем список всех таблиц в схеме museum
        tables_query = '''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'museum' AND table_type = 'BASE TABLE';
        '''
        tables_df = db_helper.read_query(tables_query)
        tables = tables_df['table_name'].tolist()

        # Генерируем запрос для удаления всех таблиц
        if tables:
            drop_tables_query = f"DROP TABLE IF EXISTS {', '.join([f'museum.{table}' for table in tables])} CASCADE;"
            db_helper.execute_query(drop_tables_query)

        # Получаем список всех последовательностей в схеме museum
        sequences_query = '''
            SELECT sequence_name
            FROM information_schema.sequences
            WHERE sequence_schema = 'museum';
        '''
        sequences_df = db_helper.read_query(sequences_query)
        sequences = sequences_df['sequence_name'].tolist()

        # Генерируем запрос для удаления всех последовательностей
        if sequences:
            drop_sequences_query = f"DROP SEQUENCE IF EXISTS {', '.join([f'museum.{sequence}' for sequence in sequences])} CASCADE;"
            db_helper.execute_query(drop_sequences_query)

        print("Все таблицы и последовательности в схеме museum успешно удалены.")
    except Exception as e:
        print(f"Ошибка при удалении таблиц и последовательностей: {e}")
    finally:
        db_helper.close_connection()


# Функция для очистки всех данных без удаления БД
def clear_all_tables():
    """Очистка всех таблиц"""
    db_helper = DbHelper()
    try:
        # Получаем список всех таблиц в схеме museum
        tables_query = '''
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'museum' AND table_type = 'BASE TABLE';
        '''
        tables_df = db_helper.read_query(tables_query)
        tables = tables_df['table_name'].tolist()

        if not tables:
            print("В схеме museum нет таблиц для очистки.")
            return

        # Генерируем запрос для очистки всех таблиц
        truncate_query = f"TRUNCATE TABLE {', '.join([f'museum.{table}' for table in tables])} CASCADE;"
        db_helper.execute_query(truncate_query)

        print("Все таблицы в схеме museum успешно очищены.")
    except Exception as e:
        print(f"Ошибка при очистке таблиц: {e}")
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