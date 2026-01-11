#!/usr/bin/env python3

import os
import sys
import hashlib
import shutil
import random
import string
import re
from pathlib import Path
from typing import List, Dict, Set, Optional, Callable, Tuple
from collections import defaultdict
from datetime import datetime
import subprocess

# Optional imports with graceful fallbacks
try:
    from PIL import Image
    import piexif
    IMAGING_AVAILABLE = True
except ImportError:
    IMAGING_AVAILABLE = False


# ============================================================================
# TERMINAL UI UTILITIES
# ============================================================================

def get_key():
    """Get single keypress from terminal"""
    import termios
    import tty
    
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(fd)
        ch = sys.stdin.read(1)
        
        # Handle escape sequences (arrow keys)
        if ch == '\x1b':
            ch2 = sys.stdin.read(1)
            if ch2 == '[':
                ch3 = sys.stdin.read(1)
                if ch3 == 'A':
                    return 'UP'
                elif ch3 == 'B':
                    return 'DOWN'
        elif ch in '\r\n':
            return 'ENTER'
        elif ch == '\x03':  # Ctrl+C
            return 'CTRL_C'
        
        return ch
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def clear():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')


# ============================================================================
# CORE UTILITIES
# ============================================================================

class Config:
    """Central configuration"""
    CHUNK_SIZE = 8192
    LOG_DIR = Path.home() / "Desktop"
    
    # File type definitions
    IMAGE_EXTS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.ico', '.heic', '.webp', '.tiff'}
    VIDEO_EXTS = {'.webm', '.mp4', '.mov', '.flv', '.avi', '.mkv', '.wmv', '.rmvb', '.3gp', '.m4v'}
    AUDIO_EXTS = {'.m4a', '.mp3', '.ogg', '.opus', '.flac', '.alac', '.wav', '.amr', '.aac', '.m4b', '.m4p'}
    DOCUMENT_EXTS = {'.txt', '.doc', '.docx', '.pdf', '.ppt', '.pptx', '.xls', '.xlsx', '.odt'}
    ARCHIVE_EXTS = {'.zip', '.tar', '.tar.gz', '.rar', '.gz', '.7z'}
    MEDIA_EXTS = IMAGE_EXTS | VIDEO_EXTS


class FileHash:
    """File hashing utilities"""
    
    @staticmethod
    def calculate(filepath: Path, algorithm: str = 'md5') -> str:
        """Calculate file hash using specified algorithm"""
        hash_obj = hashlib.new(algorithm)
        try:
            with open(filepath, 'rb') as f:
                while chunk := f.read(Config.CHUNK_SIZE):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except (FileNotFoundError, PermissionError) as e:
            raise IOError(f"Failed to hash {filepath}: {e}")
    
    @staticmethod
    def modify(filepath: Path) -> Tuple[str, str]:
        """Modify file to change its hash (appends null byte)"""
        old_hash = FileHash.calculate(filepath)
        with open(filepath, 'ab') as f:
            f.write(b'\0')
        new_hash = FileHash.calculate(filepath)
        return old_hash, new_hash


class PathUtils:
    """Path and filename utilities"""
    
    @staticmethod
    def get_valid_path(prompt: str = "Enter path: ", must_exist: bool = True) -> Optional[Path]:
        """Get and validate a path from user input"""
        while True:
            path_str = input(prompt).strip().strip("'\"")
            if not path_str:
                print("Error: Path cannot be empty")
                continue
            
            path = Path(os.path.expanduser(path_str)).resolve()
            
            if must_exist and not path.exists():
                print(f"Error: Path does not exist: {path}")
                continue
            
            return path
    
    @staticmethod
    def sanitize_filename(name: str, replacement: str = '_') -> str:
        """Remove invalid characters from filename"""
        return re.sub(r'[<>:"/\\|?*]', replacement, name).strip()
    
    @staticmethod
    def ensure_unique(filepath: Path) -> Path:
        """Ensure filepath is unique by adding counter if needed"""
        if not filepath.exists():
            return filepath
        
        stem = filepath.stem
        suffix = filepath.suffix
        parent = filepath.parent
        counter = 1
        
        while True:
            new_path = parent / f"{stem}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1


class UserInput:
    """User interaction utilities"""
    
    @staticmethod
    def yes_no(prompt: str, default: bool = False) -> bool:
        """Get yes/no response from user"""
        suffix = " [Y/n]: " if default else " [y/N]: "
        response = input(prompt + suffix).strip().lower()
        
        if not response:
            return default
        return response in {'y', 'yes'}


