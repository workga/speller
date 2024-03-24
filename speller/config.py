import configparser


class ConfigParams:
    def __init__(self):
        self.config_parser = configparser.RawConfigParser()
        self.config_parser.read("./default.cfg")
        section = "Parameters"

        self.flash_duration = self.config_parser.getint(section, "flash_duration")
        self.break_duration = self.config_parser.getint(section, "break_duration")

        self.epoch_size = self.config_parser.getint(section, "epoch_size")
        self.epoch_baseline = self.config_parser.getint(section, "epoch_baseline")
        self.epoch_interval = self.config_parser.getint(section, "epoch_interval")

        self.view_update_interval = 1