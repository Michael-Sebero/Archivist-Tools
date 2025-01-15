import os
import shutil

def organize_files(dir_to_sort, recursive=False):
    # Define directories
    image_dir = os.path.join(dir_to_sort, 'Images')
    video_dir = os.path.join(dir_to_sort, 'Videos')
    audio_dir = os.path.join(dir_to_sort, 'Audio')
    archive_dir = os.path.join(dir_to_sort, 'Archives')
    document_dir = os.path.join(dir_to_sort, 'Documents')

    # List of file extensions for each category
    image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.heic', '.webp']
    video_extensions = ['.webm', '.mp4', '.mov', '.flv', '.avi', '.mkv', '.wmv', '.rmvb', '.3gp', '.m4v']
    audio_extensions = ['.m4a', '.mp3', '.ogg', '.opus', '.flac', '.alac', '.wav', '.amr', '.aac', '.m4b', '.m4p']
    archive_extensions = ['.zip', '.tar', '.tar.gz', '.rar','.tar', '.gz', '.7z']
    document_extensions = ['.txt', '.doc', '.docx', '.pdf', '.ppt', '.pptx', '.xls', '.xlsx','.odt']

    # Initialize counters
    counts = {'image': 0, 'video': 0, 'audio': 0, 'archive': 0, 'document': 0}

    def process_directory(directory):
        for entry in os.scandir(directory):
            if entry.is_file():
                _, ext = os.path.splitext(entry.name)
                ext = ext.lower()

                target_dir = None
                if ext in image_extensions:
                    target_dir = image_dir
                    counts['image'] += 1
                elif ext in video_extensions:
                    target_dir = video_dir
                    counts['video'] += 1
                elif ext in audio_extensions:
                    target_dir = audio_dir
                    counts['audio'] += 1
                elif ext in archive_extensions:
                    target_dir = archive_dir
                    counts['archive'] += 1
                elif ext in document_extensions:
                    target_dir = document_dir
                    counts['document'] += 1

                if target_dir:
                    if not os.path.exists(target_dir):
                        os.makedirs(target_dir)
                    shutil.move(entry.path, os.path.join(target_dir, entry.name))
            elif entry.is_dir() and recursive and entry.name not in ['Images', 'Videos', 'Audio', 'Archives', 'Documents']:
                process_directory(entry.path)

    process_directory(dir_to_sort)

    # Print summary
    for category, count in counts.items():
        if count > 0:
            print(f"Moved {count} {category} files")

if __name__ == "__main__":
    dir_to_sort = input("Directory path: ")
    recursive = input("Apply recursively? (y/n): ").lower() == 'y'

    if not os.path.isdir(dir_to_sort):
        print("Error: Invalid directory path")
    else:
        organize_files(dir_to_sort, recursive)
        print("\nOrganization complete!")
