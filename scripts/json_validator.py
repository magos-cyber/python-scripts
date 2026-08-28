#!/usr/bin/env python3
"""JSON Validator and Formatter - Validates and pretty-prints JSON files."""

import json
import sys

def validate_json(filepath):
    """Validate a JSON file and return True if valid."""
    try:
        with open(filepath) as f:
            data = json.load(f)
        print(f"OK: {filepath} is valid JSON")
        return True
    except json.JSONDecodeError as e:
        print(f"FAIL: {filepath} - {e}")
        return False

def format_json(filepath, indent=2):
    """Format a JSON file with proper indentation."""
    try:
        with open(filepath) as f:
            data = json.load(f)
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=indent)
        print(f"Formatted: {filepath}")
        return True
    except Exception as e:
        print(f"Error formatting {filepath}: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python json_validator.py <file.json> [--format]")
        sys.exit(1)
    
    filepath = sys.argv[1]
    if "--format" in sys.argv:
        format_json(filepath)
    else:
        validate_json(filepath)
