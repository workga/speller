from collections import deque
import signal
from threading import Event
from typing import Callable
import numpy as np
import pyqtgraph as pg

from speller.data_aquisition.data_collector import DataSampleType
from speller.monitoring.monitoring_collector import IMonitoringCollector
from speller.settings import MonitoringSettings


class MonitoringVisualizer:
    def __init__(self, monitoring_collector: IMonitoringCollector, settings: MonitoringSettings):
        self._monitoring_collector = monitoring_collector
        self._settings = settings

        self._shutdown_event = Event()

        self._xs = np.arange(-self._settings.plot_length_samples, 0)
        self._quality_xs = np.arange(-self._settings.quality_length_measurements, 0)
        self._quality_data = deque([[0] * 8] * self._settings.quality_length_measurements, maxlen=self._settings.quality_length_measurements)

        self._layout = pg.GraphicsLayoutWidget()
        self._plots = []
        self._quality_plots = []
        for i in range(8):
            plot = self._layout.addPlot(row=i, col=0).plot()
            self._plots.append(plot)
            quality_plot = self._layout.addPlot(row=i, col=1).plot()
            self._quality_plots.append(quality_plot)

        self._layout.show()

        self._timers = []

        signal.signal(signal.SIGINT, self._exit)


    def _update(self):
        data = self._monitoring_collector.get_data()
        for i in range(8):
            self._plots[i].setData(self._xs, [s[i] for s in data])

    def _update_qualities(self):
        data = list(self._monitoring_collector.get_data())
        self._quality_data.append(self._get_channels_qualities(data[1 - self._settings.quality_interval_samples:]))
        for i in range(8):
            self._quality_plots[i].setData(self._quality_xs, [s[i] for s in self._quality_data])

    def _start_timer(self, func: Callable[[], None], interval: int) -> None:
        timer = pg.QtCore.QTimer()
        timer.timeout.connect(func)
        timer.setInterval(interval)
        timer.start()

        self._timers.append(timer)

    def run(self):
        self._monitoring_collector.run(self._settings.plot_length_samples, self._shutdown_event)

        self._start_timer(self._update, self._settings.update_interval_ms)
        self._start_timer(self._update_qualities, self._settings.update_quality_interval_ms)

        pg.QtWidgets.QApplication.exec()
        self._shutdown_event.set()

    def _exit(self, *args):
        pg.QtWidgets.QApplication.quit()
    
    def _get_channels_qualities(self, samples: list[DataSampleType]) -> list[float]:
        array = np.array(samples)
        sd = np.std((array - array.mean(axis=0)), axis=0)

        return sd.tolist()
    