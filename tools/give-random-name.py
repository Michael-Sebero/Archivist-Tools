import os
import random
import string

def generate_random_string(length):
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

def rename_files_in_directory(directory_path, recursive=False):
    def process_directory(dir_path):
        for entry in os.scandir(dir_path):
            if entry.is_file():
                new_name = generate_random_string(8) + os.path.splitext(entry.name)[1]
                new_path = os.path.join(os.path.dirname(entry.path), new_name)
                os.rename(entry.path, new_path)
                print(f"Renamed: {entry.path} -> {new_path}")
            elif entry.is_dir() and recursive:
                process_directory(entry.path)
    
    if not os.path.exists(directory_path):
        print("Directory does not exist!")
        return
        
    process_directory(directory_path)
    print("Renaming complete!")

if __name__ == "__main__":
    directory_path = input("Directory path: ")
    recursive = input("Apply recursively? (y/n): ").lower() == 'y'
    
    rename_files_in_directory(directory_path, recursive)
