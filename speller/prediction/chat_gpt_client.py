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

        try:
            if all(str(i) in content for i in range(1, max_words + 1)):
                options = [' '.join(re.findall(r'([а-я]+)', line.lower())) for line in content.splitlines()]
            else:
                options: list[str] = json.loads(content)

            words = [option.lower().removeprefix(text).split(' ', 1)[0] for option in options]
            words = list(set(filter(lambda word: text[:-1] not in word, words)))
            if len(words) > max_words:
                logger.warn("Expected %d words, got %d", max_words, len(words))
                words = words[:max_words]
        except:
            logger.exception('Can not parse ChatGPT response %s to text %s', content, text)
            return []

        return words