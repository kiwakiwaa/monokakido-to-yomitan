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
LATIN_CHARS = re.compile(r'\p{Latin}[\p{Latin}\d\s\-\']*')

PUNCT_FIX_REGEX = re.compile(
    fr'(?<={JAPANESE_CHARS})([.,!?:，．！？：])|([.,!?:，．！？：])(?={JAPANESE_CHARS})'
)

JAPANESE_PUNCT = r'[。、！？：；]'
JP_PUNCT_SPACE_REGEX = re.compile(fr'({JAPANESE_PUNCT}){FULLWIDTH_SPACE}')
SINGLE_PUNCT_REGEX = re.compile(r'^[.,!?:，．！？：]$')

escaped_open = re.escape('([{{"\'')
escaped_close = re.escape(')]}}"\'')
OPEN_PUNCT_REGEX = re.compile(fr'([{escaped_open}])(?={JAPANESE_CHARS})')
CLOSE_PUNCT_REGEX = re.compile(fr'(?<={JAPANESE_CHARS})([{escaped_close}])')

TRAILING_JP_WHITESPACE_REGEX = re.compile(fr'{FULLWIDTH_SPACE}+$')
CONSECUTIVE_JP_WHITESPACE_REGEX = re.compile(fr'{FULLWIDTH_SPACE}{{2,}}')

NUMBERS = re.compile(r'\d+(?:\.\d+)?%?(?:[-–~～]\d+(?:\.\d+)?%?)?')

ROMAN_NUMERAL_ENTITY_REGEX = re.compile(r'&((?:I|V|X){1,4})(?:_w)?;')
ROMAN_NUMERALS = [
    'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
    'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX'
]

def replace_roman_numeral_entities(html_content):
    """Replace Roman numeral entities with properly formatted spans."""
    def replacement(match):
        roman_numeral = match.group(1)
        # Only process if it's a valid Roman numeral in our list
        if roman_numeral in ROMAN_NUMERALS:
            return f'<span class="roman_numeral">{roman_numeral}</span>'
        # If not valid, leave as is
        return match.group(0)
    
    # Replace all Roman numeral entity patterns
    return ROMAN_NUMERAL_ENTITY_REGEX.sub(replacement, html_content)

def contains_japanese(text):
    """Check if text contains Japanese characters."""
    return bool(re.search(JAPANESE_CHARS, text))

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

def get_surrounding_text_content(node, max_length=50):
    """Get surrounding text content to determine language context."""
    # Get previous siblings' text
    prev_text = ""
    current = node
    while current.previous_sibling and len(prev_text) < max_length:
        current = current.previous_sibling
        if isinstance(current, bs4.NavigableString):
            prev_text = str(current) + prev_text
        elif hasattr(current, 'get_text'):
            prev_text = current.get_text() + prev_text
    
    # Get parent's previous siblings if needed
    if len(prev_text) < 10 and node.parent and node.parent.previous_sibling:
        parent_prev = node.parent.previous_sibling
        if isinstance(parent_prev, bs4.NavigableString):
            prev_text = str(parent_prev) + prev_text
        elif hasattr(parent_prev, 'get_text'):
            prev_text = parent_prev.get_text() + prev_text
    
    # Get next siblings' text
    next_text = ""
    current = node
    while current.next_sibling and len(next_text) < max_length:
        current = current.next_sibling
        if isinstance(current, bs4.NavigableString):
            next_text += str(current)
        elif hasattr(current, 'get_text'):
            next_text += current.get_text()
    
    # Get parent's next siblings if needed
    if len(next_text) < 10 and node.parent and node.parent.next_sibling:
        parent_next = node.parent.next_sibling
        if isinstance(parent_next, bs4.NavigableString):
            next_text += str(parent_next)
        elif hasattr(parent_next, 'get_text'):
            next_text += parent_next.get_text()
    
    return prev_text, next_text

def should_use_japanese_punctuation(prev_text, next_text):
    """Determine if Japanese punctuation should be used based on context."""
    # Check if either previous or next content contains Japanese
    prev_has_japanese = bool(re.search(JAPANESE_CHARS, prev_text))
    next_has_japanese = bool(re.search(JAPANESE_CHARS, next_text))
    
    # Count Japanese and Latin characters
    jp_chars = len(re.findall(JAPANESE_CHARS, prev_text + next_text))
    latin_chars = len(re.findall(LATIN_CHARS, prev_text + next_text))
    
    # If there's Japanese on both sides, definitely use Japanese punctuation
    if prev_has_japanese and next_has_japanese:
        return True
    
    # If there's more Japanese than Latin overall, use Japanese punctuation
    return jp_chars > latin_chars

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
    html_content = replace_roman_numeral_entities(html_content)
    
    # Step 1: Replace HTML entities with placeholders
    modified_content, entity_map = preserve_html_entities(html_content)
    
    # Step 2: Parse with BeautifulSoup
    soup = BeautifulSoup(modified_content, 'html.parser')
    
    changes_made = False
    
    # First pass: handle isolated punctuation
    def process_isolated_punctuation():
        nonlocal changes_made
        
        # Find all spans with lang="ja" attribute that might contain punctuation
        for span in soup.find_all('span', lang='ja'):
            if should_skip_element(span):
                continue
                
            # Check if the span contains only punctuation
            text = span.get_text().strip()
            if len(text) == 1 and text in PUNCTUATION_MAP:
                # Get surrounding text
                prev_text, next_text = get_surrounding_text_content(span)
                
                # Check if Japanese punctuation should be used
                if should_use_japanese_punctuation(prev_text, next_text):
                    jp_punct = PUNCTUATION_MAP[text]
                    if span.string != jp_punct:
                        span.string.replace_with(jp_punct)
                        changes_made = True
        
        # Also check for any isolated punctuation in text nodes
        for text_node in soup.find_all(string=SINGLE_PUNCT_REGEX):
            if should_skip_element(text_node.parent):
                continue
                
            # Get the punctuation mark
            punct = str(text_node).strip()
            
            # Skip if not in our mapping
            if punct not in PUNCTUATION_MAP:
                continue
                
            # Get surrounding text
            prev_text, next_text = get_surrounding_text_content(text_node)
            
            # Check if Japanese punctuation should be used
            if should_use_japanese_punctuation(prev_text, next_text):
                jp_punct = PUNCTUATION_MAP[punct]
                if str(text_node) != jp_punct:
                    text_node.replace_with(jp_punct)
                    changes_made = True
    
    # Second pass: normal text processing
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
    
    # Apply both passes
    process_isolated_punctuation()
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