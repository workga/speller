import abc
import logging
from pathlib import Path

from marisa_trie import Trie, RecordTrie

from speller.settings import DictionarySettings


logger = logging.getLogger(__name__)


class IDictionary(abc.ABC):
    @abc.abstractmethod
    def get_words(self, prefixes: list[str], max_words: int) -> list[str]:
        pass

    @abc.abstractmethod
    def get_possible_prefixes(self, prefixes: list[str]) -> list[str]:
        pass


class Dictionary(IDictionary):
    def __init__(self, settings: DictionarySettings):
        self._settings = settings

        with open(Path('./static/words_with_ipm.txt'), 'r') as f:
            self._primary_trie = RecordTrie('d', map(self._line_to_item, f.read().splitlines()))

        with open(Path('./static/words_without_ipm.txt'), 'r') as f:
            self._secondary_trie = Trie(f.read().splitlines())

    @staticmethod
    def _line_to_item(line: str) -> tuple[str, tuple[float]]:
        value, key = line.split()[1:]
        return key, (float(value),)
    
    @staticmethod
    def _ipm_from_item(item: tuple[str, tuple[float]]) -> float:
        return item[1][0]
    
    @staticmethod
    def _word_from_item(item: tuple[str, tuple[float]]) -> float:
        return item[0]
    
    def _search_words(self, prefixes: list[str], max_words: int | None = None, only_equal: bool = True) -> list[str]:
        if only_equal:
            primary_items = [
                (prefix, value) for prefix in prefixes if (value := self._primary_trie.get(prefix, None))
            ]
        else:
            primary_items = []
            for prefix in prefixes:
                primary_items.extend(self._primary_trie.items(prefix))
        primary_items.sort(key=self._ipm_from_item, reverse=True)
        primary_words = [self._word_from_item(item) for item in primary_items[:max_words]]

        logger.info('Got primary words from dictionary (only_equal=%s): %s', only_equal, primary_words)
        if len(primary_words) == max_words:
            return primary_words
        
        if only_equal:
            if not self._settings.search_equal_words_in_secondary:
                return primary_words
            all_words = [prefix for prefix in prefixes if prefix in self._secondary_trie]
        else:
            all_words = []
            for prefix in prefixes:
                all_words.extend(self._secondary_trie.keys(prefix))
        all_words.sort()
        all_words.sort(key=lambda word: len(word))

        secondary_len = max_words - len(primary_words)
        secondary_words = []
        for word in all_words:
            if word not in primary_words:
                secondary_words.append(word)
                if len(secondary_words) == secondary_len:
                    break

        logger.info('Got secondary words from dictionary (only_equal=%s): %s', only_equal,  secondary_words)
        return primary_words + secondary_words
    
    def get_words(self, prefixes: list[str], max_words: int) -> list[str]:
        # оригинальный Т9 подсказывает только слова с той же длиной, но мы поступим умнее:
        # если слов той же длины нашли меньше, чем нужно, то добавляем слова большей длины
        # + еще есть варианты: искать ли слова той же длины дополнительно в большом словаре без частот или нет
        words = self._search_words(prefixes, max_words, only_equal=True)
        if len(words) == max_words:
            return words
        
        for word in self._search_words(prefixes, max_words, only_equal=False):
            if word not in words:
                words.append(word)
                if len(words) == max_words:
                    break
        
        return words
    
    def _is_prefix_possible(self, prefix: str) -> bool:
        return bool(next(self._secondary_trie.iterkeys(prefix), None))
    
    def get_possible_prefixes(self, prefixes: list[str]) -> list[str]:
        return list(filter(self._is_prefix_possible, prefixes))