import abc
from queue import Empty, Queue
from typing import Iterator, Sequence

from speller.data_aquisition.data_collector import DataSampleType

EpochType = Sequence[DataSampleType]


class IEpochGetter(abc.ABC):
    @abc.abstractmethod
    def get_epochs(self, number_of_epoches: int) -> Iterator[EpochType]:
        pass


class EpochGetter(IEpochGetter):
    _QUEUE_TIMEOUT = 1

    def __init__(self, data_queue: Queue, epoch_size: int, epoch_interval: int):
        self._data_queue = data_queue
        self._epoch_size = epoch_size
        self._epoch_interval = epoch_interval

    def get_epochs(self, number_of_epoches: int) -> Iterator[EpochType]:
        try:
            current_epoch = []
            for _ in range(self._epoch_size):
                current_epoch.append(self._data_queue.get())
            yield current_epoch

            for _ in range(number_of_epoches - 1):
                current_epoch = current_epoch[self._epoch_interval:]
                for _ in range(self._epoch_interval):
                    current_epoch.append(self._data_queue.get(timeout=self._QUEUE_TIMEOUT))
                yield current_epoch
        except Empty:
            return


# q = Queue()
# for i in range(10):
#     q.put((i, i, i, i))

# d = DataEpochGetter(q, 4, 1)
# for epoch in d.get_epochs():
#     for sample in epoch:
#         print(sample)
#     print('\n')