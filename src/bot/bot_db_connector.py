from typing import List, Dict, Any, Optional

from src.db.db_helper import DbHelper
from src.utils.logger import log


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
                INSERT INTO museum.telegram_user (tg_id) VALUES (:tg_id)
                ON CONFLICT (tg_id) DO NOTHING;  
            '''
            db_helper.insert_data(query, {"tg_id": tg_id})
        finally:
            db_helper.close_connection()

    @staticmethod
    def get_interest_id(interest_name):
        """Получение ID интереса по названию"""
        db_helper = DbHelper()
        try:
            query = '''
                SELECT interest_id FROM museum.interest WHERE interest_name = :interest_name
            '''
            df = db_helper.read_query(query, {"interest_name": interest_name})
            return df['interest_id'].iloc[0] if not df.empty else None
        except Exception as e:
            log(f"Ошибка при получении id интереса: {e}")
            raise
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
                WHERE tg_id = :tg_id AND interest_id = :interest_id;
            '''
            df = db_helper.read_query(check_query, {"tg_id": tg_id, "interest_id": int(interest_id)})
            log(f"Связь юзер-интерес: {df}")
            if not df.empty:
                log(f"empty: {df}")
                return  # Интерес уже добавлен

            # Добавляем интерес, если его нет
            insert_query = '''
                INSERT INTO museum.user_interest (tg_id, interest_id) 
                VALUES (:tg_id, :interest_id);
            '''
            db_helper.insert_data(insert_query, {"tg_id": tg_id, "interest_id": int(interest_id)})
            log(f"Добавлен интерес: {interest_id} пользователю {tg_id}")
        except Exception as e:
            log(f"Ошибка при добавлении интереса: {e}")
            raise
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
                WHERE ui.tg_id = :tg_id;
            '''
            df = db_helper.read_query(query, {"tg_id": tg_id})
            return df['interest_name'].tolist() if not df.empty else []
        except Exception as e:
            log(f"Ошибка при получении интересов пользователя: {e}")
            raise
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
                FROM museum.telegram_user
                WHERE tg_id = :tg_id;
            '''
            user_exists = db_helper.read_query(check_user_query, {"tg_id": tg_id})
            if user_exists.empty:
                return  # Пользователя нет, ничего не делаем

            # Удаляем связь пользователь-интерес
            delete_query = '''
                DELETE FROM museum.user_interest
                WHERE tg_id = :tg_id AND interest_id = :interest_id;
            '''
            db_helper.execute_query(delete_query, {"tg_id": tg_id, "interest_id": int(interest_id)})
        finally:
            db_helper.close_connection()

    @staticmethod
    def find_interests(tg_id, interest_ids):
        """Поиск интересов у пользователя"""
        BotDbConnector.add_user(tg_id)  # Создаем пользователя, если его нет
        db_helper = DbHelper()
        try:
            query = '''
                SELECT EXISTS (
                    SELECT 1
                    FROM museum.user_interest
                    WHERE tg_id = :tg_id 
                    AND interest_id IN :interest_ids
                ) as has_interests
            '''
            df = db_helper.read_query(query, {"tg_id": tg_id, "interest_ids": tuple(interest_ids)})
            return bool(df.iloc[0]['has_interests'])
        finally:
            db_helper.close_connection()

    @staticmethod
    def filter_museums_by_city(city: str, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Фильтрует музеи по городу с возможностью ограничения количества результатов.

        :param city: Город для фильтрации.
        :param limit: Опциональный параметр для ограничения количества результатов.
        :return: Список музеев в указанном городе (ограниченный, если указан limit).
        """
        db_helper = DbHelper()
        try:
            query = '''
            SELECT museum_id, name, description, city, address
            FROM museum.museum
            WHERE LOWER(city) = LOWER(:city)
        '''
            params = {"city": city}

            # Добавляем LIMIT в запрос, если параметр limit указан
            if limit is not None and limit > 0:
                query += ' LIMIT :limit;'
                params["limit"] = limit
            else:
                query += ';'

            return db_helper.read_query(query, params).to_dict('records')
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
                WHERE mi.museum_id = :museum_id;
            '''
            df = db_helper.read_query(query, {"museum_id": museum_id})
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
