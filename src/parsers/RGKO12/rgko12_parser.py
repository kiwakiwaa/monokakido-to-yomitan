import os
import bs4
import jaconv
from typing import List

from utils import FileUtils, KanjiUtils
from core import Parser
from config import DictionaryConfig
from handlers import process_unmatched_entries
from parsers.RGKO12.rgko12_utils import Rgko12Utils

class Rgko12Parser(Parser):

    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        
        
    def normalize_keys(self, reading: str, entry_keys: List[str]) -> List[str]:
        if all(KanjiUtils.is_kanji(c) for c in reading):
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]
        elif any(KanjiUtils.is_hiragana(c) for c in reading):
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]
        else:
            normalized_keys = [jaconv.hira2kata(entry) for entry in entry_keys]
        
        return normalized_keys
        
    
    def _process_file(self, filename: str, xml: str):
        local_count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Get keys from index
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")
        
        # Use headword for normalisation (Whether to convert keys to hiragana or keep katakana)
        reading = Rgko12Utils.extract_reading(soup)
        if not reading:
            print(f"No reading found for: {filename_without_ext}")
            
        if not entry_keys:
            print(f"No entry keys for: {filename_without_ext}")
            
        # Normalise and match keys
        normalized_keys = self.normalize_keys(reading, entry_keys)
        matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
        matched_key_pairs = process_unmatched_entries(
            self, filename, normalized_keys, matched_key_pairs, self.manual_handler
        )
        
        # Determine search ranking (rank kana entries higher)
        has_kanji = any(kanji_part for kanji_part, _ in matched_key_pairs)
        search_rank = 1 if not has_kanji else 0 
        
        is_tsukaiwake_entry, index = Rgko12Utils.is_tsukaiwake_entry(soup)
        info_tag, pos_tag = "", ""
        
        if not is_tsukaiwake_entry:
            for kanji_part, kana_part in matched_key_pairs:
                if kanji_part:
                    info_tag, pos_tag = self.get_pos_tags(kanji_part)
                    local_count += self.parse_entry(
                        kanji_part, kana_part, soup, pos_tag=pos_tag, search_rank=search_rank, ignore_expressions=True
                    )
                elif kana_part:
                    local_count += self.parse_entry(
                        kana_part, "", soup, pos_tag=pos_tag, search_rank=search_rank, ignore_expressions=True
                    )
                
                
            # Add any kana only entries if theres a "uk" tag (usually written using kana alone)
            info_tags = info_tag.split()
            if "uk" in info_tags:
                # Find unique kana parts that haven't been parsed yet
                unique_kana_parts = set()
                for _, kana_part in matched_key_pairs:
                    # Check if the kana part hasn't been added before
                    if kana_part not in unique_kana_parts and not any(kanji is None and kana_part == kana for kanji, kana in matched_key_pairs):
                        unique_kana_parts.add(kana_part)
                        local_count += self.parse_entry(kana_part, "", soup, pos_tag=pos_tag, search_rank=1, ignore_expressions=True)
                        
        else:
            tsukaiwake_entries = Rgko12Utils.get_tsukaiwake_entries(index)
            for kanji, kana in tsukaiwake_entries:
                info_tag, pos_tag = self.get_pos_tags(kanji)
                local_count += self.parse_entry(kanji, kana, soup, pos_tag=pos_tag, ignore_expressions=True)
                
        if local_count == 0:
            print(f"No entry was parsed for file {filename_without_ext}") 
            
        return local_count