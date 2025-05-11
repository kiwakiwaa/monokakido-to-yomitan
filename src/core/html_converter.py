
from typing import List, Dict, Optional, Tuple
import bs4

from core.yomitan_dictionary import create_html_element
from strategies import LinkHandlingStrategy, ImageHandlingStrategy, DefaultLinkHandlingStrategy, DefaultImageHandlingStrategy

class HTMLToYomitanConverter:
	def __init__(self, 
		tag_mapping: Optional[Dict] = None, 
		ignored_elements: Optional[Dict] = None,
		expression_element: Optional[str] = None,
		link_handling_strategy: Optional[LinkHandlingStrategy] = None,
		image_handling_strategy: Optional[ImageHandlingStrategy] = None,
		parse_all_links: Optional[bool] = False):
		
		self.tag_mapping = tag_mapping or {}
		self.ignored_elements = ignored_elements or {}
		self.expression_element = expression_element or None
		self.link_handling_strategy = link_handling_strategy or DefaultLinkHandlingStrategy()
		self.image_handling_strategy = image_handling_strategy or DefaultImageHandlingStrategy()
		self.parse_all_links = parse_all_links
		
		self.__yomitan_supported_tags = {
			"br", "ruby", "rt", "rp", "table", "thead", "tbody", "tfoot",
			"tr", "td", "th", "span", "div", "ol", "ul", "li", "details", "summary"
		}
		
		
	def get_class_list_and_data(self, html_glossary: bs4.element.Tag) -> Tuple[List[str], Dict[str, str]]:
		"""Extract class list and data attributes from an HTML element"""
		class_list = html_glossary.get("class", [])
		if isinstance(class_list, str):
			class_list = class_list.split(" ")
   
		if html_glossary.name and not class_list and html_glossary.name not in self.__yomitan_supported_tags:
			class_list.append(html_glossary.name)
			
		data_dict = {}
		data_dict[html_glossary.name] = ""
		
		for cls in class_list:
			data_dict[cls.replace("-", "_")] = ""
			
		for attribute, value in html_glossary.attrs.items():
			if(isinstance(value, str)):
				data_dict[attribute.replace("-", "_")] = value
				
		return class_list, data_dict
		
		
	def get_target_tag(self, tag_name: str, class_list: Optional[List[str]] = None,
						parent: Optional[bs4.element.Tag] = None, recursion_depth: int = 0) -> str:
		"""
		Get the appropriate HTML tag based on tag name and CSS classes
		"""
		if not class_list:
			class_list = []
			
		# Look for nested rules
		if parent:
			parent_classes, _ = self.get_class_list_and_data(parent)
			
			# Try parent.class + tag 
			for parent_class in parent_classes:
				nested_selector = f"{parent.name}.{parent_class} {tag_name}"
				if nested_selector in self.tag_mapping:
					return self.tag_mapping[nested_selector]
				
			# Try parent + tag
			nested_selector = f"{parent.name} {tag_name}"
			if nested_selector in self.tag_mapping:
				return self.tag_mapping[nested_selector]
			
			# Recurse up the ancestor chain if no match
			if recursion_depth < 5 and parent.parent:
				target_tag = self.get_target_tag(tag_name, class_list=class_list, parent=parent.parent, recursion_depth=recursion_depth + 1)
				if target_tag != "span":
					return target_tag
				
		# Try tag.class (no parent involvement)
		for css_class in class_list:
			class_specific_key = f"{tag_name}.{css_class}"
			if class_specific_key in self.tag_mapping:
				return self.tag_mapping[class_specific_key]
			
		# Fall back to regular tag mapping or default
		return self.tag_mapping.get(tag_name, "span")
	
	
	def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
							data_dict: Dict, class_list: List[str]) -> Dict:
		return self.link_handling_strategy.handle_link_element(html_glossary, html_elements, data_dict, class_list)
	
	
	def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, data_dict: Dict, class_list: List[str]) -> str:
		return self.image_handling_strategy.handle_image_element(html_glossary, html_elements, data_dict, class_list)
	
	
	def _process_html_children(self, html_glossary: bs4.element.Tag, data_dict: Dict[str, str], class_list: List[str],
								ignore_expressions: bool = False) -> List:
		"""Process child elements of an HTML element"""
		html_elements = []
		if html_glossary.contents:
			for content in html_glossary.contents:
				if isinstance(content, bs4.Comment):
					continue
				if isinstance(content, bs4.NavigableString) or isinstance(content, str):
					html_elements.append(create_html_element("span", content))
				else:
					converted_element = self.convert_element_to_yomitan(content, ignore_expressions=ignore_expressions)
					if converted_element is not None:  # Avoid inserting None
						html_elements.append(converted_element)
					
		# Special case for img tags without contents
		elif html_glossary.name.lower() == "img":
			img_element = self.handle_image_element(html_glossary, html_elements, data_dict, class_list)
			if img_element:
				return img_element
			
		return html_elements  
	
	
	def convert_element_to_yomitan(self, html_glossary: Optional[bs4.element.Tag] = None,
									ignore_expressions: bool = False) -> Optional[Dict]:
		"""Recursively converts HTML elements into Yomitan JSON format"""
		if not html_glossary:
			return None
		
		tag_name = html_glossary.name.lower()
		if tag_name in self.ignored_elements:
			return None
		
		if ignore_expressions and self.expression_element and tag_name == self.expression_element:
			return None
		
		class_list, data_dict = self.get_class_list_and_data(html_glossary)
			
		# Recursively process children elements
		html_elements = self._process_html_children(html_glossary, data_dict, class_list, ignore_expressions=ignore_expressions)
		if not html_elements:
			return None
		
		if not isinstance(html_elements, List):
			return html_elements
		
		# Check if all elements in the list are empty strings or whitespace-only strings
		if all(isinstance(elem, dict) and 
			elem.get('content') and 
			(not elem['content'] or 
				(isinstance(elem['content'], str) and elem['content'].isspace())) 
			for elem in html_elements):
			return None
	
		# add elements that yomitan supports
		if tag_name in self.__yomitan_supported_tags:
			return create_html_element(html_glossary.name, content=html_elements, data=data_dict)
	
		# map any custom tags to html
		target_tag = self.get_target_tag(html_glossary.name, class_list, html_glossary.parent)
		
		# Handle image elements where the content isnt empty
		if tag_name == "img" and html_glossary.contents:
			element = self.handle_image_element(html_glossary, html_elements, data_dict, class_list)
			if element:
				return element
			
		# Hanle link elements
		if self.parse_all_links:
			if tag_name == "a" or html_glossary.get("href", ""):
				element = self.handle_link_element(html_glossary, html_elements, data_dict, class_list)
				if element:
					return element
		else:
			if tag_name == "a" or html_glossary.get("href", ""):
				element = self.handle_link_element(html_glossary, html_elements, data_dict, class_list)
				if element:
					return element
			
		return create_html_element(target_tag, content=html_elements, data=data_dict)