#!/usr/bin/env python3
"""SSL Certificate Checker - Checks SSL certificate expiration."""

import ssl
import socket
from datetime import datetime
import sys

def check_ssl(hostname, port=443):
    """Check SSL certificate for a hostname."""
    context = ssl.create_default_context()
    try:
        with socket.create_connection((hostname, port), timeout=5) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                cert = ssock.getpeercert()
                expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z")
                remaining = expires - datetime.now()
                
                print(f"Host: {hostname}:{port}")
                print(f"Subject: {dict(x[0] for x in cert['subject'])}")
                print(f"Issuer: {dict(x[0] for x in cert['issuer'])}")
                print(f"Expires: {expires}")
                print(f"Days remaining: {remaining.days}")
                
                if remaining.days <= 0:
                    print("Status: EXPIRED")
                elif remaining.days <= 7:
                    print("Status: CRITICAL")
                elif remaining.days <= 30:
                    print("Status: WARNING")
                else:
                    print("Status: OK")
    except Exception as e:
        print(f"Error checking {hostname}: {e}")

if __name__ == "__main__":
    for host in sys.argv[1:]:
        check_ssl(host)
        print()
