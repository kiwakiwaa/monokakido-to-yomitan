import os
import hashlib
import argparse

def hash_filename(filename, length=10):
    hash_obj = hashlib.md5(filename.encode())
    hash_hex = hash_obj.hexdigest()[:length]
    return hash_hex

def process_image_files(input_folder, output_folder=None):
    # If output folder is not specified, use the input folder
    if output_folder is None:
        output_folder = input_folder
    
    # Create output directory if it doesn't exist
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # Process all PNG and SVG files in a folder, hash filenames, and rename them
    image_file_map = {}
    
    # Get all PNG and SVG files in the input directory
    image_files = [f for f in os.listdir(input_folder) 
                  if f.lower().endswith(('.png', '.svg'))]
    
    for original_filename in image_files:
        base_name = os.path.splitext(original_filename)[0]
        file_ext = os.path.splitext(original_filename)[1].lower()  # Preserve extension
        hashed_name = hash_filename(base_name)
        new_filename = f"{hashed_name}{file_ext}"
        
        image_file_map[original_filename] = new_filename
        
        original_path = os.path.join(input_folder, original_filename)
        new_path = os.path.join(output_folder, new_filename)
        
        # Handle potential collision (extremely unlikely)
        counter = 1
        while os.path.exists(new_path):
            hashed_name = hash_filename(f"{base_name}_{counter}")
            new_filename = f"{hashed_name}{file_ext}"
            new_path = os.path.join(output_folder, new_filename)
            image_file_map[original_filename] = new_filename
            counter += 1
        
        # If input and output folders are different, copy the file instead of renaming
        if input_folder != output_folder:
            import shutil
            shutil.copy2(original_path, new_path)
            print(f"Copied: {original_filename} → {new_filename}")
        else:
            os.rename(original_path, new_path)
            print(f"Renamed: {original_filename} → {new_filename}")
    
    # Save the mapping dictionary
    map_path = os.path.join(output_folder, 'image_file_map.py')
    with open(map_path, 'w') as f:
        f.write("IMAGE_FILE_MAP = {\n")
        for original, hashed in image_file_map.items():
            f.write(f"    '{original}': '{hashed}',\n")
        f.write("}\n")
    
    return image_file_map, map_path

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Hash image filenames to avoid encoding issues')
    parser.add_argument('-i', '--input', required=True, help='Input directory containing image files')
    parser.add_argument('-o', '--output', help='Output directory for hashed files (defaults to input directory)')
    
    args = parser.parse_args()
    
    input_dir = args.input
    output_dir = args.output
    
    if not os.path.isdir(input_dir):
        print(f"Error: '{input_dir}' is not a valid directory")
        exit(1)
    
    try:
        image_map, map_path = process_image_files(input_dir, output_dir)
        print(f"Processed {len(image_map)} image files")
        print(f"Mapping dictionary saved to {map_path}")
    except Exception as e:
        print(f"Error processing files: {e}")
        exit(1)