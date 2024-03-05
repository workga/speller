import logging
from queue import Queue
import signal
from threading import Event, Thread
from time import sleep
from typing import Callable

from speller.data_aquisition.data_collector import StubDataCollector, SyncStubDataCollector, UnicornDataCollector
from speller.data_aquisition.epoch_getter import EpochGetter, QueueEpochGetter
from speller.data_aquisition.data_streamer import DataStreamer
from speller.prediction.chat_gpt_predictor import ChatGptPredictor
from speller.classification.classifier import Classifier, StubClassifier
from speller.prediction.suggestions_getter import SuggestionsGetter
from speller.prediction.t9_predictor import StubT9Predictor, T9Predictor
from speller.session.command_decoder import CommandDecoder
from speller.session.flashing_strategy import SquareRowColumnFlashingStrategy
from speller.session.sequence_handler import SequenceHandler
from speller.session.speller_runner import ISessionHandler, SpellerRunner
from speller.session.state_manager import StateManager
from speller.view.speller_window import SpellerWindow


logger = logging.getLogger(__name__)


def register_shutdown_event() -> Event:
    shutdown_event = Event()
    def signal_handler(sig, frame):
        print(f'Got {sig}')
        shutdown_event.set()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    return shutdown_event


def build_runner() -> Callable[[], None]:
    logging.basicConfig(level='DEBUG')

    keyboard_size = 4
    # data_queue = Queue()
    
    shutdown_event = register_shutdown_event()
    # data_collector = UnicornDataCollector(shutdown_event=shutdown_event)
    # data_collector = SyncUnicornDataCollector(shutdown_event=shutdown_event)
    # data_collector = StubDataCollector(shutdown_event=shutdown_event)
    data_collector = SyncStubDataCollector(shutdown_event=shutdown_event)
    # data_streamer = DataStreamer(data_collector=data_collector, data_queue=data_queue)

    # epoch_getter = QueueEpochGetter(data_queue=data_queue)
    epoch_getter = EpochGetter(data_collector=data_collector)
    # classifier = Classifier()
    classifier = StubClassifier()
    flashing_strategy = SquareRowColumnFlashingStrategy(size=keyboard_size)
    # t9_predictor = T9Predictor()
    t9_predictor = StubT9Predictor()
    chat_gpt_predictor = ChatGptPredictor()
    suggestions_getter = SuggestionsGetter(t9_predictor=t9_predictor, chat_gpt_predictor=chat_gpt_predictor)
    state_manager = StateManager(suggestions_getter=suggestions_getter)
    sequence_handler = SequenceHandler(epoch_getter=epoch_getter, classifier=classifier, flashing_strategy=flashing_strategy, state_manager=state_manager)

    command_decoder = CommandDecoder()
    speller_runner = SpellerRunner(sequence_handler=sequence_handler, command_decoder=command_decoder, state_manager=state_manager, shutdown_event=shutdown_event)

    speller_window = SpellerWindow(state_manager=state_manager)

    def run_speller():
        # data_streamer_thread = Thread(target=data_streamer.stream)
        speller_runner_thread = Thread(target=speller_runner.handle_session)

        # data_streamer_thread.start()
        speller_runner_thread.start()

        speller_window.run()

        while True:
            logger.info("runner: waiting threads...")
            # logger.info(f"speller_runner: {data_streamer_thread.is_alive()=}")
            is_alive = speller_runner_thread.is_alive()
            logger.info(f"speller_runner is alive: %s", is_alive)
            if not is_alive:
            # if not any((data_streamer_thread.is_alive(), session_handler_thread.is_alive())):
                break
            sleep(1)
        logger.info("runner: finish waiting threads")
        

    return run_speller
    

if __name__ == "__main__":
    runner = build_runner()
    runner()

    