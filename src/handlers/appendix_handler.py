from typing import Dict, List, Optional, Iterator
from abc import abstractmethod
import bs4
import os
from pathlib import Path

from core.yomitan_dictionary import Dictionary, DicEntry, create_html_element

class AppendixHandler:
	def __init__(self, 
				dictionary, 
				directory_path: str,
				tag_mapping: Dict = None,
				appendix_entries: Dict = None,
				link_strategy=None,
				image_strategy=None,
				ignored_elements: Optional[Dict] = None):
				
		from core.html_converter import HTMLToYomitanConverter

		self.dictionary = dictionary
		self.directory_path = directory_path
		self.tag_mapping = tag_mapping or {}
		self.appendix_entries = appendix_entries or {}
		self.link_handling_strategy = link_strategy
		self.image_handling_strategy = image_strategy
		self.ignored_elements = ignored_elements
		
		self.html_converter = HTMLToYomitanConverter(
			tag_mapping=self.tag_mapping,
			ignored_elements=self.ignored_elements,
			image_handling_strategy=self.image_handling_strategy
		)
			
			
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
					
				count += self.parse_appendix_file(file_path, content)
			except Exception as e:
				print(f"Error processing appendix file {file_path}: {e}")
				
		return count
		
		
	def add_appendix_entry(self, title: str, soup: bs4.BeautifulSoup) -> DicEntry:
		if not title:
			return 0
			
		appendix_entry = DicEntry(title, "")
		
		for tag in soup.find_all(recursive=False):
			yomitan_element = self.html_converter.convert_element_to_yomitan(tag)
			
			if yomitan_element:
				wrapper = create_html_element("span", content=[yomitan_element], data={"付録": ""})
				appendix_entry.add_element(wrapper)
				self.dictionary.add_entry(appendix_entry)
			else:
				print(f"Failed parsing entry contents: {entry_key}, reading: {reading}")
				return 0
			
		return 1
		
	
	def parse_appendix_file(self, file_path: str, content: str) -> int:
		count = 0
		
		filename = os.path.basename(file_path)
		appendix_key = os.path.join("appendix", filename)
		
		# Parse xml
		soup = bs4.BeautifulSoup(content, "xml")
		if appendix_key in self.appendix_entries:
			appendix_title = self.appendix_entries[appendix_key]
			count += self.add_appendix_entry(appendix_title, soup)
		else:
			print(f"Appendix title not found for: {appendix_key}")
			
		if count == 0:
			print(f"No appendix entry was parsed for {appendix_key}")
			
		return count