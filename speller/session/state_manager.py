import abc
from dataclasses import dataclass
from datetime import datetime
from functools import singledispatchmethod
import logging
from threading import Event
from typing import Sequence
from speller.prediction.suggestions_getter import ISuggestionsGetter

from speller.prediction.t9_predictor import T9_CHARS
from speller.session.command_decoder import BaseCommand, InputCancelCommand, InputClearCommand, InputSuggestionCommand, InputT9Command
from speller.session.entity import FlashingListType
from speller.settings import ExperimentSettings, StateManagerSettings, StrategySettings


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

    session_name: str
    session_comment: str
    session_target: int
    session_reps: int
    session_cycles: int
    session_start_time: datetime
    

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
    def start_session(self, name: str, comment: str, target: int, reps: int, cycles: int) -> None:
        pass

    @abc.abstractmethod
    def finish_session(self) -> None:
        pass

    @abc.abstractmethod
    def shutdown(self) -> None:
        pass

    @abc.abstractmethod
    def handle_command(self, command: BaseCommand) -> None:
        pass
    

class StateManager(IStateManager):
    def __init__(
        self,
        suggestions_getter: ISuggestionsGetter,
        shutdown_event: Event, settings: StateManagerSettings,
        strategy_settings: StrategySettings,
        experiment_settings: ExperimentSettings,
    ):
        self._suggestions_getter = suggestions_getter
        self.shutdown_event = shutdown_event
        self._settings = settings
        self._strategy_settings = strategy_settings
        self._experiment_settings = experiment_settings
        self._history: list[HistoryState] = []
        self._initialize()
        self.info = ""
        self.info_counter = 1
        self.is_session_running: Event = Event()

        self.session_name = self._experiment_settings.name
        self.session_comment = self._experiment_settings.comment
        self.session_target = self._experiment_settings.target
        self.session_reps = self._strategy_settings.repetitions_count
        self.session_cycles = self._experiment_settings.cycles_count
        self.session_start_time = datetime.now()

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

    def start_session(self, name: str, comment: str, target: int, reps: int, cycles: int) -> None:
        self.session_name = name
        self.session_comment = comment
        self.session_target = target
        self.session_reps = reps
        self.session_cycles = cycles
        self.session_start_time = datetime.now()
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
    
    def _t9_input(self, charset_number: int) -> None:
        self.info = f'{self.info_counter}. T9 {T9_CHARS[charset_number].upper()}'
        self.info_counter += 1

        self.preselected_clear = False
        self.preselected_cancel = False

        self.prefix.append(charset_number)
        self._update_suggestions()


        self._history.append(self._history_state)
        logger.info("StateManager: _t9_input, new state: %s", self._history_state)

    def _suggestion_input(self, suggestion_number: int) -> None:
        self.preselected_clear = False
        self.preselected_cancel = False

        if suggestion_number >= len(self.suggestions):
            logger.info("StateManager: suggestion_number is big, skip it")
            self.info = f'{self.info_counter}. ВАРИАНТ {suggestion_number + 1} НЕДОСТУПЕН'
            self.info_counter += 1
            return
        self.info = f'{self.info_counter}. ВАРИАНТ {suggestion_number + 1}'
        self.info_counter += 1
        
        self.text += self.suggestions[suggestion_number] + " "
        self.prefix = []
        self._update_suggestions()


        self._history.append(self._history_state)
        logger.info("StateManager: suggestions_input, new state: %s", self._history_state)

    def _clear_input(self) -> None:
        self.preselected_cancel = False
        if not self.preselected_clear:
            self.preselected_clear = True
            self.info = f'{self.info_counter}. ПОВТОРИТЕ СБРОС' 
            logger.info("StateManager: _clear_input, preselect, new state: %s", self._history_state)
        else:
            self._initialize()
            self._history.append(self._history_state)
            self.info = f'{self.info_counter}. СБРОС'
            logger.info("StateManager: _clear_input, clear, new state: %s", self._history_state)
        self.info_counter += 1

    def _cancel_input(self) -> None:
        self.preselected_clear = False
        if not self.preselected_cancel:
            self.preselected_cancel = True
            self.info = f'{self.info_counter}. ПОВТОРИТЕ ОТМЕНА' 
            logger.info("StateManager: _cancel_input, preselected, new state: %s", self._history_state)
        else:
            self.preselected_cancel = False
            self._cancel()
            self.info = f'{self.info_counter}. ОТМЕНА' 
            logger.info("StateManager: _cancel_input, cancel, new state: %s", self._history_state)
        self.info_counter += 1

    @singledispatchmethod
    def handle_command(self, command: BaseCommand) -> None:
        raise RuntimeError(f"Unknown command type {command}!")
    
    @handle_command.register
    def _handle_input_t9_command(self, command: InputT9Command) -> None:
        self._t9_input(command.charset_number)

    @handle_command.register
    def _handle_input_suggestion_command(self, command: InputSuggestionCommand) -> None:
        self._suggestion_input(command.suggestion_number)

    @handle_command.register
    def _handle_input_clear_command(self, command: InputClearCommand) -> None:
        self._clear_input()

    @handle_command.register
    def _handle_input_cancel_command(self, command: InputCancelCommand) -> None:
        self._cancel_input()
    
        

    


    
    



