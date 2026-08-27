#!/usr/bin/env python3
"""
config_manager.py — YAML/TOML/JSON config file manager with validation and templates
Loads, saves, validates, and generates configuration files in multiple formats.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

# Try to import optional dependencies (yaml, toml) - but we know they're available
try:
    import yaml
except ImportError:
    yaml = None

try:
    import tomllib  # Python 3.11+
    import tomli_w  # for writing TOML
except ImportError:
    tomllib = None
    tomli_w = None

# Setup logging
import logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration files in JSON, YAML, and TOML formats."""

    def __init__(self):
        self.supported_formats = {
            '.json': self._load_json, '.yaml': self._load_yaml, '.yml': self._load_yaml,
            '.toml': self._load_toml
        }
        self.save_formats = {
            '.json': self._save_json, '.yaml': self._save_yaml, '.yml': self._save_yaml,
            '.toml': self._save_toml
        }

    def load_config(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Load configuration from file.
        Auto-detects format by file extension.
        Returns dictionary with configuration data.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {file_path}")

        # Determine format by extension
        ext = file_path.suffix.lower()
        if ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {ext}. Supported: {list(self.supported_formats.keys())}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return self.supported_formats[ext](content)
        except Exception as e:
            logger.error(f"Failed to load config from {file_path}: {e}")
            raise

    def save_config(self, config: Dict[str, Any], file_path: Union[str, Path]):
        """
        Save configuration to file.
        Format determined by file extension.
        Creates parent directories if needed.
        """
        file_path = Path(file_path)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        ext = file_path.suffix.lower()
        if ext not in self.save_formats:
            raise ValueError(f"Unsupported file format for saving: {ext}. Supported: {list(self.save_formats.keys())}")

        try:
            content = self.save_formats[ext](config)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info(f"Configuration saved to {file_path}")
        except Exception as e:
            logger.error(f"Failed to save config to {file_path}: {e}")
            raise

    def _load_json(self, content: str) -> Dict[str, Any]:
        return json.loads(content)

    def _save_json(self, config: Dict[str, Any]) -> str:
        return json.dumps(config, indent=2, sort_keys=True)

    def _load_yaml(self, content: str) -> Dict[str, Any]:
        if yaml is None:
            raise ImportError("PyYAML not installed. Install with: pip install pyyaml")
        return yaml.safe_load(content) or {}

    def _save_yaml(self, config: Dict[str, Any]) -> str:
        if yaml is None:
            raise ImportError("PyYAML not installed. Install with: pip install pyyaml")
        return yaml.dump(config, default_flow_style=False, sort_keys=True, allow_unicode=True)

    def _load_toml(self, content: str) -> Dict[str, Any]:
        if tomllib is None:
            raise ImportError("tomli not installed. Install with: pip install tomli")
        return tomllib.loads(content)

    def _save_toml(self, config: Dict[str, Any]) -> str:
        if tomli_w is None:
            raise ImportError("tomli-w not installed. Install with: pip install tomli-w")
        return tomli_w.dumps(config)

    def validate_config(self, config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
        """
        Validate configuration against a schema.
        Returns list of validation errors (empty if valid).
        Schema format:
        {
            "key": {
                "type": str/int/bool/list/dict,
                "required": True/False,
                "default": value (optional),
                "allowed": [list of allowed values] (optional),
                "min": minimum value (for numbers),
                "max": maximum value (for numbers),
                "min_length": minimum length (for strings/lists),
                "max_length": maximum length (for strings/lists),
                "schema": nested schema (for dicts)
            }
        }
        """
        errors = []
        self._validate_recursive(config, schema, "", errors)
        return errors

    def _validate_recursive(self, config: Dict[str, Any], schema: Dict[str, Any], path: str, errors: List[str]):
        for key, rules in schema.items():
            full_path = f"{path}.{key}" if path else key
            value = config.get(key)

            # Check if required
            if rules.get("required", False) and key not in config:
                errors.append(f"Missing required field: {full_path}")
                continue

            # If not present and not required, skip further validation
            if key not in config:
                continue

            # Type checking
            expected_type = rules.get("type")
            if expected_type:
                type_map = {
                    "str": str,
                    "int": int,
                    "float": (int, float),
                    "bool": bool,
                    "list": list,
                    "dict": dict
                }
                if expected_type in type_map:
                    expected = type_map[expected_type]
                    if not isinstance(value, expected):
                        errors.append(f"Field '{full_path}' must be {expected_type}, got {type(value).__name__}")
                        continue  # Skip further type-specific checks

            # Allowed values
            if "allowed" in rules:
                if value not in rules["allowed"]:
                    errors.append(f"Field '{full_path}' must be one of {rules['allowed']}, got {value}")

            # Numeric constraints
            if isinstance(value, (int, float)):
                if "min" in rules and value < rules["min"]:
                    errors.append(f"Field '{full_path}' must be >= {rules['min']}, got {value}")
                if "max" in rules and value > rules["max"]:
                    errors.append(f"Field '{full_path}' must be <= {rules['max']}, got {value}")

            # String/list length constraints
            if isinstance(value, (str, list)):
                if "min_length" in rules and len(value) < rules["min_length"]:
                    errors.append(f"Field '{full_path}' length must be >= {rules['min_length']}, got {len(value)}")
                if "max_length" in rules and len(value) > rules["max_length"]:
                    errors.append(f"Field '{full_path}' length must be <= {rules['max_length']}, got {len(value)}")

            # Nested dict validation
            if isinstance(value, dict) and "schema" in rules:
                self._validate_recursive(value, rules["schema"], full_path, errors)

            # Nested list validation (if items have schema)
            if isinstance(value, list) and "item_schema" in rules:
                for i, item in enumerate(value):
                    if isinstance(item, dict):
                        self._validate_recursive(item, rules["item_schema"], f"{full_path}[{i}]", errors)

    def generate_template(self, schema: Dict[str, Any], format: str = "json") -> str:
        """
        Generate a template configuration file from schema.
        Format: json, yaml, or toml.
        Includes comments and example values based on schema.
        """
        template = self._generate_template_recursive(schema, "", format)
        if format == "json":
            return json.dumps(template, indent=2)
        elif format in ("yaml", "yml"):
            if yaml is None:
                raise ImportError("PyYAML not installed")
            return yaml.dump(template, default_flow_style=False, sort_keys=False)
        elif format == "toml":
            if tomli_w is None:
                raise ImportError("tomli-w not installed")
            return tomli_w.dumps(template)
        else:
            raise ValueError(f"Unsupported format for template: {format}")

    def _generate_template_recursive(self, schema: Dict[str, Any], path: str, format: str) -> Any:
        result = {}
        for key, rules in schema.items():
            # Determine example value
            if "default" in rules:
                example = rules["default"]
            elif "allowed" in rules:
                example = rules["allowed"][0] if rules["allowed"] else None
            elif "type" in rules:
                type_map = {
                    "str": "example_string",
                    "int": 42,
                    "float": 3.14,
                    "bool": True,
                    "list": ["example_item"],
                    "dict": {}
                }
                example = type_map.get(rules["type"], None)
            else:
                example = None

            # If nested schema, recurse
            if "schema" in rules and rules["type"] == "dict":
                example = self._generate_template_recursive(rules["schema"], key, format)
            elif "item_schema" in rules and rules["type"] == "list":
                example = [self._generate_template_recursive(rules["item_schema"], key, format)]

            result[key] = example
        return result

    def get_config_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        Get a nested configuration value using dot notation.
        Example: get_config_value(config, "database.host", "localhost")
        """
        keys = key_path.split(".")
        value = config
        try:
            for key in keys:
                if isinstance(value, dict):
                    value = value[key]
                else:
                    return default
            return value
        except (KeyError, TypeError):
            return default

    def set_config_value(self, config: Dict[str, Any], key_path: str, value: Any):
        """
        Set a nested configuration value using dot notation.
        Creates intermediate dictionaries as needed.
        """
        keys = key_path.split(".")
        current = config
        for key in keys[:-1]:
            if key not in current or not isinstance(current[key], dict):
                current[key] = {}
            current = current[key]
        current[keys[-1]] = value


# Convenience functions for backward compatibility
def load_config(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Load configuration from file (JSON/YAML/TOML)."""
    return ConfigManager().load_config(file_path)


def save_config(config: Dict[str, Any], file_path: Union[str, Path]):
    """Save configuration to file (JSON/YAML/TOML)."""
    ConfigManager().save_config(config, file_path)


def validate_config(config: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate configuration against schema."""
    return ConfigManager().validate_config(config, schema)


def generate_template(schema: Dict[str, Any], format: str = "json") -> str:
    """Generate template configuration from schema."""
    return ConfigManager().generate_template(schema, format)


def get_config_value(config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
    """Get nested config value using dot notation."""
    return ConfigManager().get_config_value(config, key_path, default)


def set_config_value(config: Dict[str, Any], key_path: str, value: Any):
    """Set nested config value using dot notation."""
    ConfigManager().set_config_value(config, key_path, value)


def main():
    """Command line interface for config manager."""
    import argparse

    parser = argparse.ArgumentParser(description="Configuration file manager")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Load command
    load_parser = subparsers.add_parser("load", help="Load and display a config file")
    load_parser.add_argument("file", help="Path to config file")

    # Save command
    save_parser = subparsers.add_parser("save", help="Save config to file (from stdin JSON)")
    save_parser.add_argument("file", help="Path to save config file")

    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate config file against schema")
    validate_parser.add_argument("file", help="Path to config file")
    validate_parser.add_argument("--schema", required=True, help="Path to schema file (JSON)")

    # Template command
    template_parser = subparsers.add_parser("template", help="Generate template from schema")
    template_parser.add_argument("--schema", required=True, help="Path to schema file (JSON)")
    template_parser.add_argument("--format", choices=["json", "yaml", "yml", "toml"], default="json", help="Output format")

    args = parser.parse_args()

    if args.command == "load":
        try:
            config = load_config(args.file)
            print(json.dumps(config, indent=2))
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    elif args.command == "save":
        try:
            # Read JSON from stdin
            config_data = json.load(sys.stdin)
            save_config(config_data, args.file)
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    elif args.command == "validate":
        try:
            config = load_config(args.file)
            with open(args.schema) as f:
                schema = json.load(f)
            errors = validate_config(config, schema)
            if errors:
                print("Validation errors:")
                for error in errors:
                    print(f"  - {error}")
                sys.exit(1)
            else:
                print("Configuration is valid!")
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    elif args.command == "template":
        try:
            with open(args.schema) as f:
                schema = json.load(f)
            template = generate_template(schema, args.format)
            print(template)
        except Exception as e:
            logger.error(f"Error: {e}")
            sys.exit(1)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()