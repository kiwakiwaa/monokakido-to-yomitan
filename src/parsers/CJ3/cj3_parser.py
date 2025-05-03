import os
import regex as re
import bs4
import random
import dragonmapper.transcriptions as dt
from typing import List

from config import DictionaryConfig
from utils import CNUtils, FileUtils
from core import Parser
from handlers import AudioHandler, CJ3AudioHandler

from parsers.CJ3.cj3_utils import CJ3Utils


class CJ3Parser(Parser):

    def __init__(self, config: DictionaryConfig, dict_path: str, index_path: str, jmdict_path: str, audio_path: str):
        
        super().__init__(
            config, dict_path, index_path
        )
        
        self.ignored_elements = {"entry-index"}
        self.use_zhuyin = True
        
        self.audio_handler = CJ3AudioHandler(config.dict_name, audio_path)
            
        
    def _handle_missing_entry_keys(self, soup: bs4.BeautifulSoup, file: str) -> int:
        count = 0
        
        hanzi_contents = CJ3Utils.extract_from_field(soup, "headword", "小知識")
        if not hanzi_contents:
            hanzi_contents = CJ3Utils.extract_from_field(soup, "headword", "熟語")
        
        audio_filenames = CJ3Utils.extract_audio_links_from_headword(soup)
        
        pinyin_readings = CJ3Utils.extract_from_field(soup, "headword", "ピンイン")
        pinyin_readings = self.process_readings(pinyin_readings)
        
        for pinyin, hanzi in zip(pinyin_readings, hanzi_contents):
            zhuyin = CNUtils.pinyin_to_zhuyin(pinyin)
            
            if audio_filenames:
                for audio_filename in audio_filenames:
                    self.audio_handler.save_audio_entry(hanzi, pinyin, zhuyin, audio_filename)
                    
            count += self.parse_entry(hanzi, zhuyin if self.use_zhuyin else pinyin, soup)
            
        return count
    
    
    def process_readings(self, pinyin_readings: List[str]) -> List[str]:
        processed_readings = []
        for pinyin_reading in pinyin_readings:
            pinyin_reading = re.sub('//', '', pinyin_reading)
            pinyin_reading = re.sub(', ', ' ', pinyin_reading)
            pinyin_reading = re.sub(',', ' ', pinyin_reading)
            if pinyin_reading.startswith('-'):
                pinyin_reading = pinyin_reading[1:]
            
            processed_readings.append(pinyin_reading)
                
        return processed_readings
        
    
    def _process_file(self, filename: str, xml: str) -> int:
        count = 0
        filename_without_ext = os.path.splitext(filename)[0]
        
        # Get keys from index
        entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
        hanzi_keys = [k for k in entry_keys if CNUtils.is_hanzi(k)]
        pinyin_keys = [k for k in entry_keys if k not in hanzi_keys]
        
        # Parse xml
        soup = bs4.BeautifulSoup(xml, "xml")
        audio_filenames = CJ3Utils.extract_audio_links_from_headword(soup)
        
        # Handl entries without keys
        if not entry_keys:
            return self._handle_missing_entry_keys(soup, filename_without_ext)
        
        original_readings = CJ3Utils.extract_from_field(soup, "headword", "ピンイン")
        
        # Check if no pinyin readings were extracted
        if not original_readings:
            print(f"\nNo pinyin extracted from: {filename_without_ext}\nentries: {entry_keys}")
            
        has_parentheses = any('(' in r for r in original_readings)
        if len(hanzi_keys) == 2 and len(original_readings) == 1 and '(' in original_readings[0] and ')' in original_readings[0]:
            pinyin_reading = original_readings[0]
            start = pinyin_reading.find('(')
            end = pinyin_reading.find(')')
            
            without_parentheses = pinyin_reading[:start] + pinyin_reading[end+1:]
            with_parentheses = pinyin_reading[:start] + pinyin_reading[start+1:end] + pinyin_reading[end+1:]
            
            hanzi_keys_sorted = sorted(hanzi_keys, key=len)
                
            # Process first hanzi with the first reading
            zhuyin_reading = CNUtils.pinyin_to_zhuyin(without_parentheses)
                
            if audio_filenames:
                for audio_filename in audio_filenames:
                    self.audio_handler.save_audio_entry(hanzi_keys_sorted[0], without_parentheses, zhuyin_reading, audio_filename)
                    
            count += self.parse_entry(hanzi_keys_sorted[0], zhuyin_reading if self.use_zhuyin else without_parentheses, soup)
            
            # Process second hanzi with the second reading
            zhuyin_reading = CNUtils.pinyin_to_zhuyin(with_parentheses)
                
            if audio_filenames:
                for audio_filename in audio_filenames:
                    self.audio_handler.save_audio_entry(hanzi_keys_sorted[1], with_parentheses, zhuyin_reading, audio_filename)
                    
            count += self.parse_entry(hanzi_keys_sorted[1], zhuyin_reading if self.use_zhuyin else with_parentheses, soup)
            
        else:
            # For other cases, process normally
            processed_readings = self.process_readings(original_readings[:])
            for pinyin_reading in processed_readings:
                zhuyin_reading = CNUtils.pinyin_to_zhuyin(pinyin_reading)
                    
                for hanzi in hanzi_keys:
                    if audio_filenames:
                        for audio_filename in audio_filenames:
                            self.audio_handler.save_audio_entry(hanzi, pinyin_reading, zhuyin_reading, audio_filename)
                            
                    if hanzi == "洛桑桑盖": 
                        if self.use_zhuyin:
                            count += self.parse_entry("洛桑", "ㄌㄨㄛˋㄙㄤ", soup)
                            count += self.parse_entry("桑盖", "ㄌㄨㄛˋㄙㄤ", soup)
                        else:
                            count += self.parse_entry("洛桑", "Luòsāng・Sānggài", soup)
                            count += self.parse_entry("桑盖", "Luòsāng・Sānggài", soup)
                    else:
                        count += self.parse_entry(hanzi, zhuyin_reading if self.use_zhuyin else pinyin_reading, soup)
                    
            # Process any 外字 hanzi that haven't been parsed
            gaiji_characters = CJ3Utils.extract_unicode_from_gaiji(soup)
            for gaiji in gaiji_characters:
                if gaiji not in hanzi_keys:
                    for pinyin_reading in processed_readings:
                        zhuyin_reading = CNUtils.pinyin_to_zhuyin(pinyin_reading)
                                
                        if audio_filenames:
                            for audio_filename in audio_filenames:
                                self.audio_handler.save_audio_entry(gaiji, pinyin_reading, zhuyin_reading, audio_filename)
                                
                        count += self.parse_entry(gaiji, zhuyin_reading if self.use_zhuyin else pinyin_reading, soup)
                        
        return count