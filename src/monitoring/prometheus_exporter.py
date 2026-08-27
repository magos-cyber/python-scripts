#!/usr/bin/env python3
"""
prometheus_exporter.py — Custom Prometheus exporter for homelab metrics
"""

import http.server
import socketserver
import time
import random
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

class MetricsHandler(http.server.BaseHTTPRequestHandler):
    """Serve metrics for Prometheus"""
    
    def do_GET(self):
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            
            # Simulated metrics
            metrics = [
                f'homelab_cpu_usage_percent {random.uniform(0, 100):.2f}',
                f'homelab_memory_usage_bytes {random.randint(1000, 9999999)}',
                f'homelab_disk_free_bytes {random.randint(1000000, 99999999)}'
            ]
            
            for metric in metrics:
                self.wfile.write(f"{metric}\n".encode())
        else:
            self.send_response(404)
            self.end_headers()

def run_exporter(port: int = 8000):
    """Start the exporter"""
    with socketserver.TCPServer(("", port), MetricsHandler) as httpd:
        logger.info(f"Prometheus exporter running on port {port}")
        httpd.serve_forever()

if __name__ == "__main__":
    run_exporter()
