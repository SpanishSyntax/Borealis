"""Additional wallpaper backends: swww, hyprpaper, and generic custom commands."""

import shutil
import subprocess
import time
from pathlib import Path
from borealis.backends.base import BaseBackend


class SwwwBackend(BaseBackend):
    """Integrates with swww-daemon and swww CLI."""

    def __init__(self, transition_type: str = "fade", transition_step: int = 90) -> None:
        super().__init__("swww")
        self.transition_type = transition_type
        self.transition_step = transition_step

    def ensure_daemon(self) -> None:
        if shutil.which("swww-daemon") is None:
            return
        check = subprocess.run(["swww", "query"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if check.returncode != 0:
            try:
                subprocess.Popen(
                    ["swww-daemon"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                time.sleep(1)
            except Exception:
                pass

    def apply(self, image_path: Path) -> bool:
        self.ensure_daemon()
        if shutil.which("swww") is None:
            return False

        cmd = [
            "swww",
            "img",
            str(image_path),
            "--transition-type",
            self.transition_type,
            "--transition-step",
            str(self.transition_step),
        ]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False


class HyprpaperBackend(BaseBackend):
    """Integrates with Hyprland's native hyprpaper."""

    def __init__(self) -> None:
        super().__init__("hyprpaper")

    def apply(self, image_path: Path) -> bool:
        if shutil.which("hyprctl") is None:
            return False

        p = str(image_path)
        try:
            # Preload and set wallpaper on all monitors
            subprocess.run(["hyprctl", "hyprpaper", "preload", p], stdout=subprocess.DEVNULL, timeout=4)
            res = subprocess.run(
                ["hyprctl", "hyprpaper", "wallpaper", f",{p}"],
                stdout=subprocess.DEVNULL,
                timeout=4,
            )
            return res.returncode == 0
        except Exception:
            return False


class CommandBackend(BaseBackend):
    """Executes a custom shell command template with {path} formatted."""

    def __init__(self, command_template: str) -> None:
        super().__init__("command")
        self.command_template = command_template

    def apply(self, image_path: Path) -> bool:
        cmd = self.command_template.format(path=str(image_path))
        try:
            res = subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False
