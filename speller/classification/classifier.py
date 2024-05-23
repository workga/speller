import abc
import logging
import os
from pathlib import Path
import pickle
from random import random
from typing import Sequence

import numpy as np
from sklearn.svm import SVC

from preprocessing.files import find_model_file
from preprocessing.model import ClassifierModel, Model
from speller.data_aquisition.data_collector import DataSampleType
from speller.data_aquisition.epoch_getter import EpochType
from speller.settings import FilesSettings


logger = logging.getLogger(__name__)


class IClassifier(abc.ABC):
    @abc.abstractmethod
    def classify(self, epochs: np.ndarray) -> list[float]:  # returns bools or probabilities
        pass


class StubClassifier(IClassifier):
    def classify(self, epochs: np.ndarray) -> list[float]:
        logger.debug("StubClassifier: called classify()")
        return [1 if random() >= 0.5 else 0 for _ in epochs]
    

class Classifier(IClassifier):
    def __init__(self, files_settings: FilesSettings, model: Model):
        self._files_settings = files_settings
        self._clf_model = model.load(find_model_file(self._files_settings))

    def classify(self, epochs: np.ndarray) -> list[float]:
        logger.debug("Classifier: called classify()")
        return self._clf_model.predict(epochs)