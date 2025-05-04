import os
import regex as re
import bs4

from typing import Dict, List, Tuple, Optional, Set, Callable, Any

from utils import KanjiUtils
from core.yomitan_dictionary import create_html_element
from strategies import LinkHandlingStrategy, ImageHandlingStrategy
from parsers.SKOGO.mapping.image_map import IMAGE_FILE_MAP

class SKOGOLinkHandlingStrategy(LinkHandlingStrategy):
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        """Handle link elements for SKOGO dictionary"""
        if html_glossary.text and "識別" in html_glossary.text:
            guide_ref = KanjiUtils.clean_headword(html_glossary.text.strip())
            return create_html_element("a", content=html_elements, href="?query="+guide_ref+"&wildcards=off")
    
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
    
    
class SKOGOImageHandlingStrategy(ImageHandlingStrategy):
    def __init__(self):
        self.image_file_map = IMAGE_FILE_MAP
    
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                       data_dict: Dict, class_list: List[str]) -> Dict:
        """
        Get the correct image path, applying hashed filename mapping if needed
        """
        src_attr = html_glossary.get("src", "")
        
        if not src_attr:
            return ""
        
        if src_attr.startswith("graphics/"):
            original_filename = os.path.basename(src_attr)
            
            # Try direct lookup first
            if original_filename in self.image_file_map:
                src_attr = src_attr.replace(original_filename, self.image_file_map[original_filename])
                
                imgElement = {"tag": "img", "path": src_attr, "collapsible": False, "background": False, "data": data_dict}
                html_elements.insert(0, imgElement)
                return create_html_element("span", content=html_elements, data=data_dict) 
            
            # Try normalized versions
            import unicodedata
            for norm_form in ['NFC', 'NFD', 'NFKC', 'NFKD']:
                normalized = unicodedata.normalize(norm_form, original_filename)
                if normalized in self.image_file_map:
                    src_attr = src_attr.replace(original_filename, self.image_file_map[normalized])
                    
                    imgElement = {"tag": "img", "path": src_attr, "collapsible": False, "background": False, "data": data_dict}
                    html_elements.insert(0, imgElement)
                    return create_html_element("span", content=html_elements, data=data_dict) 
            
            # If exact match fails, try loose matching by removing the file extension
            base_name = os.path.splitext(original_filename)[0]
            for key in self.image_file_map:
                key_base = os.path.splitext(key)[0]
                if base_name == key_base:
                    src_attr = src_attr.replace(original_filename, self.image_file_map[key])
                    
                    imgElement = {"tag": "img", "path": src_attr, "collapsible": False, "background": False, "data": data_dict}
                    html_elements.insert(0, imgElement)
                    return create_html_element("span", content=html_elements, data=data_dict) 
            
            # As a last resort, try the closest match
            import difflib
            possible_matches = difflib.get_close_matches(original_filename, self.image_file_map.keys(), n=1)
            if possible_matches:
                src_attr = src_attr.replace(original_filename, self.image_file_map[possible_matches[0]])
                
                imgElement = {"tag": "img", "path": src_attr, "collapsible": False, "background": False, "data": data_dict}
                html_elements.insert(0, imgElement)
                return create_html_element("span", content=html_elements, data=data_dict) 
            
            print(f"No match found for '{original_filename}'")
            
        if src_attr:
            imgElement = {"tag": "img", "path": src_attr, "collapsible": False, "background": False, "data": data_dict}
            html_elements.insert(0, imgElement)
            return create_html_element("span", content=html_elements, data=data_dict)
            
        
        return create_html_element("span", content=html_elements, data=data_dict)