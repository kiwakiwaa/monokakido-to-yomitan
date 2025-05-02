import regex as re
import jaconv
from utils import KanjiUtils

class SKOGOUtils:
    
    @staticmethod
    def extract_headword(soup):
        head_word = ""
        
        head_element = soup.find("見出部")
        if head_element:
            element = head_element.find("表記G")
            if element:
                head_word = element.text.strip()
                if any(KanjiUtils.is_kanji(c) for c in head_word):
                    return KanjiUtils.clean_headword(head_word).split('・')
                else:
                    head_word = re.sub("・", "", head_word)
                    return [KanjiUtils.clean_headword(head_word)]
        
            
        return ""
             
                    
    @staticmethod
    def extract_reading(soup):
        reading = ""
        
        # Attempt to find a reading in the Head element
        head_element = soup.find("見出部")
        if head_element:
            element = head_element.find("見出G")
            if element:
                reading = element.text.strip()
                return KanjiUtils.clean_reading(reading)
                
        return ""
    

    @staticmethod
    def extract_gendai_reading(soup):
        reading = ""
        
        # Attempt to find a reading in the Head element
        head_element = soup.find("見出部")
        if head_element:
            element = head_element.find("Gendai見出")
            if element:
                reading = element.text.strip()
                return KanjiUtils.clean_reading(reading)
                
        return ""
    
    
    @staticmethod
    def extract_rekishi_gendai(soup):
        head_word = ""
        reading = ""
        
        # Attempt to find a reading in the Head element
        head_element = soup.find("見出部")
        if head_element:
            head_word_element = head_element.find("見出G")
            if head_word_element:
                head_word = head_word_element.text.strip()
                head_word = jaconv.kata2hira(KanjiUtils.clean_headword(head_word))
            
            reading_element = head_element.find("見出現代仮名")
            if reading_element:
                reading = reading_element.text.strip()
                reading = jaconv.kata2hira(KanjiUtils.clean_reading(reading))
                
        return head_word, reading
    
    
    @staticmethod
    def extract_guide_entry(soup):
        """Extracts 識別 entries in the guide entries that dont have any keys."""
        # E.g しかの識別
        reading = ""
        
        head_element = soup.find("識別見出行")
        if head_element:
            reading_element = head_element.find("識別見出")
            if reading_element:
                reading = reading_element.text.strip()
                
            sub_element = head_element.find("識別見出サブ")
            if sub_element:
                guide_type = sub_element.text.strip()
                entry_key = reading + guide_type
                return KanjiUtils.clean_headword(entry_key)
                
        return ""