#!/usr/bin/env python3

import json
import regex as re
import argparse
from bs4 import BeautifulSoup

import bs4
FULLWIDTH_SPACE = '\u3000'
NORMAL_SPACE = ' '

SKIP_TAGS = {'a', 'script', 'style', 'code'}
SKIP_CLASSES = {'imageMark'}

PUNCTUATION_MAP = {
    '.': '。', 
    ',': '、',
    '!': '！',
    '?': '？',
    ':': '：',
    '，': '、',
    '．': '。'
}

OPEN_PUNCT_MAP = {
    '(': '（',
    '[': '［',
    '{': '｛',
    '"': '「',
    "'": '「',
}

CLOSE_PUNCT_MAP = {
    ')': '）',
    ']': '］',
    '}': '｝',
    '"': '」',
    "'": '」',
}


JAPANESE_CHARS = r'[\p{Script=Hiragana}\p{Script=Katakana}\p{Script=Han}ー]'

PUNCT_FIX_REGEX = re.compile(
    fr'(?<={JAPANESE_CHARS})([.,!?:，．！？：])|([.,!?:，．！？：])(?={JAPANESE_CHARS})'
)

escaped_open = re.escape('([{{"\'')
escaped_close = re.escape(')]}}"\'')

OPEN_PUNCT_REGEX = re.compile(fr'([{escaped_open}])(?={JAPANESE_CHARS})')
CLOSE_PUNCT_REGEX = re.compile(fr'(?<={re})([{escaped_close}])')

TRAILING_JP_WHITESPACE_REGEX = re.compile(fr'{FULLWIDTH_SPACE}+$')
CONSECUTIVE_JP_WHITESPACE_REGEX = re.compile(fr'{FULLWIDTH_SPACE}{{2,}}')

JAPANESE_PUNCT = r'[。、！？：；]'
JP_PUNCT_SPACE_REGEX = re.compile(fr'({JAPANESE_PUNCT}){FULLWIDTH_SPACE}')

LATIN_CHARS = re.compile(r'\p{Latin}[\p{Latin}\d\s\-\']*')

NUMBERS = re.compile(r'\d+(?:\.\d+)?%?(?:[-–~～]\d+(?:\.\d+)?%?)?')

def contains_japanese(text):
    """Check if text contains Japanese characters."""
    return bool(JAPANESE_CHARS.search(text))

def fix_spaces_in_latin(text):
    text = re.sub(r'(?<=\p{Latin})\u3000(?=\p{Latin})', NORMAL_SPACE, text)
    text = re.sub(r'(?<=\p{Latin})－(?=\p{Latin})', '-', text)
    return text

def fix_punctuation(text):
    return PUNCT_FIX_REGEX.sub(
        lambda m: PUNCTUATION_MAP.get(m.group(1) or m.group(2), m.group(0)), text
    )
    
def fix_japanese_whitespace(text):
    text = TRAILING_JP_WHITESPACE_REGEX.sub('', text)
    
    text = CONSECUTIVE_JP_WHITESPACE_REGEX.sub(FULLWIDTH_SPACE, text)
    
    text = JP_PUNCT_SPACE_REGEX.sub(r'\1', text)
    
    return text

def fix_punctuation_and_par(text):
    text = fix_punctuation(text)
    text = OPEN_PUNCT_REGEX.sub(lambda m: OPEN_PUNCT_MAP[m.group(1)], text)
    text = CLOSE_PUNCT_REGEX.sub(lambda m: CLOSE_PUNCT_MAP[m.group(1)], text)
    
    return text

def process_text_node(text):
    """Process a text node, fixing spaces and punctuation."""
    if not text or len(text) == 0:
        return text
    
    text = fix_punctuation(text) 
    
    text = fix_spaces_in_latin(text)
    
    text = fix_japanese_whitespace(text)
    
    return text

def should_skip_element(el):
    if el.name in SKIP_TAGS:
        return True
    classes = el.get('class', [])
    return any(cls in SKIP_CLASSES for cls in classes)


def preserve_html_entities(html_content):
    """Replace HTML entities with temporary placeholders before parsing."""
    entity_map = {}
    counter = 0
    
    # Regular expression to find HTML entities like &vBar;
    def replace_entity(match):
        nonlocal counter
        placeholder = f"__ENTITY_{counter}__"
        counter += 1
        entity_map[placeholder] = match.group(0)
        return placeholder
    
    # Replace all &word; patterns with placeholders
    modified_content = re.sub(r'&([a-zA-Z0-9#]+);', replace_entity, html_content)
    
    return modified_content, entity_map

def restore_html_entities(html_content, entity_map):
    """Restore HTML entities from placeholders after parsing."""
    for placeholder, entity in entity_map.items():
        html_content = html_content.replace(placeholder, entity)
    return html_content

def process_html_content(html_content):
    """Process HTML content and preserve entities."""
    # Step 1: Replace HTML entities with placeholders
    modified_content, entity_map = preserve_html_entities(html_content)
    
    # Step 2: Parse with BeautifulSoup
    soup = BeautifulSoup(modified_content, 'html.parser')
    
    changes_made = False
    
    def process_node(node):
        nonlocal changes_made
        # Skip comments
        if isinstance(node, bs4.Comment):
            return
            
        # Process direct text in the current node
        if isinstance(node, bs4.NavigableString) and not isinstance(node, bs4.CData):
            parent = node.parent
            if parent and not should_skip_element(parent):
                original = str(node)
                fixed = process_text_node(original)
                if fixed != original:
                    node.replace_with(fixed)
                    changes_made = True
            return
            
        # Recurse into children
        for child in list(node.children):
            process_node(child)
    
    process_node(soup)
    
    # Step 3: Convert back to string and restore entities
    processed_html = str(soup)
    final_html = restore_html_entities(processed_html, entity_map)
    
    return final_html, changes_made


def main():
    parser = argparse.ArgumentParser(description='Fix dictionary text formatting')
    parser.add_argument('input_file', help='Input JSON dictionary file')
    parser.add_argument('output_file', help='Output JSON dictionary file')
    parser.add_argument('--verbose', '-v', action='store_true', help='Print detailed information')
    parser.add_argument('--test', '-t', help='Test a piece of text instead of processing files')
    
    args = parser.parse_args()
    
    # Test mode
    if args.test:
        print(f"Input:  {args.test}")
        print(f"Output: {process_text_node(args.test)}")
        return
    
    try:
        print(f"Reading dictionary from {args.input_file}...")
        with open(args.input_file, 'r', encoding='utf-8') as f:
            dictionary = json.load(f)
        
        print(f"Processing {len(dictionary)} entries...")
        fixed_count = 0
        fixed_dictionary = {}
        
        for key, content in dictionary.items():
            fixed_content, changes_made = process_html_content(content)
            
            if changes_made:
                fixed_count += 1
                if args.verbose:
                    print(f"Fixed entry: {key}")
            
            fixed_dictionary[key] = fixed_content
        
        print(f"Writing fixed dictionary to {args.output_file}...")
        with open(args.output_file, 'w', encoding='utf-8') as f:
            json.dump(fixed_dictionary, f, ensure_ascii=False, indent=2)
        
        print(f"Successfully processed {len(dictionary)} entries, fixed {fixed_count} entries.")
        
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    main()
