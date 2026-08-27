#!/usr/bin/env python3
"""
weather.py — Get current weather from Open-Meteo API (no API key required)
Displays temperature, humidity, wind speed, and conditions
"""

import urllib.request
import json
import argparse
import logging
from typing import Optional, Dict

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# WMO Weather interpretation codes
WEATHER_CODES = {
    0: "Clear sky",
    1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
    45: "Fog", 48: "Depositing rime fog",
    51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
    56: "Light freezing drizzle", 57: "Dense freezing drizzle",
    61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
    66: "Light freezing rain", 67: "Heavy freezing rain",
    71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
    77: "Snow grains",
    80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
    85: "Slight snow showers", 86: "Heavy snow showers",
    95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
}


def get_weather(lat: float, lon: float) -> Optional[Dict]:
    """Get current weather from Open-Meteo"""
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,apparent_temperature,"
        f"weather_code,wind_speed_10m,wind_direction_10m"
        f"&timezone=auto"
    )
    
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        
        current = data.get("current", {})
        units = data.get("current_units", {})
        
        weather_code = current.get("weather_code", -1)
        
        return {
            "temperature": current.get("temperature_2m", "N/A"),
            "temperature_unit": units.get("temperature_2m", "°C"),
            "feels_like": current.get("apparent_temperature", "N/A"),
            "humidity": current.get("relative_humidity_2m", "N/A"),
            "humidity_unit": units.get("relative_humidity_2m", "%"),
            "wind_speed": current.get("wind_speed_10m", "N/A"),
            "wind_speed_unit": units.get("wind_speed_10m", "km/h"),
            "wind_direction": current.get("wind_direction_10m", "N/A"),
            "condition": WEATHER_CODES.get(weather_code, f"Unknown ({weather_code})"),
            "time": current.get("time", "N/A")
        }
    except Exception as e:
        logger.error(f"Failed to get weather: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Get current weather")
    parser.add_argument("--lat", type=float, default=37.9838, help="Latitude (default: Athens)")
    parser.add_argument("--lon", type=float, default=23.7275, help="Longitude (default: Athens)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    weather = get_weather(args.lat, args.lon)
    
    if not weather:
        print("Failed to get weather data")
        return
    
    if args.json:
        print(json.dumps(weather, indent=2))
    else:
        print(f"[WEATHER]  Current Weather")
        print(f"{'='*40}")
        print(f"Condition: {weather['condition']}")
        print(f"Temperature: {weather['temperature']}{weather['temperature_unit']}")
        print(f"Feels like: {weather['feels_like']}{weather['temperature_unit']}")
        print(f"Humidity: {weather['humidity']}{weather['humidity_unit']}")
        print(f"Wind: {weather['wind_speed']} {weather['wind_speed_unit']} from {weather['wind_direction']}°")
        print(f"Updated: {weather['time']}")


if __name__ == "__main__":
    main()