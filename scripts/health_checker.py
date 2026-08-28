#!/usr/bin/env python3
"""Health Checker - Monitors endpoints and services for availability."""

import requests
import smtplib
import time
from datetime import datetime
import sys

class HealthChecker:
    def __init__(self, endpoints, interval=60, alert_email=None):
        self.endpoints = endpoints
        self.interval = interval
        self.alert_email = alert_email
        self.failures = {}

    def check_endpoint(self, url, expected_status=200, timeout=5):
        """Check a single endpoint."""
        try:
            resp = requests.get(url, timeout=timeout)
            return resp.status_code == expected_status
        except requests.RequestException:
            return False

    def run(self):
        """Run health checks loop."""
        print(f"Starting health checker at {datetime.now()}")
        while True:
            for name, url in self.endpoints.items():
                ok = self.check_endpoint(url)
                if ok:
                    self.failures[name] = 0
                    print(f"[{datetime.now()}] OK: {name}")
                else:
                    self.failures[name] = self.failures.get(name, 0) + 1
                    print(f"[{datetime.now()}] FAIL: {name} (attempt {self.failures[name]})")
                    if self.failures[name] >= 3 and self.alert_email:
                        self.send_alert(name, url)
            time.sleep(self.interval)

    def send_alert(self, name, url):
        """Send alert email."""
        # Implement email alerting
        print(f"ALERT: {name} ({url}) is down!")

if __name__ == "__main__":
    endpoints = {
        "proxmox": "https://10.0.0.10:8006",
        "homeassistant": "https://10.0.0.162:8123",
        "grafana": "http://10.0.0.85:3000",
    }
    checker = HealthChecker(endpoints, interval=60)
    checker.run()
