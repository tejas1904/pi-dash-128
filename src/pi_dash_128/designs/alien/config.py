from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


def number(values, name: str, default: str) -> float:
    try:
        return float(values.get(name) or default)
    except ValueError as error:
        raise ValueError(f"{name} must be a number") from error


@dataclass(frozen=True)
class Config:
    refresh: float
    frame: float
    bar_smoothing: float
    weather_unit: str
    weather_refresh: float
    network_refresh: float
    info_switch: float
    animate: bool

    @classmethod
    def load(cls) -> "Config":
        values = dotenv_values(Path(__file__).with_name("config.env"))
        config = cls(number(values, "REFRESH_SECONDS", "0.5"), number(values, "FRAME_SECONDS", "0.1"), number(values, "BAR_SMOOTHING", "0.2"), (values.get("WEATHER_UNIT") or "F").upper(), number(values, "WEATHER_REFRESH_SECONDS", "900"), number(values, "NETWORK_REFRESH_SECONDS", "10"), number(values, "INFO_SWITCH_SECONDS", "4"), (values.get("ANIMATE") or "true").lower() == "true")
        if min(config.refresh, config.frame, config.bar_smoothing, config.weather_refresh, config.network_refresh, config.info_switch) <= 0:
            raise ValueError("Alien timing values must be greater than zero")
        if config.weather_unit not in ("C", "F"):
            raise ValueError("WEATHER_UNIT must be C or F")
        if config.bar_smoothing > 1:
            raise ValueError("BAR_SMOOTHING must be at most 1")
        return config
