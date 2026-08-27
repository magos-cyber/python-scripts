#!/usr/bin/env python3
"""
github_backup.py — Backup GitHub repositories
Clones all repositories for a user/org with optional private repo support
"""

import urllib.request
import json
import os
import subprocess
import argparse
import logging
from pathlib import Path
from typing import Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class GitHubBackup:
    """Backup GitHub repositories"""
    
    def __init__(self, token: Optional[str] = None):
        self.token = token
        self.base_url = "https://api.github.com"
    
    def _request(self, endpoint: str) -> Optional[list]:
        """Make GitHub API request"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            headers = {"User-Agent": "python-github-backup"}
            if self.token:
                headers["Authorization"] = f"token {self.token}"
            
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return None
    
    def get_user_repos(self, username: str) -> List[dict]:
        """Get all repositories for a user"""
        repos = []
        page = 1
        
        while True:
            result = self._request(f"/users/{username}/repos?per_page=100&page={page}")
            if not result:
                break
            repos.extend(result)
            if len(result) < 100:
                break
            page += 1
        
        return repos
    
    def get_org_repos(self, org: str) -> List[dict]:
        """Get all repositories for an organization"""
        repos = []
        page = 1
        
        while True:
            result = self._request(f"/orgs/{org}/repos?per_page=100&page={page}")
            if not result:
                break
            repos.extend(result)
            if len(result) < 100:
                break
            page += 1
        
        return repos
    
    def backup_repo(self, repo: dict, backup_dir: Path, use_ssh: bool = False) -> bool:
        """Clone or update a repository"""
        name = repo["name"]
        full_name = repo["full_name"]
        
        if use_ssh:
            clone_url = repo.get("ssh_url", "")
        else:
            clone_url = repo.get("clone_url", "")
        
        if not clone_url:
            return False
        
        repo_dir = backup_dir / name
        
        try:
            if repo_dir.exists():
                # Update existing repo
                logger.info(f"Updating {full_name}...")
                subprocess.run(
                    ["git", "pull"],
                    cwd=repo_dir,
                    capture_output=True,
                    timeout=120
                )
            else:
                # Clone new repo
                logger.info(f"Cloning {full_name}...")
                subprocess.run(
                    ["git", "clone", "--mirror", clone_url, str(repo_dir)],
                    capture_output=True,
                    timeout=300
                )
            
            return True
        except Exception as e:
            logger.error(f"Failed to backup {full_name}: {e}")
            return False
    
    def backup_all(self, backup_dir: str, username: Optional[str] = None, 
                   org: Optional[str] = None, use_ssh: bool = False,
                   include_forks: bool = False) -> dict:
        """Backup all repositories"""
        backup_path = Path(backup_dir)
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # Get repos
        if org:
            repos = self.get_org_repos(org)
        elif username:
            repos = self.get_user_repos(username)
        else:
            logger.error("No username or org specified")
            return {"success": 0, "failed": 0}
        
        # Filter forks
        if not include_forks:
            repos = [r for r in repos if not r.get("fork", False)]
        
        logger.info(f"Found {len(repos)} repositories to backup")
        
        success = 0
        failed = 0
        
        for repo in repos:
            if self.backup_repo(repo, backup_path, use_ssh):
                success += 1
            else:
                failed += 1
        
        return {"success": success, "failed": failed, "total": len(repos)}


def main():
    parser = argparse.ArgumentParser(description="GitHub Repository Backup")
    parser.add_argument("--user", help="GitHub username")
    parser.add_argument("--org", help="GitHub organization")
    parser.add_argument("--token", help="GitHub personal access token (for private repos)")
    parser.add_argument("--dir", default="./github-backup", help="Backup directory")
    parser.add_argument("--ssh", action="store_true", help="Use SSH for cloning")
    parser.add_argument("--forks", action="store_true", help="Include forked repos")
    args = parser.parse_args()
    
    backup = GitHubBackup(args.token)
    results = backup.backup_all(
        args.dir,
        username=args.user,
        org=args.org,
        use_ssh=args.ssh,
        include_forks=args.forks
    )
    
    print(f"\n[PACKAGE] Backup Complete")
    print(f"{'='*40}")
    print(f"Total: {results['total']}")
    print(f"Success: {results['success']}")
    print(f"Failed: {results['failed']}")


if __name__ == "__main__":
    main()