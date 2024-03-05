import abc
from functools import partial
import logging
from threading import Event
from tkinter import Button, StringVar, Tk
from typing import Callable

from speller.session.flashing_strategy import FlashingListType, FlashingSequenceType
from speller.session.state_manager import IStateManager
from speller.config import ConfigParams


logger = logging.getLogger(__name__)


class ISpellerWindow(abc.ABC):
    @abc.abstractmethod
    def run(self) -> None:
        pass


class SpellerWindow(ISpellerWindow):
    def __init__(self, state_manager: IStateManager):
        self._state_manager = state_manager
        self._config = ConfigParams()
        self._window = Tk()
        self._window.protocol("WM_DELETE_WINDOW", self._finish)
        self._initialize()

    def _initialize(self):
        self._start_btn_text = StringVar()
        self._start_btn_text.set("Start")
        self._start_btn = Button(self._window, textvariable=self._start_btn_text, command=self._state_manager.start_session)
        self._start_btn.grid(row=self._config.number_of_rows + 1, column=self._config.number_of_columns - 1)

    def run(self) -> None:
        self._update_loop()
        self._window.mainloop()

    def _update_loop(self):
        state = self._state_manager.get_state()
        self._start_btn_text.set(str(state))
        # logger.info("CurrentState: %s", state)
        self._window.after(self._config.view_update_interval, self._update_loop)

    def _finish(self) -> None:
        logger.error("FINISH!")
        self._state_manager.shutdown()
        self._window.destroy()
