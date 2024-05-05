import abc
from typing import cast
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
import pandas as pd
import glob

from speller.data_aquisition.data_collector import DataSampleType, IDataCollector
from speller.settings import FilesSettings, MonitoringSettings

class IMonitoring(abc.ABC):
    @abc.abstractmethod
    def run(self) -> None:
        pass

class StubMonitoring:
    _HEADERS = [f'EEG {i}' for i in range(1, 9)]

    def __init__(self, settings: MonitoringSettings, files_settings: FilesSettings):
        self._settings = settings
        self._files_settings = files_settings
        self._fig, self._subplots = plt.subplots(8, 2)
        
        self._xs = list(range(-self._settings.plot_length_samples, 0))
        self._ys = [[0] * 8 ] * self._settings.plot_length_samples
        
        self._qxs = list(range(-10, 0))
        self._qys = [[0] * 8] * 10

        self._init_data_iterator()

    def _init_data_iterator(self):
        latest_filename = max(glob.glob(str(self._files_settings.records_dir / '*')))
        self._data_iter = pd.read_csv(latest_filename, header=0)[self._HEADERS].iloc[250:].iterrows()


    def _get_samples(self) -> list[DataSampleType]:
        count = 250 * 1000 // self._settings.update_interval_ms
        samples = []
        for _ in range(count):
            samples.append(next(self._data_iter)[1])
        return samples
    
    def _get_channels_qualities(self, samples: list[DataSampleType]) -> list[float]:
        array = np.array(samples)
        sd = np.std((array - array.mean(axis=0)), axis=0)

        return sd.tolist()

    def _update(self, *args) -> None:
        samples = self._get_samples()
        self._ys = self._ys[len(samples) - self._settings.plot_length_samples:] + samples
        self._qys = self._qys[1:] + [self._get_channels_qualities(self._ys[-249:])]

        for i in range(8):
            self._subplots[i, 0].clear()
            self._subplots[i, 1].clear()

            self._subplots[i, 0].plot(self._xs, [y[i] for y in self._ys], linewidth=1)
            self._subplots[i, 1].plot(self._qxs, [qy[i] for qy in self._qys], linewidth=1)
    
    def run(self) -> None:
        # складывать данные в deque фиксированного размера в отдельном треде
        self._animation = animation.FuncAnimation(self._fig, self._update, interval=self._settings.update_interval_ms, cache_frame_data=False)
        plt.show()


class Monitoring(StubMonitoring):
    def __init__(self, data_collector: IDataCollector, settings: MonitoringSettings, files_settings: FilesSettings):
        self._data_collector = data_collector
        super().__init__(settings=settings, files_settings=files_settings)

    def _init_data_iterator(self):
        self._data_iter = self._data_collector.collect_continuously(250 * self._settings.update_interval_ms // 1000)

    def _get_samples(self) -> list[DataSampleType]:
        return next(self._data_iter)