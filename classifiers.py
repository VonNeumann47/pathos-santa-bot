import re
from string import punctuation

from pymorphy2 import MorphAnalyzer
from razdel import tokenize

from patterns import (
    GREET_PATTERNS, EASTER_PATTERNS, PERSONAL_PATTERNS, QUESTION_PATTERNS,
)


PUNCTUATION = set(punctuation) - {'-'}
MORPH = MorphAnalyzer()

with open('swears.txt', 'r') as file:
    SWEARS = file.read().splitlines()

MEDIA_TYPES = [
    'audio', 'document', 'photo', 'sticker', 'video', 'video_note',
    'voice', 'location', 'contact', 'pinned_message',
]


def fast_preprocess(text: str) -> str:
    for c in PUNCTUATION:
        text = text.replace(c, f' {c} ')
    text = text.lower().replace('ё', 'е').replace('  ', ' ').strip()
    return text


def is_greeting(text: str) -> bool:
    processed = fast_preprocess(text)
    return any(
        re.search(pattern, processed) is not None
        for pattern in GREET_PATTERNS
    )


def is_imperative(text: str) -> bool:
    for token in tokenize(fast_preprocess(text)):
        parse = MORPH.parse(token.text)[0]
        if 'impr' in parse.tag:
            return True
    return False


def is_easter(text: str) -> bool:
    processed = fast_preprocess(text)
    return any(
        re.search(pattern, processed) is not None
        for pattern in EASTER_PATTERNS
    )


def is_toxic(text: str) -> bool:
    for token in tokenize(fast_preprocess(text)):
        if token.text in SWEARS:
            return True
    return False


def is_personal(text: str) -> bool:
    processed = fast_preprocess(text)
    return any(
        re.search(pattern, processed) is not None
        for pattern in PERSONAL_PATTERNS
    )


def is_question(text: str) -> bool:
    processed = fast_preprocess(text)
    return any(
        re.search(pattern, processed) is not None
        for pattern in QUESTION_PATTERNS
    )
