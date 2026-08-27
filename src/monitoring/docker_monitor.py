#!/usr/bin/env python3
"""
docker_monitor.py — Monitor Docker containers and send alerts
Tracks container status, resource usage, and restart events
"""

import json
import urllib.parse
import urllib.request
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class DockerMonitor:
    """Monitor Docker containers via Unix socket"""
    
    def __init__(self, socket_path: str = "/var/run/docker.sock"):
        self.socket_path = socket_path
        self.base_url = "http://localhost/v1.43"
    
    def _request(self, endpoint: str) -> Optional[dict]:
        """Make request to Docker socket"""
        import socket as sock
        
        try:
            s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
            s.connect(self.socket_path)
            s.settimeout(5)
            
            request = f"GET {endpoint} HTTP/1.0\r\n\r\n"
            s.sendall(request.encode())
            
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            s.close()
            
            # Parse HTTP response
            body = response.split(b"\r\n\r\n", 1)[1]
            return json.loads(body.decode())
        except Exception as e:
            logger.error(f"Docker API request failed: {e}")
            return None
    
    def list_containers(self, all_containers: bool = True) -> list:
        """List all containers"""
        result = self._request("/containers/json?all=true" if all_containers else "/containers/json")
        if isinstance(result, list):
            return result
        return []
    
    def get_container_stats(self, container_id: str) -> Optional[dict]:
        """Get container resource usage stats"""
        result = self._request(f"/containers/{container_id}/stats?stream=false")
        return result
    
    def get_container_logs(self, container_id: str, tail: int = 100) -> str:
        """Get recent container logs"""
        import socket as sock
        
        try:
            s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
            s.connect(self.socket_path)
            s.settimeout(5)
            
            request = f"GET /containers/{container_id}/logs?stdout=true&stderr=true&tail={tail} HTTP/1.0\r\n\r\n"
            s.sendall(request.encode())
            
            response = b""
            while True:
                chunk = s.recv(4096)
                if not chunk:
                    break
                response += chunk
            
            s.close()
            
            body = response.split(b"\r\n\r\n", 1)[1]
            # Docker logs have 8-byte header per frame, strip them
            logs = ""
            i = 0
            while i < len(body):
                if i + 8 <= len(body):
                    # Skip header (8 bytes)
                    logs += body[i+8:].split(b"\x00")[0].decode('utf-8', errors='replace')
                    break
            return logs
        except Exception as e:
            logger.error(f"Failed to get logs: {e}")
            return ""
    
    def check_health(self) -> list:
        """Check health status of all containers"""
        containers = self.list_containers()
        unhealthy = []
        
        for container in containers:
            name = container.get("Names", [""])[0].lstrip("/")
            state = container.get("State", "")
            status = container.get("Status", "")
            
            if state != "running":
                unhealthy.append({
                    "name": name,
                    "state": state,
                    "status": status,
                    "healthy": False
                })
            elif "unhealthy" in status.lower():
                unhealthy.append({
                    "name": name,
                    "state": state,
                    "status": status,
                    "healthy": False
                })
        
        return unhealthy
    
    def get_disk_usage(self) -> Optional[dict]:
        """Get Docker disk usage"""
        return self._request("/system/df")


def send_telegram(message: str, bot_token: str, chat_id: str):
    """Send Telegram notification"""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }).encode()
    
    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
    except Exception as e:
        logger.error(f"Telegram send failed: {e}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Docker Container Monitor")
    parser.add_argument("--telegram", action="store_true", help="Send alerts via Telegram")
    parser.add_argument("--bot-token", default="YOUR_BOT_TOKEN", help="Telegram bot token")
    parser.add_argument("--chat-id", default="YOUR_CHAT_ID", help="Telegram chat id")
    args = parser.parse_args()
    
    monitor = DockerMonitor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Check container health
    unhealthy = monitor.check_health()
    
    if unhealthy:
        message = f"[DOCKER] <b>Docker Alert</b> - {timestamp}\n\n"
        message += f"<b>{len(unhealthy)} container(s) unhealthy:</b>\n"
        for c in unhealthy:
            message += f"  [FAIL] {c['name']}: {c['state']} ({c['status']})\n"
        
        logger.warning(message.replace("<b>", "").replace("</b>", ""))
        
        if args.telegram:
            send_telegram(message, args.bot_token, args.chat_id)
    else:
        logger.info("All containers healthy")
    
    # Show disk usage
    disk = monitor.get_disk_usage()
    if disk:
        logger.info("Docker disk usage retrieved")


if __name__ == "__main__":
    main()