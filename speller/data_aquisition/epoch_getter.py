import abc
import logging
from typing import Iterator, Sequence

from speller.data_aquisition.data_collector import DataSampleType, IDataCollector
from speller.data_aquisition.recorder import IRecorder
from speller.settings import StrategySettings


logger = logging.getLogger(__name__)


EpochType = Sequence[DataSampleType]


class IEpochGetter(abc.ABC):
    @abc.abstractmethod
    def get_epochs(self, number_of_epoches: int) -> Iterator[EpochType]:
        pass


class EpochGetter(IEpochGetter):
    def __init__(self, data_collector: IDataCollector, recorder: IRecorder, strategy_settings: StrategySettings):
        self._data_collector = data_collector
        self._strategy_settings = strategy_settings
        self._recorder = recorder

    def get_epochs(self, number_of_epoches: int) -> Iterator[EpochType]:
        logger.debug("EpochGetter: start yielding %s epochs", number_of_epoches)
        number_of_samples = self._strategy_settings.epoch_size_samples + (number_of_epoches - 1) * self._strategy_settings.epoch_interval_samples
        sample_generator = self._data_collector.collect(number_of_samples)
        
        current_epoch = []
        for _ in range(self._strategy_settings.epoch_size_samples):
            current_epoch.append(next(sample_generator))
        samples = current_epoch
        logger.debug("EpochGetter: yield epoch")
        yield current_epoch

        interval = self._strategy_settings.epoch_interval_samples
        for _ in range(number_of_epoches - 1):
            current_epoch = current_epoch[interval:]
            for _ in range(interval):
                current_epoch.append(next(sample_generator))
            samples.extend(current_epoch[-interval:])
            logger.debug("EpochGetter: yield epoch")
            yield current_epoch
        next(sample_generator, None)
        logger.debug("EpochGetter: stop yielding epochs")

        assert len(samples) == number_of_samples
        self._recorder.record_sequence(samples, [0]*len(samples))
