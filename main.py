import logging
from threading import Thread
from time import sleep
from deps import get_speller_container

from speller.session.speller_runner import SpellerRunner
from speller.settings import LoggingSettings
from speller.view.speller_view import SpellerView


logger = logging.getLogger(__name__)


def run() -> None:
    container = get_speller_container()

    logging.basicConfig(level=container.resolve(LoggingSettings).level)

    speller_runner = container.resolve(SpellerRunner)
    speller_view = container.resolve(SpellerView)

    speller_runner_thread = Thread(target=speller_runner.handle_session)
    speller_runner_thread.start()

    speller_view.run()

    logger.info("Waiting SpellerRunner...")
    while True:
        if not speller_runner_thread.is_alive():
            break
        logger.info(f"SpellerRunner is still alive...")
        sleep(1)

    logger.info("SpellerRunner finished")
    

if __name__ == "__main__":
    run()

    