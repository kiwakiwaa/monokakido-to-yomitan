import os
import jaconv

from bs4 import BeautifulSoup
from tqdm import tqdm

from ..old_parser import OldParser
from utils.sudachi_tags import sudachi_rules
from parser.base.manual_match_handler import ManualMatchHandler, process_unmatched_entries

from .tag_map import TAG_MAPPING
from .knje_utils import KNJEUtils

from index import IndexReader
from utils import KanjiUtils, FileUtils
from yomitandic import DicEntry, create_html_element


class KNJEParser(OldParser):
    
    IGNORED_ELEMENTS = {"header", "entry-index"}
    EXPRESSION_ELEMENT = "subitem"
    
    def __init__(self, dict_name, dict_path, index_path, jmdict_path):
        super().__init__(dict_name, dict_path)
        self.index_reader = IndexReader(index_path)
        self.jmdict_data = FileUtils.load_term_banks(jmdict_path)
        self.manual_handler = ManualMatchHandler()
        
        
    def parse(self):
        count = 0
        
        bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit} [経過: {elapsed} | 残り: {remaining}]{postfix}"
        with tqdm(total=len(self.dict_data.items()), desc="進歩", bar_format=bar_format, unit="事項") as pbar:
            for filename, xml in self.dict_data.items():
                local_count = 0
                filename_without_ext = os.path.splitext(filename)[0]
                entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
                if not entry_keys:
                    print(f"Found no entry keys for file: {filename_without_ext}")
                
                if count > 200:
                    break
                
                soup = BeautifulSoup(xml, "xml")
                
                # Add any expression entries from subitems
                local_count += self._handle_expression_entries(soup)
                reading = KNJEUtils.extract_reading(soup)
                head_word = KNJEUtils.extract_headword(soup)
                
                if reading and any(KanjiUtils.is_kanji(c) for c in reading):
                    print(f"Found reading with kanji: {reading}, File: {filename_without_ext}")
                
                
                if head_word and reading:
                    
                    for term in head_word:
                        info_tag, pos_tag = self.get_pos_tags(term)
                        local_count += self.parse_entry(term, reading, soup, pos_tag=pos_tag, ignore_expressions=True)
                        
                        # Add any kana only entries if theres a "uk" tag (usually written using kana alone)
                        info_tags = info_tag.split()
                        if "uk" in info_tags:
                            local_count += self.parse_entry(reading, "", soup, pos_tag=pos_tag, ignore_expressions=True)
                                    
                elif reading:
                    local_count += self.parse_entry(reading, "", ignore_expressions=True)
                else:
                    print(f"Found no headword or reading for: {filename_without_ext}")         
                            
                count += local_count
                pbar.update(1)
                pbar.set_postfix_str(f"{count}の項目を収録しました。")     
                if local_count == 0:
                    print(f"No entry was parsed for file {filename_without_ext}") 
        
                
    def _handle_expression_entries(self, soup):
        count = 0
        
        for sub_item in soup.find_all("SubItem"):
            headword_element = sub_item.find("subheadword")
            if not headword_element:
                continue
            
            headword = headword_element.text.strip()
            _, pos_tag = self.get_pos_tags(headword)
            
            entry = DicEntry(headword, "", info_tag="", pos_tag=pos_tag)
            
            yomitan_element = self.convert_element_to_yomitan(sub_item, ignore_expressions=False)
            if yomitan_element:
                entry.add_element(yomitan_element)
                count += 1
                    
        return count
                
                
    def handle_link_element(self, html_glossary, html_elements, data_dict, class_list):
        text = html_glossary.get_text(strip=True, separator=" ")
        
        # Ignore links with "本文"
        if text == "本文":
            return None
        
        # Remove <sup> tags
        for sup in html_glossary.find_all("sup"):
            sup.extract()
            
        # Extract text again after removing <sup>
        text = html_glossary.get_text(strip=True, separator=" ")

        # Remove readings in parentheses (e.g., "（⇒はいせつ）")
        text = text.split("（⇒")[0].strip()
        
        return create_html_element("a", content=html_elements, href="?query="+text+"&wildcards=off")
    
    
    def get_image_path(self, html_glossary):
        return html_glossary.get("src", "")
                
    
    def get_target_tag(self, tag):
        return TAG_MAPPING.get(tag, "span")
    
    
    def get_pos_tags(self, term):   
        info_tag, pos_tag = self.jmdict_data.get(term, ["", ""])
        
        # Didnt find a POS tag match in Jmdict, use sudachi instead
        if not pos_tag:
            sudachi_tag = sudachi_rules(term)
            return info_tag, sudachi_tag
            
        return info_tag, pos_tag
    
    
    def _normalize_keys(self, reading, entry_keys):
        if KanjiUtils.is_only_hiragana(reading):
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]
        else:
            normalized_keys = [jaconv.hira2kata(entry) for entry in entry_keys]
            
        return normalized_keys
                