import abc
from collections import deque
from datetime import datetime
from enum import Enum
from functools import cache, cached_property
from itertools import chain
import os
from pathlib import Path
from typing import Sequence

from speller.data_aquisition.data_collector import DataSampleType
from speller.session.entity import FlashingSequenceType
from speller.settings import ExperimentSettings, FilesSettings, StrategySettings


class SpellerEvent(Enum):
    NONE = 0
    FLASH = 1
    NON_TARGET = 2
    TARGET = 7


class IRecorder(abc.ABC):
    @abc.abstractmethod
    def record_samples(self, samples: Sequence[DataSampleType]) -> None:
        pass

    @abc.abstractmethod
    def record_flashing_sequence(self, flashing_sequecne: FlashingSequenceType) -> None:
        pass


class Recorder(abc.ABC):
    _HEADERS = [f'EEG {i}' for i in range(1, 9)] + ['FLASH', 'ITEM']

    def __init__(self, files_settings: FilesSettings, strategy_settings: StrategySettings, experiment_settings: ExperimentSettings):
        self._files_settings = files_settings
        self._strategy_settings = strategy_settings
        self._experiment_settings = experiment_settings
        self._prepare_records_file()

        self._samples_queue = deque()
        self._flashing_sequence_queue = deque()

    def _get_meta(self) -> str:
        return '__'.join((repr(self._strategy_settings), repr(self._experiment_settings)))

    @cached_property
    def _filename(self) -> Path:
        time_str = datetime.now().strftime(self._files_settings.time_format)
        meta = self._get_meta()
        filename = self._files_settings.record_pattern.format(time_str, meta)
        return self._files_settings.records_dir / filename
    
    def _write(self, value: str, create: bool = False):
        with open(self._filename, ('a+' if create else 'a')) as f:
            f.write(value)

    def _prepare_records_file(self):
        header = ",".join(self._HEADERS) + "\n"
        self._write(header, create=True)

    @staticmethod
    def _make_record(sample: DataSampleType, flash: int, item: int):
        return ",".join(map(str, sample + [flash, item]))
    
    def record_samples(self, samples: Sequence[DataSampleType]) -> None:
        self._samples_queue.appendleft(samples)
        self._record()

    def record_flashing_sequence(self, flashing_sequence: FlashingSequenceType) -> None:
        self._flashing_sequence_queue.appendleft(flashing_sequence)
        self._record()

    def _record(self) -> None:
        if all((self._samples_queue, self._flashing_sequence_queue)):
            samples = self._samples_queue.pop()
            flashing_sequence = self._flashing_sequence_queue.pop()

            indexes = self._strategy_settings.get_flashing_samples_indexes(len(flashing_sequence))

            flash_list = [0] * len(samples)
            item_list = [0] * len(samples)
            for index, flashing_list in zip(indexes, flashing_sequence):
                flash_list[index] = 1

                i, j = flashing_list[0]
                item_list[index] = i * 4 + j
                
            records = '\n'.join(map(self._make_record, samples, flash_list, item_list)) + '\n'
            self._write(records)
        
