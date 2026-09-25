# Borealis 🌌❄️

> **Atmospheric, Astronomical & Space-Weather Dynamic Wallpaper Engine for Linux & Wayland**

Borealis is a telemetry-driven dynamic wallpaper daemon that continuously synchronizes your desktop ambiance with celestial mechanics, real-time planetary weather, and geomagnetic solar storms.

---

## ✨ Features

- 🔭 **Astronomical & Celestial Engine**:
  - Calculates real-time solar declination, orbital zenith, and solar elevation angle using spherical orbital mechanics.
  - Automatically identifies twilight stages: *astronomical night*, *nautical twilight*, *civil twilight*, *golden hour (crepuscular)*, and *high day*.
  - Calculates ground-level solar lumens attenuated non-linearly by real-time cloud canopy density.
- ☀️ **Space Weather & Geomagnetic Telemetry**:
  - Direct integration with NOAA Space Weather Prediction Center.
  - Detects solar winds and geomagnetic storms in real time via the planetary Kp-index ($\ge 5$).
- 🌧️ **Terrestrial Weather Telemetry**:
  - Real-time cloud canopy, humidity, temperature, and precipitation parsing.
- ⚡ **Host & Environmental Telemetry**:
  - Battery capacity and charging status detection.
  - Temporal rhythms, day-of-week, and seasonal transitions.
- 🎛️ **Declarative Rule Engine (`borealis.toml`)**:
  - Configure decision-making using intuitive boolean expressions without writing code.
  - Customizable priorities, custom moods, and fallback chains.
- 🏷️ **Smart Wallpaper Library (Beyond Simple Directories)**:
  - **Filename Tags**: Name files `artwork[cosmic_void,night].jpg` to index multiple moods on one image.
  - **Directory Hierarchy**: Out-of-the-box support for nested mood directories (`wallpapers/cosmic_void/`).
  - **Manifest Support**: Optional `wallpapers.toml` for explicit weights and metadata.
  - **Anti-Repetition Memory**: Prevents consecutive image repeats across cycles.
