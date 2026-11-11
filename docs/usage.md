# CLI & Operations Reference

This guide covers operational commands, debugging recipes, and wallpaper indexing workflows for Borealis.

---

## CLI Commands

The `borealis` executable provides several execution modes:

```bash
# Display live telemetry dashboard (default when run without arguments)
borealis status

# Apply a wallpaper from a specific mood or tag immediately
borealis set cosmic_void

# Point set directly to an image file
borealis set ~/Pictures/nordic_fjord.jpg

# Evaluate atmospheric telemetry, apply wallpaper once, and exit
borealis once

# Run dry-run evaluation and output calculated values without applying
borealis dry-run

# List all discovered wallpaper tags and indexed counts
borealis list-tags

# Launch continuous background daemon
borealis run
```

---

## Options Reference

| Flag | Argument | Description |
| :--- | :--- | :--- |
| `-c`, `--config` | `<path>` | Explicit path to `borealis.toml` configuration file |
| `-d`, `--wallpaper-dir` | `<dir>` | Path to wallpapers directory (can be specified multiple times) |
| `-b`, `--backend` | `name` | Override display backend (`awww`, `swww`, `hyprpaper`, `command`) |
| `-v`, `--verbose` | None | Enable verbose debug logging output |
| `-A`, `--agent` | None | Compact, machine-friendly plain text output format |
| `--json` | None | Emits structured JSON output (ideal for scripting and bar widgets) |
| `--color` | `mode` | Terminal ANSI color mode: `auto`, `always`, or `never` |
| `-h`, `--help` | None | Print command line help documentation |
| `-V`, `--version` | None | Display version information |

---

## Live Telemetry Dashboard

Running `borealis status` renders an instant diagnostic breakdown of environmental conditions:

```text
========================================================================
 BOREALIS TELEMETRY DASHBOARD | 2026-11-11 02:30:00
========================================================================
  Geographic Origin         : Oslo, Norway (LAT: 59.91, LON: 10.75)
  Solar Elevation           : -32.14° (astronomical_night)
  Atmospheric Lumens        : 0.0 lm (sin_elev: -0.532)
------------------------------------------------------------------------
  Thermal State             : -2°C (Clear)
  Moisture Content          : 74% (Rain: False)
  Cloud Canopy              : 12%
  Geomagnetic Scale         : Kp-Index 2.3 (quiet)
------------------------------------------------------------------------
  Local Temporal State      : Wednesday 02:30 (autumn)
  Battery Telemetry         : 100% (AC Connected)
------------------------------------------------------------------------
  ACTIVE MOOD VECTOR        : cosmic_void (tags: cosmic_void, night)
  Decision Origin           : Matched Rule 'astronomical_night'
  Candidate Wallpaper       : Caspar_David_Friedrich_Abtei.jpg
  Wallpaper Library         : 142 assets indexed from /home/user/Pictures/Wallpapers
========================================================================
```

### Scripting with JSON Output

Combine `--json` with `jq` to integrate Borealis state into Waybar, Eww, or desktop widgets:

```bash
borealis status --json | jq '{mood: .active_mood, rule: .matched_rule, kp: .space.kp_index}'
```

---

## Wallpaper Indexing Strategies

Borealis pools wallpapers from multiple directories while supporting three simultaneous metadata methods:

### 1. Bracketed Filename Tags

Add bracketed comma-separated tags directly to image filenames:

```text
pictures/wallpapers/
├── arctic_tundra[glacial_stark,cold,day].png
├── northern_lights[wildcard_anomaly,night,aurora].jpg
└── misty_forest[winter_gothic,rain].webp
```

An image containing multiple tags is eligible for selection whenever any of those moods match.

### 2. Directory Hierarchy

Subdirectories automatically map their folder names as tags:

```text
pictures/wallpapers/
├── cosmic_void/
│   ├── deep_field.png
│   └── obsidian_monolith.jpg
├── pastoral_sun/
│   └── summer_meadow.jpg
└── wildcard_anomaly/
    └── solar_flare.jpg
```

### 3. Explicit Manifests (`wallpapers.toml`)

For advanced tuning, place `wallpapers.toml` inside your wallpaper directory:

```toml
[[wallpaper]]
file = "rare_aurora.jpg"
tags = ["wildcard_anomaly", "cosmic_void"]
weight = 3.0 # Displays 3x as often as standard wallpapers

[[wallpaper]]
file = "heavy_monsoon.jpg"
tags = ["pastoral_rain"]
weight = 1.0
```

---

## Daemon Operation Recipes

### Managing User Service

When deployed via Home Manager, Borealis runs as a systemd user service:

```bash
# Check service status
systemctl --user status borealis.service

# View live log output
journalctl --user -u borealis.service -f

# Restart daemon after editing rules
systemctl --user restart borealis.service
```

### Testing Rule Routing with Dry Run

Test how current atmospheric conditions evaluate against your rules without altering your desktop wallpaper:

```bash
borealis dry-run
```
