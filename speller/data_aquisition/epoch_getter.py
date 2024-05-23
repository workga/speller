import abc
from itertools import islice
import logging
from typing import Iterable, Sequence

from preprocessing.epoch_collector import EpochCollector
from preprocessing.preprocessor import Preprocessor
from speller.data_aquisition.data_collector import DataSampleType, IDataCollector
from speller.data_aquisition.recorder import IRecorder
from speller.settings import StrategySettings


logger = logging.getLogger(__name__)


EpochType = Sequence[DataSampleType]


class IEpochGetter(abc.ABC):
    @abc.abstractmethod
    def get_epochs(self, number_of_epoches: int) -> Iterable[EpochType]:
        pass


class EpochGetter(IEpochGetter):
    def __init__(
        self,
        data_collector: IDataCollector,
        recorder: IRecorder,
        strategy_settings: StrategySettings,
        preprocessor: Preprocessor,
        epoch_collector: EpochCollector,
    ):
        self._data_collector = data_collector
        self._strategy_settings = strategy_settings
        self._recorder = recorder
        self._preprocessor = preprocessor
        self._epoch_collector = epoch_collector

    def get_epochs(self, number_of_epoches: int) -> Iterable[EpochType]:
        logger.debug("EpochGetter: start collecting epochs", number_of_epoches)
        number_of_samples = self._strategy_settings.get_number_of_samples(number_of_epoches)

        collector = self._data_collector.collect(number_of_samples)

        samples = list(islice(collector, self._strategy_settings.wait_samples, None))  # block until all samples are received
        self._recorder.record_samples(samples)

        samples = self._preprocessor.preprocess_samples(samples)

        epochs = []
        start = 0
        stop = self._strategy_settings.epoch_size_samples
        for _ in range(number_of_epoches):
            epochs.append(samples[start:stop])
            start += self._strategy_settings.epoch_interval_samples
            stop += self._strategy_settings.epoch_interval_samples
        
        epochs = self._epoch_collector.preprocess_epochs(epochs)
        logger.debug("EpochGetter: stop collecting epochs")
        return epochs