class FileScanner:
    """File system scanning utilities"""
    
    @staticmethod
    def scan(directory: Path, extensions: Set[str] = None, recursive: bool = False) -> List[Path]:
        """Scan directory for files with specified extensions"""
        files = []
        
        if recursive:
            for root, _, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = Path(root) / filename
                    if extensions is None or filepath.suffix.lower() in extensions:
                        files.append(filepath)
        else:
            for item in directory.iterdir():
                if item.is_file():
                    if extensions is None or item.suffix.lower() in extensions:
                        files.append(item)
        
        return sorted(files)


# ============================================================================
# FILE OPERATIONS
# ============================================================================

class HashOperations:
    """Hash-based file operations"""
    
    @staticmethod
    def change_hashes(directory: Path, recursive: bool = False):
        """Change file hashes by appending null bytes"""
        files = FileScanner.scan(directory, recursive=recursive)
        
        if not files:
            print("No files found")
            return
        
        print(f"Modifying {len(files)} files...\n")
        
        for filepath in files:
            try:
                old_hash, new_hash = FileHash.modify(filepath)
                print(f"{filepath.name}")
                print(f"  Old: {old_hash}")
                print(f"  New: {new_hash}\n")
            except Exception as e:
                print(f"Error: {filepath.name}: {e}\n")
        
        print("Complete!")
    
    @staticmethod
    def find_duplicates(directory: Path, recursive: bool = False) -> Dict[str, List[Path]]:
        """Find duplicate files by hash"""
        files = FileScanner.scan(directory, recursive=recursive)
        
        if not files:
            return {}
        
        print(f"Scanning {len(files)} files for duplicates...")
        hash_map = defaultdict(list)
        
        for i, filepath in enumerate(files, 1):
            try:
                file_hash = FileHash.calculate(filepath)
                hash_map[file_hash].append(filepath)
                print(f"\rProgress: {i}/{len(files)}", end='', flush=True)
            except IOError as e:
                print(f"\nError: {e}")
        
        print("\n")
        
        # Return only duplicates
        duplicates = {h: paths for h, paths in hash_map.items() if len(paths) > 1}
        return duplicates
    
    @staticmethod
    def remove_duplicates(directory: Path, recursive: bool = False):
        """Remove duplicate files, keeping first occurrence"""
        duplicates = HashOperations.find_duplicates(directory, recursive)
        
        if not duplicates:
            print("No duplicate files found")
            return
        
        total_dupes = sum(len(paths) - 1 for paths in duplicates.values())
        print(f"Found {len(duplicates)} sets of duplicates ({total_dupes} files to remove)\n")
        
        if not UserInput.yes_no("Proceed with deletion?"):
            print("Cancelled")
            return
        
        deleted = 0
        for paths in duplicates.values():
            # Keep first, delete rest
            for filepath in paths[1:]:
                try:
                    filepath.unlink()
                    print(f"Deleted: {filepath}")
                    deleted += 1
                except Exception as e:
                    print(f"Error deleting {filepath}: {e}")
        
        print(f"\nDeleted {deleted} duplicate files")


