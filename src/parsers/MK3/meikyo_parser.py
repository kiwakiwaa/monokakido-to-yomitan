import os
import bs4

from utils import KanjiUtils
from yomitandic import DicEntry

from core import Parser
from config import DictionaryConfig
from handlers import process_unmatched_entries
from parsers.MK3.meikyo_utils import MeikyoUtils

class MeikyoParser(Parser):
    
    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        
        self.ignored_elements = {"link", "meta", "entry-index", "index", "key"}
        self.expression_element = "child-items"
        
        
    def _handle_expression_entries(self, soup: bs4.BeautifulSoup):
        count = 0
        
        for child in soup.find_all("child-item"):
            head_element = child.find("headword", class_="子見出し")
            if not head_element:
                print(f"Found no headword element for expression in: {child}")
                continue
            
            expression, reading = MeikyoUtils.extract_ruby_text(head_element)
            _, pos_tag = self.get_pos_tags(expression)
            
            if not expression:
                print(f"No expression in: {child}")
                continue
            
            if reading:
                entry = DicEntry(expression, reading, pos_tag=pos_tag)
                yomitan_element = self.convert_element_to_yomitan(child, ignore_expressions=False)
                if yomitan_element:
                    entry.add_element(yomitan_element)
                    self.dictionary.add_entry(entry)
                    count += 1
            else:
                print(f"No reading for expression: {expression} in:\n{child}")

                    
        return count
    
    
    def _process_file(self, filename: str, xml: str) -> int:
        local_count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Get keys from index
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")
        self._handle_expression_entries(soup)
        
        if not entry_keys:
            print(f"Found entry without keys: {filename_without_ext}")
            
        reading = MeikyoUtils.extract_reading(soup)
        if not reading:
            print(f"Found no reading: {filename_without_ext}")
            
        # Normalise and match keys
        normalized_keys = self.normalize_keys(reading, entry_keys)
        matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
        matched_key_pairs = process_unmatched_entries(
            self, filename, entry_keys, matched_key_pairs, self.manual_handler
        )
        
        # Determine search ranking (rank kana entries higher)
        has_kanji = any(kanji_part for kanji_part, _ in matched_key_pairs)
        search_rank = 1 if not has_kanji else 0 
        self.keys = matched_key_pairs
        
        # Process each key pair
        for kanji_part, kana_part in matched_key_pairs:
            info_tag, pos_tag = "", ""
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
                
        if local_count == 0:
            print(f"No entry was parsed for file {filename_without_ext}") 
            
        return local_count