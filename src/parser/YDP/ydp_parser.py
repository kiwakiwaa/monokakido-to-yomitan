import os
import bs4
import jaconv
from typing import List

from utils import KanjiUtils
from parser.base.parser import Parser
from parser.base.manual_match_handler import process_unmatched_entries
from parser.YDP.tag_map import TAG_MAPPING
from parser.YDP.ydp_utils import YDPUtils
from parser.YDP.ydp_strategies import YDPImageHandlingStrategy

class YDPParser(Parser):

    def __init__(self, dict_name: str, dict_path: str, index_path: str, jmdict_path: str):
        
        super().__init__(
            dict_name, dict_path, index_path,
            image_handling_strategy=YDPImageHandlingStrategy()
        )
        
        self.ignored_elements = {"entry-index", "key"}
        self.tag_mapping = TAG_MAPPING
        
        
    def normalize_keys(self, reading: str, entry_keys: List[str]) -> List[str]:
        if all(KanjiUtils.is_kanji(c) for c in reading):
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]
        elif any(KanjiUtils.is_katakana(c) for c in reading):
            normalized_keys = [jaconv.hira2kata(entry) for entry in entry_keys]
        else:
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]
        
        return normalized_keys
        
    
    def _process_file(self, filename: str, xml: str):
        local_count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Get keys from index
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")
        
        # Use headword for normalisation (Whether to convert keys to hiragana or keep katakana)
        head_word = YDPUtils.extract_headword(soup)
            
        # Normalise and match keys
        normalized_keys = self.normalize_keys(head_word, entry_keys)
        matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
        matched_key_pairs = process_unmatched_entries(
            self, filename, normalized_keys, matched_key_pairs, self.manual_handler
        )
        
        # Determine search ranking (rank kana entries higher)
        has_kanji = any(kanji_part for kanji_part, _ in matched_key_pairs)
        search_rank = 1 if not has_kanji else 0 
        
        # Process each key pair
        for kanji_part, kana_part in matched_key_pairs:
            pos_tag = ""
            if kanji_part:
                _, pos_tag = self.get_pos_tags(kanji_part)
                local_count += self.parse_entry(
                    kanji_part, kana_part, soup, pos_tag=pos_tag, search_rank=search_rank
                )
            elif kana_part:
                local_count += self.parse_entry(
                    kana_part, "", soup, pos_tag=pos_tag, search_rank=search_rank
                )
                
        if local_count == 0:
            print(f"\nNo entry was parsed for file {filename_without_ext}")           
            
        return local_count