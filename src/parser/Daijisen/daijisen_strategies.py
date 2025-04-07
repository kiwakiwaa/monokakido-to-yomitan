import bs4
from typing import Dict, List, Optional, Tuple

from utils import KanjiUtils
from yomitandic import create_html_element

from parser.base.strategies import LinkHandlingStrategy, ImageHandlingStrategy

class DaijisenLinkHandlingStrategy(LinkHandlingStrategy):
    def handle_link_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                            data_dict: Dict, class_list: List[str]) -> Dict:   
        """Handle link elements for Daijisen""" 
        href = html_glossary.get("href", "")
        if href and href.startswith("map:ll="):
            # Extract coordinates from the href and create an Apple maps link
            try:
                coords_part = href.split("map:ll=")[1].split("&")[0]
                lat, lng = coords_part.split(",")
                
                apple_maps_url = f"https://maps.apple.com/?ll={lat},{lng}"
                return create_html_element("a", content=html_elements, href=apple_maps_url)
            except Exception as e:
                print(f"Error processing map coordinates: {e}")
                
        elif "blue" in class_list:
            collected_text = []
            
            for child in html_glossary.contents:
                if child.name == "wari":
                    continue
                if isinstance(child, str):  # Plain text
                    collected_text.append(child.strip())
                elif child.name:  # Other elements, preserve their text
                    collected_text.append(child.get_text(strip=True))

            href = "".join(filter(None, collected_text))
            if href:
                return create_html_element("a", content=html_elements, href="?query="+href+"&wildcards=off")
        
        else:
            return create_html_element("span", content=html_elements, data=data_dict)
        
        
class DaijisenImageHandlingStrategy(ImageHandlingStrategy):
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List,
                       data_dict: Dict, class_list: List[str]) -> Dict:
        # Check if the src attribute ends with .heic
        src_attr = html_glossary.get("src", "")
        if src_attr.lower().endswith('.heic'):
            jpg_src = src_attr[:-5] + '.avif'
            
            imgElement = {"tag": "img", "path": jpg_src, "collapsible": False, "data": data_dict}
            html_elements.insert(0, imgElement)
    
        return create_html_element("span", content=html_elements, data=data_dict)