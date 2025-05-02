import bs4
import regex as re
from typing import Tuple
from utils import KanjiUtils

class Oko12Utils:
    
    @staticmethod
    def extract_reading(soup: bs4.BeautifulSoup) -> str:
        reading = ""

        head_element = soup.find("head2")
        if head_element:
            element = head_element.find("headword", class_="かな")
            if element:
                reading = element.text.strip()
                reading = KanjiUtils.clean_reading(reading)

            if not reading:
                element = head_element.find("headword", class_="慣用")
                
                if element:
                    collected_text = []
                    for child in element.contents:
                        if child.name == "mlg":
                            continue
                        if isinstance(child, str):  # Plain text
                            collected_text.append(child.strip())
                        elif child.name:  # Other elements, preserve their text
                            collected_text.append(child.get_text(strip=True))   
                
                    if collected_text:
                        reading = "".join(filter(None, collected_text)).strip()    
                        reading = KanjiUtils.clean_reading(reading) 
                
        return reading
    
    
    @staticmethod
    def extract_kanji_headword(soup: bs4.BeautifulSoup) -> str:
        headword = ""

        head_element = soup.find("head2", class_="漢字")
        if head_element:
            element = head_element.find("headword", class_="表記")
            if element:
                headword = element.text.strip()
                headword = KanjiUtils.clean_headword(headword)
                
        return headword
    
    
    @staticmethod
    def extract_kanji_reading(soup: bs4.BeautifulSoup) -> str:
        reading = ""

        head_element = soup.find("head2", class_="漢字")
        if head_element:
            element = head_element.find("headword", class_="かな")
            
            if element:
                collected_text = []
                for child in element.contents:
                    if child.name == "mlg":
                        continue
                    if isinstance(child, str):  # Plain text
                        collected_text.append(child.strip())
                    elif child.name:  # Other elements, preserve their text
                        collected_text.append(child.get_text(strip=True))   
            
                if collected_text:
                    reading = "".join(filter(None, collected_text)).strip()    
                    reading = KanjiUtils.clean_reading(reading)     
                
        return reading
    
    
    @staticmethod
    def extract_kanyou_headword(soup: bs4.BeautifulSoup) -> str:
        headword = ""

        head_element = soup.find("head2", class_="慣用")
        if head_element:
            element = head_element.find("headword", class_="慣用") 
    
            if element:
                collected_text = []
                for child in element.contents:
                    if child.name == "mlg":
                        continue
                    if isinstance(child, str):  # Plain text
                        collected_text.append(child.strip())
                    elif child.name:  # Other elements, preserve their text
                        collected_text.append(child.get_text(strip=True))   
        
                if collected_text:
                    headword = "".join(filter(None, collected_text)).strip()    
                    headword = KanjiUtils.clean_headword(headword)            
                
        return headword
    

    @staticmethod
    def extract_waka_headword(soup: bs4.BeautifulSoup) -> str:
        headword = ""

        head_element = soup.find("head2", class_="和歌")
        if head_element:
            element = head_element.find("headword", class_="和歌") 
            
            if element:
                collected_text = []
                for child in element.contents:
                    if child.name == "mlg":
                        continue
                    if isinstance(child, str):  # Plain text
                        collected_text.append(child.strip())
                    elif child.name:  # Other elements, preserve their text
                        collected_text.append(child.get_text(strip=True))   
            
                if collected_text:
                    headword = "".join(filter(None, collected_text)).strip()    
                    headword = KanjiUtils.clean_headword(headword)      
                
        return headword