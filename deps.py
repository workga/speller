from enum import StrEnum
import signal
from threading import Event
from independency import Container, ContainerBuilder
from independency.container import Dependency

from speller.data_aquisition.data_collector import IDataCollector, StubDataCollector, UnicornDataCollector
from speller.data_aquisition.epoch_getter import EpochGetter, IEpochGetter
from speller.prediction.chat_gpt_predictor import ChatGptPredictor, IChatGptPredictor
from speller.classification.classifier import Classifier, IClassifier, StubClassifier
from speller.prediction.suggestions_getter import ISuggestionsGetter, SuggestionsGetter
from speller.prediction.t9_predictor import IT9Predictor, StubT9Predictor, T9Predictor
from speller.session.command_decoder import CommandDecoder, ICommandDecoder
from speller.session.flashing_strategy import IFlashingStrategy, SquareSingleCharacterFlashingStrategy, SquareRowColumnFlashingStrategy
from speller.session.sequence_handler import ISequenceHandler, SequenceHandler
from speller.session.speller_runner import SpellerRunner
from speller.session.state_manager import IStateManager, StateManager
from speller.settings import FilesSettings, LoggingSettings, SquareSingleCharacterStrategySettings, StateManagerSettings, StrategySettings, StubDataCollectorSettings, UnicornDataCollectorSettings, ViewSettings
from speller.view.speller_view import SpellerView


def register_shutdown_event() -> Event:
    shutdown_event = Event()
    def signal_handler(sig, frame):
        print(f'Got {sig}')
        shutdown_event.set()
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    return shutdown_event


class SpellerContainerKey(StrEnum):
    SHUTDOWN_EVENT='SHUTDOWN_EVENT'


def get_speller_container(stub: bool = True) -> Container:
    builder = ContainerBuilder()

    builder.singleton(SpellerContainerKey.SHUTDOWN_EVENT.value, register_shutdown_event)

    builder.singleton(StrategySettings, lambda: StrategySettings())
    builder.singleton(SquareSingleCharacterStrategySettings, lambda: SquareSingleCharacterStrategySettings())
    builder.singleton(FilesSettings, lambda: FilesSettings())
    builder.singleton(ViewSettings, lambda: ViewSettings())
    builder.singleton(LoggingSettings, lambda: LoggingSettings())
    builder.singleton(StateManagerSettings, lambda: StateManagerSettings())
    builder.singleton(StubDataCollectorSettings, lambda: StubDataCollectorSettings())
    builder.singleton(UnicornDataCollectorSettings, lambda: UnicornDataCollectorSettings())

    if stub:
        builder.singleton(IDataCollector, StubDataCollector)
        builder.singleton(IClassifier, StubClassifier)
        builder.singleton(IT9Predictor, StubT9Predictor)
    else:
        builder.singleton(IDataCollector, UnicornDataCollector)
        builder.singleton(IClassifier, Classifier)
        builder.singleton(IT9Predictor, T9Predictor)

    builder.singleton(IEpochGetter, EpochGetter)
    builder.singleton(IFlashingStrategy, SquareSingleCharacterFlashingStrategy)
    builder.singleton(IChatGptPredictor, ChatGptPredictor)
    builder.singleton(ISuggestionsGetter, SuggestionsGetter)

    builder.singleton(IStateManager, StateManager, shutdown_event=Dependency(SpellerContainerKey.SHUTDOWN_EVENT))
    builder.singleton(ISequenceHandler, SequenceHandler)

    builder.singleton(ICommandDecoder, CommandDecoder)

    builder.singleton(SpellerRunner, SpellerRunner)
    builder.singleton(SpellerView, SpellerView)

    return builder.build()
