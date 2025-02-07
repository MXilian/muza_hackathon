import os
import requests
from typing import Dict, Optional

from src.utils.logger import log


class MistralConnector:
    """Класс для интеграции с API Mistral."""

    def __init__(
            self,
            api_key: Optional[str] = None,
            api_url: str = "https://api.mistral.ai/v1/chat/completions",
            default_model: str = "mistral-small-latest",
            default_max_tokens: int = 5000,
            default_temperature: float = 0.7,
    ):
        """
        Инициализация интегратора.

        :param api_key: API-ключ для доступа к Mistral. Если не указан, берется из переменной окружения MISTRAL_API_KEY.
        :param api_url: URL эндпоинта API (по умолчанию: "https://api.mistral.ai/v1/chat/completions").
        :param default_model: Модель по умолчанию (по умолчанию: "mistral-small-latest").
        :param default_max_tokens: Максимальное количество токенов в ответе (по умолчанию: 1500).
        :param default_temperature: Креативность ответа (по умолчанию: 0.7).
        """
        self.api_key = api_key or self._get_api_key_from_env()
        if not self.api_key:
            raise ValueError(
                "API-ключ не предоставлен и не найден в переменной окружения MISTRAL_API_KEY."
            )

        self.api_url = api_url
        self.default_model = default_model
        self.default_max_tokens = default_max_tokens
        self.default_temperature = default_temperature
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _get_api_key_from_env() -> Optional[str]:
        """
        Получает API-ключ из переменной окружения MISTRAL_API_KEY.

        Возвращает API-ключ или None, если не найден.
        """
        return os.getenv("MISTRAL_API_KEY")

    def generate_text(
            self,
            prompt: str,
            model: Optional[str] = None,
            max_tokens: Optional[int] = None,
            temperature: Optional[float] = None,
    ) -> Dict:
        """
        Генерирует текст с использованием API Mistral.

        :param prompt: Текст запроса.
        :param model: Модель для генерации (если None, используется модель по умолчанию).
        :param max_tokens: Максимальное количество токенов (если None, используется значение по умолчанию).
        :param temperature: Креативность ответа (если None, используется значение по умолчанию).
        Возвращает Ответ API в формате JSON.
        """
        payload = {
            "model": model or self.default_model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": max_tokens or self.default_max_tokens,
            "temperature": temperature or self.default_temperature,
        }

        try:
            log("[MistralConnector] отправка запроса...")
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            response.raise_for_status()  # Проверка HTTP ошибок
            log("[MistralConnector] получен ответ...")
            return response.json()
        except requests.exceptions.RequestException as e:
            return {"error": str(e)}

    @staticmethod
    def extract_response_text(api_response: Dict) -> Optional[str]:
        """
        Извлекает текст ответа из JSON-ответа API.

        :param api_response: Ответ API в формате JSON.
        Возвращает текст ответа или None, если произошла ошибка.
        """
        if "error" in api_response:
            return None
        return api_response.get("choices", [{}])[0].get("message", {}).get("content")
