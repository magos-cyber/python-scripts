#!/usr/bin/env python3
"""YAML Validator - Checks YAML files for syntax errors."""

import yaml
import sys

def validate_yaml(filepath):
    """Validate a YAML file."""
    try:
        with open(filepath) as f:
            yaml.safe_load(f)
        print(f"OK: {filepath} is valid YAML")
        return True
    except yaml.YAMLError as e:
        print(f"FAIL: {filepath} - {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python yaml_validator.py <file.yaml>")
        sys.exit(1)
    
    for filepath in sys.argv[1:]:
        validate_yaml(filepath)
