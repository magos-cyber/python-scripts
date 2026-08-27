# Python Scripts

Α collection of useful Python scripts organized by category — automation, monitoring, APIs, utilities. All scripts are standalone, well-documented, and ready to use.

## 📁 Structure

```
python-scripts/
├── src/
│   ├── automation/     # Backup manager, task automation
│   ├── monitoring/     # System monitoring with alerts
│   ├── api/            # Telegram bot, Home Assistant client
│   ├── network/        # Port scanner, network tools
│   ├── utilities/      # File organizer, misc tools
│   └── data/           # Data processing scripts
├── tests/              # Unit tests
├── config/             # Configuration files
└── docs/               # Documentation
```

## 🚀 Quick Start

```bash
# Clone the repo
git clone https://github.com/magos-cyber/python-scripts.git
cd python-scripts

# No external dependencies required! All scripts use Python stdlib only.
# Just run them directly:

# System Monitor
python3 src/monitoring/system_monitor.py

# Telegram Bot
python3 src/api/telegram_bot.py

# Home Assistant Client
python3 src/api/home_assistant.py

# Port Scanner
python3 src/network/port_scanner.py --host 192.168.1.1

# File Organizer
python3 src/utilities/file_organizer.py ~/Downloads --by type

# Backup Manager
python3 src/automation/backup_manager.py
```

## 📝 Contents

### 🔧 Automation
- **`src/automation/backup_manager.py`** — Automated backup manager with rotation, compression, and restore capabilities. Supports manifest tracking and integrity verification.

### 📊 Monitoring
- **`src/monitoring/system_monitor.py`** — System resource monitor (CPU, memory, disk) with Telegram alerts. State-aware to avoid duplicate notifications.

### 🤖 API Clients
- **`src/api/telegram_bot.py`** — Telegram Bot API wrapper. Send messages, photos, and documents with a simple interface.
- **`src/api/home_assistant.py`** — Home Assistant REST API client. Control entities, call services, and monitor states.

### 🌐 Network
- **`src/network/port_scanner.py`** — Multi-threaded TCP port scanner with common homelab ports preset. Supports single host and network scanning.

### 🛠️ Utilities
- **`src/utilities/file_organizer.py`** — Organize files by type or date. Supports dry-run mode and duplicate handling.

## ⚙️ Configuration

Most scripts work out of the box with sensible defaults. For Telegram alerts, edit the config dictionary at the top of each script:

```python
CONFIG = {
    "telegram": {
        "enabled": True,
        "bot_token": "YOUR_BOT_TOKEN",
        "chat_id": "YOUR_CHAT_ID"
    }
}
```

Or create a config file at `/etc/python-scripts/<script-name>.json` to override defaults.

## 🔑 Getting a Telegram Bot Token

1. Message [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot` and follow the instructions
3. Copy the token and use it in your scripts
4. Get your chat ID by messaging [@userinfobot](https://t.me/userinfobot)

## 🏠 Home Assistant Token

1. Go to your HA profile (bottom left)
2. Scroll to "Long-Lived Access Tokens"
3. Create a token and copy it

## 🤝 Contributing

Contributions are welcome! Please:
- Keep scripts in English
- Add docstrings and comments
- Use only Python stdlib (no external dependencies)
- Test before submitting

## 📜 License

MIT License — see [LICENSE](LICENSE) for details.