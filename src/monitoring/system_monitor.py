#!/usr/bin/env python3
"""
system_monitor.py — System resource monitor with Telegram alerts
Monitors CPU, memory, disk usage and sends alerts when thresholds are exceeded.
"""

import shutil
import os
import json
import urllib.request
import urllib.parse
import logging
from datetime import datetime
from pathlib import Path

# Configuration
CONFIG = {
    "telegram": {
        "enabled": False,
        "bot_token": "YOUR_BOT_TOKEN",
        "chat_id": "YOUR_CHAT_ID"
    },
    "thresholds": {
        "cpu_warning": 80,
        "cpu_critical": 95,
        "memory_warning": 80,
        "memory_critical": 95,
        "disk_warning": 80,
        "disk_critical": 90
    },
    "paths": ["/", "/home", "/var", "/opt"],
    "log_file": "/var/log/python-scripts/system-monitor.log",
    "state_file": "/var/lib/python-scripts/system-monitor-state.json"
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
    config_path = Path("/etc/python-scripts/system-monitor.json")
    if config_path.exists():
        with open(config_path) as f:
            return {**CONFIG, **json.load(f)}
    return CONFIG


def get_disk_usage(path: str) -> dict:
    """Get disk usage for a given path"""
    try:
        usage = shutil.disk_usage(path)
        return {
            "path": path,
            "total_gb": round(usage.total / (1024**3), 2),
            "used_gb": round(usage.used / (1024**3), 2),
            "free_gb": round(usage.free / (1024**3), 2),
            "percent": round((usage.used / usage.total) * 100, 1)
        }
    except Exception as e:
        logger.error(f"Error reading disk usage for {path}: {e}")
        return {"path": path, "error": str(e)}


def get_memory_usage() -> dict:
    """Get memory usage statistics"""
    try:
        with open('/proc/meminfo') as f:
            meminfo = f.read()
        
        mem_total = int(meminfo.split('MemTotal:')[1].split('kB')[0].strip()) / 1024 / 1024
        mem_available = int(meminfo.split('MemAvailable:')[1].split('kB')[0].strip()) / 1024 / 1024
        mem_used = mem_total - mem_available
        mem_percent = round((mem_used / mem_total) * 100, 1)
        
        return {
            "total_gb": round(mem_total, 2),
            "used_gb": round(mem_used, 2),
            "available_gb": round(mem_available, 2),
            "percent": mem_percent
        }
    except Exception as e:
        logger.error(f"Error reading memory usage: {e}")
        return {"error": str(e)}


def get_cpu_usage() -> float:
    """Get CPU usage percentage"""
    try:
        with open('/proc/stat') as f:
            cpu_line = f.readline()
        
        cpu_times = [int(x) for x in cpu_line.split()[1:]]
        idle = cpu_times[3]
        total = sum(cpu_times)
        
        # Wait a bit and read again for accurate measurement
        import time
        time.sleep(0.5)
        
        with open('/proc/stat') as f:
            cpu_line2 = f.readline()
        
        cpu_times2 = [int(x) for x in cpu_line2.split()[1:]]
        idle2 = cpu_times2[3]
        total2 = sum(cpu_times2)
        
        idle_delta = idle2 - idle
        total_delta = total2 - total
        
        cpu_percent = round(((total_delta - idle_delta) / total_delta) * 100, 1)
        return cpu_percent
    except Exception as e:
        logger.error(f"Error reading CPU usage: {e}")
        return 0.0


def send_telegram_alert(message: str, config: dict):
    """Send alert via Telegram bot"""
    if not config["telegram"]["enabled"]:
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

    # Check CPU
    cpu_percent = get_cpu_usage()
    if cpu_percent >= config["thresholds"]["cpu_critical"]:
        status_lines.append(f"[RED] CPU: {cpu_percent}% (CRITICAL)")
        alerts.append(f"[RED] <b>CPU CRITICAL</b>: {cpu_percent}%")
        new_state["cpu"] = "critical"
    elif cpu_percent >= config["thresholds"]["cpu_warning"]:
        status_lines.append(f"[YELLOW] CPU: {cpu_percent}% (WARNING)")
        alerts.append(f"[YELLOW] <b>CPU WARNING</b>: {cpu_percent}%")
        new_state["cpu"] = "warning"
    else:
        status_lines.append(f"[GREEN] CPU: {cpu_percent}%")
        new_state["cpu"] = "ok"

    # Check Memory
    memory = get_memory_usage()
    if "error" not in memory:
        if memory["percent"] >= config["thresholds"]["memory_critical"]:
            status_lines.append(f"[RED] Memory: {memory['percent']}% (CRITICAL)")
            alerts.append(f"[RED] <b>MEMORY CRITICAL</b>: {memory['percent']}% ({memory['used_gb']}/{memory['total_gb']}GB)")
            new_state["memory"] = "critical"
        elif memory["percent"] >= config["thresholds"]["memory_warning"]:
            status_lines.append(f"[YELLOW] Memory: {memory['percent']}% (WARNING)")
            alerts.append(f"[YELLOW] <b>MEMORY WARNING</b>: {memory['percent']}% ({memory['used_gb']}/{memory['total_gb']}GB)")
            new_state["memory"] = "warning"
        else:
            status_lines.append(f"[GREEN] Memory: {memory['percent']}%")
            new_state["memory"] = "ok"

    # Check Disk
    for path in config["paths"]:
        if not os.path.exists(path):
            continue
        usage = get_disk_usage(path)
        if "error" in usage:
            continue
        
        if usage["percent"] >= config["thresholds"]["disk_critical"]:
            status_lines.append(f"[RED] Disk {path}: {usage['percent']}% (CRITICAL)")
            alerts.append(f"[RED] <b>DISK CRITICAL</b> - {path}: {usage['percent']}% ({usage['free_gb']}GB free)")
            new_state[f"disk_{path}"] = "critical"
        elif usage["percent"] >= config["thresholds"]["disk_warning"]:
            status_lines.append(f"[YELLOW] Disk {path}: {usage['percent']}% (WARNING)")
            alerts.append(f"[YELLOW] <b>DISK WARNING</b> - {path}: {usage['percent']}% ({usage['free_gb']}GB free)")
            new_state[f"disk_{path}"] = "warning"
        else:
            status_lines.append(f"[GREEN] Disk {path}: {usage['percent']}%")
            new_state[f"disk_{path}"] = "ok"

    # Build report
    report = f"[CHART] <b>System Monitor</b> - {timestamp}\n\n" + "\n".join(status_lines)
    logger.info(f"\n{report.replace('<b>', '').replace('</b>', '')}")

    # Send alerts if any
    if alerts:
        alert_msg = f"[ALERT] <b>System Alert!</b>\n\n" + "\n\n".join(alerts)
        send_telegram_alert(alert_msg, config)

    # Save state
    save_state(new_state, config["state_file"])


if __name__ == "__main__":
    main()