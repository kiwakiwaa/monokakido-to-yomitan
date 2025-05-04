import os
import time
import json
import glob
import zipfile
import regex as re

from typing import List, Dict, Any
from tqdm import tqdm
from datetime import datetime

bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit}"

class FileUtils:
    
    @staticmethod
    def read_xml_files(directory_path: str) -> Dict[str, str]:
        """
        Reads all XML files in the specified directory and stores them in a dictionary.
        """
        result = {}
        
        if not os.path.isdir(directory_path):
            raise ValueError(f"ディレクトリ '{directory_path}' は存在しません")
        
        # Find all XML files in the directory
        xml_files = glob.glob(os.path.join(directory_path, "*.xml"))
        
        for xml_file in tqdm(xml_files, desc="辞書ファイル読込中", unit="ファイル", bar_format=bar_format, ascii="░▒█"):
            try:
                filename = os.path.basename(xml_file)
                
                with open(xml_file, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                result[filename] = content
                
            except Exception as e:
                print(f"エラー: ファイル '{xml_file}' を読み込めませんでした: {str(e)}")
        
        return result
    
    
    @staticmethod
    def gather_files(term_bank_folder: str, assets_folder: str, index_json_path: str, output_path: str) -> List[str]:
        file_paths = []

        # Collect dictionary files
        for file in os.listdir(term_bank_folder):
            if file.startswith("term_bank_") and file.endswith(".json"):
                file_paths.append(os.path.join(term_bank_folder, file))

        # Collect all files inside assets
        for root, _, files in os.walk(assets_folder):
            for f in files:
                file_paths.append(os.path.join(root, f))
                
        # Collect index file
        if os.path.exists(index_json_path) and os.path.isfile(index_json_path):
            file_paths.append(index_json_path)
            
        return file_paths
        
    
    @staticmethod
    def zip_dictionary(file_paths: List[str], name: str, base_path: str, output_path: str, flatten_dict_folder: bool = True) -> str:
        if not file_paths:
            raise ValueError("No files provided")

        date_str = datetime.now().strftime("%Y-%m-%d")
        zip_name = name + f"[{date_str}].zip"
        zip_path = os.path.join(output_path, zip_name)
        
        total_files = len(file_paths)

        with tqdm(total=total_files, desc="辞書圧縮処理", bar_format="「{desc}: {bar:30}」{percentage:3.0f}%{postfix}", 
                ascii="░▒█") as p_bar:
            
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as zipf:
                for i, file in enumerate(file_paths):
                    path_parts = os.path.normpath(file).split(os.sep)
                    
                    # Determine the relative path in the zip
                    if 'gaiji' in path_parts:
                        rel_path = os.path.join('gaiji', os.path.basename(file))
                    elif 'graphics' in path_parts:
                        rel_path = os.path.join('graphics', os.path.basename(file))
                    elif 'images' in path_parts:
                        rel_path = os.path.join('images', os.path.basename(file))
                    elif 'images2' in path_parts:
                        rel_path = os.path.join('images2', os.path.basename(file))
                    elif 'images_column' in path_parts:
                        rel_path = os.path.join('images_column', os.path.basename(file))  
                    elif 'images_hitsujun' in path_parts:
                        rel_path = os.path.join('images_hitsujun', os.path.basename(file))  
                    elif 'logos' in path_parts:
                        rel_path = os.path.join('logos', os.path.basename(file))
                    elif 'icons' in path_parts:
                        rel_path = os.path.join('icons', os.path.basename(file))
                    elif 'formulas' in path_parts:
                        rel_path = os.path.join('formulas', os.path.basename(file))
                    elif 'tables' in path_parts:
                        rel_path = os.path.join('tables', os.path.basename(file))
                    elif 'svg' in path_parts:
                        rel_path = os.path.join('svg', os.path.basename(file))
                    elif str(file).endswith('.json') or str(file).endswith('.css'):
                        rel_path = os.path.basename(file)
                    elif '.DS_Store' in path_parts:
                        continue
                    else: 
                        rel_path = os.path.join(base_path, file)
                        
                    # Remove dictionary folder prefix if flatten_dict_folder=True
                    if flatten_dict_folder and rel_path.startswith(f"{name}/"):
                        rel_path = os.path.basename(rel_path)  # Only keep filename

                    # Write file to zip
                    zipf.write(file, rel_path)
                    
                    p_bar.update(1)

        print(f"完了しました: {zip_path}")
        return zip_path
    
    
    @staticmethod
    def extract_entry_keys(entry: str) -> List[str]:
        parts = entry.split('|')
        
        # Ensure there are at least two parts (to skip the number)
        if len(parts) < 2:
            return []
        
        # Return everything except the first element (the number)
        return parts[1:]
    

    # Reads JMdict for part of speech tags
    @staticmethod
    def load_term_banks(folder_path: str) -> Dict[str, List[str]]:
        term_dict = {}
        
        # Find all term_bank_*.json files in the folder
        json_files = sorted(glob.glob(os.path.join(folder_path, "term_bank_*.json")))
        count = 0
        
        jmdict_bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit}{postfix}"
        with tqdm(total=len(json_files), desc="JMDICT読込中", unit="ファイル", bar_format=jmdict_bar_format, ascii="░▒█") as pbar:
            for file in json_files:
                try:
                    with open(file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            for entry in data:
                                if isinstance(entry, list) and len(entry) > 3:
                                    term = entry[0]  # First element is the term
                                    pos_tags = entry[2:4]  #  third and fourth element are POS tags
                                    
                                    pos_tag_1 = pos_tags[0]
                                    pos_tag_1 = re.sub(r'^\d+\s+', '', pos_tag_1)
                                    
                                    pos_tag_2 = pos_tags[1]
                                    
                                    if not pos_tags:
                                        continue
                                    
                                    if term in term_dict:
                                        existing_tag = term_dict[term]
                                        existing_tag_1 = existing_tag[0]
                                        existing_tag_2 = existing_tag[1]
                                        
                                        if existing_tag_2.strip() != pos_tag_2.strip():
                                            if "vk" in existing_tag_2 or "vk" in pos_tag_2: # dont replace vk tags (来る)
                                                pos_tag_2 = "vk"
                                            else:
                                                pos_tag_2 = max(pos_tag_2, existing_tag_2, key=len) # replace if the new tag is longer
                                                
                                        if existing_tag_1.strip() != pos_tag_1.strip():
                                            if pos_tag_1 == "forms": # skip the "forms" tag
                                                pos_tag_1 = existing_tag_1
                                        
                                        term_dict[term] = [pos_tag_1, pos_tag_2]
                                    else:
                                        count += 1
                                        term_dict[term] = [pos_tag_1, pos_tag_2]
                                                
                        else:
                            print(f"警告: {file} にリストが含まれていません。")
                except Exception as e:
                    print(f"エラー: {file}の読み込み中: {e}")
                    
                pbar.update(1)
                
            pbar.set_postfix_str(f" | JMdictから {count} の品詞タグが見つかりました")
        return term_dict
    
    
    @staticmethod
    def update_index_revision(revision_name: str, index_path: str) -> None:
        if not os.path.exists(index_path):
            print("Warning: index.json not found, skipping revision update.")
            return
        
        with open(index_path, "r", encoding="utf-8") as f:
            index_data = json.load(f)

        # Update revision field
        today_str = datetime.today().strftime("%Y-%m-%d")
        index_data["revision"] = f"{revision_name};{today_str}"

        # Write updated data back
        with open(index_path, "w", encoding="utf-8") as f:
            json.dump(index_data, f, ensure_ascii=False, indent=4)
            

    @staticmethod
    def load_mdx_json(dir_path: str) -> Dict[str, Any]:
        """
        Load the first JSON file found in the specified directory.
        """
        try:
            # Check if the directory exists
            if not os.path.isdir(dir_path):
                print(f"Error: {dir_path} is not a valid directory")
                return {}
                
            # Find all JSON files in the directory
            json_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.json')]
            
            if not json_files:
                print(f"No JSON files found in {dir_path}")
                return {}
                
            # Get the first JSON file
            json_file_path = os.path.join(dir_path, json_files[0])
            
            # Load and return the JSON data
            with open(json_file_path, 'r', encoding='utf-8') as f:
                mdx_data = json.load(f)
                print(f"Successfully loaded JSON file: {json_files[0]}")
                return mdx_data
                
        except Exception as e:
            print(f"Error loading MDX JSON file: {e}")
            return {}
        
        
    @staticmethod
    def load_json(file_path: str):
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            return data
        except FileNotFoundError:
            print(f"Error: File '{file_path}' not found.")
            raise
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON format in '{file_path}': {e}")
            raise
        except Exception as e:
            print(f"Unexpected error while loading '{file_path}': {e}")
            raise
    