from typing import List, Dict, Any

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


    @staticmethod
    def filter_museums_by_city(city: str) -> List[Dict[str, Any]]:
        """
        Фильтрует музеи по городу.

        :param city: Город для фильтрации.
        :return: Список музеев в указанном городе.
        """
        db_helper = DbHelper()
        try:
            query = '''
                SELECT museum_id, name, description, city, address
                FROM museum.museum
                WHERE city = %s;
            '''
            return db_helper.read_query(query, (city,)).to_dict('records')
        finally:
            db_helper.close_connection()


    @staticmethod
    def link_museum_interests(museum_id: int, interests: List[str]):
        """
        Связывает музей с интересами.

        :param museum_id: ID музея.
        :param interests: Список интересов для связывания.
        """
        db_helper = DbHelper()
        try:
            for interest in interests:
                interest_id = BotDbConnector.get_interest_id(interest)
                if interest_id:
                    query = '''
                        INSERT INTO museum.museum_interest (museum_id, interest_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    '''
                    db_helper.execute_query(query, (museum_id, interest_id))
        finally:
            db_helper.close_connection()


    @staticmethod
    def get_museum_interests(museum_id: int) -> List[str]:
        """
        Возвращает список интересов, связанных с музеем.

        :param museum_id: ID музея.
        :return: Список интересов.
        """
        db_helper = DbHelper()
        try:
            query = '''
                SELECT i.interest_name
                FROM museum.museum_interest mi
                JOIN museum.interest i ON mi.interest_id = i.interest_id
                WHERE mi.museum_id = %s;
            '''
            df = db_helper.read_query(query, (museum_id,))
            return df['interest_name'].tolist()
        finally:
            db_helper.close_connection()


    @staticmethod
    def filter_museums_by_interests(museums: List[Dict[str, Any]], user_interests: List[str]) -> List[Dict[str, Any]]:
        """
        Фильтрует музеи по интересам пользователя.

        :param museums: Список музеев.
        :param user_interests: Список интересов пользователя.
        :return: Отфильтрованный и отсортированный список музеев.
        """
        filtered_museums = []
        for museum in museums:
            museum_interests = BotDbConnector.get_museum_interests(museum['museum_id'])
            common_interests = set(museum_interests).intersection(set(user_interests))
            if common_interests:
                museum['matched_interest_names'] = ', '.join(common_interests)
                museum['matched_interest_count'] = len(common_interests)
                filtered_museums.append(museum)

        # Сортируем музеи по количеству совпадений и названию
        filtered_museums.sort(key=lambda x: (-x['matched_interest_count'], x['name']))

        # Ограничиваем результат 10 музеями
        return filtered_museums[:10]
