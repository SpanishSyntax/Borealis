"""Base backend interface for setting desktop wallpapers."""

from abc import ABC, abstractmethod
from pathlib import Path


class BaseBackend(ABC):
    """Abstract base class for wallpaper display backends."""

    def __init__(self, name: str) -> None:
        self.name = name

    def ensure_daemon(self) -> None:
        """Ensure necessary wallpaper background daemon is active."""
        pass

    @abstractmethod
    def apply(self, image_path: Path) -> bool:
        """Apply the specified image to the desktop environment. Returns True on success."""
        pass
