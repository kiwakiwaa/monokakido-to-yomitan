import bs4
import os
from typing import Dict, List, Optional, Tuple

from utils import KanjiUtils
from yomitandic import create_html_element

from parser.base.strategies import LinkHandlingStrategy, ImageHandlingStrategy
from parser.RGKO12.image_file_map import IMAGE_FILE_MAP

class Rgko12LinkHandlingStrategy(LinkHandlingStrategy):
    
    def __init__(self):
        self.appendix_entries = {
            "appendix/010_編集のことば.html": "【例解】付録：編集のことば",
            "appendix/020_辞典で新たな世界をひらこう.html": "【例解】付録：この辞典で新たな世界をひらこう",
            "appendix/030_この辞典の使い方.html": "【例解】付録：この辞典の使い方",
            "appendix/040_辞典を100倍活用する方法.html": "【例解】付録：辞典を100倍活用する方法",
            "appendix/050_記号一覧.html": "【例解】付録：記号一覧",
            "appendix/070_編集された先生がた.html": "【例解】付録：編集された先生がた",
            "appendix/100_人の性格に関することば.html": "【例解】付録：人の性格に関することば", 
            "appendix/110_敬語の使い方.html": "【例解】付録：敬語の使い方",
            "appendix/120_ものの数え方.html": "【例解】付録：ものの数え方",
            "appendix/130_ことばのはたらき.html": "【例解】付録：ことばのはたらき",
            "appendix/140_ことばの組み合わせ.html": "【例解】付録：ことばの組み合わせ",
            "appendix/150_符号の使い方.html": "【例解】付録：符号の使い方",
            "appendix/160_かなづかいきまり.html": "【例解】付録：かなづかいきまり",
            "appendix/170_送りがなのきまり.html": "【例解】付録：送りがなのきまり",
            "appendix/180_かたかなで書くことば.html": "【例解】付録：かたかなで書くことば",
            "appendix/200_アクセントと方言.html": "【例解】付録：アクセントと方言",
            "appendix/210_原こう用紙・手紙の書き方.html": "【例解】付録：原こう用紙・手紙の書き方",
            "appendix/220_とくべつな読みのことば.html": "【例解】付録：とくべつな読みのことば",
            "appendix/230_印刷文字と手書き文字.html": "【例解】付録：印刷文字と手書き文字",
            "appendix/240_日本の旧国名.html": "【例解】付録：日本の旧国名",
            "appendix/250_小倉百人一首.html": "【例解】付録：小倉百人一首"
        }
        
    
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
        self.gaiji_replacements = {
            "arrow-black-down-thick.svg": {
                "text": "➡",
                "class": "外字 矢印"
            },
            "arrow-black-up-thick.svg": {
                "text": "⇨",
                "class": "外字 矢印"
            },
            "arrow-white-down-thick.svg": {
                "text": "⇨",
                "class": "外字 矢印"
            },
            "dash.svg": {
                "text": "-",
                "class": "外字"
            },
            "equal.svg": {
                "text": "＝",
                "class": "外字"
            },
            "hyphen.svg": {
                "text": "-",
                "class": "外字"
            },
            "参照.svg": {
                "text": "⇨",
                "class": "外字 矢印"
            },
            "活用.svg": {
                "text": "活用▶",
                "class": "外字 全丸 fill"
            },
            "コラム.svg": {
                "text": "コラム",
                "class": "外字 全丸 fill orange"
            },
            "関連.svg": {
                "text": "関連",
                "class": "外字 左丸"
            },
            "敬語.svg": {
                "text": "敬語",
                "class": "外字 左丸"
            },
            "黒三角.svg": {
                "text": "▶",
                "class": "外字 三角"
            },
            "三角.svg": {
                "text": "▷",
                "class": "外字 三角"
            },
            "参考.svg": {
                "text": "参考",
                "class": "外字 左丸"
            },
            "熟語.svg": {
                "text": "熟語▶",
                "class": "外字 全丸 fill"
            },
            "図表-ミニ情報.svg": {
                "text": "◆",
                "class": "外字 ダイヤ blue"
            },
            "図表-使い分け.svg": {
                "text": "使い分け",
                "class": "外字 全丸 fill light-brown"
            },
            "図表-使い分け縦.svg": {
                "text": "使い分け",
                "class": "外字 全丸 fill light-brown"
            },
            "図表-使い方.svg": {
                "text": "◆",
                "class": "外字 ダイヤ orange"
            },
            "図表-組み合わせ.svg": {
                "text": "◆",
                "class": "外字 ダイヤ red"
            },
            "成句.svg": {
                "text": "成句",
                "class": "外字 左丸"
            },
            "別読み.svg": {
                "text": "➡",
                "class": "外字 矢印"
            },
            "int_down.svg": {
                "text": "⤵",
                "class": "外字 下印"
            },
            "ellipsis.svg": {
                "text": "●",
                "class": "外字"
            }
        }
        
        
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