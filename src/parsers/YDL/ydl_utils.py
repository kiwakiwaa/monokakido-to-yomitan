from utils import KanjiUtils

class YDLUtils:
    
    @staticmethod
    def extract_headword(soup):
        headword = ""
        
        head_element = soup.find("管理データ")
        if head_element:
            # Get all text within 管理データ, then remove text from child elements
            headword = head_element.text
            for child in head_element.find_all():
                headword = headword.replace(child.text, "")
            headword = headword.strip()
            
        if not KanjiUtils.clean_headword(headword).strip():
            display_name = soup.find("項目表示")
            if display_name:
                headword = display_name.text.strip()
            
        return KanjiUtils.clean_headword(headword) if headword else ""