import json
import os
import zipfile
import shutil
from tqdm import tqdm

class DicEntry:
    def __init__(self, word, reading, info_tag="", pos_tag="", search_rank=0, definition=None):
        self.word = word
        self.reading = reading
        self.info_tag = info_tag
        self.pos_tag = pos_tag
        self.search_rank = search_rank
        self.content = []
        self.structured_content = False
        if definition:
            self.set_simple_content(definition)

    def to_list(self):
        if self.structured_content:
            content = [{"type": "structured-content", "content": self.content}]
        else:
            content = self.content
        return [
            self.word,
            self.reading,
            self.info_tag,
            self.pos_tag,
            self.search_rank,
            content,
            0,
            ""
        ]
        
    def print_content(self):
        print(self.content)

    def add_element(self, element):
        self.validate_element(element)
        self.content.append(element)
        self.structured_content = True

    def set_simple_content(self, definition):
        if isinstance(definition, str):
            self.content = [definition]
        elif isinstance(definition, list):
            self.content = definition
        else:
            raise ValueError("Definition must be a string or a list of strings")
        self.structured_content = False

    def set_link_content(self, definition, link):
        self.content = [
            create_html_element("ul", [
                create_html_element("li", definition)
            ]),
            create_html_element("ul", [
                create_html_element("li", [create_html_element("a", link, href=link)])
            ], style={"listStyleType": "\"⧉\""})
        ]
        self.structured_content = True

    def validate_element(self, element):
        allowed_elements = ["br", "ruby", "rt", "rp", "table", "thead", "tbody", "tfoot", "tr", "td", "th", "span", "div", "ol", "ul", "li", "img", "a"]
        allowed_href_elements = ["a"]

        if element["tag"] not in allowed_elements:
            raise ValueError(f"Unsupported HTML element: {element['tag']}")

        if "href" in element and element["tag"] not in allowed_href_elements:
            raise ValueError(f"The 'href' attribute is not allowed in the '{element['tag']}' element, only <a>.")

        if "content" in element:
            if isinstance(element["content"], list):
                for child_element in element["content"]:
                    self.validate_element(child_element)
            elif not isinstance(element["content"], str):
                raise ValueError("Content must be a string or a list of elements")

class Dictionary:
    def __init__(self, dictionary_name):
        self.dictionary_name = dictionary_name
        self.entries = []

    def add_entry(self, entry):
        self.entries.append(entry)

    def export(self, output_path=None):
        folder_name = self.dictionary_name
        
        if output_path:
            folder_name = os.path.join(output_path, folder_name)
        
        # Remove the existing folder if it already exists
        if os.path.exists(folder_name):
            shutil.rmtree(folder_name)
        
        os.makedirs(folder_name, exist_ok=True)

        # Save index.json
        index_json = {
            "title": self.dictionary_name,
            "format": 3,
            "revision": "1"
        }
        index_file = os.path.join(folder_name, "index.json")
        with open(index_file, 'w', encoding='utf-8') as out_file:
            json.dump(index_json, out_file, ensure_ascii=False)

        file_counter = 1
        entry_counter = 0
        dictionary = []
        entry_id = 0
        
        # Create a progress bar for processing entries
        total_entries = len(self.entries)
        bar_format = "「{desc}: {bar:30}」{percentage:3.0f}% | {n_fmt}/{total_fmt} {unit}"
        pbar = tqdm(total=total_entries, desc="辞書をエクスポート中", bar_format=bar_format)

        for entry in self.entries:
            entry_list = entry.to_list()
            entry_list[6] = entry_id
            dictionary.append(entry_list)
            entry_counter += 1
            entry_id += 1
            
            # Update the progress bar
            pbar.update(1)

            if entry_counter >= 10000:
                output_file = os.path.join(folder_name, f"term_bank_{file_counter}.json")
                with open(output_file, 'w', encoding='utf-8') as out_file:
                    json.dump(dictionary, out_file, ensure_ascii=False)
                dictionary = []
                file_counter += 1
                entry_counter = 0
                
                # Update description to show current file
                pbar.set_description(f"辞書をエクスポート中 - ファイル {file_counter-1} 完了")

        if dictionary:
            output_file = os.path.join(folder_name, f"term_bank_{file_counter}.json")
            with open(output_file, 'w', encoding='utf-8') as out_file:
                json.dump(dictionary, out_file, ensure_ascii=False)
                
        # Close the progress bar
        pbar.close()

    def zip(self):
        zip_file_name = f"{self.dictionary_name}.zip"
        
        if os.path.exists(zip_file_name):
            os.remove(zip_file_name)
        
        with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(self.dictionary_name):
                for file in files:
                    file_path = os.path.join(root, file)
                    zipf.write(file_path, os.path.relpath(file_path, self.dictionary_name))

def create_html_element(tag, content=None, id=None, title=None, href=None, style=None, data=None):
    element = {"tag": tag}
    if tag != "br":
        if isinstance(content, str):
            element["content"] = content
        else:
            element["content"] = content
    if id:
        element["id"] = id
    if title:
        element["title"] = title    
    if href:
        element["href"] = href
    if style:
        element["style"] = style
    if data:
        element["data"] = data
    return element

if __name__ == "__main__":
    dictionary = Dictionary("Example_Dictionary")

    entry = DicEntry("食べる", "たべる", tag="v5r")

    definition_element = create_html_element("ul", [
        create_html_element("li", "To eat")
    ])
    link_element = create_html_element("ul", [
        create_html_element("li", [
            create_html_element("a", "View on Jisho", href="https://jisho.org/word/食べる")
        ])
    ], style={"listStyleType": "\"⧉\""})

    entry.add_element(definition_element)
    entry.add_element(link_element)

    dictionary.add_entry(entry)

    dictionary.export()
    dictionary.zip()