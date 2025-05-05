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
    
    
    
    @staticmethod
    def get_tsukaiwake_entries(index_str: str):
        EXCLUDE_PATTERNS = [
            r'\{RB:活:かつ\}',
            r'\{RB:用:よう\}',
            r'\{RB:関:かん\}',
            r'\{RB:連:れん\}',
            r'\{RB:敬:けい\}',
            r'\{RB:語:ご\}',
            r'\{RB:参:さん\}',
            r'\{RB:考:こう\}'
        ]
        
        cleaned_str = index_str
        for pattern in EXCLUDE_PATTERNS:
            cleaned_str = re.sub(pattern, '', cleaned_str)
            
        variants = cleaned_str.split('・')
        pairs = []
        
        for variant in variants:
            # Skip empty variants (from removed metadata)
            if not variant.strip():
                continue
            
            # Extract all remaining RB tags
            rb_tags = re.findall(r'\{RB:([^:]+):([^}]+)\}', variant)
            
            if not rb_tags:
                # Handle cases like "ほどく" without RB tags
                kanji = variant
                reading = variant
                pairs.append((kanji, reading))
                continue
            
            # Extract remaining text after RB tags
            remaining_text = re.sub(r'\{RB:[^}]+\}', '', variant)
            
            # Build kanji and reading from RB tags and remaining text
            kanji_parts = []
            reading_parts = []
            
            for kanji, reading in rb_tags:
                kanji_parts.append(kanji)
                reading_parts.append(reading)
                
            kanji = ''.join(kanji_parts) + remaining_text
            reading = ''.join(reading_parts) + remaining_text
            
            pairs.append((kanji, reading))
            
        return pairs
    
    
    @staticmethod
    def is_tsukaiwake_entry(soup: bs4.BeautifulSoup) -> Tuple[bool, str]:
        header_element = soup.find("table", class_="使い分け ヘッダあり")
        main_element = soup.find("table", class_="使い分け")
        
        index = soup.find("entry-index")
        if index:
            index = index.get_text(strip=True)
        
        if main_element or header_element:
            return True, index
        
        return False, ""