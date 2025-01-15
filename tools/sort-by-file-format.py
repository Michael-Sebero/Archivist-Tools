import os
import shutil

# Ask the user for the directory to sort
dir_to_sort = input("Enter the directory: ")

# Get list of files in the directory
files = os.listdir(dir_to_sort)

# Create destination directories for each file extension
destination_directories = {}

# Initialize counters
file_count = 0

# Iterate over each file
for file in files:
    # Get the file extension
    _, ext = os.path.splitext(file)
    ext = ext.lower()  # Convert to lowercase

    # Create destination directory if it doesn't exist
    destination_subdir = os.path.join(dir_to_sort, ext[1:])
    destination_directories[ext] = destination_subdir

# Create destination directories if they don't exist
for destination_subdir in destination_directories.values():
    os.makedirs(destination_subdir, exist_ok=True)

# Move files to the destination directories based on their extensions
for file in files:
    _, ext = os.path.splitext(file)
    ext = ext.lower()
    shutil.move(os.path.join(dir_to_sort, file), os.path.join(destination_directories[ext], file))
    file_count += 1

print(f"{file_count} files moved to {dir_to_sort} in separate folders based on their file formats.")
