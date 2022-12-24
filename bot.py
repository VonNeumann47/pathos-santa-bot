from datetime import datetime as dt
from random import choice
import re
import sys
from threading import Thread
from time import sleep

import telebot as tb
import wikipedia as wiki

from classifiers import (
    MEDIA_TYPES,
    is_greeting, is_imperative, is_easter,
    is_toxic, is_personal, is_question,
)
from fallbacks import (
    LYCEUM_STICKERS, GREETINGS, IMPERATIVES,
    EASTER_ANSWERS, TOXIC_ANSWERS, PERSONAL_ANSWERS,
    QA_START, QA_MIDDLE, QA_END, QA_TOO_LONG, FALLBACKS,
)
from ngrams import Talker
from tasks import TASKS, MAX_ATTEMPTS
from utils import *


class ExceptionHandler:
    def handle(self, exc_info, *args, **kwargs):
        if isinstance(exc_info, tb.apihelper.ApiTelegramException):
            log(
                "One of the threads couldn't capture the ownership "
                # "over the Telegram bot. It's gonna sleep forever..."
                "over the Telegram bot. It's gonna exit now..."
            )
            sys.exit(0)
            # while True:
            #     sleep(1)


bot = tb.TeleBot(
    BOT_TOKEN,
    exception_handler=ExceptionHandler(),
)


