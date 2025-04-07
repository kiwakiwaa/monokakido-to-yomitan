from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Set, Callable, Any

import bs4
import jaconv

from index import IndexReader
from utils import FileUtils, KanjiUtils
from yomitandic import Dictionary, DicEntry, create_html_element

from utils.sudachi_tags import sudachi_rules
from parser.base.manual_match_handler import ManualMatchHandler
from parser.base.strategies import LinkHandlingStrategy, ImageHandlingStrategy, DefaultLinkHandlingStrategy, DefaultImageHandlingStrategy


class EnhancedParser:
    def __init__(self, dict_name: str, dict_path: str, index_path: str, jmdict_path: str = None,
                 link_handling_strategy: LinkHandlingStrategy = None,
                 image_handling_strategy: ImageHandlingStrategy = None):
        
        self.dict_data = FileUtils.read_xml_files(dict_path)
        self.dictionary = Dictionary(dict_name)
        self.index_reader = IndexReader(index_path)
        
        # Set up index and JMdict data if provided
        self.jmdict_data = FileUtils.load_term_banks(jmdict_path) if jmdict_path else {}
        self.manual_handler = ManualMatchHandler() if index_path else None
        
        # Setup strategies (using defaults if none provided)
        self.link_handling_strategy = link_handling_strategy or DefaultLinkHandlingStrategy()
        self.image_handling_strategy = image_handling_strategy or DefaultImageHandlingStrategy()
        
        # Set default properties
        self.tag_mapping = {}
        self.ignored_elements: Set[str] = set()
        self.expression_element: Optional[str] = None
        self.__yomitan_supported_tags = {
            "br", "ruby", "rt", "rp", "table", "thead", "tbody", "tfoot",
            "tr", "td", "th", "span", "div", "ol", "ul", "li"
        }
        self.bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit} [経過: {elapsed} | 残り: {remaining}]{postfix}"
        
        
    def get_target_tag(self, tag_name: str, class_list: Optional[List[str]] = None,
                       parent: Optional[bs4.element.Tag] = None, recursion_depth: int = 0) -> str:
        """
        Get the appropriate HTML tag based on tag name and CSS classes
        """
        if not class_list:
            class_list = []
            
        # Look for nested rules
        if parent:
            parent_classes, _ = self.get_class_list_and_data(parent)
            
            # Try parent.class + tag 
            for parent_class in parent_classes:
                nested_selector = f"{parent.name}.{parent_class} {tag_name}"
                if nested_selector in self.tag_mapping:
                    return self.tag_mapping[nested_selector]
                
            # Try parent + tag
            nested_selector = f"{parent.name} {tag_name}"
            if nested_selector in self.tag_mapping:
                return self.tag_mapping[nested_selector]
            
            # Recurse up the ancestor chain if no match
            if recursion_depth < 5 and parent.parent:
                target_tag = self.get_target_tag(tag_name, class_list=class_list, parent=parent.parent, recursion_depth=recursion_depth + 1)
                if target_tag != "span":
                    return target_tag
        
        # Try tag.class (no parent involvement)
        for css_class in class_list:
            class_specific_key = f"{tag_name}.{css_class}"
            if class_specific_key in self.tag_mapping:
                return self.tag_mapping[class_specific_key]
        
        # Fall back to regular tag mapping or default
        return self.tag_mapping.get(tag_name, "span")
    
    
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        return self.link_handling_strategy.handle_link_element(html_glossary, html_elements, data_dict, class_list)
    
    
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, data_dict: Dict, class_list: List[str]) -> str:
        return self.image_handling_strategy.handle_image_element(html_glossary, html_elements, data_dict, class_list)
    
    
    def normalize_keys(self, reading: str, entry_keys: List[str]) -> List[str]:
        if KanjiUtils.is_only_katakana(reading):
            normalized_keys = [jaconv.hira2kata(entry) for entry in entry_keys]
        else:
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]
            
        return normalized_keys
    
    
    def get_pos_tags(self, term: str) -> Tuple[str, str]:
        """Get part-of-speech tags for a term"""
        info_tag, pos_tag = self.jmdict_data.get(term, ["", ""])
        
        # Didn't find a POS tag match in JMdict, use sudachi instead
        if not pos_tag:
            sudachi_tag = sudachi_rules(term)
            return info_tag, sudachi_tag
            
        return info_tag, pos_tag
    
    
    def get_class_list_and_data(self, html_glossary: bs4.element.Tag) -> Tuple[List[str], Dict[str, str]]:
        """Extract class list and data attributes from an HTML element"""
        class_list = html_glossary.get("class", [])
        if isinstance(class_list, str):
            class_list = class_list.split(" ")
        
        data_dict = {}
        data_dict[html_glossary.name] = ""

        for cls in class_list:
            data_dict[cls.replace("-", "_")] = ""
                
        for attribute, value in html_glossary.attrs.items():
            if(isinstance(value, str)):
                data_dict[attribute.replace("-", "_")] = value
                
        return class_list, data_dict
    
    
    def _process_html_children(self, html_glossary: bs4.element.Tag, data_dict: Dict[str, str], class_list: List[str],
                               ignore_expressions: bool = False) -> List:
        """Process child elements of an HTML element"""
        html_elements = []
        
        if html_glossary.contents:
            for content in html_glossary.contents:
                if isinstance(content, bs4.Comment):
                    continue
                if isinstance(content, bs4.NavigableString) or isinstance(content, str):
                    html_elements.append(create_html_element("span", content))
                else:
                    converted_element = self.convert_element_to_yomitan(content, ignore_expressions=ignore_expressions)
                    if converted_element is not None:  # Avoid inserting None
                        html_elements.append(converted_element)
                        
        # Special case for img tags without contents
        elif html_glossary.name.lower() == "img":
            img_element = self.handle_image_element(html_glossary, html_elements, data_dict, class_list)
            if img_element:
                return img_element
        
        return html_elements  
    
    
    def convert_element_to_yomitan(self, html_glossary: Optional[bs4.element.Tag] = None,
                                   ignore_expressions: bool = False) -> Optional[Dict]:
        """Recursively converts HTML elements into Yomitan JSON format"""
        if not html_glossary:
            return None
        
        tag_name = html_glossary.name.lower()
        if tag_name in self.ignored_elements:
            return None
        
        if ignore_expressions and self.expression_element and tag_name == self.expression_element:
            return None
                
        class_list, data_dict = self.get_class_list_and_data(html_glossary)
        
        # Recursively process children elements
        html_elements = self._process_html_children(html_glossary, data_dict, class_list, ignore_expressions=ignore_expressions)
        if not html_elements:
            return None
        
        if not isinstance(html_elements, List):
            return html_elements
        
        # add elements that yomitan supports
        if tag_name in self.__yomitan_supported_tags:
            return create_html_element(html_glossary.name, content=html_elements, data=data_dict)
        
        # map any custom tags to html
        target_tag = self.get_target_tag(html_glossary.name, class_list, html_glossary.parent)
        
        # Handle image elements where the content isnt empty
        if tag_name == "img" and html_glossary.contents:
            element = self.handle_image_element(html_glossary)
            if element:
                return element
        
        # Hanle link elements
        if tag_name == "a":
            element = self.handle_link_element(html_glossary, html_elements, data_dict, class_list) 
            if element:
                return element
        
        return create_html_element(target_tag, content=html_elements, data=data_dict)
    
    
    def parse_entry(self, entry_key: str, reading: str, soup: bs4.BeautifulSoup,
                    info_tag: str = "", pos_tag: str = "", search_rank: int = 0,
                    ignore_expressions: bool = False) -> int:
        """Parse an entry and add it to the dictionary"""
        if not reading or reading is None:
            reading = ""
        
        if not entry_key:
            entry_key = reading
            reading = ""
        
        entry = DicEntry(entry_key, reading, info_tag=info_tag, pos_tag=pos_tag, search_rank=search_rank)
        
        for tag in soup.find_all(recursive=False):
            yomitan_element = self.convert_element_to_yomitan(tag, ignore_expressions=ignore_expressions)
            
            if yomitan_element:
                entry.add_element(yomitan_element)
                self.dictionary.add_entry(entry)
            else:
                print(f"Failed parsing entry: {entry_key}, reading: {reading}")
                return 0
        
        return 1
    
    
    def export(self, output_path: Optional[str] = None) -> None:
        """Export the dictionary to the specified path"""
        self.dictionary.export(output_path)
        
    
    @abstractmethod
    def parse(self) -> None:
        """Parse the dictionary - to be implemented by derived classes"""
        pass