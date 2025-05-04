from abc import ABC, abstractmethod
from typing import Dict, List, Tuple, Optional, Set, Iterator
import bs4
import jaconv
from tqdm import tqdm

from utils import FileUtils, KanjiUtils, sudachi_rules
from core.yomitan_dictionary import DicEntry, create_html_element


class Parser(ABC):
    def __init__(self, config, batch_size: int = 250):
        
        from core import Dictionary, HTMLToYomitanConverter
        from index import IndexReader
        from handlers import ManualMatchHandler
        
        self.config = config
        self.dictionary = Dictionary(config.dict_name)
        self.index_reader = IndexReader(config.index_path) if config.index_path else None
        self.dict_data = FileUtils.read_xml_files(config.dict_path) if config.dict_path else None
        self.jmdict_data = FileUtils.load_term_banks(config.jmdict_path) if config.jmdict_path else {}
        self.tag_mapping = FileUtils.load_json(config.tag_map_path) if config.tag_map_path else {}
        self.manual_handler = ManualMatchHandler() if config.index_path else None
        
        self.batch_size = batch_size
        self.link_handling_strategy = config.create_link_strategy()
        self.image_handling_strategy = config.create_image_strategy()
            
        self.ignored_elements = {}
        self.expression_element = None
        
        self.html_converter = HTMLToYomitanConverter(
            tag_mapping=self.tag_mapping,
            ignored_elements=self.ignored_elements,
            expression_element=self.expression_element,
            link_handling_strategy=self.link_handling_strategy,
            image_handling_strategy=self.image_handling_strategy
        )
        
        self.bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit} [経過: {elapsed} | 残り: {remaining}]{postfix}"
        
        
    def get_target_tag(self, tag_name: str, class_list: Optional[List[str]] = None,
                       parent: Optional[bs4.element.Tag] = None, recursion_depth: int = 0) -> str:
        """
        Get the appropriate HTML tag based on tag name and CSS classes
        """
        return self.html_converter.get_target_tag(tag_name, class_list, parent, recursion_depth)
    
    
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        return self.html_converter.handle_link_element(html_glossary, html_elements, data_dict, class_list)
    
    
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, data_dict: Dict, class_list: List[str]) -> str:
        return self.html_converter.handle_image_element(html_glossary, html_elements, data_dict, class_list)
    
    
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
        return self.html_converter.get_class_list_and_data(html_glossary)
    
    
    def convert_element_to_yomitan(self, html_glossary: Optional[bs4.element.Tag] = None,
                                   ignore_expressions: bool = False) -> Optional[Dict]:
        """Recursively converts HTML elements into Yomitan JSON format"""
        return self.html_converter.convert_element_to_yomitan(
            html_glossary, ignore_expressions
        )
    
    
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
    

    def _process_batch(self, batch: List[Tuple[str, str]]) -> int:
        batch_count = 0
        for filename, xml in batch:
            try:
                batch_count += self._process_file(filename, xml)
            except Exception as e:
                print(f"Error processing file {filename}: {str(e)}")
        return batch_count
    
    
    @abstractmethod
    def _process_file(self, filename: str, xml: str) -> int:
        """Process a single file - to be implemented by derived classes"""
        pass
        
        
    def _get_batches(self) -> Iterator[List[Tuple[str, str]]]:
        """Split the input into batches"""
        items = list(self.dict_data.items())
        for i in range(0, len(items), self.batch_size):
            yield items[i:i + self.batch_size]
        
    
    def parse(self) -> int:
        """Parse the dictionary with batch processing"""
        count = 0
        
        with tqdm(total=len(self.dict_data), desc="進歩", bar_format=self.bar_format, unit="事項") as pbar:
            for batch in self._get_batches():
                batch_count = self._process_batch(batch)
                count += batch_count
                pbar.update(len(batch))
        
        return count
    
    
    def export(self, output_path: Optional[str] = None) -> None:
        """Export the dictionary to the specified path"""
        self.dictionary.export(output_path)
        
        # Export audio if it exists
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, '__class__') and 'AudioHandler' in attr.__class__.__name__:
                # If it has an export method, call it
                if hasattr(attr, 'export') and callable(attr.export):
                    attr.export()