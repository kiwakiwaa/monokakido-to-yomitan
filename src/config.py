from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Type


@dataclass
class DictionaryConfig:
    """Configuration for dictionary processing"""
    dict_name: str
    rev_name: str
    dict_type: str  # Type identifier like "Daijisen" or "OZK5"
    parser_class: type  # The parser class to use
    
    # Appendix config (optional)
    appendix_handler_class: Optional[type] = None
    has_appendix: bool = False
    
    
class PathManager:
    def __init__(self, base_dir: Optional[str] = None):
        """Initialize path manager with optional base directory override"""
        self.base_dir = Path(base_dir) if base_dir else Path(__file__).parent.parent
        
    def get_paths(self, config: DictionaryConfig):
        """Generate all required paths for a dictionary config"""
        dict_type = config.dict_type
        
        paths = {
            "base_dir": self.base_dir,
            "dict_path": self.base_dir / f"data/{dict_type}/pages",
            "index_path": self.base_dir / f"data/{dict_type}/index/index_d.tsv",
            "output_path": self.base_dir / "converted",
            "jmdict_path": self.base_dir / "data/JMdict_english",
            "term_bank_folder": self.base_dir / "converted" / config.dict_name,
            "assets_folder": self.base_dir / f"assets/{dict_type}",
            "index_json_path": self.base_dir / f"data/{dict_type}/index/index.json"
        }
        
        if config.has_appendix:
            paths["appendix_path"] = self.base_dir / f"data/{dict_type}/appendix"
        
        return paths