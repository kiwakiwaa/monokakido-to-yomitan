import bs4
import regex as re
from typing import Tuple
from utils import KanjiUtils

class Rgko12Utils:
    
    @staticmethod
    def extract_reading(soup: bs4.BeautifulSoup) -> str:
        reading = ""

        head_element = soup.find("head2")
        if head_element:
            element = head_element.find("headword")
            if element:
                reading = element.text.strip()
                reading = KanjiUtils.clean_headword(reading)
                
        return reading