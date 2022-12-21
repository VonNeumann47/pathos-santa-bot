import re
from typing import List, Pattern


def compile_regexps(regexps: List[str]) -> List[Pattern]:
    return [re.compile(regexp, re.I) for regexp in regexps]


GREET_PATTERNS = compile_regexps([
    r'(добр(ый|ого|ейш(ий|его))|хорош(его|ей|ий|ая|ее)) +'
    r'(дня|ден(ь|ек|ька)|утр(о|а|ечк(о|а))|'
    r'ноч(ь|и|еньк(а|и))|вечер(|а|ок|ка|оч(ек|ка)))',

    r'\b(при+ве+т|здра+в?ст(е|и|вуй(те)?)|до+ро+у+|дра+тути+|'
    r'здоро+в(о|а)+|hi+|he+y|hel+o+|gree+t(ings?)?|х(а|е|э)+й|х(е|э)лл?о+у?|салю+т)\b',
])

EASTER_PATTERNS = compile_regexps([
    r'\bnlp\b|\bнлп\b|лингвист|\b(уни?|би|три|квадро|n-)грамм',
])

INTJS = (
    r'\b(через|в|у|на|от|(сзади|спереди|позади|сбоку) +(от)?|об?|про|за|из( *\-? *за)|'
    r'до|для|ради|внутри|к|по|в|о(бо?)?|с|над|перед|между|за)\b'
)

PERSONAL_PATTERNS = compile_regexps([
    r'\b(ты|вы|'
    r'тво(й|я|е|и|их|им|ими|ей|его|ю|ему|ем)|ваш(|а|е|и|его|ей|их|ему|им|ими|ем)|'
    r'теб(е|я)|тобой|ва(с|ми?))\b',

    r'\b((давид|авагян|пафнутий?|паф(о|у)ос|влад|кирилл|л(е|ё)ш)(ик|ка)?'
    r'(|а|я|ю|у|е|и|ом|ем|ы|ов|ев|ям|ам|ями|ами|ях|ах)|mathematician)\b',
])

QUESTION_PATTERNS = compile_regexps([
    r'^.*\?$',

    fr'((ну +)?(а|и|но|однако|все(\-| +|)(таки|же?)|в ?оо?б?ще|ваще) +)*({INTJS} +)?'
    r'\b(как|что|чем|чего|чему|кто|кого|кому|кем|ком|чей|чья|чьи|чьем|чьей|чье|'
    r'скольк(о|им|их)|где|(как|котор)(ой|ого|ом|ая|ое|ые|ие|ую|им)|'
    r'когда|зачем|почему|(от)?куда|каков(|а|о|ы)|отчего|причем)\b',
])
