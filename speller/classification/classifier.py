import abc
import logging
import os
from pathlib import Path
import pickle
from random import random
from typing import Sequence

from sklearn.svm import SVC

from speller.data_aquisition.data_collector import DataSampleType
from speller.data_aquisition.epoch_getter import EpochType
from speller.settings import FilesSettings


logger = logging.getLogger(__name__)


class IClassifier(abc.ABC):
    @abc.abstractmethod
    def classify(self, epoch: EpochType) -> float:  # returns bool or probability
        pass


class StubClassifier(IClassifier):
    def classify(self, epoch: EpochType) -> float:
        logger.debug("StubClassifier: called classify()")
        return random()
    

class Classifier(IClassifier):
    _ORIGIN_UNITS_TO_VOLTS_FACTOR = 1e-6

    def __init__(self, files_settings: FilesSettings):
        self._files_settings = files_settings
        self._model = self._load_model()

    def _load_model(self) -> SVC:
        with open(
            os.path.join(self._files_settings.static_dir, self._files_settings.classifier_model_filename), "rb"
        ) as f:
            return pickle.load(f)

    def preprocess_data(raw: Sequence[DataSampleType]) -> Sequence[DataSampleType]:
        pass

    def classify(self, epoch: EpochType) -> float:
        logger.debug("Classifier: called classify()")
        return random()