from typing import Dict, Any, List

from src.db.db_helper import DbHelper
from src.llm.mistral_connector import MistralConnector

# Утилита для связывания музеев с интересами
class MuseumInterestLinker:
    def __init__(self, mistral_connector: MistralConnector):
        """
        Инициализация связывателя интересов с музеями.

        :param mistral_connector: Объект для интеграции с Mistral API.
        """
        self.mistral_connector = mistral_connector

    def link_museum_interests(self, museum: Dict[str, Any], interests: List[str]) -> List[str]:
        """
        Связывает музей с подходящими интересами с помощью Mistral.

        :param museum: Данные музея (название, описание).
        :param interests: Полный список интересов.
        :return: Список подходящих интересов для музея.
        """
        # Формируем запрос для Mistral
        prompt = (
            f"Есть музей: {museum['name']}. "
            f"Описание музея: {museum['description']}. "
            f"Из следующего списка интересов выбери те, которые подходят этому музею: {', '.join(interests)}. "
            "В ответе перечисли только названия подходящих интересов через запятую, без дополнительных комментариев."
        )

        # Отправляем запрос в Mistral
        response = self.mistral_connector.generate_text(prompt)
        linked_interests = self.mistral_connector.extract_response_text(response)

        if linked_interests:
            # Разделяем ответ на список интересов
            return [interest.strip() for interest in linked_interests.split(",")]
        return []

    def save_linked_interests(self, museum_id: int, linked_interests: List[str], interests_dict: Dict[str, int]):
        """
        Сохраняет привязанные интересы в БД.

        :param museum_id: ID музея.
        :param linked_interests: Список подходящих интересов.
        :param interests_dict: Словарь интересов (название -> ID).
        """
        db_helper = DbHelper()
        try:
            for interest in linked_interests:
                if interest in interests_dict:
                    interest_id = interests_dict[interest]
                    query = '''
                        INSERT INTO museum.museum_interest (museum_id, interest_id)
                        VALUES (%s, %s)
                        ON CONFLICT DO NOTHING;
                    '''
                    db_helper.execute_query(query, (museum_id, interest_id))
        finally:
            db_helper.close_connection()