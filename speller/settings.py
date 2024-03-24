from pathlib import Path
from pydantic_settings import BaseSettings

class StrategySettings(BaseSettings):
    keyboard_size: int = 4

class FilesSettings(BaseSettings):
    images_dir: Path = Path("./static")
    keyboard_items_pattern: str = 'keyboard_item_{}_{}'
    keyboard_flash_item_filename: str = 'keyboard_item_flash'
    keyboard_items_scale: float = 0.8