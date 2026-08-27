#!/usr/bin/env python3
"""Verify backup integrity and age."""
import os
import sys
from datetime import datetime, timedelta

def check_backups(backup_dir, max_age_days=7):
    """Check all backups in directory."""
    if not os.path.exists(backup_dir):
        print(f"Directory not found: {backup_dir}")
        return False
    
    now = datetime.now()
    max_age = timedelta(days=max_age_days)
    issues = []
    
    for f in os.listdir(backup_dir):
        filepath = os.path.join(backup_dir, f)
        if not os.path.isfile(filepath):
            continue
        
        mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
        age = now - mtime
        size = os.path.getsize(filepath)
        
        if age > max_age:
            issues.append(f"OLD: {f} ({age.days} days)")
        if size == 0:
            issues.append(f"EMPTY: {f}")
    
    if issues:
        print("Backup issues found:")
        for issue in issues:
            print(f"  {issue}")
        return False
    else:
        print("All backups OK")
        return True

if __name__ == "__main__":
    directory = sys.argv[1] if len(sys.argv) > 1 else "/var/backups"
    check_backups(directory)
