# Configuration Guide

Borealis is configured declaratively via `borealis.toml` or Nix Home Manager modules.

---

## borealis.toml Reference

The primary configuration file resides at `~/.config/borealis/borealis.toml`.

```toml
[general]
# Target wallpaper daemon: "awww", "swww", "hyprpaper", or "command"
backend = "awww"

# Wallpaper rotation interval within current mood (seconds)
interval = 20

# Telemetry polling interval for weather and solar position (seconds)
telemetry_interval = 900

# Number of recently shown wallpapers to remember to prevent repeats
history_size = 10

# Primary directory to search for wallpapers
# wallpaper_dir = "~/.local/share/wallpapers"

[location]
# Manual geolocation coordinates (defaults to automatic IP-based lookup if omitted)
# latitude = 52.3676
# longitude = 4.9041

[backend]
# Backend transition styling (used by swww / awww)
transition_type = "simple"
transition_step = 90

# Command template when backend = "command"
# command_template = "feh --bg-fill {path}"
```

---

## Home Manager Module Options

The Home Manager Flake module exposes typed options under `services.borealis`:

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `services.borealis.enable` | boolean | `false` | Enables the Borealis background daemon and systemd user unit. |
| `services.borealis.backend` | enum: `["awww", "swww", "hyprpaper", "command"]` | `"awww"` | Wallpaper rendering backend to manage. |
| `services.borealis.interval` | integer | `20` | Wallpaper change interval in seconds. |
| `services.borealis.telemetryInterval` | integer | `900` | Atmospheric telemetry polling interval in seconds. |
| `services.borealis.includeDefaultWallpapers` | boolean | `true` | Downloads and indexes the curated 400 MB art pack from GitHub Releases. |
| `services.borealis.wallpaperDir` | null or path/string | `null` | Primary local wallpaper folder to index. |
| `services.borealis.extraWallpaperDirs` | list of path/string | `[]` | Additional directories to pool into the wallpaper index. |
| `services.borealis.settings` | attribute set (TOML) | `{}` | Declarative overrides serialized into `~/.config/borealis/borealis.toml`. |

---

## Declarative Rule Syntax

Rules are evaluated in descending order of `priority`. The first rule whose `when` condition evaluates to `true` selects the active mood.

```toml
[[rules]]
name = "geomagnetic_storm"
priority = 100
when = "space.kp_index >= 5 and random() > 0.2"
mood = "wildcard_anomaly"
description = "High-energy auroral displays during solar storms"

[[rules]]
name = "astronomical_night"
priority = 90
when = "solar.elevation_deg < -6 or solar.phase == 'astronomical_night'"
mood = "cosmic_void"
description = "Deep night sky after evening twilight"

[[rules]]
name = "crepuscular_twilight"
priority = 80
when = "solar.is_crepuscular or (0.0 <= solar.sin_elevation < 0.16)"
mood = "crepuscular"
description = "Golden hour and twilight around dawn and dusk"

[[rules]]
name = "heavy_soup_freezing"
priority = 70
when = "weather.humidity > 75 and weather.temperature < 8"
mood = "winter_gothic"
description = "Freezing fog and heavy winter moisture"

[[rules]]
name = "heavy_soup_sweltering"
priority = 69
when = "weather.humidity > 75 and weather.temperature > 22"
mood = "heavy_mist"
description = "Heavy tropical moisture or summer downpours"

[[rules]]
name = "heavy_soup_mild"
priority = 68
when = "weather.humidity > 75 or weather.is_raining"
mood = "pastoral_rain"
description = "Rainy or wet temperate weather"

[[rules]]
name = "blinding_dry_freezing"
priority = 65
when = "solar.estimated_lumens > 600 and weather.humidity < 40 and weather.temperature < 8"
mood = "glacial_stark"
description = "Crisp, blinding sunlight on cold dry air"

[[rules]]
name = "blinding_dry_sweltering"
priority = 64
when = "solar.estimated_lumens > 600 and weather.humidity < 40 and weather.temperature > 22"
mood = "crisp_sharp"
description = "Arid, intense sunlight"

[[rules]]
name = "blinding_comfortable_sweltering"
priority = 63
when = "solar.estimated_lumens > 600 and weather.temperature > 20"
mood = "pastoral_sun"
description = "Brilliant, warm sunny afternoon"

[[rules]]
name = "dim_freezing"
priority = 50
when = "solar.estimated_lumens < 250 and weather.temperature < 8"
mood = "cozy_hearth"
description = "Cold, dim overcast winter day"

[[rules]]
name = "dim_general"
priority = 40
when = "solar.estimated_lumens < 250"
mood = "nebula_diffuse"
description = "Diffuse daytime cloud canopy"
```

---

## Rule Context Variables

The following telemetry values are available within `when` expressions:

### Solar & Ephemerides (`solar.*`)

| Variable | Type | Description |
| :--- | :--- | :--- |
| `solar.elevation_deg` | float | Sun angle above local horizon in degrees (negative at night). |
| `solar.sin_elevation` | float | Sine of elevation angle ($-1.0$ to $1.0$). |
| `solar.estimated_lumens` | float | Calculated ground lumens attenuated by cloud cover ($0.0$ to $1000.0$). |
| `solar.phase` | string | Current phase: `"night"`, `"astronomical_night"`, `"nautical_twilight"`, `"civil_twilight"`, `"crepuscular"`, `"day"`. |
| `solar.is_day` | boolean | `true` when elevation angle is greater than $0^\circ$. |
| `solar.is_crepuscular` | boolean | `true` during golden hour and twilight transitions. |

### Space Weather (`space.*`)

| Variable | Type | Description |
| :--- | :--- | :--- |
| `space.kp_index` | float | Planetary geomagnetic disturbance index ($0.0$ to $9.0$). |
| `space.is_storm` | boolean | `true` when $\text{Kp} \ge 5.0$. |
| `space.activity` | string | Qualitative description: `"quiet"`, `"unsettled"`, `"active"`, `"minor_storm"`, `"severe_storm"`. |

### Terrestrial Weather (`weather.*`)

| Variable | Type | Description |
| :--- | :--- | :--- |
| `weather.temperature` | float | Ambient air temperature in degrees Celsius (°C). |
| `weather.humidity` | float | Relative humidity percentage ($0$ to $100$). |
| `weather.clouds` | float | Cloud canopy coverage percentage ($0$ to $100$). |
| `weather.precipitation_mm` | float | Precipitation rate in millimeters. |
| `weather.is_raining` | boolean | `true` if liquid precipitation is detected. |
| `weather.is_snowing` | boolean | `true` if frozen precipitation is detected. |
| `weather.is_foggy` | boolean | `true` if visibility is obscured by fog or mist. |

### Host & Temporal State (`system.*`)

| Variable | Type | Description |
| :--- | :--- | :--- |
| `system.hour` | integer | Local time hour ($0$ to $23$). |
| `system.minute` | integer | Local time minute ($0$ to $59$). |
| `system.weekday` | string | Day of the week: `"monday"` through `"sunday"`. |
| `system.season` | string | Current astronomical season: `"winter"`, `"spring"`, `"summer"`, `"autumn"`. |
| `system.battery_percent` | integer | Battery charge level ($0$ to $100$). |
| `system.is_charging` | boolean | `true` if AC power is connected and battery is charging. |

### Mathematical Functions

Expressions support standard Python numeric functions: `min(a, b)`, `max(a, b)`, `abs(x)`, `round(x)`, and `random()` (returns float in $[0.0, 1.0)$).
