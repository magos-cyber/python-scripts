#!/usr/bin/env python3
"""
service_health_checker.py — Check health of services (HTTP, TCP, Docker) and send alerts
Monitors HTTP endpoints, TCP ports, and Docker containers. Sends Telegram alerts on failure.
"""

import json
import socket
import urllib.request
import urllib.error
import urllib.parse
import logging
import os
from datetime import datetime
from pathlib import Path
import time

# Configuration
CONFIG = {
    "telegram": {
        "enabled": False,
        "bot_token": "YOUR_BOT_TOKEN",
        "chat_id": "YOUR_CHAT_ID"
    },
    "check_interval": 60,  # seconds (if run in loop, but default is one-shot)
    "services": [
        # Example HTTP service
        # {
        #     "name": "example.com",
        #     "type": "http",
        #     "url": "https://example.com",
        #     "timeout": 10,
        #     "expected_status": 200,
        #     "max_response_time": 5.0  # seconds
        # },
        # Example TCP service
        # {
        #     "name": "SSH on localhost",
        #     "type": "tcp",
        #     "host": "localhost",
        #     "port": 22,
        #         "timeout": 5
        # },
        # Example Docker service
        # {
        #     "name": "web_app",
        #     "type": "docker",
        #     "container_name": "web_app",
        #     "check_running": True
        # }
    ],
    "log_file": "/var/log/python-scripts/service-health-checker.log",
    "state_file": "/var/lib/python-scripts/service-health-checker-state.json"
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
    config_path = Path("/etc/python-scripts/service-health-checker.json")
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


def send_telegram_alert(message: str, config: dict):
    """Send alert via Telegram bot"""
    if not config["telegram"]["enabled"]:
        logger.info("Telegram alerts disabled")
        return

    url = f"https://api.telegram.org/bot{config['telegram']['bot_token']}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": config["telegram"]["chat_id"],
        "text": message,
        "parse_mode": "HTML"
    }).encode()

    try:
        req = urllib.request.Request(url, data=data)
        urllib.request.urlopen(req, timeout=10)
        logger.info("Telegram alert sent")
    except Exception as e:
        logger.error(f"Telegram alert failed: {e}")


def check_http_service(service: dict) -> tuple[bool, str]:
    """Check an HTTP service"""
    name = service.get("name", "Unnamed HTTP service")
    url = service.get("url")
    timeout = service.get("timeout", 10)
    expected_status = service.get("expected_status", 200)
    max_response_time = service.get("max_response_time")  # optional

    if not url:
        return False, f"HTTP service '{name}' missing 'url'"

    start_time = time.time()
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            status = response.status
            elapsed = time.time() - start_time

            if status != expected_status:
                return False, f"HTTP {name}: expected status {expected_status}, got {status}"

            if max_response_time is not None and elapsed > max_response_time:
                return False, f"HTTP {name}: response time {elapsed:.2f}s exceeds max {max_response_time}s"

            return True, f"HTTP {name}: OK (status {status}, response {elapsed:.2f}s)"
    except urllib.error.HTTPError as e:
        elapsed = time.time() - start_time
        return False, f"HTTP {name}: HTTP error {e.code} {e.reason} (after {elapsed:.2f}s)"
    except urllib.error.URLError as e:
        elapsed = time.time() - start_time
        return False, f"HTTP {name}: URL error {e.reason} (after {elapsed:.2f}s)"
    except Exception as e:
        elapsed = time.time() - start_time
        return False, f"HTTP {name}: unexpected error {e} (after {elapsed:.2f}s)"


def check_tcp_service(service: dict) -> tuple[bool, str]:
    """Check a TCP service"""
    name = service.get("name", "Unnamed TCP service")
    host = service.get("host")
    port = service.get("port")
    timeout = service.get("timeout", 5)

    if not host or port is None:
        return False, f"TCP service '{name}' missing 'host' or 'port'"

    start_time = time.time()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            elapsed = time.time() - start_time
            return True, f"TCP {name}: OK (connected to {host}:{port} in {elapsed:.2f}s)"
    except socket.timeout:
        elapsed = time.time() - start_time
        return False, f"TCP {name}: connection timeout to {host}:{port} (after {elapsed:.2f}s)"
    except socket.error as e:
        elapsed = time.time() - start_time
        return False, f"TCP {name}: connection error to {host}:{port}: {e} (after {elapsed:.2f}s)"
    except Exception as e:
        elapsed = time.time() - start_time
        return False, f"TCP {name}: unexpected error {e} (after {elapsed:.2f}s)"


