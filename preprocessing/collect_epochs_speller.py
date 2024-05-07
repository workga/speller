import glob
import numpy as np
import pandas as pd
import mne
from matplotlib import pyplot as plt
from pathlib import Path
import os.path
from datetime import datetime

TARGET = 5

BASE_PATH = Path('H:\\home\\study\\VKR\\data\\p300\\data\\')
RESULTS_PATH = Path('H:\\home\\study\\VKR\\data\\p300\\data\\results\\')
RESULT_EPOCHS_FILENAME = Path(f"result_epochs.fif")
RESULT_EPOCHS_FILENAME_BACKUP = Path(f"result_epochs_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.fif")
COLLECTED_EPOCHS_FILENAME = Path("result_epochs_2023-12-06_02-20-41_2_draft_annotations.fif")
DATA_INFO = [  # (path, crop_time, bad)
    (Path('records\\record__09_04_2024__21_52_01____flash=60__break=100__reps=25__name=gleb__comment=first_test__target=5__cycles=1.csv'), 1, False),
]

ALL_CHANNELS = ['Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8']
P300_CHANNELS = ['Cz', 'C4', 'PO7', 'Oz', 'PO8']  # ['Fz', 'Cz', 'Pz', 'PO7', 'Oz', 'PO8'] # ['Pz', 'PO7', 'Oz']
USE_P300_CHANNELS = False
SELECTED_CHANNELS = P300_CHANNELS if USE_P300_CHANNELS else ALL_CHANNELS
COMBINE_METHOD='mean'
AVG_COMBINE_METHOD='mean'
EVOKED_COMBINE_METHOD='mean'
ORIGIN_UNITS_TO_VOLTS_FACTOR = 1e-6
CROP_TIME = 1  # 20
LOWER_PASSBAND_FREQUENCY = 0.1
UPPER_PASSBAND_FREQUENCY = 15
NOTCH_FILTER_LENGTH = "10s"
START_TIME = 0
DURATION_TIME = 140
SCALING_VOLTS = '500e-6'
EPOCH_PRE_TIME = -0.2  # <= 0, default baseline is from it to zero
EPOCH_POST_TIME = 0.6
BASELINE_MIN = None
BASELINE_MAX = 0
EPOCH_MAX_PP_VOLTS = 150e-6
USE_REJECT_CRITERIA = False
EQUALIZE_EVENTS = True

LOG_LEVEL = 'WARNING'

mne.set_log_level(LOG_LEVEL)

def read_epochs_from_csv(i) -> mne.Epochs | None:
    path, crop_time, bad = DATA_INFO[i - 1]
    if bad:
        return None
    data = pd.read_csv(path)

    def calculate_marker(row):
        if row['FLASH'] == 1:
            if row['ITEM'] == TARGET:
                return 7
            else:
                return 2
        else:
            return 0

    data['EVENT_MARKER'] = data.apply(calculate_marker, axis=1)
    eeg_data = data[['EEG 1', 'EEG 2', 'EEG 3', 'EEG 4', 'EEG 5', 'EEG 6', 'EEG 7', 'EEG 8', 'EVENT_MARKER']].to_numpy().transpose()
    
    ch_names = ['Fz', 'C3', 'Cz', 'C4', 'Pz', 'PO7', 'Oz', 'PO8', 'STIM_EVENT']
    sfreq = 250
    info = mne.create_info(ch_names=ch_names, sfreq=sfreq, ch_types=['eeg']*8 + ['stim'])
    info.set_montage("standard_1020")
    
    raw = mne.io.RawArray(eeg_data, info)
    raw.crop(tmin=crop_time)  # DATA LOSS
    raw.apply_function(lambda x: x*ORIGIN_UNITS_TO_VOLTS_FACTOR)
    raw.filter(l_freq=LOWER_PASSBAND_FREQUENCY, h_freq=UPPER_PASSBAND_FREQUENCY)  # DATA LOSS
    raw.notch_filter(freqs=50, method='spectrum_fit', filter_length=NOTCH_FILTER_LENGTH)  # DATA LOSS

    raw.plot(start=START_TIME, duration=DURATION_TIME, scalings=SCALING_VOLTS, title=f"{i} ({path})", block=True)  # DATA LOSS (annotate 'bad')

    events = mne.find_events(raw, stim_channel="STIM_EVENT")
    event_dict = {
        "non-target": 2,
        "target": 7,
    }

    reject_criteria = {"eeg": EPOCH_MAX_PP_VOLTS}
    epochs = mne.Epochs(
        raw,
        events,
        event_id=event_dict,
        tmin=EPOCH_PRE_TIME,
        tmax=EPOCH_POST_TIME,
        reject=reject_criteria if USE_REJECT_CRITERIA else None,  # POSSIBLE DATA LOSS
        baseline=(BASELINE_MIN, BASELINE_MAX),
    )

    if EQUALIZE_EVENTS:
        epochs.equalize_event_counts()  # DATA LOSS

    # plt.plot(data[['EEG 1', 'EEG 2', 'EEG 3', 'EEG 4', 'EEG 5', 'EEG 6', 'EEG 7', 'EEG 8']]); plt.show(block=True)
    # plt.plot(data[['EEG 1', 'EEG 2', 'EEG 3', 'EEG 4', 'EEG 5', 'EEG 6', 'EEG 7', 'EEG 8']][int(250*crop_time):])
    # raw.plot(start=START_TIME, duration=DURATION_TIME, scalings=SCALING_VOLTS, title=f"{i} ({path})", block=True)
    # raw.compute_psd().plot()
    # mne.viz.plot_events(events, event_id=event_dict, sfreq=raw.info["sfreq"], first_samp=raw.first_samp)
    # raw.plot(start=START_TIME, duration=DURATION_TIME, scalings=SCALING_VOLTS, events=events, color="k", event_color={2: "g", 7: "r"})

    return epochs
    

