#!/usr/bin/env python3
from typing import Optional, Dict, List
import argparse
import sys
from pathlib import Path
from config import DictionaryConfig, PathManager
from utils import FileUtils


def process_dictionary(config: DictionaryConfig, base_dir: Optional[str] = None, repackage_only: bool = False):
    """Process a dictionary based on its configuration
    
    Args:
        config: Dictionary configuration
        base_dir: Optional base directory for files
        repackage_only: If True, skip parsing and just repackage existing files
    """
    path_manager = PathManager(base_dir)
    paths = path_manager.get_paths(config)
    
    config.set_paths(paths)
    config.validate_required_paths()
    
    # Only parse if not in repackage-only mode
    if not repackage_only:
        print(f"Parsing dictionary: {config.dict_name}")
        
        # Create parser instance with required paths
        parser_class = config.get_parser_class()
        parser = parser_class(config)
        
        # TODO add variant character entry handling
        
        parser.parse()
        
        if config.has_appendix and "appendix_path" in paths:
            appendix_path = paths["appendix_path"]
            if appendix_path.exists():
                print(f"{config.dict_name}の付録を処理します")
                appendix_handler = config.create_appendix_handler(
                    parser.dictionary, 
                    str(appendix_path)
                )
                appendix_count = appendix_handler.parse_appendix_directory()
                print(f"{appendix_count}の付録項目を追加しました")
        
        parser.export(paths["output_path"])
        FileUtils.update_index_revision(config.rev_name, paths["index_json_path"])
    else:
        print(f"Repackaging only for dictionary: {config.dict_name}")
    
    # Always gather files and create zip
    file_paths = FileUtils.gather_files(
        paths["term_bank_folder"],
        paths["assets_folder"],
        paths["index_json_path"],
        paths["output_path"]
    )
    
    print(f"Creating dictionary package...")
    FileUtils.zip_dictionary(
        file_paths,
        config.dict_name,
        paths["base_dir"],
        paths["output_path"],
        flatten_dict_folder=True
    )
    print(f"Dictionary package created at: {paths['output_path']}")


def main():
    config_path = Path(__file__).parent / "config/dictionaries.yaml"
    dictionary_configs = DictionaryConfig.load_configs(config_path)
    
    parser = argparse.ArgumentParser(description='Dictionary processing tool')
    parser.add_argument('--dict', '-d', choices=list(dictionary_configs.keys()), 
                        help='Dictionary to process', required=False)
    parser.add_argument('--all', '-a', action='store_true', 
                        help='Process all dictionaries')
    parser.add_argument('--repackage', '-r', action='store_true', 
                        help='Repackage only (skip parsing)')
    parser.add_argument('--base-dir', '-b', type=str, default=None,
                        help='Base directory for files')
    parser.add_argument('--list', '-l', action='store_true',
                        help='List available dictionaries and exit')
    
    args = parser.parse_args()
    
    if args.list:
        print("Available dictionaries:")
        for key, config in dictionary_configs.items():
            print(f"  {key}: {config.dict_name}")
        return 0
    
    if not args.dict and not args.all:
        parser.error("Either --dict or --all must be specified")
    
    if args.all:
        # Process all dictionaries
        for dict_key, config in dictionary_configs.items():
            try:
                print(f"\n{'='*60}")
                print(f"Processing {dict_key}: {config.dict_name}")
                print(f"{'='*60}")
                process_dictionary(config, args.base_dir, args.repackage)
            except Exception as e:
                print(f"Error processing {dict_key}: {e}")
                import traceback
                traceback.print_exc()
                print(f"Continuing with next dictionary...")
    else:
        # Process a single dictionary
        dict_key = args.dict
        config = dictionary_configs[dict_key]
        try:
            process_dictionary(config, args.base_dir, args.repackage)
        except Exception as e:
            print(f"Error processing {dict_key}: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    print("Dictionary processing completed")
    return 0


if __name__ == "__main__":
    sys.exit(main())