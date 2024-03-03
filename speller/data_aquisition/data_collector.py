import abc
from contextlib import contextmanager
import logging
from threading import Event
import time
from typing import Iterator, Sequence, cast
from unapi import Unicorn


logger = logging.getLogger(__name__)


DataSampleType = Sequence[float]


class IDataCollector(abc.ABC):
    @abc.abstractmethod
    def collect(self, batch_size: int = 1) -> Iterator[DataSampleType]:
        pass

class StubDataCollector(IDataCollector):
    _SLEEP_S = 0.004
    _SAMPLES_COUNT = 4000
    def __init__(self, shutdown_event: Event):
        self._shutdown_event = shutdown_event

    def collect(self) -> Iterator[DataSampleType]:
        counter = 0
        while not self._shutdown_event.is_set():
            yield (counter,) * 8
            time.sleep(self._SLEEP_S)
            counter += 1
            if counter >= self._SAMPLES_COUNT:
                logger.info("StubDataCollector: _SAMPLES_COUNT exceeded")
                return

        logger.info(f"StubDataCollector: shutdown_event was set at {counter}")


class UnicornDataCollector(IDataCollector): 
    _NAMES_OF_EEG_CHANNELS = [f'EEG {i}' for i in range(1, 9)]
    _BATCH_SIZE = 50

    def __init__(self, shutdown_event: Event):
        self._shutdown_event = shutdown_event
        
        self.bci = Unicorn()

        devices, devices_cnt = cast(tuple[list[bytes], int], self.bci.getAvailableDevices())
        if devices_cnt == 0:
            raise RuntimeError("There are no available devices")
        serial = devices[0]

        self.handle_id = self.bci.openDevice(serial)
        self.config = self.bci.getConfiguration(self.handle_id)
        self.number_of_channels = len(self.config.channels)

        channel_name_to_index = {channel.name: channel.index for channel in self.config.channels}
        self.eeg_indexes = [channel_name_to_index[name] for name in self._NAMES_OF_EEG_CHANNELS]

    @contextmanager
    def _start_acquisition(self) -> Iterator[None]:
        self.bci.startAcquisition(self.handle_id)
        yield
        self.bci.stopAcquisition(self.handle_id)

    def _get_samples(self) -> Iterator[DataSampleType]:
        flatten_batch = self.bci.getData(self.handle_id, self._BATCH_SIZE)
        logger.info("UnicornDataCollector: got batch of data from bci")
        samples = (flatten_batch[i * self.number_of_channels, (i + 1) * self.number_of_channels] for i in range(self._BATCH_SIZE))
        for sample in samples:
            yield [sample[i] for i in self.eeg_indexes]
    
    def collect(self) -> Iterator[DataSampleType]:
        with self._start_acquisition():
            while not self._shutdown_event.is_set():
                yield from self._get_samples()
            logger.info('UnicornDataCollector: shutdown_event was set')

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
