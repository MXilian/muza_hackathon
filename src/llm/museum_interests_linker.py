from typing import Dict, Any, List

from src.bot.bot_db_connector import BotDbConnector
from src.db.db_helper import DbHelper
from src.llm.mistral_connector import MistralConnector
from src.utils.logger import log


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
            "Интерес должен привязываться к музею только в том случае, если этой теме соответствует как минимум "
            "один зал или памятник, а не отдельный экспонат."
            "В ответе перечисли только названия подходящих интересов через запятую, без дополнительных комментариев."
        )
        log(f"[MuseumInterestLinker] отправляем запрос по музею {museum['name']}")

        # Отправляем запрос в Mistral
        response = self.mistral_connector.generate_text(prompt, temperature = 0.6)
        linked_interests = self.mistral_connector.extract_response_text(response)
        log(f"[MuseumInterestLinker] linked_interests {linked_interests}")

        if linked_interests:
            # Разделяем ответ на список интересов
            return [interest.strip() for interest in linked_interests.split(",")]
        return []


    @staticmethod
    def save_linked_interests(museum_id: int, interests: List[str]):
        """
        Связывает музей с интересами в БД

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
                        VALUES (:museum_id, :interest_id)
                        ON CONFLICT DO NOTHING;
                    '''
                    db_helper.execute_query(query, {"museum_id": museum_id, "interest_id": int(interest_id)})
        finally:
            db_helper.close_connection()