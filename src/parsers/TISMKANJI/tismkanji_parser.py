import os
import json
import regex as re
from typing import Dict, List, Optional

from utils import KanjiUtils, FileUtils

from core import Parser
from config import DictionaryConfig
from parsers.TISMKANJI.tismkanji_utils import TismKanjiUtils
from core.yomitan_dictionary import DicEntry, create_html_element

    
class TismKanjiParser(Parser):
    
    def __init__(self, config: DictionaryConfig):
        super().__init__(config)
        
        self.dict_data = {i: item for i, item in enumerate(TismKanjiUtils.load_json(config.dict_path))}
        self.kanken_data = FileUtils.load_json(os.path.join(os.path.dirname(__file__), "kanken_data.json"))
        
        self.kanken_level_map = {}
        for level in self.kanken_data.get('groups', []):
            level_name = level.get('name', '')
            for kanji in level.get('characters', []):
                self.kanken_level_map[kanji] = level_name
    
    
    def clean_content(self, text: str) -> str:
        text = re.sub(r'◆', '', text)  # Remove bullet points
        text = re.sub(r'◇', '', text)
        text = re.sub(r'。+', '。', text)  # Replace multiple consecutive '。' with a single '。'
        text = re.sub(r'、+', '、', text)
        text = re.sub(r'\n\s*\n+', '\n', text)
        return text.strip() 
            
            
    def create_kanken_level_element(self, kanji: str) -> Dict:
        # 漢字検定レベルを確定、ディフォルトは配当外
        kanken_level = self.kanken_level_map.get(kanji, self.kanken_data.get('leftover_group', '配当外'))
                
        html_elements = []
        data_dict = {}
        data_dict[f"{kanken_level}"] = ""
        data_dict["漢検級"] = ""
        inner_element = create_html_element(
            "span", 
            content=kanken_level, 
            title=f"日本語漢字能力検定の{kanken_level}",
            data=data_dict
        )
        html_elements.append(inner_element)
        
        data_dict = {}
        data_dict["漢検G"] = ""
        return create_html_element("div", content=html_elements, data=data_dict)
    
    
    def create_reading_element(self, content: str) -> Dict:
        reading_types = {
            "音読み": "音",
            "訓読み": "訓"
        }
        
        collected_content = []
        for label, short_label in reading_types.items():
            
            match = re.search(fr'【{label}】([^\n]+)', content)
            if match:
                readings = [reading.strip() for reading in match.group(1).strip().split('、')]
                formatted_readings = '／'.join(readings)
                
                data_dict = {}
                data_dict["rect"] = ""
                reading_tag_element = create_html_element(
                    "span",
                    title=label,
                    content=short_label,
                    data=data_dict
                )
                data_dict = {}
                data_dict["よみ"] = ""
                reading_element = create_html_element(
                    "span",
                    content=formatted_readings,
                    data=data_dict
                )
                data_dict = {}
                data_dict[f"{short_label}アイテム"] = ""
                outer_element = create_html_element(
                    "span", 
                    content=[reading_tag_element, reading_element], 
                    data=data_dict
                )
                collected_content.append(outer_element)
                
        data_dict = {}
        data_dict["よみG"] = ""
        return create_html_element("div", content=collected_content, data=data_dict)
    
    
    def create_definition_element(self, definition: str) -> Dict:
        # 1. Replace カタカナ漢字 in the beginning of the text with 漢字(カタカナ)
        # 2. Replace 「漢字カタカナ」with 漢字(カタカナ)
        # Also works for example like 「鸒𪆁・鸒斯イシ」and 「髻タブサ・モトドリ」
        text = TismKanjiUtils.replace_furigana_pattern(re.compile(r'^(?<furigana>\p{Katakana}+)(?<kanji>\p{Han}+)'), definition)
        text = TismKanjiUtils.replace_furigana_pattern(re.compile(r'[「・](?<kanji>\p{Han}+(?:・\p{Han}+)?)(?<furigana>\p{Katakana}+(?:・\p{Katakana}+)?)(?:」)?'), text)
        
        # Add furigana style to 漢字（かな）pattern
        furigana_full = r'([^()]+)\(([^)]+)\)'
        pattern = re.compile(furigana_full)
        
        parts = []
        last_index = 0
        
        for match in pattern.finditer(text):
            start, end = match.span()
            
            # Add the text from the previous match to the beginning of the current match
            if start > last_index:
                parts.append(text[last_index:start])
                
            if match.group(1) and match.group(2):
                text_before, furigana = match.group(1), match.group(2)
                
                # Make sure that the character before the furigana is a kanji
                # Also make sure that the matched furigana doesn't include any kanji
                if not any(KanjiUtils.is_kanji(c) for c in furigana) and KanjiUtils.is_kanji(text_before[-1]):
                    parts.append(text_before)
                    
                    # Add furigana styling to the matched furigana
                    data_dict = {}
                    data_dict["振り仮名"] = ""
                    furigana_element = create_html_element("span", content=f'({furigana})', data=data_dict)
                    parts.append(furigana_element)
                else: 
                    # Wasnt valid furigana, simply add the full text
                    parts.append(match.group(0))
            else:
                # No match, simply add the full text
                parts.append(match.group(0))
                
            # Save the end index of the current match
            last_index = end
        
        # Add the remaining text from the last match
        if last_index < len(text):
            parts.append(text[last_index:])
            
        data_dict = {}
        data_dict["rect"] = ""
        meaning_tag = create_html_element(
            "span",
            title="漢字の持つ意味",
            content="意味",
            data=data_dict
        )
        data_dict = {}
        data_dict["意味内容"] = ""
        definition_content = create_html_element("span", content=parts, data=data_dict)
            
        data_dict = {}
        data_dict["意味G"] = ""
        return create_html_element("div", content=[meaning_tag, definition_content], data=data_dict)
        
        
    def create_notes_element(self, notes: List[Dict]) -> Dict:
        collected_content = []
        for note in notes:
            note_type = note.get("type", "")
            note_content = self.clean_content(note.get("content", ""))
            
            type_element = create_html_element("span", content=note_type, data={"rect": ""})
            content_element = create_html_element("span", content=note_content, data={f"{note_type}": ""})
            note_element = create_html_element("div", content=[type_element, content_element], data={f"{note_type}項": ""})
            collected_content.append(note_element)
            
        if collected_content:
            return create_html_element("div", content=collected_content, data={"注解G": ""})
        else:
            return None
        
        
    def create_itaiji_element(self, content: str) -> Dict:
        itaiji_pattern = re.search(r'【異体字】(.+?)(?=\n【|$)', content, re.DOTALL)
        if not itaiji_pattern:
            return None
        
        itaiji_text = itaiji_pattern.group(1).strip()
        itaiji_text = re.sub('。', '', itaiji_text)
        itaiji_text = re.sub('}', '', itaiji_text)
        itaiji_text = re.sub('はかま', '', itaiji_text)
            
        itaiji_content = []
        if itaiji_text:
            tag_element = create_html_element("span", content="異体字", data={"rect": ""})
            itaiji_element = create_html_element("span", content=itaiji_text, data={"異体字": ""})
            itaiji_content.append(tag_element)
            itaiji_content.append(itaiji_element)
            
        if itaiji_content:
            return create_html_element("div", content=itaiji_content, data={"異体字G": ""})
        else:
            return None
        
        
    def create_busyu_element(self, content: str) -> Dict:
        busyu_pattern = re.search(r'【部首】(.+?)(?=\n【|$)', content, re.DOTALL)
        if not busyu_pattern:
            return None
        
        busyu_text = busyu_pattern.group(1).strip()
        busyu_text = re.sub('。', '', busyu_text)
        busyu_text = re.sub('}', '', busyu_text)
        busyu_text = re.sub('\?', '', busyu_text)
            
        busyu_content = []
        if busyu_text:
            tag_element = create_html_element("span", content="部首", data={"rect": ""})
            itaiji_element = create_html_element("span", content=busyu_text, data={"部首": ""})
            busyu_content.append(tag_element)
            busyu_content.append(itaiji_element)
            
        if busyu_content:
            return create_html_element("div", content=busyu_content, data={"部首G": ""})
        else:
            return None
    
    
    def extract_meaning(self, content: str) -> str:
        meaning_pattern = re.search(r'【意味】(.+?)(?=\n【|$)', content, re.DOTALL)
        
        if not meaning_pattern:
            return ""

        return self.clean_content(meaning_pattern.group(1).strip())
    
    
    def _process_file(self, idx: str, glossary: str) -> int:
        try: 
            # Extract glossary
            kanji = glossary[0] if len(glossary) > 0 else ""
            reading = glossary[1] if len(glossary) > 1 else ""
            content = ""
            if len(glossary) > 5 and isinstance(glossary[5], list) and len(glossary[5]) > 0:
                content = glossary[5][0]
            
            # Create entry
            entry = DicEntry(kanji, reading)
            
            # Extract meaning components
            meaning = self.extract_meaning(content)
            definition, notes = TismKanjiUtils.separate_notes(meaning)
            
            if not kanji:
                return 0
            if reading:
                print(f"\nFound reading for entry (kanji: {kanji}) id {idx}\nReading: {reading}")
            
            # 1. Get Kanken tag element
            kanken_element = self.create_kanken_level_element(kanji)
            
            # 2. Get 音 and 訓 readings
            reading_element = self.create_reading_element(content)
            
            # 3. Get formatted definition element
            definition_element = self.create_definition_element(definition)
            
            # 4. Get formatted Notes div
            notes_element = self.create_notes_element(notes)
            
            # 5. Get formatted 異体字 div
            itaiji_element = self.create_itaiji_element(content)
            
            # 6. Get formatted 部首 div
            busyu_element = self.create_busyu_element(content)
            
            # 7. Create a div with all elements and add it to entry
            elements = [kanken_element, reading_element, definition_element]
            if notes_element:
                elements.append(notes_element)
            if itaiji_element:
                elements.append(itaiji_element)
            if busyu_element:
                elements.append(busyu_element)
            
            data_dict = {}
            data_dict["entry"] = ""
            entry_content = create_html_element("div", content=elements, data=data_dict)
            
            # Add to dictionary
            entry.add_element(entry_content)
            self.dictionary.add_entry(entry)
            return 1
        
        except Exception as e:
            print(f"\nError processing entry (kanji: {kanji}) id {idx}: {e}")
            return 0