import os
import bs4
import regex as re

from typing import List, Dict, Tuple
from yomitandic import create_html_element
from parser.base.strategies import ImageHandlingStrategy


class ShinjigenImageHandlingStrategy(ImageHandlingStrategy):
    def __init__(self):
        self.replacements = {
            "1E0D.png": {
                "text": "ḍ",
                "class": "diacritic"
            },
            "1E43.png": {
                "text": "ṃ",
                "class": "diacritic"
            },
            "1E45.png": {
                "text": "ṅ",
                "class": "diacritic"
            },
            "1E47.png": {
                "text": "ṇ",
                "class": "diacritic"
            },
            "1E63.png": {
                "text": "ṣ",
                "class": "diacritic"
            },
            "1ECD.png": {
                "text": "ọ",
                "class": "diacritic"
            },
            "ontenka.png": {
                "text": "→",
                "class": "音転化"
            }
        }
    
    def extract_inmoku_info(self, filename: str):
        match = re.search(r'Inmoku-(\d+)-([^.]+)', filename)
        if match:
            inmoku_type = match.group(1)  # The number after "Inmoku-"
            last_char = match.group(2)[-1]  # The last character before extension
            if last_char == 'E':
                last_char = '⠀'
            return inmoku_type, last_char
        return None, None
    
    
    def add_class(self, data_dict: Dict, class_: str) -> Dict:
        if "class" not in data_dict:
            data_dict["class"] = class_
        else:
            data_dict["class"] += " " + class_ 
        
        
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, 
                             data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = html_glossary.get("src", "").lstrip("/")
        
        if src_path:
            basename = os.path.basename(src_path)
            
            if basename.startswith("Inmoku"):
                inmoku_type, kanji = self.extract_inmoku_info(basename)
                inmoku_type = "韻目" + inmoku_type
                if inmoku_type and kanji and kanji != '':
                    data_dict = self.add_class(data_dict, inmoku_type)
                    return create_html_element("span", content=kanji, data=data_dict)
            
            elif basename in self.replacements:
                text = self.replacements[basename]["text"]
                class_name = self.replacements[basename]["class"]
                data_dict = self.add_class(data_dict, class_name)
                return create_html_element("span", content=text, data=data_dict)
                
            else:
                imgElement = {
                    "tag": "img", 
                    "path": src_path, 
                    "collapsible": False, 
                    "collapsed": False,
                    "background": False,
                    "appearance": "auto",
                    "imageRendering": "auto",
                    "data": data_dict
                }
                html_elements.insert(0, imgElement)
        
        return create_html_element("span", content=html_elements, data=data_dict)