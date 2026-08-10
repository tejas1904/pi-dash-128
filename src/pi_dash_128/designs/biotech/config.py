"""Configuration for the BioTech page."""

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
class BioTechConfig:
    refresh_seconds: float
    frame_seconds: float
    bar_smoothing: float
    weather_unit: str
    weather_refresh_seconds: float
    network_refresh_seconds: float
    info_switch_seconds: float
    animate: bool

    @classmethod
    def load(cls, path: Path | None = None) -> "BioTechConfig":
        values = dotenv_values(path or Path(__file__).with_name("config.env"))
        config = cls(
            refresh_seconds=_number(values, "REFRESH_SECONDS", "0.5"),
            frame_seconds=_number(values, "FRAME_SECONDS", "0.1"),
            bar_smoothing=_number(values, "BAR_SMOOTHING", "0.2"),
            weather_unit=(values.get("WEATHER_UNIT") or "F").strip().upper(),
            weather_refresh_seconds=_number(values, "WEATHER_REFRESH_SECONDS", "900"),
            network_refresh_seconds=_number(values, "NETWORK_REFRESH_SECONDS", "10"),
            info_switch_seconds=_number(values, "INFO_SWITCH_SECONDS", "4"),
            animate=(values.get("ANIMATE") or "false").lower() == "true",
        )
        if min(
            config.refresh_seconds,
            config.frame_seconds,
            config.bar_smoothing,
            config.weather_refresh_seconds,
            config.network_refresh_seconds,
            config.info_switch_seconds,
        ) <= 0:
            raise ValueError("BioTech timing and speed values must be greater than zero")
        if config.weather_unit not in ("C", "F"):
            raise ValueError("WEATHER_UNIT must be C or F")
        if config.bar_smoothing > 1:
            raise ValueError("BAR_SMOOTHING must be at most 1")
        return config
