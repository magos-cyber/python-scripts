#!/usr/bin/env python3
"""
port_scanner.py — Multi-threaded TCP port scanner
Scans common homelab ports with optional Telegram notifications
"""

import socket
import argparse
import urllib.parse
import urllib.request
import json
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Common homelab ports
COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 25: "SMTP", 53: "DNS",
    80: "HTTP", 110: "POP3", 143: "IMAP", 443: "HTTPS", 465: "SMTPS",
    587: "SMTP-Sub", 993: "IMAPS", 995: "POP3S", 3000: "Grafana",
    3001: "Uptime-Kuma", 3306: "MySQL", 4533: "Navidrome",
    51820: "WireGuard", 5432: "PostgreSQL", 8000: "Paperless-ngx",
    8080: "HTTP-Alt", 8096: "Jellyfin", 8123: "Home-Assistant",
    8443: "HTTPS-Alt", 9000: "Portainer", 9090: "Prometheus",
    9443: "Authentik-HTTPS"
}


class PortScanner:
    """Multi-threaded TCP port scanner"""
    
    def __init__(self, timeout: float = 0.5, max_workers: int = 100):
        self.timeout = timeout
        self.max_workers = max_workers
    
    def scan_port(self, host: str, port: int) -> tuple:
        """Scan a single port"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                result = s.connect_ex((host, port))
                if result == 0:
                    return (port, True)
                return (port, False)
        except Exception:
            return (port, False)
    
    def scan_host(self, host: str, ports: List[int]) -> Dict[int, bool]:
        """Scan multiple ports on a host"""
        results = {}
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(self.scan_port, host, port): port for port in ports}
            for future in as_completed(futures):
                port, is_open = future.result()
                results[port] = is_open
        return results
    
    def scan_network(self, network: str, ports: List[int]) -> Dict[str, Dict[int, bool]]:
        """Scan multiple hosts in a network"""
        import ipaddress
        results = {}
        net = ipaddress.ip_network(network, strict=False)
        
        for host in net.hosts():
            host_str = str(host)
            host_results = self.scan_host(host_str, ports)
            open_ports = {p: v for p, v in host_results.items() if v}
            if open_ports:
                results[host_str] = open_ports
        
        return results


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
    parser = argparse.ArgumentParser(description="Port Scanner")
    parser.add_argument("--host", help="Single host to scan")
    parser.add_argument("--network", help="Network to scan (CIDR)")
    parser.add_argument("--ports", default="common", help="Ports to scan (comma-separated or 'common')")
    parser.add_argument("--timeout", type=float, default=0.5, help="Connection timeout")
    parser.add_argument("--telegram", action="store_true", help="Send results via Telegram")
    parser.add_argument("--bot-token", default="YOUR_BOT_TOKEN", help="Telegram bot token")
    parser.add_argument("--chat-id", default="YOUR_CHAT_ID", help="Telegram chat id")
    args = parser.parse_args()
    
    scanner = PortScanner(timeout=args.timeout)
    
    # Determine ports to scan
    if args.ports == "common":
        ports = list(COMMON_PORTS.keys())
    else:
        ports = [int(p) for p in args.ports.split(",") if p.strip()]
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    results_text = f"[SEARCH] <b>Port Scan Results</b> - {timestamp}\n\n"
    
    if args.host:
        # Scan single host
        results = scanner.scan_host(args.host, ports)
        open_ports = {p: v for p, v in results.items() if v}
        
        results_text += f"<b>Host:</b> {args.host}\n"
        if open_ports:
            results_text += f"<b>Open ports:</b>\n"
            for port, _ in sorted(open_ports.items()):
                service = COMMON_PORTS.get(port, "unknown")
                results_text += f"  [OK] {port} ({service})\n"
        else:
            results_text += "No open ports found.\n"
    
    elif args.network:
        # Scan network
        network_results = scanner.scan_network(args.network, ports)
        
        results_text += f"<b>Network:</b> {args.network}\n"
        if network_results:
            for host, open_ports in sorted(network_results.items()):
                results_text += f"\n<b>{host}:</b>\n"
                for port, _ in sorted(open_ports.items()):
                    service = COMMON_PORTS.get(port, "unknown")
                    results_text += f"  [OK] {port} ({service})\n"
        else:
            results_text += "No hosts with open ports found.\n"
    
    print(results_text.replace("<b>", "").replace("</b>", ""))
    
    if args.telegram:
        send_telegram(results_text, args.bot_token, args.chat_id)


if __name__ == "__main__":
    main()