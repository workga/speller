import abc
from collections import deque
from contextlib import contextmanager
import logging
import random
import time
from typing import Iterator, Sequence, cast
from speller.settings import StubDataCollectorSettings, UnicornDataCollectorSettings
from unapi import Unicorn


logger = logging.getLogger(__name__)


DataSampleType = Sequence[float]


class IDataCollector(abc.ABC):
    @abc.abstractmethod
    def collect(self, number_of_samples: int) -> Iterator[DataSampleType]:
        pass


class StubDataCollector(IDataCollector):
    def __init__(self, settings: StubDataCollectorSettings):
        self._settings = settings

    def collect(self, number_of_samples: int) -> Iterator[DataSampleType]:
        time.sleep(self._settings.ms_per_sample * number_of_samples / 1000)
        for _ in range(number_of_samples):
            yield [random.random()] * 8


class UnicornDataCollector(IDataCollector): 
    _NAMES_OF_EEG_CHANNELS = [f'EEG {i}' for i in range(1, 9)]

    def __init__(self, settings: UnicornDataCollectorSettings):
        self._settings = settings
        
        self.bci = Unicorn()

        devices, devices_cnt = cast(tuple[list[bytes], int], self.bci.getAvailableDevices())
        if devices_cnt == 0:
            raise RuntimeError("There are no available devices")
        serial = devices[0]

        self.handle_id = self.bci.openDevice(serial)
        self.config = self.bci.getConfiguration(self.handle_id)
        self.number_of_channels = len(self.config.channels)

        channel_name_to_index = {channel.name.decode(): channel.index for channel in self.config.channels}
        self.eeg_indexes = [channel_name_to_index[name] for name in self._NAMES_OF_EEG_CHANNELS]

    @contextmanager
    def _start_acquisition(self) -> Iterator[None]:
        self.bci.startAcquisition(self.handle_id)
        yield
        self.bci.stopAcquisition(self.handle_id)

    def _eeg_sample(self, sample: DataSampleType) -> DataSampleType:
        return [sample[i] for i in self.eeg_indexes]
    
    def collect(self, number_of_samples: int) -> Iterator[DataSampleType]:
        batch_size = self._settings.batch_size

        # t = Timer()
        with self._start_acquisition():
            flatten_batches = deque()
            for _ in range(number_of_samples // batch_size):
                flatten_batches.append(self.bci.getData(self.handle_id, batch_size))
            if size := number_of_samples % batch_size:
                flatten_batches.append(self.bci.getData(self.handle_id, size))

        # t.time('collecting')

        for flatten_batch in flatten_batches:
            for i in range(len(flatten_batch) // self.number_of_channels):
                sample = flatten_batch[i * self.number_of_channels: (i + 1) * self.number_of_channels]
                yield self._eeg_sample(sample)

    def __del__(self):
        self.bci.closeDevice(self.handle_id)


# s = Event()
# u = UnicornDataCollector(s)

# counter = 0
# for sample in u.collect():
#     print(sample)
#     counter += 1
#     if counter > 10:
#         s.set()
            
# u = SyncUnicornDataCollector(Event())
# t = time.monotonic()
# for s in u.collect(15000):
#     pass
# print(time.monotonic() - t)
            
# u = UnicornDataCollector(Event())
# for s in u.collect():
#     print(s)
