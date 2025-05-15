import os
import shutil
from datetime import datetime
from PIL import Image
import piexif

# File extensions to process
IMAGE_EXTENSIONS = ('jpg', 'jpeg', 'png', 'heic')
VIDEO_EXTENSIONS = ('mp4', 'mov', 'avi', 'mkv')

def get_image_date_taken(file_path):
    try:
        image = Image.open(file_path)
        exif_data = image.info.get('exif')
        if exif_data:
            exif_dict = piexif.load(exif_data)
            date_taken = exif_dict.get('Exif', {}).get(piexif.ExifIFD.DateTimeOriginal)
            if date_taken:
                date_taken_str = date_taken.decode('utf-8')
                date_taken_obj = datetime.strptime(date_taken_str, "%Y:%m:%d %H:%M:%S")
                return date_taken_obj
    except Exception as e:
        print(f"Could not extract EXIF date for {file_path}: {e}")
    
    # If EXIF data is not found, fall back to last modified time
    return get_file_modified_date(file_path)

def get_video_date_taken(file_path):
    # For videos, use last modified time
    return get_file_modified_date(file_path)

def get_file_modified_date(file_path):
    try:
        last_modified_time = os.path.getmtime(file_path)
        date_taken = datetime.fromtimestamp(last_modified_time)
        return date_taken
    except Exception as e:
        print(f"Could not get last modified date for {file_path}: {e}")
    return None

def organize_by_date(src_dir, recursive=False):
    def process_directory(directory):
        for entry in os.scandir(directory):
            if entry.is_file():
                file_path = entry.path
                date_taken = None
                media_type = None

                if entry.name.lower().endswith(IMAGE_EXTENSIONS):
                    date_taken = get_image_date_taken(file_path)
                    media_type = "Images"
                elif entry.name.lower().endswith(VIDEO_EXTENSIONS):
                    date_taken = get_video_date_taken(file_path)
                    media_type = "Videos"

                if date_taken:
                    year = date_taken.strftime("%Y")
                    month = date_taken.strftime("%B")

                    # Create directory structure: Year > Month > Media Type
                    year_dir = os.path.join(src_dir, year)
                    month_dir = os.path.join(year_dir, month)
                    media_dir = os.path.join(month_dir, media_type)

                    if not os.path.exists(media_dir):
                        os.makedirs(media_dir)

                    dest_path = os.path.join(media_dir, entry.name)
                    # Check if destination file already exists
                    if os.path.exists(dest_path):
                        base_name, extension = os.path.splitext(entry.name)
                        counter = 1
                        while os.path.exists(dest_path):
                            new_name = f"{base_name}_{counter}{extension}"
                            dest_path = os.path.join(media_dir, new_name)
                            counter += 1
                    
                    shutil.move(file_path, dest_path)
                    print(f'Moved {entry.name} to {os.path.relpath(dest_path, src_dir)}')
                else:
                    print(f"Date could not be determined for {entry.name}, skipping...")
            elif entry.is_dir() and recursive:
                # Skip directories that were created by this script
                if not (entry.name.isdigit() and len(entry.name) == 4):  # Skip year folders
                    process_directory(entry.path)

    process_directory(src_dir)

if __name__ == "__main__":
    source_directory = input("Directory path: ").strip()
    recursive = input("Apply recursively? (y/n): ").lower() == 'y'

    if not os.path.exists(source_directory):
        print("Source directory does not exist. Please enter a valid path.")
    else:
        print(f"Starting to organize files in {source_directory}")
        print(f"Recursive mode: {'Enabled' if recursive else 'Disabled'}")
        organize_by_date(source_directory, recursive)
        print("Sorting complete.")
