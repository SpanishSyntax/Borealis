"""Base sensor interface for Borealis telemetry collection."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseSensor(ABC):
    """Abstract base class for all telemetry sensors/providers."""

    def __init__(self, name: str, ttl: int = 900) -> None:
        self.name = name
        self.ttl = ttl  # Default time-to-live in seconds
        self._last_fetched: float = 0.0
        self._cached_data: Dict[str, Any] = {}

    @abstractmethod
    def fetch(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch fresh telemetry data. Context contains telemetry from previously run sensors."""
        pass

    def update(self, context: Dict[str, Any], current_time: float, force: bool = False) -> Dict[str, Any]:
        """Update sensor data, returning cached data if TTL has not expired."""
        if not force and self._cached_data and (current_time - self._last_fetched) < self.ttl:
            return self._cached_data

        try:
            data = self.fetch(context)
            self._cached_data = data
            self._last_fetched = current_time
            return data
        except Exception as e:
            # On failure, return existing cache if available, or empty dict
            if self._cached_data:
                return self._cached_data
            return {"error": str(e)}
