import abc
from itertools import islice
from typing import Iterator, Sequence


T9_CHARS = [
    'абвг', 'дежз', 'ийкл', 'мноп', 'рсту', 'фхцч', 'шщъы', 'ьэюя'
]


class IT9Predictor(abc.ABC):
    @abc.abstractmethod
    def predict(self, prefix: Sequence[int], max_words: int | None = None) -> Sequence[str]:
        pass


class StubT9Predictor(IT9Predictor):
    def predict(self, prefix: Sequence[int], max_words: int | None = None) -> Sequence[str]:
        def concat_recursivly(prefix: Sequence[int]) -> Iterator[str]:
            if len(prefix) == 0:
                return ""
            elif len(prefix) == 1:
                yield from T9_CHARS[prefix[0]]
            else:
                for char in T9_CHARS[prefix[0]]:
                    for suffix in concat_recursivly(prefix[1:]):
                        yield char + suffix
        
        return list(islice(concat_recursivly(prefix), max_words))
    
class T9Predictor(IT9Predictor):
    def predict(self, prefix: Sequence[int], max_words: int | None = None) -> Sequence[str]:
        return []
    


# p = StubT9Predictor()
# print(p.predict([0, 1, 2], 5))
