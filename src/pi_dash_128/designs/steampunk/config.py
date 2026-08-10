from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True)
class Config:
    refresh: float
    frame: float
    weather_unit: str
    weather_refresh: float
    info_switch: float

    @classmethod
    def load(cls) -> "Config":
        values = dotenv_values(Path(__file__).with_name("config.env"))
        def number(name: str, default: str) -> float:
            value = float(values.get(name) or default)
            if value <= 0:
                raise ValueError(f"{name} must be greater than zero")
            return value
        unit = (values.get("WEATHER_UNIT") or "F").upper()
        if unit not in ("C", "F"):
            raise ValueError("WEATHER_UNIT must be C or F")
        return cls(number("REFRESH_SECONDS", "0.5"), number("FRAME_SECONDS", "0.1"), unit, number("WEATHER_REFRESH_SECONDS", "900"), number("INFO_SWITCH_SECONDS", "4"))
