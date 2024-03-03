import abc
from queue import Queue

from speller.data_aquisition.data_collector import IDataCollector


class IDataStreamer(abc.ABC):
    @abc.abstractmethod
    def stream(self) -> None:
        pass


class DataStreamer(IDataStreamer):
    def __init__(self, data_collector: IDataCollector, data_queue: Queue):
        self._data_collector = data_collector
        self._data_queue = data_queue
    
    def stream(self) -> None:
        for sample in self._data_collector.collect():
            self._data_queue.put(sample)
