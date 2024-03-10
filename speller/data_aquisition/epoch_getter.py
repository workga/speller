import abc
import logging
from queue import Empty, Queue
from typing import Iterator, Sequence

from speller.data_aquisition.data_collector import DataSampleType, IDataCollector, ISyncDataCollector
from speller.data_aquisition.data_streamer import IDataStreamer
from speller.config import ConfigParams


logger = logging.getLogger(__name__)


EpochType = Sequence[DataSampleType]


class IEpochGetter(abc.ABC):
    @abc.abstractmethod
    def get_epochs(self, number_of_epoches: int) -> Iterator[EpochType]:
        pass


class QueueEpochGetter(IEpochGetter):
    _QUEUE_TIMEOUT = 1

    def __init__(self, data_queue: Queue, epoch_size: int, epoch_interval: int):
        self._data_queue = data_queue
        self._epoch_size = epoch_size
        self._epoch_interval = epoch_interval

    def get_epochs(self, number_of_epoches: int) -> Iterator[EpochType]:
        logger.debug("EpochGetter: start yielding epochs")
        try:
            current_epoch = []
            for _ in range(self._epoch_size):
                current_epoch.append(self._data_queue.get(timeout=self._QUEUE_TIMEOUT))
            logger.debug("EpochGetter: yield epoch")
            yield current_epoch

            for _ in range(number_of_epoches - 1):
                current_epoch = current_epoch[self._epoch_interval:]
                for _ in range(self._epoch_interval):
                    current_epoch.append(self._data_queue.get(timeout=self._QUEUE_TIMEOUT))
                logger.debug("EpochGetter: yield epoch")
                yield current_epoch
            logger.debug("EpochGetter: stop yielding epochs")
        except Empty:
            logger.debug("EpochGetter: queue is empty, got timeout")
            return
  
class EpochGetter(IEpochGetter):
    def __init__(self, data_collector: ISyncDataCollector):
        self._config = ConfigParams()
        self._data_collector = data_collector

    def get_epochs(self, number_of_epoches: int) -> Iterator[EpochType]:
        logger.debug("EpochGetter: start yielding %s epochs", number_of_epoches)
        number_of_samples = self._config.epoch_size + (number_of_epoches - 1) * self._config.epoch_interval
        sample_generator = self._data_collector.collect(number_of_samples)
        
        current_epoch = []
        for _ in range(self._config.epoch_size):
            current_epoch.append(next(sample_generator))
        logger.debug("EpochGetter: yield epoch")
        yield current_epoch

        for _ in range(number_of_epoches - 1):
            current_epoch = current_epoch[self._config.epoch_interval:]
            for _ in range(self._config.epoch_interval):
                current_epoch.append(next(sample_generator))
            logger.debug("EpochGetter: yield epoch")
            yield current_epoch
        next(sample_generator, None)
        logger.debug("EpochGetter: stop yielding epochs")


# q = Queue()
# for i in range(10):
#     q.put((i, i, i, i))

# d = DataEpochGetter(q, 4, 1)
# for epoch in d.get_epochs():
#     for sample in epoch:
#         print(sample)
#     print('\n')