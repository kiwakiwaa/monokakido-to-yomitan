import os
import random
import jaconv

from bs4 import BeautifulSoup
from tqdm import tqdm

from ..parser import Parser
from utils.sudachi_tags import sudachi_rules
from parser.base.manual_match_handler import ManualMatchHandler, process_unmatched_entries

from .daijisen_utils import DaijisenUtils
from .tag_map import TAG_MAPPING

from index import IndexReader
from utils import KanjiUtils, FileUtils
from yomitandic import DicEntry, create_html_element


class DaijisenParser(Parser):
    
    IGNORED_ELEMENTS = {"k-v", "header", "index"}
    EXPRESSION_ELEMENT = "subitem"
    
    def __init__(self, dict_name, dict_path, index_path, jmdict_path):
        super().__init__(dict_name, dict_path)
        self.index_reader = IndexReader(index_path)
        self.jmdict_data = FileUtils.load_term_banks(jmdict_path)
        self.manual_handler = ManualMatchHandler()
        
        
    def _handle_expression_entries(self, soup):
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
        
            
    def parse(self):
        count = 0
        
        shuffled_items = list(self.dict_data.items())
        random.shuffle(shuffled_items)
        bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit} [経過: {elapsed} | 残り: {remaining}]{postfix}"
        with tqdm(total=len(self.dict_data.items()), desc="進歩", bar_format=bar_format, unit="事項") as pbar:
            for filename, xml in shuffled_items:
                local_count = 0
                
                filename_without_ext = os.path.splitext(filename)[0]
                entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
                
                soup = BeautifulSoup(xml, "xml")
                
                # Add any expression entries from subitems
                local_count += self._handle_expression_entries(soup)
                reading = DaijisenUtils.extract_reading(soup)
                head_word = DaijisenUtils.extract_headword(soup)
                
                if not entry_keys:
                    if not head_word:
                        head_word = DaijisenUtils.extract_plus_headword(soup)
                        
                        if head_word:
                            for term in head_word:
                                info_tag, pos_tag = self.get_pos_tags(term)
                                local_count += self.parse_entry(term, "", soup, pos_tag=pos_tag, ignore_expressions=True)
                        else:
                            print(f"Did not find plus headword for file: {filename_without_ext}")
                    else:
                        for term in head_word:
                            info_tag, pos_tag = self.get_pos_tags(term)
                            local_count += self.parse_entry(term, reading, soup, pos_tag=pos_tag, ignore_expressions=True)
                            
                    pbar.update(1)
                    continue
                    
                normalized_keys = self._normalize_keys(reading, entry_keys)
                matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
                matched_key_pairs = process_unmatched_entries(self, filename, entry_keys, matched_key_pairs, self.manual_handler)
                
                for kanji_part, kana_part in matched_key_pairs:
                    info_tag, pos_tag = "", ""
                    if kanji_part:
                        info_tag, pos_tag = self.get_pos_tags(kanji_part)
                        local_count += self.parse_entry(kanji_part, kana_part, soup, pos_tag=pos_tag, ignore_expressions=True)
                    elif kana_part:
                        local_count += self.parse_entry(kana_part, "", soup, pos_tag=pos_tag, ignore_expressions=True)
                    
                    
                # Add any kana only entries if theres a "uk" tag (usually written using kana alone)
                info_tags = info_tag.split()
                if "uk" in info_tags:
                    # Find unique kana parts that haven't been parsed yet
                    unique_kana_parts = set()
                    for _, kana_part in matched_key_pairs:
                        # Check if the kana part hasn't been added before
                        if kana_part not in unique_kana_parts and not any(kanji is None and kana_part == kana for kanji, kana in matched_key_pairs):
                            unique_kana_parts.add(kana_part)
                            local_count += self.parse_entry(kana_part, "", soup, pos_tag=pos_tag, ignore_expressions=True)
        
                                            
                count += local_count
                pbar.update(1)
                pbar.set_postfix_str(f"{count}の項目を収録しました。")     
                if local_count == 0:
                    print(f"No entry was parsed for file {filename_without_ext}") 
            
            
    def _normalize_keys(self, reading, entry_keys):
        if KanjiUtils.is_only_hiragana(reading):
            normalized_keys = [jaconv.kata2hira(entry) for entry in entry_keys]
        else:
            normalized_keys = [jaconv.hira2kata(entry) for entry in entry_keys]
            
        return normalized_keys
            
            
    def get_pos_tags(self, term):   
        info_tag, pos_tag = self.jmdict_data.get(term, ["", ""])
        
        # Didnt find a POS tag match in Jmdict, use sudachi instead
        if not pos_tag:
            sudachi_tag = sudachi_rules(term)
            return info_tag, sudachi_tag
            
        return info_tag, pos_tag
            
            
    def get_target_tag(self, tag):
        return TAG_MAPPING.get(tag, "span")
    
    
    def handle_link_element(self, html_glossary, html_elements, data_dict, class_list):
        href = html_glossary.get("href", "")
        if href and href.startswith("map:ll="):
            # Extract coordinates from the href and create an Apple maps link
            try:
                coords_part = href.split("map:ll=")[1].split("&")[0]
                lat, lng = coords_part.split(",")
                
                apple_maps_url = f"https://maps.apple.com/?ll={lat},{lng}"
                return create_html_element("a", content=html_elements, href=apple_maps_url)
            except Exception as e:
                print(f"Error processing map coordinates: {e}")
                
        elif "blue" in class_list:
            href_word = DaijisenUtils.get_first_reference_word(html_glossary)
            return create_html_element("a", content=html_elements, href="?query="+href_word+"&wildcards=off")
        
        else:
            return create_html_element("span", content=html_elements, data=data_dict)
    
    
    def get_image_path(self, html_glossary):
        # Check if the src attribute ends with .heic
        src_attr = html_glossary.get("src", "")
        if src_attr.lower().endswith('.heic'):
            jpg_src = src_attr[:-5] + '.avif'
            return jpg_src
    
        return ""