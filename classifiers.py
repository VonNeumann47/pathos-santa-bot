import re
from string import punctuation

from pymorphy2 import MorphAnalyzer
from razdel import tokenize

from patterns import (
    GREET_PATTERNS, EASTER_PATTERNS, PERSONAL_PATTERNS, QUESTION_PATTERNS,
)
from utils import MORPH


PUNCTUATION = set(punctuation) - {'-'}

with open('swears.txt', 'r', encoding='utf-8') as file:
    SWEARS = set(file.read().splitlines())
with open('swear_lemmas.txt', 'r', encoding='utf-8') as file:
    SWEARS |= set(file.read().splitlines())

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
        word = token.text
        lemma = MORPH.parse(word)[0].normal_form
        if word in SWEARS or lemma in SWEARS:
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
