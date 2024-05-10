import glob
import click

import logging
from threading import Thread

from deps import get_monitoring_container, get_model_container, get_speller_container

from preprocessing.model import Model
from preprocessing.epoch_collector import EpochCollector
from preprocessing.files import get_preprocessed_files, get_raw_files
from preprocessing.preprocessor import Preprocessor
from preprocessing.collect_epochs_speller import view_file
from speller.monitoring.visualizer import MonitoringVisualizer
from speller.session.speller_runner import SpellerRunner
from speller.settings import FilesSettings, LoggingSettings
from speller.view.speller_view import SpellerView


logger = logging.getLogger(__name__)


@click.group()
def speller_group():
    pass


@speller_group.command()
@click.option("--stub", is_flag=True, show_default=True, default=False, help="Use stub dependencies")
def speller(stub: bool) -> None:
    # import sys
    # sys.setswitchinterval(0.001)
    container = get_speller_container(stub)

    logging.basicConfig(level=container.resolve(LoggingSettings).level)

    speller_runner = container.resolve(SpellerRunner)
    speller_view = container.resolve(SpellerView)

    speller_runner_thread = Thread(target=speller_runner.run)
    speller_runner_thread.start()

    speller_view.run()

    speller_runner_thread.join()


@click.group()
def monitoring_group():
    pass


@monitoring_group.command()
@click.option("--stub", is_flag=True, show_default=True, default=False, help="Use stub dependencies")
@click.option("--file", is_flag=True, show_default=True, default=False, help="Read stub data from file")
def monitoring(stub: bool, file: bool) -> None:
    container = get_monitoring_container(stub, file)
    monitoring = container.resolve(MonitoringVisualizer)
    monitoring.run()


@click.group()
def viewer_group():
    pass


@viewer_group.command()
@click.argument("file", required=False)
@click.option("--target", default=5, help="Target item")
def viewer(file: str | None, target: int) -> None:
    view_file(file, target)


@click.group()
def preprocessor_group():
    pass


@preprocessor_group.command()
@click.argument("name")
@click.argument("iter")
def preprocessor(name: str, iter: int) -> None:
    container = get_model_container()

    preprocessor = container.resolve(Preprocessor)
    epoch_collector = container.resolve(EpochCollector)

    files_settings = container.resolve(FilesSettings)
    
    file = glob.glob(f"{files_settings.records_dir}\\*name={name}*comment=iter_{iter}*")[0]

    raw = preprocessor.preprocess(file)
    epochs = epoch_collector.collect(raw)
    epoch_collector.plot_comparison(epochs)


@click.group()
def epoch_collector_group():
    pass


@epoch_collector_group.command()
@click.option("--name", required=False, help="Filter by name")
@click.option("--raw", is_flag=True, show_default=True, default=False, help="Use raw files without annotations")
def epoch_collector(raw: bool, name: str | None) -> None:
    container = get_model_container()

    preprocessor = container.resolve(Preprocessor)
    epoch_collector = container.resolve(EpochCollector)
    files_settings = container.resolve(FilesSettings)

    if raw:
        files = [preprocessor.preprocess(file, silent=True) for file in get_raw_files(files_settings.records_dir, name)]
    else:
        files = get_preprocessed_files(files_settings.records_dir, name)

    epochs = epoch_collector.collect_many(files)
    epoch_collector.plot_comparison(epochs)


@click.group()
def fit_model_group():
    pass


@fit_model_group.command()
@click.option("--name", required=False, help="Filter by name")
@click.option("--raw", is_flag=True, show_default=True, default=False, help="Use raw files without annotations")
def fit_model(raw: bool, name: str | None) -> None:
    container = get_model_container()

    preprocessor = container.resolve(Preprocessor)
    epoch_collector = container.resolve(EpochCollector)
    model = container.resolve(Model)
    files_settings = container.resolve(FilesSettings)

    if raw:
        files = [preprocessor.preprocess(file, silent=True) for file in get_raw_files(files_settings.records_dir, name)]
    else:
        files = get_preprocessed_files(files_settings.records_dir, name)
    
    epochs = epoch_collector.collect_many(files)
    model.fit(epochs)



cli = click.CommandCollection(
    sources=[
        speller_group,
        monitoring_group,
        viewer_group,
        preprocessor_group,
        epoch_collector_group,
        fit_model_group,
    ]
)


if __name__ == '__main__':
    cli()
    