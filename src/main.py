from typing import Optional

from config import DictionaryConfig, PathManager
from utils import FileUtils
from parser.OZK5 import OZK5Parser
from parser.Daijisen import DaijisenParser
from parser.KNJE import KNJEParser
from parser.SKOGO import SKOGOParser
from parser.YDP import YDPParser
from parser.SHINJIGEN2 import ShinjigenParser
        

def process_dictionary(config: DictionaryConfig, base_dir: Optional[str] = None):
    """Process a dictionary based on its configuration"""
    path_manager = PathManager(base_dir)
    paths = path_manager.get_paths(config)
    
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
    file_paths = FileUtils.gather_files(
        paths["term_bank_folder"],
        paths["assets_folder"],
        paths["index_json_path"],
        paths["output_path"]
    )
    
    FileUtils.zip_dictionary(
        file_paths,
        config.dict_name,
        paths["base_dir"],
        paths["output_path"],
        flatten_dict_folder=True
    )


def main():
    dictionary_configs = {
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
        )
    }
    
    # TODO maybe add caching for JMdict data
    
    config_to_process = "shinjigen"
    process_dictionary(dictionary_configs[config_to_process])
    

if __name__ == "__main__":
    main()