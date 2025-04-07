import os
import regex as re
import bs4

from typing import Dict, List, Tuple, Optional, Set, Callable, Any

from utils import KanjiUtils
from yomitandic import create_html_element

from parser.base.strategies import LinkHandlingStrategy, ImageHandlingStrategy

class ShinjigenLinkHandlingStrategy(LinkHandlingStrategy):
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        """Handle link elements for 新字源 dictionary"""

        # Handle "blue" links
        href = ""
        if "blue" in class_list:
            # Check for 表記G first
            hyoki_g = html_glossary.find('表記G')
            if hyoki_g:
                href = hyoki_g.text.strip()
                
                if any(KanjiUtils.is_kanji(c) for c in href):
                    href = KanjiUtils.clean_headword(href).split('・')[0]
                else:
                    href = re.sub("・", "", href)
                
            if not href:
                midashi_g = html_glossary.find('見出G')
                if midashi_g:
                    href = KanjiUtils.clean_reading(midashi_g.text.strip())
                    
            if href:   
                return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
            
            
        return create_html_element("span", content=html_elements, data=data_dict)
    
    
class ShinjigenImageHandlingStrategy(ImageHandlingStrategy):
  
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                       data_dict: Dict, class_list: List[str]) -> Dict:
        """
        Get the correct image path, applying hashed filename mapping if needed
        """
        src_attr = html_glossary.get("src", "")

        return create_html_element("span", content=html_elements, data=data_dict)