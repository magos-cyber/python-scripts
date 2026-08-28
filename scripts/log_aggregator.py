#!/usr/bin/env python3
"""Log Aggregator - Collects and analyzes logs from multiple sources."""

import os
import re
from collections import defaultdict, Counter
import sys

class LogAggregator:
    def __init__(self):
        self.sources = []
        self.patterns = {
            'error': re.compile(r'ERROR|FATAL|CRITICAL', re.IGNORECASE),
            'warning': re.compile(r'WARN|WARNING', re.IGNORECASE),
            'auth_fail': re.compile(r'Failed password|authentication failure', re.IGNORECASE),
        }

    def add_source(self, filepath):
        """Add a log file to monitor."""
        if os.path.exists(filepath):
            self.sources.append(filepath)

    def aggregate(self):
        """Aggregate logs and count patterns."""
        results = defaultdict(Counter)
        for source in self.sources:
            with open(source) as f:
                for line in f:
                    for name, pattern in self.patterns.items():
                        if pattern.search(line):
                            results[source][name] += 1
        return results

    def report(self):
        """Print aggregated report."""
        results = self.aggregate()
        print("=== Log Aggregation Report ===
")
        for source, counts in results.items():
            print(f"{source}:")
            for pattern, count in counts.items():
                print(f"  {pattern}: {count}")
            print()

if __name__ == "__main__":
    aggregator = LogAggregator()
    for logfile in sys.argv[1:]:
        aggregator.add_source(logfile)
    aggregator.report()
