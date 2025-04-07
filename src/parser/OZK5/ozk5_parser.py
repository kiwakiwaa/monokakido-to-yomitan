import os
import json
import jaconv

from pathlib import Path
from tqdm import tqdm
from bs4 import BeautifulSoup

from ..parser import Parser
from .ozk5_utils import OZK5Utils
from .tag_map import TAG_MAPPING

from index import IndexReader
from utils import KanjiUtils
from yomitandic import create_html_element

class OZK5Parser(Parser):
    
    
    def __init__(self, dict_name, dict_path, index_path, jmdict_path):
        # XML files stored with the filename as key
        super().__init__(dict_name, dict_path)
        self.index_reader = IndexReader(index_path)
        
        self.waka_entries = {"entries": [], "reading_index": {}} # List to store 和歌 entries (I add the head word manually for these 269 entries)
        self.waka_path =  Path(index_path).parent / "waka_entries.json"
        self.audio_path =  Path(index_path).parent.parent / "audio/index.json"
        self.audio_index = self._init_audio_index()
    
    
    def export(self, output_path=None, export_waka_entries=False):
        self.dictionary.export(output_path)
        
        if export_waka_entries:
            with open(self.waka_path, 'w', encoding='utf-8') as f:
                json.dump(self.waka_entries, f, ensure_ascii=False, indent=2) 
                
        with open(self.audio_path, "w", encoding="utf-8") as f:
            json.dump(self.audio_index, f, ensure_ascii=False, indent=2)
            
            
    def get_target_tag(self, tag):
        return TAG_MAPPING.get(tag, "span")
    

    def handle_link_element(self, html_glossary, html_elements, data_dict, class_list):
        next_element = html_glossary.next_element
        if next_element and hasattr(next_element, 'name') and next_element.name:
            if next_element.name.lower() == "rectr":
                return create_html_element("span", content=html_elements, data=data_dict)
            
            next_element_class_list = next_element.get("class", [])
            if isinstance(next_element_class_list, str):
                next_element_class_list = next_element_class_list.split(" ")
                
            for cls in next_element_class_list:
                if cls in ['fill', "FM", "BM", "IM"]:
                    return create_html_element("span", content=html_elements, data=data_dict)
        elif "blue" in class_list:
            href_word = OZK5Utils.get_first_reference_word(html_glossary)
            return create_html_element("a", content=html_elements, href="?query="+href_word+"&wildcards=off")
        
        return None  

    
    def parse(self):
        count = 0
        
        for filename, xml in tqdm(self.dict_data.items(), desc="進歩", unit="事項"):
            filename_without_ext = os.path.splitext(filename)[0]
            entry_keys = self.index_reader.get_keys_for_file(filename_without_ext) 
            if not entry_keys: # Skip entries without keys
                continue
            
            soup = BeautifulSoup(xml, "xml") 
            if soup.find("付録タイトル") or soup.find("付録見出"): # Skip appendix entries
                continue
            
            # Handle Gendai entries
            reading = ""
            if soup.find("GendaiRef") or soup.find("GendaiHeadG"):
                reading = OZK5Utils.extract_gendai_reading(soup)
            else:
                reading = OZK5Utils.extract_reading(soup)
                
            # Find audio files
            audio_element = soup.find("a", class_="audio-play-button")
            audio_filename = ""
            if audio_element:
                audio_filename = audio_element.get("href", "")
    
            normalized_keys = self._normalize_keys(entry_keys, reading)
                
            # ----- Parsing of 和歌 entries ----- #
            result = self._handle_waka_entry(soup, reading, filename_without_ext, audio_filename)
            if result:
                continue
            
            # ----- Parsing of extracted information ----- #
            matched_key_pairs = KanjiUtils.match_kana_with_kanji(entry_keys)
            for kanji_part, kana_part in matched_key_pairs:
                count += self.parse_entry(kanji_part, kana_part, soup)
                
                if audio_filename:
                    entry_data = {
                        "kanji": kanji_part or "",  # Empty string if no kanji
                        "kana": kana_part,
                        "audio_file": audio_filename
                    }
                    
                    # Add to entries array and get index
                    entry_index = len(self.audio_index["entries"])
                    self.audio_index["entries"].append(entry_data)
                    
                    # Update kanji index if kanji exists
                    if kanji_part:
                        if kanji_part not in self.audio_index["kanji_index"]:
                            self.audio_index["kanji_index"][kanji_part] = []
                        self.audio_index["kanji_index"][kanji_part].append(entry_index)
                    
                    # Update kana index
                    if kana_part not in self.audio_index["kana_index"]:
                        self.audio_index["kana_index"][kana_part] = []
                    self.audio_index["kana_index"][kana_part].append(entry_index)
                            
            # Document any 和歌 entries in a list (Head word needs to be added manually, 269 entries)
            self._save_waka_entry(reading, filename_without_ext, soup)
            
        print(f"和歌事項を{len(self.waka_entries)}件見つかりました")
        print(f"{count}の事項を収録しました")
    
    
    def _handle_waka_entry(self, soup, reading, filename, audio_filename):
        count = 0
        waka_element = soup.find("rectr", class_="fill 分類")
        if waka_element:    
            waka_text = waka_element.text.strip()
            if waka_text == "和歌":
                with open(self.waka_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    
                waka_index = data["reading_index"][reading]
                head_word = data["entries"][waka_index]["head_word"]
                waka_filename = data["entries"][waka_index]["file"]
                
                if waka_filename == filename:
                    if head_word:
                        count += self.parse_entry(head_word, reading, soup, search_rank=1)
                        
                    count += self.parse_entry(reading, reading, soup, search_rank=1)
                    
                if audio_filename:
                    entry_data = {
                        "kanji": head_word or "",  # Empty string if no kanji
                        "kana": reading,
                        "audio_file": audio_filename
                    }
                    
                    # Add to entries array and get index
                    entry_index = len(self.audio_index["entries"])
                    self.audio_index["entries"].append(entry_data)
                    
                    # Update kanji index if kanji exists
                    if head_word:
                        if head_word not in self.audio_index["kanji_index"]:
                            self.audio_index["kanji_index"][head_word] = []
                        self.audio_index["kanji_index"][head_word].append(entry_index)
                    
                    # Update kana index
                    if reading not in self.audio_index["kana_index"]:
                        self.audio_index["kana_index"][reading] = []
                    self.audio_index["kana_index"][reading].append(entry_index)
                    
        return count
                

    def _save_waka_entry(self, reading, filename, soup):
        waka_element = soup.find("rectr", class_="fill 分類")
        if waka_element:
            entry_index = len(self.waka_entries["entries"])
            
            waka_text = waka_element.text.strip()
            if waka_text == "和歌":
                self.waka_entries["entries"].append({
                    "reading": reading,
                    "head_word": "",
                    "file": filename
                })
                if reading not in self.waka_entries["reading_index"]:
                    self.waka_entries["reading_index"][reading] = ""
                self.waka_entries["reading_index"][reading] = entry_index
    
    
    def _init_audio_index(self):
        index = {
            "meta": {
                "name": "旺文社 全訳古語辞典",
                "year": 2025,
                "version": 1,
                "media_dir": "media"
            },
            "entries": [],
            "kanji_index": {},
            "kana_index": {}
        }
        return index
    
    
    def _normalize_keys(self, keys, reading):
        normalized_keys = {}
        if KanjiUtils.is_only_hiragana(reading):
            for i, entry in enumerate(keys):
                normalized_keys[i] = jaconv.kata2hira(entry)
        else:
            for i, entry in enumerate(keys):
                normalized_keys[i] = jaconv.hira2kata(entry)
                
        return normalized_keys