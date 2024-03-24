import abc
from functools import singledispatchmethod
import logging

from speller.session.sequence_handler import ISequenceHandler
from speller.session.command_decoder import BaseCommand, ICommandDecoder, InputCancelCommand, InputClearCommand, InputSuggestionCommand, InputT9Command
from speller.session.state_manager import IStateManager


logger = logging.getLogger(__name__)


class SpellerRunner:
    def __init__(
        self,
        sequence_handler: ISequenceHandler,
        command_decoder: ICommandDecoder,
        state_manager: IStateManager,
    ):
        self._sequence_handler = sequence_handler
        self._command_decoder = command_decoder
        self._state_manager = state_manager

    def run(self) -> None:
        while True:
            if self._state_manager.is_session_running.wait(1):
                logger.debug("SpellerRunner: start session")
                self._handle_session()
            if self._state_manager.shutdown_event.is_set():
                logger.info("SpellerRunner: shutdown")
                return

    def _handle_session(self) -> None:
        while self._state_manager.is_session_running.is_set() and not self._state_manager.shutdown_event.is_set():
            predicted_item_position = self._sequence_handler.handle_sequence()
            logger.debug("SpellerRunner: got position=%s", predicted_item_position)
            command = self._command_decoder.decode_command(predicted_item_position)
            logger.info("SpellerRunner: got command %s", command)
            self._handle_command(command)

    @singledispatchmethod
    def _handle_command(self, command: BaseCommand) -> None:
        raise RuntimeError(f"Unknown command type {command}!")
    
    @_handle_command.register
    def _handle_input_t9_command(self, command: InputT9Command) -> None:
        self._state_manager.t9_input(command.charset_number)

    @_handle_command.register
    def _handle_input_suggestion_command(self, command: InputSuggestionCommand) -> None:
        self._state_manager.suggestion_input(command.suggestion_number)

    @_handle_command.register
    def _handle_input_clear_command(self, command: InputClearCommand) -> None:
        self._state_manager.clear_input()

    @_handle_command.register
    def _handle_input_cancel_command(self, command: InputCancelCommand) -> None:
        self._state_manager.cancel_input()
