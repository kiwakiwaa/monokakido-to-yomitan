import regex as re

from utils import KanjiUtils

class OZK5Utils:

    @staticmethod
    def extract_gendai_reading(soup):
        reading = ""
                    
        gendai_head = soup.find("GendaiHeadG")
        
        if gendai_head:
            gendai_midashi = gendai_head.find("Gendai見出")
            
            if gendai_midashi:
                reading = gendai_midashi.text.strip()
                
        if not any(KanjiUtils.is_kanji(c) for c in reading):
            return KanjiUtils.clean_reading(reading)
        else:       
            return ""
        
        
    @staticmethod
    def extract_headword(soup):
        head_word = ""
        
        head_element = soup.find("見出G")
        if head_element:
            element = head_element.find("見出表記")
            if element:
                head_word = element.text.strip()
                if any(KanjiUtils.is_kanji(c) for c in head_word):
                    return KanjiUtils.clean_headword(head_word).split('・')
                else:
                    head_word = re.sub("・", "", head_word)
                    return [KanjiUtils.clean_headword(head_word)]
        
            element = head_element.find("主見出")
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
        head_element = soup.find("見出G")
        if head_element:
            element = head_element.find("主見出")
            if element:
                reading = element.text.strip()
                if not any(KanjiUtils.is_kanji(c) for c in reading):
                    return KanjiUtils.clean_reading(reading)
                
            # No reading found, check wari elements
            element = head_element.find("割")
            if element:
                reading = element.text.strip()
                if not any(KanjiUtils.is_kanji(c) for c in reading):
                    return KanjiUtils.clean_reading(reading)
        
        if not any(KanjiUtils.is_kanji(c) for c in reading):
            return KanjiUtils.clean_reading(reading)
        else:       
            return ""
        

    @staticmethod
    def get_first_reference_word(html_glossary):
        collected_text = []
        
        for child in html_glossary.contents:
            if child.name == "rectr":  # Stop when encountering <rectr>
                break
            if child.name == "割":
                continue
            if isinstance(child, str):  # Plain text
                collected_text.append(child.strip())
            elif child.name:  # Other elements, preserve their text
                collected_text.append(child.get_text(strip=True))

        text = "".join(filter(None, collected_text))
        return KanjiUtils.clean_headword(text)