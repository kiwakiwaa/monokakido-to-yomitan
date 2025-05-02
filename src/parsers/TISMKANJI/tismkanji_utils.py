import os
import json
import regex as re
from typing import Tuple, List, Dict, Any

class TismKanjiUtils:
    
    PUNCTUATION_PATTERN = re.compile(r'[、-〿]')
    
    @staticmethod
    def replace_furigana_pattern(pattern, text):
        for match in pattern.finditer(text):
            start, _ = match.span()
            full_text, kanji, furigana = match.group(0), match.group("kanji"), match.group("furigana")
            
            # Check if the last character is Japanese punctuation, don't add a comma in that case
            preceding_char = text[start - 1] if start > 0 else ""
            if start == 0 or TismKanjiUtils.PUNCTUATION_PATTERN.search(preceding_char) or preceding_char == '\n':
                text = re.sub(full_text, kanji + f'({furigana})', text)
            else:
                text = re.sub(full_text, "、" + kanji + f'({furigana})', text)
            
        return text
    
    
    @staticmethod
    def separate_notes(content: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Separates main definitions from notes (注/注解) in 漢字林.
        Handles nested structures within notes and multiple note types.
        
        Args:
            content: The raw content string containing definitions and notes
            
        Returns:
            tuple: (cleaned_definitions, notes_list)
            where notes_list contains dicts with {'type': '注'/'注解', 'content': note_text}
        """
        # Initialize
        notes = []
        remaining_content = content
        
        # Pattern to match both 注 and 注解 with their content
        # Uses atomic grouping (?>...) for better performance with nested structures
        note_pattern = r'''
            (?<note>
                (?<type>注解|注)       # Note type (注 or 注解)
                [：:]?\s*              # Optional colon/space after type
                (?<content>
                    (?:                # Content can contain:
                        (?!\n注解|\n注) # - Anything until next note marker
                        [^\n]          # - Any non-newline char
                        |              # OR
                        「[^」]*」      # - Balanced brackets (non-greedy)
                        |             # OR
                        \{.*?\}       # - Special characters in braces
                    )+
                )
            )
        '''
        
        # Find all notes and their positions
        matches = list(re.finditer(note_pattern, remaining_content, re.VERBOSE | re.MULTILINE))
        
        # Process from last to first to maintain correct positions
        for match in reversed(matches):
            note_type = match.group('type')
            note_content = match.group('content').strip()
            
            # Remove the note from the main content
            remaining_content = (
                remaining_content[:match.start()] + 
                remaining_content[match.end():]
            )
            
            # Clean note content (handle nested structures)
            note_content = re.sub(r'^\s*[：:]\s*', '', note_content)  # Remove leading colons
            note_content = note_content.replace('\n', ' ')  # Normalize newlines
            
            notes.insert(0, {  # Insert at beginning to maintain order
                'type': note_type,
                'content': note_content
            })
        
        # Clean the remaining definition content
        cleaned_definitions = re.sub(r'\n\s*\n+', '\n', remaining_content).strip()
        return cleaned_definitions, notes
    
    
    def load_json(dir_path: str) -> Dict[str, Any]:
        """
        Load the first JSON file found in the specified directory.
        """
        try:
            # Check if the directory exists
            if not os.path.isdir(dir_path):
                print(f"Error: {dir_path} is not a valid directory")
                return {}
                
            # Find all JSON files in the directory
            json_files = [f for f in os.listdir(dir_path) if f.lower().endswith('.json')]
            
            if not json_files:
                print(f"No JSON files found in {dir_path}")
                return {}
                
            # Get the first JSON file
            json_file_path = os.path.join(dir_path, json_files[0])
            
            # Load and return the JSON data
            with open(json_file_path, 'r', encoding='utf-8') as f:
                mdx_data = json.load(f)
                print(f"Successfully loaded JSON file: {json_files[0]}")
                return mdx_data
                
        except Exception as e:
            print(f"Error loading MDX JSON file: {e}")
            return {}


# Test cases
#test_cases = [
    # Example 1
    #"""◆宮中内の道、同「𡆵」。\n注：「【爾雅注疏:釋宮】宮中衖謂之壼…」\n◆宮中の婦女子が居住するところ、またそこに住む婦女子、「壼闈コンイ」\n注解:本字は{⿳士冖亞}で「壺」とは別字6178\n""",
    
    # Example 2
    #"""◆「壿壿ソンソン」、奮(ふる)い立つ、奮い立たせる、鼓舞コブする。\n注：「【爾雅注疏:釋訓】坎坎墫墫喜也(臣照按疏引詩墫墫舞我説文作竷竷舞我鄭{⿱椎灬}曰據詩所言非喜意但喜躍而鼓舞也)」\n注：「【說文解字注:士部:墫】士舞也(各本無士依詩爾雅音義補周禮大胥以學士合舞小胥巡學士舞列故其字从士也當爲皃毛傳墫墫舞皃古書也皃二字多互譌)从士𢍜聲(慈損切十三部)詩曰墫墫舞我(詩小雅文爾雅坎坎墫墫喜也今詩作蹲)」\n注解:本字は「士部{⿰士尊}」で「土部」の「墫」とは別字6191\n""",
    
    # Example 3
    #"""◆鼻口部ビコウブ(動物の鼻と口が突き出た部分)の長い犬、鼻口部が短い犬を「猲獢ケツキョウ」。\n◆体は黒く頭が黄色い犬。\n◆「猃狁ケンイン」、古代の中国北方の異民族の名、同「玁狁」、【廣韻】ば夏代(前21世紀～前17世紀)に「獯鬻クンイク」、漢代(前202年～220年)に「匈奴キョウド」と呼ばれた民族の西周代(前1046年～前771年)の名とする。\n注：「【廣韻:上平聲:文第二十:薰:獯】北方胡名夏曰獯鬻周曰獫狁漢曰匈奴」\n""",
    
    # Example 4
    #"""◆「𤞤狁ケンイン」、古代の中国北方の異民族の名、同「獫狁」、【廣韻】ば夏代(前21世紀～前17世紀)に「獯鬻クンイク」、漢代(前202年～220年)に「匈奴キョウド」と呼ばれた民族の西周代(前1046年～前771年)の名とする。\n注：「【太平御覽:卷第七百九十九四:四夷部二十:北狄一:揔敘北狄上】…文王之時西有昆夷之患北有玁狁之難…(「文王」は周朝の始祖)」\n注：「【廣韻:上平聲:文第二十:薰:獯】北方胡名夏曰獯鬻周曰獫狁漢曰匈奴」\n"""
#]
""" 
for i, test_case in enumerate(test_cases, 1):
    print(f"\n=== Processing Example {i} ===")
    definitions, notes = separate_notes(test_case)
    
    print("\nDefinitions:")
    print(definitions)
    
    print("\nNotes:")
    for note in notes:
        print(f"{note['type']}: {note['content']}")
 """