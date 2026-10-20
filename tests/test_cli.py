"""Tests for Borealis CLI parsing and status dashboard."""

from borealis import __version__
from borealis.cli import main


def test_cli_version(capsys):
    ret = main(["--version"])
    assert ret == 0
    captured = capsys.readouterr()
    assert f"v{__version__}" in captured.out


def test_cli_help(capsys):
    ret = main(["--help"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "Atmospheric & Astronomical Dynamic Wallpaper Engine" in captured.out


def test_cli_status(capsys):
    ret = main(["status"])
    assert ret == 0
    captured = capsys.readouterr()
    assert "BOREALIS TELEMETRY DASHBOARD" in captured.out
