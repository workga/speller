from datetime import datetime
import glob
from pathlib import Path

from speller.settings import FilesSettings


def get_raw_files(records_dir: Path, name: str | None) -> list[str]:
    pattern = "record*"
    if name:
        pattern += f"name={name}*"

    files = (
        set(glob.glob(f"{records_dir}\\{pattern}"))
        - set(glob.glob(f"{records_dir}\\*PREPROCESSED*"))
        - set(glob.glob(f"{records_dir}\\*test*"))
    )

    print(f"Got raw files: {len(files)}")
    return files


def get_preprocessed_files(records_dir: Path, name: str | None) -> list[str]:
    pattern = "*PREPROCESSED*"
    if name:
        pattern = f"*name={name}" + pattern

    files = glob.glob(f"{records_dir}\\{pattern}")

    print(f"Got preprocessed files: {len(files)}")
    return files

def get_model_filename(settings: FilesSettings, name: str | None, comment: str | None) -> str:
    time_str = datetime.now().strftime(settings.time_format)
    meta = (
        f'__name={name or "default"}'
        f'__comment={comment or "default"}'
    )
    filename = str(settings.models_dir / settings.model_pattern.format(time_str, meta))
    return filename

def find_model_file(settings: FilesSettings) -> str:
    pattern = "model__*"
    if settings.clf_name:
        pattern += f"name={settings.clf_name}*"
    if settings.clf_comment:
        pattern += f"comment={settings.clf_comment}*"

    file = glob.glob(f"{settings.models_dir}\\{pattern}")[-1]
    print(f"Got ClassifierModel file: {file}")
    return file