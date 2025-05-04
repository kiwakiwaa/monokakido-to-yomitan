import os
import json
import bs4
from pathlib import Path
from typing import Dict, List, Optional

from utils import KanjiUtils

from core import Parser
from config import DictionaryConfig
from handlers import AudioHandler, process_unmatched_entries
from parsers.OZK5.ozk5_utils import OZK5Utils
    
class OZK5Parser(Parser):
    
    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        
        # List to store 和歌 entries (I add the head word manually for these 269 entries)
        self.waka_entries = {"entries": [], "reading_index": {}}
        self.waka_path =  Path(config.index_path).parent / "waka_entries.json"
        self.audio_handler = AudioHandler(config.dict_name, config.audio_path)
            
            
    def _process_file(self, filename: str, xml: str):
        local_count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Get keys from index
        entry_keys = self.index_reader.get_keys_for_file(filename_without_ext) 
        
        # Skip entries without keys
        if not entry_keys:
            return local_count
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml") 
        
        # Skip appendix entries
        if soup.find("付録タイトル") or soup.find("付録見出"):     
            return local_count
        
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
            
        # ----- Parsing of 和歌 entries ----- #
        waka_element = soup.find("rectr", class_="fill 分類")
        if waka_element and waka_element.text.strip() == "和歌":
            local_count += self._handle_waka_entry(soup, reading, filename_without_ext, audio_filename)
            self._save_waka_entry(soup, reading, filename_without_ext)
        
        # ----- Parsing of normal entries ----- #
        else:
            normalized_keys = self.normalize_keys(reading, entry_keys)
            matched_key_pairs = KanjiUtils.match_kana_with_kanji(normalized_keys)
            matched_key_pairs = process_unmatched_entries(
                self, filename, normalized_keys, matched_key_pairs, self.manual_handler
            )
            
            # Determine search ranking (rank kana entries higher)
            has_kanji = any(kanji_part for kanji_part, _ in matched_key_pairs)
            search_rank = 1 if not has_kanji else 0 
            
            for kanji_part, kana_part in matched_key_pairs:
                pos_tag = ""
                if kanji_part:
                    _, pos_tag = self.get_pos_tags(kanji_part)
                    local_count += self.parse_entry(
                        kanji_part, kana_part, soup, pos_tag=pos_tag, search_rank=search_rank
                    )
                elif kana_part:
                    local_count += self.parse_entry(
                        kana_part, "", soup, search_rank=search_rank
                    )
                
                if audio_filename:
                    self.audio_handler.save_audio_entry(kanji_part, kana_part, audio_filename)
                    
        return local_count
        
        
    def _handle_waka_entry(self, soup: bs4.BeautifulSoup, reading: str,
                           filename: str, audio_filename: str):
        count = 0
        with open(self.waka_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        waka_index = data["reading_index"][reading]
        head_word = data["entries"][waka_index]["head_word"]
        waka_filename = data["entries"][waka_index]["file"]
        
        if waka_filename == filename:
            if head_word:
                count += self.parse_entry(head_word, reading, soup)
                
            count += self.parse_entry(reading, reading, soup)
            
        if audio_filename:
            self.audio_handler.save_audio_entry(head_word or "", reading, audio_filename)
                    
        return count
    
    
    def _save_waka_entry(self, soup: bs4.BeautifulSoup, reading: str, filename: str):
        entry_index = len(self.waka_entries["entries"])
        
        self.waka_entries["entries"].append({
            "reading": reading,
            "head_word": "",
            "file": filename
        })
        if reading not in self.waka_entries["reading_index"]:
            self.waka_entries["reading_index"][reading] = ""
            
        self.waka_entries["reading_index"][reading] = entry_index
        
        
    def export(self, output_path: Optional[str] = None, export_waka_entries: bool = False):
        self.dictionary.export(output_path)
        
        if export_waka_entries:
            with open(self.waka_path, 'w', encoding='utf-8') as f:
                json.dump(self.waka_entries, f, ensure_ascii=False, indent=2) 
                
        self.audio_handler.export()
    