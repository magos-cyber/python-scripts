#!/usr/bin/env python3
"""
home_assistant.py — Home Assistant REST API client
Simple wrapper for controlling Home Assistant entities and services
"""

import urllib.request
import urllib.parse
import json
import logging
from typing import Optional, Any

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)


class HomeAssistant:
    """Home Assistant REST API client"""
    
    def __init__(self, base_url: str, token: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.token = token
        self.timeout = timeout
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
    
    def _request(self, method: str, endpoint: str, data: Optional[dict] = None) -> dict:
        """Make an API request"""
        url = f"{self.base_url}/api/{endpoint}"
        
        try:
            body = json.dumps(data).encode() if data else None
            req = urllib.request.Request(url, data=body, headers=self.headers, method=method)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception as e:
            logger.error(f"API request failed: {e}")
            return {"error": str(e)}
    
    def get_config(self) -> dict:
        """Get Home Assistant configuration"""
        return self._request("GET", "config")
    
    def get_states(self) -> list:
        """Get all entity states"""
        return self._request("GET", "states")
    
    def get_state(self, entity_id: str) -> dict:
        """Get state of a specific entity"""
        return self._request("GET", f"states/{entity_id}")
    
    def set_state(self, entity_id: str, state: str, attributes: Optional[dict] = None) -> dict:
        """Set state of an entity"""
        data = {"state": state}
        if attributes:
            data["attributes"] = attributes
        return self._request("POST", f"states/{entity_id}", data)
    
    def call_service(self, domain: str, service: str, entity_id: Optional[str] = None, **kwargs) -> dict:
        """Call a Home Assistant service"""
        data = {}
        if entity_id:
            data["entity_id"] = entity_id
        data.update(kwargs)
        return self._request("POST", f"services/{domain}/{service}", data)
    
    def turn_on(self, entity_id: str, **kwargs) -> dict:
        """Turn on an entity"""
        return self.call_service("homeassistant", "turn_on", entity_id, **kwargs)
    
    def turn_off(self, entity_id: str) -> dict:
        """Turn off an entity"""
        return self.call_service("homeassistant", "turn_off", entity_id)
    
    def toggle(self, entity_id: str) -> dict:
        """Toggle an entity"""
        return self.call_service("homeassistant", "toggle", entity_id)
    
    def get_light_brightness(self, entity_id: str) -> Optional[int]:
        """Get current brightness of a light (0-255)"""
        state = self.get_state(entity_id)
        if "attributes" in state:
            return state["attributes"].get("brightness")
        return None
    
    def set_light(self, entity_id: str, brightness: Optional[int] = None, 
                  color_temp: Optional[int] = None, rgb_color: Optional[list] = None) -> dict:
        """Set light properties"""
        kwargs = {}
        if brightness is not None:
            kwargs["brightness"] = brightness
        if color_temp is not None:
            kwargs["color_temp"] = color_temp
        if rgb_color is not None:
            kwargs["rgb_color"] = rgb_color
        return self.call_service("light", "turn_on", entity_id, **kwargs)
    
    def get_temperature(self, entity_id: str) -> Optional[float]:
        """Get temperature from a sensor"""
        state = self.get_state(entity_id)
        try:
            return float(state.get("state", 0))
        except (ValueError, TypeError):
            return None
    
    def fire_event(self, event_type: str, event_data: Optional[dict] = None) -> dict:
        """Fire a custom event"""
        return self._request("POST", f"events/{event_type}", event_data)
    
    def render_template(self, template: str) -> str:
        """Render a Jinja2 template"""
        data = {"template": template}
        result = self._request("POST", "template", data)
        return str(result)


# Example usage
if __name__ == "__main__":
    # Replace with your HA URL and long-lived token
    HA_URL = "http://homeassistant.local:8123"
    HA_TOKEN = "YOUR_LONG_LIVED_ACCESS_TOKEN"
    
    ha = HomeAssistant(HA_URL, HA_TOKEN)
    
    # Get all states
    states = ha.get_states()
    print(f"Found {len(states)} entities")
    
    # Turn on a light
    # ha.turn_on("light.living_room")
    
    # Set brightness
    # ha.set_light("light.bedroom", brightness=128)
    
    # Get temperature
    # temp = ha.get_temperature("sensor.living_room_temperature")
    # print(f"Temperature: {temp}°C")