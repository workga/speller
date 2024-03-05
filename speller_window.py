import abc
import configparser
import glob
import os
from tkinter import StringVar, Tk
from tkinter.ttk import Button, Frame, Label
from typing import Iterator

from PIL import Image, ImageTk


from speller.session.flashing_strategy import FlashingListType, SquareRowColumnFlashingStrategy


class ISpellerWindow(abc.ABC):
    @abc.abstractmethod
    def initialize(self, window: Tk) -> None:
        pass



# class ConfigParams:
#     def __init__(self):
#         self.config_parser = configparser.RawConfigParser()
#         self.config_parser.read("./conf_files/default.cfg")
#         section = "Parameters"

#         self.number_of_rows = self.config_parser.getint(section, "number_of_rows")
#         self.number_of_columns = self.config_parser.getint(section, "number_of_columns")
#         self.flash_duration = self.config_parser.getint(section, "flash_duration")
#         self.break_duration = self.config_parser.getint(section, "break_duration")
#         self.imagesize = self.config_parser.getint(section, "imagesize")
#         self.images_folder_path = "./number_images"
#         self.flash_image_path = "./flash_images/einstein.jpg"
        
#         self.epoch_size = self.config_parser.getint(section, "epoch_size")
#         self.epoch_interval = self.config_parser.getint(section, "epoch_interval")

#         self.update_interval = 10


class P300Window:
    def __init__(self, master: Tk, config: ConfigParams):
        self.master = master
        self.config = config
        
        self.master.protocol("WM_DELETE_WINDOW", self.close_window)

        self.running = 0

        self.image_labels = []
        self.sequence_number = 0
        self.lsl_output = None
        self.usable_images = []
        self.flash_sequence = []

        self.image_frame = Frame(self.master)
        self.image_frame.grid(
            row=0, column=0, rowspan=self.config.number_of_rows, columnspan=self.config.number_of_columns
        )

        self.start_btn_text = StringVar()
        self.start_btn_text.set("Start")
        self.start_btn = Button(self.master, textvariable=self.start_btn_text, command=self.start)
        self.start_btn.grid(row=self.config.number_of_rows + 1, column=self.config.number_of_columns - 1)

        self.pause_btn = Button(self.master, text="Pause", command=self.pause)
        self.pause_btn.grid(row=self.config.number_of_rows + 1, column=self.config.number_of_columns - 2)
        self.pause_btn.configure(state="disabled")

        self.close_btn = Button(self.master, text="Close", command=self.close_window)
        self.close_btn.grid(row=self.config.number_of_rows + 1, column=0)


        self.show_images()
        self._flashing_strategy = SquareRowColumnFlashingStrategy(
            size=min(self.config.number_of_rows, self.config.number_of_columns)
        )

    def open_images(self):
        self.usable_images = []
        image_paths = glob.glob(os.path.join(self.config.images_folder_path, "*.jpg"))
        png_images = glob.glob(os.path.join(self.config.images_folder_path, "*.png"))
        for png_image in png_images:
            image_paths.append(png_image)
        min_number_of_images = self.config.number_of_columns * self.config.number_of_rows
        if len(image_paths) < min_number_of_images:
            return

        # Convert and resize images
        for image_path in image_paths:
            image = Image.open(image_path)
            resized = image.resize((self.config.imagesize, self.config.imagesize), Image.ANTIALIAS)
            Tkimage = ImageTk.PhotoImage(resized)
            self.usable_images.append(Tkimage)

        flash_img = Image.open(self.config.flash_image_path)
        flash_img_res = flash_img.resize((self.config.imagesize, self.config.imagesize), Image.ANTIALIAS)
        self.flash_image = ImageTk.PhotoImage(flash_img_res)

    def show_images(self):
        self.open_images()

        if self.usable_images == []:
            return

        num_rows = self.config.number_of_rows
        num_cols = self.config.number_of_columns

        # Arrange images
        for r in range(0, num_rows):
            for c in range(0, num_cols):
                current_image = self.usable_images[r * num_cols + c]
                label = Label(self.image_frame, image=current_image)
                label.image = current_image
                label.grid(row=r, column=c)
                self.image_labels.append(label)

    def change_image(self, label, img):
        label.configure(image=img)
        label.image = img


    def start(self):
        self.running = 1
        self.start_flashing()
        self.start_btn.configure(state="disabled")
        self.pause_btn.configure(state="normal")

    def pause(self):
        self.running = 0
        self.start_btn_text.set("Resume")
        self.start_btn.configure(state="normal")
        self.pause_btn.configure(state="disabled")

    def start_flashing(self):
        flashing_list_generator = self._flashing_strategy.flash()
        self._flashing_loop(flashing_list_generator)

    def _flashing_loop(self, flashing_list_generator: Iterator[FlashingListType]):
        if not self.running:
            return
        flashing_list = next(flashing_list_generator)
        self._flash(flashing_list)
        self.master.after(self.config.flash_duration, self._unflash, flashing_list)
        self.master.after(self.config.flash_duration + self.config.break_duration, self._flashing_loop, flashing_list_generator)

    def _pos_to_image_index(self, i: int, j: int) -> int:
        return i * self.config.number_of_columns + j

    def _flash(self, flashing_list: FlashingListType):
        for i, j in flashing_list:
            image_index = self._pos_to_image_index(i, j)
            self.change_image(self.image_labels[image_index], self.flash_image)

    def _unflash(self, flashing_list: FlashingListType):
        for i, j in flashing_list:
            image_index = self._pos_to_image_index(i, j)
            self.change_image(self.image_labels[image_index], self.usable_images[image_index])

    def close_window(self):
        self.master.destroy()


def main():
    from tkinter import Tk

    root = Tk()

    P300Window(root, ConfigParams())
    root.mainloop()

if __name__ == "__main__":
    main()