# Media handler
@bot.message_handler(content_types=MEDIA_TYPES)
def media_content(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    cloud_download_files()

    sticker = choice(LYCEUM_STICKERS)

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[media]', f'{sticker=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='media', sticker=sticker)
    save_history(uid, state)

    bot.send_sticker(uid, sticker)


# Text handlers
@bot.message_handler(func=lambda msg: len(msg.text) > MAX_QUESTION_LEN)
def too_long(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text
    cloud_download_files()

    answer = choice(QA_TOO_LONG)
    text = f'{text[:MAX_QUESTION_LEN]}<...>'

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[too-long]', f'{text=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='too-long', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(func=lambda msg: is_toxic(msg.text))
def toxic_response(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text
    cloud_download_files()

    answer = choice(TOXIC_ANSWERS)

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[toxic]', f'{text=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='toxic', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(func=lambda msg: is_easter(msg.text))
def easter_response(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text
    cloud_download_files()

    answer = choice(EASTER_ANSWERS)

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[easter]', f'{text=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='easter', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(func=lambda msg: is_imperative(msg.text))
def imperative_response(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text
    cloud_download_files()

    answer = choice(IMPERATIVES)

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[imperative]', f'{text=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='imperative', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(func=lambda msg: is_personal(msg.text))
def personal_response(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text

    answer = choice(PERSONAL_ANSWERS)

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[personal]', f'{text=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='personal', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(func=lambda msg: is_greeting(msg.text))
def greeting_response(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text
    cloud_download_files()

    answer = choice(GREETINGS)

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[greet]', f'{text=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='greet', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(func=lambda msg: is_question(msg.text))
def qa_response(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    question = msg.text
    cloud_download_files()

    if len(question) > MAX_QUESTION_LEN:
        answer = choice(QA_TOO_LONG)
        question = f'{question[:MAX_QUESTION_LEN]}<...>'
    else:
        bot.send_message(uid, 'Хмм...', parse_mode='markdown')
        page = fetch_wiki(question, uid)
        answer = ''
        if page is not None:
            sentence = get_first_sentence(page.summary)
            answer = postprocess_answer(sentence)

        if answer:
            answer = ''.join((
                f'{answer}\n', choice(QA_START), choice(QA_MIDDLE), choice(QA_END),
            ))

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    if answer:
        bot.send_message(uid, answer, parse_mode='markdown')
    else:
        answer = choice(LYCEUM_STICKERS)
        bot.send_sticker(uid, answer)

    log(uid, f'{time=}', '[qa]', f'{question=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='qa', text=question, answer=answer)
    save_history(uid, state)


# Commands
@bot.message_handler(commands=['help'])
def start_dialog(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    answer = (
        'Котя устал, котя запутался? Я помогу, не парься ^^\n'
        'Пиши `/start`, если хочешь, чтобы я поприветствовал тебя. Можно повторять, хотя это и бесит.\n'
        'Жми `/play`, чтобы поиграть. Но помни: поиграть можно лишь один раз, и прервать игру не выйдет!\n'
        'Если ты в игре, пиши `/repeat`, чтобы я скопипастил тебе вопрос и ты не листал вверх, коть\n'
        'Милашик, забыл, сколько баллов у тебя? Пиши `/score`. Только не часто ^^\n'
        'А ещё ты можешь мне просто _написать_. И мы поболтаем :)\n'
        'Масянь, я очень много всего знаю! Люблю питон, NLP, искусственный интеллект, кошечек и кондитерку.\n'
        'Если ты тоже пушистый, умный, безумный красавчик и/или просто котя и хочешь поболтать, то вот он я :)\n'
        'Пиши мне почаще. Я всё логирую ^^\n'
        '*Точно*, пока не забыл: если я крашнусь, то сразу пиши моему владельцу. Он у меня просто топчик ^^\n'
        'Мррр :)'
    )

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[help]')
    state = read_history(uid)
    state.append_history(uid=uid, tag='help', answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(commands=['start'])
def start_dialog(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    answer = (
        'Муррр, кто это тут у нас?\n'
        'Привет! Я Пафнутий. Можно просто *Пафос* ^^\n'
        'Ты можешь просто побалакать со мной. А можешь побороться за звание лучшего питониста, которого знает мой владелец!\n'
        'Пока что этот крутой статус ношу я. Да! Коты тоже умеют программировать!\n'
        'Думаешь, что ты лучше? Жмякай /play. Рискни.\n'
        'Но помни: сыграть ты сможешь лишь *один раз*. Я жёсткий кот, ясно?\n'
        'А вообще я милаш и люблю болтать ^^\n'
        'Мррр :)'
    )

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[start]')
    state = read_history(uid)
    state.append_history(uid=uid, tag='start', answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(commands=['play'])
def play_handler(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    cloud_download_files()
    state = read_history(uid)

    if state.is_playing():
        answer = (
            'Ты ведь уже начинал игру. Меня не проведёшь!\n'
            'Я _котик_, конечно, но я не тупенький. Я просто маленький.'
        )
    else:
        word_attempts = MORPH \
            .parse('попытка')[0] \
            .inflect({'plur', 'nomn'}) \
            .make_agree_with_number(MAX_ATTEMPTS) \
            .word
        word_tasks = MORPH \
            .parse('задачка')[0] \
            .inflect({'plur', 'nomn'}) \
            .make_agree_with_number(len(TASKS)) \
            .word
        answer = (
            'Ну, ладненько, человек. Ты сам напросился...\n'
            f'Я покажу тебе {len(TASKS)} {word_tasks} по питону. '
            f'Для решения каждой тебе будет дано {MAX_ATTEMPTS} {word_attempts} \n'
            'Если отвечаешь правильно, получаешь баллы. Нет -- не расстраивайся. '
            '_Просто ты не шаришь в питоне_ :)\n'
            'Когда ответишь на *все* вопросы, найди моего владельца. '
            'Во-первых, он классный: с ним можно поболтать. А во-вторых, хватит и первого.\n'
            'Удачи! Будь умным котей ^^\n'
            'Ты вполне можешь пользоваться _чем угодно_. Но это не поможет...\n'
            'Во всех задачах считай, что у меня на компе бесконечно много памяти, если что.\n'
            'И да: юзай Python 3.3+ в реализации CPython (стандартный питон крч).\n'
            'Мяу ^^'
        )
        bot.send_message(uid, answer, parse_mode='markdown')

        state.start_play()
        task = state.get_task()
        word_points = MORPH \
            .parse('балл')[0] \
            .inflect({'plur', 'nomn'}) \
            .make_agree_with_number(task.points) \
            .word
        answer = (
            'Котя, напрягись чутка! Задачки подъехали ^^\n'
            f'Сейчас твоя задачка стоит *{task.points} {word_points}* и формулируется так.\n\n'
            f'{task.formulate()}'
        )

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    task_id = state.tasks[-1] if state.tasks else None
    log(uid, f'{time=}', '[play]', task_id)
    state.append_history(uid=uid, tag='play', answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(commands=['repeat'])
def repeat_task(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    cloud_download_files()
    state = read_history(uid)

    if not state.is_playing() or not state.has_tasks():
        answer = (
            'Коть, иди поешь! Ты же не в игре :)\n'
            'Жми /play, чтобы поиграть. Если, конечно, не играл уже...'
        )
    else:
        task = state.get_task()
        word_points = MORPH \
            .parse('балл')[0] \
            .inflect({'plur', 'nomn'}) \
            .make_agree_with_number(task.points) \
            .word
        answer = (
            'Ой, ладно, *ладно*! Угомонись. Сейчас повторю условие. Но *только* потому что я добряк безмерный :)\n'
            f'Сейчас твоя задачка стоит *{task.points} {word_points}* и формулируется так.\n\n'
            f'{task.formulate()}'
        )

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    task_id = state.tasks[-1] if state.tasks else None
    log(uid, f'{time=}', '[repeat]', task_id)
    state.append_history(uid=uid, tag='repeat', answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(commands=['score'])
def ask_score(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    cloud_download_files()
    state = read_history(uid)

    word_points = MORPH \
        .parse('балл')[0] \
        .inflect({'plur', 'nomn'}) \
        .make_agree_with_number(state.points) \
        .word
    answer = (
        'Повторяю. Но *только* потому что я добряк безмерный :)\n'
        f'У тебя сейчас {state.points} {word_points}'
    )

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[score]', f'{answer=}')
    state.append_history(uid=uid, tag='repeat', answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


@bot.message_handler(func=lambda msg: msg.text.startswith('/'))
def bad_command(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text
    cloud_download_files()

    answer = (
        'Бусь, ты опечатался! Я такой команды не знаю.\n'
        'Впредь будь осторожнее: я могу _обидеться_...'
    )

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[bad-cmd]', f'{text=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='bad-cmd', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


# Game mode
@bot.message_handler(func=lambda msg: is_playing(msg.chat.id))
def tasks_story_line(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text
    cloud_download_files()

    state = read_history(uid)
    answer = ''

    task = state.get_task()
    guessed = task.check_answer(text)
    switched = False
    state.attempts -= 1

    if guessed:
        state.points += task.points
        switched = state.switch_task()

        word_points = MORPH \
            .parse('балл')[0] \
            .inflect({'plur', 'nomn'}) \
            .make_agree_with_number(state.points) \
            .word
        answer += (
            'Ты ответил *верно*! Повезло тебе, наверное...\n'
            f'Сейчас у тебя всего *{state.points} {word_points}*.'
        )
    else:
        answer += (
            'Ты ответил *неверно*. А подумать?\n'
            'Мы вот, коты, всегда сначала думаем, потом ляпаем.'
        )

        if not state.attempts:
            switched = state.switch_task()
            answer += (
                '\n\nКотя, у тебя _закончились попытки_ :(\n'
                'Не расстраивайся! Нафиг нам эта задачка сдалась? Пойдём _чаёк пить_?..'
            )

    if switched:
        task = state.get_task()
        word_points = MORPH \
            .parse('балл')[0] \
            .inflect({'plur', 'nomn'}) \
            .make_agree_with_number(task.points) \
            .word
        answer += (
            '\n\nЧаёк откладывается, коть! Давай думать дальше, задачки-то ещё остались ^^\n'
            f'Сейчас твоя задачка стоит *{task.points} {word_points}* и формулируется так.\n\n'
            f'{task.formulate()}'
        )
    elif guessed or not state.attempts:
        word_points = MORPH \
            .parse('балл')[0] \
            .inflect({'plur', 'nomn'}) \
            .make_agree_with_number(state.points) \
            .word
        answer += (
            '\n\nТы завершил свой квест! Молодец, котя ^^\n'
            f'Ты набрал в общей сложности *{state.points} {word_points}*.\n'
            'Подойди к моему владельцу и скажи ему, что вы оба классные :)\n'
        )

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    log(uid, f'{time=}', '[tasks]', f'{text=}', f'{guessed}', f'{switched=}', f'{state.points=}')
    state.append_history(uid=uid, tag='tasks', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


# Fallback handler
@bot.message_handler(func=lambda msg: True)
def fallback_response(msg: tb.types.Message) -> None:
    uid = msg.chat.id
    text = msg.text
    cloud_download_files()

    time = dt.fromtimestamp(msg.date).strftime('%d %b %Y %H:%M:%S')
    if roll_dice(STICKER_PROBABILITY):
        sticker = choice(LYCEUM_STICKERS)
        bot.send_sticker(uid, sticker)

        log(uid, f'{time=}', '[fallback]', f'{text=}', f'{sticker=}')
        state = read_history(uid)
        state.append_history(uid=uid, tag='fallback-sticker', text=text, answer=sticker)
        save_history(uid, state)
        return

    if roll_dice(NGRAM_PROBABILITY / (1 - STICKER_PROBABILITY)):
        with lock:
            answer = talker.talk(
                text,
                temperature=0.9,
                top_p=0.85,
                max_len=50,
            )
            for ch in '*_`':
                answer = answer.replace(ch, rf'\{ch}')
    else:
        answer = choice(FALLBACKS)

    log(uid, f'{time=}', '[fallback]', f'{text=}', f'{answer=}')
    state = read_history(uid)
    state.append_history(uid=uid, tag='fallback', text=text, answer=answer)
    save_history(uid, state)

    bot.send_message(uid, answer, parse_mode='markdown')


def bot_thread():
    cloud_download_files()
    talker.fit(*TEXT_PATHS)
    logger.info('Ngram model is fit!')

    wiki.set_lang('ru')
    logger.info('Ready for polling!')

    bot.infinity_polling()


def cloud_thread():
    while True:
        logger.info(f'Cloud thread gonna sleep for {CLOUD_SLEEP_MINS} mins...')
        sleep(60 * CLOUD_SLEEP_MINS)
        logger.info('Cloud thread woke up!')
        cloud_upload_files()
        time = dt.now().strftime('%d %b %Y %H:%M:%S')
        log(f'{time=}', 'Uploaded files!')


if __name__ == '__main__':
    talker = Talker(n=4, delta=1e-2)
    bot_job = Thread(target=bot_thread)
    cloud_job = Thread(target=cloud_thread)

    bot_job.start()
    cloud_job.start()
