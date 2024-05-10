

from dataclasses import dataclass
from matplotlib import pyplot as plt
import mne
import numpy as np
from sklearn import metrics
from sklearn.base import ClassifierMixin
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

from preprocessing.settings import ModelSettings
from speller.data_aquisition.data_collector import DataSampleType


@dataclass
class Data:
    X: list[DataSampleType]
    y: list[int]


@dataclass
class Dataset:
    train: Data
    test: Data


class Model:
    def __init__(self, settings: ModelSettings):
        self._settings = settings

    def _get_epochs_subset(self, epochs: mne.Epochs) -> mne.Epochs:
        upper_bound = int(len(epochs) * self._settings.data_proportion)
        return epochs[:upper_bound]

    def _get_dataset_from_epochs(self, epochs: mne.Epochs) -> Dataset:        
        epochs_list = [self._get_epochs_subset(epochs[k]) for k in epochs.event_id]
        X = [e.get_data(picks='eeg') for e in epochs_list]
        y = [k * np.ones(len(this_X)) for k, this_X in enumerate(X)]
        X = np.concatenate(X)
        X = X.reshape(len(X), -1)
        y = np.concatenate(y)

        # тут хотелось бы для обучающей иметь поровну разных стимулов, а для тестовой не поровну
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, stratify=y, test_size=self._settings.test_proportion, random_state=self._settings.random_seed
        )

        return Dataset(train=Data(X=X_train, y=y_train), test=Data(X=X_test, y=y_test))

    def _apply_scaler(self, data: Dataset) -> StandardScaler:
        scaler = StandardScaler().fit(data.train.X)
        data.train.X = scaler.transform(data.train.X)
        data.test.X = scaler.transform(data.test.X)

        return scaler
    
    def _fit_classifier(self, data: Dataset) -> ClassifierMixin:
        clf = SVC(C=self._settings.classifier__C, kernel=self._settings.classifier__kernel)

        print("Start fitting...")
        clf.fit(data.train.X, data.train.y)
        print("Finished fitting")

        return clf
    
    def _print_scores(self, y_test: list[int], y_pred: list[int]) -> None:
        print("Accuracy:", metrics.accuracy_score(y_test, y_pred))
        print("Precision:", metrics.precision_score(y_test, y_pred))
        print("Recall:", metrics.recall_score(y_test, y_pred))
        print("F1-score:", metrics.f1_score(y_test, y_pred))

        print(metrics.classification_report(y_test, y_pred))
        print(metrics.confusion_matrix(y_test, y_pred, labels=[0, 1], normalize='true'))

    def _report(self, clf: ClassifierMixin, data: Dataset) -> None:
        y_test = list(map(int, data.test.y))
        y_pred = list(map(int, clf.predict(data.test.X)))
        
        self._print_scores(y_test, y_pred)

        metrics.ConfusionMatrixDisplay.from_predictions(
            y_test, y_pred, display_labels=['non-target', 'target'], labels=[0, 1], normalize='true', cmap='gist_yarg'
        )
        plt.show()
    
    def fit(self, epochs: mne.Epochs) -> None:
        if self._settings.downsample_freq:
            epochs.resample(self._settings.downsample_freq)
        data = self._get_dataset_from_epochs(epochs)
        scaler = self._apply_scaler(data)

        clf = self._fit_classifier(data)

        self._report(clf, data)
    
    def save(self) -> None:
        pass

    def load(self) -> None:
        pass
