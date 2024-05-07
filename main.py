import click

import logging
from threading import Thread
from deps import get_monitoring_container, get_speller_container

from preprocessing.collect_epochs_speller import view_file
from speller.monitoring.visualizer import MonitoringVisualizer
from speller.session.speller_runner import SpellerRunner
from speller.settings import LoggingSettings
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


cli = click.CommandCollection(sources=[speller_group, monitoring_group, viewer_group])


if __name__ == '__main__':
    cli()
    