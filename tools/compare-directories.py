import os
import hashlib
import pathlib

def calculate_hash(file_path):
    hash_algo = hashlib.md5()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            hash_algo.update(chunk)
    return hash_algo.hexdigest()

def compare_directories(dir1, dir2, log_file):
    items_in_dir1 = {}
    items_in_dir2 = {}
    
    # Walk through the first directory
    for root, dirs, files in os.walk(dir1):
        for name in dirs + files:
            item_path = os.path.join(root, name)
            relative_path = os.path.relpath(item_path, dir1)
            if os.path.isfile(item_path):
                items_in_dir1[relative_path] = calculate_hash(item_path)
            else:
                items_in_dir1[relative_path] = "DIR"
    
    # Walk through the second directory
    for root, dirs, files in os.walk(dir2):
        for name in dirs + files:
            item_path = os.path.join(root, name)
            relative_path = os.path.relpath(item_path, dir2)
            if os.path.isfile(item_path):
                items_in_dir2[relative_path] = calculate_hash(item_path)
            else:
                items_in_dir2[relative_path] = "DIR"
    
    differences = []
    unique_to_dir1 = []
    unique_to_dir2 = []
    identical = []
    
    # Identify differences, unique, and identical items
    all_items = set(items_in_dir1.keys()).union(items_in_dir2.keys())
    for item in all_items:
        if item in items_in_dir1 and item in items_in_dir2:
            if items_in_dir1[item] != items_in_dir2[item]:
                differences.append(item)
            else:
                identical.append(item)
        elif item in items_in_dir1:
            unique_to_dir1.append(item)
        elif item in items_in_dir2:
            unique_to_dir2.append(item)
    
    # Write to the log file
    with open(log_file, 'w') as log:
        # Function to write sections with clustering
        def write_section(title, items):
            log.write("=======================================\n")
            log.write(f"{title}:\n")
            log.write("=======================================\n\n")
            previous_dir = None
            for item in sorted(items):
                current_dir = os.path.dirname(item)
                if previous_dir is not None and current_dir != previous_dir:
                    log.write("\n")  # Add a small space between different directories
                log.write(f"{item}\n")
                previous_dir = current_dir
            log.write("\n")

        # Write the sections
        write_section("Differences between directories", differences)
        write_section("Items only in directory 1", unique_to_dir1)
        write_section("Items only in directory 2", unique_to_dir2)
        write_section("Identical items in both directories", identical)

if __name__ == "__main__":
    dir1 = input("Enter the path to the first directory: ")
    dir2 = input("Enter the path to the second directory: ")
    
    desktop = pathlib.Path.home() / "Desktop"
    log_file = desktop / "comparison_log.txt"
    
    compare_directories(dir1, dir2, log_file)
    
    print(f"Comparison complete. Log saved to {log_file}")
