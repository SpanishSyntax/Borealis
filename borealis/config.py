"""Configuration management: loads and validates TOML configuration for Borealis."""

import os
import pathlib
from typing import Any, Dict, List, Optional
from borealis.rules.evaluator import Rule

try:
    import tomllib
except ImportError:
    import tomli as tomllib  # type: ignore

DEFAULT_RULES = [
    Rule(
        name="geomagnetic_storm",
        when="space.kp_index >= 5 and random() > 0.2",
        mood="wildcard_anomaly",
        priority=100,
        tags=["wildcard_anomaly", "geomagnetic"],
        description="Triggered when NOAA Kp-index indicates geomagnetic storms",
    ),
    Rule(
        name="astronomical_night",
        when="solar.elevation_deg < -6 or solar.phase == 'astronomical_night'",
        mood="cosmic_void",
        priority=90,
        tags=["cosmic_void", "night"],
        description="Deep night sky when solar elevation is well below horizon",
    ),
    Rule(
        name="crepuscular_twilight",
        when="solar.is_crepuscular or (0.0 <= solar.sin_elevation < 0.16)",
        mood="crepuscular",
        priority=80,
        tags=["crepuscular", "golden_hour", "twilight"],
        description="Golden hour and crepuscular twilight near sunrise/sunset",
    ),
    Rule(
        name="heavy_soup_freezing",
        when="weather.humidity > 75 and weather.temperature < 8",
        mood="winter_gothic",
        priority=70,
        tags=["winter_gothic", "cold", "gloomy"],
        description="Freezing fog and heavy winter moisture",
    ),
    Rule(
        name="heavy_soup_sweltering",
        when="weather.humidity > 75 and weather.temperature > 22",
        mood="heavy_mist",
        priority=69,
        tags=["heavy_mist", "fog", "humid"],
        description="Heavy tropical humidity or summer downpours",
    ),
    Rule(
        name="heavy_soup_mild",
        when="weather.humidity > 75 or weather.is_raining",
        mood="pastoral_rain",
        priority=68,
        tags=["pastoral_rain", "rain"],
        description="Gentle rain and moist temperate weather",
    ),
    Rule(
        name="blinding_dry_freezing",
        when="solar.estimated_lumens > 600 and weather.humidity < 40 and weather.temperature < 8",
        mood="glacial_stark",
        priority=65,
        tags=["glacial_stark", "cold", "bright"],
        description="Blinding sunlight on frozen crisp air",
    ),
    Rule(
        name="blinding_dry_sweltering",
        when="solar.estimated_lumens > 600 and weather.humidity < 40 and weather.temperature > 22",
        mood="crisp_sharp",
        priority=64,
        tags=["crisp_sharp", "bright"],
        description="Blinding arid heat",
    ),
    Rule(
        name="blinding_comfortable_sweltering",
        when="solar.estimated_lumens > 600 and weather.temperature > 20",
        mood="pastoral_sun",
        priority=63,
        tags=["pastoral_sun", "bright", "warm"],
        description="Brilliant warm sunny day",
    ),
    Rule(
        name="arid_clarity",
        when="weather.humidity < 40",
        mood="geometric_clarity",
        priority=55,
        tags=["geometric_clarity", "dry"],
        description="Clear dry atmospheric conditions",
    ),
    Rule(
        name="dim_freezing",
        when="solar.estimated_lumens < 250 and weather.temperature < 8",
        mood="cozy_hearth",
        priority=50,
        tags=["cozy_hearth", "cold", "indoor"],
        description="Cold overcast dim skies",
    ),
    Rule(
        name="dim_sweltering",
        when="solar.estimated_lumens < 250 and weather.temperature > 22",
        mood="melancholic_tempest",
        priority=49,
        tags=["melancholic_tempest", "storm"],
        description="Warm oppressive thunderstorm mood",
    ),
    Rule(
        name="dim_general",
        when="solar.estimated_lumens < 250",
        mood="nebula_diffuse",
        priority=40,
        tags=["nebula_diffuse", "dim"],
        description="Diffuse overcast daytime light",
    ),
]


