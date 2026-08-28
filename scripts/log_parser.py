#!/usr/bin/env python3
"""Log Parser - Parses common log files for analysis."""

import re
from collections import Counter
import sys

def parse_nginx_log(logfile):
    """Parse Nginx access log."""
    pattern = r'(\d+\.\d+\.\d+\.\d+).*\[(.*?)\]"(\w+)\s+(\S+)\s+HTTP/\d\.\d"\s+(\d{3})'
    
    ips = Counter()
    status_codes = Counter()
    urls = Counter()
    
    with open(logfile) as f:
        for line in f:
            match = re.match(pattern, line)
            if match:
                ips[match.group(1)] += 1
                status_codes[match.group(5)] += 1
                urls[match.group(4)] += 1
    
    print("=== Top 10 IPs ===")
    for ip, count in ips.most_common(10):
        print(f"  {ip}: {count} requests")
    
    print("
=== Status Codes ===")
    for code, count in status_codes.most_common():
        print(f"  {code}: {count}")
    
    print("
=== Top 10 URLs ===")
    for url, count in urls.most_common(10):
        print(f"  {url}: {count}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python log_parser.py <logfile>")
        sys.exit(1)
    parse_nginx_log(sys.argv[1])
