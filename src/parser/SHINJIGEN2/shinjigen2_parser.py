import os
import bs4
import jaconv
from tqdm import tqdm
from typing import List

from utils import KanjiUtils
from parser.base.parser import Parser
from parser.base.manual_match_handler import process_unmatched_entries

from parser.SHINJIGEN2.tag_map import TAG_MAPPING
from parser.SHINJIGEN2.shinjigen2_utils import Shinjigen2Utils

from yomitandic import DicEntry

class ShinjigenParser(Parser):

    def __init__(self, dict_name: str, dict_path: str, index_path: str, jmdict_path: str):
        
        super().__init__(
            dict_name, dict_path, index_path
        )
        
        self.ignored_elements = {"entry-index"}
        self.expression_element = "JukugoItem"
        self.tag_mapping = TAG_MAPPING
        
    
    def _handle_jukugo_entry(self, soup: bs4.BeautifulSoup):
        local_count = 0
        
        for jukugo_item in soup.find_all("JukugoItem"):
            jukugo_headword, jukugo_reading = Shinjigen2Utils.extract_jukugo(jukugo_item)
            
            _, pos_tag = self.get_pos_tags(jukugo_headword)
            
            if jukugo_headword and jukugo_reading:
                entry = DicEntry(jukugo_headword, jukugo_reading, info_tag="", pos_tag=pos_tag)
                yomitan_element = self.convert_element_to_yomitan(jukugo_item, ignore_expressions=False)
                
                if yomitan_element:
                    entry.add_element(yomitan_element)
                    
                self.dictionary.add_entry(entry)
                local_count += 1
            
            else:
                return -1
             

        return local_count
        

    def _parse_file(self, filename: str, xml: str):
        local_count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Get keys from index
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        
        # TODO filter JIS, unicode, pinyin entry keys
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")
        
        if soup.find("JukugoG"):
            result += self._handle_jukugo_entry(soup)
            
            if result == -1:
                print(f"Jukugo entry missing headword or reading: {filename_without_ext}.\nEntry keys: {entry_keys}")
            
        
        # TODO normalising 漢字 entries by hiragana or katakana use 国語 reading first -> 音
        normalized_keys = self.normalize_keys("ひらがな", entry_keys)
        matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
        matched_key_pairs = process_unmatched_entries(
            self, filename, normalized_keys, matched_key_pairs, self.manual_handler
        )
        
        
        # Process each key pair
        for kanji_part, kana_part in matched_key_pairs:
            pos_tag = ""
            if kanji_part:
                _, pos_tag = self.get_pos_tags(kanji_part)
                local_count += self.parse_entry(kanji_part, kana_part, soup, pos_tag=pos_tag)
            elif kana_part:
                local_count += self.parse_entry(kana_part, "", soup, pos_tag=pos_tag)
                
        if local_count == 0:
            print(f"\nNo entry was parsed for file {filename_without_ext}")           
            
        return local_count