import json
import logging
import re
from typing import Sequence
from gigachat import GigaChat
from gigachat.models import Chat, Messages
from langchain.prompts.chat import (
    AIMessagePromptTemplate,
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage
from sklearn.metrics import max_error
from speller.secrets_settings import ChatGPTSecretsSettings
from speller.settings import ChatGPTSettings


logger = logging.getLogger(__name__)


class ChatGPTClient:
    def __init__(self, settings: ChatGPTSettings, secrets_settings: ChatGPTSecretsSettings):
        self._settings = settings
        self._secrets_settings = secrets_settings
        self._client = GigaChat(credentials=secrets_settings.auth, verify_ssl_certs=False)
    
    def predict(self, text: str, max_words: int, prefixes: list[str] | None = None) -> Sequence[str]:
        if not self._settings.enabled:
            return ['нечто'] * max_words

        prompt = self._settings.template.format(text=text, count=max_words)

        logger.info("Prompt for ChatGPT: %s", prompt)

        result = self._client.chat(
            Chat(
                model=self._settings.model,
                messages=[Messages(role='user', content=prompt)],
                temperature=self._settings.temperature,
            )
        )
        content = result.choices[0].message.content
        logger.info("Answer from ChatGPT: %s", content)

        words = re.findall('\w+', content.lower())
        if len(words) > max_words:
            logger.warn("Expected %d words, got %d", max_words, len(words))
            words = words[:max_words]

        return words