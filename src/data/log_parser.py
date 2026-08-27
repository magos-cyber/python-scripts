#!/usr/bin/env python3
"""
log_parser.py — Advanced log parser with filtering and statistics
Supports multiple log formats with real-time monitoring capabilities
"""

import re
import logging
from datetime import datetime
from collections import Counter, defaultdict
from pathlib import Path
from typing import List, Dict, Optional
import argparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class LogParser:
    """Parse and analyze log files"""
    
    def __init__(self, log_path: str):
        self.log_path = Path(log_path)
        self.lines = []
        self._load()
    
    def _load(self):
        """Load log file"""
        if not self.log_path.exists():
            logger.error(f"Log file not found: {self.log_path}")
            return
        
        with open(self.log_path, 'r', errors='replace') as f:
            self.lines = f.readlines()
        
        logger.info(f"Loaded {len(self.lines)} lines from {self.log_path}")
    
    def count_levels(self) -> Dict[str, int]:
        """Count log levels (ERROR, WARN, INFO, DEBUG)"""
        levels = Counter()
        patterns = {
            "ERROR": r'\bERROR\b',
            "WARN": r'\bWARN(ING)?\b',
            "INFO": r'\bINFO\b',
            "DEBUG": r'\bDEBUG\b',
            "CRITICAL": r'\bCRITICAL\b',
            "FATAL": r'\bFATAL\b'
        }
        
        for line in self.lines:
            for level, pattern in patterns.items():
                if re.search(pattern, line, re.IGNORECASE):
                    levels[level] += 1
        
        return dict(levels)
    
    def find_errors(self, context: int = 0) -> List[str]:
        """Find all error lines"""
        errors = []
        for i, line in enumerate(self.lines):
            if re.search(r'\bERROR\b', line, re.IGNORECASE):
                if context > 0:
                    start = max(0, i - context)
                    end = min(len(self.lines), i + context + 1)
                    errors.append(''.join(self.lines[start:end]))
                else:
                    errors.append(line.strip())
        return errors
    
    def search_pattern(self, pattern: str) -> List[str]:
        """Search for a regex pattern"""
        results = []
        for line in self.lines:
            if re.search(pattern, line):
                results.append(line.strip())
        return results
    
    def top_ips(self, n: int = 10) -> List[tuple]:
        """Find top IP addresses (useful for access logs)"""
        ip_pattern = r'\b(?:\d{1,3}\.){3}\d{1,3}\b'
        ips = Counter()
        
        for line in self.lines:
            matches = re.findall(ip_pattern, line)
            for ip in matches:
                ips[ip] += 1
        
        return ips.most_common(n)
    
    def top_errors(self, n: int = 10) -> List[tuple]:
        """Find most common error messages"""
        error_lines = self.find_errors()
        errors = Counter()
        
        for line in error_lines:
            # Normalize by removing timestamps and IDs
            normalized = re.sub(r'\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}', '<TIME>', line)
            normalized = re.sub(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', '<UUID>', normalized)
            normalized = re.sub(r'\b\d+\b', '<NUM>', normalized)
            errors[normalized] += 1
        
        return errors.most_common(n)
    
    def hourly_distribution(self) -> Dict[int, int]:
        """Get log distribution by hour"""
        hours = Counter()
        
        for line in self.lines:
            match = re.search(r'(\d{2}):\d{2}:\d{2}', line)
            if match:
                hours[int(match.group(1))] += 1
        
        return dict(sorted(hours.items()))
    
    def generate_report(self) -> str:
        """Generate a summary report"""
        report = []
        report.append(f"[CHART] Log Analysis Report")
        report.append(f"{'='*50}")
        report.append(f"File: {self.log_path}")
        report.append(f"Total lines: {len(self.lines)}")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Log levels
        levels = self.count_levels()
        if levels:
            report.append("Log Levels:")
            for level, count in sorted(levels.items(), key=lambda x: x[1], reverse=True):
                report.append(f"  {level}: {count}")
            report.append("")
        
        # Top IPs
        ips = self.top_ips(5)
        if ips:
            report.append("Top IPs:")
            for ip, count in ips:
                report.append(f"  {ip}: {count}")
            report.append("")
        
        # Top errors
        errors = self.top_errors(5)
        if errors:
            report.append("Top Errors:")
            for error, count in errors[:5]:
                report.append(f"  [{count}x] {error[:100]}")
            report.append("")
        
        # Hourly distribution
        hours = self.hourly_distribution()
        if hours:
            report.append("Hourly Distribution:")
            for hour, count in hours.items():
                bar = '#' * min(count // 10, 50)
                report.append(f"  {hour:02d}:00 | {bar} ({count})")
        
        return '\n'.join(report)


def main():
    parser = argparse.ArgumentParser(description="Log File Analyzer")
    parser.add_argument("log_file", help="Path to log file")
    parser.add_argument("--errors", action="store_true", help="Show only errors")
    parser.add_argument("--search", help="Search for pattern")
    parser.add_argument("--report", action="store_true", help="Generate full report")
    parser.add_argument("--top-ips", action="store_true", help="Show top IPs")
    args = parser.parse_args()
    
    analyzer = LogParser(args.log_file)
    
    if args.report:
        print(analyzer.generate_report())
    elif args.errors:
        errors = analyzer.find_errors()
        for e in errors[:50]:
            print(e)
        print(f"\nTotal errors: {len(errors)}")
    elif args.search:
        results = analyzer.search_pattern(args.search)
        for r in results[:50]:
            print(r)
        print(f"\nTotal matches: {len(results)}")
    elif args.top_ips:
        for ip, count in analyzer.top_ips():
            print(f"{ip}: {count}")
    else:
        print(analyzer.generate_report())


if __name__ == "__main__":
    main()