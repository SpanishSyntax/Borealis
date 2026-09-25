"""Backend registry and factory for Borealis wallpaper engines."""

from typing import Any, Dict
from borealis.backends.additional import CommandBackend, HyprpaperBackend, SwwwBackend
from borealis.backends.awww import AwwwBackend
from borealis.backends.base import BaseBackend


def get_backend(name: str, config: Dict[str, Any]) -> BaseBackend:
    """Instantiate a wallpaper backend by name."""
    name_lower = name.lower()
    if name_lower == "awww":
        return AwwwBackend(
            transition_type=config.get("transition_type", "simple"),
            transition_step=int(config.get("transition_step", 90)),
        )
    elif name_lower == "swww":
        return SwwwBackend(
            transition_type=config.get("transition_type", "fade"),
            transition_step=int(config.get("transition_step", 90)),
        )
    elif name_lower == "hyprpaper":
        return HyprpaperBackend()
    elif name_lower == "command":
        template = config.get("command_template", "echo {path}")
        return CommandBackend(template)
    else:
        # Default to awww
        return AwwwBackend()
