from textwrap import dedent
from typing import Callable, Optional
from warnings import catch_warnings, filterwarnings

import numpy as np


class Task:
    def __init__(self,
                 points: int,
                 question: str,
                 answers: List[int] = None,
                 callback: Optional[Callable] = None):
        self._question = question
        self._answers = answers or []
        self.points = points
        self._callback = callback

    def formulate(self) -> str:
        return dedent(self._question)

    def check_answer(self, text: str) -> bool:
        text = ' '.join(text.strip().split())
        if self._callback is not None:
            return self._callback(text)
        return text.isdigit() and int(text) in self._answers


class GcdTester:
    @staticmethod
    def func(a, b) -> int:
        a, b, ans = map(int, (a, b, a * b))
        if a < b:
            a, b = b, a
        while b:
            a, b = b, a % b
        return ans // a

    def main(self, *args: int) -> int:
        with catch_warnings():
            filterwarnings('ignore', category=RuntimeWarning)
            a, b = map(np.int32, args)
            return GcdTester.func(a, b)


def check_gcd(text: str) -> bool:
    try:
        numbers = list(map(int, text.split()))
        assert len(numbers) == 8, f'Test 0 failed: expected 8 numbers, got {len(numbers)}'

        tester = GcdTester()
        val_1 = tester.main(*numbers[:2])
        assert val_1 == 42, f'Test 1 failed: expected 42, got {val_1}'

        val_2 = tester.main(*numbers[2:4])
        assert any(numbers[2:4]) and val_2 == 0, f'Test 2 failed: expected 0, got {val_2}'

        val_3 = tester.main(*numbers[4:6])
        int_max = np.iinfo(np.int32).max
        assert val_3 == int_max, f'Test 3 failed: expected {int_max}, got {val_3}'

        try:
            val_4 = tester.main(*numbers[6:8])
        except:
            pass
        else:
            print('Test 4 failed :(')
            return False

        return True
    except Exception as err:
        print('False:', err)
        return False


MAX_ATTEMPTS = 5

