from functools import cached_property
from pathlib import Path
from typing import Literal
from pydantic import ValidationInfo, field_validator, model_validator
from pydantic_settings import BaseSettings

def samples_to_ms(samples: int) -> int:
    return samples * 4

def ms_to_samples(ms: int) -> int:
    assert ms % 4 == 0, f'ms must be a multiple of 4!'
    return ms // 4

class StrategySettings(BaseSettings):
    keyboard_size: int = 4
    repetitions_count: int = 1

    flash_duration_ms: int = 60
    break_duration_ms: int = 100

    epoch_baseline_ms: Literal[200] = 200
    epoch_size_samples: Literal[200] = 200

    @field_validator('flash_duration_ms', 'break_duration_ms')
    @classmethod
    def value_is_multiple_of_four(cls, v: int, info: ValidationInfo) -> int:
        assert v % 4 == 0, f'{info.field_name} must be a multiple of 4!'
        return v
    
    @model_validator(mode='after')
    def epoch_is_longer_than_flashing(self) -> 'StrategySettings':
        epoch_duration = samples_to_ms(self.epoch_size_samples)
        flashing_duration = self.flash_duration_ms + self.break_duration_ms
        assert epoch_duration > flashing_duration, f'epoch duration must be greater than flashing duration!'
        return self

    @cached_property
    def epoch_interval_ms(self) -> int:
        return self.flash_duration_ms + self.break_duration_ms

    @cached_property
    def epoch_interval_samples(self) -> int:
        return self.epoch_interval_ms // 4
    
    @cached_property
    def flash_duration_s(self):
        return self.flash_duration_ms / 1000
    
    @cached_property
    def break_duration_s(self):
        return self.break_duration_ms / 1000
    
    @cached_property
    def epoch_baseline_s(self):
        return self.epoch_baseline_ms / 1000
    

    def get_flashing_samples_indexes(self, number: int) -> list[int]:
        index = ms_to_samples(self.epoch_baseline_ms)
        indexes = []
        for _ in range(number):
            indexes.append(index)
            index += self.epoch_interval_samples

        return indexes
    
    def get_number_of_samples(self, number_of_epoches) -> int:
        return self.epoch_size_samples + (number_of_epoches - 1) * self.epoch_interval_samples

class ExperimentSettings(BaseSettings):
    name: str = 'gleb'
    comment: str = 'first_test'
    target: int = 5
    cycles_count: int = 10

    def __repr__(self) -> str:
        return f'name={self.name}__comment={self.comment}__target={self.target}'

class FilesSettings(BaseSettings):
    static_dir: Path = Path("./static")
    keyboard_items_pattern: str = 'keyboard_item_{}_{}'
    keyboard_flash_item_filename: str = 'keyboard_item_flash'

    classifier_model_filename: str = 'classifier_model.pickle'
    records_dir: Path = Path("./records")
    time_format: str = '%Y_%m_%d__%H_%M_%S'
    record_pattern: str = 'record__{}__{}.csv'

class ViewSettings(BaseSettings):
    update_interval_ms: int = 1
    font_size: int = 14
    keyboard_items_scale: float = 1.4

    screen_width: int = 1920
    screen_height: int = 1080
    fullscreen: bool = True

class LoggingSettings(BaseSettings):
    level: str = 'WARNING'

class StateManagerSettings(BaseSettings):
    max_suggestions: int = 6

class StubDataCollectorSettings(BaseSettings):
    ms_per_sample: Literal[4] = 4

class UnicornDataCollectorSettings(BaseSettings):
    batch_size: int = 250

class MonitoringSettings(BaseSettings):
    plot_length_s: int = 10
    update_interval_ms: int = 100
    quality_interval_samples: int = 250

    @field_validator('update_interval_ms')
    @classmethod
    def value_is_multiple_of_four(cls, v: int, info: ValidationInfo) -> int:
        assert v % 4 == 0, f'{info.field_name} must be a multiple of 4!'
        return v
    
    @model_validator(mode='after')
    def plot_length_is_multiple_of_quality_interval(self) -> 'MonitoringSettings':
        assert self.plot_length_samples % self.quality_interval_samples == 0, f'plot length samples must be a multiple of quality interval samples!'
        return self

    @cached_property
    def plot_length_samples(self) -> int:
        return self.plot_length_s * 250
    
    @cached_property
    def collect_interval_samples(self) -> int:
        return self.update_interval_ms // 4
    
    @cached_property
    def quality_length_measurements(self) -> int:
        return self.plot_length_samples // self.quality_interval_samples
    
    @cached_property
    def update_quality_interval_ms(self) -> int:
        return 1000 * self.quality_interval_samples // 250
