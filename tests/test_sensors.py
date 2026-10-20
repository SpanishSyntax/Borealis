"""Tests for Borealis telemetry sensors (solar, system, space)."""

from borealis.sensors.solar import SolarSensor
from borealis.sensors.system import SystemSensor
from borealis.sensors.space import SpaceWeatherSensor


def test_solar_sensor():
    sensor = SolarSensor()
    data = sensor.fetch({"location": {"latitude": 52.0, "longitude": 4.35}})
    assert "elevation_deg" in data
    assert "sin_elevation" in data
    assert "phase" in data
    assert isinstance(data["elevation_deg"], float)


def test_system_sensor():
    sensor = SystemSensor()
    data = sensor.fetch({})
    assert "hour" in data
    assert "minute" in data
    assert "weekday" in data
    assert "season" in data
    assert 0 <= data["hour"] <= 23


def test_space_sensor():
    sensor = SpaceWeatherSensor()
    data = sensor.fetch({})
    assert "kp_index" in data
    assert "activity" in data
    assert data["kp_index"] >= 0.0
