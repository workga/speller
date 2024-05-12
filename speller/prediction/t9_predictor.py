import abc
from itertools import islice, product
from typing import Iterator, Sequence

from speller.prediction.dictionary import IDictionary


T9_CHARS = [
    'абвг', 'дежз', 'ийкл', 'мноп', 'рсту', 'фхцч', 'шщъы', 'ьэюя'
]


class IT9Predictor(abc.ABC):
    @abc.abstractmethod
    def get_possible_prefixes(self, prefix: Sequence[int]) -> Sequence[str]:
        pass

    @abc.abstractmethod
    def predict(self, prefix: Sequence[int], max_words: int) -> Sequence[str]:
        pass
    

class T9Predictor(IT9Predictor):
    def __init__(self, dictionary: IDictionary):
        self._dictionary = dictionary
    
    @staticmethod
    def _get_prefixes_as_strings(prefix: Sequence[int]) -> Sequence[str]:
        prefixes_as_chars = product(*[T9_CHARS[i] for i in prefix])
        return [''.join(chars) for chars in prefixes_as_chars]

    def predict(self, prefix: Sequence[int], max_words: int) -> Sequence[str]:
        prefixes_as_strings = self._get_prefixes_as_strings(prefix)
        words = self._dictionary.get_words(prefixes_as_strings, max_words)

        if len(words) < max_words:
            prefixes_as_strings.sort()
            words.extend(prefixes_as_strings[: max_words - len(words)])

        return words

    def get_possible_prefixes(self, prefix: Sequence[int]) -> Sequence[str]:
        prefixes_as_strings = self._get_prefixes_as_strings(prefix)
        return self._dictionary.get_possible_prefixes(prefixes_as_strings)