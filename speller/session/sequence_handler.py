import abc
from speller.classification.classifier import IClassifier
from speller.data_aquisition.epoch_getter import IEpochGetter
from speller.session.flashing_strategy import FlashingSequenceType, IFlashingStrategy, ItemPositionType


class ISequenceHandler(abc.ABC):
    @abc.abstractmethod
    def get_flashing_sequence(self) -> FlashingSequenceType:
        pass
    
    @abc.abstractmethod
    def handle_sequence(self, flashing_sequence: FlashingSequenceType) -> ItemPositionType:
        pass


class SequenceHandler(ISequenceHandler):
    def __init__(self, epoch_getter: IEpochGetter, classifier: IClassifier, flashing_strategy: IFlashingStrategy):
        self._epoch_getter = epoch_getter
        self._classifier = classifier
        self._flashing_strategy = flashing_strategy

    def get_flashing_sequence(self) -> FlashingSequenceType:
        return self._flashing_strategy.get_flashing_sequence()

    def handle_sequence(self, flashing_sequence: FlashingSequenceType) -> ItemPositionType:
        epoch_generator = self._epoch_getter.get_epochs(len(flashing_sequence))
        probabilities = [self._classifier.classify(epoch) for epoch in epoch_generator]
        if len(probabilities) < len(flashing_sequence):
            probabilities.extend([0.]*(len(flashing_sequence) - len(probabilities)))

        return self._flashing_strategy.predict_item_position(flashing_sequence, probabilities)



        