def compare_evokeds(epochs: mne.Epochs):
    non_target_epochs = epochs["non-target"]
    target_epochs = epochs["target"]

    non_target_evoked = non_target_epochs.average(picks=SELECTED_CHANNELS, method=AVG_COMBINE_METHOD)
    target_evoked = target_epochs.average(picks=SELECTED_CHANNELS, method=AVG_COMBINE_METHOD)

    # evoked_diff = mne.combine_evoked([target_evoked, non_target_evoked,], weights=[1, -1])


    # epochs.plot(picks=SELECTED_CHANNELS, scalings=SCALING_VOLTS, n_epochs=140, events=True,  event_color={2: "g", 7: "r"}, block=True)
    # for event_type in ('non-target', 'target'):
    #     epochs[event_type].plot_image(title=event_type.upper(), picks=SELECTED_CHANNELS, combine=COMBINE_METHOD)
    # evoked_diff.plot_topo(color="b", legend=True)
    mne.viz.plot_compare_evokeds(
        {
            'non-target': non_target_evoked,
            'target': target_evoked
        },
        legend="upper left",
        show_sensors="upper right",
        colors=['g', 'r'],
        combine=EVOKED_COMBINE_METHOD,
    )

def save_collected_epochs(epochs: mne.Epochs) -> None:
    epochs.save(RESULTS_PATH / RESULT_EPOCHS_FILENAME_BACKUP, fmt='double')
    epochs.save(RESULTS_PATH / RESULT_EPOCHS_FILENAME, fmt='double', overwrite=True)

def load_collected_epochs(filename: Path | None = None) -> mne.Epochs:
   return mne.read_epochs(RESULTS_PATH / (filename or RESULT_EPOCHS_FILENAME))


def collect_epochs() -> mne.Epochs:
    NUM_OF_DATA = len(DATA_INFO)
    all_epochs = []
    for i in range(1, NUM_OF_DATA + 1):
        epochs = read_epochs_from_csv(i)
        if epochs is None:
            continue
        epochs.drop_bad()
        all_epochs.append(epochs)

    result_epochs = mne.concatenate_epochs(all_epochs)
    
    # save_collected_epochs(result_epochs)

    return result_epochs



def main():
    collected_epochs = collect_epochs()
    collected_epochs.plot(picks=SELECTED_CHANNELS, scalings=SCALING_VOLTS, n_epochs=140, events=True,  event_color={2: "g", 7: "r"}, title=f"result_epochs", block=True)
    compare_evokeds(collected_epochs)


    # collected_epochs = load_collected_epochs(COLLECTED_EPOCHS_FILENAME)
    # collected_epochs.plot(picks=SELECTED_CHANNELS, scalings=SCALING_VOLTS, n_epochs=140, events=True,  event_color={2: "g", 7: "r"}, title=f"result_epochs", block=True)

    # loaded_epochs = load_collected_epochs()
    # loaded_epochs.plot(picks=SELECTED_CHANNELS, scalings=SCALING_VOLTS, n_epochs=140, events=True,  event_color={2: "g", 7: "r"}, title=f"loaded_epochs", block=True)

def view_file(file: str | None, target: int):
    if not file:
        file = max(glob.glob(str(Path("./records") / '*'))).split('\\')[1].removesuffix('.csv')

    global DATA_INFO, TARGET
    DATA_INFO = [
        (Path(f'records\{file}.csv'), 1, False),
    ]
    TARGET = target

    collected_epochs = collect_epochs()
    compare_evokeds(collected_epochs)


if __name__ == "__main__":
    main()