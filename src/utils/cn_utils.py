import regex as re
import dragonmapper.transcriptions as dt
from typing import List, Tuple

class CNUtils:
	
	@staticmethod
	def normalize_pinyin(text):
		text = re.sub(r'\d', '', text)
		text = re.sub(r'\s+', '', text)
		text = text.lower()
		text = re.sub(r'[^a-z0-9]', '', text)
		text = text.replace('v', 'u')
		return text
	
	
	@staticmethod
	def is_hanzi(text: str) -> bool:
		cjk_unified = r'\p{Han}'
		
		cjk_compat = r'\p{InCJK_Compatibility_Ideographs}'
		cjk_compat_supp = r'\p{InCJK_Compatibility_Ideographs_Supplement}'
		
		cjk_ext_a = r'\p{InCJK_Unified_Ideographs_Extension_A}'
		cjk_ext_b = r'\p{InCJK_Unified_Ideographs_Extension_B}'
		cjk_ext_c = r'\p{InCJK_Unified_Ideographs_Extension_C}'
		cjk_ext_d = r'\p{InCJK_Unified_Ideographs_Extension_D}'
		cjk_ext_e = r'\p{InCJK_Unified_Ideographs_Extension_E}'
		cjk_ext_f = r'\p{InCJK_Unified_Ideographs_Extension_F}'
		cjk_ext_g = r'\p{InCJK_Unified_Ideographs_Extension_G}'
		cjk_ext_h = r'\p{InCJK_Unified_Ideographs_Extension_H}'
		cjk_ext_i = r'\p{InCJK_Unified_Ideographs_Extension_I}'
		
		cjk_radicals = r'\p{InCJK_Radicals_Supplement}'
		kangxi_radicals = r'\p{InKangxi_Radicals}'
		ideographic_desc = r'\p{InIdeographic_Description_Characters}'
		
		pattern = '|'.join([
			cjk_unified, cjk_compat, cjk_compat_supp,
			cjk_ext_a, cjk_ext_b, cjk_ext_c, cjk_ext_d, 
			cjk_ext_e, cjk_ext_f, cjk_ext_g, cjk_ext_h, cjk_ext_i,
			cjk_radicals, kangxi_radicals, ideographic_desc
		])

		return bool(re.search(f'({pattern})', text))
	
	
	@staticmethod
	def map_pinyin_to_hanzi(entry_keys: List[str]) -> List[Tuple[str, str]]:
		hanzi_entries = [k for k in entry_keys if CNUtils.is_hanzi(k)]
		
		# Check if there are no Hanzi entries
		if not hanzi_entries:
			return []
		
		# Identify Pinyin entries
		numbered_pinyin = [k for k in entry_keys if dt.is_pinyin(k) and any(c.isdigit() for c in k)]
		unnumbered_pinyin = [k for k in entry_keys if dt.is_pinyin(k) and not any(c.isdigit() for c in k)]
		
		# Find unclassified entries (neither Hanzi nor recognized Pinyin)
		all_classified = set(hanzi_entries + numbered_pinyin + unnumbered_pinyin)
		unclassified = [k for k in entry_keys if k not in all_classified]
		
		# Generate mappings
		mappings = []
		
		# First handle numbered Pinyin (preferred)
		if numbered_pinyin:
			for hanzi_char in hanzi_entries:
				for pinyin in numbered_pinyin:
					mappings.append((hanzi_char, pinyin))
					
		# Normalize all numbered pinyin for comparison
		normalized_numbered = set(CNUtils.normalize_pinyin(p) for p in numbered_pinyin)
		
		# Check if unnumbered Pinyin is unique
		if unnumbered_pinyin:
			# Find unique unnumbered Pinyin
			unique_unnumbered = []
			for p in unnumbered_pinyin:
				norm_p = CNUtils.normalize_pinyin(p)
				if norm_p not in normalized_numbered:
					unique_unnumbered.append(p)
					print(f"Adding unique unnumbered Pinyin: {p}, entry_keys: {entry_keys}")
					
			# Add mappings for unique unnumbered Pinyin
			for hanzi_char in hanzi_entries:
				for pinyin in unique_unnumbered:
					print(f"Adding unique unnumbered Pinyin: {p}, entry_keys: {entry_keys}")
					mappings.append((hanzi_char, pinyin))
					
		if not mappings:
			return []
				
		return mappings
	
	
	@staticmethod
	def pinyin_to_zhuyin(pinyin):
		if not pinyin or not pinyin.strip():
			return ""
		
		# Handle abbreviations followed by pinyin (e.g., "IP dìzhǐ", "SIM kǎ")
		if ' ' in pinyin:
			parts = pinyin.split()
			result_parts = []
			
			for part in parts:
				# Keep abbreviations as-is
				if part.isupper() or (part.isalnum() and not part.islower()):
					result_parts.append(part)
				else:
					# Convert pinyin part to zhuyin
					try:
						# Fix pinyin with ü replacements
						fixed_part = part.replace('lv', 'lü').replace('nv', 'nü')
						zhuyin = dt.to_zhuyin(fixed_part)
						result_parts.append(zhuyin)
					except Exception:
						try:
							part = part.lower()
							zhuyin = dt.to_zhuyin(part)
							result_parts.append(zhuyin)
						except Exception:
							result_parts.append(part)
						
			return " ".join(result_parts)
		
		# Special cases for proper names and single terms
		elif any(c.isupper() for c in pinyin) and any(c.islower() for c in pinyin):
			# Keep the pinyin format as-is for proper names, don't try to split
			return pinyin
		
		# Regular pinyin conversion for standard pinyin terms
		try:
			# Fix ü representation
			fixed_pinyin = pinyin.replace('lv', 'lü').replace('nv', 'nü')
			# Convert standard pinyin
			zhuyin = dt.to_zhuyin(fixed_pinyin)
			return zhuyin
		except Exception as e:
			# If conversion fails, return original
			return pinyin
			