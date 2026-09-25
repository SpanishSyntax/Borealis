"""Location sensor: determines geographical coordinates for solar and weather tracking."""

import json
import urllib.request
from typing import Any, Dict, Optional
from borealis.sensors.base import BaseSensor


class LocationSensor(BaseSensor):
    """Fetches geographical coordinates via IP geolocation or manual configuration."""

    def __init__(
        self,
        manual_lat: Optional[float] = None,
        manual_lon: Optional[float] = None,
        fallback_lat: float = 0.0,
        fallback_lon: float = 0.0,
        ttl: int = 86400,  # Cache location for 24 hours
    ) -> None:
        super().__init__("location", ttl=ttl)
        self.manual_lat = manual_lat
        self.manual_lon = manual_lon
        self.fallback_lat = fallback_lat
        self.fallback_lon = fallback_lon

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Manual coordinates configured by user
        if self.manual_lat is not None and self.manual_lon is not None:
            return {
                "latitude": float(self.manual_lat),
                "longitude": float(self.manual_lon),
                "city": "Configured",
                "country": "Configured",
                "source": "manual",
            }

        # 2. Dynamic IP geolocation
        try:
            req = urllib.request.Request(
                "https://ipapi.co/json/",
                headers={"User-Agent": "Borealis-Wallpaper-Engine/0.1.0"},
            )
            with urllib.request.urlopen(req, timeout=4) as response:
                if response.status == 200:
                    payload = json.loads(response.read().decode("utf-8"))
                    if "latitude" in payload and "longitude" in payload and not payload.get("error"):
                        return {
                            "latitude": float(payload["latitude"]),
                            "longitude": float(payload["longitude"]),
                            "city": payload.get("city", "Unknown"),
                            "country": payload.get("country_name", "Unknown"),
                            "source": "ipapi",
                        }
        except Exception:
            pass

        # 3. Fallback coordinates
        return {
            "latitude": self.fallback_lat,
            "longitude": self.fallback_lon,
            "city": "Fallback",
            "country": "Fallback",
            "source": "fallback",
        }
