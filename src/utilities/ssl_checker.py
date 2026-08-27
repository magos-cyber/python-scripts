#!/usr/bin/env python3
"""
ssl_checker.py — Check SSL certificate expiration dates
Monitors domains and sends alerts when certificates are about to expire
"""

import ssl
import socket
import argparse
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class SSLChecker:
    """Check SSL certificates for domains"""
    
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
    
    def get_cert_info(self, domain: str, port: int = 443) -> Optional[Dict]:
        """Get SSL certificate information"""
        try:
            context = ssl.create_default_context()
            with socket.create_connection((domain, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=domain) as ssock:
                    cert = ssock.getpeercert()
                    
                    # Parse dates
                    not_before = datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    
                    # Calculate days until expiration
                    days_until_expiry = (not_after - datetime.utcnow()).days
                    
                    # Get subject
                    subject = dict(x[0] for x in cert['subject'])
                    issuer = dict(x[0] for x in cert['issuer'])
                    
                    # Get SANs
                    san = cert.get('subjectAltName', [])
                    domains = [d[1] for d in san if d[0] == 'DNS']
                    
                    return {
                        "domain": domain,
                        "subject": subject.get('commonName', 'Unknown'),
                        "issuer": issuer.get('organizationName', 'Unknown'),
                        "not_before": not_before.strftime('%Y-%m-%d'),
                        "not_after": not_after.strftime('%Y-%m-%d'),
                        "days_until_expiry": days_until_expiry,
                        "san": domains,
                        "serial_number": cert.get('serialNumber', 'Unknown')
                    }
        except Exception as e:
            logger.error(f"SSL check failed for {domain}: {e}")
            return None
    
    def check_expiration(self, domain: str, warning_days: int = 30, critical_days: int = 7) -> Dict:
        """Check if certificate is expiring soon"""
        cert_info = self.get_cert_info(domain)
        
        if not cert_info:
            return {"domain": domain, "status": "error", "message": "Could not retrieve certificate"}
        
        days = cert_info["days_until_expiry"]
        
        if days <= critical_days:
            status = "critical"
            emoji = "🔴"
        elif days <= warning_days:
            status = "warning"
            emoji = "🟡"
        elif days < 0:
            status = "expired"
            emoji = "❌"
        else:
            status = "ok"
            emoji = "🟢"
        
        return {
            "domain": domain,
            "status": status,
            "emoji": emoji,
            "days_until_expiry": days,
            "expires": cert_info["not_after"],
            "issuer": cert_info["issuer"]
        }
    
    def check_multiple(self, domains: list, warning_days: int = 30) -> list:
        """Check multiple domains"""
        results = []
        for domain in domains:
            result = self.check_expiration(domain, warning_days)
            results.append(result)
        return results


def main():
    parser = argparse.ArgumentParser(description="SSL Certificate Checker")
    parser.add_argument("domains", nargs="+", help="Domains to check")
    parser.add_argument("--warning", type=int, default=30, help="Warning threshold (days)")
    parser.add_argument("--critical", type=int, default=7, help="Critical threshold (days)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    checker = SSLChecker()
    results = checker.check_multiple(args.domains, args.warning)
    
    if args.json:
        import json
        print(json.dumps(results, indent=2))
    else:
        print(f"🔒 SSL Certificate Check")
        print(f"{'='*50}")
        for r in results:
            status_emoji = r.get("emoji", "❓")
            domain = r["domain"]
            
            if r["status"] == "error":
                print(f"{status_emoji} {domain}: {r['message']}")
            else:
                days = r["days_until_expiry"]
                expires = r["expires"]
                issuer = r["issuer"]
                print(f"{status_emoji} {domain}: {days} days ({expires}) - {issuer}")


if __name__ == "__main__":
    main()