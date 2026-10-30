"""CLI entrypoint for Borealis."""

import argparse
import json
import logging
import sys
from pathlib import Path

from borealis import __app_name__, __version__
from borealis.config import load_config
from borealis.engine import BorealisEngine
from borealis.ui import add_color_args, handle_color_args, ui


def setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def print_help():
    """Prints beautiful colored usage instructions matching Folio & Flaker."""
    if ui.is_agent:
        print(f"""Borealis v{__version__} - Atmospheric & Astronomical Dynamic Wallpaper Engine
Usage: borealis [command] [options]

Commands:
  status                 Display live telemetry dashboard (solar, weather, mood)
  set <tag>              Apply a wallpaper matching tag, mood, or image file
  once                   Evaluate telemetry, apply wallpaper once, and exit
  dry-run                Evaluate telemetry and preview routing without applying
  list-tags              List all indexed wallpaper tags and asset counts
  run                    Start continuous background wallpaper daemon

Options:
  -A, --agent            Compact machine/agent friendly output mode
  --json                 Structured JSON output mode
  -c, --config PATH      Path to borealis.toml configuration file
  -d, --wallpaper-dir DIR Path to wallpapers directory
  -b, --backend NAME     Override display backend (awww, swww, hyprpaper, command)
  -v, --verbose          Enable verbose debug logging
  --color MODE           Color output mode: auto, always, never
  --no-color             Disable colored output
  -h, --help             Show this help message and exit
  -V, --version          Show version and exit
""")
        return

    print(f"""{ui.badge()} {ui.bold("Atmospheric & Astronomical Dynamic Wallpaper Engine")}

{ui.blue("Usage:")}
  borealis [status] [options]        Display live telemetry dashboard (default)
  borealis <command> [options]

{ui.blue("Commands:")}
  status       Display live telemetry dashboard (solar, weather, Kp-index, mood)
  set <tag>    Immediately apply a wallpaper matching a tag, mood, or image file
  once         Evaluate telemetry, apply wallpaper once, and exit
  dry-run      Evaluate telemetry and preview routing without applying
  list-tags    List all indexed wallpaper tags and asset counts
  run          Start continuous background wallpaper daemon

{ui.blue("Options:")}
  -c, --config PATH          Path to borealis.toml configuration file
  -d, --wallpaper-dir DIR    Path to wallpapers directory (can specify multiple)
  -b, --backend NAME         Override display backend (awww, swww, hyprpaper, command)
  -v, --verbose              Enable verbose debug logging
  --color MODE               Color output mode: auto, always, never (default: auto)
  --no-color                 Disable colored output
  -h, --help                 Show this help message and exit
  -V, --version              Show version and exit

{ui.blue("Examples:")}
  borealis                   # Display real-time telemetry dashboard & active mood
  borealis set cosmic_void   # Immediately apply a wallpaper from the 'cosmic_void' tag
  borealis once              # Evaluate telemetry and apply appropriate wallpaper
  borealis dry-run           # Inspect calculated telemetry JSON without setting wallpaper
  borealis list-tags         # View all wallpaper categories & indexed counts
  borealis run               # Launch continuous background daemon
""")


