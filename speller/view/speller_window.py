import abc
import copy
from enum import Enum, StrEnum
from itertools import product
import logging
import os
import textwrap
from tkinter import Button, Frame, Label, StringVar, Tk, font

from typing import Any

from PIL import Image, ImageTk

from speller.session.flashing_strategy import FlashingListType
from speller.session.state_manager import IStateManager
from speller.config import ConfigParams

from speller.settings import FilesSettings, StrategySettings

class Color(StrEnum):
    DARK_GREY = '#D9D9D9'
    LIGHT_GRAY ='#E4E4E4'
    WHITE = '#FFFFFF'
    BLACK = '#000000'

    RED = '#FF0000'

class Size(Enum):
    SCREEN_WIDTH = 1024
    SCREEN_HEIGHT = 768

    WIDTH_LEFT = 352
    WIDTH_RIGHT = 273
    HEIGHT_UP = 234
    HEIGHT_DOWN = 352

    WIDTH_MIDDLE = 10
    HEIGHT_MIDDLE = 10

    @classmethod
    def total_width(cls) -> int:
        return cls.WIDTH_LEFT.value + cls.WIDTH_MIDDLE.value + cls.WIDTH_RIGHT.value
    
    @classmethod
    def total_height(cls) -> int:
        return cls.HEIGHT_UP.value + cls.HEIGHT_MIDDLE.value + cls.HEIGHT_DOWN.value
        


logger = logging.getLogger(__name__)


class ISpellerWindow(abc.ABC):
    @abc.abstractmethod
    def run(self) -> None:
        pass


