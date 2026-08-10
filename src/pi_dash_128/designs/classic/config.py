"""Configuration owned only by the classic dashboard design."""

from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


def _number(values: dict[str, str | None], name: str, default: str) -> float:
    value = values.get(name) or default
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a number; received {value!r}") from error


@dataclass(frozen=True)
class ClassicConfig:
    refresh_seconds: float
    frame_seconds: float
    scroll_pixels_per_second: float
    weather_unit: str
    bar_smoothing: float
    weather_refresh_seconds: float
    weather_switch_seconds: float
    network_refresh_seconds: float

    @classmethod
    def load(cls) -> "ClassicConfig":
        values = dotenv_values(Path(__file__).with_name("config.env"))
        config = cls(
            refresh_seconds=_number(values, "REFRESH_SECONDS", "0.5"),
            frame_seconds=_number(values, "FRAME_SECONDS", "0.1"),
            scroll_pixels_per_second=_number(values, "SCROLL_SPEED", "10"),
            weather_unit=(values.get("WEATHER_UNIT") or "C").strip().upper(),
            bar_smoothing=_number(values, "BAR_SMOOTHING", "0.2"),
            weather_refresh_seconds=_number(values, "WEATHER_REFRESH_SECONDS", "900"),
            weather_switch_seconds=_number(values, "WEATHER_SWITCH_SECONDS", "3"),
            network_refresh_seconds=_number(values, "NETWORK_REFRESH_SECONDS", "10"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        positive = {
            "REFRESH_SECONDS": self.refresh_seconds,
            "FRAME_SECONDS": self.frame_seconds,
            "SCROLL_SPEED": self.scroll_pixels_per_second,
            "WEATHER_REFRESH_SECONDS": self.weather_refresh_seconds,
            "WEATHER_SWITCH_SECONDS": self.weather_switch_seconds,
            "NETWORK_REFRESH_SECONDS": self.network_refresh_seconds,
        }
        for name, value in positive.items():
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")
        if not 0 < self.bar_smoothing <= 1:
            raise ValueError("BAR_SMOOTHING must be greater than 0 and at most 1")
        if self.weather_unit not in ("C", "F"):
            raise ValueError("WEATHER_UNIT must be C or F")
