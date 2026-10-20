"""Tests for Borealis wallpaper library indexing and tag matching."""

from pathlib import Path
from borealis.library import WallpaperItem, WallpaperLibrary


def test_wallpaper_item():
    p = Path("/wallpapers/cosmic_void/nebula_dark.png")
    item = WallpaperItem(p, tags={"cosmic_void", "nebula"})
    assert "nebula_dark.png" in str(item.path)
    assert "cosmic_void" in item.tags
    assert "nebula" in item.tags
    assert item.matches({"cosmic_void"})


def test_wallpaper_library(tmp_path: Path):
    cat_dir = tmp_path / "night"
    cat_dir.mkdir()
    (cat_dir / "milky_way.jpg").write_text("fake_image", encoding="utf-8")
    (cat_dir / "aurora_borealis.png").write_text("fake_image", encoding="utf-8")

    lib = WallpaperLibrary([tmp_path])
    counts = lib.get_tag_counts()
    assert "night" in counts
    assert counts["night"] == 2

    chosen = lib.select("night")
    assert chosen is not None
    assert chosen.exists()