class SpellerWindow(ISpellerWindow):
    _SCREEN_WIDTH = 1920 - 120
    _SCREEN_HEIGHT = 1080 - 80
    _FULLSCREEN = True

    def __init__(self, state_manager: IStateManager, strategy_settings: StrategySettings, files_settings: FilesSettings):
        self._state_manager = state_manager
        self._strategy_settings = strategy_settings
        self._files_settings = files_settings
        self._config = ConfigParams()
        self._initialize_window()

    def _load_images(self, imagename: str, scale: float = 1) -> ImageTk.PhotoImage:
        image = Image.open(os.path.join(self._files_settings.images_dir, imagename + ".png"))
        image = image.resize(
            (int(image.width * scale), int(image.height * scale)),
            Image.LANCZOS,
        )
        return ImageTk.PhotoImage(image)

    def _initialize_window(self):
        self._window = Tk()
        self._window.protocol("WM_DELETE_WINDOW", self._finish)
        if self._FULLSCREEN:
            self._window.attributes("-fullscreen", True)
        else:
            self._window.geometry(f"{self._SCREEN_WIDTH}x{self._SCREEN_HEIGHT}")

        self._main_frame = Frame(self._window, bg=Color.LIGHT_GRAY)
        self._main_frame.pack(fill='both', expand=True)

        self._speller_frame = Frame(self._main_frame, bg=Color.LIGHT_GRAY)
        self._speller_frame.place(relx=0.5, rely=0.5, anchor='center')

        self._speller_frame.rowconfigure(0, minsize=0.4*self._SCREEN_HEIGHT)
        self._speller_frame.rowconfigure(1, minsize=0.6*self._SCREEN_HEIGHT)
        self._speller_frame.columnconfigure(0, minsize=0.6*self._SCREEN_HEIGHT)
        self._speller_frame.columnconfigure(1, minsize=0.4*self._SCREEN_HEIGHT)

        self._frame_pad = 10
        self._field_pad = 20

        self._font = font.Font(family='Inconsolata', size=14)
        self._input_field_text_width = int((0.6*self._SCREEN_HEIGHT - 2*self._field_pad) / self._font.measure('a'))
        self._input_field_text = 'Здесь появится вводимый текст'

        self._input_frame = Frame(self._speller_frame, bg=Color.WHITE)
        self._input_frame.grid(row=0, column=0, padx=self._frame_pad, pady=self._frame_pad, sticky="nsew")
        self._input_title = Label(self._input_frame, text='ВВОД', bg=Color.WHITE, fg=Color.BLACK, font=self._font)
        self._input_title.pack(fill='x')
        self._input_field = Label(self._input_frame, text=self._input_field_text, anchor='nw', justify='left', bg=Color.LIGHT_GRAY, fg=Color.BLACK, font=self._font)
        self._input_field.pack(fill='both', expand=True, padx=self._field_pad, pady=(0, self._field_pad))

        self._suggestions_frame = Frame(self._speller_frame, bg=Color.WHITE)
        self._suggestions_frame.grid(row=0, column=1, padx=self._frame_pad, pady=self._frame_pad, sticky="nsew")
        self._suggestions_title = Label(self._suggestions_frame, text='ВАРИАНТЫ', bg=Color.WHITE, fg=Color.BLACK, font=self._font)
        self._suggestions_title.pack(fill='x')
        self._suggestions_field = Label(self._suggestions_frame, text='', bg=Color.LIGHT_GRAY, fg=Color.BLACK)
        self._suggestions_field.pack(fill='both', expand=True, padx=self._field_pad, pady=(0, self._field_pad))

        self._keyboard_frame = Frame(self._speller_frame, bg=Color.BLACK)
        self._keyboard_frame.grid(row=1, column=0, padx=self._frame_pad, pady=self._frame_pad, sticky="nsew")
        self._initialize_keyboard()

        self._info_frame = Frame(self._speller_frame, bg=Color.WHITE)
        self._info_frame.grid(row=1, column=1, padx=self._frame_pad, pady=self._frame_pad, sticky="nsew")
        self._info_title = Label(self._info_frame, text='ИНФОРМАЦИЯ', bg=Color.WHITE, fg=Color.BLACK, font=self._font)
        self._info_title.pack(fill='x')
        self._info_field = Label(self._info_frame, text='', bg=Color.LIGHT_GRAY, fg=Color.BLACK)
        self._info_field.pack(fill='both', expand=True, padx=self._field_pad, pady=(0, self._field_pad))


        self._start_btn_text = StringVar()
        self._start_btn_text.set("Start")
        self._start_btn = Button(self._speller_frame, textvariable=self._start_btn_text, command=self._handle_start_btn)
        self._start_btn.grid(row=self._config.number_of_rows + 1, column=0, columnspan=self._config.number_of_columns)

    def _handle_start_btn(self):
        if self._start_btn_text.get() == 'Start':
            self._state_manager.start_session()
            self._start_btn_text.set('Stop')
        else:
            self._state_manager.finish_session()
            self._start_btn_text.set('Start')

    def _initialize_keyboard(self) -> None:
        pattern = self._files_settings.keyboard_items_pattern
        size = self._strategy_settings.keyboard_size
        self._keyboard_images: list[list[Any]] = [[None for j in range(size)] for i in range(size)] 
        self._keyboard_labels = copy.deepcopy(self._keyboard_images)

        for i in range(size):
            self._keyboard_frame.rowconfigure(i, weight=1)
            self._keyboard_frame.columnconfigure(i, weight=1)

        for i, j in product(range(size), range(size)):
            image = self._load_images(pattern.format(i, j), self._files_settings.keyboard_items_scale)
            self._keyboard_images[i][j] = image
            label = Label(self._keyboard_frame, image=image)
            self._keyboard_labels[i][j] = label
            label.grid(row=i, column=j)

        self._keyboard_flash_image = self._load_images(
            self._files_settings.keyboard_flash_item_filename, self._files_settings.keyboard_items_scale
        )


    def _set_input_field_text(self, text: str) -> None:
        lines = textwrap.wrap(text, width=self._input_field_text_width)
        self._input_field.config(text='\n'.join(lines))

    def _update_keyboard(self, flashing_list: FlashingListType) -> None:
        size = self._strategy_settings.keyboard_size
        for i, j in product(range(size), range(size)):
            if (i, j) in flashing_list:
                self._keyboard_labels[i][j].configure(image=self._keyboard_flash_image)
            else:
                self._keyboard_labels[i][j].configure(image=self._keyboard_images[i][j])

    def run(self) -> None:
        self._update_loop()
        self._window.mainloop()

    def _update_loop(self):
        if self._state_manager.shutdown_event.is_set():
            self._window.destroy()
            return
        
        state = self._state_manager.get_state()

        if self._input_field_text != state.full_text:
            self._input_field_text = state.full_text
            self._set_input_field_text(state.full_text + '_')

        self._update_keyboard(state.flashing_list)
        self._window.after(self._config.view_update_interval, self._update_loop)

    def _finish(self) -> None:
        self._state_manager.shutdown()
        self._window.destroy()