def check_docker_service(service: dict) -> tuple[bool, str]:
    """Check a Docker container"""
    name = service.get("name", "Unnamed Docker service")
    container_name = service.get("container_name")
    check_running = service.get("check_running", True)

    if not container_name:
        return False, f"Docker service '{name}' missing 'container_name'"

    try:
        import socket as sock
        socket_path = "/var/run/docker.sock"
        if not os.path.exists(socket_path):
            return False, f"Docker service '{name}': Docker socket not found at {socket_path}"

        # Connect to Docker socket
        s = sock.socket(sock.AF_UNIX, sock.SOCK_STREAM)
        s.connect(socket_path)
        s.settimeout(5)

        # Request container info by name
        request = f"GET /containers/json?name={urllib.parse.quote(container_name)} HTTP/1.0\r\n\r\n"
        s.sendall(request.encode())

        response = b""
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            response += chunk
        s.close()

        # Parse HTTP response
        if b"\r\n\r\n" not in response:
            return False, f"Docker service '{name}': malformed response from Docker API"
        body = response.split(b"\r\n\r\n", 1)[1]

        try:
            containers = json.loads(body.decode())
        except json.JSONDecodeError:
            return False, f"Docker service '{name}': invalid JSON response from Docker API"

        if not containers:
            return False, f"Docker service '{name}': container '{container_name}' not found"

        container = containers[0]
        state = container.get("State", "")
        status = container.get("Status", "")

        if check_running and state != "running":
            return False, f"Docker {name}: container is {state} (expected running)"
        elif not check_running and state == "running":
            return False, f"Docker {name}: container is running (expected not running)"

        return True, f"Docker {name}: OK (state: {state}, status: {status})"
    except Exception as e:
        return False, f"Docker {name}: error checking container: {e}"


def load_state(state_file: str) -> dict:
    """Load previous state to avoid duplicate alerts"""
    try:
        with open(state_file) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_state(state: dict, state_file: str):
    """Save current state"""
    os.makedirs(os.path.dirname(state_file), exist_ok=True)
    with open(state_file, "w") as f:
        json.dump(state, f, indent=2)


def main():
    config = load_config()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    alerts = []
    status_lines = []
    state = load_state(config["state_file"])
    new_state = {}

    logger.info(f"Starting health check at {timestamp}")

    for service in config["services"]:
        service_type = service.get("type", "").lower()
        service_name = service.get("name", "Unnamed service")

        if service_type == "http":
            success, message = check_http_service(service)
        elif service_type == "tcp":
            success, message = check_tcp_service(service)
        elif service_type == "docker":
            success, message = check_docker_service(service)
        else:
            success, message = False, f"Unknown service type '{service_type}' for service '{service_name}'"

        # Determine status for logging and state
        if success:
            status_lines.append(f"[GREEN] {message}")
            new_state[service_name] = "up"
        else:
            status_lines.append(f"[RED] {message}")
            new_state[service_name] = "down"
            alerts.append(f"[RED] <b>Service Down</b>: {message}")

        logger.info(message)

    # Build report
    report = f"[HEALTH] <b>Service Health Check</b> - {timestamp}\\n\\n" + "\\n".join(status_lines)
    logger.info(f"\\n{report.replace('<b>', '').replace('</b>', '')}")

    # Send alerts if any
    if alerts:
        alert_msg = f"[ALERT] <b>Service Alert!</b>\\n\\n" + "\\n\\n".join(alerts)
        send_telegram_alert(alert_msg, config)

    # Save state
    save_state(new_state, config["state_file"])


if __name__ == "__main__":
    main()