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
    repetitions_count: int = 2

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
    def epoch_interval_samples(self) -> int:
        return (self.flash_duration_ms + self.break_duration_ms) // 4
    

class SquareSingleCharacterStrategySettings(BaseSettings):
    min_distance: int = 2

class FilesSettings(BaseSettings):
    images_dir: Path = Path("./static")
    keyboard_items_pattern: str = 'keyboard_item_{}_{}'
    keyboard_flash_item_filename: str = 'keyboard_item_flash'

class ViewSettings(BaseSettings):
    update_interval_ms: int = 1
    font_size: int = 14
    keyboard_items_scale: float = 0.8

    screen_width: int = 1920 - 120
    screen_height: int = 1080 - 80
    fullscreen: bool = True

class LoggingSettings(BaseSettings):
    level: str = 'INFO'

class StateManagerSettings(BaseSettings):
    max_suggestions: int = 6

class StubDataCollectorSettings(BaseSettings):
    ms_per_sample: Literal[4] = 4

class UnicornDataCollectorSettings(BaseSettings):
    single_batch: bool = True
    batch_size: int = 50
