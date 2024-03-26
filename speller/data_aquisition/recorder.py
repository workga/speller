import abc
from datetime import datetime
from enum import Enum
from functools import cache, cached_property
from itertools import chain
import os
from pathlib import Path
from typing import Sequence

from speller.data_aquisition.data_collector import DataSampleType
from speller.settings import FilesSettings


class Event(Enum):
    NONE = 0
    FLASH = 1


class IRecorder(abc.ABC):
    @abc.abstractmethod
    def record_sequence(self, samples: Sequence[DataSampleType], events: Sequence[Event]) -> None:
        pass


class Recorder(abc.ABC):
    _HEADERS = [f'EEG {i}' for i in range(1, 9)] + ['MARKER']

    def __init__(self, files_settings: FilesSettings):
        self._files_settings = files_settings
        self._prepare_records_file()


    @cached_property
    def _filename(self) -> Path:
        time_str = datetime.now().strftime(self._files_settings.time_format)
        meta = 'default'
        filename = self._files_settings.record_pattern.format(time_str, meta)
        return self._files_settings.records_dir / filename
    
    def _write(self, value: str, create: bool = False):
        with open(self._filename, ('a+' if create else 'a')) as f:
            f.write(value)

    def _prepare_records_file(self):
        header = ",".join(self._HEADERS) + "\n"
        self._write(header, create=True)

    @staticmethod
    def _make_record(sample: DataSampleType, event: Event):
        return ",".join(map(str, sample + (event,)))
        
    def record_sequence(self, samples: Sequence[DataSampleType], events: Sequence[Event]) -> None:
        records = '\n'.join(map(self._make_record, samples, events)) + '\n'
        self._write(records)
        
