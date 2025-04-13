import bs4
import regex as re
from typing import Tuple
from utils import KanjiUtils

class MeikyoUtils:
    
    @staticmethod
    def extract_reading(soup: bs4.BeautifulSoup) -> str:
        reading = ""

        head_element = soup.find("head2")
        if head_element:
            element = head_element.find("headword", class_="カナ")
            if element:
                reading = element.text.strip()
                reading = KanjiUtils.clean_reading(reading)
                
        return reading
    
    
    @staticmethod
    def extract_ruby_text(element: bs4.element.Tag) -> Tuple[str, str]:
        readings = []
        base_expression = []
        
        for tag in element.contents:
            if tag.name == "ruby":
                rb = tag.find("rb")
                rt = tag.find("rt")
                
                if rb:
                    base_expression.append(rb.text.strip())
                if rt:
                    readings.append(rt.text.strip())
            elif isinstance(tag, str):
                text = tag.strip()
                if text:
                    base_expression.append(text)
                    readings.append(text)

        text_without_furigana = "".join(base_expression).strip()
        text_reading = "".join(readings).strip()

        text_without_furigana = KanjiUtils.clean_headword(text_without_furigana)
        text_without_furigana = re.sub("・", "", text_without_furigana)
        
        text_reading = KanjiUtils.clean_reading(text_reading)
        
        return text_without_furigana, text_reading