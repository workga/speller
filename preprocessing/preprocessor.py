from functools import partial
import re
from typing import Any, Sequence
import mne
import numpy as np
from numpy import ndarray
import pandas as pd
from datetime import datetime

from preprocessing.settings import NON_TARGET_MARKER, TARGET_MARKER, PreprocessorSettings
from speller.settings import FilesSettings


class Preprocessor:
    _CHANNEL_NAMES = ['Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8', 'STIM_EVENT']
    _FREQUENCY = 250
    _ORIGIN_UNITS_TO_VOLTS_FACTOR = 1e-6
    _DURATION_TIME = 100
    _SCALING_VOLTS = '100e-6'
    

    def __init__(self, settings: PreprocessorSettings, files_settings: FilesSettings):
        self._settings = settings
        self._files_settings = files_settings

    @staticmethod
    def _get_target_from_filename(filename: str) -> int:
        return int(re.search('target=(\d+)', filename).group(1))
    
    @staticmethod
    def _calculate_marker(target: int, row: Any) -> int:
        if row['FLASH'] == 1:
            if row['ITEM'] == target:
                return TARGET_MARKER
            return NON_TARGET_MARKER
        return 0

    def _read_file(self, src_file: str) -> ndarray:
        data = pd.read_csv(src_file)
        target = self._get_target_from_filename(src_file)

        data['EVENT_MARKER'] = data.apply(partial(self._calculate_marker, target), axis=1)
        return data[['EEG 1', 'EEG 2', 'EEG 3', 'EEG 4', 'EEG 5', 'EEG 6', 'EEG 7', 'EEG 8', 'EVENT_MARKER']].to_numpy().transpose()
    
    @classmethod
    def _create_info(cls) -> mne.Info:
        info = mne.create_info(ch_names=cls._CHANNEL_NAMES, sfreq=cls._FREQUENCY, ch_types=['eeg']*8 + ['stim'])
        info.set_montage("standard_1020")
        return info
    
    def _preprocess(self, raw: mne.io.RawArray) -> mne.io.RawArray:
        raw.crop(tmin=self._settings.crop_time_s)  # DATA LOSS
        raw.apply_function(lambda x: x * self._ORIGIN_UNITS_TO_VOLTS_FACTOR)
        raw.filter(l_freq=self._settings.lower_passband_frequency, h_freq=self._settings.upper_passband_frequency)  # DATA LOSS
        raw.notch_filter(freqs=50, method='spectrum_fit', filter_length=self._settings.notch_filter_length)  # DATA LOSS
        return raw
    
    def _annotate(self, raw: mne.io.RawArray) -> mne.io.RawArray:
        raw.plot(duration=self._DURATION_TIME, scalings=self._SCALING_VOLTS, block=True)  # DATA LOSS (annotate 'bad')
        return raw

    def preprocess(self, src_file: str, silent: bool = False, save: bool = True) -> mne.io.RawArray:
        eeg_data = self._read_file(src_file)
        info = self._create_info()

        raw = mne.io.RawArray(eeg_data, info)
        raw = self._preprocess(raw)
        if not silent:
            raw = self._annotate(raw)

            time_str = datetime.now().strftime(self._files_settings.time_format)
            if save:
                raw.save((src_file + f'__[PREPROCESSED]__{time_str}__eeg.fif'))

        return raw
    
    def preprocess_samples(self, samples: Sequence[Sequence[float]]) -> Sequence[Sequence[float]]:
        samples = np.array(samples)
        samples *= self._ORIGIN_UNITS_TO_VOLTS_FACTOR
        samples = samples.transpose()

        samples = mne.filter.filter_data(
            samples,
            sfreq=self._FREQUENCY,
            l_freq=self._settings.lower_passband_frequency,
            h_freq=self._settings.upper_passband_frequency,
        )
        samples = mne.filter.notch_filter(
            samples,
            self._FREQUENCY,
            freqs=50,
            method='spectrum_fit',
            filter_length=self._settings.notch_filter_length,
        )
        
        samples = samples.transpose()
        return samples.tolist()
