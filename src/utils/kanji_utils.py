import unicodedata
import regex as re
from typing import List, Tuple, Optional


class KanjiUtils:
    CJK_RE = re.compile("CJK (UNIFIED|COMPATIBILITY) IDEOGRAPH")
    IS_NOT_JAPANESE_PATTERN = re.compile(r'[^\p{N}○◯々-〇〻ぁ-ゖゝ-ゞァ-ヺー０-９Ａ-Ｚｦ-ﾝ\p{Radical}\p{Unified_Ideograph}]+')
    JAPANESE_PATTERN = re.compile(r"[\p{Hiragana}\p{Katakana}\p{Unified_Ideograph}]+", re.UNICODE)
      
    @staticmethod
    def is_kanji(unichar: str) -> bool:
        return bool(KanjiUtils.CJK_RE.match(unicodedata.name(unichar, "")))
    
    
    @staticmethod
    def is_katakana(char: str) -> bool:
        if len(char) != 1:
            raise ValueError("This function checks a single character only")
            
        # Using a regex pattern that includes all Katakana blocks
        pattern = r'[ー\p{Katakana}\p{Block: Katakana_Phonetic_Extensions}]'
        return bool(re.fullmatch(pattern, char))
    
    
    @staticmethod
    def is_hiragana(char: str) -> bool:
        if len(char) != 1:
            raise ValueError("This function checks a single character only")
            
        # ひらがな拡張Aから
        pattern = r'[\p{Hiragana}\U0001B11F\U0001B120\U0001B121\U0001B122]'
        return bool(re.fullmatch(pattern, char))
    
    
    @staticmethod
    def is_only_katakana(text: str) -> bool:
        return bool(re.fullmatch(r'[ー\p{Katakana}\p{Block: Katakana_Phonetic_Extensions}]+', text))
    
    
    @staticmethod
    def is_only_hiragana(text: str) -> bool:
        return bool(re.fullmatch(r'[\p{Hiragana}]+', text))
    
    
    @staticmethod
    def is_only_kana(text: str) -> bool:
        return bool(re.fullmatch(r'[ー\p{Hiragana}\p{Katakana}\p{Block: Kana_Extended_A}\p{Block: Kana_Extended_B}\p{Block: Kana_Supplement}\p{Block: Katakana_Phonetic_Extensions}]+', text))
    
    
    @staticmethod
    def is_not_japanese(text: str) -> bool:
        """Returns True if the string contains NO Japanese characters at all."""
        return bool(KanjiUtils.IS_NOT_JAPANESE_PATTERN.fullmatch(text))
    
    
    @staticmethod
    def clean_reading(reading: str) -> str:
        return re.sub(r'[^ー\p{Hiragana}\p{Katakana}\p{Block: Kana_Extended_A}\p{Block: Kana_Extended_B}\p{Block: Kana_Supplement}\p{Block: Katakana_Phonetic_Extensions}]', "", reading)
    
    
    @staticmethod
    def clean_headword(head_word: str) -> str:
        return re.sub(r'[^・\p{Unified_Ideograph}ー\p{Hiragana}\p{Katakana}\p{Block: Kana_Extended_A}\p{Block: Kana_Extended_B}\p{Block: Kana_Supplement}\p{Block: Katakana_Phonetic_Extensions}]', "", head_word)
    
    
    """
    Matches a list of kanji and kana keys to each other.
    E.g ['かなしべ', 'かなしび', 'かなしぶ','哀しび', '哀しぶ', '悲しぶ','哀しべ']　ー＞
    Result:
    ('哀しべ', 'かなしべ')
    ('哀しび', 'かなしび')
    ('哀しぶ', 'かなしぶ')
    ('悲しぶ', 'かなしぶ')
    (None, 'かなしべ')
    (None, 'かなしび')
    (None, 'かなしぶ')
    """
    @staticmethod
    def match_kana_with_kanji(entries: List[str], recursion_level: int = 0) -> List[Tuple[Optional[str], Optional[str]]]:
        # Returns: List of DicEntry objects with paired kanji and kana matches
            
        # Separate entries into kana and kanji
        kana_entries = []
        kanji_entries = []
        foreign_entries = []
        
        for entry in entries:
            # Check if the entry contains kanji characters
            if any(KanjiUtils.is_kanji(c) for c in entry):
                kanji_entries.append(entry)
            elif KanjiUtils.is_only_kana(entry):
                kana_entries.append(entry)
            else:
                foreign_entries.append(entry)
                
        results = [(None, foreign_entry) for foreign_entry in foreign_entries]
                
        # Check for single kana entry with one or multiple kanji entries
        # Simply pair the single kana entry with all kanji entries
        if len(kana_entries) == 1 and len(kanji_entries) >= 1:
            results.extend([(kanji, kana_entries[0]) for kanji in kanji_entries])
            return results
        
        # Check for kana entries ending with るる and kanji entries ending with るる
        ruru_kana = [kana for kana in kana_entries if kana.endswith("るる")]
        if ruru_kana:
            ruru_kanji = [kanji for kanji in kanji_entries if kanji.endswith("るる")]
            if ruru_kanji:
                # Create pairs between るる kana and るる kanji
                matches = []
                for kana in ruru_kana:
                    for kanji in ruru_kanji:
                        matches.append((kanji, kana))
                
                # Remove matched entries to prevent duplicate processing
                remaining_kana = [k for k in kana_entries if k not in ruru_kana]
                remaining_kanji = [k for k in kanji_entries if k not in ruru_kanji]
                
                # If we have remaining entries, process them with the regular algorithm
                if remaining_kana or remaining_kanji:
                    remaining_entries = remaining_kana + remaining_kanji
                    additional_matches = KanjiUtils.match_kana_with_kanji(remaining_entries, recursion_level)
                    matches.extend(additional_matches)
                    
                return matches
        
        # Group entries by their non-kanji parts or patterns
        kanji_groups = {}
        
        for kanji in kanji_entries:
            # Extract the non-kanji part
            non_kanji_part = ''.join(char for char in kanji if not KanjiUtils.is_kanji(char))
            
            # If there's no non-kanji part, use the entire string as a key
            key = non_kanji_part if non_kanji_part else kanji
            
            if key not in kanji_groups:
                kanji_groups[key] = []
            kanji_groups[key].append(kanji)
        
        # Create mappings for results
        matched_kana = set()
        matched_kanji = set()
        
        # First pass: match kanji entries with exact non-kanji part matches
        for key, kanji_list in kanji_groups.items():
            if key in kana_entries:
                # Found an exact match
                for kanji in kanji_list:
                    results.append((kanji, key))
                    matched_kanji.add(kanji)
                matched_kana.add(key)
        
        # Second pass: match entries with similar endings (conjugation forms)
        for kana in kana_entries:
            if kana in matched_kana:
                continue
                
            best_kanji_matches = []
            best_match_length = 0
            
            for key, kanji_list in kanji_groups.items():
                # Skip empty non-kanji parts
                if not key:
                    continue
                    
                # Find the longest common ending
                common_length = KanjiUtils.longest_common_suffix(kana, key)
                
                # If we have a substantial match and it's better than previous matches
                if common_length >= 1 and common_length > best_match_length:
                    best_match_length = common_length
                    best_kanji_matches = []
                    for kanji in kanji_list:
                        if kanji not in matched_kanji:
                            best_kanji_matches.append(kanji)
                elif common_length == best_match_length and common_length >= 1:
                    for kanji in kanji_list:
                        if kanji not in matched_kanji:
                            best_kanji_matches.append(kanji)
            
            # If we found matches, create entries
            if best_kanji_matches:
                for kanji in best_kanji_matches:
                    results.append((kanji, kana))
                    matched_kanji.add(kanji)
                matched_kana.add(kana)
                
        # New pass: match entries with similar prefixes
        for kana in kana_entries:
            if kana in matched_kana:
                continue
                
            best_kanji_matches = []
            best_match_length = 0
            
            for key, kanji_list in kanji_groups.items():
                # Skip empty non-kanji parts
                if not key:
                    continue
                    
                # Find the longest common prefix
                common_length = KanjiUtils.longest_common_prefix(kana, key)
                
                # If we have a substantial match and it's better than previous matches
                if common_length >= 3 and common_length > best_match_length:
                    best_match_length = common_length
                    best_kanji_matches = []
                    for kanji in kanji_list:
                        if kanji not in matched_kanji:
                            best_kanji_matches.append(kanji)
                elif common_length == best_match_length and common_length >= 3:
                    for kanji in kanji_list:
                        if kanji not in matched_kanji:
                            best_kanji_matches.append(kanji)
            
            # If we found matches, create entries
            if best_kanji_matches:
                for kanji in best_kanji_matches:
                    results.append((kanji, kana))
                    matched_kanji.add(kanji)
                matched_kana.add(kana)
        
        # Third pass: handle kanji with no non-kanji parts (e.g., "三台" for "さんたい")
        for kana in kana_entries:
            if kana in matched_kana:
                continue
                
            # Look for kanji entries with no non-kanji part
            for kanji in kanji_entries:
                if kanji in matched_kanji:
                    continue
                    
                # Check if this is a kanji with no non-kanji part
                if KanjiUtils.is_kanji(kanji[-1]):
                    # Simplified check: if lengths are compatible
                    if KanjiUtils.is_plausible_reading(kana, kanji):
                        results.append((kanji, kana))
                        matched_kanji.add(kanji)
                        matched_kana.add(kana)
        
        # Final pass: look for any pattern matches for remaining entries
        remaining_kanji = [k for k in kanji_entries if k not in matched_kanji]
        remaining_kana = [k for k in kana_entries if k not in matched_kana]
        remaining_entries = remaining_kanji + kana_entries
        
        # If we have remaining entries and haven't exceeded recursion limit
        if remaining_entries and recursion_level < 8:
            # Get additional matches through recursion
            additional_matches = KanjiUtils.match_kana_with_kanji(remaining_entries, recursion_level + 1)
            results.extend(additional_matches)
        else:
            # Add unmatched entries if we've reached recursion limit
            for kana in remaining_kana:
                results.append((None, kana))
            
            for kanji in remaining_kanji:
                results.append((kanji, None))
        
        return results

    # find the length of the longest common suffix between two strings
    @staticmethod
    def longest_common_suffix(str1: str, str2: str) -> int:
        common_length = 0
        for i in range(1, min(len(str1), len(str2)) + 1):
            if str1[-i:] == str2[-i:]:
                common_length = i
            else:
                break
        return common_length
    
    @staticmethod
    def longest_common_prefix(str1: str, str2: str) -> int:
        common_length = 0
        for i in range(min(len(str1), len(str2))):
            if str1[i] == str2[i]:
                common_length += 1
            else:
                break
        return common_length

    #extract kanji part of sentence
    @staticmethod
    def extract_kanji_stem(kanji_entry: str) -> str:
        return ''.join(char for char in kanji_entry if KanjiUtils.is_kanji(char))

    # check if a kana string could be a reading for a kanji (not very good method ngl but it doesnt matter)
    @staticmethod
    def is_plausible_reading(kana: str, kanji: str) -> bool:
        kanji_chars = sum(1 for char in kanji if KanjiUtils.is_kanji(char))
        return len(kana) >= kanji_chars and len(kana) <= kanji_chars * 5
    
    
def main():
    # Tests
    entries = ['かなしば', 'かなしび', 'かなしびよ', 'かなしぶ', 'かなしぶる', 'かなしぶれ', 'かなしべ', '哀しば', '哀しびよ', '哀しび', '哀しぶる', '哀しぶれ', '哀しぶ', '悲しぶ', '愛しぶ', '哀しべ']
    entries = ['ぬかづきむし', '額突き虫']
    entries = ['スティック糊', 'スティックノリ', 'スティックノリ']

    result = KanjiUtils.match_kana_with_kanji(entries)

    for pair in result:
        print(pair)
        

if __name__ == "__main__":
    main()