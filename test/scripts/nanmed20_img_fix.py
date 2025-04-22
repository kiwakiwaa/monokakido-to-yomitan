import os
import json
import re
import argparse

def read_images_from_folder(folder_path):
    # Reads all .png files from the specified folder and returns a dictionary of basename to filename
    images = {}
    for filename in os.listdir(folder_path):
        if filename.endswith('.png'):
            basename = os.path.splitext(filename)[0]
            images[basename] = filename
    return images

def process_html_content(html, images, folder_path):
    # Process the HTML content by replacing &<keyword>; with an <img> tag if the image exists
    pattern = r'&([a-zA-Z0-9_]+);'
    def replace_placeholder(match):
        keyword = match.group(1)
        if keyword in images:
            img_tag = f"<span><img src='/images/{images[keyword]}' alt='{keyword}' /></span>"
            return img_tag
        return match.group(0)
    return re.sub(pattern, replace_placeholder, html)

def process_json(json_data, images, folder_path):
    # Processes the entire JSON, replacing placeholders in HTML content
    processed_data = {}
    for keyword, html in json_data.items():
        processed_html = process_html_content(html, images, folder_path)
        processed_data[keyword] = processed_html
    return processed_data

def parse_args():
    parser = argparse.ArgumentParser(description='Process dictionary files for Yomitan conversion')
    parser.add_argument('--input-dir', '-i', type=str, help='Path to the folder containing the PNG images')
    parser.add_argument('--json-file', '-j', type=str, help='Path to the input JSON dictionary file')
    parser.add_argument('--output-file', '-o', type=str, help='Path to the output JSON file')
    return parser.parse_args()

def main():
    args = parse_args()
    
    folder_path = args.input_dir
    
    images = read_images_from_folder(folder_path)
    
    json_file = args.json_file
    with open(json_file, 'r', encoding='utf-8') as f:
        dictionary = json.load(f)
    
    processed_json = process_json(dictionary, images, folder_path)
    
    out_file = args.output_file
    with open(out_file, 'w', encoding='utf-8') as f:
        json.dump(processed_json, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully processed dictionary. Output saved to {out_file}")

if __name__ == "__main__":
    main()
