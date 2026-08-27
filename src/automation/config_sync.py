#!/usr/bin/env python3
"""Sync configuration files between servers."""
import os
import hashlib
import shutil
from pathlib import Path

def file_hash(filepath):
    """Calculate SHA256 hash of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def sync_dir(source, destination):
    """Sync files from source to destination."""
    source = Path(source)
    destination = Path(destination)
    
    if not source.exists():
        print(f"Source not found: {source}")
        return
    
    destination.mkdir(parents=True, exist_ok=True)
    
    for src_file in source.rglob("*"):
        if src_file.is_file():
            rel_path = src_file.relative_to(source)
            dst_file = destination / rel_path
            
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            if not dst_file.exists() or file_hash(src_file) != file_hash(dst_file):
                shutil.copy2(src_file, dst_file)
                print(f"Synced: {rel_path}")

if __name__ == "__main__":
    import sys
    src = sys.argv[1] if len(sys.argv) > 1 else "/config/src"
    dst = sys.argv[2] if len(sys.argv) > 2 else "/config/dst"
    sync_dir(src, dst)
