import abc
from collections import defaultdict
import logging
import random
from typing import Sequence


logger = logging.getLogger(__name__)
    

ItemPositionType = tuple[int, int]
FlashingListType = Sequence[ItemPositionType]
FlashingSequenceType = Sequence[FlashingListType]


class IFlashingStrategy(abc.ABC):
    @abc.abstractmethod
    def get_flashing_sequence(self) -> FlashingSequenceType:
        pass

    @abc.abstractmethod
    def predict_item_position(self, flashing_sequence: FlashingSequenceType, probabilities: list[float]) -> ItemPositionType:
        pass


class SquareRowColumnFlashingStrategy(IFlashingStrategy):
    def __init__(self, size: int):
        self._size = size
    
    def get_flashing_sequence(self) -> FlashingSequenceType:
        rows_numbers = list(range(self._size))
        columns_numbers = list(range(self._size))
        random.shuffle(rows_numbers)
        random.shuffle(columns_numbers)
        sequence = []
        for row_number, column_number in zip(rows_numbers, columns_numbers):
            sequence.append(
                tuple((row_number, j) for j in range(self._size))
            )
            sequence.append(
                tuple((i, column_number) for i in range(self._size))
            )

        return sequence
    
    def predict_item_position(self, flashing_sequence: FlashingSequenceType, probabilities: list[float]) -> ItemPositionType:
        accumulators = (defaultdict(float), defaultdict(float))  # (rows_probabilities_by_row_number, columns_probabilities_by_column_number)

        for i, flashing_list in enumerate(flashing_sequence):
            number = flashing_list[0][i % 2]
            accumulators[i % 2][number] += probabilities[i]
        
        return (
            max(accumulators[0], key=accumulators[0].__getitem__),
            max(accumulators[1], key=accumulators[1].__getitem__),
        )


# f = SquareRowColumnFlashingStrategy(3)

# g = f.flash()
# for _ in range(6):
#     print(next(g))
