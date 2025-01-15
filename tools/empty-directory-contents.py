import os
import shutil

# Get the directory from the user
source_dir = input("Enter the directory: ")

# Check if the directory exists
if not os.path.isdir(source_dir):
    print(f"The directory {source_dir} does not exist.")
else:
    # Walk through the source directory and its subdirectories
    for dirpath, dirnames, filenames in os.walk(source_dir, topdown=False):
        # For each file in the subdirectories
        for filename in filenames:
            # Construct full file path
            src_file = os.path.join(dirpath, filename)
            # Construct destination file path
            dest_file = os.path.join(source_dir, filename)
            # Move the file to the main directory
            shutil.move(src_file, dest_file)
            print(f"Moved {src_file} to {dest_file}")
        
        # Check if the subdirectory is empty after moving files
        if not os.listdir(dirpath):
            os.rmdir(dirpath)
            print(f"Deleted directory {dirpath}")
