import regex as re
from utils import KanjiUtils

class DaijisenUtils:
    
    
    @staticmethod
    def extract_plus_headword(soup):
        head_word = ""
        
        head_element = soup.find("headword", class_="見出")
        if head_element:

            head_word = head_element.text.strip()
            if any(KanjiUtils.is_kanji(c) for c in head_word):
                return KanjiUtils.clean_headword(head_word).split('・')
            else:
                head_word = re.sub("・", "", head_word)
                return [KanjiUtils.clean_headword(head_word)]
    
        return ""     
    
    
    @staticmethod
    def extract_wari_text(element):
        if element is None:
            return "", []
        
        # First extract the structure of the expression with placeholders for wari tags
        expression_parts = []  # The base expression parts
        wari_alternatives = []  # Will store [position, [alternatives]] for each wari tag
        
        for tag in element.contents:
            if tag.name == "wari":
                # Found a wari tag - store its position and extract alternatives
                alternatives = []
                parts = []
                current_part = []
                
                for content in tag.contents:
                    if hasattr(content, 'name') and content.name == "Hdot":
                        if current_part:
                            parts.append("".join(current_part))
                            current_part = []
                    else:
                        text = content.string if hasattr(content, 'string') else str(content)
                        current_part.append(text)
                
                # Add the last part
                if current_part:
                    parts.append("".join(current_part))
                
                # If we have multiple parts, store all alternatives
                if len(parts) > 1:
                    alternatives = [part.strip() for part in parts if part.strip()]
                else:
                    # Just one alternative
                    alternatives = [tag.text.strip()]
                
                # Add a placeholder in the expression
                expression_parts.append(f"__WARI_{len(wari_alternatives)}__")
                
                # Store position and alternatives
                wari_alternatives.append((len(expression_parts) - 1, alternatives))
                
            elif isinstance(tag, str):
                text = tag.strip()
                if text:
                    expression_parts.append(text)
            else:
                text = tag.text.strip()
                if text:
                    expression_parts.append(text)
        
        # Create the base expression (without wari content)
        base_expression = "".join([part for part in expression_parts if not part.startswith("__WARI_")])
        clean_base = KanjiUtils.clean_headword(base_expression)
        
        # Now generate all possible reading combinations - only complete expressions
        all_readings = []
        
        # Function to generate all combinations of alternatives
        def generate_combinations(current_pos, current_reading):
            if current_pos >= len(wari_alternatives):
                # We've processed all wari tags, add the completed reading
                full_reading = "".join(current_reading)
                clean_reading = KanjiUtils.clean_reading(full_reading)
                if clean_reading and clean_reading not in all_readings:
                    all_readings.append(clean_reading)
                return
            
            # For the current wari position, try each alternative
            pos, alternatives = wari_alternatives[current_pos]
            for alt in alternatives:
                # Create a new reading with this alternative
                new_reading = current_reading.copy()
                new_reading[pos] = alt
                
                # Proceed to the next wari position
                generate_combinations(current_pos + 1, new_reading)
        
        # Start the combination process
        if wari_alternatives:
            # Create a reading template with placeholders
            reading_template = expression_parts.copy()
            generate_combinations(0, reading_template)
        else:
            # No wari tags, just use the expression as is
            all_readings.append(KanjiUtils.clean_reading("".join(expression_parts)))
        
        clean_base = re.sub("・", "", clean_base)
        return clean_base, all_readings
        
    
    @staticmethod
    def extract_headword(soup):
        head_word = ""
        
        head_element = soup.find("headword", class_="表記")
        if head_element:

            head_word = head_element.text.strip()
            if any(KanjiUtils.is_kanji(c) for c in head_word):
                return KanjiUtils.clean_headword(head_word).split('・')
            else:
                head_word = re.sub("・", "", head_word)
                return [KanjiUtils.clean_headword(head_word)]
    
        return ""
    
    
    @staticmethod
    def extract_reading(soup):
        reading = ""
        
        # Attempt to find a reading in the Head element
        head_element = soup.find("headword", class_="見出")
        if head_element:
            reading = head_element.text.strip()
            if not any(KanjiUtils.is_kanji(c) for c in reading):
                return KanjiUtils.clean_reading(reading)
                
        return ""