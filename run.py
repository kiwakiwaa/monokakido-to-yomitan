#.
import os
import sys
import re
from bs4 import BeautifulSoup

def improve_xml_structure(input_file, output_file=None):
    """
    Improves structure for XML/HTML pages, particularly for lists of Japanese grammar terms.
    """
    # Determine output file name if not provided
    if not output_file:
        file_name, file_ext = os.path.splitext(input_file)
        output_file = f"{file_name}_improved{file_ext}"
    
    # Read the input file
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading file {input_file}: {str(e)}")
        return False
    
    # Parse with BeautifulSoup
    soup = BeautifulSoup(content, 'html.parser')
    
    # Find and process the part of speech list (品詞 section)
    hinshi_sections = soup.find_all(string=lambda text: text and "品詞" in text)
    
    for hinshi_section in hinshi_sections:
        parent = hinshi_section.parent
        
        # Look for the list of grammatical terms that typically follows
        next_p = parent.find_next('p', class_='例')
        
        if next_p:
            # Process the content to improve structure
            for ws_elem in next_p.find_all(attrs={"data-sc-ws": True}):
                # Add line break before each grammar term tag
                if ws_elem.previous_sibling and ws_elem.previous_sibling.name != 'br':
                    br = soup.new_tag('br')
                    ws_elem.insert_before(br)
            
            # Add spacing after definitions
            for span in next_p.find_all('span', string=lambda s: s and "……" in s):
                if span.next_sibling and not isinstance(span.next_sibling, str):
                    continue
                span.insert_after(soup.new_tag('br'))
    
    # Save the modified content
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"Successfully wrote improved structure to {output_file}")
        return True
    except Exception as e:
        print(f"Error writing to file {output_file}: {str(e)}")
        return False

def process_directory(directory_path, output_directory=None):
    """
    Process all HTML/XML files in a directory
    """
    if not output_directory:
        output_directory = directory_path + "_improved"
    
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    file_count = 0
    success_count = 0
    
    for filename in os.listdir(directory_path):
        if filename.lower().endswith(('.html', '.xml')):
            file_count += 1
            input_path = os.path.join(directory_path, filename)
            output_path = os.path.join(output_directory, filename)
            
            print(f"Processing {filename}...")
            if improve_xml_structure(input_path, output_path):
                success_count += 1
    
    print(f"Processed {file_count} files, {success_count} successful.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python improve_xml_structure.py <input_file_or_directory> [output_file_or_directory]")
        sys.exit(1)
    
    input_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else None
    
    if os.path.isdir(input_path):
        process_directory(input_path, output_path)
    else:
        improve_xml_structure(input_path, output_path)
