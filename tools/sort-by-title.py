import os
import shutil
import re
from collections import defaultdict

def extract_title(filename):
    """
    Extract the primary title from a filename, handling more complex naming conventions.
    
    :param filename: Original filename
    :return: Extracted title
    """
    # Remove file extension
    supported_extensions = [
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', 
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'
    ]
    
    # Remove extension
    for ext in supported_extensions:
        if filename.lower().endswith(ext):
            filename = filename[:-len(ext)]
            break
    
    # Extract name before any year or additional details
    # This regex looks for a name before any year in parentheses
    match = re.match(r'^(.*?)\s*\(', filename)
    if match:
        title = match.group(1).strip()
    else:
        # If no year in parentheses, take the first part of the filename
        title = filename.split('-')[0].strip()
    
    # Clean up the title (remove special characters)
    title = re.sub(r'[^\w\s-]', '', title).strip()
    
    return title

def organize_files_by_title(source_directory):
    """
    Organize image and video files into folders based on their titles.
    
    :param source_directory: Path to the directory containing files to organize
    """
    # Supported image and video file extensions
    supported_extensions = [
        # Images
        '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', 
        # Videos
        '.mp4', '.avi', '.mov', '.mkv', '.wmv', '.flv', '.webm'
    ]
    
    # Collect files by their base titles
    title_files = defaultdict(list)
    
    # First pass: collect files and their titles
    for filename in os.listdir(source_directory):
        # Check if the file has a supported extension
        if any(filename.lower().endswith(ext) for ext in supported_extensions):
            # Extract title
            title = extract_title(filename)
            
            # Add to the collection of files for this title
            title_files[title].append(filename)
    
    # Counters for tracking
    processed_files = 0
    created_folders = 0
    
    # Create Misc folder if needed
    misc_folder = os.path.join(source_directory, 'Misc')
    if not os.path.exists(misc_folder):
        os.makedirs(misc_folder)
    
    # Second pass: organize files
    for title, files in title_files.items():
        if len(files) > 1:
            # Multiple files with same title - create a folder for them
            target_folder = os.path.join(source_directory, title)
            
            # Create the folder if it doesn't exist
            if not os.path.exists(target_folder):
                os.makedirs(target_folder)
                created_folders += 1
            
            # Move files to the title folder
            for filename in files:
                source_path = os.path.join(source_directory, filename)
                destination_path = os.path.join(target_folder, filename)
                shutil.move(source_path, destination_path)
                processed_files += 1
        else:
            # Only one file with this title - move to Misc folder
            filename = files[0]
            source_path = os.path.join(source_directory, filename)
            destination_path = os.path.join(misc_folder, filename)
            shutil.move(source_path, destination_path)
    
    # Print summary of actions
    print(f"Organized {processed_files} files into {created_folders} titled folders.")
    print(f"Unique files moved to '{misc_folder}'.")

def main():
    # Prompt user for the source directory
    while True:
        source_dir = input("Enter the full path to the directory containing files to organize: ").strip()
        
        # Validate directory exists
        if os.path.isdir(source_dir):
            try:
                organize_files_by_title(source_dir)
                break
            except Exception as e:
                print(f"An error occurred: {e}")
        else:
            print("Invalid directory. Please enter a valid directory path.")

if __name__ == "__main__":
    main()
