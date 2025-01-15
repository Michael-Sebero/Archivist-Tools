import os

def rename_to_capitalize_first_letter(directory, recursive=False):
    def process_directory(dir_path):
        for entry in os.scandir(dir_path):
            if entry.is_dir() and recursive:
                # Process subdirectory before renaming it
                process_directory(entry.path)
                # Rename directory itself
                new_name = entry.name.capitalize()
                new_path = os.path.join(os.path.dirname(entry.path), new_name)
                os.rename(entry.path, new_path)
                print(f'Renamed directory {entry.path} to {new_path}')
            elif entry.is_file():
                # Rename files
                base_name, extension = os.path.splitext(entry.name)
                new_name = base_name.capitalize() + extension
                new_path = os.path.join(os.path.dirname(entry.path), new_name)
                os.rename(entry.path, new_path)
                print(f'Renamed file {entry.path} to {new_path}')

    process_directory(directory)

if __name__ == "__main__":
    directory = input("Directory path: ").strip()
    recursive = input("Apply recursively? (y/n): ").lower() == 'y'
    
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory.")
        exit(1)
    
    rename_to_capitalize_first_letter(directory, recursive)
    print(f"All files{' and directories' if recursive else ''} in {directory} have been renamed with first letter capitalized.")
