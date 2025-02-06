import pandas as  pd

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
    """Загрузка интересов из CSV файла"""
    interests_data = pd.read_csv('assets/tags.csv')
    interests_data = interests_data.rename(columns={'tags': 'interest_name'})

    db_helper = DbHelper()
    try:
        columns = ",".join(list(interests_data))
        values = "VALUES({})".format(",".join(["%s" for _ in interests_data.columns]))
        insert_stmt = f"INSERT INTO museum.interest ({columns}) {values}"

        cursor = db_helper.connection.cursor()
        cursor.executemany(insert_stmt, interests_data.values)
        db_helper.connection.commit()
        cursor.close()
    finally:
        db_helper.close_connection()