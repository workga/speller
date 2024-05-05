import signal
import numpy as np
import pyqtgraph as pg

from speller.monitoring.monitoring_collector import IMonitoringCollector
from speller.settings import MonitoringSettings


class MonitoringVisualizer:
    def __init__(self, monitoring_collector: IMonitoringCollector, settings: MonitoringSettings):
        self._monitoring_collector = monitoring_collector
        self._settings = settings

        self._xs = np.arange(-self._settings.plot_length_samples, 0)
        self._quality_xs = np.arange(-self._settings.plot_length_s, 0)

        self._layout = pg.GraphicsLayoutWidget()
        self._plots = []
        self._quality_plots = []
        for i in range(8):
            plot = self._layout.addPlot(row=i, col=0).plot()
            self._plots.append(plot)
            quality_plot = self._layout.addPlot(row=i, col=1).plot()
            self._quality_plots.append(quality_plot)

        self._layout.show()

        signal.signal(signal.SIGINT, self._exit)


    def _update(self):
        data = self._monitoring_collector.get_data()

        for i in range(8):
            self._plots[i].setData(self._xs, [s[i] for s in data])

    def run(self):
        self._monitoring_collector.run(self._settings.plot_length_samples)

        timer = pg.QtCore.QTimer()
        timer.timeout.connect(self._update)
        timer.setInterval(self._settings.update_interval_ms)
        timer.start()

        pg.QtWidgets.QApplication.exec()

    @staticmethod
    def _exit(*args):
        pg.QtWidgets.QApplication.quit()
    
    # def _get_channels_qualities(self, samples: list[DataSampleType]) -> list[float]:
    #     array = np.array(samples)
    #     sd = np.std((array - array.mean(axis=0)), axis=0)

    #     return sd.tolist()
    