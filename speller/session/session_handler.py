import abc
from functools import singledispatchmethod

from speller.session.sequence_handler import ISequenceHandler
from speller.session.command_decoder import BaseCommand, ICommandDecoder, InputCancelCommand, InputClearCommand, InputSuggestionCommand, InputT9Command
from speller.session.state_manager import IStateManager


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
    ):
        self._sequence_handler = sequence_handler
        self._command_decoder = command_decoder
        self._state_manager = state_manager

    def handle_session(self) -> None:
        while True:
            flashing_sequence = self._sequence_handler.get_flashing_sequence()
            
            # use here flashing_sequence to start flashing in IView synchronously
            # do not forget about baseline

            predicted_item_position = self._sequence_handler.handle_sequence(flashing_sequence)
            command = self._command_decoder.decode_command(predicted_item_position)
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



