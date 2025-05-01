from typing import Dict, List, Optional, Iterator
from abc import abstractmethod
import bs4
import os
from pathlib import Path

from parser.base import Parser
from yomitandic import Dictionary, DicEntry, create_html_element
from parser.base.strategies import LinkHandlingStrategy, ImageHandlingStrategy

class AppendixHandler(Parser):
	def __init__(self, dictionary: Dictionary, directory_path: str, 
				link_handling_strategy: LinkHandlingStrategy = None, 
				image_handling_strategy: ImageHandlingStrategy = None):
		super().__init__(
			link_handling_strategy=link_handling_strategy,
			image_handling_strategy=image_handling_strategy
		)
		self.dictionary = dictionary
		self.directory_path = directory_path
		
		self.initialize_html_converter()
		
		
	def extract_title(self, soup: bs4.BeautifulSoup, file_name: str) -> str:
		dict_item_element = soup.find("dic-item")
		if dict_item_element and dict_item_element.get("id"):
			return dict_item_element.get("id")
		
		for selector in [".title", ".appendix-title"]:
			element = soup.select_one(selector)
			if element:
				return element.get_text(strip=True)
		
		return f"付録：{file_name}"
			
			
	def _find_appendix_files(self, directory_path: str) -> Iterator[str]:
		if not os.path.exists(directory_path):
			return
		
		for root, _, files in os.walk(directory_path):
			for file in files:
				if file.lower().endswith(('.html', '.xml', '.xhtml')):
					yield os.path.join(root, file)
			
		
	def parse_appendix_directory(self) -> int:
		count = 0
		for file_path in self._find_appendix_files(self.directory_path):
			try:
				with open(file_path, 'r', encoding='utf-8') as f:
					content = f.read()
					
				file_name = Path(file_path).stem
				count += self.parse_appendix_file(file_name, content)
			except Exception as e:
				print(f"Error processing appendix file {file_path}: {e}")
				
		return count
		
		
	def add_appendix_entry(self, title: str, soup: bs4.BeautifulSoup) -> DicEntry:
		if not title:
			return 0
			
		appendix_entry = DicEntry(title, "")
		
		for tag in soup.find_all(recursive=False):
			yomitan_element = self.convert_element_to_yomitan(tag)
			
			if yomitan_element:
				wrapper = create_html_element("span", content=[yomitan_element], data={"付録": ""})
				appendix_entry.add_element(wrapper)
				self.dictionary.add_entry(appendix_entry)
			else:
				print(f"Failed parsing entry contents: {entry_key}, reading: {reading}")
				return 0
			
		return 1
		
	
	@abstractmethod
	def parse_appendix_file(self, file_name: str, content: str) -> int:
		pass