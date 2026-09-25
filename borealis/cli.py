"""CLI entrypoint for Borealis."""

import argparse
import json
import logging
import sys
from pathlib import Path

from borealis import __app_name__, __version__
from borealis.config import load_config
from borealis.engine import BorealisEngine


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        prog=__app_name__,
        description="Borealis - Atmospheric & Astronomical Dynamic Wallpaper Engine",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{__app_name__} {__version__}",
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

    # run (default daemon mode)
    subparsers.add_parser("run", help="Start continuous background wallpaper daemon")

    # once
    subparsers.add_parser("once", help="Evaluate telemetry, apply wallpaper once, and exit")

    # status
    subparsers.add_parser("status", help="Display current telemetry dashboard without changing wallpaper")

    # dry-run
    subparsers.add_parser("dry-run", help="Evaluate telemetry and pick wallpaper without applying it")

    # list-tags
    subparsers.add_parser("list-tags", help="List all indexed wallpaper tags and item counts")

    args = parser.parse_args()
    setup_logging(args.verbose)

    # Load configuration
    config = load_config(args.config)

    # CLI overrides
    if args.wallpaper_dir:
        config.wallpaper_dirs = [Path(d).expanduser().resolve() for d in args.wallpaper_dir]
        config.wallpaper_dir = config.wallpaper_dirs[0]
    if args.backend:
        config.backend_name = args.backend

    # Default to run if no command specified
    command = args.command or "run"

    engine = BorealisEngine(config)

    if command == "status":
        engine.print_status_dashboard()
        return 0

    elif command == "dry-run":
        res = engine.tick(dry_run=True)
        print(json.dumps(res, indent=2))
        return 0

    elif command == "list-tags":
        tags = engine.library.get_tag_counts()
        print(f"Total wallpapers indexed: {len(engine.library.items)}")
        print(f"Directory: {config.wallpaper_dir}")
        print("-" * 40)
        for tag, count in tags.items():
            print(f"  {tag:<25} : {count} wallpapers")
        return 0

    elif command == "once":
        res = engine.tick(dry_run=False)
        print(f"Applied {res.get('wallpaper')} (Mood: {res.get('mood')})")
        return 0 if res.get("applied") else 1

    elif command == "run":
        engine.run_daemon()
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
