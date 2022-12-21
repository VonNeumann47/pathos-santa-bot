from datetime import datetime as dt
import json
from logging import Formatter, getLogger, INFO, Logger, StreamHandler
import os
from pathlib import Path
from random import random, seed, shuffle
import re
from threading import Lock
from time import sleep
from typing import Any, Dict, List, Optional
import unicodedata

from pymorphy2 import MorphAnalyzer
from razdel import sentenize
from requests.exceptions import ConnectionError
from vedis import Vedis
import wikipedia as wiki
from yadisk import YaDisk
from yadisk.exceptions import ConflictError

from tasks import Task, TASKS, MAX_ATTEMPTS


MORPH = MorphAnalyzer()


def get_logger(name: str) -> Logger:
    log_format = Formatter('[%(asctime)s] [%(levelname)s] - %(message)s')
    logger = getLogger(name)
    logger.setLevel(INFO)

    handler = StreamHandler()
    handler.setLevel(INFO)
    handler.setFormatter(log_format)
    logger.addHandler(handler)

    return logger


BOT_TOKEN = os.environ.get('BOT_TOKEN', '@trash')
YADISK_TOKEN = os.environ.get('YADISK_TOKEN', '#trash')

logger = get_logger('@pathos_santa_bot')
ya = YaDisk(token=YADISK_TOKEN)
lock = Lock()

YADISK_PATH = '/pathos_santa_bot'
DB_PATH = 'history.db'
LOG_PATH = 'userlogs.log'
TEXT_PATHS = [
    'texts/python.txt',
    'texts/cats.txt',
    'texts/nlp.txt',
    'texts/sweet.txt',
]

MAX_HISTORY = 100
CLOUD_SLEEP_MINS = 10
MAX_QUESTION_LEN = 256
NGRAM_PROBABILITY = 0.7
STICKER_PROBABILITY = 0.1


def roll_dice(prob: float) -> bool:
    return random() < prob


def file_download(filename: str) -> None:
    if not Path(filename).exists():
        ya.download(f'{YADISK_PATH}/{filename}', filename)


def file_upload(filename: str) -> None:
    if Path(filename).exists():
        yapath = f'{YADISK_PATH}/{filename}'
        if ya.exists(yapath):
            ya.remove(yapath, permanently=True)
            sleep(0.1)
        try:
            ya.upload(filename, yapath)
        except ConflictError:
            logger.info('ConflictError :(')


def cloud_download_files() -> None:
    with lock:
        Path('texts').mkdir(exist_ok=True)
        for filename in (LOG_PATH, DB_PATH, *TEXT_PATHS):
            if not Path(filename).exists():
                file_download(filename)


def cloud_upload_files() -> None:
    with lock:
        try:
            file_upload(LOG_PATH)
            file_upload(DB_PATH)
        except ConnectionError:
            logger.info('ConnectionError :(')


def log(*args: Any) -> None:
    with lock:
        logger.info(f'Log: {args}')
        with open(LOG_PATH, 'a', encoding='utf-8') as file:
            print(*args, file=file)


class UserState:
    def __init__(self, uid: int, **kwargs: Any):
        self.uid: int = uid
        self.plays: bool = kwargs.get('plays', False)
        self.tasks: List[int] = kwargs.get('tasks', [])
        self.points: int = kwargs.get('points', 0)
        self.attempts: int = kwargs.get('attempts', 0)
        self.history: List[Dict[str, str]] = kwargs.get('history', [])

    def _init_tasks(self) -> None:
        self.tasks = list(range(len(TASKS)))
        seed(self.uid)
        shuffle(self.tasks)

    def to_json(self) -> str:
        return json.dumps({
            'uid': self.uid,
            'plays': self.plays,
            'tasks': self.tasks,
            'points': self.points,
            'attempts': self.attempts,
            'history': self.history,
        })

    @classmethod
    def from_json(self, js: str) -> 'UserState':
        kwargs = json.loads(js)
        return UserState(**kwargs)

    def append_history(self, **kwargs: str) -> None:
        self.history.append(kwargs)
        if len(self.history) > MAX_HISTORY:
            self.history.pop(0)

    def get_task(self) -> Task:
        return TASKS[self.tasks[-1]]

    def switch_task(self) -> bool:
        self.tasks.pop()
        if self.tasks:
            self.attempts = MAX_ATTEMPTS
            return True
        return False

    def has_tasks(self) -> bool:
        return self.tasks

    def is_playing(self) -> bool:
        return self.plays

    def start_play(self) -> None:
        self.plays = True
        self.attempts = MAX_ATTEMPTS
        self._init_tasks()


def save_history(uid: int, state: UserState) -> None:
    with lock:
        with Vedis(DB_PATH) as db:
            db[uid] = state.to_json()


def read_history(uid: int) -> UserState:
    with lock:
        with Vedis(DB_PATH) as db:
            if uid not in db:
                state = UserState(uid)
                db[uid] = state.to_json()
                return state
            js = db[uid].decode()
            return UserState.from_json(js)


def fetch_wiki(question: str, uid: int) -> Optional[wiki.wikipedia.WikipediaPage]:
    time = dt.now().strftime('%d %b %Y %H:%M:%S')
    results = []
    page = None

    try:
        results = wiki.search(question)
    except json.decoder.JSONDecodeError:
        log(uid, f'{time=}', '[wiki-json-exc]', f'{question=}')
    except wiki.exceptions.WikipediaException:
        log(uid, f'{time=}', '[wiki-search-exc]', f'{question=}')
    except:
        log(uid, f'{time=}', '[wiki-unkn-exc-search]', f'{question=}')
    finally:
        if not results:
            log(uid, f'{time=}', '[wiki-no-res]', f'{question=}')

    if not results:
        return None

    try:
        page = wiki.page(results[0])
        log(uid, f'{time=}', '[wiki-found]', f'{question=}')
    except wiki.exceptions.DisambiguationError as err:
        try:
            page = wiki.page(err.options[0])
            log(uid, f'{time=}', '[wiki-resolved]', f'{question=}')
        except (wiki.exceptions.DisambiguationError, wiki.page.PageError):
            log(uid, f'{time=}', '[wiki-exc-double]', f'{question=}')
        except:
            log(uid, f'{time=}', '[wiki-unkn-exc-double]', f'{question=}')
    except:
        log(uid, f'{time=}', '[wiki-unkn-exc-page]', f'{question=}')
    return page


def get_first_sentence(summary: str) -> str:
    sents = list(map(lambda s: s.text, sentenize(summary)))
    try:
        answer = sents[0]
        idx = 0
        while re.search(r'\([^)]*$|«[^»]*$', answer) is not None:
            idx += 1
            answer = ' '.join((answer, sents[idx]))
        return answer
    except IndexError:
        return ''


def postprocess_answer(text: str) -> str:
    text = ''.join(c for c in text if not unicodedata.combining(c))
    for c in '*_':
        text = text.replace(c, fr'\{c}')
    return text.strip()


def is_playing(uid: int) -> bool:
    state = read_history(uid)
    return state.is_playing() and state.has_tasks()
