import abc
import logging
from multiprocessing.pool import ThreadPool
import time
from speller.classification.classifier import IClassifier
from speller.data_aquisition.epoch_getter import IEpochGetter
from speller.session.entity import FlashingSequenceType, ItemPositionType
from speller.session.flashing_strategy import IFlashingStrategy
from speller.session.state_manager import IStateManager
from speller.settings import StrategySettings
from speller.utils import Timer


logger = logging.getLogger(__name__)


class ISequenceHandler(abc.ABC):
    @abc.abstractmethod
    def handle_sequence(self) -> ItemPositionType:
        pass


class SequenceHandler(ISequenceHandler):
    def __init__(
        self,
        epoch_getter: IEpochGetter,
        classifier: IClassifier,
        flashing_strategy: IFlashingStrategy,
        state_manager: IStateManager,
        strategy_settings: StrategySettings,
    ):
        self._epoch_getter = epoch_getter
        self._classifier = classifier
        self._flashing_strategy = flashing_strategy
        self._state_manager = state_manager
        self._strategy_settings = strategy_settings

        self._future = None
        self._pool = ThreadPool(processes=1)

    def handle_sequence(self) -> ItemPositionType:
        logger.info("SequnceHandler: start handling sequence")
        flashing_sequence = self._flashing_strategy.get_flashing_sequence(self._state_manager.session_reps)
        logger.debug("SequnceHandler: got flashing sequence")
        epoch_generator = self._epoch_getter.get_epochs(len(flashing_sequence))
        
        self._run_state_updater(flashing_sequence, time.monotonic())

        probabilities = [self._classifier.classify(epoch) for epoch in epoch_generator]

        if len(probabilities) < len(flashing_sequence):
            raise RuntimeError("SequnceHandler: run out of epochs")

        logger.info("SequnceHandler: finishing handling sequence")
        return self._flashing_strategy.predict_item_position(flashing_sequence, probabilities)
    
    def _run_state_updater(self, flashing_sequence: FlashingSequenceType, start_time: float):
        if self._future:
            self._future.wait()
        self._future = self._pool.apply_async(self._task, (flashing_sequence, start_time))

    def _task(self, flashing_sequence: FlashingSequenceType, start_time: float):
        logger.debug("SequnceHandler: running state updater")
        # t = Timer()

        next_time = start_time + self._strategy_settings.epoch_baseline_s
        time.sleep(max(0, next_time - time.monotonic()))
        for flashing_list in flashing_sequence:
            self._state_manager.set_flashing_list(flashing_list)
            next_time += self._strategy_settings.flash_duration_s
            time.sleep(max(0, next_time - time.monotonic()))

            self._state_manager.reset_flashing_list()
            next_time += self._strategy_settings.break_duration_s
            time.sleep(max(0, next_time - time.monotonic()))
        
        # t.time('flashing')
