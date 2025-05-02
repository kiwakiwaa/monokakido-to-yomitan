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
    
    # Only parse if not in repackage-only mode
    if not repackage_only:
        print(f"Parsing dictionary: {config.dict_name}")
        
        # Create parser instance with required paths
        parser_class = config.get_parser_class()
        parser = parser_class(
            config=config,
            dict_path=paths["dict_path"],
            index_path=paths["index_path"],
            jmdict_path=paths.get("jmdict_path"),
            audio_path=paths.get("audio_path")
        )
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

# TODO move to config file
def get_available_dictionaries() -> Dict[str, DictionaryConfig]:
    """Return a dictionary of available dictionary configurations"""
    return {
        "daijisen": DictionaryConfig(
            dict_name="大辞泉 第二版",
            rev_name="daijisen2",
            dict_type="Daijisen",
            parser_module="parsers.DAIJISEN",
            parser_class_name="DaijisenParser",
            strategy_module="parsers.DAIJISEN.daijisen_strategies",
            link_strategy_class="DaijisenLinkHandlingStrategy",
            image_strategy_class="DaijisenImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/DAIJISEN/tag_map.json"),
        ),
        "kogo": DictionaryConfig(
            dict_name="旺文社 全訳古語辞典",
            rev_name="oubunsha_kogo5",
            dict_type="OZK5",
            parser_module="parsers.OZK5",
            parser_class_name="OZK5Parser",
            strategy_module="parsers.OZK5.ozk5_strategies",
            link_strategy_class="OZK5LinkHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/OZK5/tag_map.json"),
        ),
        "skogo": DictionaryConfig(
            dict_name="三省堂 全訳読解古語辞典",
            rev_name="skogo5",
            dict_type="SKOGO",
            parser_module="parsers.SKOGO",
            parser_class_name="SKOGOParser",
            strategy_module="parsers.SKOGO.skogo_strategies",
            link_strategy_class="SKOGOLinkHandlingStrategy",
            image_strategy_class="SKOGOImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/SKOGO/mapping/tag_map.json"),
        ),
        "ydp": DictionaryConfig(
            dict_name="現代心理学辞典",
            rev_name="ydp1",
            dict_type="YDP",
            parser_module="parsers.YDP",
            parser_class_name="YDPParser",
            strategy_module="parsers.YDP.ydp_strategies",
            image_strategy_class="YDPImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/YDP/tag_map.json"),
        ),
        "shinjigen": DictionaryConfig(
            dict_name="角川新字源 改訂新版",
            rev_name="shinjigen2",
            dict_type="SHINJIGEN2",
            parser_module="parsers.SHINJIGEN2",
            parser_class_name="ShinjigenParser",
            strategy_module="parsers.SHINJIGEN2.shinjigen2_strategies",
            image_strategy_class="ShinjigenImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/SHINJIGEN2/tag_map.json"),
        ),
        "nanmed": DictionaryConfig(
            dict_name="南山堂医学大辞典 第20版",
            rev_name="nanmed20",
            dict_type="NANMED20",
            parser_module="parsers.NANMED20",
            parser_class_name="NanmedParser",
            strategy_module="parsers.NANMED20.nanmed_strategies",
            image_strategy_class="NanmedImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/NANMED20/tag_map.json"),
        ),
        "meikyo": DictionaryConfig (
            dict_name="明鏡国語辞典 第三版",
            rev_name="meikyo3",
            dict_type="MK3",
            parser_module="parsers.MK3",
            parser_class_name="MeikyoParser",
            strategy_module="parsers.MK3.meikyo_strategies",
            link_strategy_class="MeikyoLinkHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/MK3/tag_map.json"),
        ),
        "ydl": DictionaryConfig (
            dict_name="有斐閣 法律用語辞典",
            rev_name="ydl",
            dict_type="YDL",
            parser_module="parsers.YDL",
            parser_class_name="YDLParser",
            strategy_module="parsers.OKO12.oko12_strategies",
            image_strategy_class="Oko12ImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/YDL/tag_map.json"),
        ),
        "tismkanji": DictionaryConfig (
            dict_name="TISMKANJI",
            rev_name="kanjirin",
            dict_type="TISMKANJI",
            parser_module="parsers.TISMKANJI",
            parser_class_name="TismKanjiParser",
        ),
        "oko12": DictionaryConfig (
            dict_name="旺文社国語辞典 第十二版",
            rev_name="oko12",
            dict_type="OKO12",
            parser_module="parsers.OKO12.oko12_parser",
            parser_class_name="Oko12Parser",
            strategy_module="parsers.OKO12.oko12_strategies",
            link_strategy_class="Oko12LinkHandlingStrategy",
            image_strategy_class="Oko12ImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/OKO12/tag_map.json"),
        ),
        "rgko12": DictionaryConfig (
            dict_name="例解学習国語 第十二版",
            rev_name="rgko12",
            dict_type="RGKO12",
            parser_module="parsers.RGKO12.rgko12_parser",
            parser_class_name="Rgko12Parser",
            strategy_module="parsers.RGKO12.rgko12_strategies",
            link_strategy_class="Rgko12LinkHandlingStrategy",
            image_strategy_class="Rgko12ImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/RGKO12/mapping/tag_map.json"),
            appendix_entries_path=str(Path(__file__).parent / "parsers/RGKO12/mapping/appendix_entries.json"),
            has_appendix=True
        ),
        "cj3": DictionaryConfig(
            dict_name="小学館 中日辞典 第3版",
            rev_name="cj3",
            dict_type="CJ3",
            parser_module="parsers.CJ3.cj3_parser",
            parser_class_name="CJ3Parser",
            strategy_module="parsers.CJ3.cj3_strategies",
            link_strategy_class="CJ3LinkHandlingStrategy",
            image_strategy_class="CJ3ImageHandlingStrategy",
            tag_map_path=str(Path(__file__).parent / "parsers/CJ3/mapping/tag_map.json"),
            appendix_entries_path=str(Path(__file__).parent / "parsers/CJ3/mapping/appendix_entries.json"),
            has_appendix=True,
            has_audio=True,
            use_jmdict=False
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