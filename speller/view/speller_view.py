import abc
from collections import deque
import copy
from enum import Enum, StrEnum
from itertools import product
import logging
import os
import textwrap
from tkinter import Button, Frame, Label, StringVar, Tk, font

from typing import Any, Sequence

from PIL import Image, ImageTk

from speller.session.flashing_strategy import FlashingListType
from speller.session.state_manager import IStateManager

from speller.settings import FilesSettings, StrategySettings, ViewSettings

class Color(StrEnum):
    DARK_GREY = '#D9D9D9'
    LIGHT_GRAY ='#E4E4E4'
    WHITE = '#FFFFFF'
    BLACK = '#000000'

    RED = '#FF0000'        


logger = logging.getLogger(__name__)


class SpellerView:
    def __init__(
        self,
        state_manager: IStateManager,
        strategy_settings: StrategySettings,
        files_settings: FilesSettings,
        view_settings: ViewSettings,
    ):
        self._state_manager = state_manager
        self._strategy_settings = strategy_settings
        self._files_settings = files_settings
        self._view_settings = view_settings
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
        self._window.protocol("WM_DELETE_WINDOW", self._shutdown)
        if self._view_settings.fullscreen:
            self._window.attributes("-fullscreen", True)
        else:
            self._window.geometry(f"{self._view_settings.screen_height}x{self._view_settings.screen_height}")

        self._main_frame = Frame(self._window, bg=Color.LIGHT_GRAY)
        self._main_frame.pack(fill='both', expand=True)

        self._speller_frame = Frame(self._main_frame, bg=Color.LIGHT_GRAY)
        self._speller_frame.place(relx=0.5, rely=0.5, anchor='center')

        self._speller_frame.rowconfigure(0, minsize=0.4*self._view_settings.screen_height)
        self._speller_frame.rowconfigure(1, minsize=0.6*self._view_settings.screen_height)
        self._speller_frame.columnconfigure(0, minsize=0.6*self._view_settings.screen_height)
        self._speller_frame.columnconfigure(1, minsize=0.4*self._view_settings.screen_height)

        self._frame_pad = 10
        self._field_pad = 20

        self._font = font.Font(family='Inconsolata', size=self._view_settings.font_size)

        self._input_field_text_max_width = int((0.6*self._view_settings.screen_height - 2*self._field_pad) / self._font.measure('a'))
        self._input_field_text = ''

        self._suggestions_field_text_max_width = int((0.4*self._view_settings.screen_height - 2*self._field_pad) / self._font.measure('a'))
        self._suggestions_field_list = []

        self._info_field_text_max_height = int((0.6*self._view_settings.screen_height - 2*self._field_pad) / self._font.metrics('linespace'))
        self._info_field_text_height = 0
        self._info_field_text = ''

        self._input_frame = Frame(self._speller_frame, bg=Color.WHITE)
        self._input_frame.grid(row=0, column=0, padx=(0, self._frame_pad), pady=(0, self._frame_pad), sticky="nsew")
        self._input_title = Label(self._input_frame, text='ВВОД', bg=Color.WHITE, fg=Color.BLACK, font=self._font)
        self._input_title.pack(fill='x')
        self._input_field = Label(self._input_frame, text='_', anchor='nw', justify='left', bg=Color.LIGHT_GRAY, fg=Color.BLACK, font=self._font)
        self._input_field.pack(fill='both', expand=True, padx=self._field_pad, pady=(0, self._field_pad))

        self._suggestions_frame = Frame(self._speller_frame, bg=Color.WHITE)
        self._suggestions_frame.grid(row=0, column=1, padx=(self._frame_pad, 0), pady=(0, self._frame_pad), sticky="nsew")
        self._suggestions_title = Label(self._suggestions_frame, text='ВАРИАНТЫ', bg=Color.WHITE, fg=Color.BLACK, font=self._font)
        self._suggestions_title.pack(fill='x')
        self._suggestions_field = Label(self._suggestions_frame, text='', anchor='nw', justify='left', bg=Color.LIGHT_GRAY, fg=Color.BLACK, font=self._font)
        self._suggestions_field.pack(fill='both', expand=True, padx=self._field_pad, pady=(0, self._field_pad))

        self._keyboard_frame = Frame(self._speller_frame, bg=Color.BLACK)
        self._keyboard_frame.grid(row=1, column=0, padx=(0, self._frame_pad), pady=(self._frame_pad, 0), sticky="nsew")
        self._initialize_keyboard()

        self._info_frame = Frame(self._speller_frame, bg=Color.WHITE)
        self._info_frame.grid(row=1, column=1, padx=(self._frame_pad, 0), pady=(self._frame_pad, 0), sticky="nsew")
        self._info_title = Label(self._info_frame, text='ИНФОРМАЦИЯ', bg=Color.WHITE, fg=Color.BLACK, font=self._font)
        self._info_title.pack(fill='x')
        self._info_field = Label(self._info_frame, text='', anchor='nw', justify='left', bg=Color.LIGHT_GRAY, fg=Color.BLACK, font=self._font)
        self._info_field.pack(fill='both', expand=True, padx=self._field_pad, pady=(0, self._field_pad))


        self._start_btn_text = StringVar()
        self._start_btn_text.set("Start")
        self._start_btn = Button(self._speller_frame, textvariable=self._start_btn_text, command=self._handle_start_btn)
        self._start_btn.grid(row=self._strategy_settings.keyboard_size + 1, column=0, columnspan=self._strategy_settings.keyboard_size)

    def _initialize_keyboard(self) -> None:
        pattern = self._files_settings.keyboard_items_pattern
        size = self._strategy_settings.keyboard_size
        self._keyboard_images: list[list[Any]] = [[None for j in range(size)] for i in range(size)] 
        self._keyboard_labels = copy.deepcopy(self._keyboard_images)

        for i in range(size):
            self._keyboard_frame.rowconfigure(i, weight=1)
            self._keyboard_frame.columnconfigure(i, weight=1)

        for i, j in product(range(size), range(size)):
            image = self._load_images(pattern.format(i, j), self._view_settings.keyboard_items_scale)
            self._keyboard_images[i][j] = image
            label = Label(self._keyboard_frame, image=image)
            self._keyboard_labels[i][j] = label
            label.grid(row=i, column=j)

        self._keyboard_flash_image = self._load_images(
            self._files_settings.keyboard_flash_item_filename, self._view_settings.keyboard_items_scale
        )
        self._keyboard_flashing_list = set()

    def _handle_start_btn(self):
        if self._start_btn_text.get() == 'Start':
            self._state_manager.start_session()
            self._start_btn_text.set('Stop')
        else:
            self._state_manager.finish_session()
            self._start_btn_text.set('Start')

    def _wrap_text(self, text: str, width: int) -> str:
        return '\n'.join(textwrap.wrap(text, width=width))

    def _update_input(self, full_text: str) -> None:
        if self._input_field_text != full_text:
            self._input_field_text = full_text
            wrapped_text = self._wrap_text(full_text + '_', self._input_field_text_max_width)
            self._input_field.config(text=wrapped_text)

    def _update_suggestions(self, suggestions: Sequence[str]) -> None:
        if self._suggestions_field_list != suggestions:
            self._suggestions_field_list = suggestions
            suggestions_text = '\n'.join(f'{i}) {suggestion}' for i, suggestion in enumerate(suggestions, start=1))
            self._suggestions_field.config(text=suggestions_text)

    def _update_info(self, info: str) -> None:
        if not self._info_field_text.endswith(info):
            if self._info_field_text:
                self._info_field_text = '\n'.join((self._info_field_text, info))
            else:
                self._info_field_text = info

            self._info_field_text_height += 1
            if self._info_field_text_height >= self._info_field_text_max_height:
                self._info_field_text = self._info_field_text.split('\n', 1)[1]
            self._info_field.config(text= self._info_field_text)

    def _update_keyboard(self, flashing_list: FlashingListType) -> None:
        flashing_list = set(flashing_list)
        for i, j in flashing_list - self._keyboard_flashing_list:
            self._keyboard_labels[i][j].configure(image=self._keyboard_flash_image)
        for i, j in self._keyboard_flashing_list - flashing_list:
            self._keyboard_labels[i][j].configure(image=self._keyboard_images[i][j])
        self._keyboard_flashing_list = flashing_list

    def run(self) -> None:
        self._update_loop()
        self._window.mainloop()

    def _update_loop(self):
        self._window.after(self._view_settings.update_interval_ms, self._update_loop)

        if self._state_manager.shutdown_event.is_set():
            self._finish()
            return
        
        state = self._state_manager.get_state()
        self._update_keyboard(state.flashing_list)

        self._update_input(state.full_text)
        self._update_suggestions(state.suggestions)
        self._update_info(state.info)


    def _finish(self) -> None:
        self._window.destroy()

    def _shutdown(self) -> None:
        self._state_manager.shutdown()
        self._finish()
