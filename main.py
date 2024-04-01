import click

import logging
from threading import Thread
from deps import get_speller_container

from speller.session.speller_runner import SpellerRunner
from speller.settings import LoggingSettings
from speller.view.speller_view import SpellerView


logger = logging.getLogger(__name__)


@click.command()
@click.option("--stub", is_flag=True, show_default=True, default=False, help="Use stub dependencies")
def run(stub: bool) -> None:
    container = get_speller_container(stub)

    logging.basicConfig(level=container.resolve(LoggingSettings).level)

    speller_runner = container.resolve(SpellerRunner)
    speller_view = container.resolve(SpellerView)

    speller_runner_thread = Thread(target=speller_runner.run)
    speller_runner_thread.start()

    speller_view.run()

    speller_runner_thread.join()
    

if __name__ == "__main__":
    run()

    