#!/usr/bin/env python3
"""
github_api.py — GitHub API wrapper
Manage repositories, issues, PRs, and user data via GitHub REST API
"""

import urllib.request
import urllib.parse
import json
import logging
from typing import Optional, Dict, List, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

API_BASE = "https://api.github.com"


class GitHubAPI:
    """GitHub API client"""
    
    def __init__(self, token: str, username: Optional[str] = None):
        self.token = token
        self.username = username
        self.headers = {
            "Authorization": f"token {token}",
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "python-github-api"
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make API request"""
        url = f"{API_BASE}{endpoint}"
        
        try:
            body = json.dumps(data).encode() if data else None
            req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                if resp.status == 204:  # No content
                    return {"success": True}
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            logger.error(f"API error {e.code}: {error_body}")
            return None
        except Exception as e:
            logger.error(f"Request failed: {e}")
            return None
    
    # User operations
    def get_user(self) -> Dict:
        """Get authenticated user info"""
        return self._request("GET", "/user") or {}
    
    def get_rate_limit(self) -> Dict:
        """Get API rate limit status"""
        return self._request("GET", "/rate_limit") or {}
    
    # Repository operations
    def list_repos(self, username: Optional[str] = None) -> List[Dict]:
        """List repositories for user or authenticated user"""
        user = username or self.username
        if user:
            result = self._request("GET", f"/users/{user}/repos?per_page=100")
        else:
            result = self._request("GET", "/user/repos?per_page=100")
        return result or []
    
    def get_repo(self, owner: str, repo: str) -> Dict:
        """Get repository details"""
        return self._request("GET", f"/repos/{owner}/{repo}") or {}
    
    def create_repo(self, name: str, description: str = "", private: bool = False, 
                    auto_init: bool = True) -> Dict:
        """Create a new repository"""
        data = {
            "name": name,
            "description": description,
            "private": private,
            "auto_init": auto_init,
            "license_template": "mit"
        }
        return self._request("POST", "/user/repos", data) or {}
    
    def delete_repo(self, owner: str, repo: str) -> bool:
        """Delete a repository"""
        result = self._request("DELETE", f"/repos/{owner}/{repo}")
        return result is not None
    
    def get_repo_languages(self, owner: str, repo: str) -> Dict:
        """Get languages used in repository"""
        return self._request("GET", f"/repos/{owner}/{repo}/languages") or {}
    
    def get_repo_commits(self, owner: str, repo: str, limit: int = 10) -> List[Dict]:
        """Get recent commits"""
        result = self._request("GET", f"/repos/{owner}/{repo}/commits?per_page={limit}")
        return result or []
    
    # Issues
    def list_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """List issues"""
        result = self._request("GET", f"/repos/{owner}/{repo}/issues?state={state}")
        return result or []
    
    def create_issue(self, owner: str, repo: str, title: str, body: str = "", 
                     labels: List[str] = None) -> Dict:
        """Create an issue"""
        data = {"title": title, "body": body}
        if labels:
            data["labels"] = labels
        return self._request("POST", f"/repos/{owner}/{repo}/issues", data) or {}
    
    def close_issue(self, owner: str, repo: str, issue_number: int) -> Dict:
        """Close an issue"""
        data = {"state": "closed"}
        return self._request("PATCH", f"/repos/{owner}/{repo}/issues/{issue_number}", data) or {}
    
    # Pull requests
    def list_prs(self, owner: str, repo: str, state: str = "open") -> List[Dict]:
        """List pull requests"""
        result = self._request("GET", f"/repos/{owner}/{repo}/pulls?state={state}")
        return result or []
    
    def create_pr(self, owner: str, repo: str, title: str, head: str, base: str, 
                  body: str = "") -> Dict:
        """Create a pull request"""
        data = {"title": title, "head": head, "base": base, "body": body}
        return self._request("POST", f"/repos/{owner}/{repo}/pulls", data) or {}
    
    # Stars
    def star_repo(self, owner: str, repo: str) -> bool:
        """Star a repository"""
        result = self._request("PUT", f"/user/starred/{owner}/{repo}")
        return result is not None
    
    def unstar_repo(self, owner: str, repo: str) -> bool:
        """Unstar a repository"""
        result = self._request("DELETE", f"/user/starred/{owner}/{repo}")
        return result is not None
    
    def list_starred(self) -> List[Dict]:
        """List starred repositories"""
        result = self._request("GET", "/user/starred?per_page=100")
        return result or []
    
    # Gists
    def create_gist(self, filename: str, content: str, description: str = "", 
                    public: bool = False) -> Dict:
        """Create a gist"""
        data = {
            "description": description,
            "public": public,
            "files": {filename: {"content": content}}
        }
        return self._request("POST", "/gists", data) or {}


def main():
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description="GitHub API CLI")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="GitHub token")
    parser.add_argument("command", choices=[
        "user", "repos", "rate", "create-repo", "delete-repo", "issues", "star", "gist"
    ])
    parser.add_argument("--owner", help="Repository owner")
    parser.add_argument("--repo", help="Repository name")
    parser.add_argument("--name", help="New repo/gist name")
    parser.add_argument("--desc", default="", help="Description")
    parser.add_argument("--private", action="store_true", help="Private repo")
    parser.add_argument("--file", help="File to upload as gist")
    parser.add_argument("--content", help="Gist content")
    args = parser.parse_args()
    
    if not args.token:
        print("GitHub token required (--token or GITHUB_TOKEN env)")
        return
    
    api = GitHubAPI(args.token)
    
    if args.command == "user":
        user = api.get_user()
        print(f"User: {user.get('login', 'N/A')}")
        print(f"Name: {user.get('name', 'N/A')}")
        print(f"Public repos: {user.get('public_repos', 0)}")
    
    elif args.command == "repos":
        repos = api.list_repos()
        for r in repos:
            print(f"{r['full_name']}: {r.get('description', 'N/A')}")
    
    elif args.command == "rate":
        rate = api.get_rate_limit()
        print(json.dumps(rate, indent=2))
    
    elif args.command == "create-repo":
        if not args.name:
            print("--name required")
            return
        result = api.create_repo(args.name, args.desc, args.private)
        if "full_name" in result:
            print(f"Created: {result['full_name']}")
        else:
            print("Failed to create repo")
    
    elif args.command == "delete-repo":
        if not args.owner or not args.repo:
            print("--owner and --repo required")
            return
        if api.delete_repo(args.owner, args.repo):
            print(f"Deleted {args.owner}/{args.repo}")
        else:
            print("Failed to delete repo")
    
    elif args.command == "issues":
        if not args.owner or not args.repo:
            print("--owner and --repo required")
            return
        issues = api.list_issues(args.owner, args.repo)
        for i in issues:
            print(f"#{i['number']}: {i['title']}")
    
    elif args.command == "star":
        if not args.owner or not args.repo:
            print("--owner and --repo required")
            return
        if api.star_repo(args.owner, args.repo):
            print(f"Starred {args.owner}/{args.repo}")
    
    elif args.command == "gist":
        if not args.file and not args.content:
            print("--file or --content required")
            return
        content = args.content or open(args.file).read()
        name = args.name or args.file or "gist.txt"
        result = api.create_gist(name, content, args.desc)
        if "html_url" in result:
            print(f"Gist created: {result['html_url']}")
        else:
            print("Failed to create gist")


if __name__ == "__main__":
    main()