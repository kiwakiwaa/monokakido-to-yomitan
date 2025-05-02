import bs4
from typing import Dict, List

from utils import KanjiUtils
from core.yomitan_dictionary import create_html_element
from strategies import LinkHandlingStrategy

class OZK5LinkHandlingStrategy(LinkHandlingStrategy):
    
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        """Handle link elements for OZK5 dictionary"""
        href = ""
        if "blue" in class_list:
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

            href = "".join(filter(None, collected_text))
            href = KanjiUtils.clean_headword(href)    
                     
            return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
        
        return create_html_element("span", content=html_elements, data=data_dict)