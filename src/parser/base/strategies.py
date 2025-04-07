import bs4
from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Set, Callable, Any

from yomitandic import create_html_element


class LinkHandlingStrategy(ABC):
    @abstractmethod
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        pass


class ImageHandlingStrategy(ABC):
    @abstractmethod
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        pass
    
    
class DefaultLinkHandlingStrategy(LinkHandlingStrategy):
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        href = ""
        if html_glossary.text:
            href = html_glossary.text.strip()
            
        if href and not href.isdigit():  # Check that href is not empty and not only digits
            return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
        
        return create_html_element("span", content=html_elements, data=data_dict)
    
    
class DefaultImageHandlingStrategy(ImageHandlingStrategy):
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = html_glossary.get("src", "").lstrip("/")
        
        if src_path:
            imgElement = {"tag": "img", "path": src_path, "collapsible": False, "data": data_dict}
            html_elements.insert(0, imgElement)
        
        return create_html_element("span", content=html_elements, data=data_dict)