class DirectoryOperations:
    """Directory manipulation operations"""
    
    @staticmethod
    def delete_empty_dirs(directory: Path):
        """Recursively delete empty directories"""
        deleted = 0
        
        for root, dirs, files in os.walk(directory, topdown=False):
            root_path = Path(root)
            
            if not any(root_path.iterdir()):
                try:
                    root_path.rmdir()
                    print(f"Deleted: {root_path}")
                    deleted += 1
                except Exception as e:
                    print(f"Error deleting {root_path}: {e}")
        
        print(f"\nDeleted {deleted} empty directories")
    
    @staticmethod
    def flatten_directory(directory: Path):
        """Move all files from subdirectories to main directory"""
        if not UserInput.yes_no("This will move all files to the main directory. Continue?"):
            return
        
        moved = 0
        
        for root, dirs, files in os.walk(directory, topdown=False):
            root_path = Path(root)
            
            if root_path == directory:
                continue
            
            for filename in files:
                src = root_path / filename
                dst = directory / filename
                dst = PathUtils.ensure_unique(dst)
                
                try:
                    shutil.move(str(src), str(dst))
                    print(f"Moved: {filename}")
                    moved += 1
                except Exception as e:
                    print(f"Error moving {src}: {e}")
        
        print(f"\nMoved {moved} files")
        
        # Clean up empty directories
        DirectoryOperations.delete_empty_dirs(directory)
    
    @staticmethod
    def compare_directories():
        """Compare two directories and generate report"""
        dir1 = PathUtils.get_valid_path("First directory: ")
        dir2 = PathUtils.get_valid_path("Second directory: ")
        
        print("\nScanning directories...")
        
        items1 = DirectoryOperations._scan_items(dir1)
        items2 = DirectoryOperations._scan_items(dir2)
        
        all_items = set(items1.keys()) | set(items2.keys())
        
        differences = []
        unique_to_dir1 = []
        unique_to_dir2 = []
        identical = []
        
        for item in sorted(all_items):
            if item in items1 and item in items2:
                if items1[item] != items2[item]:
                    differences.append(item)
                else:
                    identical.append(item)
            elif item in items1:
                unique_to_dir1.append(item)
            else:
                unique_to_dir2.append(item)
        
        # Generate report
        log_path = Config.LOG_DIR / "comparison_log.txt"
        
        with open(log_path, 'w') as f:
            f.write("=" * 70 + "\n")
            f.write("DIRECTORY COMPARISON REPORT\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Directory 1: {dir1}\n")
            f.write(f"Directory 2: {dir2}\n")
            f.write(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            def write_section(title: str, items: List[str]):
                f.write("=" * 70 + "\n")
                f.write(f"{title}:\n")
                f.write("=" * 70 + "\n\n")
                
                if items:
                    prev_dir = None
                    for item in sorted(items):
                        curr_dir = str(Path(item).parent)
                        if prev_dir and curr_dir != prev_dir:
                            f.write("\n")
                        f.write(f"{item}\n")
                        prev_dir = curr_dir
                else:
                    f.write("(none)\n")
                f.write("\n")
            
            write_section("Differences between directories", differences)
            write_section("Items only in directory 1", unique_to_dir1)
            write_section("Items only in directory 2", unique_to_dir2)
            write_section("Identical items in both directories", identical)
        
        print(f"\nComparison complete!")
        print(f"Log saved to: {log_path}")
    
    @staticmethod
    def _scan_items(directory: Path) -> Dict[str, str]:
        """Scan directory and return relative paths with hashes/types"""
        items = {}
        
        for root, dirs, files in os.walk(directory):
            root_path = Path(root)
            
            # Add directories
            for dirname in dirs:
                dir_path = root_path / dirname
                rel_path = dir_path.relative_to(directory)
                items[str(rel_path)] = "DIR"
            
            # Add files with hashes
            for filename in files:
                file_path = root_path / filename
                rel_path = file_path.relative_to(directory)
                
                try:
                    file_hash = FileHash.calculate(file_path)
                    items[str(rel_path)] = file_hash
                except IOError:
                    items[str(rel_path)] = "ERROR"
        
        return items


class FileNaming:
    """File renaming operations"""
    
    @staticmethod
    def random_names(directory: Path, recursive: bool = False):
        """Rename files with random strings"""
        files = FileScanner.scan(directory, recursive=recursive)
        
        if not files:
            print("No files found")
            return
        
        length = 8
        renamed = 0
        
        for filepath in files:
            try:
                chars = string.ascii_letters + string.digits
                new_name = ''.join(random.choice(chars) for _ in range(length))
                new_path = filepath.parent / f"{new_name}{filepath.suffix}"
                new_path = PathUtils.ensure_unique(new_path)
                
                filepath.rename(new_path)
                print(f"{filepath.name} → {new_path.name}")
                renamed += 1
            except Exception as e:
                print(f"Error: {filepath.name}: {e}")
        
        print(f"\nRenamed {renamed} files")
    
    @staticmethod
    def capitalize_names(directory: Path, recursive: bool = False):
        """Capitalize first letter of file/directory names"""
        files = FileScanner.scan(directory, recursive=recursive)
        renamed = 0
        
        for filepath in files:
            try:
                new_name = filepath.name.capitalize()
                if new_name != filepath.name:
                    new_path = filepath.parent / new_name
                    filepath.rename(new_path)
                    print(f"{filepath.name} → {new_name}")
                    renamed += 1
            except Exception as e:
                print(f"Error: {filepath.name}: {e}")
        
        # Handle directories if recursive
        if recursive:
            for root, dirs, _ in os.walk(directory, topdown=False):
                for dirname in dirs:
                    dir_path = Path(root) / dirname
                    new_name = dirname.capitalize()
                    if new_name != dirname:
                        try:
                            new_path = Path(root) / new_name
                            dir_path.rename(new_path)
                            print(f"{dirname}/ → {new_name}/")
                            renamed += 1
                        except Exception as e:
                            print(f"Error: {dirname}: {e}")
        
        print(f"\nRenamed {renamed} items")
    
    @staticmethod
    def remove_keywords(directory: Path, recursive: bool = False):
        """Remove specified keywords from filenames"""
        print("\nEnter keywords to remove (one per line, empty line to finish):")
        keywords = []
        while True:
            keyword = input("  Keyword: ").strip()
            if not keyword:
                break
            keywords.append(keyword)
        
        if not keywords:
            print("No keywords provided")
            return
        
        files = FileScanner.scan(directory, recursive=recursive)
        renamed = 0
        
        for filepath in files:
            try:
                new_name = filepath.name
                modified = False
                
                for keyword in keywords:
                    if keyword in new_name:
                        new_name = new_name.replace(keyword, '')
                        modified = True
                
                if modified:
                    # Clean up multiple spaces
                    new_name = re.sub(r'\s+', ' ', new_name).strip()
                    new_path = filepath.parent / new_name
                    
                    filepath.rename(new_path)
                    print(f"{filepath.name} → {new_name}")
                    renamed += 1
            except Exception as e:
                print(f"Error: {filepath.name}: {e}")
        
        print(f"\nRenamed {renamed} files")
    
    @staticmethod
    def rename_detailed_files(directory: Path):
        """Remove trailing spaces and specific media keywords from filenames"""
        # Predefined keywords for media files
        keywords = [
            " (128kbit_AAC)", " (192kbit_AAC)", " (720p_30fps_H264-128kbit_AAC)",
            " (1080p_24fps_H264-128kbit_AAC)", " (480p_30fps_H264-128kbit_AAC)",
            " (1080p_30fps_H264-128kbit_AAC)", " (2160p_30fps_VP9 LQ-128kbit_AAC)",
            " (360p_30fps_H264-128kbit_AAC)", " (360p_30fps_H264-96kbit_AAC)",
            " (1080p_6fps_H264-128kbit_AAC)", " (360p_25fps_H264-128kbit_AAC)",
            " (480p_25fps_H264-128kbit_AAC)", " (720p_24fps_H264-192kbit_AAC)",
            " (240p_24fps_H264-96kbit_AAC)", " (1080p_60fps_H264-128kbit_AAC)",
            " (720p_30fps_H264-192kbit_AAC)", " (2160p_24fps_VP9 LQ-128kbit_AAC)",
            " (2048p_25fps_VP9 LQ-128kbit_AAC)", " (470p_30fps_H264-128kbit_AAC)",
            " (1080p_25fps_H264-128kbit_AAC)", " (864p_24fps_H264-128kbit_AAC)",
            " (720p_25fps_H264-128kbit_AAC)", " (2160p_25fps_VP9 LQ-128kbit_AAC)",
            " (1440p_30fps_H264-128kbit_AAC)", " (720p_24fps_H264-128kbit_AAC)",
            " (1080p_30fps_AV1-128kbit_AAC)", " (720p_6fps_H264-128kbit_AAC)",
            " (240p_30fps_H264-96kbit_AAC)", " (720p_25fps_H264-192kbit_AAC)",
            " (480p_30fps_VP9-128kbit_AAC)", " (1080p_24fps_AV1-128kbit_AAC)",
            " (240p_25fps_H264-96kbit_AAC)", " (336p_20fps_H264-96kbit_AAC)",
            " (152kbit_Opus)", " (720p_aac)", " [1080]", "[720p]", " [360p]",
            " [240]", " [144]", " (720p_60fps_H264-128kbit_AAC)"
        ]
        
        media_exts = {'.mp4', '.m4a', '.ogg', '.webm', '.avi', '.mkv', '.wmv', '.mp3', '.opus'}
        files = FileScanner.scan(directory, media_exts)
        
        if not files:
            print("No media files found")
            return
        
        renamed = 0
        
        for filepath in files:
            try:
                # Remove trailing spaces from stem
                stem = filepath.stem.rstrip()
                new_name = stem + filepath.suffix
                
                # Remove keywords
                for keyword in keywords:
                    if keyword in new_name:
                        new_name = new_name.replace(keyword, '')
                
                if new_name != filepath.name:
                    new_path = filepath.parent / new_name
                    filepath.rename(new_path)
                    print(f"{filepath.name} → {new_name}")
                    renamed += 1
            except Exception as e:
                print(f"Error: {filepath.name}: {e}")
        
        print(f"\nRenamed {renamed} files")


class FileOrganization:
    """File organization operations"""
    
    @staticmethod
    def by_extension(directory: Path):
        """Organize files into folders by extension"""
        files = FileScanner.scan(directory)
        
        if not files:
            print("No files found")
            return
        
        moved = 0
        
        for filepath in files:
            ext = filepath.suffix.lower().lstrip('.')
            
            if not ext:
                ext = "no_extension"
            
            target_dir = directory / ext
            target_dir.mkdir(exist_ok=True)
            
            target_path = target_dir / filepath.name
            
            if not target_path.exists():
                shutil.move(str(filepath), str(target_path))
                moved += 1
        
        print(f"Moved {moved} files")
    
    @staticmethod
    def by_type(directory: Path, recursive: bool = False):
        """Organize files into Image/Video/Audio/Document/Archive folders"""
        type_mapping = {
            'Images': Config.IMAGE_EXTS,
            'Videos': Config.VIDEO_EXTS,
            'Audio': Config.AUDIO_EXTS,
            'Documents': Config.DOCUMENT_EXTS,
            'Archives': Config.ARCHIVE_EXTS
        }
        
        files = FileScanner.scan(directory, recursive=recursive)
        counts = defaultdict(int)
        
        for filepath in files:
            ext = filepath.suffix.lower()
            
            # Find matching category
            category = None
            for cat, exts in type_mapping.items():
                if ext in exts:
                    category = cat
                    break
            
            if not category:
                continue
            
            # Skip if already in category folder
            if filepath.parent.name == category:
                continue
            
            target_dir = directory / category
            target_dir.mkdir(exist_ok=True)
            
            target_path = target_dir / filepath.name
            target_path = PathUtils.ensure_unique(target_path)
            
            try:
                shutil.move(str(filepath), str(target_path))
                counts[category] += 1
            except Exception as e:
                print(f"Error moving {filepath.name}: {e}")
        
        print("\nOrganization complete:")
        for category, count in counts.items():
            if count > 0:
                print(f"  {category}: {count} files")
    
    @staticmethod
    def by_title(directory: Path):
        """Group files by title (filename before year/details)"""
        files = FileScanner.scan(directory, Config.MEDIA_EXTS)
        
        if not files:
            print("No media files found")
            return
        
        # Extract titles and group files
        title_map = defaultdict(list)
        
        for filepath in files:
            # Extract title (everything before year in parentheses or first dash)
            name = filepath.stem
            
            # Try to find year pattern
            match = re.match(r'^(.*?)\s*\(', name)
            if match:
                title = match.group(1).strip()
            else:
                # Fallback to first part before dash
                title = name.split('-')[0].strip()
            
            # Clean title
            title = PathUtils.sanitize_filename(title)
            
            if title:
                title_map[title].append(filepath)
        
        # Organize files
        misc_dir = directory / "Misc"
        moved = 0
        created = 0
        
        for title, files_list in title_map.items():
            if len(files_list) > 1:
                # Multiple files: create folder
                target_dir = directory / title
                target_dir.mkdir(exist_ok=True)
                created += 1
                
                for filepath in files_list:
                    target_path = target_dir / filepath.name
                    shutil.move(str(filepath), str(target_path))
                    moved += 1
            else:
                # Single file: move to Misc
                misc_dir.mkdir(exist_ok=True)
                target_path = misc_dir / files_list[0].name
                shutil.move(str(files_list[0]), str(target_path))
        
        print(f"Created {created} title folders")
        print(f"Moved {moved} grouped files")


class ImageOperations:
    """Image-specific operations"""
    
    @staticmethod
    def organize_by_year(directory: Path, recursive: bool = False):
        """Organize images/videos by date into Year/Month folders"""
        if not IMAGING_AVAILABLE:
            print("Warning: PIL not available, using file modification dates only")
        
        files = FileScanner.scan(directory, Config.MEDIA_EXTS, recursive)
        
        if not files:
            print("No media files found")
            return
        
        moved = 0
        
        for filepath in files:
            try:
                # Get date from EXIF or file modification time
                date = ImageOperations._get_file_date(filepath)
                
                year = date.strftime("%Y")
                month = date.strftime("%B")
                
                # Determine media type
                if filepath.suffix.lower() in Config.IMAGE_EXTS:
                    media_type = "Images"
                else:
                    media_type = "Videos"
                
                target_dir = directory / year / month / media_type
                target_dir.mkdir(parents=True, exist_ok=True)
                
                target_path = target_dir / filepath.name
                target_path = PathUtils.ensure_unique(target_path)
                
                shutil.move(str(filepath), str(target_path))
                print(f"{filepath.name} → {year}/{month}/{media_type}/")
                moved += 1
                
            except Exception as e:
                print(f"Error processing {filepath.name}: {e}")
        
        print(f"\nMoved {moved} files")
    
    @staticmethod
    def _get_file_date(filepath: Path) -> datetime:
        """Extract date from file (EXIF if available, otherwise modification time)"""
        if IMAGING_AVAILABLE and filepath.suffix.lower() in Config.IMAGE_EXTS:
            try:
                img = Image.open(filepath)
                
                if 'exif' in img.info:
                    exif_data = piexif.load(img.info['exif'])
                    
                    # Try DateTimeOriginal
                    if piexif.ExifIFD.DateTimeOriginal in exif_data.get('Exif', {}):
                        date_str = exif_data['Exif'][piexif.ExifIFD.DateTimeOriginal].decode('utf-8')
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
                    
                    # Try DateTime
                    if piexif.ImageIFD.DateTime in exif_data.get('0th', {}):
                        date_str = exif_data['0th'][piexif.ImageIFD.DateTime].decode('utf-8')
                        return datetime.strptime(date_str, "%Y:%m:%d %H:%M:%S")
            except Exception:
                pass
        
        # Fallback to file modification time
        return datetime.fromtimestamp(filepath.stat().st_mtime)


class DateFinder:
    """Find files by creation/modification date"""
    
    @staticmethod
    def find_by_date(directory: Path):
        """Find files created in a specific month/year"""
        # Get month and year
        month = input("Enter month (MM): ").strip()
        year = input("Enter year (YYYY): ").strip()
        
        # Validate input
        if not (re.match(r'^(0[1-9]|1[0-2])$', month) and re.match(r'^\d{4}$', year)):
            print("Invalid month/year format")
            return
        
        # Create date range
        start_date = datetime.strptime(f"{year}-{month}-01", "%Y-%m-%d")
        
        # Calculate end date (first day of next month)
        if month == '12':
            end_date = datetime.strptime(f"{int(year)+1}-01-01", "%Y-%m-%d")
        else:
            next_month = f"{int(month)+1:02d}"
            end_date = datetime.strptime(f"{year}-{next_month}-01", "%Y-%m-%d")
        
        print(f"\nSearching for files created between {start_date.date()} and {end_date.date()}...")
        
        found = []
        
        for filepath in FileScanner.scan(directory, recursive=True):
            try:
                # Try to get birth time (creation time)
                stat_info = filepath.stat()
                
                # Use st_birthtime if available (macOS), otherwise use st_ctime (Linux)
                if hasattr(stat_info, 'st_birthtime'):
                    created = datetime.fromtimestamp(stat_info.st_birthtime)
                else:
                    created = datetime.fromtimestamp(stat_info.st_ctime)
                
                if start_date <= created < end_date:
                    found.append((filepath, created))
            except Exception:
                pass
        
        if found:
            print(f"\nFound {len(found)} files:\n")
            for filepath, created in found:
                print(f"{filepath} (created: {created.strftime('%Y-%m-%d')})")
        else:
            print("\nNo files found in that date range")


# ============================================================================
# MENU SYSTEM
# ============================================================================

def show_menu(commands: List[str], selected: int):
    """Display menu with highlighted selection"""
    clear()
    print("\033[1m  Archivist Tools\033[0m")
    print("  ---------------\n")
    
    for i, cmd in enumerate(commands):
        if i == selected:
            print(f"\033[1m➤ {cmd}\033[0m\n")
        else:
            print(f"  {cmd}\n")


def run_command(cmd: str):
    """Execute the selected command"""
    clear()
    
    try:
        if cmd == "Change Hash":
            directory = PathUtils.get_valid_path("Directory path: ")
            recursive = UserInput.yes_no("Apply recursively?")
            HashOperations.change_hashes(directory, recursive)
        
        elif cmd == "Compare Directories":
            DirectoryOperations.compare_directories()
        
        elif cmd == "Delete Duplicate":
            directory = PathUtils.get_valid_path("Directory path: ")
            recursive = UserInput.yes_no("Apply recursively?")
            HashOperations.remove_duplicates(directory, recursive)
        
        elif cmd == "Delete Empty Folders":
            directory = PathUtils.get_valid_path("Directory path: ")
            DirectoryOperations.delete_empty_dirs(directory)
        
        elif cmd == "Delete Filename Keyword":
            directory = PathUtils.get_valid_path("Directory path: ")
            keyword = input("Enter keyword to delete files containing it: ").strip()
            recursive = UserInput.yes_no("Apply recursively?")
            
            files = FileScanner.scan(directory, recursive=recursive)
            deleted = []
            
            for filepath in files:
                if keyword.lower() in filepath.name.lower():
                    try:
                        filepath.unlink()
                        deleted.append(filepath)
                        print(f"Deleted: {filepath.name}")
                    except Exception as e:
                        print(f"Error deleting {filepath.name}: {e}")
            
            print(f"\nDeleted {len(deleted)} files")
        
        elif cmd == "Empty Directory Contents":
            DirectoryOperations.flatten_directory(directory)
        
        elif cmd == "Find by Date":
            directory = PathUtils.get_valid_path("Directory to search: ")
            DateFinder.find_by_date(directory)
        
        elif cmd == "Give Random Name":
            directory = PathUtils.get_valid_path("Directory path: ")
            recursive = UserInput.yes_no("Apply recursively?")
            FileNaming.random_names(directory, recursive)
        
        elif cmd == "Mass Uppercase":
            directory = PathUtils.get_valid_path("Directory path: ")
            recursive = UserInput.yes_no("Apply recursively?")
            FileNaming.capitalize_names(directory, recursive)
        
        elif cmd == "Rename Detailed Files":
            directory = PathUtils.get_valid_path("Directory path: ")
            FileNaming.rename_detailed_files(directory)
        
        elif cmd == "Sort by File Format":
            directory = PathUtils.get_valid_path("Directory path: ")
            FileOrganization.by_extension(directory)
        
        elif cmd == "Sort by Filetype":
            directory = PathUtils.get_valid_path("Directory path: ")
            recursive = UserInput.yes_no("Apply recursively?")
            FileOrganization.by_type(directory, recursive)
        
        elif cmd == "Sort by Title":
            directory = PathUtils.get_valid_path("Directory path: ")
            FileOrganization.by_title(directory)
        
        elif cmd == "Sort by Year":
            directory = PathUtils.get_valid_path("Directory path: ")
            recursive = UserInput.yes_no("Apply recursively?")
            ImageOperations.organize_by_year(directory, recursive)
        
        elif cmd == "Quit":
            clear()
            print("\n\033[1mExiting Archivist Tools\033[0m\n")
            sys.exit(0)
        
    except KeyboardInterrupt:
        print("\n\nOperation cancelled")
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
    
    input("\nPress Enter to return to menu...")


def main():
    """Main program loop"""
    commands = [
        "Change Hash",
        "Compare Directories",
        "Delete Duplicate",
        "Delete Empty Folders",
        "Delete Filename Keyword",
        "Empty Directory Contents",
        "Find by Date",
        "Give Random Name",
        "Mass Uppercase",
        "Rename Detailed Files",
        "Sort by File Format",
        "Sort by Filetype",
        "Sort by Title",
        "Sort by Year",
        "Quit"
    ]
    
    selected = 0
    
    while True:
        show_menu(commands, selected)
        
        key = get_key()
        
        if key == 'UP':
            selected = (selected - 1) % len(commands)
        elif key == 'DOWN':
            selected = (selected + 1) % len(commands)
        elif key == 'ENTER':
            run_command(commands[selected])
        elif key == 'CTRL_C':
            clear()
            print("\n\033[1mExiting Archivist Tools\033[0m\n")
            break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        clear()
        print("\n\033[1mExiting Archivist Tools\033[0m\n")
