import bs4
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Set, Callable, Any

from core.yomitan_dictionary import create_html_element


class ImageHandlingStrategy(ABC):
    @abstractmethod
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        pass
    
    
class DefaultImageHandlingStrategy(ImageHandlingStrategy):
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = html_glossary.get("src", "").lstrip("/")
        
        if src_path:
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