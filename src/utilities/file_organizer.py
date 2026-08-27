#!/usr/bin/env python3
"""
file_organizer.py — Organize files by type, date, or extension
Moves files from a source directory into categorized subdirectories
"""

import os
import shutil
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# File type categories
FILE_CATEGORIES = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"],
    "Documents": [".pdf", ".doc", ".docx", ".txt", ".rtf", ".odt", ".xls", ".xlsx", ".ppt", ".pptx"],
    "Videos": [".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"],
    "Audio": [".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a"],
    "Archives": [".zip", ".rar", ".7z", ".tar", ".gz", ".bz2"],
    "Code": [".py", ".js", ".html", ".css", ".java", ".cpp", ".c", ".h", ".sh", ".yml", ".yaml", ".json", ".xml"],
    "Databases": [".db", ".sqlite", ".sql"],
    "Executables": [".exe", ".msi", ".deb", ".rpm", ".appimage"],
    "Fonts": [".ttf", ".otf", ".woff", ".woff2"],
    "Ebooks": [".epub", ".mobi", ".azw", ".azw3"],
    "Torrents": [".torrent"],
    "ISOs": [".iso", ".img"]
}


def get_category(extension: str) -> str:
    """Get category for a file extension"""
    ext = extension.lower()
    for category, extensions in FILE_CATEGORIES.items():
        if ext in extensions:
            return category
    return "Other"


def organize_by_type(source_dir: str, dest_dir: Optional[str] = None, dry_run: bool = False):
    """Organize files by type"""
    source = Path(source_dir)
    if dest_dir is None:
        dest = source
    else:
        dest = Path(dest_dir)
    
    if not source.exists():
        logger.error(f"Source directory does not exist: {source}")
        return
    
    files = [f for f in source.iterdir() if f.is_file()]
    logger.info(f"Found {len(files)} files to organize")
    
    for file in files:
        category = get_category(file.suffix)
        category_dir = dest / category
        dest_file = category_dir / file.name
        
        if dry_run:
            logger.info(f"[DRY RUN] Would move: {file.name} -> {category}/")
        else:
            category_dir.mkdir(exist_ok=True)
            # Handle duplicate filenames
            if dest_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{file.stem}_{timestamp}{file.suffix}"
                dest_file = category_dir / new_name
            
            shutil.move(str(file), str(dest_file))
            logger.info(f"Moved: {file.name} -> {category}/")


def organize_by_date(source_dir: str, dest_dir: Optional[str] = None, dry_run: bool = False):
    """Organize files by modification date"""
    source = Path(source_dir)
    if dest_dir is None:
        dest = source
    else:
        dest = Path(dest_dir)
    
    if not source.exists():
        logger.error(f"Source directory does not exist: {source}")
        return
    
    files = [f for f in source.iterdir() if f.is_file()]
    logger.info(f"Found {len(files)} files to organize")
    
    for file in files:
        mtime = datetime.fromtimestamp(file.stat().st_mtime)
        date_dir = dest / f"{mtime.year}" / f"{mtime.month:02d}"
        dest_file = date_dir / file.name
        
        if dry_run:
            logger.info(f"[DRY RUN] Would move: {file.name} -> {mtime.year}/{mtime.month:02d}/")
        else:
            date_dir.mkdir(parents=True, exist_ok=True)
            if dest_file.exists():
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                new_name = f"{file.stem}_{timestamp}{file.suffix}"
                dest_file = date_dir / new_name
            
            shutil.move(str(file), str(dest_file))
            logger.info(f"Moved: {file.name} -> {mtime.year}/{mtime.month:02d}/")


def main():
    parser = argparse.ArgumentParser(description="Organize files by type or date")
    parser.add_argument("source", help="Source directory")
    parser.add_argument("--dest", help="Destination directory (default: same as source)")
    parser.add_argument("--by", choices=["type", "date"], default="type", help="Organization method")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without moving")
    args = parser.parse_args()
    
    if args.by == "type":
        organize_by_type(args.source, args.dest, args.dry_run)
    else:
        organize_by_date(args.source, args.dest, args.dry_run)


if __name__ == "__main__":
    main()