#!/usr/bin/env python3
"""Metrics Collector - Collects system metrics and exports to Prometheus format."""

import psutil
import time
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler

class MetricsHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/metrics':
            metrics = self.collect_metrics()
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(metrics.encode())
        else:
            self.send_response(404)
            self.end_headers()

    def collect_metrics(self):
        """Collect system metrics."""
        cpu = psutil.cpu_percent(interval=1)
        mem = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        net = psutil.net_io_counters()

        metrics = f"""# HELP system_cpu_percent CPU usage percent
# TYPE system_cpu_percent gauge
system_cpu_percent {cpu}
# HELP system_memory_percent Memory usage percent
# TYPE system_memory_percent gauge
system_memory_percent {mem.percent}
# HELP system_disk_percent Disk usage percent
# TYPE system_disk_percent gauge
system_disk_percent {disk.percent}
# HELP system_net_bytes_sent Network bytes sent
# TYPE system_net_bytes_sent counter
system_net_bytes_sent {net.bytes_sent}
# HELP system_net_bytes_recv Network bytes received
# TYPE system_net_bytes_recv counter
system_net_bytes_recv {net.bytes_recv}
"""
        return metrics

    def log_message(self, format, *args):
        pass  # Suppress logging

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9101
    server = HTTPServer(('0.0.0.0', port), MetricsHandler)
    print(f"Metrics server on port {port}")
    server.serve_forever()
