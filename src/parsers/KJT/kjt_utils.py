import bs4
import regex as re

from utils import KanjiUtils

class KJTUtils: 
	
	@staticmethod
	def extract_all_oyaji(soup: bs4.BeautifulSoup):
		oyaji = []
		
		oyaji_elements = soup.find_all("OyajiHeadSubG")
		for oyaji_element in oyaji_elements:
			
			kanji_elements = oyaji_element.find_all("td", class_="親字")
			for kanji_element in kanji_elements:
				collected_text = []
				for child in kanji_element.contents:
					if isinstance(child, str):
						collected_text.append(child.strip())
					elif child.name:  # Other elements, preserve their text
						collected_text.append(child.get_text(strip=True))
					
				if collected_text:
					kanji = "".join(filter(None, collected_text)).strip()
					oyaji.append(KanjiUtils.clean_headword(kanji))
					
			gaiji_elments = oyaji_element.find_all("img", class_="外字")
			for gaiji_element in gaiji_elments:
				src_path = gaiji_element.get("src", "")
				alt = gaiji_element.get("alt", "")
				if not alt:
					print(f"\nNo alt for 外字: {src_path}\Element: {oyaji_element}")
				
				if alt not in oyaji:
					oyaji.append(alt)
					
		return oyaji
				
				
	@staticmethod
	def get_all_jukugo(soup: bs4.BeautifulSoup, sub_element: str):
		def clean_headword(headword: str):
			headword = re.sub('【', '', headword)
			headword = re.sub('】', '', headword)
			headword = re.sub('〗', '', headword)
			headword = re.sub('〖', '', headword)
			headword = re.sub('△', '', headword)
			headword = re.sub('［', '', headword)
			headword = re.sub('］', '', headword)
			return headword
		
		jukugo_data = []
		
		jukugo_elements = soup.find_all(sub_element)
		for jukugo_element in jukugo_elements:
			headword_element = jukugo_element.find("headword")
			reading_element = jukugo_element.find("yomi")
			headword = ""
			reading = ""
			has_missing_gaiji = False
			missing_in_parentheses = False
			
			collected_text = []
			current_parentheses_level = 0
			
			for child in headword_element.contents:
				if child.name == "JyouyouGaiM":
					continue
				elif isinstance(child, str):
					# Track parentheses nesting level
					for char in child:
						if char == '（':
							current_parentheses_level += 1
						elif char == '）':
							current_parentheses_level -= 1
					collected_text.append(child.strip())
				elif child.name == "img":
					gaiji_alt = child.get("alt", "")
					if gaiji_alt:
						collected_text.append(gaiji_alt.strip())
					else:
						# Check if missing gaiji is inside parentheses
						if current_parentheses_level > 0:
							missing_in_parentheses = True
						else:
							has_missing_gaiji = True
				elif child.name:
					collected_text.append(child.get_text(strip=True))
					
			# Skip entries with missing gaiji not in parentheses
			if has_missing_gaiji and not missing_in_parentheses:
				continue
			
			if collected_text:
				headword = "".join(filter(None, collected_text)).strip()
				
			if reading_element:
				reading = reading_element.get_text(strip=True)
				
			jukugo_data.append({
				'element': jukugo_element,
				'raw': {
					'headword': headword,
					'reading': reading
				},
				'processed': {
					'headwords': KJTUtils.process_jukugo_headword(clean_headword(headword)),
					'readings': KJTUtils.process_jukugo_reading(reading)
				}
			})
			
		return jukugo_data
		
				
	@staticmethod
	def process_jukugo_headword(headword):
		
		def process_single_term(term):
			if '（' not in term:
				return [term]
			
			results = []
			stack = [(term, False)]
			
			while stack:
				current, processed = stack.pop()
				
				if '（' not in current:
					results.append(current)
					continue
				
				# Find the first parentheses pair
				start = current.find('（')
				end = current.find('）', start)
				
				if start == -1 or end == -1:
					results.append(current)
					continue
				
				if start + 1 == end:
					# Just remove the empty parentheses and continue
					cleaned = current[:start] + current[end+1:]
					stack.append((cleaned, True))
					continue
				
				# Get the character before parentheses
				if start == 0:
					continue
				
				base_char = current[start-1]
				variants = current[start+1:end]
				
				# Create two versions:
				# 1. Original version
				original = current[:start-1] + base_char + current[end+1:]
				
				# 2. Variant version
				variant = current[:start-1] + variants + current[end+1:]
				
				stack.append((original, True))
				stack.append((variant, True))
				
			# Remove duplicates while preserving order
			seen = set()
			unique_results = []
			for r in results:
				if r not in seen:
					seen.add(r)
					unique_results.append(r)
					
			return unique_results
		
		if '・' in headword:
			terms = headword.split('・')
			results = []
			for term in terms:
				results.extend(process_single_term(term))
			return results
		
		return process_single_term(headword)
			
		
	
	@staticmethod
	def process_jukugo_reading(reading: str):
		modern_reading = re.sub(r'（[^）]*）', '', reading)
		modern_reading = modern_reading.replace(' ', '')
		return modern_reading.split('・')
		