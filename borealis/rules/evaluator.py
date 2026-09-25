"""Rule evaluator: evaluates declarative condition expressions against telemetry context."""

import math
import random
from typing import Any, Dict, List, Optional, Tuple


class AttrDict(dict):
    """Dictionary subclass that allows attribute-style access (e.g. obj.key)."""

    def __getattr__(self, name: str) -> Any:
        try:
            val = self[name]
            if isinstance(val, dict) and not isinstance(val, AttrDict):
                val = AttrDict(val)
                self[name] = val
            return val
        except KeyError:
            return None

    def __getitem__(self, key: str) -> Any:
        val = super().get(key)
        if isinstance(val, dict) and not isinstance(val, AttrDict):
            val = AttrDict(val)
            super().__setitem__(key, val)
        return val


class Rule:
    """Represents a single configurable decision-making rule."""

    def __init__(
        self,
        name: str,
        when: str,
        mood: str,
        priority: int = 50,
        tags: Optional[List[str]] = None,
        weight: float = 1.0,
        description: str = "",
    ) -> None:
        self.name = name
        self.when = when
        self.mood = mood
        self.priority = priority
        self.tags = tags or [mood]
        self.weight = weight
        self.description = description

    def __repr__(self) -> str:
        return f"<Rule {self.name} (pri={self.priority}) -> {self.mood}>"


class RuleEvaluator:
    """Evaluates rules against collected telemetry context with priority and fallback."""

    def __init__(self, rules: Optional[List[Rule]] = None) -> None:
        self.rules = sorted(rules or [], key=lambda r: r.priority, reverse=True)

    def evaluate(self, context: Dict[str, Any]) -> Tuple[str, List[str], Optional[Rule]]:
        """Evaluate rules in order of priority.

        Returns (mood, tags, matched_rule). If no rule matches, uses the 3D default matrix.
        """
        # Build safe evaluation context
        safe_eval_env = {
            "__builtins__": {},
            "random": random.random,
            "min": min,
            "max": max,
            "abs": abs,
            "round": round,
            "math": math,
            "location": AttrDict(context.get("location", {})),
            "solar": AttrDict(context.get("solar", {})),
            "weather": AttrDict(context.get("weather", {})),
            "space": AttrDict(context.get("space", {})),
            "system": AttrDict(context.get("system", {})),
        }

        # Check configured rules in priority order
        for rule in self.rules:
            try:
                res = eval(rule.when, safe_eval_env)
                if bool(res):
                    return rule.mood, rule.tags, rule
            except Exception:
                # Silently ignore evaluation errors on malformed rule
                continue

        # Fallback to the classic Atmospheric 3D Matrix
        mood, tags = self._evaluate_default_matrix(context)
        return mood, tags, None

    def _evaluate_default_matrix(self, context: Dict[str, Any]) -> Tuple[str, List[str]]:
        """Classic 3D environmental mood classification fallback."""
        solar = context.get("solar", {})
        weather = context.get("weather", {})
        space = context.get("space", {})

        # 1. Geomagnetic anomaly override
        kp = float(space.get("kp_index", 0))
        if kp >= 5.0 and random.random() > 0.2:
            return "wildcard_anomaly", ["wildcard_anomaly", "geomagnetic"]

        # 2. Astronomical night
        lumens = float(solar.get("estimated_lumens", 0))
        if lumens <= 0.0 or not solar.get("is_day", True):
            return "cosmic_void", ["cosmic_void", "night"]

        # 3. Crepuscular twilight
        sin_elev = float(solar.get("sin_elevation", 0))
        if 0.0 < sin_elev < 0.16:
            return "crepuscular", ["crepuscular", "twilight", "golden_hour"]

        # 4. 3D Atmospheric Vector Buckets
        if lumens < 250:
            lum_bucket = "dim"
        elif lumens > 600:
            lum_bucket = "blinding"
        else:
            lum_bucket = "muted"

        humidity = float(weather.get("humidity", 50))
        if humidity < 40:
            hum_bucket = "dry"
        elif humidity > 75:
            hum_bucket = "soup"
        else:
            hum_bucket = "comfortable"

        temp = float(weather.get("temperature", 15))
        if temp < 8:
            temp_bucket = "freezing"
        elif temp > 22:
            temp_bucket = "sweltering"
        else:
            temp_bucket = "mild"

        vec = f"{lum_bucket}_{hum_bucket}_{temp_bucket}"

        # Non-linear matrix routing
        if vec == "blinding_dry_freezing":
            return "glacial_stark", ["glacial_stark", "cold", "bright"]
        if vec == "blinding_dry_sweltering":
            return "crisp_sharp", ["crisp_sharp", "bright"]
        if vec == "blinding_comfortable_sweltering":
            return "pastoral_sun", ["pastoral_sun", "bright", "warm"]

        if hum_bucket == "soup":
            if temp_bucket == "freezing":
                return "winter_gothic", ["winter_gothic", "gloomy", "cold"]
            if temp_bucket == "sweltering":
                return "heavy_mist", ["heavy_mist", "fog", "humid"]
            return "pastoral_rain", ["pastoral_rain", "rain"]

        if hum_bucket == "dry":
            return "geometric_clarity", ["geometric_clarity", "dry"]

        if lum_bucket == "dim":
            if temp_bucket == "freezing":
                return "cozy_hearth", ["cozy_hearth", "cold", "indoor"]
            if temp_bucket == "sweltering":
                return "melancholic_tempest", ["melancholic_tempest", "storm"]
            return "nebula_diffuse", ["nebula_diffuse", "dim"]

        return "high_noon", ["high_noon", "daylight"]
