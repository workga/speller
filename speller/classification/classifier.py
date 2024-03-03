import abc
from random import random

from speller.data_aquisition.epoch_getter import EpochType


class IClassifier(abc.ABC):
    @abc.abstractmethod
    def classify(self, epoch: EpochType) -> float:  # returns bool or probability
        pass


class StubClassifier(IClassifier):
    def classify(self, epoch: EpochType) -> float:
        return random()
    

class Classifier(IClassifier):
    def classify(self, epoch: EpochType) -> float:
        return random()