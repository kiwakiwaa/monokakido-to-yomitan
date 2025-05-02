import os
import bs4
import dragonmapper.transcriptions as dt
from typing import List

from config import DictionaryConfig
from utils import CNUtils, FileUtils
from core import Parser
from handlers import AudioHandler

from parsers.CJ3.cj3_utils import CJ3Utils


class CJ3Parser(Parser):

    def __init__(self, config: DictionaryConfig, dict_path: str, index_path: str, jmdict_path: str, audio_path: str):
        
        super().__init__(
            config, dict_path, index_path
        )
        
        self.ignored_elements = {"entry-index"}
        self.use_zhuyin = True
        
        self.audio_handler = AudioHandler(config.dict_name, audio_path)
            
        
    def _handle_missing_entry_keys(self, soup: bs4.BeautifulSoup) -> int:
        count = 0
        
        hanzi_contents = CJ3Utils.extract_from_field(soup, "headword", "小知識")
        if not hanzi_contents:
            hanzi_contents = CJ3Utils.extract_from_field(soup, "headword", "熟語")
        
        audio_filenames = CJ3Utils.extract_audio_links_from_headword(soup)
        
        pinyin_readings = CJ3Utils.extract_from_field(soup, "headword", "ピンイン")
        for pinyin, hanzi in zip(pinyin_readings, hanzi_contents):
            if self.use_zhuyin:
                pinyin = CNUtils.pinyin_to_zhuyin(pinyin)
            
            if audio_filenames:
                for audio_filename in audio_filenames:
                    self.audio_handler.save_audio_entry(hanzi, pinyin, audio_filename)
                    
            count += self.parse_entry(hanzi, pinyin, soup)
            
        return count
        
        
    def _handle_unmatched_entries(self, soup: bs4.BeautifulSoup, entry_keys: List[str]) -> int:
        count = 0
        pinyin_readings = CJ3Utils.extract_from_field(soup, "headword", "ピンイン")
        hanzi_entries = [k for k in entry_keys if CNUtils.is_hanzi(k)]
        
        audio_filenames = CJ3Utils.extract_audio_links_from_headword(soup)
        
        for pinyin_reading in pinyin_readings:
            if self.use_zhuyin:
                pinyin_reading = CNUtils.pinyin_to_zhuyin(pinyin_reading)
                
            for hanzi in hanzi_entries:
                if audio_filenames:
                    for audio_filename in audio_filenames:
                        self.audio_handler.save_audio_entry(hanzi, pinyin_reading, audio_filename)
                        
                count += self.parse_entry(hanzi, pinyin_reading, soup)
            
        return count
        
    
    def _process_file(self, filename: str, xml: str) -> int:
        count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Get keys from index
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")
        audio_filenames = CJ3Utils.extract_audio_links_from_headword(soup)
        
        # Handl entries without keys
        if not entry_keys:
            return self._handle_missing_entry_keys(soup)
        
        # Match keys with hanzi
        matched_key_pairs = CNUtils.map_pinyin_to_hanzi(entry_keys)
        if entry_keys and not matched_key_pairs:
            count += self._handle_unmatched_entries(soup, entry_keys)
        
        # Process each key pair
        #info_tag, pos_tag = "", ""

        for hanzi_part, pinyin_part in matched_key_pairs:
            if hanzi_part:
                if self.use_zhuyin:
                    pinyin_part = CNUtils.pinyin_to_zhuyin(pinyin_part)
                else:
                    pinyin_part = dt.to_pinyin(pinyin_part, accented=True)
                
                if audio_filenames:
                    for audio_filename in audio_filenames:
                        self.audio_handler.save_audio_entry(hanzi_part, pinyin_part, audio_filename)
                
                #info_tag, pos_tag = self.get_pos_tags(hanzi_part)
                count += self.parse_entry(hanzi_part, pinyin_part, soup)
                
                
        # Process any 外字 hanzi that haven't been parsed
        gaiji_characters = CJ3Utils.extract_unicode_from_gaiji(soup)
        
        hanzi_entries = [k for k in entry_keys if CNUtils.is_hanzi(k)]
        pinyin_readings = CJ3Utils.extract_from_field(soup, "headword", "ピンイン")
        
        for gaiji in gaiji_characters:
            if gaiji not in hanzi_entries:
                for pinyin_reading in pinyin_readings:
                    if self.use_zhuyin:
                        pinyin_part = CNUtils.pinyin_to_zhuyin(pinyin_reading)
                    
                    if audio_filenames:
                        for audio_filename in audio_filenames:
                            self.audio_handler.save_audio_entry(gaiji, pinyin_reading, audio_filename)
        
                    count += self.parse_entry(gaiji, pinyin_reading, soup)
        
        return count