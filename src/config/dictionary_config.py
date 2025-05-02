from dataclasses import dataclass
from typing import Optional, Type, Callable
import importlib


@dataclass
class DictionaryConfig:
    """Configuration for dictionary processing"""
    dict_name: str
    rev_name: str
    dict_type: str
    parser_module: str  # Module path instead of class reference
    parser_class_name: str  # Class name as string
    
    # Strategy factories as strings to avoid circular imports
    strategy_module: str = "strategies"
    link_strategy_class: str = "DefaultLinkHandlingStrategy"
    image_strategy_class: str = "DefaultImageHandlingStrategy"
    
    # Mapping paths
    tag_map_path: Optional[str] = None
    appendix_entries_path: Optional[str] = None
    
    # Optional features
    has_appendix: bool = False
    appendix_handler_module: Optional[str] = None
    appendix_handler_class: Optional[str] = None
    use_jmdict: bool = True
    has_audio: bool = False
    
    def get_parser_class(self):
        module = importlib.import_module(self.parser_module)
        return getattr(module, self.parser_class_name)
    
    def create_link_strategy(self):
        module = importlib.import_module(self.strategy_module)
        strategy_class = getattr(module, self.link_strategy_class)
        return strategy_class()
    
    def create_image_strategy(self):
        module = importlib.import_module(self.strategy_module)
        strategy_class = getattr(module, self.image_strategy_class)
        return strategy_class()
    
    def create_appendix_handler(self, dictionary, directory_path):
        from handlers.appendix_handler import AppendixHandler
        from utils.file_utils import FileUtils
        
        # Load mappings if provided
        tag_mapping = {}
        appendix_entries = {}
        
        if self.tag_map_path:
            tag_mapping = FileUtils.load_dictionary_mapping(self.tag_map_path)
            
        if self.appendix_entries_path:
            appendix_entries = FileUtils.load_dictionary_mapping(self.appendix_entries_path)
            
        return AppendixHandler(
            dictionary=dictionary,
            directory_path=directory_path,
            tag_mapping=tag_mapping,
            appendix_entries=appendix_entries,
            link_strategy=self.create_link_strategy(),
            image_strategy=self.create_image_strategy()
        )