import os
import bs4

from utils import KanjiUtils
from core import Parser
from core.yomitan_dictionary import DicEntry
from config import DictionaryConfig
from handlers import process_unmatched_entries
from parsers.DAIJISEN.daijisen_utils import DaijisenUtils


class DaijisenParser(Parser):
    
    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        self.ignored_elements = {"k-v", "header", "index"} # mimageg
        self.expression_element = "subitem"
        
        
    def _handle_expression_entries(self, soup: bs4.BeautifulSoup):
        count = 0
        
        for sub_item in soup.find_all("SubItem"):
            headword_element = sub_item.find("headword", class_="見出")
            expression, readings = DaijisenUtils.extract_wari_text(headword_element)
            _, pos_tag = self.get_pos_tags(expression)
            
            if readings:
                for reading in readings:
                    entry = DicEntry(expression, reading, info_tag="", pos_tag=pos_tag)
                    yomitan_element = self.convert_element_to_yomitan(sub_item, ignore_expressions=False)
                    if yomitan_element:
                        entry.add_element(yomitan_element)
                        
                    self.dictionary.add_entry(entry)
                    count += 1
            
            else:
                entry = DicEntry(expression, "", info_tag="", pos_tag=pos_tag)
                yomitan_element = self.convert_element_to_yomitan(sub_item, ignore_expressions=False)
                if yomitan_element:
                    entry.add_element(yomitan_element)
                    
                self.dictionary.add_entry(entry)
                count += 1
                    
        return count
    
    
    def _process_file(self, filename: str, xml: str):
        local_count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Get keys from index
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")
        
        # Add any expression entries from subitems
        local_count += self._handle_expression_entries(soup)
        
        # Handle entries without keys
        reading = DaijisenUtils.extract_reading(soup)
        head_word = DaijisenUtils.extract_headword(soup)
        if not entry_keys:
            # Handle 大辞泉プラス entries
            if not head_word:
                head_word = DaijisenUtils.extract_plus_headword(soup)
                
                if head_word:
                    for term in head_word:
                        info_tag, pos_tag = self.get_pos_tags(term)
                        local_count += self.parse_entry(term, "", soup, pos_tag=pos_tag, search_rank=-1, ignore_expressions=True)
                else:
                    print(f"Did not find plus headword for file: {filename_without_ext}")
                    
            # Handle other entries that lack entry keys
            else:
                for term in head_word:
                    info_tag, pos_tag = self.get_pos_tags(term)
                    local_count += self.parse_entry(term, reading, soup, pos_tag=pos_tag, ignore_expressions=True)
                    
            return local_count
            
        # Normalise and match keys
        normalized_keys = self.normalize_keys(reading, entry_keys)
        matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
        matched_key_pairs = process_unmatched_entries(
            self, filename, entry_keys, matched_key_pairs, self.manual_handler
        )
        
        # Process each key pair
        for kanji_part, kana_part in matched_key_pairs:
            info_tag, pos_tag = "", ""
            if kanji_part:
                info_tag, pos_tag = self.get_pos_tags(kanji_part)
                local_count += self.parse_entry(
                    kanji_part, kana_part, soup, pos_tag=pos_tag, ignore_expressions=True
                )
            elif kana_part:
                local_count += self.parse_entry(
                    kana_part, "", soup, pos_tag=pos_tag, ignore_expressions=True
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