import bs4
import os

from typing import List, Dict, Tuple
from core.yomitan_dictionary import create_html_element
from strategies import ImageHandlingStrategy


class NanmedImageHandlingStrategy(ImageHandlingStrategy):
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = html_glossary.get("src", "").lstrip("/")
        if src_path:
            # Check if the path contains any directory components
            if "/" in src_path or "\\" in src_path:
                # Instead of warning, just use the basename
                data_dict["gaiji_img"] = ""
                src_path = os.path.basename(src_path)
            
            # Add 'images/' prefix to the path
            modified_path = f"images/{src_path}"
            
            image_element = {
                "tag": "img", 
                "path": modified_path, 
                "collapsible": False, 
                "collapsed": False,
                "background": False,
                "appearance": "auto",
                "imageRendering": "auto",
                "data": data_dict
            }
            html_elements.insert(0, image_element)
        
        return create_html_element("span", content=html_elements, data=data_dict)