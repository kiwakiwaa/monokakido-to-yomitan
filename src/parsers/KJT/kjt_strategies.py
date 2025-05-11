import bs4
import os
import regex as re
from typing import Dict, List, Optional, Tuple

from utils import FileUtils, KanjiUtils
from core.yomitan_dictionary import create_html_element
from strategies import LinkHandlingStrategy, ImageHandlingStrategy

class KJTLinkHandlingStrategy(LinkHandlingStrategy):
    
    def __init__(self):
        self.appendix_entries = FileUtils.load_json(os.path.join(os.path.dirname(__file__), "mapping/appendix_entries.json"))
    
    def clean_link_text(self, text: str) -> str:
        text = re.sub(r'[〒〓〈〉《》「」『』【】〔〕〖〗〘〙〚〛〝〞〟()\[\]{}]', '', text)
        return text
    
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        href_val = html_glossary.get("href", "").replace('index/', 'appendix/')
        if html_glossary.name == "a":
            href = ""
            collected_text = []
            for child in html_glossary.contents:
                if child.name == "mlg":
                    continue
                if isinstance(child, str):  # Plain text
                    collected_text.append(child.strip())
                elif child.name:  # Other elements, preserve their text
                    collected_text.append(child.get_text(strip=True))   
                
            if collected_text:
                href = self.clean_link_text("".join(filter(None, collected_text)).strip())
                
            if href and not href.isdigit():  # Check that href is not empty and not only digits
                return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
            
        elif href_val.split('#')[0] in self.appendix_entries:
            title = self.appendix_entries[href_val.split('#')[0]]
            link_element = create_html_element("a", content=html_elements, href="?query="+title+"&wildcards=off")
            return create_html_element("span", content=[link_element], data=data_dict)
        
        return create_html_element("span", content=html_elements, data=data_dict)
    
    
class KJTImageHandlingStrategy(ImageHandlingStrategy):
    
    def __init__(self):
        self.image_file_map = FileUtils.load_json(os.path.join(os.path.dirname(__file__), "mapping/image_file_map.json"))
    
    
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, 
                             data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = html_glossary.get("src", "").lstrip("/")
        
        if src_path:
            if src_path.startswith("img") and src_path.endswith(".png"):
                src_path = src_path[:-4] + '.avif'
            
            normalized_filename = self.get_normalized_filename(src_path)
            if "筆順" in class_list:
                summary_element = create_html_element("summary", content="筆順")
                img_element = {
                    "tag": "img", 
                    "path": normalized_filename, 
                    "collapsible": False, 
                    "collapsed": False,
                    "background": False,
                    "appearance": "auto",
                    "imageRendering": "auto",
                    "data": data_dict
                }
                return create_html_element("details", content=[summary_element, img_element])
            else:
                image_element = {
                    "tag": "img", 
                    "path": normalized_filename, 
                    "collapsible": False, 
                    "collapsed": False,
                    "background": False,
                    "appearance": "auto",
                    "imageRendering": "auto",
                    "data": data_dict
                }
                html_elements.insert(0, image_element)
            
        return create_html_element("span", content=html_elements, data=data_dict)
    
    
    def get_normalized_filename(self, src_path: str) -> str:
        if not src_path:
            return ""
        
        if src_path.startswith('../'):
            src_path = src_path.replace('../', '', 1)
            
        if src_path.startswith("img"):
            original_filename = os.path.basename(src_path)
            
            # Try direct lookup first
            if original_filename in self.image_file_map:
                return src_path.replace(original_filename, self.image_file_map[original_filename])
            
            # Try normalized versions
            import unicodedata
            for norm_form in ['NFC', 'NFD', 'NFKC', 'NFKD']:
                normalized = unicodedata.normalize(norm_form, original_filename)
                if normalized in self.image_file_map:
                    return src_path.replace(original_filename, self.image_file_map[normalized])
                
            # If exact match fails, try loose matching by removing the file extension
            base_name = os.path.splitext(original_filename)[0]
            for key in self.image_file_map:
                key_base = os.path.splitext(key)[0]
                if base_name == key_base:
                    return src_path.replace(original_filename, self.image_file_map[key])
                
            return src_path
        else:
            return src_path
        
        return ""