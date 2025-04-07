from sudachipy import tokenizer
from sudachipy import dictionary
from sudachipy import SplitMode
 
__U_KANA_LIST = ["う", "く", "す", "つ", "ぬ", "ふ", "む",
                 "ゆ", "る", "ぐ", "ず", "づ", "ぶ", "ぷ"]
 
__SUDACHI_DICTIONARY = None
 
 
def sudachi_rules(expression):
    global __SUDACHI_DICTIONARY
    if __SUDACHI_DICTIONARY is None:
        __SUDACHI_DICTIONARY = dictionary.Dictionary(dict="full").create()
    #categories = load_yomichan_inflection_categories()
    categories = {
    "sudachi": {
        "sahen": ["サ行", "サ行変格", "ザ行変格", "文語サ行変格"],
        "godan": ["五段", "文語四段", "文語上二段", "文語下二段", "マス", "ヤス", "デス"],
        "ichidan": ["上一段", "下一段", "文語上一段", "文語下一段", "レル"],
        "keiyoushi": ["形容詞", "ナイ", "タイ", "ラシイ"],
        "kahen": ["カ行変格"],
        "sudachi": []
    }
    }
    sudachi_inflection_categories = categories["sudachi"]
    splitmode = tokenizer.Tokenizer.SplitMode.A
    tokens = __SUDACHI_DICTIONARY.tokenize(expression, splitmode)
    if len(tokens) == 0:
        return ""
    pos = tokens[len(tokens)-1].part_of_speech()[4]
    tags = pos.split("-")
    rules = tags_to_rules(expression, tags, sudachi_inflection_categories)
    return rules
 
 
def tags_to_rules(expression, tags, inflection_categories):
    rules = set()
    exp_final_character = expression[len(expression)-1:]
    for tag in tags:
        if tag in inflection_categories["sahen"]:
            if expression.endswith("する"):
                rules.add("vs")
            elif expression.endswith("為る"):
                rules.add("vs")
            elif expression.endswith("ずる"):
                rules.add("vz")
            elif expression.endswith("す"):
                rules.add("v5")
        if tag in inflection_categories["godan"]:
            if exp_final_character in __U_KANA_LIST:
                rules.add("v5")
        if tag in inflection_categories["ichidan"]:
            if expression.endswith("る"):
                rules.add("v1")
        if tag in inflection_categories["keiyoushi"]:
            if expression.endswith("い"):
                rules.add("adj-i")
        if tag in inflection_categories["kahen"]:
            if expression.endswith("くる"):
                rules.add("vk")
            elif expression.endswith("来る"):
                rules.add("vk")
        if tag in inflection_categories["sudachi"]:
            return sudachi_rules(expression)
    return " ".join(list(rules))