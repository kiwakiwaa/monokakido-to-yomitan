from typing import List, Dict, Optional

from core import Parser
from config import DictionaryConfig

class KJTParser:
	
	def __init__(self, config: DictionaryConfig):
		super().__init__(config)
		
		
	def _process_file(self, filename: str, xml: str) -> int:
		count = 0
		
		return count