from enum import StrEnum
import signal
from threading import Event
from independency import Container, ContainerBuilder
from independency.container import Dependency

from preprocessing.model import Model
from preprocessing.epoch_collector import EpochCollector
from preprocessing.preprocessor import Preprocessor
from preprocessing.settings import EpochCollectorSettings, ModelSettings, PreprocessorSettings
from speller.data_aquisition.data_collector import IDataCollector, StubDataCollector, UnicornDataCollector
from speller.data_aquisition.epoch_getter import EpochGetter, IEpochGetter
from speller.data_aquisition.recorder import IRecorder, Recorder
from speller.monitoring.monitoring_collector import IMonitoringCollector, MonitoringCollector
from speller.monitoring.visualizer import MonitoringVisualizer
from speller.prediction.chat_gpt_client import ChatGPTClient
from speller.prediction.chat_gpt_predictor import ChatGptPredictor, IChatGptPredictor
from speller.classification.classifier import Classifier, IClassifier, StubClassifier
from speller.prediction.dictionary import Dictionary, IDictionary
from speller.prediction.suggestions_getter import ISuggestionsGetter, SuggestionsGetter
from speller.prediction.t9_predictor import IT9Predictor, T9Predictor
from speller.secrets_settings import ChatGPTSecretsSettings
from speller.session.command_decoder import CommandDecoder, ICommandDecoder
from speller.session.flashing_strategy import IFlashingStrategy, SquareSingleCharacterFlashingStrategy
from speller.session.sequence_handler import ISequenceHandler, SequenceHandler
from speller.session.speller_runner import SpellerRunner
from speller.session.state_manager import IStateManager, StateManager
from speller.settings import ChatGPTSettings, DictionarySettings, ExperimentSettings, FilesSettings, LoggingSettings, MonitoringSettings, StateManagerSettings, StrategySettings, StubDataCollectorSettings, UnicornDataCollectorSettings, ViewSettings
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
    builder.singleton(ExperimentSettings, lambda: ExperimentSettings())
    builder.singleton(FilesSettings, lambda: FilesSettings())
    builder.singleton(ViewSettings, lambda: ViewSettings())
    builder.singleton(LoggingSettings, lambda: LoggingSettings())
    builder.singleton(StateManagerSettings, lambda: StateManagerSettings())
    builder.singleton(DictionarySettings, lambda: DictionarySettings())
    builder.singleton(ChatGPTSettings, lambda: ChatGPTSettings())
    builder.singleton(ChatGPTSecretsSettings, lambda: ChatGPTSecretsSettings())

    builder.singleton(IRecorder, Recorder)

    if stub:
        builder.singleton(StubDataCollectorSettings, lambda: StubDataCollectorSettings())
        builder.singleton(IDataCollector, StubDataCollector)
    else:
        builder.singleton(UnicornDataCollectorSettings, lambda: UnicornDataCollectorSettings())
        builder.singleton(IDataCollector, UnicornDataCollector)

    builder.singleton(IClassifier, StubClassifier)

    builder.singleton(IDictionary, Dictionary)
    builder.singleton(IT9Predictor, T9Predictor)
    
    builder.singleton(ChatGPTClient, ChatGPTClient)
    builder.singleton(IChatGptPredictor, ChatGptPredictor)

    builder.singleton(IEpochGetter, EpochGetter)
    builder.singleton(IFlashingStrategy, SquareSingleCharacterFlashingStrategy)
    builder.singleton(ISuggestionsGetter, SuggestionsGetter)

    builder.singleton(IStateManager, StateManager, shutdown_event=Dependency(SpellerContainerKey.SHUTDOWN_EVENT))
    builder.singleton(ISequenceHandler, SequenceHandler)

    builder.singleton(ICommandDecoder, CommandDecoder)

    builder.singleton(SpellerRunner, SpellerRunner)
    builder.singleton(SpellerView, SpellerView)

    return builder.build()


def get_monitoring_container(stub: bool = True, file: bool = False) -> Container:
    builder = ContainerBuilder()

    builder.singleton(MonitoringSettings, lambda: MonitoringSettings())

    if stub:
        if file:
            raise NotImplemented('No stub file data collector!')
        else:
            builder.singleton(StubDataCollectorSettings, lambda: StubDataCollectorSettings())
            builder.singleton(IDataCollector, StubDataCollector)
    else:
        builder.singleton(UnicornDataCollectorSettings, lambda: UnicornDataCollectorSettings())
        builder.singleton(IDataCollector, UnicornDataCollector)

    builder.singleton(IMonitoringCollector, MonitoringCollector)
    builder.singleton(MonitoringVisualizer, MonitoringVisualizer)

    return builder.build()


def get_model_container() -> Container:
    builder = ContainerBuilder()

    builder.singleton(FilesSettings, lambda: FilesSettings())
    builder.singleton(PreprocessorSettings, lambda: PreprocessorSettings())
    builder.singleton(EpochCollectorSettings, lambda: EpochCollectorSettings())
    builder.singleton(ModelSettings, lambda: ModelSettings())

    builder.singleton(Preprocessor, Preprocessor)
    builder.singleton(EpochCollector, EpochCollector)
    builder.singleton(Model, Model)

    return builder.build()
