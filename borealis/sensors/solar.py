"""Solar & Celestial sensor: calculates orbital zenith, elevation, and atmospheric lumens."""

import datetime
import math
from typing import Any, Dict
from borealis.sensors.base import BaseSensor


class SolarSensor(BaseSensor):
    """Calculates astronomical solar parameters, solar elevation angle, and estimated lumens."""

    def __init__(self, ttl: int = 60) -> None:
        # Solar angle updates every 60 seconds
        super().__init__("solar", ttl=ttl)

    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        location = context.get("location", {})
        lat = float(location.get("latitude", 0.0))
        lon = float(location.get("longitude", 0.0))

        lat_rad = math.radians(lat)

        # Current time
        now = datetime.datetime.now()
        day_of_year = now.timetuple().tm_yday
        hour = now.hour
        minute = now.minute
        second = now.second

        # Map 24-hour cycle to 2*pi radian cycle
        time_fraction = (hour + (minute / 60.0) + (second / 3600.0)) / 24.0
        time_radians = time_fraction * 2.0 * math.pi

        # Solar Declination: 0.409 * sin(2*pi*(day_of_year - 80)/365)
        declination = 0.409 * math.sin((2.0 * math.pi * (day_of_year - 80)) / 365.0)

        # Sine of Solar Elevation Angle:
        # sin(alpha) = sin(lat)*sin(dec) + cos(lat)*cos(dec)*cos(time_radians - pi)
        sin_elevation = (
            math.sin(lat_rad) * math.sin(declination)
            + math.cos(lat_rad) * math.cos(declination) * math.cos(time_radians - math.pi)
        )

        # Clamp sin_elevation to [-1.0, 1.0] for asin
        clamped_sin = max(-1.0, min(1.0, sin_elevation))
        elevation_deg = math.degrees(math.asin(clamped_sin))

        # Solar phase classification
        if elevation_deg < -18.0:
            phase = "astronomical_night"
        elif elevation_deg < -12.0:
            phase = "nautical_twilight"
        elif elevation_deg < -6.0:
            phase = "civil_twilight"
        elif elevation_deg < 0.0:
            phase = "blue_hour"
        elif elevation_deg < 6.0:
            phase = "crepuscular"  # Golden hour / sunrise / sunset
        elif elevation_deg < 20.0:
            phase = "early_day"
        else:
            phase = "high_day"

        is_day = elevation_deg > 0.0

        # Estimated surface light energy (lumens), attenuated by cloud cover if available
        weather = context.get("weather", {})
        cloud_percent = float(weather.get("clouds", 0.0))

        if sin_elevation > 0.0:
            cloud_factor = 1.0 - 0.75 * math.pow(cloud_percent / 100.0, 3)
            estimated_lumens = 1361.0 * sin_elevation * max(0.0, cloud_factor)
        else:
            estimated_lumens = 0.0

        return {
            "latitude_rad": lat_rad,
            "declination": declination,
            "sin_elevation": sin_elevation,
            "elevation_deg": round(elevation_deg, 2),
            "estimated_lumens": round(estimated_lumens, 1),
            "phase": phase,
            "is_day": is_day,
            "is_crepuscular": (0.0 <= sin_elevation < 0.16),
        }
