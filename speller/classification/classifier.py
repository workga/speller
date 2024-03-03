import abc
import logging
from random import random

from speller.data_aquisition.epoch_getter import EpochType


logger = logging.getLogger(__name__)


class IClassifier(abc.ABC):
    @abc.abstractmethod
    def classify(self, epoch: EpochType) -> float:  # returns bool or probability
        pass


class StubClassifier(IClassifier):
    def classify(self, epoch: EpochType) -> float:
        logger.info("StubClassifier: called classify()")
        return random()
    

class Classifier(IClassifier):
    def classify(self, epoch: EpochType) -> float:
        logger.info("Classifier: called classify()")
        return random()