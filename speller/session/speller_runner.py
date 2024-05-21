import logging

from speller.session.sequence_handler import ISequenceHandler
from speller.session.state_manager import IStateManager


logger = logging.getLogger(__name__)


class SpellerRunner:
    def __init__(
        self,
        sequence_handler: ISequenceHandler,
        state_manager: IStateManager,
    ):
        self._sequence_handler = sequence_handler
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
        cycles = 0
        max_cycles = self._state_manager.session_cycles

        while (
            cycles < max_cycles
            and self._state_manager.is_session_running.is_set()
            and not self._state_manager.shutdown_event.is_set()
        ):
            self._sequence_handler.handle_sequence()
            cycles += 1

        if cycles >= max_cycles:
            self._state_manager.finish_session()
