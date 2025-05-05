import os
import bs4
from typing import List, Dict, Optional

from core import Parser
from config import DictionaryConfig

from parsers.KJT.kjt_utils import KJTUtils

class KJTParser(Parser):
	
	def __init__(self, config: DictionaryConfig):
		super().__init__(config)
		
		self.expression_element = "subitem"
	
	def _process_file(self, filename: str, xml: str):
		count = 0
		filename_without_ext = os.path.splitext(filename)[0]
		
		# Parse xml
		soup = bs4.BeautifulSoup(xml, "xml")
		oyaji_entries = KJTUtils.extract_all_oyaji(soup)
		
		if soup.find("SubItem"):
			jukugo_data = KJTUtils.get_all_jukugo(soup, "SubItem")
			
			for entry in jukugo_data:
				count += self._process_jukugo_entry(
					filename=filename,
					element=entry['element'],
					raw_headword=entry['raw']['headword'],
					raw_reading=entry['raw']['reading'],
					processed_headwords=entry['processed']['headwords'],
					processed_readings=entry['processed']['readings']
				)
				
		if soup.find("ZinmeiSyomeiHeadG"):
			jukugo_data = KJTUtils.get_all_jukugo(soup, "ZinmeiSyomeiHeadG")
			
			for entry in jukugo_data:
				count += self._process_jukugo_entry(
					filename=filename,
					element=entry['element'],
					raw_headword=entry['raw']['headword'],
					raw_reading=entry['raw']['reading'],
					processed_headwords=entry['processed']['headwords'],
					processed_readings=entry['processed']['readings']
				)
		
		for oyaji in oyaji_entries:
			count += self.parse_entry(oyaji, "", soup, ignore_expressions=True)
	
		if count == 0:
			print(f"\nNo entry was parsed for file {filename_without_ext}")
			
		return count
	
	
	def _process_jukugo_entry(self, filename, element, raw_headword, raw_reading, processed_headwords, processed_readings, do_print=False):
		count = 0
		if do_print:
			print(f"\n--- File: {filename} ---")
			
			print(f"Original: {raw_headword} → {processed_headwords}")
			print(f"Processed: {raw_reading} → {processed_readings}")
		
		for hw, rd in zip(processed_headwords, processed_readings):
			count += self.parse_entry(hw, rd, element, ignore_expressions=False)
			
		return count