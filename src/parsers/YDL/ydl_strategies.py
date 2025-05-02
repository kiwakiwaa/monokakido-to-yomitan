import os
import bs4

from typing import List, Dict
from core.yomitan_dictionary import create_html_element
from strategies import ImageHandlingStrategy


class YDLImageHandlingStrategy(ImageHandlingStrategy):
    def __init__(self):
        self.replacements = {
            "arrow-thin-h.svg": {
                "text": "⇀",
                "class": "矢印"
            },
            "arrow-thin.svg": {
                "text": "⇀",
                "class": "矢印"
            },
            "arrow-h.svg": {
                "text": "⇨",
                "class": "大矢印"
            },
            "arrow.svg": {
                "text": "⇨",
                "class": "大矢印"
            },
            "135.svg": {
                "text": "-",
                "class": "ハイフン"
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