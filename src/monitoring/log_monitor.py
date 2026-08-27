#!/usr/bin/env python3
import os, sys, time
def monitor_log(filepath, patterns):
    with open(filepath) as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                for p in patterns:
                    if p in line:
                        print(f"[MATCH] {line.strip()}")
            else:
                time.sleep(0.1)
if __name__ == "__main__":
    monitor_log(sys.argv[1], sys.argv[2:])