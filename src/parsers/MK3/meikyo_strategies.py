import os
import regex as re
import bs4

from typing import Dict, List, Tuple, Optional, Set, Callable, Any

from utils import KanjiUtils
from core.yomitan_dictionary import create_html_element
from strategies import LinkHandlingStrategy


class MeikyoLinkHandlingStrategy(LinkHandlingStrategy):
    
    def _get_bword_reference(self, html_glossary: bs4.element.Tag):
        for ruby_tag in html_glossary.find_all("ruby"):
            ruby_tag.unwrap()
            
        for rt_tag in html_glossary.find_all("rt"):
            rt_tag.decompose()
            
        cleaned_word = "".join(html_glossary.text).strip()
        cleaned_word = KanjiUtils.clean_headword(cleaned_word)
        
        return cleaned_word
    
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        href = self._get_bword_reference(html_glossary)
        if href and not href.isdigit():
            if "・" in href:
                terms = href.split("・")
                link_elements = []
                
                for i, term in enumerate(terms):
                    link = create_html_element("a", content=term, href="?query="+term+"&wildcards=off")
                    link_elements.append(link)
                    if i < len(terms) - 1:
                        separator_element = create_html_element("span", content="・")
                        link_elements.append(separator_element)
                        
                # Wrap all the links in a span
                return create_html_element("span", content=link_elements, data=data_dict)
            else:
                return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
        
        return create_html_element("span", content=html_elements, data=data_dict)
    