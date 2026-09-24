import logging

import requests

from constants import AIConstants, ErrorMessages, LogMessages
from app.exceptions import AIServiceError
from app.validators import validate_chat


logger = logging.getLogger(__name__)


class AIService:
    def __init__(self, settings):
        self.settings = settings

    def _sistem_talimati(self):
        return self.settings.BUSINESS_CONTEXT

    def yanit_uret(self, mesaj, gecmis=None):
        mesaj, gecmis = validate_chat({
            "mesaj": mesaj,
            "gecmis": [] if gecmis is None else gecmis,
        })

        if self.settings.AI_PROVIDER != "groq":
            raise AIServiceError(ErrorMessages.AI_PROVIDER)

        if not self.settings.GROQ_API_KEY.strip():
            return AIConstants.DEMO_REPLY

        messages = [
            {
                "role": "system",
                "content": self._sistem_talimati(),
            },
            *gecmis,
            {
                "role": "user",
                "content": mesaj,
            },
        ]

        return self._groq_yaniti_al(messages)

    def _groq_yaniti_al(self, messages):
        headers = {
            "Authorization": (
                f"Bearer {self.settings.GROQ_API_KEY.strip()}"
            ),
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.settings.GROQ_MODEL,
            "messages": messages,
            "temperature": AIConstants.TEMPERATURE,
            "max_completion_tokens": AIConstants.MAX_COMPLETION_TOKENS,
            "reasoning_effort": AIConstants.REASONING_EFFORT,
        }

        try:
            response = requests.post(
                AIConstants.API_URL,
                headers=headers,
                json=payload,
                timeout=(
                    AIConstants.CONNECT_TIMEOUT,
                    AIConstants.READ_TIMEOUT,
                ),
            )

            response.raise_for_status()

        except requests.Timeout as error:
            logger.warning(LogMessages.AI_TIMEOUT)

            raise AIServiceError(
                ErrorMessages.AI_TIMEOUT
            ) from error

        except requests.RequestException as error:
            status = (
                error.response.status_code
                if error.response is not None
                else None
            )

            logger.warning(
                LogMessages.AI_REQUEST_FAILED,
                status,
            )

            raise AIServiceError(
                ErrorMessages.AI_UNAVAILABLE
            ) from error

        try:
            data = response.json()
            cevap = data["choices"][0]["message"]["content"]

        except (ValueError, KeyError, IndexError, TypeError) as error:
            logger.warning(LogMessages.AI_INVALID_RESPONSE)

            raise AIServiceError(
                ErrorMessages.AI_INVALID_RESPONSE
            ) from error

        if not isinstance(cevap, str) or not cevap.strip():
            logger.warning(LogMessages.AI_INVALID_RESPONSE)

            raise AIServiceError(
                ErrorMessages.AI_INVALID_RESPONSE
            )

        return cevap.strip()


