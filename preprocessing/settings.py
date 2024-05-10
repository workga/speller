from pydantic_settings import BaseSettings

TARGET_MARKER = 7
NON_TARGET_MARKER = 2


class PreprocessorSettings(BaseSettings):
    crop_time_s: float = 9
    lower_passband_frequency: float = 0.1
    upper_passband_frequency: float = 15.
    notch_filter_length: str = "10s"


class EpochCollectorSettings(BaseSettings):
    epoch_pre_time_s: float = -0.2
    epoch_post_time_s: float = 0.6
    baseline_start_s: float | None = None
    baseline_end_s: float | None = 0

    equalize_events: bool = True  # крепко подумать!  # если False, то обязательно stratify
    equilize_events_method: str = ('truncate', 'mintime')[0]  # крепко подумать!


class ModelSettings(BaseSettings):
    downsample_freq: int | None = None
    data_proportion: float = 1
    test_proportion: float = 0.2
    random_seed: int = 0

    classifier__C: float = 0.1
    classifier__kernel: str = 'linear'

    
