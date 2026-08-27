#!/usr/bin/env python3
"""
speedtest.py — Internet speed test using speedtest.net
Measures download, upload, and ping with optional Telegram reporting
"""

import urllib.request
import urllib.parse
import json
import time
import logging
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class SpeedTest:
    """Simple speed test using speedtest.net"""
    
    def __init__(self):
        self.servers = []
        self.best_server = None
    
    def get_servers(self) -> list:
        """Get list of speedtest servers"""
        try:
            url = "https://www.speedtest.net/api/js/servers?engine=js&limit=5&https_functional=true"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                self.servers = json.loads(resp.read().decode())
            return self.servers
        except Exception as e:
            logger.error(f"Failed to get servers: {e}")
            return []
    
    def select_best_server(self) -> Optional[dict]:
        """Select best server (closest)"""
        if not self.servers:
            self.get_servers()
        
        if self.servers:
            self.best_server = self.servers[0]
            return self.best_server
        return None
    
    def measure_ping(self) -> float:
        """Measure ping to best server"""
        if not self.best_server:
            self.select_best_server()
        
        if not self.best_server:
            return 0.0
        
        host = self.best_server.get("host", "")
        try:
            import socket
            start = time.time()
            sock = socket.create_connection((host.split(":")[0], int(host.split(":")[1])), timeout=5)
            sock.close()
            return round((time.time() - start) * 1000, 2)
        except Exception:
            return 0.0
    
    def measure_download(self, duration: int = 5) -> float:
        """Measure download speed in Mbps"""
        test_url = "https://speed.hetzner.de/10MB.bin"
        
        try:
            start = time.time()
            req = urllib.request.Request(test_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=duration + 5) as resp:
                downloaded = 0
                while time.time() - start < duration:
                    chunk = resp.read(8192)
                    if not chunk:
                        break
                    downloaded += len(chunk)
            
            elapsed = time.time() - start
            speed_mbps = (downloaded * 8) / (elapsed * 1_000_000)
            return round(speed_mbps, 2)
        except Exception as e:
            logger.error(f"Download test failed: {e}")
            return 0.0
    
    def measure_upload(self, duration: int = 5) -> float:
        """Measure upload speed in Mbps"""
        test_url = "https://speed.hetzner.de/10MB.bin"
        
        try:
            data = b"0" * (1024 * 1024)  # 1MB chunks
            start = time.time()
            uploaded = 0
            
            while time.time() - start < duration:
                req = urllib.request.Request(test_url, data=data, method="POST", headers={"User-Agent": "Mozilla/5.0"})
                try:
                    urllib.request.urlopen(req, timeout=5)
                    uploaded += len(data)
                except Exception:
                    break
            
            elapsed = time.time() - start
            speed_mbps = (uploaded * 8) / (elapsed * 1_000_000)
            return round(speed_mbps, 2)
        except Exception as e:
            logger.error(f"Upload test failed: {e}")
            return 0.0
    
    def run_test(self) -> Dict:
        """Run full speed test"""
        logger.info("Starting speed test...")
        
        self.get_servers()
        self.select_best_server()
        
        ping = self.measure_ping()
        logger.info(f"Ping: {ping}ms")
        
        download = self.measure_download()
        logger.info(f"Download: {download} Mbps")
        
        upload = self.measure_upload()
        logger.info(f"Upload: {upload} Mbps")
        
        return {
            "ping_ms": ping,
            "download_mbps": download,
            "upload_mbps": upload,
            "server": self.best_server.get("name", "Unknown") if self.best_server else "Unknown"
        }


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Internet Speed Test")
    parser.add_argument("--telegram", action="store_true", help="Send results via Telegram")
    parser.add_argument("--bot-token", default="YOUR_BOT_TOKEN", help="Telegram bot token")
    parser.add_argument("--chat-id", default="YOUR_CHAT_ID", help="Telegram chat id")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    st = SpeedTest()
    results = st.run_test()
    
    if args.json:
        print(json.dumps(results, indent=2))
    else:
        print(f"🚀 Speed Test Results")
        print(f"{'='*40}")
        print(f"Server: {results['server']}")
        print(f"Ping: {results['ping_ms']}ms")
        print(f"Download: {results['download_mbps']} Mbps")
        print(f"Upload: {results['upload_mbps']} Mbps")
    
    if args.telegram:
        message = f"🚀 <b>Speed Test</b>\n\n"
        message += f"Server: {results['server']}\n"
        message += f"Ping: {results['ping_ms']}ms\n"
        message += f"Download: {results['download_mbps']} Mbps\n"
        message += f"Upload: {results['upload_mbps']} Mbps"
        
        url = f"https://api.telegram.org/bot{args.bot_token}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": args.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }).encode()
        
        try:
            req = urllib.request.Request(url, data=data)
            urllib.request.urlopen(req, timeout=10)
        except Exception as e:
            logger.error(f"Telegram send failed: {e}")


if __name__ == "__main__":
    main()