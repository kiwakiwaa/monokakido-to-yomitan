import json
from datetime import datetime

class AudioHandler:
	
	def __init__(self, dict_name: str, audio_path: str):
		self.audio_path = audio_path
		self.audio_index = {
			"meta": {
				"name": dict_name,
				"year": datetime.today().strftime("%Y"),
				"version": 1,
				"media_dir": "media"
			},
			"entries": [],
			"kanji_index": {},
			"kana_index": {}
		}
	
	
	def save_audio_entry(self, headword: str, reading: str, audio_filename: str):
		entry_index = len(self.audio_index["entries"])
		
		entry_data = {
			"kanji": headword or "",  # Empty string if no headword
			"kana": reading,
			"audio_file": audio_filename
		}
		# Add to entries array and get index
		self.audio_index["entries"].append(entry_data)
		
		# Update kanji index if headword exists
		if headword:
			if headword not in self.audio_index["kanji_index"]:
				self.audio_index["kanji_index"][headword] = []
			self.audio_index["kanji_index"][headword].append(entry_index)
			
		# Update reading index
		if reading not in self.audio_index["kana_index"]:
			self.audio_index["kana_index"][reading] = []
		self.audio_index["kana_index"][reading].append(entry_index)
		
		
	def export(self):
		with open(self.audio_path, "w", encoding="utf-8") as f:
			json.dump(self.audio_index, f, ensure_ascii=False, indent=2)