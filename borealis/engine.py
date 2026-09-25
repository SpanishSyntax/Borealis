"""Core Borealis engine coordinator: sensors, rules, library, and daemon loop."""

import datetime
import logging
import signal
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from borealis.backends import get_backend
from borealis.config import Config
from borealis.library import WallpaperLibrary
from borealis.rules.evaluator import Rule, RuleEvaluator
from borealis.sensors.location import LocationSensor
from borealis.sensors.solar import SolarSensor
from borealis.sensors.space import SpaceWeatherSensor
from borealis.sensors.system import SystemSensor
from borealis.sensors.weather import WeatherSensor

logger = logging.getLogger("borealis")


class BorealisEngine:
    """Coordinates telemetry sensors, rule evaluation, wallpaper library, and daemon runtime."""

    def __init__(self, config: Config) -> None:
        self.config = config

        # 1. Sensors
        self.location_sensor = LocationSensor(
            manual_lat=config.manual_lat,
            manual_lon=config.manual_lon,
        )
        self.solar_sensor = SolarSensor()
        self.weather_sensor = WeatherSensor(ttl=config.telemetry_interval)
        self.space_sensor = SpaceWeatherSensor(ttl=config.telemetry_interval)
        self.system_sensor = SystemSensor()

        self.sensors = [
            self.location_sensor,
            self.space_sensor,
            self.weather_sensor,
            self.solar_sensor,
            self.system_sensor,
        ]

        # 2. Rule Evaluator
        self.rule_evaluator = RuleEvaluator(rules=config.rules)

        # 3. Library
        self.library = WallpaperLibrary(
            root_dirs=config.wallpaper_dirs,
            history_size=config.history_size,
        )

        # 4. Display Backend
        self.backend = get_backend(config.backend_name, config.backend_config)

        self._telemetry_cache: Dict[str, Any] = {}
        self._last_telemetry_time: float = 0.0
        self._running = False

    def update_telemetry(self, force: bool = False) -> Dict[str, Any]:
        """Poll telemetry sensors and update unified context."""
        now = time.time()
        context = dict(self._telemetry_cache)

        for sensor in self.sensors:
            data = sensor.update(context, now, force=force)
            context[sensor.name] = data

        self._telemetry_cache = context
        self._last_telemetry_time = now
        return context

    def evaluate_and_pick(self, force_telemetry: bool = False) -> Tuple[str, List[str], Optional[Path], Optional[Rule], Dict[str, Any]]:
        """Run telemetry evaluation, match rules, and select candidate wallpaper."""
        context = self.update_telemetry(force=force_telemetry)
        mood, tags, matched_rule = self.rule_evaluator.evaluate(context)
        selected_path = self.library.select(mood=mood, tags=tags)
        return mood, tags, selected_path, matched_rule, context

    def tick(self, dry_run: bool = False) -> Dict[str, Any]:
        """Execute one complete evaluation and wallpaper update cycle."""
        mood, tags, path, rule, context = self.evaluate_and_pick()

        result = {
            "mood": mood,
            "tags": tags,
            "wallpaper": str(path) if path else None,
            "rule": rule.name if rule else "default_matrix",
            "timestamp": datetime.datetime.now().isoformat(),
            "applied": False,
        }

        if path and not dry_run:
            success = self.backend.apply(path)
            result["applied"] = success
            if not success:
                logger.warning(f"Backend '{self.backend.name}' failed to apply wallpaper: {path}")

        return result

    def print_status_dashboard(self) -> None:
        """Print an informative, formatted telemetry dashboard to terminal."""
        mood, tags, path, rule, ctx = self.evaluate_and_pick(force_telemetry=True)
        loc = ctx.get("location", {})
        sol = ctx.get("solar", {})
        wth = ctx.get("weather", {})
        spc = ctx.get("space", {})
        sys_ctx = ctx.get("system", {})

        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print("=" * 72)
        print(f" BOREALIS TELEMETRY DASHBOARD | {now}")
        print("=" * 72)
        print(f"  {'Geographic Origin':<25} : {loc.get('city', 'Unknown')}, {loc.get('country', '')} (LAT: {loc.get('latitude')}, LON: {loc.get('longitude')})")
        print(f"  {'Solar Elevation':<25} : {sol.get('elevation_deg')}° ({sol.get('phase', 'unknown')})")
        print(f"  {'Atmospheric Lumens':<25} : {sol.get('estimated_lumens', 0)} lm (sin_elev: {round(sol.get('sin_elevation', 0), 3)})")
        print("-" * 72)
        print(f"  {'Thermal State':<25} : {wth.get('temperature', 0)}°C ({wth.get('description', 'N/A')})")
        print(f"  {'Moisture Content':<25} : {wth.get('humidity', 0)}% (Rain: {wth.get('is_raining', False)})")
        print(f"  {'Cloud Canopy':<25} : {wth.get('clouds', 0)}%")
        print(f"  {'Geomagnetic Scale':<25} : Kp-Index {spc.get('kp_index', 0)} ({spc.get('activity', 'quiet')})")
        print("-" * 72)
        print(f"  {'Local Temporal State':<25} : {sys_ctx.get('weekday', '').capitalize()} {sys_ctx.get('hour')}:{sys_ctx.get('minute'):02d} ({sys_ctx.get('season', '')})")
        if sys_ctx.get("battery_percent") is not None:
            charging_str = "Charging" if sys_ctx.get("is_charging") else "Discharging"
            print(f"  {'Battery Telemetry':<25} : {sys_ctx.get('battery_percent')}% ({charging_str})")
        print("-" * 72)
        rule_desc = f"Matched Rule '{rule.name}'" if rule else "Default 3D Matrix Routing"
        print(f"  \033[1;36m{'ACTIVE MOOD VECTOR':<25}\033[0m : \033[1;35m{mood}\033[0m (tags: {', '.join(tags)})")
        print(f"  {'Decision Origin':<25} : {rule_desc}")
        dirs_str = ", ".join(str(d) for d in self.config.wallpaper_dirs)
        print(f"  {'Wallpaper Library':<25} : {len(self.library.items)} assets indexed from {dirs_str}")
        print("=" * 72)

    def run_daemon(self) -> None:
        """Start the background daemon loop."""
        self._running = True

        def _handle_signal(signum, frame):
            logger.info("Termination signal received. Shutting down Borealis daemon.")
            self._running = False

        signal.signal(signal.SIGINT, _handle_signal)
        signal.signal(signal.SIGTERM, _handle_signal)

        dirs_str = ", ".join(str(d) for d in self.config.wallpaper_dirs)
        logger.info(f"Starting Borealis wallpaper daemon using backend '{self.config.backend_name}'...")
        logger.info(f"Wallpaper repositories: {dirs_str} ({len(self.library.items)} images)")
        logger.info(f"Interval: {self.config.interval}s | Telemetry refresh: {self.config.telemetry_interval}s")

        # Initial tick
        self.tick()

        ticks_since_telemetry = 0
        telemetry_tick_limit = max(1, self.config.telemetry_interval // max(1, self.config.interval))

        while self._running:
            try:
                time.sleep(self.config.interval)
                if not self._running:
                    break

                ticks_since_telemetry += 1
                if ticks_since_telemetry >= telemetry_tick_limit:
                    ticks_since_telemetry = 0
                    self.update_telemetry(force=True)

                self.tick()
            except InterruptedError:
                break
            except Exception as e:
                logger.error(f"Error in daemon tick: {e}", exc_info=True)
                time.sleep(5)

        logger.info("Borealis daemon stopped.")
