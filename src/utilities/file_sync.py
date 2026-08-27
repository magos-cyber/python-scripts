#!/usr/bin/env python3
import os, shutil, hashlib
def file_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()
def sync_dirs(src, dst):
    for root, dirs, files in os.walk(src):
        rel = os.path.relpath(root, src)
        os.makedirs(os.path.join(dst, rel), exist_ok=True)
        for f in files:
            src_f, dst_f = os.path.join(root, f), os.path.join(dst, rel, f)
            if not os.path.exists(dst_f) or file_hash(src_f) != file_hash(dst_f):
                shutil.copy2(src_f, dst_f)
                print(f"Synced: {os.path.join(rel, f)}")