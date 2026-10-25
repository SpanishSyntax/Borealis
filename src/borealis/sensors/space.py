"""Space weather sensor: tracks solar wind, geomagnetic Kp-index, and magnetosphere storms."""

import json
import urllib.request
from typing import Any, Dict
from borealis.sensors.base import BaseSensor


class SpaceWeatherSensor(BaseSensor):
    """Fetches real-time space weather scales from NOAA Space Weather Prediction Center."""

    def __init__(self, ttl: int = 900) -> None:
        # 15 minutes TTL
        super().__init__("space", ttl=ttl)

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        url = "https://services.swpc.noaa.gov/products/noaa-scales.json"

        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Borealis-Wallpaper-Engine/0.1.0"},
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    data = json.loads(response.read().decode("utf-8"))
                    # Search for active geomagnetic scale
                    for item in data:
                        if isinstance(item, dict) and "geomagnetic" in item:
                            geo = item["geomagnetic"]
                            if geo and "kp" in geo:
                                kp = float(geo.get("kp", 0.0))
                                scale = geo.get("Scale", "G0")

                                # Classify storm activity
                                is_storm = kp >= 5.0
                                if kp >= 8:
                                    activity = "severe_storm"
                                elif kp >= 6:
                                    activity = "moderate_storm"
                                elif kp >= 5:
                                    activity = "minor_storm"
                                elif kp >= 4:
                                    activity = "unsettled"
                                else:
                                    activity = "quiet"

                                return {
                                    "kp_index": kp,
                                    "scale": scale,
                                    "activity": activity,
                                    "is_storm": is_storm,
                                    "online": True,
                                }
        except Exception:
            pass

        return {
            "kp_index": 0.0,
            "scale": "G0",
            "activity": "quiet",
            "is_storm": False,
            "online": False,
        }
