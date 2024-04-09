import abc
from collections import deque
from enum import Enum
import os
from pathlib import Path
from typing import Sequence

from speller.data_aquisition.data_collector import DataSampleType
from speller.session.entity import FlashingSequenceType
from speller.session.state_manager import IStateManager
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

    def __init__(
        self, files_settings: FilesSettings, strategy_settings: StrategySettings, experiment_settings: ExperimentSettings, state_manager: IStateManager):
        self._files_settings = files_settings
        self._strategy_settings = strategy_settings
        self._experiment_settings = experiment_settings
        self._state_manager = state_manager

        self._samples_queue = deque()
        self._flashing_sequence_queue = deque()

    def _get_meta(self) -> str:
        return (
            f'__flash={self._strategy_settings.flash_duration_ms}'
            f'__break={self._strategy_settings.break_duration_ms}'
            f'__reps={self._state_manager.session_reps}'
            f'__name={self._state_manager.session_name}'
            f'__comment={self._state_manager.session_comment}'
            f'__target={self._state_manager.session_target}'
            f'__cycles={self._state_manager.session_cycles}'
        )

    def _get_filename(self) -> Path:
        time_str = self._state_manager.session_start_time.strftime(self._files_settings.time_format)
        meta = self._get_meta()
        filename = self._files_settings.record_pattern.format(time_str, meta)
        return self._files_settings.records_dir / filename
    
    def _write(self, value: str):
        filename = self._get_filename()
            
        with open(filename, 'a+') as f:
            if os.stat(filename).st_size == 0:
                header = ",".join(self._HEADERS) + "\n"
                f.write(header)
            f.write(value)

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
        
