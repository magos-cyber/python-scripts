#!/usr/bin/env python3
"""
gitlab-ci-generator.py — Generate GitLab CI/CD pipeline configs
"""

import yaml
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

def generate_ci_config(project_name: str, stages: list) -> str:
    """Generate basic .gitlab-ci.yml content"""
    config = {
        "stages": stages,
        "variables": {
            "PROJECT_NAME": project_name
        },
        "build": {
            "stage": "build",
            "script": ["echo Building $PROJECT_NAME", "make build"]
        },
        "test": {
            "stage": "test",
            "script": ["echo Testing $PROJECT_NAME", "make test"]
        }
    }
    return yaml.dump(config, default_flow_style=False)

if __name__ == "__main__":
    config = generate_ci_config("my-app", ["build", "test", "deploy"])
    with open(".gitlab-ci.yml", "w") as f:
        f.write(config)
    print("Generated .gitlab-ci.yml")
