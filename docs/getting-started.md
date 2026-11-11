# Getting Started

This guide details installation options, prerequisites, and quick-start instructions for Borealis.

---

## Prerequisites

- **Linux / Wayland** desktop session (Hyprland, Sway, River, Niri, GNOME on Wayland, KDE Plasma).
- **Wallpaper backend**:
  - `awww` (recommended, lightweight Wayland wallpaper daemon)
  - `swww`
  - `hyprpaper`
  - Any external command supporting image paths via custom command template (e.g. `feh`, `swaybg`).
- **Python $\ge$ 3.10** (standard library only; zero external runtime pip requirements).

---

## Installation

### Nix / NixOS Flake (Home Manager)

Add Borealis to your `flake.nix`:

```nix
{
  inputs = {
    nixpkgs.url = "github:nixos/nixpkgs/nixos-unstable";
    borealis.url = "github:SpanishSyntax/Borealis";
  };

  outputs = { self, nixpkgs, borealis, ... }: {
    homeConfigurations.user = home-manager.lib.homeManagerConfiguration {
      modules = [
        borealis.homeManagerModules.default
        {
          services.borealis = {
            enable = true;
            backend = "awww";             # "awww" | "swww" | "hyprpaper" | "command"
            interval = 20;                # Wallpaper rotation interval (seconds)
            telemetryInterval = 900;      # Atmospheric polling interval (seconds)
            includeDefaultWallpapers = true; # Curated art pack from GitHub Releases
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

This automatically configures:
1. Installation of the `borealis` package and `awww` backend.
2. Generating `~/.config/borealis/borealis.toml` if settings are declared.
3. Systemd user service `borealis.service` bound to `graphical-session.target`.

---

### NixOS System Module

To install the `borealis` CLI system-wide:

```nix
{
  imports = [ borealis.nixosModules.default ];

  programs.borealis.enable = true;
}
```

---

### Direct Execution with Nix

Test or run Borealis without installing:

```bash
# Display live telemetry dashboard
nix run github:SpanishSyntax/Borealis

# Evaluate telemetry and apply wallpaper once
nix run github:SpanishSyntax/Borealis -- once

# Start the continuous daemon
nix run github:SpanishSyntax/Borealis -- run
```

---

### Manual / pip Installation

```bash
# Clone the repository
git clone https://github.com/SpanishSyntax/Borealis.git ~/Borealis
cd ~/Borealis

# Install package in editable or standard mode
pip install -e .
```

---

## Quick Start

### 1. Inspect Current Telemetry

Run `borealis status` (or simply `borealis`):

```bash
borealis status
```

This contacts NOAA and Open-Meteo, calculates local solar angles and atmospheric lumens, evaluates declarative rules, and prints the active mood vector.

### 2. Immediate Wallpaper Override

Force the wallpaper to match a specific mood or tag:

```bash
borealis set cosmic_void
```

### 3. List Available Tags

Inspect all discovered wallpaper categories and counts:

```bash
borealis list-tags
```

### 4. Run Single Evaluation

Evaluate atmospheric conditions and apply the appropriate wallpaper once:

```bash
borealis once
```

### 5. Start Background Daemon

Launch the daemon in the foreground or as a user service:

```bash
borealis run
```
