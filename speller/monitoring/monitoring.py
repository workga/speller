import abc
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np
from speller.data_aquisition.data_collector import DataSampleType
from speller.settings import MonitoringSettings

class IMonitoring(abc.ABC):
    @abc.abstractmethod
    def run(self) -> None:
        pass

class StubMonitoring:
    def __init__(self, settings: MonitoringSettings):
        self._settings = settings
        self._fig = plt.figure()
        self._axs = []
        for i in range(1, 9):
            self._axs.append(self._fig.add_subplot(8, 1, i))
        
        self._xs = list(range(-self._settings.last_samples_count, 0))
        self._ys = [[0] * 8 ] * self._settings.last_samples_count

    def _get_samples(self) -> list[DataSampleType]:
        count = self._settings.last_samples_count // 10
        return np.random.rand(count, 8).tolist()

    def _update(self, *args) -> None:
        samples = self._get_samples()
        self._ys = self._ys[len(samples) - self._settings.last_samples_count:] + samples

        for i, ax in enumerate(self._axs):
            ax.clear()
            ax.plot(self._xs, [y[i] for y in self._ys], linewidth=1)
    
    def run(self) -> None:
        self._animation = animation.FuncAnimation(self._fig, self._update, interval=self._settings.update_interval_ms, cache_frame_data=False)
        plt.show()