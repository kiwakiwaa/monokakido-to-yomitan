from typing import List, Dict, Optional
import bs4
import os

from parser.appendix import AppendixHandler
from parser.RGKO12.tag_map import TAG_MAPPING
from parser.RGKO12.rgko12_strategies import Rgko12LinkHandlingStrategy, Rgko12ImageHandlingStrategy
from yomitandic import Dictionary

class Rgko12AppendixHandler(AppendixHandler):
	def __init__(self, dictionary: Dictionary, directory_path: str):
		super().__init__(
			dictionary, 
			directory_path,
			link_handling_strategy=Rgko12LinkHandlingStrategy(),
			image_handling_strategy=Rgko12ImageHandlingStrategy()
		)
		self.tag_mapping = TAG_MAPPING
		self.initialize_html_converter()
		
		self.appendix_entries = {
			"編集のことば": "【例解】付録：編集のことば",
			"辞典で新たな世界をひらこう": "【例解】付録：この辞典で新たな世界をひらこう",
			"この辞典の使い方": "【例解】付録：この辞典の使い方",
			"辞典を100倍活用する方法": "【例解】付録：辞典を100倍活用する方法",
			"記号一覧": "【例解】付録：記号一覧",
			"編集された先生方": "【例解】付録：編集された先生方",
			"人の性格に関することば": "【例解】付録：人の性格に関することば", 
			"敬語の使い方": "【例解】付録：敬語の使い方",
			"ものの数え方": "【例解】付録：ものの数え方",
			"ことばのはたらき": "【例解】付録：ことばのはたらき",
			"ことばの組み合わせ": "【例解】付録：ことばの組み合わせ",
			"符号の使い方": "【例解】付録：符号の使い方",
			"かなづかいきまり": "【例解】付録：かなづかいきまり",
			"送りがなのきまり": "【例解】付録：送りがなのきまり",
			"かたかなで書くことば": "【例解】付録：かたかなで書くことば",
			"ローマ字": "【例解】付録：ローマ字",
			"アクセントと方言": "【例解】付録：アクセントと方言",
			"原こう用紙・手紙の書き方": "【例解】付録：原こう用紙・手紙の書き方",
			"とくべつな読みのことば": "【例解】付録：とくべつな読みのことば",
			"印刷文字と手書き文字": "【例解】付録：印刷文字と手書き文字",
			"日本の旧国名": "【例解】付録：日本の旧国名",
			"小倉百人一首": "【例解】付録：小倉百人一首",
			"例解学習国語辞典 付録一覧": "【例解】付録",
			"【例解】付録": "【例解】付録"
		}
		
		
	def parse_appendix_file(self, file_name: str, content: str) -> int:
		count = 0
		filename_without_ext = os.path.splitext(file_name)[0]
		
		# Parse xml
		soup = bs4.BeautifulSoup(content, "xml")
		title = self.extract_title(soup, file_name)
		if title in self.appendix_entries:
			appendix_title = self.appendix_entries[title]
			count += self.add_appendix_entry(appendix_title, soup)
		else:
			print(f"Appendix title not found for: {title}, file: {filename_without_ext}")
						
		if count == 0:
			print(f"No appendix entry was parsed for file {filename_without_ext}")
			
		return count