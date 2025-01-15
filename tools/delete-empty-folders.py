import os
import pathlib

def delete_empty_dirs(directory):
    # Walk through the directory tree
    for root, dirs, files in os.walk(directory, topdown=False):
        # Check if the directory is empty
        if not dirs and not files:
            # Remove the empty directory
            pathlib.Path(root).rmdir()
            print(f"Deleted empty directory: {root}")

# Ask the user to input the directory to clean up
directory_to_clean = input("Enter the directory: ")

# Call the function to delete empty directories
delete_empty_dirs(directory_to_clean)
