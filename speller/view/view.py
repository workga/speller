import abc
import configparser
import glob
import os
from queue import Queue
from tkinter import StringVar, Tk
from tkinter.ttk import Button, Frame, Label
from typing import Iterator

from PIL import Image, ImageTk


from speller.session.flashing_strategy import FlashingListType, IFlashingStrategy, SquareRowColumnFlashingStrategy
from speller.session.state_manager import IStateManager
from speller_event import SpellerEventType



class ConfigParams:
    def __init__(self):
        self.config_parser = configparser.RawConfigParser()
        self.config_parser.read("./conf_files/default.cfg")
        section = "Parameters"

        self.number_of_rows = self.config_parser.getint(section, "number_of_rows")
        self.number_of_columns = self.config_parser.getint(section, "number_of_columns")
        self.flash_duration = self.config_parser.getint(section, "flash_duration")
        self.break_duration = self.config_parser.getint(section, "break_duration")
        self.imagesize = self.config_parser.getint(section, "imagesize")
        self.images_folder_path = "./number_images"
        self.flash_image_path = "./flash_images/einstein.jpg"


class IView(abc.ABC):
    @abc.abstractmethod
    def run(self) -> None:
        pass

    # @abc.abstractmethod
    # def start(self, flashing_strategy: IFlashingStrategy) -> None:
    #     pass


class SpellerView(IView):
    _IMAGES_DIR = "./static"
    _IMAGES_NAMES = (
        "background",
        "input",
        "suggestions",
        "keyboard",
        "info",
    )
    _SCALING_FACTOR = 0.8
    _PADDING = 5

    # def __init__(self, state_manager: IStateManager, event_queue: Queue):
    #     self._state_manager = state_manager
    #     self._event_queue = event_queue

    def __init__(self) -> None:
        self._initialize_window()

    def _load_images(self) -> dict[str, ImageTk.PhotoImage]:
        images = {}
        for image_name in self._IMAGES_NAMES:
            image = Image.open(os.path.join(self._IMAGES_DIR, image_name + ".png"))
            image = image.resize(
                (
                    int(image.width * self._SCALING_FACTOR),
                    int(image.height * self._SCALING_FACTOR),
                ),
                Image.ANTIALIAS,
            )
            images[image_name] = ImageTk.PhotoImage(image)
        return images

    def _initialize_window(self) -> None:
        self._window = Tk()
        self._window.protocol("WM_DELETE_WINDOW", self._finish)

        self._images = self._load_images()

        self._main_frame = Frame(self._window)
        self._main_frame.grid(
            row=0,
            column=0,
            rowspan=self._images["background"].width(),
            columnspan=self._images["background"].height(),
        )

        markup = (
            ("input", 0, 0),
            ("suggestions", 0, self._images["input"].width()),
            ("keyboard", self._images["keyboard"].height(), 0),
            ("info", self._images["info"].height(), self._images["input"].width()),
        )
        self._labels = {}        
        for name, row, column in markup:
            label = Label(self._main_frame, image=self._images[name])
            label.grid(
                row=row,
                column=column,
                rowspan=self._images[name].width(),
                columnspan=self._images[name].height(),
                padx=self._PADDING,
                pady=self._PADDING,
            )
            self._labels[name] = label


    def run(self) -> None:
        self._window.mainloop()

    
    def _finish(self) -> None:
        self._window.destroy()
        # self._event_queue.put(SpellerEventType.FINISH)


