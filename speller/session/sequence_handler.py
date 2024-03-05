import abc
import logging
from threading import Thread
import time
from speller.classification.classifier import IClassifier
from speller.data_aquisition.epoch_getter import IEpochGetter
from speller.session.flashing_strategy import FlashingSequenceType, IFlashingStrategy, ItemPositionType
from speller.session.state_manager import IStateManager
from speller.config import ConfigParams


logger = logging.getLogger(__name__)


class ISequenceHandler(abc.ABC):
    @abc.abstractmethod
    def handle_sequence(self) -> ItemPositionType:
        pass


class SequenceHandler(ISequenceHandler):
    def __init__(self, epoch_getter: IEpochGetter, classifier: IClassifier, flashing_strategy: IFlashingStrategy, state_manager: IStateManager):
        self._config = ConfigParams()
        self._epoch_getter = epoch_getter
        self._classifier = classifier
        self._flashing_strategy = flashing_strategy
        self._state_manager = state_manager
        self._task_thread: Thread | None = None

    def handle_sequence(self) -> ItemPositionType:
        logger.info("SequnceHandler: start handling sequence")
        flashing_sequence = self._flashing_strategy.get_flashing_sequence()
        logger.info("SequnceHandler: got flashing sequence")
        epoch_generator = self._epoch_getter.get_epochs(len(flashing_sequence))
        
        self._run_state_updater(flashing_sequence)

        probabilities = [self._classifier.classify(epoch) for epoch in epoch_generator]
        if len(probabilities) < len(flashing_sequence):
            raise RuntimeError("SequnceHandler: run out of epochs")

        logger.info("SequnceHandler: finishing handling sequence")
        return self._flashing_strategy.predict_item_position(flashing_sequence, probabilities)
    
    def _run_state_updater(self, flashing_sequence: FlashingSequenceType):
        def task():
            logger.info("SequnceHandler: running state updater")
            time.sleep(self._config.epoch_baseline / 1000)
            for flashing_list in flashing_sequence:
                self._state_manager.set_flashing_list(flashing_list)
                time.sleep(self._config.flash_duration / 1000)
                self._state_manager.reset_flashing_list()
                time.sleep(self._config.break_duration / 1000)

        if self._task_thread is not None:
            self._task_thread.join()
        
        self._task_thread = Thread(target=task)
        self._task_thread.start()
            




        