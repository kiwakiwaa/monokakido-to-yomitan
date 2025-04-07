import json
import os

"""
Used for manual matching with readings provided by the user
when an entry key with kanji hasn't been matched by a corresponding kana reading.
"""
class ManualMatchHandler:
    def __init__(self, mappings_file="manual_mappings.json"):
        self.mappings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), mappings_file)
        self.mappings = self._load_mappings()
        self.ignored_entries = self._load_ignored_entries()
    
    def _load_mappings(self):
        """Load existing manual mappings from file"""
        if os.path.exists(self.mappings_file):
            try:
                with open(self.mappings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('mappings', {})
            except json.JSONDecodeError:
                print(f"Error reading {self.mappings_file}, starting with empty mappings")
                return {}
        return {}
    
    def _load_ignored_entries(self):
        """Load entries that should be ignored"""
        if os.path.exists(self.mappings_file):
            try:
                with open(self.mappings_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get('ignored', {})
            except json.JSONDecodeError:
                return {}
        return {}
    
    def _save_data(self):
        """Save all data to file"""
        data = {
            'mappings': self.mappings,
            'ignored': self.ignored_entries
        }
        with open(self.mappings_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def has_mapping(self, key, file_id=None):
        """Check if there's a manual mapping for this entry"""
        # Check if entry should be ignored
        if self._is_ignored(key, file_id):
            return True
            
        # Check file-specific mapping first
        if file_id and file_id in self.mappings and key in self.mappings[file_id]:
            return True
        # Check global mappings
        return key in self.mappings.get('global', {})
    
    def get_mapping(self, key, file_id=None):
        """Get the manual mapping for an entry"""
        # Check if entry should be ignored
        if self._is_ignored(key, file_id):
            return None
            
        # Try file-specific mapping first
        if file_id and file_id in self.mappings and key in self.mappings[file_id]:
            return self.mappings[file_id][key]
        # Fall back to global mapping
        return self.mappings.get('global', {}).get(key)
    
    def add_mapping(self, unmatched_key, matched_value, file_id=None, is_global=False):
        """Add a new manual mapping"""
        # Remove from ignored if it exists
        self._remove_from_ignored(unmatched_key, file_id, is_global)
        
        if is_global:
            if 'global' not in self.mappings:
                self.mappings['global'] = {}
            self.mappings['global'][unmatched_key] = matched_value
        else:
            if file_id not in self.mappings:
                self.mappings[file_id] = {}
            self.mappings[file_id][unmatched_key] = matched_value
        
        self._save_data()
    
    def remove_mapping(self, key, file_id=None, is_global=False):
        """Remove a mapping"""
        if is_global and 'global' in self.mappings and key in self.mappings['global']:
            del self.mappings['global'][key]
        elif file_id in self.mappings and key in self.mappings[file_id]:
            del self.mappings[file_id][key]
            
        self._save_data()
    
    def ignore_entry(self, key, file_id=None, is_global=False):
        """Mark an entry to be ignored in future runs"""
        if is_global:
            if 'global' not in self.ignored_entries:
                self.ignored_entries['global'] = []
            if key not in self.ignored_entries['global']:
                self.ignored_entries['global'].append(key)
        else:
            if file_id not in self.ignored_entries:
                self.ignored_entries[file_id] = []
            if key not in self.ignored_entries[file_id]:
                self.ignored_entries[file_id].append(key)
        
        self._save_data()
    
    def _is_ignored(self, key, file_id=None):
        """Check if an entry should be ignored"""
        # Check file-specific ignored entries
        if file_id and file_id in self.ignored_entries and key in self.ignored_entries[file_id]:
            return True
        # Check global ignored entries
        return key in self.ignored_entries.get('global', [])
    
    def _remove_from_ignored(self, key, file_id=None, is_global=False):
        """Remove an entry from the ignored list if it exists"""
        if is_global and 'global' in self.ignored_entries and key in self.ignored_entries['global']:
            self.ignored_entries['global'].remove(key)
        elif file_id in self.ignored_entries and key in self.ignored_entries[file_id]:
            self.ignored_entries[file_id].remove(key)

def process_unmatched_entries(parser, filename, entry_keys, matched_key_pairs, manual_handler):
    """Process unmatched entries with user input"""
    filename_without_ext = os.path.splitext(os.path.basename(filename))[0]
    
    # Identify unmatched entries
    unmatched_kanji = []
    unmatched_kana = []
    
    for kanji_part, kana_part in matched_key_pairs:
        if kanji_part and not kana_part:
            unmatched_kanji.append(kanji_part)
        elif kana_part and not kanji_part:
            unmatched_kana.append(kana_part)
    
    # Nothing unmatched, return normally processed pairs
    if not unmatched_kanji:
        return matched_key_pairs
    
    updated_pairs = [pair for pair in matched_key_pairs if pair[0] and pair[1]]
    
    #print(f"\n===== Processing unmatched entries in file {filename_without_ext} =====")
    
    # Process unmatched kanji entries
    for kanji in unmatched_kanji:
        # Check if we already have a manual mapping
        if manual_handler.has_mapping(kanji, filename_without_ext):
            kana_match = manual_handler.get_mapping(kanji, filename_without_ext)
            if kana_match is None:
                #print(f"Skipping ignored entry: {kanji}")
                continue
            else:
                #print(f"Using saved mapping: {kanji} → {kana_match}")
                updated_pairs.append((kanji, kana_match))
                continue
            
        if len(matched_key_pairs) == 1:
            return matched_key_pairs
        
        print(f"\nUnmatched kanji: {kanji}")
        print(f"Available kana entries: {entry_keys}")
        print(f"Currently unmatched kana: {unmatched_kana}")
        
        print("\nOptions:")
        print("1. Enter a matching kana from the list")
        print("2. Enter a custom kana (not in the list)")
        print("3. Ignore this entry (won't be asked again)")
        print("4. Skip for now (will ask again next time)")
        
        choice = input("Choose an option (1-4):\n")
        
        if choice == '1':
            # Match with existing kana entry
            user_input = input("Enter matching kana entry from the list:\n")
            
            if user_input in entry_keys:
                global_mapping = input("Apply this mapping globally? (y/n):\n").lower() == 'y'
                manual_handler.add_mapping(kanji, user_input, 
                                          file_id=None if global_mapping else filename_without_ext,
                                          is_global=global_mapping)
                updated_pairs.append((kanji, user_input))
                
                # Remove from unmatched if it was there
                if user_input in unmatched_kana:
                    unmatched_kana.remove(user_input)
            else:
                print(f"'{user_input}' is not in the entry list. Skipping for now.")
                updated_pairs.append((kanji, None))
                
        elif choice == '2':
            # Enter custom kana
            custom_kana = input("Enter custom kana reading:\n")
            if custom_kana:
                global_mapping = input("Apply this mapping globally? (y/n):\n").lower() == 'y'
                manual_handler.add_mapping(kanji, custom_kana, 
                                          file_id=None if global_mapping else filename_without_ext,
                                          is_global=global_mapping)
                updated_pairs.append((kanji, custom_kana))
            else:
                updated_pairs.append((kanji, None))
                
        elif choice == '3':
            # Ignore this entry
            global_ignore = input("Ignore globally? (y/n):\n").lower() == 'y'
            manual_handler.ignore_entry(kanji, 
                                       file_id=None if global_ignore else filename_without_ext,
                                       is_global=global_ignore)
            # Don't add to updated pairs - it's ignored
            
        else:  # choice == '4' or invalid input
            # Skip for now
            updated_pairs.append((kanji, None))
    
    # Process unmatched kana entries (similar structure with appropriate modifications)
    for kana in unmatched_kana:
        if manual_handler.has_mapping(kana, filename_without_ext):
            kanji_match = manual_handler.get_mapping(kana, filename_without_ext)
            if kanji_match is None:
                #print(f"Skipping ignored entry: {kana}")
                continue
            else:
                #print(f"Using saved mapping: {kana} → {kanji_match}")
                updated_pairs.append((kanji_match, kana))
                continue
            
        updated_pairs.append((None, kana))

    
    return updated_pairs

# Add a function to manage existing mappings
def manage_mappings(manual_handler):
    """Interface for managing existing mappings"""
    print("\n===== Manage Existing Mappings =====")
    print("1. View all mappings")
    print("2. Remove a mapping")
    print("3. Remove an ignored entry")
    print("4. Exit to main")
    
    choice = input("Choose an option (1-4): ")
    
    if choice == '1':
        # View all mappings
        print("\n--- Global Mappings ---")
        if 'global' in manual_handler.mappings:
            for key, value in manual_handler.mappings['global'].items():
                print(f"{key} → {value}")
        else:
            print("No global mappings")
            
        print("\n--- File-specific Mappings ---")
        for file_id, mappings in manual_handler.mappings.items():
            if file_id != 'global':
                print(f"\nFile: {file_id}")
                for key, value in mappings.items():
                    print(f"{key} → {value}")
        
        print("\n--- Ignored Entries ---")
        if 'global' in manual_handler.ignored_entries:
            print("\nGlobal ignored:")
            for key in manual_handler.ignored_entries['global']:
                print(f"- {key}")
                
        for file_id, ignored in manual_handler.ignored_entries.items():
            if file_id != 'global':
                print(f"\nFile {file_id} ignored:")
                for key in ignored:
                    print(f"- {key}")
        
        manage_mappings(manual_handler)
        
    elif choice == '2':
        # Remove a mapping
        print("\n1. Remove global mapping")
        print("2. Remove file-specific mapping")
        subchoice = input("Choose an option (1-2): ")
        
        if subchoice == '1':
            if 'global' not in manual_handler.mappings or not manual_handler.mappings['global']:
                print("No global mappings to remove")
            else:
                print("\nGlobal mappings:")
                for i, (key, value) in enumerate(manual_handler.mappings['global'].items(), 1):
                    print(f"{i}. {key} → {value}")
                
                try:
                    index = int(input("\nEnter number to remove (0 to cancel): "))
                    if index > 0:
                        key_to_remove = list(manual_handler.mappings['global'].keys())[index-1]
                        manual_handler.remove_mapping(key_to_remove, is_global=True)
                        print(f"Removed mapping for {key_to_remove}")
                except (ValueError, IndexError):
                    print("Invalid selection")
        
        elif subchoice == '2':
            file_ids = [fid for fid in manual_handler.mappings.keys() if fid != 'global']
            if not file_ids:
                print("No file-specific mappings to remove")
            else:
                print("\nFiles with mappings:")
                for i, file_id in enumerate(file_ids, 1):
                    print(f"{i}. {file_id}")
                
                try:
                    index = int(input("\nEnter file number (0 to cancel): "))
                    if index > 0:
                        selected_file = file_ids[index-1]
                        
                        print(f"\nMappings for {selected_file}:")
                        for i, (key, value) in enumerate(manual_handler.mappings[selected_file].items(), 1):
                            print(f"{i}. {key} → {value}")
                        
                        try:
                            map_index = int(input("\nEnter mapping number to remove (0 to cancel): "))
                            if map_index > 0:
                                key_to_remove = list(manual_handler.mappings[selected_file].keys())[map_index-1]
                                manual_handler.remove_mapping(key_to_remove, file_id=selected_file)
                                print(f"Removed mapping for {key_to_remove}")
                        except (ValueError, IndexError):
                            print("Invalid selection")
                except (ValueError, IndexError):
                    print("Invalid selection")
        
        manage_mappings(manual_handler)
        
    elif choice == '3':
        # Remove an ignored entry
        print("\n1. Remove global ignored entry")
        print("2. Remove file-specific ignored entry")
        subchoice = input("Choose an option (1-2): ")
        
        if subchoice == '1':
            if 'global' not in manual_handler.ignored_entries or not manual_handler.ignored_entries['global']:
                print("No global ignored entries")
            else:
                print("\nGlobal ignored entries:")
                for i, key in enumerate(manual_handler.ignored_entries['global'], 1):
                    print(f"{i}. {key}")
                
                try:
                    index = int(input("\nEnter number to remove (0 to cancel): "))
                    if index > 0:
                        key_to_remove = manual_handler.ignored_entries['global'][index-1]
                        manual_handler.ignored_entries['global'].remove(key_to_remove)
                        manual_handler._save_data()
                        print(f"Removed ignored entry: {key_to_remove}")
                except (ValueError, IndexError):
                    print("Invalid selection")
        
        elif subchoice == '2':
            file_ids = [fid for fid in manual_handler.ignored_entries.keys() if fid != 'global']
            if not file_ids:
                print("No file-specific ignored entries")
            else:
                print("\nFiles with ignored entries:")
                for i, file_id in enumerate(file_ids, 1):
                    print(f"{i}. {file_id}")
                
                try:
                    index = int(input("\nEnter file number (0 to cancel): "))
                    if index > 0:
                        selected_file = file_ids[index-1]
                        
                        print(f"\nIgnored entries for {selected_file}:")
                        for i, key in enumerate(manual_handler.ignored_entries[selected_file], 1):
                            print(f"{i}. {key}")
                        
                        try:
                            entry_index = int(input("\nEnter entry number to remove (0 to cancel): "))
                            if entry_index > 0:
                                key_to_remove = manual_handler.ignored_entries[selected_file][entry_index-1]
                                manual_handler.ignored_entries[selected_file].remove(key_to_remove)
                                manual_handler._save_data()
                                print(f"Removed ignored entry: {key_to_remove}")
                        except (ValueError, IndexError):
                            print("Invalid selection")
                except (ValueError, IndexError):
                    print("Invalid selection")
        
        manage_mappings(manual_handler)
        
    elif choice == '4':
        # Exit to main
        return
    
    else:
        print("Invalid option")
        manage_mappings(manual_handler)