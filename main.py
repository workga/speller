from queue import Queue
import signal
from threading import Event, Thread
from time import sleep
from typing import Callable

from speller.data_aquisition.data_collector import StubDataCollector, UnicornDataCollector
from speller.data_aquisition.epoch_getter import EpochGetter
from speller.data_aquisition.data_streamer import DataStreamer
from speller.prediction.chat_gpt_predictor import ChatGptPredictor
from speller.classification.classifier import Classifier, StubClassifier
from speller.prediction.suggestions_getter import SuggestionsGetter
from speller.prediction.t9_predictor import StubT9Predictor, T9Predictor
from speller.session.command_decoder import CommandDecoder
from speller.session.flashing_strategy import SquareRowColumnFlashingStrategy
from speller.session.sequence_handler import SequenceHandler
from speller.session.session_handler import ISessionHandler, SessionHandler
from speller.session.state_manager import StateManager


def register_shutdown_event() -> Event:
    shutdown_event = Event()
    def signal_handler(sig, frame):
        print(f'Got {sig}')
        shutdown_event.set()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    return shutdown_event


def build_speller_runner() -> Callable[[], None]:
    keyboard_size = 4
    epoch_size = 200 # 800 ms (200 ms + 600 ms) <=> 200 samples
    epoch_interval = 45 # now flash + dark = 80 + 100 = 180 ms <=> 45 samples
    
    data_queue = Queue()
    
    shutdown_event = register_shutdown_event()
    # data_collector = UnicornDataCollector(shutdown_event=shutdown_event)
    data_collector = StubDataCollector(shutdown_event=shutdown_event)
    data_streamer = DataStreamer(data_collector=data_collector, data_queue=data_queue)

    epoch_getter = EpochGetter(data_queue=data_queue, epoch_size=epoch_size, epoch_interval=epoch_interval)
    # classifier = Classifier()
    classifier = StubClassifier()
    flashing_strategy = SquareRowColumnFlashingStrategy(size=keyboard_size)
    sequence_handler = SequenceHandler(epoch_getter=epoch_getter, classifier=classifier, flashing_strategy=flashing_strategy)
    command_decoder = CommandDecoder()
    # t9_predictor = T9Predictor()
    t9_predictor = StubT9Predictor()
    chat_gpt_predictor = ChatGptPredictor()
    suggestions_getter = SuggestionsGetter(t9_predictor=t9_predictor, chat_gpt_predictor=chat_gpt_predictor)
    state_manager = StateManager(suggestions_getter=suggestions_getter)
    session_handler = SessionHandler(sequence_handler=sequence_handler, command_decoder=command_decoder, state_manager=state_manager)


    def run_speller():
        data_streamer_thread = Thread(target=data_streamer.stream)
        session_handler_thread = Thread(target=session_handler.handle_session)

        data_streamer_thread.start()
        session_handler_thread.start()

        while True:
            if not any((data_streamer_thread.is_alive(), session_handler_thread.is_alive())):
                break
            sleep(1)

    return run_speller
    

if __name__ == "__main__":
    speller_runner = build_speller_runner()
    speller_runner()

    