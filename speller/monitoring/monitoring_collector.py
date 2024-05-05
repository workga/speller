import abc
from collections import deque
from threading import Event
from threading import Thread
from typing import Sequence

from speller.data_aquisition.data_collector import DataSampleType, IDataCollector
from speller.settings import MonitoringSettings

class IMonitoringCollector(abc.ABC):
    @abc.abstractmethod
    def run(self, accumulator_size: int) -> None:
        pass

    @abc.abstractmethod
    def get_data(self) -> Sequence[DataSampleType]:
        pass

class MonitoringCollector:
    def __init__(self, data_collector: IDataCollector, settings: MonitoringSettings):
        self._data_collector = data_collector
        self._settings = settings

    def run(self, accumulator_size: int, shutdown_event: Event) -> None:
        self._accumulator = deque([[0] * 8] * accumulator_size, maxlen=accumulator_size)
        self._collector_thread = Thread(target=self._collect, args=(shutdown_event,))
        self._collector_thread.start()

    def _collect(self, shutdown_event):
        for samples in self._data_collector.collect_continuously(self._settings.collect_interval_samples, shutdown_event):
            self._accumulator.extend(samples)
        

    def get_data(self) -> Sequence[DataSampleType]:
        return self._accumulator
