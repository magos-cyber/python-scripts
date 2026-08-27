#!/usr/bin/env python3
"""
terraform_wrapper.py — Python wrapper for Terraform operations
Supports init, plan, apply, destroy with logging
"""

import subprocess
import logging
from pathlib import Path
from typing import List, Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class TerraformWrapper:
    """Wrapper for Terraform operations"""

    def __init__(self, working_dir: str):
        self.working_dir = Path(working_dir)
        if not self.working_dir.exists():
            raise FileNotFoundError(f"Directory not found: {working_dir}")

    def _run(self, cmd: List[str]) -> bool:
        """Run a terraform command"""
        try:
            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(
                ['terraform'] + cmd,
                cwd=self.working_dir,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            logger.error(f"Command failed: {e.stderr}")
            return False
        except FileNotFoundError:
            logger.error("terraform executable not found")
            return False

    def init(self) -> bool:
        """Run terraform init"""
        return self._run(['init'])

    def plan(self, out: str = "tfplan") -> bool:
        """Run terraform plan"""
        return self._run(['plan', '-out', out])

    def apply(self, plan: Optional[str] = None) -> bool:
        """Run terraform apply"""
        cmd = ['apply', '-auto-approve']
        if plan:
            cmd.append(plan)
        return self._run(cmd)

    def destroy(self) -> bool:
        """Run terraform destroy"""
        return self._run(['destroy', '-auto-approve'])

if __name__ == "__main__":
    tf = TerraformWrapper(".")
    if tf.init():
        tf.plan()
