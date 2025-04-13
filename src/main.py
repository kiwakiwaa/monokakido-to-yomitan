#!/usr/bin/env python3
from typing import Optional, Dict, List
import argparse
import sys

from config import DictionaryConfig, PathManager
from utils import FileUtils
from parser.OZK5 import OZK5Parser
from parser.Daijisen import DaijisenParser
from parser.KNJE import KNJEParser
from parser.SKOGO import SKOGOParser
from parser.YDP import YDPParser
from parser.SHINJIGEN2 import ShinjigenParser
from parser.NANMED20 import NanmedParser
from parser.MK3 import MeikyoParser


def process_dictionary(config: DictionaryConfig, base_dir: Optional[str] = None, repackage_only: bool = False):
    """Process a dictionary based on its configuration
    
    Args:
        config: Dictionary configuration
        base_dir: Optional base directory for files
        repackage_only: If True, skip parsing and just repackage existing files
    """
    path_manager = PathManager(base_dir)
    paths = path_manager.get_paths(config)
    
    # Only parse if not in repackage-only mode
    if not repackage_only:
        print(f"Parsing dictionary: {config.dict_name}")
        # Create parser instance with required paths
        parser = config.parser_class(
            config.dict_name,
            paths["dict_path"],
            paths["index_path"],
            paths["jmdict_path"]
        )
        parser.parse()
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


def get_available_dictionaries() -> Dict[str, DictionaryConfig]:
    """Return a dictionary of available dictionary configurations"""
    return {
        "daijisen": DictionaryConfig(
            dict_name="大辞泉 第二版",
            rev_name="daijisen2",
            dict_type="Daijisen",
            parser_class=DaijisenParser
        ),
        "kogo": DictionaryConfig(
            dict_name="旺文社 全訳古語辞典",
            rev_name="oubunsha_kogo5",
            dict_type="OZK5",
            parser_class=OZK5Parser
        ),
        "knje": DictionaryConfig(
            dict_name="研究社 新和英大辞典 第5版",
            rev_name="knje5",
            dict_type="KNJE",
            parser_class=KNJEParser
        ),
        "skogo": DictionaryConfig(
            dict_name="三省堂 全訳読解古語辞典",
            rev_name="skogo5",
            dict_type="SKOGO",
            parser_class=SKOGOParser
        ),
        "ydp": DictionaryConfig(
            dict_name="現代心理学辞典",
            rev_name="ydp1",
            dict_type="YDP",
            parser_class=YDPParser
        ),
        "shinjigen": DictionaryConfig(
            dict_name="角川新字源 改訂新版",
            rev_name="shinjigen2",
            dict_type="SHINJIGEN2",
            parser_class=ShinjigenParser
        ),
        "nanmed": DictionaryConfig(
            dict_name="南山堂医学大辞典 第20版",
            rev_name="nanmed20",
            dict_type="NANMED20",
            parser_class=NanmedParser
        ),
        "meikyo": DictionaryConfig (
            dict_name="明鏡国語辞典 第三版",
            rev_name="meikyo3",
            dict_type="MK3",
            parser_class=MeikyoParser
        )
    }


def main():
    dictionary_configs = get_available_dictionaries()
    
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