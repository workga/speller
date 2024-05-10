

import glob
from pathlib import Path

def get_raw_files(records_dir: Path, name: str | None) -> list[str]:
    pattern = "record*"
    if name:
        pattern += f"name={name}*"

    files = (
        set(glob.glob(f"{records_dir}\\{pattern}"))
        - set(glob.glob(f"{records_dir}\\*PREPROCESSED*"))
        - set(glob.glob(f"{records_dir}\\*test*"))
    )

    # print("Got raw files:\n", '\n'.join(files))
    return files


def get_preprocessed_files(records_dir: Path, name: str | None) -> list[str]:
    pattern = "*PREPROCESSED*"
    if name:
        pattern = f"*name={name}" + pattern

    files = glob.glob(f"{records_dir}\\{pattern}")

    # print("Got preprocessed files:\n", '\n'.join(files))
    return files