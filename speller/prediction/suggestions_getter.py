import abc
import logging
from typing import Sequence
from speller.prediction.chat_gpt_predictor import IChatGptPredictor

from speller.prediction.t9_predictor import IT9Predictor


logger = logging.getLogger(__name__)


class ISuggestionsGetter(abc.ABC):
    @abc.abstractmethod
    def get_suggestions(self, text: str, prefix: Sequence[int], max_suggestions: int) -> Sequence[str]:
        pass


class SuggestionsGetter(ISuggestionsGetter):
    def __init__(self, t9_predictor: IT9Predictor, chat_gpt_predictor: IChatGptPredictor):
        self._t9_predictor = t9_predictor
        self._chat_gpt_predictor = chat_gpt_predictor

    def get_suggestions(self, text: str, prefix: Sequence[int], max_suggestions: int) -> Sequence[str]:
        logger.info("SuggestionsGetter: called get_suggestions")
        if prefix:
            return self._t9_predictor.predict(prefix, max_suggestions)
        else:
            return []