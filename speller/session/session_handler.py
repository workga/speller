import abc
from functools import singledispatchmethod
import logging
from threading import Event

from speller.session.sequence_handler import ISequenceHandler
from speller.session.command_decoder import BaseCommand, ICommandDecoder, InputCancelCommand, InputClearCommand, InputSuggestionCommand, InputT9Command
from speller.session.state_manager import IStateManager


logger = logging.getLogger(__name__)


class ISessionHandler(abc.ABC):
    @abc.abstractmethod
    def handle_session(self) -> None:
        pass


class SessionHandler(ISessionHandler):
    def __init__(
        self,
        sequence_handler: ISequenceHandler,
        command_decoder: ICommandDecoder,
        state_manager: IStateManager,
        shutdown_event: Event,
    ):
        self._sequence_handler = sequence_handler
        self._command_decoder = command_decoder
        self._state_manager = state_manager
        self._shutdown_event = shutdown_event

    def handle_session(self) -> None:
        logger.info("SessionHandler: start handling")
        while not self._shutdown_event.is_set():
            flashing_sequence = self._sequence_handler.get_flashing_sequence()
            logger.info("SessionHandler: created flashing sequence")
            
            # use here flashing_sequence to start flashing in IView synchronously
            # do not forget about baseline

            predicted_item_position = self._sequence_handler.handle_sequence(flashing_sequence)
            logger.info("SessionHandler: got position=%s", predicted_item_position)
            command = self._command_decoder.decode_command(predicted_item_position)
            logger.info("SessionHandler: got command %s", command)
            self._handle_command(command)
        logger.info("SessionHandler: shutdown_event was set")

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



