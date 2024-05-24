import random
import sys
from typing import Sequence
import mne
import numpy as np

from preprocessing.settings import NON_TARGET_MARKER, TARGET_MARKER, EpochCollectorSettings
from speller.settings import FilesSettings, samples_to_ms


class EpochCollector:
    def __init__(self, settings: EpochCollectorSettings, files_settings: FilesSettings):
        self._settings = settings
        self._files_settings = files_settings

    def _read_raw_data(self, src_file: str) -> mne.io.RawArray:
        return mne.io.read_raw(src_file)
    
    def _equalize_event_counts_randomly(self, epochs: mne.EpochsArray) -> mne.EpochsArray:
        target_epochs = epochs["target"]
        non_target_epochs = epochs["non-target"]

        drop_count = len(non_target_epochs) - len(target_epochs)
        assert drop_count > 0

        # random.seed(0)
        drop_indexes = random.sample(range(len(non_target_epochs)), drop_count)
        non_target_epochs.drop(drop_indexes)

        epochs = mne.concatenate_epochs([target_epochs, non_target_epochs])
        return epochs
    
    @staticmethod
    def plot_comparison(epochs: mne.EpochsArray) -> None:
        non_target_evoked = epochs["non-target"].average(method='mean')
        target_evoked = epochs["target"].average(method='mean')

        mne.viz.plot_compare_evokeds(
            {'non-target': non_target_evoked, 'target': target_evoked},
            legend="upper left",
            show_sensors="upper right",
            colors=['g', 'r'],
            combine='mean',
        )

    def collect(self, raw: str | mne.io.RawArray) -> mne.EpochsArray:
        if not isinstance(raw, mne.io.RawArray):
            raw = self._read_raw_data(raw)
        
        events = mne.find_events(raw, stim_channel="STIM_EVENT")

        event_dict = {"non-target": NON_TARGET_MARKER, "target": TARGET_MARKER}
        epochs = mne.Epochs(
            raw,
            events,
            event_id=event_dict,
            tmin=self._settings.epoch_pre_time_s,
            tmax=self._settings.epoch_post_time_s,
            baseline=(self._settings.baseline_start_s, self._settings.baseline_end_s),
        )

        epochs.drop_bad()

        if self._settings.equalize_events:  # DATA LOSS
            if self._settings.equilize_events_method == 'random':
                epochs = self._equalize_event_counts_randomly(epochs)
            else:
                epochs.equalize_event_counts(method=self._settings.equilize_events_method)

        return epochs
    
    def collect_many(self, raws: list[str] | list[mne.io.RawArray]) -> mne.EpochsArray:
        all_epochs = []
        for raw in raws:
            epochs = self.collect(raw)
            all_epochs.append(epochs)

        result_epochs = mne.concatenate_epochs(all_epochs)
        print("Collected epochs: ", len(result_epochs))
        return result_epochs
    
    def preprocess_epochs(self, epochs: Sequence[Sequence[float]]) -> np.ndarray:
        epochs = np.array(epochs)
        epochs = epochs.transpose((0, 2, 1))
        
        times_range_ms =  range(self._settings.epoch_pre_time_ms, self._settings.epoch_post_time_ms + 1, samples_to_ms(1))
        times_s = np.array([int(ms * 1000) for ms in times_range_ms])
        
        epochs = mne.baseline.rescale(epochs, times_s, (self._settings.baseline_start_s, self._settings.baseline_end_s))
        epochs = epochs.reshape(len(epochs), -1)
        return epochs