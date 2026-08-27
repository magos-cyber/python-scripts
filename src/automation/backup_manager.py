#!/usr/bin/env python3
"""
backup_manager.py — Automated backup manager with rotation and compression
Supports local and remote backups with configurable retention policies
"""

import os
import gzip
import shutil
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Optional
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class BackupManager:
    """Manage file backups with rotation and compression"""
    
    def __init__(self, backup_dir: str, retention_days: int = 30, compress: bool = True):
        self.backup_dir = Path(backup_dir)
        self.retention_days = retention_days
        self.compress = compress
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.manifest_file = self.backup_dir / "manifest.json"
        self.manifest = self._load_manifest()
    
    def _load_manifest(self) -> dict:
        """Load backup manifest"""
        if self.manifest_file.exists():
            with open(self.manifest_file) as f:
                return json.load(f)
        return {"backups": []}
    
    def _save_manifest(self):
        """Save backup manifest"""
        with open(self.manifest_file, 'w') as f:
            json.dump(self.manifest, f, indent=2)
    
    def create_backup(self, paths: List[str], name: Optional[str] = None) -> Optional[Path]:
        """Create a backup of specified paths"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if not name:
            name = f"backup_{timestamp}"
        
        backup_path = self.backup_dir / name
        backup_path.mkdir(exist_ok=True)
        
        logger.info(f"Creating backup: {name}")
        
        for path in paths:
            src = Path(path)
            if not src.exists():
                logger.warning(f"Path does not exist: {src}")
                continue
            
            dest = backup_path / src.name
            
            try:
                if src.is_dir():
                    shutil.copytree(src, dest, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dest)
                logger.info(f"  Backed up: {src}")
            except Exception as e:
                logger.error(f"  Failed to backup {src}: {e}")
        
        # Compress if enabled
        if self.compress:
            archive_path = self._compress(backup_path)
            if archive_path:
                shutil.rmtree(backup_path)
                backup_path = archive_path
        
        # Record in manifest
        self.manifest["backups"].append({
            "name": name,
            "path": str(backup_path),
            "timestamp": timestamp,
            "paths": paths,
            "compressed": self.compress
        })
        self._save_manifest()
        
        logger.info(f"Backup complete: {backup_path}")
        return backup_path
    
    def _compress(self, path: Path) -> Optional[Path]:
        """Compress a directory to tar.gz"""
        try:
            archive_path = Path(f"{path}.tar.gz")
            shutil.make_archive(str(path), 'gztar', root_dir=path.parent, base_dir=path.name)
            logger.info(f"Compressed to: {archive_path}")
            return archive_path
        except Exception as e:
            logger.error(f"Compression failed: {e}")
            return None
    
    def restore_backup(self, name: str, restore_dir: str) -> bool:
        """Restore a backup to specified directory"""
        backup_info = None
        for b in self.manifest["backups"]:
            if b["name"] == name:
                backup_info = b
                break
        
        if not backup_info:
            logger.error(f"Backup not found: {name}")
            return False
        
        backup_path = Path(backup_info["path"])
        restore_path = Path(restore_dir)
        restore_path.mkdir(parents=True, exist_ok=True)
        
        try:
            if backup_path.suffix == '.gz' or str(backup_path).endswith('.tar.gz'):
                shutil.unpack_archive(backup_path, restore_path)
            elif backup_path.is_dir():
                shutil.copytree(backup_path, restore_path, dirs_exist_ok=True)
            else:
                shutil.copy2(backup_path, restore_path)
            
            logger.info(f"Restored {name} to {restore_path}")
            return True
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            return False
    
    def rotate_backups(self, keep_count: Optional[int] = None):
        """Remove old backups based on retention policy"""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)
        to_remove = []
        
        for backup in self.manifest["backups"]:
            try:
                backup_date = datetime.strptime(backup["timestamp"], "%Y%m%d_%H%M%S")
                if backup_date < cutoff_date:
                    to_remove.append(backup)
            except ValueError:
                continue
        
        for backup in to_remove:
            backup_path = Path(backup["path"])
            try:
                if backup_path.exists():
                    if backup_path.is_dir():
                        shutil.rmtree(backup_path)
                    else:
                        backup_path.unlink()
                    logger.info(f"Removed old backup: {backup['name']}")
                self.manifest["backups"].remove(backup)
            except Exception as e:
                logger.error(f"Failed to remove backup {backup['name']}: {e}")
        
        self._save_manifest()
        logger.info(f"Rotation complete. Removed {len(to_remove)} old backups.")
    
    def list_backups(self) -> List[dict]:
        """List all backups"""
        return self.manifest["backups"]
    
    def verify_backup(self, name: str) -> bool:
        """Verify backup integrity"""
        for backup in self.manifest["backups"]:
            if backup["name"] == name:
                backup_path = Path(backup["path"])
                if not backup_path.exists():
                    logger.error(f"Backup file missing: {backup_path}")
                    return False
                
                # Check if compressed archive is valid
                if str(backup_path).endswith('.tar.gz'):
                    import tarfile
                    try:
                        with tarfile.open(backup_path, 'r:gz') as tf:
                            tf.getmembers()
                        logger.info(f"Backup verified: {name}")
                        return True
                    except Exception as e:
                        logger.error(f"Backup corrupted: {e}")
                        return False
                return True
        
        logger.error(f"Backup not found: {name}")
        return False


# Example usage
if __name__ == "__main__":
    # Initialize backup manager
    bm = BackupManager("/tmp/test_backups", retention_days=7, compress=True)
    
    # Create a backup
    bm.create_backup(["/etc/hostname", "/etc/resolv.conf"], name="test_backup")
    
    # List backups
    print("Backups:")
    for b in bm.list_backups():
        print(f"  - {b['name']} ({b['timestamp']})")
    
    # Rotate old backups
    bm.rotate_backups()