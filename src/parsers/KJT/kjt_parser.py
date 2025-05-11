import os
import bs4
import jaconv
import regex as re
from typing import List, Dict, Optional

from core import Parser
from config import DictionaryConfig
from utils import KanjiUtils
from index import JukugoIndexReader

from parsers.KJT.kjt_utils import KJTUtils

class KJTParser(Parser):
	
	def __init__(self, config: DictionaryConfig):
		super().__init__(config)
		self.jukugo_index_reader = JukugoIndexReader(os.path.join(os.path.dirname(config.index_path), "jyukugo_prefix.tsv"))
	
	
	def get_search_rank(self, reading: str) -> int:
		
		def is_archaic_onyomi(reading: str) -> bool:
			ARCHAIC_PATTERNS = [
				r"クヮ",
				r"グヮ",
				r"クワ",
				r"グワ",
				r"セツヱウ",
				r"セヅヱウ",
				r"シツヱウ",
				r"シヅヱウ",
				r"ヤクワン",
				r"スヰ",
				r"ツヰ",
				r"ヰ",
				r"ヱ",
				r"クヰ",
				r"グヰ",
				r"シヤ",
				r"チヤ",
				r"テフ",
				r"テウ",
				r"バウ",
				r"パウ",
				r"マウ",
				r"ガウ",
				r"タウ"
			]

			kata_reading = jaconv.hira2kata(reading)
			
			# Check against known archaic patterns
			for pattern in ARCHAIC_PATTERNS:
				if re.search(pattern, kata_reading):
					return True
				
			return False
		
		if is_archaic_onyomi(reading):
			return -2
		
		return len(reading)
	
	
	def _handle_busyu_entry(self, soup: bs4.BeautifulSoup) -> int:
		count = 0
		busyu_headwords, readings = KJTUtils.extract_busyu(soup)

		if not busyu_headwords:
			if "おと" in readings:
				busyu_headwords.append("音")
			elif "つ" in readings: 
				busyu_headwords.append("⺍")
			elif "つき" in readings: 
				busyu_headwords.append("月")
			elif "ぶん" in readings: 
				busyu_headwords.append("文")
			elif "ちち" in readings: 
				busyu_headwords.append("父")	
			elif "く" in readings: 
				busyu_headwords.append("𠂊")
				
		for busyu in busyu_headwords:
			count += self.parse_entry(busyu, "", soup, search_rank=-1, ignore_expressions=False)
				
		return count
	
	
	def _process_file(self, filename: str, xml: str):
		count = 0
		filename_without_ext = os.path.splitext(filename)[0]
		entry_keys = list(set(self.index_reader.get_keys_for_file(filename_without_ext)))
		kanji_keys = [k for k in entry_keys if any(KanjiUtils.is_kanji(c) for c in k)]
		reading_keys = [k for k in entry_keys if k not in kanji_keys and k != '〓']
		
		# Parse xml
		soup = bs4.BeautifulSoup(xml, "xml")
		
		if soup.find("SubItem"):
			count += self._handle_jukugo(soup, filename_without_ext)
				
		if soup.find("BusyuHeadG") and not entry_keys:
			count += self._handle_busyu_entry(soup)
		
		for kanji in kanji_keys:
			if sum(KanjiUtils.is_kanji(c) for c in kanji) > 1:
				continue
			
			for reading in reading_keys:
				reading = jaconv.kata2hira(reading)
				search_rank = self.get_search_rank(reading)
				count += self.parse_entry(kanji, reading, soup, ignore_expressions=True)
				
		if count == 0:
			if soup.find("ZinmeiSyomeiHeadG") and not self.is_gaiji_entry(soup):
				jukugo_data = KJTUtils.get_all_jukugo(soup, "ZinmeiSyomeiHeadG")
				for entry in jukugo_data:
					for headword in entry['processed']['headwords']:
						for reading in entry['processed']['readings']:
							reading = jaconv.kata2hira(reading)
							search_rank = self.get_search_rank(reading)
							count += self.parse_entry(headword, reading, soup)
	
					return count
			
		return count
	
	
	def is_gaiji_entry(self, soup):
		oyaji_head = soup.find("OyajiHeadG")
		if not oyaji_head:
			oyaji_head = soup.find("ZinmeiSyomeiHeadG")
			if not oyaji_head:
				return False
		
		headwords = oyaji_head.find_all("headword")
		for headword in headwords:
			if headword.find("img", class_="gaiji"):
				return True
		
		return False
	
	
	def _handle_jukugo(self, soup: bs4.BeautifulSoup, filename_without_ext: str) -> int:
		count = 0
		jukugo_entries = self.jukugo_index_reader.get_organized_entries_for_page(filename_without_ext)
		for subitem in soup.find_all("SubItem"):
			full_id = subitem.get("id")
			item_id = KJTUtils.get_item_id(full_id)
			
			jukugo_entry = jukugo_entries.get(item_id)

			kanji_forms = jukugo_entry['kanji']
			reading_forms = jukugo_entry['readings']
			
			for kanji in kanji_forms:
				for reading in reading_forms:
					if "〓" in kanji or "〓" in reading:
						continue
					
					reading = jaconv.kata2hira(reading)
					search_rank = self.get_search_rank(reading)
					count += self.parse_entry(kanji, reading, subitem, search_rank=search_rank, ignore_expressions=False)
			
		return count
	