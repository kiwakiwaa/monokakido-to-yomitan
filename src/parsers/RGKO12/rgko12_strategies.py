import bs4
import os
from typing import Dict, List, Optional, Tuple

from utils import KanjiUtils, FileUtils
from core.yomitan_dictionary import create_html_element

from strategies import LinkHandlingStrategy, ImageHandlingStrategy
from parsers.RGKO12.image_file_map import IMAGE_FILE_MAP

class Rgko12LinkHandlingStrategy(LinkHandlingStrategy):
    
    def __init__(self):
        self.appendix_entries = FileUtils.load_dictionary_mapping(
            os.path.join(os.path.dirname(__file__), "mapping", "appendix_entries.json")
        )
    
    def extract_ruby_text(self, html_glossary: bs4.element.Tag):
        for ruby_tag in html_glossary.find_all("ruby"):
            ruby_tag.unwrap()
            
        for rt_tag in html_glossary.find_all("rt"):
            rt_tag.decompose()
            
        cleaned_word = "".join(html_glossary.text).strip()
        cleaned_word = KanjiUtils.clean_headword(cleaned_word)
        
        return cleaned_word
        
    
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        href_text = ""
        href = html_glossary.get("href", "")
        if href.split('#')[0] in self.appendix_entries:
            title = self.appendix_entries[href.split('#')[0]]
            return create_html_element("a", content=html_elements, href="?query="+title+"&wildcards=off")
        
        elif html_glossary.find("ruby"):
            href_word = self.extract_ruby_text(html_glossary)
            if href_word:
                return create_html_element("a", content=html_elements, href="?query="+href_word+"&wildcards=off")
            
        else:
            if html_glossary.text:
                href_text = html_glossary.text.strip()
                
                if href_text and not href_text.isdigit():  # Check that href is not empty and not only digits
                    return create_html_element("a", content=html_elements, href="?query="+href_text+"&wildcards=off")
                
        return create_html_element("span", content=html_elements, data=data_dict)
    
    
class Rgko12ImageHandlingStrategy(ImageHandlingStrategy):
    
    def __init__(self):
        self.image_file_map = IMAGE_FILE_MAP
        self.missing_images = {
            "名・形動とたる.svg",
            "形動とたる.svg"
        }
        
        self.gaiji_replacements = FileUtils.load_dictionary_mapping(
            os.path.join(os.path.dirname(__file__), "mapping", "gaiji_replacements.json")
        )
        
        
    def set_class_names(self, class_: str, data: Dict) -> Dict:
        class_list = class_.split(' ')
        for class_ in class_list:
            data[class_] = ""
        return data
    
    
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:
        src_path = html_glossary.get("src", "").lstrip("/")
        
        if src_path:
            basename = os.path.basename(src_path)
            
            if basename in self.gaiji_replacements:
                text = self.gaiji_replacements[basename]["text"]
                class_name = self.gaiji_replacements[basename]["class"]
                data_dict = self.set_class_names(class_name, data_dict)
                return create_html_element("span", content=text, data=data_dict)
            else:
                hashed_filename = self.get_normalized_filename(src_path)
                
                if hashed_filename.lower().endswith('.png'):
                    hashed_filename = hashed_filename[:-4] + '.avif'
                
                if os.path.basename(hashed_filename) not in self.missing_images:
                    if "hitsujun" in src_path.lower():
                        summary_element = create_html_element("summary", content="筆順")
                        img_element = {
                            "tag": "img", 
                            "path": hashed_filename, 
                            "collapsible": False, 
                            "collapsed": False,
                            "background": False,
                            "appearance": "auto",
                            "imageRendering": "auto",
                            "data": data_dict
                        }
                        return create_html_element("details", content=[summary_element, img_element])
                    else:
                        img_element = {
                            "tag": "img", 
                            "path": hashed_filename, 
                            "collapsible": False, 
                            "collapsed": False,
                            "background": False,
                            "appearance": "auto",
                            "imageRendering": "auto",
                            "data": data_dict
                        }
                        html_elements.insert(0, img_element)
                
        return create_html_element("span", content=html_elements, data=data_dict)
    
    
    def get_normalized_filename(self, src_path: str) -> str:
        if not src_path:
            return ""
        
        if src_path.startswith('../'):
            src_path = src_path.replace('../', '', 1)
        
        if src_path.startswith("images") or src_path.startswith("gaiji"):
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