- 🔌 **Pluggable Backends**:
  - [`awww`](https://codeberg.org/LGFae/awww) (default)
  - [`swww`](https://github.com/LGFae/swww)
  - [`hyprpaper`](https://github.com/hyprwm/hyprpaper)
  - Custom shell command template (`feh`, `swaybg`, `mpvpaper`, etc.)
- ❄️ **Nix-Native**:
  - 100% pure standard library Python core (<30ms startup, zero runtime pip dependencies).
  - Built-in Home Manager systemd user service module.

---

## 🚀 Quick Start

Run Borealis directly using Nix:

```bash
# View live telemetry dashboard and current selected mood
nix run github:SpanishSyntax/Borealis -- status

# Inspect indexed wallpapers and mood tags
nix run github:SpanishSyntax/Borealis -- list-tags

# Run dry-run evaluation
nix run github:SpanishSyntax/Borealis -- dry-run

# Start the continuous background daemon
nix run github:SpanishSyntax/Borealis -- run
```

---

## 📊 Live Dashboard Preview

Running `borealis status` displays an instant diagnostic view of all atmospheric sensors:

```text
========================================================================
 BOREALIS TELEMETRY DASHBOARD | 2026-09-25 21:29:00
========================================================================
  Geographic Origin         : Foo, Bar (LAT: 00.00, LON: 00.00)
  Solar Elevation           : -30.77° (astronomical_night)
  Atmospheric Lumens        : 0.0 lm (sin_elev: -0.512)
------------------------------------------------------------------------
  Thermal State             : 14°C (Clear)
  Moisture Content          : 66% (Rain: False)
  Cloud Canopy              : 0%
  Geomagnetic Scale         : Kp-Index 0.0 (quiet)
------------------------------------------------------------------------
  Local Temporal State      : Friday 21:29 (autumn)
  Battery Telemetry         : 96% (Charging)
------------------------------------------------------------------------
  ACTIVE MOOD VECTOR        : cosmic_void (tags: cosmic_void, night)
  Decision Origin           : Matched Rule 'astronomical_night'
  Candidate Wallpaper       : Caspar_David_Friedrich_Abtei.jpg
  Wallpaper Library         : 79 assets indexed from wallpapers/
========================================================================
```

---

## 🛠️ Home Manager Configuration

Add Borealis to your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    borealis.url = "github:SpanishSyntax/Borealis";
  };

  outputs = { self, nixpkgs, borealis, ... }: {
    # In your Home Manager configuration:
    homeManagerConfigurations.user = home-manager.lib.homeManagerConfiguration {
      modules = [
        borealis.homeManagerModules.default
        {
          services.borealis = {
            enable = true;
            backend = "awww";             # "awww" | "swww" | "hyprpaper" | "command"
            interval = 20;                # Wallpaper switch interval in seconds
            telemetryInterval = 900;      # Weather/telemetry poll interval (15 min)

            # Lazy download flag: set to false to use purely your own wallpapers
            # without downloading the 400 MB curated art pack from GitHub Releases:
            includeDefaultWallpapers = true;

            # Additional user wallpaper directories to pool alongside the default pack:
            extraWallpaperDirs = [
              "${config.home.homeDirectory}/Pictures/Wallpapers"
            ];
          };
        }
      ];
    };
  };
}
```

Borealis automatically provisions a `systemd.user.service` bound to `graphical-session.target`.

---

## ⚙️ Declarative Rules (`borealis.toml`)

Place your configuration at `~/.config/borealis/borealis.toml` or define via `services.borealis.settings`.

```toml
[general]
backend = "awww"
interval = 20
telemetry_interval = 900

# Overwrite location (defaults to automatic IP geolocation)
# [location]
# latitude = 0.0
# longitude = 0.0

[[rules]]
name = "geomagnetic_storm"
priority = 100
when = "space.kp_index >= 5 and random() > 0.2"
mood = "wildcard_anomaly"

[[rules]]
name = "astronomical_night"
priority = 90
when = "solar.elevation_deg < -6 or solar.phase == 'astronomical_night'"
mood = "cosmic_void"

[[rules]]
name = "golden_hour"
priority = 80
when = "solar.is_crepuscular or (0.0 <= solar.sin_elevation < 0.16)"
mood = "crepuscular"

[[rules]]
name = "winter_rain"
priority = 70
when = "weather.humidity > 75 and weather.temperature < 8"
mood = "winter_gothic"
```

### Context Variables Available in Rules:
- **`solar`**: `elevation_deg`, `sin_elevation`, `estimated_lumens`, `phase`, `is_day`, `is_crepuscular`
- **`space`**: `kp_index`, `is_storm`, `activity` (`quiet`, `unsettled`, `minor_storm`, `severe_storm`)
- **`weather`**: `temperature` (°C), `humidity` (%), `clouds` (%), `precipitation_mm`, `is_raining`, `is_snowing`, `is_foggy`
- **`system`**: `hour`, `minute`, `weekday`, `season` (`winter`, `spring`, `summer`, `autumn`), `battery_percent`, `is_charging`
- **Functions**: `random()`, `min()`, `max()`, `abs()`, `round()`

---

## 🏷️ Organizing Wallpapers

Borealis supports three simultaneous discovery methods:

1. **Filename Tags**:
   ```text
   neo_tokyo[cosmic_void,night,rain].jpg
   alpine_blizzard[glacial_stark,cold].png
   ```
2. **Directory Folders**:
   ```text
   wallpapers/
   ├── cosmic_void/
   ├── pastoral_sun/
   └── winter_gothic/
   ```
3. **Manifest file (`wallpapers.toml`)**:
   ```toml
   [[wallpaper]]
   file = "custom_image.jpg"
   tags = ["cosmic_void", "wildcard_anomaly"]
   weight = 2.0  # Appears twice as often
   ```

---

## 📜 License

MIT © SpanishSyntax
