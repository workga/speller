import abc
from dataclasses import dataclass
import logging
from threading import Event
from typing import Sequence
from speller.prediction.suggestions_getter import ISuggestionsGetter

from speller.prediction.t9_predictor import T9_CHARS
from speller.session.entity import FlashingListType
from speller.settings import StateManagerSettings


logger = logging.getLogger(__name__)


@dataclass
class HistoryState:
    text: str
    prefix: list[int]
    suggestions: Sequence[str]

    @property
    def full_text(self) -> str:
        return self.text + ''.join(T9_CHARS[i][0] for i in self.prefix)


@dataclass
class State(HistoryState):
    info: str
    preselected_clear: bool
    preselected_cancel: bool
    flashing_list: FlashingListType


class IStateManager(abc.ABC):
    is_session_running: Event
    shutdown_event: Event

    @abc.abstractmethod
    def get_state(self) -> State:
        pass

    @abc.abstractmethod
    def set_flashing_list(self, flashing_list: FlashingListType) -> None:
        pass

    @abc.abstractmethod
    def reset_flashing_list(self) -> None:
        pass

    @abc.abstractmethod
    def start_session(self) -> None:
        pass

    @abc.abstractmethod
    def finish_session(self) -> None:
        pass

    @abc.abstractmethod
    def shutdown(self) -> None:
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
    

class StateManager(IStateManager):
    def __init__(self, suggestions_getter: ISuggestionsGetter, shutdown_event: Event, settings: StateManagerSettings):
        self._suggestions_getter = suggestions_getter
        self.shutdown_event = shutdown_event
        self._settings = settings
        self._history: list[HistoryState] = []
        self._initialize()
        self.info = ""
        self.is_session_running: Event = Event()

    def _initialize(self) -> None:
        self.text = ""
        self.prefix = []
        self.suggestions =[]
        self.preselected_clear = False
        self.preselected_cancel = False
        self.flashing_list = []

    def set_flashing_list(self, flashing_list: FlashingListType) -> None:
        self.flashing_list = flashing_list

    def reset_flashing_list(self) -> None:
        self.flashing_list = []

    def start_session(self) -> None:
        self.is_session_running.set()

    def finish_session(self) -> None:
        self.is_session_running.clear()

    def shutdown(self) -> None:
        self.shutdown_event.set()
    
    def get_state(self) -> State:
        return State(
            text=self.text,
            prefix=self.prefix,
            suggestions=self.suggestions,
            info=self.info,
            preselected_clear=self.preselected_clear,
            preselected_cancel=self.preselected_cancel,
            flashing_list=self.flashing_list
        )

    @property
    def _history_state(self) -> HistoryState:
        return HistoryState(
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
    
    def _update_suggestions(self):
        self.suggestions = self._suggestions_getter.get_suggestions(self.text, self.prefix, self._settings.max_suggestions)
    
    def t9_input(self, charset_number: int) -> None:
        self.info = f'T9 {T9_CHARS[charset_number].upper()}'

        self.preselected_clear = False
        self.preselected_cancel = False

        self.prefix.append(charset_number)
        self._update_suggestions()


        self._history.append(self._history_state)
        logger.info("StateManager: t9_input, new state: %s", self._history_state)

    def suggestion_input(self, suggestion_number: int) -> None:
        self.preselected_clear = False
        self.preselected_cancel = False

        if suggestion_number >= len(self.suggestions):
            logger.info("StateManager: suggestion_number is big, skip it")
            self.info = f'ВАРИАНТ {suggestion_number + 1} НЕДОСТУПЕН'
            return
        self.info = f'ВАРИАНТ {suggestion_number + 1}' 
        
        self.text += self.suggestions[suggestion_number] + " "
        self.prefix = []
        self._update_suggestions()


        self._history.append(self._history_state)
        logger.info("StateManager: suggestions_input, new state: %s", self._history_state)

    def clear_input(self) -> None:
        self.preselected_cancel = False
        if not self.preselected_clear:
            self.preselected_clear = True
            self.info = f'ПОВТОРИТЕ СБРОС' 
            logger.info("StateManager: clear_input, preselect, new state: %s", self._history_state)
        else:
            self._initialize()
            self._history.append(self._history_state)
            self.info = f'СБРОС'
            logger.info("StateManager: clear_input, clear, new state: %s", self._history_state)

    def cancel_input(self) -> None:
        self.preselected_clear = False
        if not self.preselected_cancel:
            self.preselected_cancel = True
            self.info = f'ПОВТОРИТЕ ОТМЕНА' 
            logger.info("StateManager: cancel_input, preselected, new state: %s", self._history_state)
        else:
            self.preselected_cancel = False
            self._cancel()
            self.info = f'ОТМЕНА' 
            logger.info("StateManager: cancel_input, cancel, new state: %s", self._history_state)
    
        

    


    
    



