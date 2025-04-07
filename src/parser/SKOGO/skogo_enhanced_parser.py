import os
import bs4
from tqdm import tqdm
from typing import Dict, List, Tuple, Optional, Set, Callable, Any

from utils import KanjiUtils
from parser.base.enhanced_parser import EnhancedParser
from parser.base.manual_match_handler import process_unmatched_entries
from parser.SKOGO.mapping.tag_map import TAG_MAPPING
from parser.SKOGO.skogo_utils import SKOGOUtils
from parser.SKOGO.skogo_strategies import SKOGOLinkHandlingStrategy, SKOGOImageHandlingStrategy


class EnhancedSKOGOParser(EnhancedParser):
    
    def __init__(self, dict_name: str, dict_path: str, index_path: str, jmdict_path: str):
        
        super().__init__(
            dict_name, dict_path, index_path, jmdict_path,
            link_handling_strategy=SKOGOLinkHandlingStrategy(),
            image_handling_strategy=SKOGOImageHandlingStrategy()
        )
        
        self.ignored_elements = {"entry-index"}
        self.tag_mapping = TAG_MAPPING
        
        
    def parse(self):
        count = 0
        
        for filename, xml in tqdm(self.dict_data.items(), desc="進歩", bar_format=self.bar_format, unit="事項"):
            local_count = 0
            filename_without_ext = os.path.splitext(filename)[0]
            entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
            
            soup = bs4.BeautifulSoup(xml, "xml")
            
            reading = SKOGOUtils.extract_reading(soup)
            if not reading:
                reading = SKOGOUtils.extract_gendai_reading(soup)
            if not reading:
                head_word, reading = SKOGOUtils.extract_rekishi_gendai(soup)
                pos_tag = ""
                if reading:
                    _, pos_tag = self.get_pos_tags(head_word)
                    local_count += self.parse_entry(head_word, reading, soup, pos_tag="")
                    
            if not entry_keys and not reading:
                guide_entry = SKOGOUtils.extract_guide_entry(soup)
                if guide_entry:
                    if "識別" not in guide_entry:
                        print(f"Found new guide type: {guide_entry} in file: {filename_without_ext}")
                    local_count += self.parse_entry(guide_entry, "", soup)
            
            head_word = SKOGOUtils.extract_headword(soup)
            
            normalized_keys = self.normalize_keys(reading, entry_keys)
            matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
            matched_key_pairs = process_unmatched_entries(self, filename, normalized_keys, matched_key_pairs, self.manual_handler)
            
            has_kanji = any(kanji_part for kanji_part, _ in matched_key_pairs)
            search_rank = 1 if not has_kanji else 0 
            
            self.keys = matched_key_pairs
            
            for kanji_part, kana_part in matched_key_pairs:
                pos_tag = ""
                if kanji_part:
                    _, pos_tag = self.get_pos_tags(kanji_part)
                    local_count += self.parse_entry(kanji_part, kana_part, soup, pos_tag=pos_tag, search_rank=search_rank)
                elif kana_part:
                    local_count += self.parse_entry(kana_part, "", soup, pos_tag=pos_tag, search_rank=search_rank)
                  
            count += local_count  
            if local_count == 0:
                print(f"\nNo entry was parsed for file {filename_without_ext}") 