def main(argv: list[str] | None = None) -> int:
    raw_args = list(argv) if argv is not None else sys.argv[1:]
    handle_color_args(raw_args)

    if any(a in ("-h", "--help", "help") for a in raw_args):
        print_help()
        return 0

    if ui.handle_version_arg(raw_args, __version__):
        return 0

    config = load_config(None)

    # When run interactively without any subcommands or options, display dashboard!
    if not raw_args:
        engine = BorealisEngine(config)
        engine.print_status_dashboard()
        if ui.is_interactive:
            action = ui.select(
                "Quick Actions:",
                [
                    ("exit", "Keep current state and exit"),
                    ("once", "Evaluate telemetry and apply matching wallpaper"),
                    ("set", "Pick a tag / mood and set wallpaper immediately"),
                    ("list-tags", "List all indexed wallpaper tags and counts"),
                    (
                        "dry-run",
                        "Preview telemetry evaluation without changing wallpaper",
                    ),
                    ("run", "Start continuous background daemon"),
                ],
            )
            if action == "exit":
                return 0
            elif action == "once":
                res = engine.tick(dry_run=False)
                if res.get("applied"):
                    ui.success(
                        f"Applied {ui.bold(str(res.get('wallpaper')))} (Mood: {ui.cyan(str(res.get('mood')))})"
                    )
                    return 0
                else:
                    ui.error(f"Failed to apply wallpaper: {res.get('wallpaper')}")
                    return 1
            elif action == "set":
                tags = engine.library.get_tag_counts()
                if tags:
                    options = [
                        (t, f"{t:<20} ({c} wallpapers)") for t, c in tags.items()
                    ]
                    chosen_tag = ui.select("Select wallpaper tag or mood:", options)
                    path = engine.set_wallpaper(chosen_tag)
                    if path:
                        ui.success(
                            f"Applied wallpaper {ui.bold(path.name)} for tag '{ui.cyan(chosen_tag)}'"
                        )
                        return 0
                    else:
                        ui.error(f"No wallpapers found matching '{chosen_tag}'.")
                        return 1
                else:
                    ui.warn("No wallpaper tags indexed.")
                    return 0
            elif action == "list-tags":
                tags = engine.library.get_tag_counts()
                dirs_str = ", ".join(str(d) for d in config.wallpaper_dirs)
                lines = [
                    f"{ui.bold('Total Wallpapers:')}  {len(engine.library.items)} indexed",
                    f"{ui.bold('Repositories:')}      {ui.dim(dirs_str)}",
                    "",
                    f"{ui.bold('TAG'):<28} {ui.bold('COUNT')}",
                    ui.dim("-" * 42),
                ]
                for tag, count in tags.items():
                    lines.append(f"{ui.cyan(tag):<35} {ui.bold(str(count))} wallpapers")
                ui.panel("BOREALIS WALLPAPER LIBRARY TAGS", lines)
                return 0
            elif action == "dry-run":
                res = engine.tick(dry_run=True)
                ui.info(
                    f"Dry-run evaluation complete (Mood: {ui.bold(str(res.get('mood')))}, Rule: {ui.cyan(str(res.get('rule')))})",
                    symbol="🔍",
                )
                print(json.dumps(res, indent=2))
                return 0
            elif action == "run":
                ui.action(
                    f"Starting Borealis wallpaper daemon using backend '{ui.bold(config.backend_name)}'...",
                    symbol="🌌",
                )
                engine.run_daemon()
                return 0
        else:
            ui.info(
                "Quick Commands: 'borealis once' to set wallpaper, 'borealis run' for daemon, 'borealis --help' for commands.",
                symbol="💡",
            )
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
    add_color_args(parser)
    parser.add_argument(
        "-V",
        "--version",
        action="store_true",
        help="Show version and exit",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    p_run = subparsers.add_parser("run", help="Start continuous background wallpaper daemon")
    add_color_args(p_run)
    p_once = subparsers.add_parser(
        "once", help="Evaluate telemetry, apply wallpaper once, and exit"
    )
    add_color_args(p_once)
    p_status = subparsers.add_parser(
        "status", help="Display current telemetry dashboard without changing wallpaper"
    )
    add_color_args(p_status)
    p_dry_run = subparsers.add_parser(
        "dry-run", help="Evaluate telemetry and pick wallpaper without applying it"
    )
    add_color_args(p_dry_run)
    p_list_tags = subparsers.add_parser(
        "list-tags", help="List all indexed wallpaper tags and item counts"
    )
    add_color_args(p_list_tags)

    set_parser = subparsers.add_parser(
        "set", help="Immediately apply a wallpaper matching a tag, mood, or image file"
    )
    add_color_args(set_parser)
    set_parser.add_argument(
        "tag",
        nargs="?",
        default=None,
        help="Tag, mood name (e.g. cosmic_void, rain, aurora), or image path",
    )

    args = parser.parse_args(raw_args)
    if args.version:
        ui.version(__version__)
        return 0

    setup_logging(args.verbose)

    # Load configuration (with explicit config file if provided)
    if args.config:
        config = load_config(args.config)

    # CLI overrides
    if args.wallpaper_dir:
        config.wallpaper_dirs = [
            Path(d).expanduser().resolve() for d in args.wallpaper_dir
        ]
        config.wallpaper_dir = config.wallpaper_dirs[0]
    if args.backend:
        config.backend_name = args.backend

    command = args.command or "status"

    engine = BorealisEngine(config)

    if command == "status":
        engine.print_status_dashboard()
        return 0

    elif command == "set":
        tag = args.tag
        if not tag:
            if sys.stdin.isatty():
                tags = engine.library.get_tag_counts()
                if tags:
                    options = [
                        (t, f"{t:<20} ({c} wallpapers)") for t, c in tags.items()
                    ]
                    tag = ui.select("Select wallpaper tag or mood to apply:", options)
                else:
                    ui.error("No wallpaper tags indexed.")
                    return 1
            else:
                ui.error(
                    "Missing tag argument for 'borealis set'. Example: borealis set cosmic_void"
                )
                return 1

        path = engine.set_wallpaper(tag)
        if path:
            ui.success(
                f"Applied wallpaper {ui.bold(path.name)} for tag '{ui.cyan(tag)}'"
            )
            return 0
        else:
            ui.error(
                f"No wallpapers found matching '{tag}'. Run 'borealis list-tags' to see available tags."
            )
            return 1

    elif command == "dry-run":
        res = engine.tick(dry_run=True)
        ui.info(
            f"Dry-run evaluation complete (Mood: {ui.bold(str(res.get('mood')))}, Rule: {ui.cyan(str(res.get('rule')))})",
            symbol="🔍",
        )
        ui.json(res)
        return 0

    elif command == "list-tags":
        tags = engine.library.get_tag_counts()
        dirs_str = ", ".join(str(d) for d in config.wallpaper_dirs)
        lines = [
            f"{ui.bold('Total Wallpapers:')}  {len(engine.library.items)} indexed",
            f"{ui.bold('Repositories:')}      {ui.dim(dirs_str)}",
            "",
            f"{ui.bold('TAG'):<28} {ui.bold('COUNT')}",
            ui.dim("-" * 42),
        ]
        for tag, count in tags.items():
            lines.append(f"{ui.cyan(tag):<35} {ui.bold(str(count))} wallpapers")
        ui.panel("BOREALIS WALLPAPER LIBRARY TAGS", lines)
        return 0

    elif command == "once":
        res = engine.tick(dry_run=False)
        if res.get("applied"):
            ui.success(
                f"Applied {ui.bold(str(res.get('wallpaper')))} (Mood: {ui.cyan(str(res.get('mood')))})"
            )
            return 0
        else:
            ui.error(f"Failed to apply wallpaper: {res.get('wallpaper')}")
            return 1

    elif command == "run":
        ui.action(
            f"Starting Borealis wallpaper daemon using backend '{ui.bold(config.backend_name)}'...",
            symbol="🌌",
        )
        engine.run_daemon()
        return 0

    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
