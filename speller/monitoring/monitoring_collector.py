import abc
from collections import deque
from threading import Thread
import time
from typing import Sequence, cast
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
import glob

from speller.data_aquisition.data_collector import DataSampleType, IDataCollector
from speller.settings import FilesSettings, MonitoringSettings

class IMonitoringCollector(abc.ABC):
    @abc.abstractmethod
    def run(self, accumulator_size: int) -> None:
        pass

    @abc.abstractmethod
    def get_data(self) -> Sequence[Sequence[DataSampleType]]:
        pass

class MonitoringCollector:
    def __init__(self, data_collector: IDataCollector, settings: MonitoringSettings):
        self._data_collector = data_collector
        self._settings = settings

    def run(self, accumulator_size: int) -> None:
        self._accumulator = deque([[0] * 8] * accumulator_size, maxlen=accumulator_size)
        self._daemon = Thread(target=self._collect, daemon=True)
        self._daemon.start()

    def _collect(self):
        data_iterator = self._data_collector.collect_continuously(self._settings.collect_interval_samples)
        while True:
            self._accumulator.extend(next(data_iterator))

    def get_data(self) -> Sequence[Sequence[DataSampleType]]:
        return self._accumulator
