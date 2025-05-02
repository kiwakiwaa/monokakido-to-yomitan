import os
from typing import List
from collections import defaultdict
from tqdm import tqdm

class IndexReader:
    def __init__(self, index_file_path: str) -> None:
        """Initialize with the path to the index_d.tsv file"""
        self.index_file_path = index_file_path
        self.dict_data = {}  # Dictionary mapping keys to filenames
        self.file_to_keys = defaultdict(list)  # Reverse mapping: filename -> keys
        self.load_index()
        
    
    def load_index(self) -> None:
        """Load the index file and build both mappings"""
        if not os.path.exists(self.index_file_path):
            raise FileNotFoundError(f"Index file not found: {self.index_file_path}")
        
        # Count total lines for progress tracking
        with open(self.index_file_path, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
        
        bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit}"

        with open(self.index_file_path, 'r', encoding='utf-8') as f, \
            tqdm(total=total_lines, desc="索引読込中", unit="行", bar_format=bar_format, ascii="░▒█") as pbar:
            
            for line in f:
                parts = line.strip().split('\t')
                if len(parts) < 2:
                    print(f"Found a malformed line: {parts}")
                    continue
                
                key = parts[0]
                filenames = parts[1:]
                
                self.dict_data[key] = filenames
                
                # Build reverse mapping
                for filename in filenames:
                    self.file_to_keys[filename].append(key)
                    
                pbar.update(1)
                    
    
    def get_keys_for_file(self, filename: str) -> List[str]:
        """Get all dictionary keys associated with a given filename"""
        return self.file_to_keys.get(filename, [])
    
    
    def process_all_files(self) -> None:
        """Process all files and show their associated keys"""
        count = 0
        import random
        shuffled_items = list(self.file_to_keys.items())
        random.shuffle(shuffled_items)
        
        for filename, keys in tqdm(shuffled_items, desc="進歩", unit="事項"):
            if count > 20:
                break
            
            print(f"Filename: {filename}")
            print(f"Associated keys: {', '.join(keys)}")
            print("-" * 50)
            count += 1