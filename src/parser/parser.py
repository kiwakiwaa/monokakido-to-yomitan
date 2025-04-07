import bs4

from utils import FileUtils
from yomitandic import Dictionary, DicEntry, create_html_element

class Parser:
    
    IGNORED_ELEMENTS = {}
    EXPRESSION_ELEMENT = None
    __YOMITAN_SUPPORTED_TAGS = {"br", "ruby", "rt", "rp", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "span", "div", "ol", "ul", "li"}
    
    
    def __init__(self, dict_name, dict_path):
        self.dict_data = FileUtils.read_xml_files(dict_path)
        self.dictionary = Dictionary(dict_name)
        
    
    def parse(self):
        raise NotImplementedError
    
    
    def parse_entry(self, entry_key, reading, soup, info_tag="", pos_tag="", search_rank=0, ignore_expressions=False):
        if not reading or reading is None:
            reading = ""
        
        if not entry_key:
            entry_key = reading
            reading = ""
        
        entry = DicEntry(entry_key, reading, info_tag=info_tag, pos_tag=pos_tag, search_rank=search_rank)
        
        for tag in soup.find_all(recursive=False):
            yomitan_element = self.convert_element_to_yomitan(tag, ignore_expressions=ignore_expressions)
            
            if yomitan_element:
                entry.add_element(yomitan_element)
                self.dictionary.add_entry(entry)
            else:
                print(f"Failed parsing entry: {entry_key}, reading: {reading}")
                return False
        
        return True
        
    
    def export(self, ouput_path=None):
        self.dictionary.export(ouput_path)
    
    
    def get_target_tag(self, tag):
        raise NotImplementedError
    
    
    def handle_link_element(self, html_glossary, html_elements, data_dict, class_list):
        raise NotImplementedError
    
    
    def get_image_path(self, html_glossary):
        return html_glossary.get("src", "").lstrip("/")
    
    
    def get_class_list_and_data(self, html_glossary):
        class_list = html_glossary.get("class", [])
        if isinstance(class_list, str):
            class_list = class_list.split(" ")
        
        data_dict = {}
        data_dict[html_glossary.name] = ""

        for cls in class_list:
            data_dict[cls.replace("-", "_")] = ""
                
        for attribute, value in html_glossary.attrs.items():
            if(isinstance(value, str)):
                data_dict[attribute.replace("-", "_")] = value
                
        return class_list, data_dict
    
    
    def _process_html_children(self, html_glossary, data_dict, ignore_expressions=False):
        html_elements = []
        
        if html_glossary.contents:
            for content in html_glossary.contents:
                if isinstance(content, bs4.Comment):
                    continue
                if isinstance(content, bs4.NavigableString) or isinstance(content, str):
                    html_elements.append(create_html_element("span", content))
                else:
                    converted_element = self.convert_element_to_yomitan(content, ignore_expressions=ignore_expressions)
                    if converted_element is not None:  # Avoid inserting None
                        html_elements.append(converted_element)
                        
        # Special case for img tags without contents
        elif html_glossary.name.lower() == "img":
            img_path = self.get_image_path(html_glossary)
            if img_path:
                
                # Use create_html_element instead of direct dictionary creation
                imgElement = {"tag": "img", "path": img_path, "collapsible": False, "data": data_dict}
                html_elements.insert(0, imgElement)
                
                return html_elements
        
        return html_elements  
    
    
    def convert_element_to_yomitan(self, html_glossary=None, ignore_expressions=False):
        # Recursively converts HTML elements into Yomitan JSON format
        tag_name = html_glossary.name.lower()
        if not html_glossary or tag_name in self.IGNORED_ELEMENTS:
            return None
        
        if ignore_expressions and self.EXPRESSION_ELEMENT and tag_name == self.EXPRESSION_ELEMENT:
            return None
                
        class_list, data_dict = self.get_class_list_and_data(html_glossary)
        
        # Recursively process children elements
        html_elements = self._process_html_children(html_glossary, data_dict, ignore_expressions=ignore_expressions)
        if not html_elements:
            return None
        
        # add elements that yomitan supports
        if tag_name in self.__YOMITAN_SUPPORTED_TAGS:
            return create_html_element(html_glossary.name, content=html_elements, data=data_dict)
        
        # map any custom tags to html
        target_tag = self.get_target_tag(html_glossary.name, class_list, html_glossary.parent)
        
        # Handle image elements where the content isnt empty
        if tag_name == "img" and html_glossary.contents:
            img_path = self.get_image_path(html_glossary)
            if img_path:
                imgElement = {"tag": "img", "path": img_path, "collapsible": False, "data": data_dict}
                html_elements.insert(0, imgElement)
                
                return create_html_element(target_tag, content=html_elements, data=data_dict)
        
        # Hanle link elements
        if tag_name == "a":
            element = self.handle_link_element(html_glossary, html_elements, data_dict, class_list) 
            if element:
                return element
        
        return create_html_element(target_tag, content=html_elements, data=data_dict)