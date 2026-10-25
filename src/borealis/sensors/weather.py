"""Terrestrial weather sensor: collects cloud canopy, humidity, temperature, and precipitation."""

import json
import urllib.request
from typing import Any, Dict
from borealis.sensors.base import BaseSensor


class WeatherSensor(BaseSensor):
    """Collects real-time terrestrial weather data from wttr.in."""

    def __init__(self, ttl: int = 900) -> None:
        # Default refresh interval: 15 minutes (900s)
        super().__init__("weather", ttl=ttl)

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        location = context.get("location", {})
        lat = location.get("latitude", 0.0)
        lon = location.get("longitude", 0.0)

        url = f"https://wttr.in/{lat},{lon}?format=j1"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Borealis-Wallpaper-Engine/0.1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    current = data.get("current_condition", [{}])[0]

                    clouds = int(current.get("cloudcover", 0))
                    humidity = int(current.get("humidity", 50))
                    temp_c = int(current.get("temp_C", 15))
                    precip_mm = float(current.get("precipMM", 0.0))
                    desc = current.get("weatherDesc", [{}])[0].get("value", "")

                    desc_lower = desc.lower()
                    is_raining = (
                        precip_mm > 0.1
                        or "rain" in desc_lower
                        or "drizzle" in desc_lower
                        or "shower" in desc_lower
                    )
                    is_snowing = (
                        "snow" in desc_lower
                        or "blizzard" in desc_lower
                        or "sleet" in desc_lower
                    )
                    is_foggy = (
                        "fog" in desc_lower
                        or "mist" in desc_lower
                        or "haze" in desc_lower
                    )

                    return {
                        "clouds": clouds,
                        "humidity": humidity,
                        "temperature": temp_c,
                        "precipitation_mm": precip_mm,
                        "description": desc,
                        "is_raining": is_raining,
                        "is_snowing": is_snowing,
                        "is_foggy": is_foggy,
                        "online": True,
                    }
        except Exception:
            pass

        # Return fallback defaults if offline / timeout
        return {
            "clouds": 0,
            "humidity": 50,
            "temperature": 15,
            "precipitation_mm": 0.0,
            "description": "Default / Offline",
            "is_raining": False,
            "is_snowing": False,
            "is_foggy": False,
            "online": False,
        }
