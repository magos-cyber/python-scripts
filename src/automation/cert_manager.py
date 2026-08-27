#!/usr/bin/env python3
"""
cert_manager.py — Manage SSL certificates with Let's Encrypt
Handles certificate issuance, renewal, and deployment hooks
"""

import subprocess
import os
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class CertManager:
    """Manage Let's Encrypt certificates"""
    
    def __init__(self, email: str, staging: bool = False):
        self.email = email
        self.staging = staging
        self.cert_dir = Path("/etc/letsencrypt/live")
    
    def issue(self, domains: List[str], webroot: str = "/var/www/html") -> bool:
        """Issue a new certificate"""
        cmd = [
            "certbot", "certonly",
            "--non-interactive",
            "--agree-tos",
            "--email", self.email,
            "--webroot",
            "--webroot-path", webroot
        ]
        
        for domain in domains:
            cmd.extend(["-d", domain])
        
        if self.staging:
            cmd.append("--staging")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info(f"Certificate issued for {', '.join(domains)}")
                return True
            else:
                logger.error(f"Failed to issue certificate: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Certbot error: {e}")
            return False
    
    def renew(self, dry_run: bool = False) -> bool:
        """Renew all certificates"""
        cmd = ["certbot", "renew", "--non-interactive"]
        
        if dry_run:
            cmd.append("--dry-run")
        
        if self.staging:
            cmd.append("--staging")
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                logger.info("Certificate renewal successful")
                return True
            else:
                logger.error(f"Renewal failed: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Renewal error: {e}")
            return False
    
    def get_cert_info(self, domain: str) -> Optional[dict]:
        """Get certificate information"""
        cert_path = self.cert_dir / domain / "fullchain.pem"
        
        if not cert_path.exists():
            logger.error(f"Certificate not found for {domain}")
            return None
        
        try:
            cmd = [
                "openssl", "x509",
                "-in", str(cert_path),
                "-noout",
                "-dates", "-subject", "-issuer"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            info = {"domain": domain}
            for line in result.stdout.split("\n"):
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip().lower()
                    if key == "notbefore":
                        info["not_before"] = value.strip()
                    elif key == "notafter":
                        info["not_after"] = value.strip()
                    elif key == "subject":
                        info["subject"] = value.strip()
                    elif key == "issuer":
                        info["issuer"] = value.strip()
            
            return info
        except Exception as e:
            logger.error(f"Failed to get cert info: {e}")
            return None
    
    def list_certificates(self) -> List[str]:
        """List all certificates"""
        certs = []
        if self.cert_dir.exists():
            for d in self.cert_dir.iterdir():
                if d.is_dir():
                    certs.append(d.name)
        return certs
    
    def days_until_expiry(self, domain: str) -> Optional[int]:
        """Get days until certificate expires"""
        cert_path = self.cert_dir / domain / "fullchain.pem"
        
        if not cert_path.exists():
            return None
        
        try:
            cmd = [
                "openssl", "x509",
                "-in", str(cert_path),
                "-noout",
                "-enddate"
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            # Parse "notAfter=Dec 15 12:00:00 2024 GMT"
            date_str = result.stdout.split("=", 1)[1].strip()
            expiry = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
            
            return (expiry - datetime.utcnow()).days
        except Exception as e:
            logger.error(f"Failed to check expiry: {e}")
            return None


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="SSL Certificate Manager")
    parser.add_argument("--email", required=True, help="Contact email for Let's Encrypt")
    parser.add_argument("--staging", action="store_true", help="Use staging server")
    subparsers = parser.add_subparsers(dest="command")
    
    # Issue command
    issue_parser = subparsers.add_parser("issue", help="Issue new certificate")
    issue_parser.add_argument("--domains", required=True, help="Comma-separated domains")
    issue_parser.add_argument("--webroot", default="/var/www/html", help="Webroot path")
    
    # Renew command
    renew_parser = subparsers.add_parser("renew", help="Renew certificates")
    renew_parser.add_argument("--dry-run", action="store_true", help="Dry run")
    
    # List command
    subparsers.add_parser("list", help="List certificates")
    
    # Info command
    info_parser = subparsers.add_parser("info", help="Get certificate info")
    info_parser.add_argument("--domain", required=True, help="Domain name")
    
    args = parser.parse_args()
    
    manager = CertManager(args.email, args.staging)
    
    if args.command == "issue":
        domains = [d.strip() for d in args.domains.split(",")]
        manager.issue(domains, args.webroot)
    elif args.command == "renew":
        manager.renew(args.dry_run)
    elif args.command == "list":
        certs = manager.list_certificates()
        for cert in certs:
            days = manager.days_until_expiry(cert)
            status = f"({days} days)" if days else "(unknown)"
            print(f"  {cert} {status}")
    elif args.command == "info":
        info = manager.get_cert_info(args.domain)
        if info:
            for key, value in info.items():
                print(f"  {key}: {value}")


if __name__ == "__main__":
    main()