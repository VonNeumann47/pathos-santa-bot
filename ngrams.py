from bisect import bisect_left
from collections import Counter, defaultdict
from pathlib import Path
import random
from tqdm import tqdm
from typing import Any, Callable, Dict, Iterable, List, Tuple

from nltk.util import ngrams
import numpy as np
from pymorphy2 import MorphAnalyzer
import razdel

from utils import MORPH


START = '<S>'
UNK = '<UNK>'


def tokenize(text: str) -> List[str]:
    tokens = []
    for sentence in razdel.sentenize(text):
        tokens.extend([START] + [
            word.text.lower()
            for word in razdel.tokenize(sentence.text)
        ])
    return tokens


def pad_ngram(line: List[str], n: int, until: int = None) -> Tuple[str, ...]:
    if not n:
        return ()
    ngram = line[:until][-n:]
    ngram = [UNK] * (n - len(ngram)) + ngram
    return tuple(ngram)


def count_ngrams(lines: Iterable[str],
                 n: int,
                 verbose: bool = True,
                 ) -> Dict[Tuple[str, ...], Dict[str, int]]:
    counts = defaultdict(Counter)
    if n == 1:
        empty = tuple()
        counts[empty] = Counter(
            token
            for line in tqdm(lines, desc=f'Counting 1-grams', disable=not verbose)
            for token in tokenize(line)
        )
        return counts

    for line in tqdm(lines, desc=f'Counting {n}-grams', disable=not verbose):
        tokens = tokenize(line)
        for idx, next_token in enumerate(tokens):
            prefix = pad_ngram(tokens, n - 1, idx)
            counts[prefix][next_token] += 1
    return counts


class NgramLM:
    def __init__(self, n: int, delta: float = 1, verbose: bool = True):
        assert n >= 1
        self.n = n
        self.delta = delta
        self.verbose = verbose

    def fit(self, lines: List[str]) -> 'NgramLM':
        counts = defaultdict(Counter)
        for k in range(1, self.n + 1):
            counts.update(count_ngrams(lines, k, verbose=self.verbose))

        self.probs = defaultdict(Counter)
        self.vocab = set(
            token
            for nexts in counts.values()
            for token in nexts
        )

        for prefix, nexts in tqdm(
                counts.items(),
                desc=f'Initializing {self.n}-gram LM',
                total=len(counts),
                disable=not self.verbose):
            denom = sum(nexts.values()) + self.delta * len(self.vocab)
            self.probs[prefix] = {
                token: (cnt + self.delta) / denom
                for token, cnt in nexts.items()
            }
        return self

    def get_possible_next_tokens(self, prefix: List[str]) -> Dict[str, float]:
        ngram = pad_ngram(prefix, self.n - 1)
        probs = self.probs.get(ngram)
        while ngram and probs is None:
            ngram = ngram[1:]
            probs = self.probs.get(ngram)
        return probs or UNK


Strategy = Callable[..., str]

def generate_nucleus(model: NgramLM,
                     prefix: List[str],
                     temperature: float = 0.9,
                     top_p: float = 0.85) -> str:
    distribution = model.get_possible_next_tokens(prefix)
    if not distribution:
        return UNK

    tokens, weights = map(
        lambda arr: np.array(list(arr)),
        zip(*distribution.items()),
    )
    if temperature != 1:
        weights = np.power(weights, 1 / temperature)
        weights /= weights.sum()
    idx = max(1, bisect_left(np.cumsum(weights), top_p))

    tokens = tokens[:idx]
    probs = weights[:idx]
    probs /= probs.sum()
    return random.choices(tokens, probs)[0]


def postprocess_tokens(tokens: List[str]) -> str:
    tokens = [
        token
        for token in tokens
        if token != UNK
    ]

    last_start = None
    for idx, (prev_token, token) in enumerate(zip(tokens, tokens[1:]), start=1):
        if token == START:
            last_start = idx
            continue
        if prev_token in (START, '.', '!', '?', '...', '…'):
            tokens[idx] = token.capitalize()
            continue

        score = 0
        for parse in MORPH.parse(token):
            for tag in (
                    'Geox',
                    'Name',
                    'Surn',
                    'Patr',
                    'Orgn',
                    'Trad',
                    'Init',
                ):
                if tag in parse.tag:
                    score += parse.score
                    break
        if score >= 0.5:
            tokens[idx] = token.capitalize()

    output = ' '.join(
        token
        for token in tokens[:last_start]
        if token != START
    )
    for ch in '.,!?:;)]}»…':
        output = output.replace(f' {ch}', ch)
    for ch in '([{«':
        output = output.replace(f'{ch} ', ch)
    return output


class Talker:
    def __init__(self,
                 strategy: Strategy = generate_nucleus,
                 **model_params: Any):
        self.model = NgramLM(**model_params)
        self.strategy = strategy

    def fit(self, *files: Path) -> 'Talker':
        lines = []
        for filename in files:
            path = Path(filename)
            if path.exists() and path.is_file():
                with open(path, 'r', encoding='utf-8') as file:
                    lines += file.readlines()
        self.model.fit(lines)
        return self

    def talk(self,
             prompt: str = '',
             max_len: int = 50,
             random_state: int = None,
             **gen_params: Any) -> str:
        random.seed(random_state)
        np.random.seed(random_state)
        tokens = tokenize(prompt)
        while len(tokens) < max_len:
            next_token = self.strategy(self.model, tokens, **gen_params)
            tokens.append(next_token)
        return postprocess_tokens(tokens)


if __name__ == '__main__':
    talker = Talker(n=4, delta=1e-2)
    from utils import TEXT_PATHS
    talker.fit(*TEXT_PATHS)