class Config:
    """Parsed Borealis runtime configuration."""

    def __init__(self, raw: Dict[str, Any], config_path: Optional[pathlib.Path] = None) -> None:
        self.config_path = config_path
        self.raw = raw

        # [general] section
        gen = raw.get("general", {})
        self.backend_name = gen.get("backend", "awww")
        self.interval = int(gen.get("interval", 20))
        self.telemetry_interval = int(gen.get("telemetry_interval", 900))
        self.history_size = int(gen.get("history_size", 10))

        # Wallpaper directories: config -> env -> fallback
        self.wallpaper_dirs: List[pathlib.Path] = []
        raw_dirs = gen.get("wallpaper_dirs") or gen.get("wallpaper_dir") or os.environ.get("BOREALIS_WALLPAPER_DIR")

        if raw_dirs:
            if isinstance(raw_dirs, list):
                self.wallpaper_dirs = [pathlib.Path(d).expanduser().resolve() for d in raw_dirs]
            elif isinstance(raw_dirs, str):
                # Allow comma or colon separated paths in string
                delimiters = [",", ":"]
                parts = [raw_dirs]
                for delim in delimiters:
                    if delim in raw_dirs:
                        parts = [p.strip() for p in raw_dirs.split(delim)]
                        break
                self.wallpaper_dirs = [pathlib.Path(p).expanduser().resolve() for p in parts if p.strip()]

        if not self.wallpaper_dirs:
            # Fallback to local ./wallpapers or ~/.local/share/wallpapers
            local_wp = pathlib.Path("wallpapers").resolve()
            if local_wp.is_dir():
                self.wallpaper_dirs = [local_wp]
            else:
                self.wallpaper_dirs = [pathlib.Path.home() / ".local" / "share" / "wallpapers"]

        # Backwards compatibility property
        self.wallpaper_dir = self.wallpaper_dirs[0] if self.wallpaper_dirs else pathlib.Path(".")

        # [location] section
        loc = raw.get("location", {})
        self.manual_lat = loc.get("latitude")
        self.manual_lon = loc.get("longitude")

        # [backend] section
        self.backend_config = raw.get("backend", {})

        # [[rules]] section
        self.rules: List[Rule] = []
        user_rules = raw.get("rules")
        if user_rules and isinstance(user_rules, list):
            for r in user_rules:
                if isinstance(r, dict) and "name" in r and "when" in r and "mood" in r:
                    self.rules.append(
                        Rule(
                            name=r["name"],
                            when=r["when"],
                            mood=r["mood"],
                            priority=int(r.get("priority", 50)),
                            tags=r.get("tags"),
                            weight=float(r.get("weight", 1.0)),
                            description=r.get("description", ""),
                        )
                    )
        else:
            self.rules = list(DEFAULT_RULES)


def find_config_file(custom_path: Optional[str] = None) -> Optional[pathlib.Path]:
    """Locate candidate configuration file."""
    if custom_path:
        p = pathlib.Path(custom_path).expanduser().resolve()
        if p.is_file():
            return p

    env_path = os.environ.get("BOREALIS_CONFIG")
    if env_path:
        p = pathlib.Path(env_path).expanduser().resolve()
        if p.is_file():
            return p

    candidates = [
        pathlib.Path("borealis.toml"),
        pathlib.Path.home() / ".config" / "borealis" / "borealis.toml",
        pathlib.Path("/etc/borealis/borealis.toml"),
    ]

    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config:
        candidates.insert(1, pathlib.Path(xdg_config) / "borealis" / "borealis.toml")

    for c in candidates:
        if c.is_file():
            return c.resolve()

    return None


def load_config(custom_path: Optional[str] = None) -> Config:
    """Load configuration from file or return built-in defaults."""
    cfg_file = find_config_file(custom_path)
    if cfg_file and cfg_file.is_file():
        try:
            with open(cfg_file, "rb") as f:
                data = tomllib.load(f)
                return Config(data, config_path=cfg_file)
        except Exception as e:
            print(f"Warning: Failed to parse {cfg_file}: {e}. Using default config.")

    return Config({}, config_path=None)
