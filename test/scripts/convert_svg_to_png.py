import os
import subprocess
import argparse
from pathlib import Path

def convert_svg_to_png(svg_file, output_dir=None, dpi=96):
    """
    Convert an SVG file to PNG using Inkscape
    
    Args:
        svg_file (str): Path to the SVG file
        output_dir (str, optional): Directory to save the PNG file. If None, use the same directory as the SVG.
        dpi (int, optional): Resolution of the output PNG in dots per inch. Default is 96.
    
    Returns:
        str: Path to the output PNG file, or None if conversion failed
    """
    svg_path = Path(svg_file)
    
    # Create output path
    if output_dir:
        output_path = Path(output_dir) / f"{svg_path.stem}.png"
    else:
        output_path = svg_path.with_suffix('.png')
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Build the Inkscape command
    cmd = [
        'inkscape',
        '--export-filename', str(output_path),
        '--export-dpi', str(dpi),
        str(svg_path)
    ]
    
    try:
        # Run Inkscape to convert the file
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode == 0:
            print(f"Converted: {svg_file} -> {output_path}")
            return str(output_path)
        else:
            print(f"Error converting {svg_file}:")
            print(result.stderr)
            return None
            
    except Exception as e:
        print(f"Exception while converting {svg_file}: {str(e)}")
        return None

def batch_convert_svgs(input_dir, output_dir=None, dpi=96):
    """
    Convert all SVG files in a directory to PNG using Inkscape
    
    Args:
        input_dir (str): Directory containing SVG files
        output_dir (str, optional): Directory to save the PNG files. If None, use the same directory as the SVGs.
        dpi (int, optional): Resolution of the output PNGs. Default is 96.
    
    Returns:
        list: List of paths to successfully converted PNG files
    """
    input_path = Path(input_dir)
    
    # Find all SVG files
    svg_files = list(input_path.glob('*.svg'))
    
    if not svg_files:
        print(f"No SVG files found in {input_dir}")
        return []
    
    print(f"Found {len(svg_files)} SVG files in {input_dir}")
    
    # Convert each SVG file
    converted_files = []
    for svg_file in svg_files:
        png_file = convert_svg_to_png(svg_file, output_dir, dpi)
        if png_file:
            converted_files.append(png_file)
    
    print(f"Successfully converted {len(converted_files)} of {len(svg_files)} files")
    return converted_files

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Convert SVG files to PNG using Inkscape')
    parser.add_argument('input_dir', help='Directory containing SVG files')
    parser.add_argument('-o', '--output-dir', help='Directory to save PNG files (default: same as input)')
    parser.add_argument('-d', '--dpi', type=int, default=96, help='Output resolution in DPI (default: 96)')
    
    args = parser.parse_args()
    
    # Check if Inkscape is available
    try:
        subprocess.run(['inkscape', '--version'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    except (subprocess.SubprocessError, FileNotFoundError):
        print("Error: Inkscape is not installed or not available in PATH.")
        print("Please install Inkscape and ensure it's accessible from the command line.")
        return
    
    # Convert SVG files
    batch_convert_svgs(args.input_dir, args.output_dir, args.dpi)

if __name__ == '__main__':
    main()