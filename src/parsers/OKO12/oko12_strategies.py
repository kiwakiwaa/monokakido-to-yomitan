import bs4
import os
from typing import Dict, List, Optional, Tuple

from utils import KanjiUtils
from core.yomitan_dictionary import create_html_element

from strategies import LinkHandlingStrategy, ImageHandlingStrategy

class Oko12LinkHandlingStrategy(LinkHandlingStrategy):
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:   
        """Handle link elements for 旺文社国語""" 
        href = ""
        collected_text = []
        for child in html_glossary.contents:
            if child.name == "mlg":
                continue
            if isinstance(child, str):  # Plain text
                collected_text.append(child.strip())
            elif child.name:  # Other elements, preserve their text
                collected_text.append(child.get_text(strip=True))   
    
        if collected_text:
            href = "".join(filter(None, collected_text)).strip()
            
        if href and not href.isdigit():  # Check that href is not empty and not only digits
            return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
        
        return create_html_element("span", content=html_elements, data=data_dict)
    
    
class Oko12ImageHandlingStrategy(ImageHandlingStrategy):
    def __init__(self):
        self.replacements = {
            "arrow_both_h_thin.svg": {
                "text": "↔",
                "class": "矢印"
            },
            "arrow_both_v_thin.svg": {
                "text": "↔",
                "class": "矢印"
            },
            "arrow_down.svg": {
                "text": "⇨",
                "class": "大矢印"
            },
            "arrow_right.svg": {
                "text": "⇨",
                "class": "大矢印"
            },
            "dollar2.svg": {
                "text": "$",
                "class": "外字"
            },
            "maruko.svg": {
                "text": "高",
                "class": "maru"
            },
            "maruchu.svg": {
                "text": "中",
                "class": "maru"
            }
        }


    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, 
                             data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = html_glossary.get("src", "").lstrip("/")

        if src_path:
            basename = os.path.basename(src_path)

            if basename in self.replacements:
                text = self.replacements[basename]["text"]
                class_name = self.replacements[basename]["class"]
                data_dict[class_name] = ""
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