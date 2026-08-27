#!/usr/bin/env python3
"""
telegram_bot.py — Simple Telegram bot for homelab notifications
Provides a wrapper class for sending messages, photos, and files via Telegram Bot API
"""

import urllib.request
import urllib.parse
import json
import logging
from pathlib import Path
from typing import Optional, Union

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class TelegramBot:
    """Telegram Bot API wrapper"""
    
    def __init__(self, bot_token: str, chat_id: str, timeout: int = 10):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.timeout = timeout
        self.base_url = f"https://api.telegram.org/bot{bot_token}"
    
    def send_message(self, text: str, parse_mode: str = "HTML") -> dict:
        """Send a text message"""
        url = f"{self.base_url}/sendMessage"
        data = urllib.parse.urlencode({
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": parse_mode
        }).encode()
        
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())
                logger.info("Message sent successfully")
                return result
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            return {"error": str(e)}
    
    def send_photo(self, photo_path: str, caption: str = "") -> dict:
        """Send a photo from local file"""
        url = f"{self.base_url}/sendPhoto"
        photo_p = Path(photo_path)
        
        if not photo_p.exists():
            logger.error(f"Photo not found: {photo_p}")
            return {"error": "File not found"}
        
        try:
            with open(photo_p, 'rb') as f:
                photo_data = f.read()
            
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            data = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{self.chat_id}\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="photo"; filename="{photo_p.name}"\r\n'
                f"Content-Type: image/jpeg\r\n\r\n"
            ).encode() + photo_data + f"\r\n--{boundary}--\r\n".encode()
            
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())
                logger.info("Photo sent successfully")
                return result
        except Exception as e:
            logger.error(f"Failed to send photo: {e}")
            return {"error": str(e)}
    
    def send_document(self, file_path: str, caption: str = "") -> dict:
        """Send a document/file"""
        url = f"{self.base_url}/sendDocument"
        file_path = Path(file_path)
        
        if not file_path.exists():
            logger.error(f"File not found: {file_path}")
            return {"error": "File not found"}
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
            data = (
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{self.chat_id}\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
                f"--{boundary}\r\n"
                f'Content-Disposition: form-data; name="document"; filename="{file_path.name}"\r\n'
                f"Content-Type: application/octet-stream\r\n\r\n"
            ).encode() + file_data + f"\r\n--{boundary}--\r\n".encode()
            
            req = urllib.request.Request(
                url, data=data,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
            )
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                result = json.loads(resp.read().decode())
                logger.info("Document sent successfully")
                return result
        except Exception as e:
            logger.error(f"Failed to send document: {e}")
            return {"error": str(e)}
    
    def get_updates(self, offset: int = 0, limit: int = 10) -> dict:
        """Get recent updates (messages) from bot"""
        url = f"{self.base_url}/getUpdates"
        data = urllib.parse.urlencode({
            "offset": offset,
            "limit": limit
        }).encode()
        
        try:
            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"Failed to get updates: {e}")
            return {"error": str(e)}


# Example usage
if __name__ == "__main__":
    # Replace with your bot token and chat ID
    BOT_TOKEN = "YOUR_BOT_TOKEN"
    CHAT_ID = "YOUR_CHAT_ID"
    
    bot = TelegramBot(BOT_TOKEN, CHAT_ID)
    
    # Send a test message
    bot.send_message("🤖 <b>Bot Test</b>\n\nHello from python-scripts!")
    
    # Send a photo (uncomment if you have a photo)
    # bot.send_photo("/path/to/photo.jpg", caption="Test photo")
    
    # Send a file (uncomment if you have a file)
    # bot.send_document("/path/to/file.txt", caption="Test document")