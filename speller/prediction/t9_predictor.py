import abc
from itertools import islice, product
from typing import Iterator, Sequence

from speller.prediction.dictionary import IDictionary


T9_CHARS = [
    'абвг', 'дежз', 'ийкл', 'мноп', 'рсту', 'фхцч', 'шщъы', 'ьэюя'
]


class IT9Predictor(abc.ABC):
    @abc.abstractmethod
    def predict(self, prefix: Sequence[int], max_words: int) -> Sequence[str]:
        pass
    

class T9Predictor(IT9Predictor):
    def __init__(self, dictionary: IDictionary):
        self._dictionary = dictionary

    def predict(self, prefix: Sequence[int], max_words: int) -> Sequence[str]:
        prefixes_as_chars = product(*[T9_CHARS[i] for i in prefix])
        prefixes_as_strings = [''.join(chars) for chars in prefixes_as_chars]

        words = self._dictionary.get_words(prefixes_as_strings, max_words)

        if len(words) < max_words:
            prefixes_as_strings.sort()
            words.extend(prefixes_as_strings[: max_words - len(words)])

        return words