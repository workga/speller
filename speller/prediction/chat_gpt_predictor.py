import abc
from typing import Sequence

from speller.prediction.chat_gpt_client import ChatGPTClient


class IChatGptPredictor(abc.ABC):
    @abc.abstractmethod
    def predict(self, text: str, max_words: int, prefixes: list[str] | None = None) -> Sequence[str]:
        pass

class ChatGptPredictor(IChatGptPredictor):
    def __init__(self, chat_gpt_client: ChatGPTClient):
        self._chat_gpt_client = chat_gpt_client

    def predict(self, text: str, max_words: int, prefixes: list[str] | None = None) -> Sequence[str]:
        return self._chat_gpt_client.predict(text, max_words, prefixes)