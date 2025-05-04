import bs4
from typing import List

from utils import FileUtils

from core import Parser
from config import DictionaryConfig

class ShinjigenParser(Parser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        
        self.dict_data = FileUtils.load_mdx_json(config.dict_path)
        self.ignored_elements = {"entry-index", "link"}

        
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