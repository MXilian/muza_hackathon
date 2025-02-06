from src.db.db_helper import DbHelper

# Класс для соединения бота с БД
class BotDbConnector:
    @staticmethod
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

    @staticmethod
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

    @staticmethod
    def add_interest(tg_id, interest_id):
        """Добавление интереса пользователю"""
        BotDbConnector.add_user(tg_id)  # Создаем пользователя, если его нет
        db_helper = DbHelper()
        try:
            # Проверяем, существует ли связь пользователь-интерес
            check_query = '''
                SELECT 1 
                FROM museum.user_interest 
                WHERE tg_id = %s AND interest_id = %s;
            '''
            df = db_helper.read_query(check_query, (tg_id, interest_id))
            if not df.empty:
                return  # Интерес уже добавлен

            # Добавляем интерес, если его нет
            insert_query = '''
                INSERT INTO museum.user_interest (tg_id, interest_id) 
                VALUES (%s, %s);
            '''
            db_helper.insert_data(insert_query, (tg_id, interest_id))
        finally:
            db_helper.close_connection()

    @staticmethod
    def get_user_interests(tg_id):
        """Получение списка интересов пользователя"""
        BotDbConnector.add_user(tg_id)  # Создаем пользователя, если его нет
        db_helper = DbHelper()
        try:
            query = '''
                SELECT i.interest_name
                FROM museum.user_interest ui
                JOIN museum.interest i ON ui.interest_id = i.interest_id
                WHERE ui.tg_id = %s;
            '''
            df = db_helper.read_query(query, (tg_id,))
            return df['interest_name'].tolist() if not df.empty else []
        finally:
            db_helper.close_connection()

    @staticmethod
    def remove_interest(tg_id, interest_id):
        """Удаление интереса пользователя"""
        db_helper = DbHelper()
        try:
            # Проверяем, существует ли пользователь
            check_user_query = '''
                SELECT 1 
                FROM museum."user" 
                WHERE tg_id = %s;
            '''
            user_exists = db_helper.read_query(check_user_query, (tg_id,))
            if user_exists.empty:
                return  # Пользователя нет, ничего не делаем

            # Удаляем связь пользователь-интерес
            delete_query = '''
                DELETE FROM museum.user_interest
                WHERE tg_id = %s AND interest_id = %s;
            '''
            db_helper.execute_query(delete_query, (tg_id, interest_id))
        finally:
            db_helper.close_connection()

    @staticmethod
    def find_interests(tg_id, interest_ids):
        """Поиск интересов у пользователя"""
        BotDbConnector.add_user(tg_id)  # Создаем пользователя, если его нет
        db_helper = DbHelper()
        try:
            query = '''
                SELECT 1 AS res
                FROM museum.user_interest
                WHERE tg_id = %s AND interest_id = ANY(%s)
                LIMIT 1
            '''
            df = db_helper.read_query(query, (tg_id, list(interest_ids)))
            return not df.empty
        finally:
            db_helper.close_connection()