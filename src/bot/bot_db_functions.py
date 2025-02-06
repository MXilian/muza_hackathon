from src.db.db_helper import DbHelper

def add_user(tg_id: int):
    """
    Добавление нового пользователя по Telegram ID.

    :param tg_id: Telegram ID пользователя
    """
    db_helper = DbHelper()
    try:
        query = '''
            INSERT INTO museum."user" (tg_id) VALUES (%s)
            ON CONFLICT (tg_id) DO NOTHING;  -- Избегаем дублирования пользователей
        '''
        db_helper.insert_data(query, (tg_id,))
    finally:
        db_helper.close_connection()

def get_interest_id(interest_name):
    """Получение ID интереса по названию"""
    db_helper = DbHelper()
    try:
        query = '''
            SELECT interest_id FROM museum.interest WHERE interest_name = %s
        '''
        df = db_helper.read_query(query, (interest_name,))
        return df['interest_id'].iloc[0] if not df.empty else None
    finally:
        db_helper.close_connection()

def add_interest(tg_id, interest_id):
    """Добавление интереса пользователю"""
    db_helper = DbHelper()
    try:
        query = '''
            INSERT INTO museum.recommendation (tg_id, interest_id) VALUES (%s, %s)
            ON CONFLICT (tg_id, interest_id) DO NOTHING;
        '''
        db_helper.insert_data(query, (tg_id, interest_id))
    finally:
        db_helper.close_connection()

def get_user_interests(tg_id):
    """Получение списка интересов пользователя"""
    db_helper = DbHelper()
    try:
        query = '''
            SELECT i.interest_name
            FROM museum.recommendation r
            JOIN museum.interest i ON r.interest_id = i.interest_id
            WHERE r.tg_id = %s;
        '''
        df = db_helper.read_query(query, (tg_id,))
        return df['interest_name'].tolist() if not df.empty else []
    finally:
        db_helper.close_connection()


def remove_interest(tg_id, interest_id):
    """Удаление интереса пользователя"""
    db_helper = DbHelper()
    try:
        query = '''
            DELETE FROM museum.recommendation
            WHERE tg_id = %s AND interest_id = %s;
        '''
        db_helper.execute_query(query, (tg_id, interest_id))
    finally:
        db_helper.close_connection()

def find_interests(tg_id, interest_ids):
    """Поиск интересов у пользователя"""
    db_helper = DbHelper()
    try:
        query = '''
            SELECT 1 AS res
            FROM museum.recommendation
            WHERE tg_id = %s AND interest_id = ANY(%s)
            LIMIT 1
        '''
        df = db_helper.read_query(query, (tg_id, list(interest_ids)))
        return not df.empty
    finally:
        db_helper.close_connection()