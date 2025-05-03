import os
import json
import regex as re
from typing import Dict, List, Any, Set, Optional

class VariantHandler:
	
	def __init__(self, directory: str):
		self.directory = directory
		self.all_terms = set()
		self.term_banks = self.load_all_term_banks(self.directory)
		if self.term_banks:
			self.add_all_terms(self.term_banks)
			
	def get_next_term_bank_number(self) -> int:
		"""Find the next available term bank number with proper numeric sorting"""
		pattern = re.compile(r'term_bank_(\d+)\.json')
		existing_numbers = []
		
		for filename in os.listdir(self.directory):
			match = pattern.match(filename)
			if match:
				try:
					existing_numbers.append(int(match.group(1)))
				except ValueError:
					continue
				
		if not existing_numbers:
			return 1
		
		# Sort numerically (not lexicographically)
		existing_numbers.sort()
		return existing_numbers[-1] + 1
	
		
	def load_all_term_banks(self, directory: str) -> Dict[str, List[Any]]:
		# Load all term_bank_*.json files from the specified directory
		term_banks = {}
		pattern = re.compile(r'term_bank_\d+\.json')
		
		for filename in os.listdir(directory):
			if pattern.match(filename):
				file_path = os.path.join(directory, filename)
				with open(file_path, 'r', encoding='utf-8') as f:
					try:
						term_banks[filename] = json.load(f)
						print(f"Loaded {filename} with {len(term_banks[filename])} entries")
					except json.JSONDecodeError:
						print(f"Error: Could not parse {filename} as JSON")
						
		return term_banks
	
	
	def add_all_terms(self, term_banks: Dict[str, List[Any]]) -> Set[str]:
		# Extract all dictionary terms from the term banks
		for bank_name, entries in term_banks.items():
			for entry in entries:
				if entry and isinstance(entry, list) and len(entry) > 0 and isinstance(entry[0], str):
					self.all_terms.add(entry[0])
					
					
class HanziVariantHandler(VariantHandler):
	
	def __init__(self, directory: str):
		super().__init__(directory)
		self.variant_maps = self.load_variant_maps()
		self.new_entries = []
		
	def load_variant_maps(self) -> Dict[str, Dict[str, str]]:
		"""Load all variant mapping files"""
		base_dir = os.path.dirname(__file__)
		variant_maps = {
			'STCharacters': self.load_json_file(os.path.join(base_dir, 'data/STCharacters.json')),
			'STPhrases': self.load_json_file(os.path.join(base_dir, 'data/STPhrases.json')),
			'twvariants': self.load_json_file(os.path.join(base_dir, 'data/twvariants.json')),
			'twphrases': self.load_json_file(os.path.join(base_dir, 'data/twphrases.json')),
			'hkvariants': self.load_json_file(os.path.join(base_dir, 'data/hkvariants.json'))
		}
		return variant_maps
	
	def load_json_file(self, filepath: str) -> Optional[Dict[str, str]]:
		"""Helper to load a JSON file"""
		try:
			with open(filepath, 'r', encoding='utf-8') as f:
				return json.load(f)
		except (FileNotFoundError, json.JSONDecodeError):
			print(f"Warning: Could not load {filepath}")
			return {}
		
	def find_variants(self, term: str) -> List[str]:
		"""Find all variants for a given term"""
		variants = set()
		
		# 1. First check for phrase-level variants (both STPhrases and twphrases)
		for map_name in ['STPhrases', 'twphrases']:
			if term in self.variant_maps[map_name]:
				variants.update(self.variant_maps[map_name][term].split('|'))
				
		# 2. Handle character-level variants differently for STCharacters vs others
		if len(term) == 1:
			# Single character - check all variant maps
			for map_name in ['STCharacters', 'twvariants', 'hkvariants']:
				if term in self.variant_maps[map_name]:
					variants.update(self.variant_maps[map_name][term].split('|'))
		else:
			# Multi-character term
			# First check STCharacters (Simplified-Traditional)
			traditional_version = []
			needs_traditional = False
			
			# Build traditional version character by character
			for char in term:
				if char in self.variant_maps['STCharacters']:
					# Take the first traditional variant (before |)
					trad_char = self.variant_maps['STCharacters'][char].split('|')[0]
					traditional_version.append(trad_char)
					needs_traditional = True
				else:
					traditional_version.append(char)
					
			# Add the full traditional version if any characters were converted
			if needs_traditional:
				variants.add(''.join(traditional_version))
				
			# Then check other variant types (twvariants, hkvariants) for full combinations
			char_combinations = ['']
			for char in term:
				new_combinations = []
				char_variants = {char}
				
				# Only check these maps for character variants
				for map_name in ['twvariants', 'hkvariants']:
					if char in self.variant_maps[map_name]:
						char_variants.update(self.variant_maps[map_name][char].split('|'))
						
				for combo in char_combinations:
					for variant in char_variants:
						new_combinations.append(combo + variant)
						
				char_combinations = new_combinations
				
			# Add these combinations (excluding original term and traditional version we already added)
			variants.update(c for c in char_combinations 
							if c != term and c != ''.join(traditional_version))
			
		return list(variants)
	
	def find_original_entry(self, term: str) -> Optional[List[Any]]:
		"""Find the original dictionary entry for a term"""
		for bank_name, entries in self.term_banks.items():
			for entry in entries:
				if entry and isinstance(entry, list) and len(entry) > 0:
					if entry[0] == term:
						return entry
		return None
	
	def process_all_terms(self):
		"""Process all terms to find and add variants"""
		processed_terms = set()
		
		for bank_name, entries in self.term_banks.items():
			for entry in entries:
				if not entry or not isinstance(entry, list) or len(entry) == 0:
					continue
				
				term = entry[0]
				if term in processed_terms:
					continue
				
				processed_terms.add(term)
				variants = self.find_variants(term)
				
				for variant in variants:
					if variant not in self.all_terms and variant != term:
						# Create a new entry with the variant as headword
						new_entry = entry.copy()
						new_entry[0] = variant
						self.new_entries.append(new_entry)
						self.all_terms.add(variant)
						
		print(f"Found {len(self.new_entries)} new variants to add")
		
	def save_new_entries(self):
		"""Save the new entries to term banks with proper sequential numbering"""
		if not self.new_entries:
			print("No new entries to save")
			return
		
		# Get the starting number
		starting_num = self.get_next_term_bank_number()
		
		# Split into chunks of max 10000 entries
		chunks = [self.new_entries[i:i + 10000] 
				for i in range(0, len(self.new_entries), 10000)]
		
		for i, chunk in enumerate(chunks):
			bank_num = starting_num + i
			filename = f"term_bank_{bank_num}.json"
			filepath = os.path.join(self.directory, filename)
			
			with open(filepath, 'w', encoding='utf-8') as f:
				json.dump(chunk, f, ensure_ascii=False, indent=2)
				
			print(f"Saved {len(chunk)} entries to {filename}")
			
	def run(self):
		"""Run the complete variant processing pipeline"""
		self.process_all_terms()
		self.save_new_entries()
		
		
# data/STCharacters.json: Simplified Chinese to Traditional Chinese
# data/STPhrases.json: Simplified Chinese phrases to Traditional
# data/twvariants.json: Taiwan variants
# data/twphrases: Taiwan Phrase variants
# data/hkvariants.json: Hong kong variants