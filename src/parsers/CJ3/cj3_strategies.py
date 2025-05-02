import os
import regex as re
import bs4

from typing import Dict, List, Tuple, Optional, Set, Callable, Any

from utils import CNUtils
from core.yomitan_dictionary import create_html_element

from strategies import LinkHandlingStrategy, ImageHandlingStrategy

class CJ3LinkHandlingStrategy(LinkHandlingStrategy):
	def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
							data_dict: Dict, class_list: List[str]) -> Dict:
		href = ""
		if html_glossary.text:
			href = html_glossary.text.strip()
		
		if href and not href.isdigit():
			href = re.sub(r'\[', '', href)
			href = re.sub(r'\]', '', href)
			
			href = re.sub(r'〖', '', href)
			href = re.sub(r'〗', '', href)
			return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
	
		return create_html_element("span", content=html_elements, data=data_dict)
	
	
class CJ3ImageHandlingStrategy(ImageHandlingStrategy):
	def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
							data_dict: Dict, class_list: List[str]) -> Dict:
		src_path = html_glossary.get("src", "").lstrip("/")
		
		if src_path and src_path != "HMDicAudio.png":
			if not src_path.startswith("gaiji") and src_path.endswith(".png"):
				src_path = src_path[:-4] + '.avif'
			
			img_element = {
				"tag": "img", 
				"path": src_path, 
				"collapsible": False, 
				"collapsed": False,
				"background": False,
				"appearance": "auto",
				"imageRendering": "auto",
				"data": data_dict
			}
			html_elements.insert(0, img_element)
			
		return create_html_element("span", content=html_elements, data=data_dict)