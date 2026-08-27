#!/usr/bin/env python3
"""
notification_dispatcher.py — Unified notification system for Telegram, Discord, Slack, and Email
Sends notifications via multiple channels with a simple interface.
"""

import json
import smtplib
import ssl
import urllib.request
import urllib.parse
import urllib.error
import logging
import os
from datetime import datetime
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Configuration
CONFIG = {
    "telegram": {
        "enabled": False,
        "bot_token": "YOUR_BOT_TOKEN",
        "chat_id": "YOUR_CHAT_ID"
    },
    "discord": {
        "enabled": False,
        "webhook_url": "YOUR_DISCORD_WEBHOOK_URL"
    },
    "slack": {
        "enabled": False,
        "webhook_url": "YOUR_SLACK_WEBHOOK_URL"
    },
    "email": {
        "enabled": False,
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "username": "YOUR_EMAIL_USERNAME",
        "password": "YOUR_EMAIL_PASSWORD",
        "from_addr": "YOUR_EMAIL_FROM",
        "to_addrs": ["YOUR_EMAIL_TO"],
        "use_tls": True
    },
    "log_file": "/var/log/python-scripts/notification-dispatcher.log",
    "state_file": "/var/lib/python-scripts/notification-dispatcher-state.json"
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler(CONFIG["log_file"]) if os.path.exists(os.path.dirname(CONFIG["log_file"])) else logging.NullHandler(),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def load_config():
    """Load config from file if exists"""
    config_path = Path("/etc/python-scripts/notification-dispatcher.json")
    if config_path.exists():
        try:
            with open(config_path) as f:
                user_config = json.load(f)
            # Update CONFIG with user config (shallow merge for simplicity)
            for key, value in user_config.items():
                if key in CONFIG:
                    if isinstance(CONFIG[key], dict) and isinstance(value, dict):
                        CONFIG[key].update(value)
                    else:
                        CONFIG[key] = value
                else:
                    CONFIG[key] = value
            logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            logger.error(f"Error loading config from {config_path}: {e}")
    return CONFIG


def send_telegram(message: str, config: dict):
    """Send notification via Telegram bot"""
    if not config["telegram"]["enabled"]:
        logger.info("Telegram notifications disabled")
        return False

    url = f"https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": config["telegram"]["chat_id"],
        "text": message,
        "parse_mode": "HTML"
    }).encode()

    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        logger.info("Telegram notification sent")
        return True
    except Exception as e:
        logger.error(f"Telegram notification failed: {e}")
        return False


def send_discord(message: str, config: dict):
    """Send notification via Discord webhook"""
    if not config["discord"]["enabled"]:
        logger.info("Discord notifications disabled")
        return False

    webhook_url = config["discord"]["webhook_url"]
    if not webhook_url or webhook_url == "YOUR_DISCORD_WEBHOOK_URL":
        logger.error("Discord webhook URL not configured")
        return False

    # Discord expects JSON payload
    data = json.dumps({
        "content": message
    }).encode('utf-8')

    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        urllib.request.urlopen(req, timeout=10)
        logger.info("Discord notification sent")
        return True
    except Exception as e:
        logger.error(f"Discord notification failed: {e}")
        return False


def send_slack(message: str, config: dict):
    """Send notification via Slack webhook"""
    if not config["slack"]["enabled"]:
        logger.info("Slack notifications disabled")
        return False

    webhook_url = config["slack"]["webhook_url"]
    if not webhook_url or webhook_url == "YOUR_SLACK_WEBHOOK_URL":
        logger.error("Slack webhook URL not configured")
        return False

    # Slack expects JSON payload
    data = json.dumps({
        "text": message
    }).encode('utf-8')

    req = urllib.request.Request(
        webhook_url,
        data=data,
        headers={'Content-Type': 'application/json'}
    )

    try:
        urllib.request.urlopen(req, timeout=10)
        logger.info("Slack notification sent")
        return True
    except Exception as e:
        logger.error(f"Slack notification failed: {e}")
        return False


def send_email(message: str, config: dict, subject: str = "Notification"):
    """Send notification via email"""
    if not config["email"]["enabled"]:
        logger.info("Email notifications disabled")
        return False

    smtp_server = config["email"]["smtp_server"]
    smtp_port = config["email"]["smtp_port"]
    username = config["email"]["username"]
    password = config["email"]["password"]
    from_addr = config["email"]["from_addr"]
    to_addrs = config["email"]["to_addrs"]
    use_tls = config["email"]["use_tls"]

    if not all([smtp_server, smtp_port, username, password, from_addr, to_addrs]):
        logger.error("Email configuration incomplete")
        return False

    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_addr
    msg['To'] = ", ".join(to_addrs)
    msg['Subject'] = subject

    # Add body
    msg.attach(MIMEText(message, 'plain'))

    text = msg.as_string()

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls(context=context)
            server.login(username, password)
            server.sendmail(from_addr, to_addrs, text)
        logger.info("Email notification sent")
        return True
    except Exception as e:
        logger.error(f"Email notification failed: {e}")
        return False


def send_notification(message: str, config: dict = None, subject: str = "Notification") -> dict:
    """
    Send notification via all enabled channels.
    Returns a dictionary with channel names as keys and boolean success as values.
    """
    if config is None:
        config = load_config()

    results = {
        "telegram": False,
        "discord": False,
        "slack": False,
        "email": False
    }

    # Send via each channel
    results["telegram"] = send_telegram(message, config)
    results["discord"] = send_discord(message, config)
    results["slack"] = send_slack(message, config)
    results["email"] = send_email(message, config, subject)

    # Log summary
    successful = [k for k, v in results.items() if v]
    failed = [k for k, v in results.items() if not v]
    if successful:
        logger.info(f"Notifications sent via: {', '.join(successful)}")
    if failed:
        logger.warning(f"Notifications failed via: {', '.join(failed)}")

    return results


def main():
    """Command line interface for testing"""
    import argparse

    parser = argparse.ArgumentParser(description="Send a notification via enabled channels")
    parser.add_argument("message", help="Message to send")
    parser.add_argument("--subject", default="Notification", help="Email subject (if email enabled)")
    parser.add_argument("--config", help="Path to config file (JSON)")
    args = parser.parse_args()

    config = load_config()
    if args.config:
        config_path = Path(args.config)
        if config_path.exists():
            with open(config_path) as f:
                user_config = json.load(f)
            # Update CONFIG with user config (shallow merge)
            for key, value in user_config.items():
                if key in CONFIG:
                    if isinstance(CONFIG[key], dict) and isinstance(value, dict):
                        CONFIG[key].update(value)
                    else:
                        CONFIG[key] = value
                else:
                    CONFIG[key] = value
            config = CONFIG
            logger.info(f"Loaded additional configuration from {args.config}")

    results = send_notification(args.message, config, args.subject)
    print(f"Notification results: {json.dumps(results, indent=2)}")


if __name__ == "__main__":
    main()