import os
import hashlib
from pathlib import Path

def remove_duplicates(directory, recursive=False):
    unique_files = dict()
    
    def process_directory(dir_path):
        for item in os.scandir(dir_path):
            if item.is_file():
                try:
                    file_hash = hashlib.md5(open(item.path, 'rb').read()).hexdigest()
                except (FileNotFoundError, PermissionError) as e:
                    print(f"Failed to open {item.path}: {e}")
                    continue

                if file_hash not in unique_files:
                    unique_files[file_hash] = item.path
                else:
                    os.remove(item.path)
                    print(f"{item.path} has been deleted")
            elif item.is_dir() and recursive:
                process_directory(item.path)
    
    process_directory(directory)

def main():
    directory = input("Directory path: ")
    recursive = input("Apply recursively? (y/n): ").lower() == 'y'
    
    if os.path.exists(directory):
        remove_duplicates(directory, recursive)
    else:
        print("Directory does not exist!")

if __name__ == "__main__":
    main()
