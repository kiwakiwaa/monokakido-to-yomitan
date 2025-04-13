import bs4
from typing import List

from utils import FileUtils

from parser.base.parser import Parser
from parser.SHINJIGEN2.tag_map import TAG_MAPPING
from parser.SHINJIGEN2.shinjigen2_strategies import ShinjigenImageHandlingStrategy

class ShinjigenParser(Parser):

    def __init__(self, dict_name: str, dict_path: str, index_path: str, jmdict_path: str):
        
        super().__init__(dict_name, image_handling_strategy=ShinjigenImageHandlingStrategy())
        
        self.dict_data = FileUtils.load_mdx_json(dict_path)
        self.ignored_elements = {"entry-index", "link"}
        self.tag_mapping = TAG_MAPPING
        
        
    def extract_entry_keys(self, entry: str) -> List[str]:
        entry = entry.replace('《', '').replace('》', '')
        entries = entry.split('|')
        return entries
        
        
    def _process_file(self, entry: str, xml: str) -> int:
        local_count = 0
    
        entry_keys = self.extract_entry_keys(entry)
        soup = bs4.BeautifulSoup(xml, "lxml")
    
        for entry in entry_keys:
            local_count += self.parse_entry(entry, "", soup)      
            
        return local_count