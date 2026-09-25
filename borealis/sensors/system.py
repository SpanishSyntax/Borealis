"""System sensor: monitors local time, temporal cycles, seasons, and host battery telemetry."""

import datetime
from pathlib import Path
from typing import Any, Dict
from borealis.sensors.base import BaseSensor


class SystemSensor(BaseSensor):
    """Monitors host system telemetry, time parameters, and battery status."""

    def __init__(self, ttl: int = 10) -> None:
        super().__init__("system", ttl=ttl)

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        now = datetime.datetime.now()
        month = now.month
        day = now.day

        # Estimate meteorological season (Northern hemisphere baseline)
        if month in (12, 1, 2):
            season = "winter"
        elif month in (3, 4, 5):
            season = "spring"
        elif month in (6, 7, 8):
            season = "summer"
        else:
            season = "autumn"

        # Check battery level if available on Linux
        battery_pct = None
        is_charging = None

        power_supply_dir = Path("/sys/class/power_supply")
        if power_supply_dir.exists():
            for p in power_supply_dir.iterdir():
                if p.name.startswith("BAT"):
                    cap_file = p / "capacity"
                    status_file = p / "status"
                    if cap_file.exists():
                        try:
                            battery_pct = int(cap_file.read_text().strip())
                        except Exception:
                            pass
                    if status_file.exists():
                        try:
                            is_charging = status_file.read_text().strip().lower() == "charging"
                        except Exception:
                            pass
                    break

        return {
            "hour": now.hour,
            "minute": now.minute,
            "day": day,
            "month": month,
            "weekday": now.strftime("%A").lower(),
            "season": season,
            "battery_percent": battery_pct,
            "is_charging": is_charging,
            "is_low_battery": (battery_pct is not None and battery_pct < 20 and not is_charging),
        }
