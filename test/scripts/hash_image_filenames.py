import os
import hashlib

"""
Used this for SKOGO because the image file names were being weird
"""
def hash_filename(filename, length=10):
    hash_obj = hashlib.md5(filename.encode())
    hash_hex = hash_obj.hexdigest()[:length]
    return hash_hex

def process_png_files(folder_path):
    """Process all PNG files in a folder, hash filenames, and rename them"""
    image_file_map = {}
    
    png_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.png')]
    
    for original_filename in png_files:
        base_name = os.path.splitext(original_filename)[0]
        hashed_name = hash_filename(base_name)
        new_filename = f"{hashed_name}.png"
        
        image_file_map[original_filename] = new_filename
        
        original_path = os.path.join(folder_path, original_filename)
        new_path = os.path.join(folder_path, new_filename)
        
        # Handle potential collision (extremely unlikely)
        counter = 1
        while os.path.exists(new_path):
            hashed_name = hash_filename(f"{base_name}_{counter}")
            new_filename = f"{hashed_name}.png"
            new_path = os.path.join(folder_path, new_filename)
            image_file_map[original_filename] = new_filename
            counter += 1
            
        os.rename(original_path, new_path)
        print(f"Renamed: {original_filename} → {new_filename}")
    
    with open(os.path.join(folder_path, 'image_file_map.py'), 'w') as f:
        f.write("IMAGE_FILE_MAP = {\n")
        for original, hashed in image_file_map.items():
            f.write(f"    '{original}': '{hashed}',\n")
        f.write("}\n")
    
    return image_file_map

if __name__ == "__main__":
    folder_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "graphics")
    
    if os.path.isdir(folder_path):
        image_map = process_png_files(folder_path)
        print(f"Processed {len(image_map)} PNG files")
        print(f"Mapping dictionary saved to {os.path.join(folder_path, 'image_file_map.py')}")
    else:
        print(f"Error: '{folder_path}' is not a valid directory")