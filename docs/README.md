<p align="center">
  <img src="assets/banner.png" alt="Borealis Banner" width="100%" />
</p>

# Borealis 🌌

An atmospheric, astronomical, and space-weather dynamic wallpaper engine for Linux and Wayland.

Borealis is a telemetry-driven background daemon that synchronizes desktop wallpaper ambiance with celestial orbital mechanics, real-time atmospheric weather, and planetary geomagnetic solar storms.

> [!TIP]
> **Complete Documentation:** Rule expression references, Home Manager options, telemetry variable definitions, and display backend configuration are available on the **[Documentation Site](https://spanishsyntax.github.io/Borealis)**.

---

## Why "Borealis"? (The Lore)

> **aurora borealis** (`/ˌbɔː.riˈæl.ɪs/`) — *noun:* The luminous celestial curtain of green, violet, and crimson ribbons that dances across high-latitude polar skies, sparked by solar wind colliding with Earth's magnetosphere.

The polar night is never static; its sky pulses with the rhythmic ebb and flow of space weather, geomagnetic storms, and the silent turn of the planetary axis.

**Borealis mirrors the living polar sky on your desktop:**
- **Telemetry-Driven Ambiance**: Continuously synchronizes Wayland desktop wallpapers with live geomagnetic disturbance indices (Kp), solar wind velocity, and local solar ephemerides.
- **Autonomous Transitions**: Shifts smoothly between daylight radiance, twilight gradients, and dancing auroral displays without abrupt background flashes or heavy GPU overhead.

---

## Features

- **Astronomical & Celestial Engine**:
  - Calculates real-time solar declination, orbital zenith, and solar elevation angle using spherical orbital mechanics.
  - Automatically identifies twilight stages: *astronomical night*, *nautical twilight*, *civil twilight*, *golden hour (crepuscular)*, and *high day*.
  - Calculates ground-level solar lumens attenuated non-linearly by real-time cloud canopy density.
- **Space Weather & Geomagnetic Telemetry**:
  - Direct integration with the NOAA Space Weather Prediction Center.
  - Detects solar winds and geomagnetic storms in real time via the planetary Kp-index ($\ge 5$).
- **Terrestrial Weather Telemetry**:
  - Real-time cloud canopy, humidity, temperature, and precipitation parsing.
- **Host & Environmental Telemetry**:
  - Battery capacity and charging status detection.
  - Temporal rhythms, day-of-week, and seasonal transitions.
- **Declarative Rule Engine (`borealis.toml`)**:
  - Configure decision-making using intuitive boolean expressions without writing code.
  - Customizable priorities, custom moods, and fallback chains.
- **Smart Wallpaper Library**:
  - **Filename Tags**: Name files `artwork[cosmic_void,night].jpg` to index multiple moods on one image.
  - **Directory Hierarchy**: Out-of-the-box support for nested mood directories (`wallpapers/cosmic_void/`).
  - **Manifest Support**: Optional `wallpapers.toml` for explicit weights and metadata.
  - **Anti-Repetition Memory**: Prevents consecutive image repeats across cycles.
- **Pluggable Backends**:
  - `awww` (default, high-performance Wayland daemon)
  - `swww`
  - `hyprpaper`
  - Custom shell command template (`feh`, `swaybg`, `mpvpaper`, etc.)
- **Nix-Native Architecture**:
  - Pure standard library Python core (<30ms startup, zero runtime pip dependencies).
  - Built-in Home Manager and NixOS system service modules.

---

## Table of Contents

- [Getting Started](getting-started.md)
  - [Installation Guide](getting-started.md#installation)
  - [Nix & Home Manager Setup](getting-started.md#nix--home-manager-setup)
  - [Quick Start](getting-started.md#quick-start)
- [Architecture & Foundations](architecture.md)
  - [The Lore](architecture.md#why-borealis-the-lore)
  - [Telemetry Sensing Pipeline](architecture.md#telemetry-sensing-pipeline)
  - [Astronomical Mechanics & Solar Phases](architecture.md#astronomical-mechanics--solar-phases)
  - [Space Weather & Geomagnetic Storms](architecture.md#space-weather--geomagnetic-storms)
  - [Rule Engine Architecture](architecture.md#rule-engine-architecture)
  - [Display Backends](architecture.md#display-backends)
- [Configuration Guide](configuration.md)
  - [borealis.toml Reference](configuration.md#borealistoml-reference)
  - [Home Manager Module Options](configuration.md#home-manager-module-options)
  - [NixOS System Module](configuration.md#nixos-system-module)
  - [Declarative Rule Syntax](configuration.md#declarative-rule-syntax)
  - [Rule Context Variables](configuration.md#rule-context-variables)
- [CLI & Operations](usage.md)
  - [CLI Commands](usage.md#cli-commands)
  - [Options Reference](usage.md#options-reference)
  - [Live Telemetry Dashboard](usage.md#live-telemetry-dashboard)
  - [Wallpaper Indexing Strategies](usage.md#wallpaper-indexing-strategies)
  - [Daemon Operation Recipes](usage.md#daemon-operation-recipes)
