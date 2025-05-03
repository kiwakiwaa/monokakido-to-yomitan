import os
import bs4
from typing import List
from utils import CNUtils

class CJ3Utils:
	
	@staticmethod
	def extract_pinyin(soup: bs4.BeautifulSoup) -> str:
		pinyin_reading = ""
		pinyin_element = soup.find("headword", class_="ピンイン")
		
		if not pinyin_element:
			return ""
		
		for content in pinyin_element.contents:
			if isinstance(content, bs4.NavigableString):
				pinyin_reading += str(content).strip()
			
			
		return pinyin_reading
	
	
	@staticmethod
	def extract_unicode_from_gaiji(soup: bs4.BeautifulSoup) -> List[str]:
		"""
		Extracts Unicode characters from gaiji entries in the soup.
		"""
		unicode_chars = []
		headword_elements = soup.find_all("headword")
		for headword_element in headword_elements:
			gaiji_images = headword_element.find_all("img", class_="外字") 
			
			for img in gaiji_images:
				if not img:
					return ""
				
				src = img.get("src", "")
				if src and src.startswith("gaiji/"):
					# Extract the hex code from the filename (e.g., "gaiji/933D.png" -> "933D")
					try: 
						hex_code = os.path.splitext(os.path.basename(src))[0]
						unicode_chars.append(chr(int(hex_code, 16)))
					except Exception as e:
						return ""
					
		return unicode_chars
	
	
	@staticmethod
	def extract_from_field(soup: bs4.BeautifulSoup, element: str, class_: str) -> List[str]:
		text = ""
		text_element = soup.find(element, class_=class_)
		
		if not text_element:
			return ""
		
		for content in text_element.contents:
			if isinstance(content, bs4.NavigableString):
				text += str(content).strip()
			elif content.name == "cn":
				text += str(content.text).strip()
			
		text_content = text.split('・')
				
		return text_content
	
	
	@staticmethod
	def extract_audio_links_from_headword(soup: bs4.BeautifulSoup) -> List[str]:
		audio_links = []
		
		headword_elements = soup.find_all('headword')
		
		for headword in headword_elements:
			audio_elements = headword.find_all('audio')
			
			for audio in audio_elements:
				links = audio.find_all('a')
				
				for link in links:
					href = link.get('href')
					if href:
						audio_links.append(href)
						
		return audio_links
	
	
	@staticmethod
	def filter_pinyin_readings(keys: List[str]) -> List[str]:
		
		pass