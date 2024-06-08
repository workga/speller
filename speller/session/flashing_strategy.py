import abc
from collections import defaultdict
from itertools import product
import logging
import random

from speller.data_aquisition.recorder import IRecorder
from speller.session.entity import FlashingSequenceType, ItemPositionType
from speller.settings import StrategySettings


logger = logging.getLogger(__name__)
    

class IFlashingStrategy(abc.ABC):
    @abc.abstractmethod
    def get_flashing_sequence(self, repetitions_count: int) -> FlashingSequenceType:
        pass

    @abc.abstractmethod
    def predict_item_position(self, flashing_sequence: FlashingSequenceType, probabilities: list[float]) -> ItemPositionType:
        pass


class SquareRowColumnFlashingStrategy(IFlashingStrategy):
    def __init__(self, settings: StrategySettings):
        self._settings = settings
    
    def get_flashing_sequence(self, repetitions_count: int) -> FlashingSequenceType:
        rows_numbers = list(range(self._settings.keyboard_size))
        columns_numbers = list(range(self._settings.keyboard_size))

        sequence = []
        for _ in range(repetitions_count):
            random.shuffle(rows_numbers)
            random.shuffle(columns_numbers)
            for row_number, column_number in zip(rows_numbers, columns_numbers):
                sequence.append(
                    tuple((row_number, j) for j in range(self._settings.keyboard_size))
                )
                sequence.append(
                    tuple((i, column_number) for i in range(self._settings.keyboard_size))
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


class SquareSingleCharacterFlashingStrategy(IFlashingStrategy):
    def __init__(self, strategy_settings: StrategySettings, recorder: IRecorder):
        self._strategy_settings = strategy_settings
        self._recorder = recorder
   
    def _generate_flat_sequence(self, repetitions_count: int) -> list[int]:
        size = self._strategy_settings.keyboard_size

        result = []
        items = list(range(size**2))
        for _ in range(repetitions_count):
            random.shuffle(items)
            if result and result[-1] == items[0]:
                items[0], items[1] = items[1], items[0]
            result += items
        
        return result
    
    def get_flashing_sequence(self, repetitions_count: int) -> FlashingSequenceType:
        sequence = [[(i // 4, i % 4)] for i in self._generate_flat_sequence(repetitions_count)]
        self._recorder.record_flashing_sequence(sequence)
        return sequence
    
    def predict_item_position(self, flashing_sequence: FlashingSequenceType, probabilities: list[float]) -> ItemPositionType:
        accumulators = [0] * (self._strategy_settings.keyboard_size ** 2)

        for flashing_list, probability in zip(flashing_sequence, probabilities):
            for i, j in flashing_list:
                accumulators[i * 4 + j] += probability

        lines = []
        for i in range(self._strategy_settings.keyboard_size):
            row = accumulators[i * self._strategy_settings.keyboard_size: (i + 1) * self._strategy_settings.keyboard_size]
            lines.append('\t'.join(map(str, row)))
        logger.info("Probabilities distribution:\n%s", '\n'.join(lines))

        index = max(range(len(accumulators)), key=accumulators.__getitem__)
        return index // 4, index % 4
    
    # @staticmethod
    # def generate_flat_groups(size: int, min_dist: int) -> list[list[int]]:
    #     # Нужно научиться генерировать последовательности кратной длины с сохранением min_dist
    #     # Сейчас слишком предсказуемо, потому что один и тот же элемент встречается только в разных половинах)
    #     s1 = set(range(size**2))

    #     center = random.sample(list(s1), size * min_dist * 2)
    #     left_part = list(s1 - set(center[: size * min_dist]))
    #     right_part = list(s1 - set(center[size * min_dist:]))

    #     random.shuffle(left_part)
    #     random.shuffle(right_part)

    #     result = left_part + center + right_part
    #     return [result[i * size: (i + 1) * size] for i in range(size * 2)]
    
    # def generate_flat_groups(self) -> list[list[int]]:
    #     size = self._strategy_settings.keyboard_size
    #     repetitions = self._strategy_settings.repetitions_count

    #     result = []
    #     for _ in range(repetitions):
    #         random.shuffle(items)
    #         result += items
        
    #     groups = [result[i * size: (i + 1) * size] for i in range(size * repetitions)]
    #     random.shuffle(groups)
    #     return groups
    
    # def generate_flat_groups(self) -> list[list[int]]:
    #     # проблема - у двух выбранных групп могут быть общие элементы, тогда не понять какой элемент выбран
    #     # нужно все таки адаптировать chekerboard, т к она дает гарантии RC но без недостатков RC
    #     size = self._strategy_settings.keyboard_size
    #     repetitions = self._strategy_settings.repetitions_count

    #     assert size % 2 == 0, "This strategy does not work with odd keyboard sizes!"

    #     even_items = [i * 4 + j for i in range(size) for j in range(size) if (i + j) % 2 == 0]
    #     odd_items = [i * 4 + j for i in range(size) for j in range(size) if (i + j) % 2 == 1]

    #     groups = []
    #     even_groups = []
    #     odd_groups = []
    #     for _ in range(repetitions):
    #         # тут шафлим чтобы сгенерировать разные группы для каждого повторения
    #         random.shuffle(even_items)
    #         random.shuffle(odd_items)
    #         even_groups += [even_items[i * size: (i + 1) * size] for i in range(size // 2)]
    #         odd_groups += [odd_items[i * size: (i + 1) * size] for i in range(size // 2)]
    #     # тут шафлим, чтобы не было равномерного распределения
    #     # (иначе один и тот же элемент встречается ровно один раз внутри одного повторения - предсказуемо)
    #     # при этом сохраняется min_dist=1
    #     random.shuffle(even_groups)
    #     random.shuffle(odd_groups)
        
    #     for even_group, odd_group in zip(even_groups, odd_groups):
    #         groups += even_group, odd_group

    #     return groups
