import os
import hashlib
import sys

def calculate_hash(file_path):
    with open(file_path, 'rb') as f:
        bytes = f.read()
        return hashlib.md5(bytes).hexdigest()

def change_hash(file_path):
    with open(file_path, 'ab') as f:
        f.write(b'\0')

def process_directory(directory_path, recursive=False):
    for item in os.scandir(directory_path):
        if item.is_file():
            old_hash = calculate_hash(item.path)
            change_hash(item.path)
            new_hash = calculate_hash(item.path)
            print(f'{item.path} - Old hash: {old_hash}, New hash: {new_hash}')
        elif item.is_dir() and recursive:
            process_directory(item.path, recursive)

def main():
    directory_path = input("Directory path: ")
    recursive = input("Apply recursively? (y/n): ").lower() == 'y'
    
    if os.path.exists(directory_path):
        process_directory(directory_path, recursive)
    else:
        print("Directory does not exist!")

if __name__ == '__main__':
    main()
