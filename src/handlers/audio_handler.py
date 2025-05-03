import json
from datetime import datetime

class AudioHandler:
	
	def __init__(self, dict_name: str, audio_path: str):
		self.dict_name = dict_name
		self.audio_path = audio_path
		self.audio_index = self._init_index()
		
	def _init_index(self):
		audio_index = {
			"meta": {
				"name": self.dict_name,
				"year": datetime.today().strftime("%Y"),
				"version": 1,
				"media_dir": "media"
			},
			"entries": [],
			"headword_index": {},
			"reading_index": {}
		}
		return audio_index
	
	
	def save_audio_entry(self, headword: str, reading: str, audio_filename: str):
		entry_index = len(self.audio_index["entries"])
		
		entry_data = {
			"headword": headword or "",  # Empty string if no headword
			"reading": reading,
			"audio_file": audio_filename
		}
		# Add to entries array and get index
		self.audio_index["entries"].append(entry_data)
		
		# Update kanji index if headword exists
		if headword:
			if headword not in self.audio_index["headword_index"]:
				self.audio_index["headword_index"][headword] = []
			self.audio_index["headword_index"][headword].append(entry_index)
			
		# Update reading index
		if reading not in self.audio_index["reading_index"]:
			self.audio_index["reading_index"][reading] = []
		self.audio_index["reading_index"][reading].append(entry_index)
		
		
	def export(self):
		with open(self.audio_path, "w", encoding="utf-8") as f:
			json.dump(self.audio_index, f, ensure_ascii=False, indent=2)
			
			
class CJ3AudioHandler(AudioHandler):
	
	def __init__(self, dict_name: str, audio_path: str):
		super().__init__(dict_name, audio_path)
	
	
	def _init_index(self):
		audio_index = {
			"meta": {
				"name": self.dict_name,
				"year": datetime.today().strftime("%Y"),
				"version": 1,
				"media_dir": "media"
			},
			"headwords": {},
			"files": {}
		}
		return audio_index
	
	
	def save_audio_entry(self, headword: str, pinyin: str, zhuyin: str, audio_filename: str):
		# Add file entry with readings
		self.audio_index["files"][audio_filename] = {
			"pinyin": pinyin or "",
			"zhuyin": zhuyin or ""
		}
		
		# Update headwords index
		if headword:
			if headword not in self.audio_index["headwords"]:
				self.audio_index["headwords"][headword] = []
			self.audio_index["headwords"][headword].append(audio_filename)
	