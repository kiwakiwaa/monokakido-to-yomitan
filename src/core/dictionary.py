import json
import os
import zipfile
import shutil
from tqdm import tqdm

class Dictionary:
    def __init__(self, dictionary_name):
        self.dictionary_name = dictionary_name
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def export(self, output_path=None):
        folder_name = self.dictionary_name
        
        if output_path:
            folder_name = os.path.join(output_path, folder_name)
        
        # Remove the existing folder if it already exists
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        
        os.makedirs(folder_name, exist_ok=True)

        # Save index.json
        index_json = {
            "title": self.dictionary_name,
            "format": 3,
            "revision": "1"
        }
        index_file = os.path.join(folder_name, "index.json")
        with open(index_file, 'w', encoding='utf-8') as out_file:
            json.dump(index_json, out_file, ensure_ascii=False)

        file_counter = 1
        entry_counter = 0
        dictionary = []
        entry_id = 0
        
        # Create a progress bar for processing entries
        total_entries = len(self.entries)
        bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit}"
        pbar = tqdm(total=total_entries, desc="辞書をエクスポート中", bar_format=bar_format)

        for entry in self.entries:
            entry_list = entry.to_list()
            entry_list[6] = entry_id
            dictionary.append(entry_list)
            entry_counter += 1
            entry_id += 1
            
            # Update the progress bar
            pbar.update(1)

            if entry_counter >= 10000:
                output_file = os.path.join(folder_name, f"term_bank_{file_counter}.json")
                with open(output_file, 'w', encoding='utf-8') as out_file:
                    json.dump(dictionary, out_file, ensure_ascii=False)
                dictionary = []
                file_counter += 1
                entry_counter = 0
                
                # Update description to show current file
                pbar.set_description(f"辞書をエクスポート中 - ファイル {file_counter-1} 完了")

        if dictionary:
            output_file = os.path.join(folder_name, f"term_bank_{file_counter}.json")
            with open(output_file, 'w', encoding='utf-8') as out_file:
                json.dump(dictionary, out_file, ensure_ascii=False)
                
        # Close the progress bar
        pbar.close()

    def zip(self):
        zip_file_name = f"{self.dictionary_name}.zip"
        
        if os.path.exists(zip_file_name):
            os.remove(zip_file_name)
        
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.dictionary_name):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, self.dictionary_name))