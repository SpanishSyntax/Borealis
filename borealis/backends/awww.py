"""Awww backend implementation for Wayland desktop environments."""

import shutil
import subprocess
import time
from pathlib import Path
from borealis.backends.base import BaseBackend


class AwwwBackend(BaseBackend):
    """Integrates with awww-daemon and awww CLI."""

    def __init__(self, transition_type: str = "simple", transition_step: int = 90) -> None:
        super().__init__("awww")
        self.transition_type = transition_type
        self.transition_step = transition_step

    def ensure_daemon(self) -> None:
        """Start awww-daemon in background if not already active."""
        if shutil.which("awww-daemon") is None:
            return

        # Check if awww-daemon process is running
        check = subprocess.run(["pgrep", "-x", "awww-daemon"], stdout=subprocess.DEVNULL)
        if check.returncode != 0:
            try:
                subprocess.Popen(
                    ["awww-daemon"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                time.sleep(1)
            except Exception:
                pass

    def apply(self, image_path: Path) -> bool:
        self.ensure_daemon()
        if shutil.which("awww") is None:
            return False

        cmd = ["awww", "img", str(image_path)]
        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            return res.returncode == 0
        except Exception:
            return False