v = SpellerView()
v.run()
        
    #     self._config = ConfigParams()
    #     self._running = 0

    #     self.image_labels = []
    #     self.sequence_number = 0
    #     self.lsl_output = None
    #     self.usable_images = []
    #     self.flash_sequence = []

    #     self.image_frame = Frame(self._window)
    #     self.image_frame.grid(
    #         row=0, column=0, rowspan=self._config.number_of_rows, columnspan=self._config.number_of_columns
    #     )

    #     self.start_btn_text = StringVar()
    #     self.start_btn_text.set("Start")
    #     self.start_btn = Button(self._window, textvariable=self.start_btn_text, command=self.start)
    #     self.start_btn.grid(row=self._config.number_of_rows + 1, column=self._config.number_of_columns - 1)

    #     self.pause_btn = Button(self._window, text="Pause", command=self.pause)
    #     self.pause_btn.grid(row=self._config.number_of_rows + 1, column=self._config.number_of_columns - 2)
    #     self.pause_btn.configure(state="disabled")

    #     self.close_btn = Button(self._window, text="Close", command=self.close_window)
    #     self.close_btn.grid(row=self._config.number_of_rows + 1, column=0)


    #     self.show_images()
    #     self._flashing_strategy = SquareRowColumnFlashingStrategy(
    #         size=min(self._config.number_of_rows, self._config.number_of_columns)
    #     )

    # def open_images(self):
    #     self.usable_images = []
    #     image_paths = glob.glob(os.path.join(self._config.images_folder_path, "*.jpg"))
    #     png_images = glob.glob(os.path.join(self._config.images_folder_path, "*.png"))
    #     for png_image in png_images:
    #         image_paths.append(png_image)
    #     min_number_of_images = self._config.number_of_columns * self._config.number_of_rows
    #     if len(image_paths) < min_number_of_images:
    #         return

    #     # Convert and resize images
    #     for image_path in image_paths:
    #         image = Image.open(image_path)
    #         resized = image.resize((self._config.imagesize, self._config.imagesize), Image.ANTIALIAS)
    #         Tkimage = ImageTk.PhotoImage(resized)
    #         self.usable_images.append(Tkimage)

    #     flash_img = Image.open(self._config.flash_image_path)
    #     flash_img_res = flash_img.resize((self._config.imagesize, self._config.imagesize), Image.ANTIALIAS)
    #     self.flash_image = ImageTk.PhotoImage(flash_img_res)

    # def show_images(self):
    #     self.open_images()

    #     if self.usable_images == []:
    #         return

    #     num_rows = self._config.number_of_rows
    #     num_cols = self._config.number_of_columns

    #     # Arrange images
    #     for r in range(0, num_rows):
    #         for c in range(0, num_cols):
    #             current_image = self.usable_images[r * num_cols + c]
    #             label = Label(self.image_frame, image=current_image)
    #             label.image = current_image
    #             label.grid(row=r, column=c)
    #             self.image_labels.append(label)

    # def change_image(self, label, img):
    #     label.configure(image=img)
    #     label.image = img


    # def start(self):
    #     self._running = 1
    #     self.start_flashing()
    #     self.start_btn.configure(state="disabled")
    #     self.pause_btn.configure(state="normal")

    # def pause(self):
    #     self._running = 0
    #     self.start_btn_text.set("Resume")
    #     self.start_btn.configure(state="normal")
    #     self.pause_btn.configure(state="disabled")

    # def start_flashing(self):
    #     flashing_list_generator = self._flashing_strategy.flash()
    #     self._flashing_loop(flashing_list_generator)

    # def _flashing_loop(self, flashing_list_generator: Iterator[FlashingListType]):
    #     if not self._running:
    #         return
    #     flashing_list = next(flashing_list_generator)
    #     self._flash(flashing_list)
    #     self._window.after(self._config.flash_duration, self._unflash, flashing_list)
    #     self._window.after(self._config.flash_duration + self._config.break_duration, self._flashing_loop, flashing_list_generator)

    # def _pos_to_image_index(self, i: int, j: int) -> int:
    #     return i * self._config.number_of_columns + j

    # def _flash(self, flashing_list: FlashingListType):
    #     for i, j in flashing_list:
    #         image_index = self._pos_to_image_index(i, j)
    #         self.change_image(self.image_labels[image_index], self.flash_image)

    # def _unflash(self, flashing_list: FlashingListType):
    #     for i, j in flashing_list:
    #         image_index = self._pos_to_image_index(i, j)
    #         self.change_image(self.image_labels[image_index], self.usable_images[image_index])
