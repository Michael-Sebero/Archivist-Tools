import os

def delete_files(directory, keyword, recursive=False):
    deleted_files = []
    
    def process_directory(dir_path):
        for item in os.scandir(dir_path):
            if item.is_file() and keyword.lower() in item.name.lower():
                try:
                    os.remove(item.path)
                    deleted_files.append(item.path)
                except Exception as e:
                    print(f"Error deleting {item.path}: {e}")
            elif item.is_dir() and recursive:
                process_directory(item.path)
    
    process_directory(directory)
    
    if deleted_files:
        print("\nSummary of deleted files:")
        for file_path in deleted_files:
            print(f"- {file_path}")
    else:
        print("No files were deleted.")

def main():
    directory = input("Directory path: ")
    keyword = input("Enter the keyword to delete files containing it: ")
    recursive = input("Apply recursively? (y/n): ").lower() == 'y'
    
    if os.path.exists(directory):
        delete_files(directory, keyword, recursive)
    else:
        print("Directory does not exist!")

if __name__ == "__main__":
    main()
