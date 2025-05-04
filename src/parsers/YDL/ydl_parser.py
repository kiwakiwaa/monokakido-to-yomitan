import os
import bs4
import jaconv
from typing import Dict, List, Optional

from utils import KanjiUtils

from core import Parser
from config import DictionaryConfig
from handlers import process_unmatched_entries
from parsers.YDL.ydl_utils import YDLUtils
    
class YDLParser(Parser):
    
    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        self.ignored_elements = {"index", "参照先ID", "管理データ", "項目読み"}


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
        
        if not entry_keys:
            print(f"No entry keys for entry: {filename_without_ext}")
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")
        
        # Use reading for normalisation (Whether to convert keys to hiragana or keep katakana)
        headword = YDLUtils.extract_headword(soup)
        
        if not headword:
            print(f"No headowrd for entry: {filename_without_ext}\nKeys: {entry_keys}")
            
        # Normalise and match keys
        normalized_keys = self.normalize_keys(headword, entry_keys)
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