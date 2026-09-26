"""CLI entrypoint for Borealis."""

import argparse
import json
import logging
import sys
from pathlib import Path

from borealis import __app_name__, __version__
from borealis.config import load_config
from borealis.engine import BorealisEngine
from borealis.ui import ui


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_help():
    """Prints beautiful colored usage instructions matching Folio & Flaker."""
    print(f"""{ui.badge()} {ui.bold("Atmospheric & Astronomical Dynamic Wallpaper Engine")}

{ui.blue("Usage:")}
  borealis [command] [options]
  borealis [options]

{ui.blue("Commands:")}
  status       Display live telemetry dashboard (solar, weather, Kp-index, mood)
  once         Evaluate telemetry, apply wallpaper once, and exit
  dry-run      Evaluate telemetry and preview routing without applying
  list-tags    List all indexed wallpaper tags and asset counts
  run          Start continuous background wallpaper daemon

{ui.blue("Options:")}
  -c, --config PATH          Path to borealis.toml configuration file
  -d, --wallpaper-dir DIR    Path to wallpapers directory (can specify multiple)
  -b, --backend NAME         Override display backend (awww, swww, hyprpaper, command)
  -v, --verbose              Enable verbose debug logging
  -h, --help                 Show this help message and exit
  --version                  Show version and exit

{ui.blue("Examples:")}
  borealis                   # Display real-time telemetry dashboard & active mood
  borealis status            # Inspect atmospheric, solar, & space-weather state
  borealis once              # Evaluate and apply wallpaper immediately
  borealis dry-run           # Inspect calculated telemetry JSON without setting wallpaper
  borealis list-tags         # View all wallpaper categories & indexed counts
  borealis run               # Launch continuous background daemon
""")


def main() -> int:
    if any(a in ("-h", "--help", "help") for a in sys.argv[1:]):
        print_help()
        return 0

    if any(a in ("--version", "-V") for a in sys.argv[1:]) or (len(sys.argv) == 2 and sys.argv[1] in ("-v", "version")):
        print(f"{ui.badge()} {ui.bold(__version__)}")
        return 0

    config = load_config(None)

    # When run interactively without any subcommands or options, display dashboard!
    if len(sys.argv) == 1:
        engine = BorealisEngine(config)
        engine.print_status_dashboard()
        ui.info("Quick Commands: 'borealis once' to set wallpaper, 'borealis run' for daemon, 'borealis --help' for commands.", symbol="💡")
        return 0

    parser = argparse.ArgumentParser(
        prog=__app_name__,
        add_help=False,
    )
    parser.add_argument(
        "-c",
        "--config",
        type=str,
        help="Path to borealis.toml configuration file",
    )
    parser.add_argument(
        "-d",
        "--wallpaper-dir",
        action="append",
        type=str,
        help="Path to wallpapers directory (can be specified multiple times to index multiple directories)",
    )
    parser.add_argument(
        "-b",
        "--backend",
        type=str,
        choices=["awww", "swww", "hyprpaper", "command"],
        help="Override wallpaper backend",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose debug logging",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    subparsers.add_parser("run", help="Start continuous background wallpaper daemon")
    subparsers.add_parser("once", help="Evaluate telemetry, apply wallpaper once, and exit")
    subparsers.add_parser("status", help="Display current telemetry dashboard without changing wallpaper")
    subparsers.add_parser("dry-run", help="Evaluate telemetry and pick wallpaper without applying it")
    subparsers.add_parser("list-tags", help="List all indexed wallpaper tags and item counts")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Load configuration (with explicit config file if provided)
    if args.config:
        config = load_config(args.config)

    # CLI overrides
    if args.wallpaper_dir:
        config.wallpaper_dirs = [Path(d).expanduser().resolve() for d in args.wallpaper_dir]
        config.wallpaper_dir = config.wallpaper_dirs[0]
    if args.backend:
        config.backend_name = args.backend

    command = args.command or "status"

    engine = BorealisEngine(config)

    if command == "status":
        engine.print_status_dashboard()
        return 0

    elif command == "dry-run":
        res = engine.tick(dry_run=True)
        ui.info(f"Dry-run evaluation complete (Mood: {ui.bold(str(res.get('mood')))}, Rule: {ui.cyan(str(res.get('rule')))})", symbol="🔍")
        print(json.dumps(res, indent=2))
        return 0

    elif command == "list-tags":
        tags = engine.library.get_tag_counts()
        ui.header("BOREALIS WALLPAPER LIBRARY TAGS", width=72)
        ui.info(f"Total wallpapers indexed: {ui.bold(str(len(engine.library.items)))}", symbol="📊")
        dirs_str = ", ".join(str(d) for d in config.wallpaper_dirs)
        ui.info(f"Repositories: {ui.cyan(dirs_str)}", symbol="📁")
        print(ui.dim("-" * 72))
        tag_hdr = ui.bold(f"{'TAG':<25}")
        count_hdr = ui.bold("COUNT")
        print(f"  {tag_hdr}   {count_hdr}")
        print(f"  {ui.dim('-' * 25)}   {ui.dim('-' * 10)}")
        for tag, count in tags.items():
            t_col = ui.cyan(f"{tag:<25}")
            print(f"  {t_col} : {ui.bold(str(count))} wallpapers")
        print(ui.blue("=" * 72) + "\n")
        return 0

    elif command == "once":
        res = engine.tick(dry_run=False)
        if res.get("applied"):
            ui.success(f"Applied {ui.bold(str(res.get('wallpaper')))} (Mood: {ui.cyan(str(res.get('mood')))})")
            return 0
        else:
            ui.error(f"Failed to apply wallpaper: {res.get('wallpaper')}")
            return 1

    elif command == "run":
        ui.action(f"Starting Borealis wallpaper daemon using backend '{ui.bold(config.backend_name)}'...", symbol="🌌")
        engine.run_daemon()
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
