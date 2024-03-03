import abc
from typing import Sequence
from speller.session.flashing_strategy import ItemPositionType
from speller.prediction.t9_predictor import T9_CHARS


class BaseCommand(abc.ABC):
    pass


class ICommandDecoder(abc.ABC):
    @abc.abstractmethod
    def decode_command(self, item_position: ItemPositionType) -> BaseCommand:
        pass


class InputT9Command(BaseCommand):
    def __init__(self, charset_number: int):
        self.charset_number = charset_number


class InputSuggestionCommand(BaseCommand):
    def __init__(self, suggestion_number: int):
        self.suggestion_number = suggestion_number


class InputCancelCommand(BaseCommand):
    pass


class InputClearCommand(BaseCommand):
    pass


class CommandDecoder(ICommandDecoder):
    def __init__(self):
        self._mapping = (
            (InputT9Command(0), InputT9Command(1), InputT9Command(2), InputT9Command(3)),
            (InputT9Command(4), InputT9Command(5), InputT9Command(6), InputT9Command(7)),
            (InputSuggestionCommand(0), InputSuggestionCommand(1), InputSuggestionCommand(2), InputSuggestionCommand(3)),
            (InputSuggestionCommand(4), InputSuggestionCommand(5), InputClearCommand(), InputCancelCommand()),
        )

    def decode_command(self, item_position: ItemPositionType) -> BaseCommand:
        return self._mapping[item_position[0]][item_position[1]]
        
