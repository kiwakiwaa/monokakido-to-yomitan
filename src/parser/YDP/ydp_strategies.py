import os
import bs4
import regex as re

from typing import List, Dict, Tuple
from yomitandic import create_html_element
from parser.base.strategies import ImageHandlingStrategy

"""
All svg files under formulas/ have been converted to png since the svgs didnt work well in yomitan
Im reading the viewbox in the svg to get the dimensions that I use to scale the images based on what type of
formula they are.
The 4 外字 are replaced with text equivalents
"""
class YDPImageHandlingStrategy(ImageHandlingStrategy):
    def __init__(self):
        self.replacements = {
            "arrow-thick.svg": {
                "text": "➡",
                "class": "gaiji_arrow_thick",
                "style": "font-size: 1.5em; font-weight: bold;"
            },
            "arrow-thin.svg": {
                "text": "→",
                "class": "gaiji_arrow_thin",
                "style": "font-size: 1.25em;"
            },
            "DSM-5.svg": {
                "text": "DSM-5",
                "class": "gaiji_dsm_5",
                "style": "border: 1px solid black; border-radius: 0.5em; padding: 0.1em 0.5em; font-weight: bold;"
            },
            "maruko.svg": {
                "text": "公",
                "class": "gaiji_maruko",
                "style": "display: inline-block; border: 2px solid black; border-radius: 50%; width: 1.5em; height: 1.5em; text-align: center; line-height: 1.5em;"
            }
        }
        
        # Cache for SVG viewBox dimensions to avoid repeated file reads
        self.svg_dimensions_cache = {}
        
        # Path to the dictionary files
        self.dictionary_path = "assets/YDP"
        
        # Configuration for different equation types
        self.equation_config = {
            "single_character": {
                "height": 0.8,
                "display_as_block": False,
                "adjust_width_factor": 1.0
            },
            "simple_symbol": {
                "height": 0.8,
                "display_as_block": False,
                "adjust_width_factor": 1.0
            },
            "regular_equation": {
                "height": 1.2,
                "display_as_block": False,
                "adjust_width_factor": 1.0
            },
            "tall_equation": {
                "height": 3,
                "display_as_block": True,
                "adjust_width_factor": 1
            },
            "tall_wide_equation": {
                "height": 4.0,
                "display_as_block": True,
                "adjust_width_factor": 1.0
            },
            "long_inline_equation": {
                "height": 1.5,
                "display_as_block": False,  # Some long equations might still be inline
                "adjust_width_factor": 1.0
            },
            "wide_equation": {
                "height": 1.8,
                "display_as_block": True,
                "adjust_width_factor": 1.0
            }
        }
        
    def extract_svg_viewbox(self, svg_path: str) -> Tuple[float, float]:
        """Extract width and height from SVG viewBox attribute"""
        try:
            # Use cached dimensions if available
            if svg_path in self.svg_dimensions_cache:
                return self.svg_dimensions_cache[svg_path]
            
            full_path = os.path.join(self.dictionary_path, svg_path)
            
            if not os.path.exists(full_path):
                return (0, 0)
            
            with open(full_path, 'r', encoding='utf-8') as f:
                svg_content = f.read()
            
            # Extract viewBox using regex
            viewbox_match = re.search(r'viewBox=["\']([-\d\.,\s]+)["\']', svg_content)
            if viewbox_match:
                viewbox = viewbox_match.group(1)
                values = re.split(r'[ ,]+', viewbox.strip())
                
                if len(values) >= 4:
                    try:
                        # The first two values are min-x and min-y, the last two are width and height
                        width = float(values[-2])
                        height = float(values[-1])
                        self.svg_dimensions_cache[svg_path] = (width, height)
                        return width, height
                    except ValueError:
                        pass
            
            # If viewBox not found or invalid, try width and height attributes
            width_match = re.search(r'width=["\']([\d\.]+)["\']', svg_content)
            height_match = re.search(r'height=["\']([\d\.]+)["\']', svg_content)
            
            if width_match and height_match:
                try:
                    width = float(width_match.group(1))
                    height = float(height_match.group(1))
                    self.svg_dimensions_cache[svg_path] = (width, height)
                    return width, height
                except ValueError:
                    pass
            
            return (0, 0)
        except Exception as e:
            print(f"Error extracting viewBox from {svg_path}: {e}")
            return (0, 0)
    
    def calculate_svg_dimensions(self, svg_path: str) -> Dict:
        """Calculate appropriate width and height for SVG based on its viewBox"""
        width, height = self.extract_svg_viewbox(svg_path)
        
        if width == 0 or height == 0:
            # Default values if dimensions cannot be determined
            return {"width": 3, "height": 1.5, "sizeUnits": "em", "display_as_block": False}
        
        aspect_ratio = width / height if height > 0 else 1
        
        # Determine the type of equation based on dimensions and content
        equation_type = self.classify_svg_content(width, height, svg_path)
        
        config = self.equation_config[equation_type]
        
        base_height = config["height"]
        base_width = base_height * aspect_ratio * config["adjust_width_factor"]
        
        # Ensure minimum width
        base_width = max(base_width, 0.8)
        
        # For very wide equations, if displayed as block, we can scale to a fixed width
        if equation_type in ("wide_equation", "tall_wide_equation") and config["display_as_block"]:
            if equation_type == "wide_equation":
                target_width = 8.0  # Target width for block display wide equations
            else:
                target_width = 10.0  # Target width for tall and wide equations
                
            # Only apply if the equation is wider than our target
            if base_width > target_width:
                scale_factor = target_width / base_width
                base_width = target_width
                base_height *= scale_factor
        
        return {
            "width": round(base_width, 2), 
            "height": round(base_height, 2), 
            "sizeUnits": "em",
            "display_as_block": config["display_as_block"]
        }
    
    def classify_svg_content(self, width: float, height: float, svg_path: str) -> str:
        """Classify the SVG content based on dimensions and content"""
        # Very long and tall equations
        if height > 15 and width > 100:
            return "tall_wide_equation"
            
        # Tall equations (fractions, etc.)
        elif height > 15:
            return "tall_equation"
            
        # Very long inline equations
        elif width > 100 and height < 10:
            return "long_inline_equation"
            
        # Very wide equations
        elif width > 150:
            return "wide_equation"
            
        # Single characters or simple symbols
        elif width < 10 and height < 10:
            # Optionally check SVG content to differentiate between characters and symbols
            return "single_character"
            
        # Regular equations
        else:
            return "regular_equation"
    
    def handle_image_element(self, html_glossary: bs4.element.Tag, html_elements: List, data_dict: Dict, class_list: List[str]) -> Dict:
        img_path = html_glossary.get("src", "").lstrip("/")
        
        if re.search(r'\.eps', img_path, flags=re.IGNORECASE):
            return None
        
        # Replace PDF and TIFF file extensions with PNG
        if img_path:
            img_path = re.sub(r'\.(pdf|tif|tiff)', '.png', img_path, flags=re.IGNORECASE)
        
        # Check if it's a gaiji image
        basename = os.path.basename(img_path)
        if basename in self.replacements:
            class_name = self.replacements[basename]["class"]
            if "class" not in data_dict:
                data_dict["class"] = class_name
            else:
                data_dict["class"] += " " + class_name
            
            html_elements = self.replacements[basename]["text"]
            
            return create_html_element("span", content=html_elements, data=data_dict)
        
        # Determine if it's an SVG and get dimensions
        is_svg = img_path.endswith(".svg") or img_path.startswith("formulas")
        dimensions = {}
        display_as_block = False
        
        if is_svg:
            dimensions = self.calculate_svg_dimensions(img_path)
            display_as_block = dimensions.pop("display_as_block", False)
            img_path = img_path[:-4] + '.png'
        
        imgElement = {
            "tag": "img", 
            "path": img_path, 
            "collapsible": False, 
            "collapsed": False,
            "background": False,
            "appearance": "auto",
            "imageRendering": "auto",
            "data": data_dict
        }
        
        # Apply the calculated dimensions
        if dimensions:
            imgElement.update(dimensions)
        
        html_elements.insert(0, imgElement)
        
        # Use div for block elements, span for inline elements
        if display_as_block:
            return create_html_element("div", content=html_elements, data=data_dict)
        else:
            return create_html_element("span", content=html_elements, data=data_dict)