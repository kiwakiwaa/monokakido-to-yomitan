import regex as re
import bs4
from typing import List, Tuple

from utils import KanjiUtils

class Shinjigen2Utils: 
    
    @staticmethod
    def extract_jukugo(soup: bs4.BeautifulSoup) -> Tuple[List[str], str]:
        headword = []
        reading = ""
        
        head_element = soup.find("JukugoHead")
        if head_element:
            reading_element = head_element.find("JukugoYomi")
            if reading_element:
                reading = KanjiUtils.clean_reading(reading_element.text.strip())
                
            hyoki_element = head_element.find("JukugoHyoki")
            if hyoki_element:
                head_word = hyoki_element.text.strip()
                if any(KanjiUtils.is_kanji(c) for c in head_word):
                    headword = KanjiUtils.clean_headword(head_word).split('・')
                else:
                    head_word = re.sub("・", "", head_word)
                    headword [KanjiUtils.clean_headword(head_word)]
                
        return headword, reading