TASKS = [
    Task(  # 1: prime global constants
        question=r'''
        Масянь, определишь, что выведет следующая программа?
        В качестве ответа вбивай только _одно целое число_. Мне больше ничего не надо.

        ```
        def is_prime(n):
            if n == 1 or not n & 1 and n != 2:
                return False
            k = 3
            while k * k <= n:
                if not n % k:
                    return False
                k += 2
            return True

        def is_valid(n):
            return is_prime(n) and n is n + 1 - 1

        INF = 2 ** 42 ** 47

        def main():
            cnt = 0
            for x in range(-INF, INF):
                cnt += is_valid(x)
            print(cnt)

        main()
        ```
        ''',
        answers=[57],
        points=4,
    ),
    Task(  # 2: log_2 and powers of 2
        question=r'''
            Котёночек, смотри, всё очень просто!
            Этот код должен напечатать лишь одно целое число. Какое?
            Вбивай только _одно целое число_: всякий мусор сюда не пихай, попыток-то мало!

            ```
            BOUND = 63382530011411470074835160268800

            def search(x, out=[]):
                for y in range(1000):
                    if y < x >= (x := x // 2):
                        out.append(x)
                return out

            def main():
                answer = 0
                for x in range(BOUND):
                    sequence = search(x)
                    size = len(sequence)
                    if not size & (size - 1):
                        answer += size
                print(answer)

            main()
            ```
        ''',
        answers=[1099511631939],
        points=7,
    ),
    Task(  # 3: MRO
        question=r'''
            Комбинаторная задача. Котя любит такие!
            В коде ниже есть слоты, пронумерованные от 0 до 4.
            Твоя задача - определить, сколько существует способов заполнить их \
            строками из набора `{"object", "A", "B", "C", "D", "E"}` так, чтобы:
            - программа не крашилась (котя упаси!)
            - в каждом слоте строки не повторялись (слот может быть пустым)
            - программа выведет буквы `A B C D E`, каждую на своей строке
            Котя, давай! Ты всё можешь ^^

            ```
            class A({0}):
                def __init__(self):
                    print('A')
                    super().__init__()

            class B({1}):
                def __init__(self):
                    print('B')
                    super().__init__()

            class C({2}):
                def __init__(self):
                    super().__init__()
                    print('C')

            class D({3}):
                def __init__(self):
                    print('D')
                    super().__init__()

            class E({4}):
                def __init__(self):
                    super().__init__()
                    print('E')

            _ = E()
            ```
        ''',
        answers=[0],
        points=2,
    ),
    Task(  # 4: closure, float underflow etc.
        question=r'''
            Мой кореш Пшека подкинул мне вот _это_.
            Назвать это кодом язык не поворачивается. Как Пше любит говорить, _ship happens_.
            Давай утрём носик Пшушке! Вбей то, что напечатает эта программка.
            Должно быть просто. Я бы и сам справился, но... у меня лапки, you know ^^

            ```
            import numpy as np

            BOUND = 11911111932115111321049799107101114

            def check(*objs, **more_objs):
                checkers = more_objs
                for i, obj in enumerate(objs):
                    try:
                        checkers[obj] = lambda x: x == i
                    except TypeError:
                        # ship happens
                        pass
                size = len(checkers)
                for x in range(-BOUND, BOUND):
                    for func in checkers.values():
                        if func(x):
                            size += 1
                return size

            def main():
                print(check(
                    True, False, None,
                    '', [], (), {},
                    0_0, {0_0}, 0x0, 0o0, 0O0,
                    1.0, 1e-1532, 0b101010, 0,
                    *(float(f'2.{k}e-324') for k in range(BOUND)),
                    1, 0B0, 0B_0,
                    kek=lambda x: x == x ** 2,
                    lol=lambda x: x ** 2 == 2 ** x,
                    arbidol=lambda x: np.power(2 if x > 0 else 2., x),
                ))

            main()
            ```
        ''',
        answers=[1120, 1152],
        points=6,
    ),
    Task(  # 5: sqrt is not sqrt
        question=r'''
            *Я не понимаю, где баг!* Ну, она же _идеальная_, тут нет бага сто пудов!
            Короче, делай что хочешь, но объясни мне, почему программка циклится.
            Что она должна напечатать?
            _Подсказка_: это одно целое число. Котя помог, котя хороший ^^

            ```
            from math import sqrt

            def check(n):
                return sqrt(n * n) != n

            def main():
                n = 1
                while not check(n):
                    n += 1
                print(n)

            main()
            ```
        ''',
        answers=[9007199254740993],
        points=5,
    ),
    Task(  # 6: sizeof
        question=r'''
            Лично на моём компуктере бесконечно много памяти. Я прогаю на Машине Тьюринга просто.
            А мой препод Мурка всё равно докопался!
            Он спрашивает, сколько памяти займут суммарно все элементы списка и сам список.
            Ответ хочет _в байтах_. Выручай! Мрррр ^^
            P.S.: у него Python 3.9.13 и винда 64-битная, но это не важно...

            ```
            [True, False, None, '', 'oh ship', 0, 1, 1073741824, -42]
            ```
        ''',
        answers=[437],
        points=3,
    ),
    Task(  # 7: buggy gcd
        question=r'''
            Этот код написал первый котёнок-программист Шпрота. Он у Евклида жил, "Начала" ему диктовал!
            Короче, гениальный был котёнок. Пушистый, красавчик, всё на свете знает...
            Но вот этот вот код его почему-то не работает, по его словам. А как по мне, всё замечательно.
            В общем, нам, его потомкам теперь разгребать. Задача такая.
            Надо подобрать пары целых чисел, которые нужно ввести, чтобы программа:
            - вывела `42`
            - вывела `0` (но числа должны быть ненулевые!)
            - вывела максимальное значение типа `np.int32`
            - _крашнулась_ к фигам (Евклид, 298 г. до н.э., цитата)
            И все эти пары надо ввести через пробельчик, по одной паре на каждый кейс.
            Должно получиться всего 8 чисел. Есть идеи?

            ```
            from warnings import catch_warnings, filterwarnings
            import numpy as np

            def func(a, b):
                a, b, ans = map(int, (a, b, a * b))
                if a < b:
                    a, b = b, a
                while b:
                    a, b = b, a % b
                return ans // a

            def main():
                with catch_warnings():
                    filterwarnings('ignore', category=RuntimeWarning)
                    a, b = map(np.int32, input().split())
                    print(func(a, b))

            main()
            ```
        ''',
        points=3,
        callback=check_gcd,
    ),
]
