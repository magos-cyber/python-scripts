#!/usr/bin/env python3
"""
kubernetes_client.py — K8s API client for pod/service management
"""

import urllib.request
import urllib.error
import json
import logging
import os
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class K8sClient:
    """Minimal K8s client using standard API token"""

    def __init__(self, api_server: str, token_path: str = "/var/run/secrets/kubernetes.io/serviceaccount/token"):
        self.api_server = api_server
        self.token = self._load_token(token_path)

    def _load_token(self, path: str) -> str:
        if os.path.exists(path):
            with open(path, 'r') as f:
                return f.read().strip()
        return ""

    def _request(self, method: str, path: str) -> Optional[dict]:
        url = f"{self.api_server}{path}"
        headers = {"Authorization": f"Bearer {self.token}"}
        req = urllib.request.Request(url, headers=headers, method=method)
        
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                return json.loads(response.read().decode())
        except Exception as e:
            logger.error(f"K8s request failed: {e}")
            return None

    def list_pods(self, namespace: str = "default") -> list:
        """List pods in namespace"""
        data = self._request("GET", f"/api/v1/namespaces/{namespace}/pods")
        return data.get("items", []) if data else []

if __name__ == "__main__":
    # Example
    client = K8sClient("https://kubernetes.default.svc")
    pods = client.list_pods()
    print(f"Found {len(pods)} pods")
