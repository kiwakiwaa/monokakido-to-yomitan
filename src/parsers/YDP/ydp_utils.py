import regex as re
import jaconv
import bs4
from utils import KanjiUtils

class YDPUtils:
    
    @staticmethod
    def extract_headword(soup: bs4.BeautifulSoup) -> str:
        head_word = ""
        
        element = soup.find("headword", class_="見出")
        if element:
            head_word = element.text.strip()
        
        return head_word
    
    
    @staticmethod
    def extract_english_headword(soup: bs4.BeautifulSoup) -> str:
        collected_text = []
        
        element = soup.find("headword", class_="英語")
        for child in element:
            if child.name == "lang":
                continue
            else:
                head_word = element.text.strip()
                collected_text.append(head_word)
        
        return collected_text