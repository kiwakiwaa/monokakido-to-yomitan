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
	def extract_busyu(soup: bs4.BeautifulSoup):
		busyu = []
		readings = []
		
		busyu_head_element = soup.find("BusyuHeadG")
				
		headwords = busyu_head_element.find_all("headword", class_="部首見出")
		for headword in headwords:
			busyu_text = headword.get_text(strip=True).strip()
			if busyu_text:
				busyu.append(busyu_text)
		
		
		variants = busyu_head_element.find_all("headword", class_="部首異体")
		for itaiji in variants:
			itaiji_text = itaiji.get_text(strip=True).strip()
			if itaiji_text:
				busyu.append(itaiji_text)
			
		for reading in busyu_head_element.find_all("headword", class_="部首名"):
			readings.append(reading.get_text(strip=True).strip())
	
		return busyu, readings
			
			
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
			is_kanbun_element = jukugo_element.find("kanbun")
			
			collected_text = []
			current_parentheses_level = 0
			
			for child in headword_element.contents:
				if child.name and child.name == "kkaeri":
					continue # remove 返点
				elif child.name and child.name == "JyouyouGaiM": 
					continue # remove triangles 
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
				
			
			if not is_kanbun_element:	
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
				
				variants = current[start+1:end]
				num_variants = len(variants)
				
				# Get the same number of base characters
				base_chars = current[start-num_variants:start]
				
				# Create two versions:
				# 1. Original version (keep base chars)
				original = current[:start-num_variants] + base_chars + current[end+1:]
				
				# 2. Variant version (use variant chars)
				variant = current[:start-num_variants] + variants + current[end+1:]
				
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
	
	
	@staticmethod
	def get_item_id(full_id: str) -> str:
		parts = full_id.split('-')
		if len(parts) != 2:
			print(f"Invalid ID format: {full_id}")
			return None
		
		# Get the last part which contains the item number
		item_part = parts[1]
		
		# Always take the last 3 characters (works for both hex and decimal)
		last_three = item_part[-3:]

		try:
			# Convert just the last 3 hex digits to decimal
			decimal_value = int(last_three, 16)
			
			# Convert to 3-digit string
			item_id = f"{decimal_value:03d}"
		except ValueError:
			print(f"Failed to convert hex ID: {last_three}")
			return None
			
		return item_id
		