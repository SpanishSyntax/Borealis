"""Tests for Borealis configuration loader."""

from pathlib import Path
from borealis.config import load_config


def test_load_config_defaults():
    cfg = load_config(None)
    assert cfg.backend_name in ("awww", "swww", "hyprpaper", "command")
    assert cfg.interval > 0
    assert len(cfg.wallpaper_dirs) >= 1


def test_load_config_custom(tmp_path: Path):
    cfg_file = tmp_path / "borealis.toml"
    cfg_file.write_text(
        '[general]\nbackend = "awww"\ninterval = 600\nwallpaper_dirs = ["/tmp/wallpapers"]\n',
        encoding="utf-8",
    )
    cfg = load_config(str(cfg_file))
    assert cfg.backend_name == "awww"
    assert cfg.interval == 600
    assert Path("/tmp/wallpapers") in cfg.wallpaper_dirs
