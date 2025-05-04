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
	
	import dragonmapper.transcriptions as dt
	
	@staticmethod
	def pinyin_to_zhuyin(pinyin: str) -> str:
		if not pinyin or not pinyin.strip():
			return ""
		
		special_cases = {
			"hsk": "hsk", # abbrev.
			"ktv": "ktv",
			"ńg": "ㄣ", # nasal sounds
			"ǹg": "ㄣ",
			"ňg": "ㄣ",
			"ň": "ㄣ",
			"ń": "ㄣ",
			"ǹ": "ㄣ",
			"lǒngàn": "ㄌㄨㄥˇ", # 拢岸
			"fiào": "ㄠˋ", # 覅
			"cèi": "ㄘㄜ", # 𤭢 
			"ruá": "ㄖㄨㄚ", # 挼
			"m̄": "ㄇ", # 姆
			"wènān": "ㄨㄣˋㄢ", # 问安
			"ế": "ㄞ", # 欸
			"ề èi": "ㄞ",# 欸
			"ê̌ ěi": "ㄞ",
			"ḿshá": "ㄇˊㄕㄚˊ", # 呒啥
			"dìngàn": "ㄉㄧㄥˋㄢ",
			"m̄mā": "ㄇㄇㄚ", # 姆妈
			"ḿ": "ㄇˊ", # 呣
			"m̀": "ㄇˊ", # 呣
			"ê̄": "ㄞ", # 欸,
			"wènàn": "ㄨㄣˋ ㄢˋ", # 问案
			"hng": "ㄏㄥ", # 哼
			"hm": "˙ㄏㄇ", # 噷,
		}
		
		# Check for direct special case match
		if pinyin.lower() in special_cases:
			return special_cases[pinyin.lower()]
		
		# Handle abbreviations followed by pinyin (e.g., "IP dìzhǐ", "SIM kǎ")
		if ' ' in pinyin:
			parts = pinyin.split()
			result_parts = []
			
			for part in parts:
				# Keep abbreviations as-is
				if part.isupper() or (part.isalnum() and not part.islower()):
					result_parts.append(part)
				elif part == "F-yāo":
					result_parts.append("F－15")
				else:
					part = part.lower()
					
					try:
						zhuyin = dt.to_zhuyin(part)
						result_parts.append(zhuyin)
					except Exception:
						if part.lower() in special_cases:
							result_parts.append(special_cases[part.lower()])
						else:
							return pinyin #丝绸之路：长安—天山廊道的路网 & 皖南古村落—西递，宏村 & 北京及沈阳的明清皇家宫殿
							
			return "".join(result_parts)

		
		# Regular pinyin conversion for standard pinyin terms
		try:
			fixed_pinyin = pinyin.lower()
			zhuyin = dt.to_zhuyin(pinyin.lower())
			return zhuyin
		except Exception as e:
			print(f"\nFailed to convert to zhuyin: {fixed_pinyin}")
			return pinyin
			