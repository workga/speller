import abc
from dataclasses import dataclass
from typing import Sequence
from speller.prediction.suggestions_getter import ISuggestionsGetter

from speller.prediction.t9_predictor import T9_CHARS
from speller.session.flashing_strategy import ItemPositionType


class IStateManager(abc.ABC):
    text: str
    prefix: list[int]
    suggestions: Sequence[str]
    preselected_clear: bool
    preselected_cancel: bool
    info: str

    @property
    @abc.abstractmethod
    def full_text(self) -> str:
        pass

    @abc.abstractmethod
    def t9_input(self, charset_number: int) -> None:
        pass

    @abc.abstractmethod
    def suggestion_input(self, suggestion_number: int) -> None:
        pass

    @abc.abstractmethod
    def clear_input(self) -> None:
        pass

    @abc.abstractmethod
    def cancel_input(self) -> None:
        pass

@dataclass
class State:
    text: str
    prefix: list[int]
    suggestions: Sequence[str]

class StateManager(IStateManager):
    _MAX_SUGGESTIONS = 6

    def __init__(self, suggestions_getter: ISuggestionsGetter):
        self._suggestions_getter = suggestions_getter
        self._initialize()
        self._history: list[State] = []

    def _initialize(self) -> None:
        self.text = ""
        self.prefix = []
        self.suggestions =[]
        self.preselected_clear = False
        self.preselected_cancel = False

    @property
    def _state(self) -> State:
        return State(
            text=self.text,
            prefix=self.prefix,
            suggestions=self.suggestions,
        )

    def _cancel(self) -> None:
        if not self._history:
            return
        previous_state = self._history.pop()
        self.text = previous_state.text
        self.prefix = previous_state.prefix
        self.suggestions = previous_state.suggestions

    @property
    def full_text(self) -> str:
        return self.text + ''.join(T9_CHARS[i][0] for i in self.prefix)
    
    def _update_suggestions(self):
        self.suggestions = self._suggestions_getter.get_suggestions(self.text, self.prefix, self._MAX_SUGGESTIONS)
    
    def t9_input(self, charset_number: int) -> None:
        self.preselected_clear = False
        self.preselected_cancel = False

        self.prefix.append(charset_number)
        self._update_suggestions()

        self._history.append(self._state)

    def suggestion_input(self, suggestion_number: int) -> None:
        self.preselected_clear = False
        self.preselected_cancel = False

        if suggestion_number >= len(self.suggestions):
            return
        
        self.text = " ".join((self.text, self.suggestions[suggestion_number]))
        self.prefix = []
        self._update_suggestions()

        self._history.append(self._state)

    def clear_input(self) -> None:
        self.preselected_cancel = False
        if not self.preselected_clear:
            self.preselected_clear = True
            return
        else:
            self._initialize()
            self._history.append(self._state)

    def cancel_input(self) -> None:
        self.preselected_clear = False
        if not self.preselected_cancel:
            self.preselected_cancel = True
            return
        else:
            self.preselected_cancel = False
            self._cancel()
    
        

    


    
    



