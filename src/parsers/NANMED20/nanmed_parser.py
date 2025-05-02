import bs4
import jaconv
import regex as re
from typing import List

from utils import FileUtils, KanjiUtils
from core import Parser
from parser.NANMED20.nanmed_strategies import NanmedImageHandlingStrategy

class NanmedParser(Parser):

    def __init__(self, dict_name: str, dict_path: str, index_path: str, jmdict_path: str):
        
        super().__init__(dict_name, image_handling_strategy=NanmedImageHandlingStrategy())
        
        self.dict_data = FileUtils.load_mdx_json(dict_path)
        self.parantheses = {'(', ')', '（', '）'}
        self.parantheses_ignored = {
            "細菌", "関節", "角膜", "器具", "歯科インプラント", "硫酸", "塩素", "塩酸", "ニコチン酸", "リン酸",
            "臭化", "糖尿病", "フッ化", "'卵巣癌", "放射線", "嚥下", "腫瘍", "腸管", "トシル酸", "視床下部",
            "体温", "5q", "プロピオン酸", "マレイン酸", "遺伝子組換え", "メシル酸", "フマル酸", "次硝酸",
            "酢酸"
        }
        
        self.initialize_html_converter()
        
        
    def extract_entry_keys(self, entry: str) -> List[str]:
        entry = entry.replace('《', '').replace('》', '')
        entries = entry.split('|')
        return entries
        
        
    def _process_file(self, filename: str, xml: str) -> int:
        local_count = 0
        entry_keys = self.extract_entry_keys(filename)
        soup = bs4.BeautifulSoup(xml, "lxml")
        
        if any(any(p in key for p in self.parantheses) for key in entry_keys):   
            if len(entry_keys) == 1:
                headword = entry_keys[0]
                
                # Check if this is a kana entry with kanji in parentheses
                if "（" in headword:
                    # Get the content before the first parenthesis
                    before_paren = headword.split("（")[0].strip()
                    
                    # Check if the part before parenthesis is kana-only
                    if KanjiUtils.is_only_kana(before_paren):
                        # Extract the content inside parentheses
                        inside_paren_match = re.search(r'（([^）]+)）', headword)
                        if inside_paren_match:
                            kanji_form = inside_paren_match.group(1)
                            # Add entry with kanji as headword and kana as reading
                            local_count += self.parse_entry(kanji_form, before_paren, soup)
                    else:
                        # For normal entries, remove parentheses
                        clean_headword = re.sub(r'（[^）]+）', '', headword)
                        local_count += self.parse_entry(clean_headword, "", soup)
                else:
                    # No parentheses, just use as is
                    local_count += self.parse_entry(headword, "", soup)
                    
            elif len(entry_keys) == 2:
                headword = entry_keys[0]
                reading = entry_keys[1]
                
                # Check if this is a kana entry with kanji in parentheses
                if "（" in headword:
                    # Get the content before the first parenthesis
                    before_paren = headword.split("（")[0].strip()
                    
                    # Check if the part before parenthesis is kana-only
                    if KanjiUtils.is_only_kana(before_paren):
                        # Extract the content inside parentheses
                        inside_paren_match = re.search(r'（([^）]+)）', headword)
                        if inside_paren_match and any(KanjiUtils.is_kanji(c) for c in inside_paren_match.group(1)) and inside_paren_match.group(1) not in self.parantheses_ignored:
                            kanji_form = inside_paren_match.group(1)
                            # Add entry with kanji as headword and kana as reading
                            if all(KanjiUtils.is_kanji(c) for c in kanji_form):
                                before_paren = jaconv.kata2hira(before_paren)
                            elif any(KanjiUtils.is_katakana(c) for c in kanji_form):
                                before_paren = jaconv.hira2kata(before_paren)
                            else:
                                before_paren = jaconv.kata2hira(before_paren)
                            
                            local_count += self.parse_entry(kanji_form, before_paren, soup)
                
                # Always process the main entry with cleaned headword
                clean_headword = re.sub(r'（[^）]+）', '', headword)
                if not any(KanjiUtils.is_kanji(c) for c in reading):
                    if all(KanjiUtils.is_kanji(c) for c in clean_headword):
                        reading = jaconv.kata2hira(reading)
                    elif any(KanjiUtils.is_katakana(c) for c in clean_headword):
                        reading = jaconv.hira2kata(reading)
                    else:
                        reading = jaconv.kata2hira(reading)
                        
                    local_count += self.parse_entry(clean_headword, reading, soup)
                else:
                    print(f"\nFound entry with non-kana reading: {headword}, reading: {reading}\n{xml}")
            elif len(entry_keys) > 2:
                print(f"\nFound entry with more than 2 keys: {entry_keys}\n{xml}")
        else:
            # Normal processing for entries without parentheses
            if len(entry_keys) == 1:
                headword = entry_keys[0]
                local_count += self.parse_entry(headword, "", soup)
            elif len(entry_keys) == 2:
                headword = entry_keys[0]
                reading = entry_keys[1]
                if not any(KanjiUtils.is_kanji(c) for c in reading):
                    if all(KanjiUtils.is_kanji(c) for c in headword):
                        reading = jaconv.kata2hira(reading)
                    elif any(KanjiUtils.is_katakana(c) for c in headword):
                        reading = jaconv.hira2kata(reading)
                    else:
                        reading = jaconv.kata2hira(reading)
                        
                    local_count += self.parse_entry(headword, reading, soup)
                else:
                    print(f"\nFound entry with non-kana reading: {headword}, reading: {reading}\n{xml}")
            elif len(entry_keys) > 2:
                print(f"\nFound entry with more than 2 keys: {entry_keys}\n{xml}")
                
        return local_count