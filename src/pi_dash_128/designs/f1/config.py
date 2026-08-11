"""Configuration for the F1 telemetry page."""

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
class F1Config:
    refresh_seconds: float
    frame_seconds: float
    info_switch_seconds: float
    bar_smoothing: float
    animate: bool
    gear_shift_flash: bool = True

    @classmethod
    def load(cls, path: Path | None = None) -> "F1Config":
        values = dotenv_values(path or Path(__file__).with_name("config.env"))
        config = cls(
            refresh_seconds=_number(values, "REFRESH_SECONDS", "0.5"),
            frame_seconds=_number(values, "FRAME_SECONDS", "0.08"),
            info_switch_seconds=_number(values, "INFO_SWITCH_SECONDS", "4"),
            bar_smoothing=_number(values, "BAR_SMOOTHING", "0.12"),
            animate=(values.get("ANIMATE") or "true").strip().lower() == "true",
            gear_shift_flash=(values.get("GEAR_SHIFT_FLASH") or "true")
            .strip()
            .lower()
            == "true",
        )
        if min(config.refresh_seconds, config.frame_seconds, config.info_switch_seconds) <= 0:
            raise ValueError("F1 timing values must be greater than zero")
        if not 0 < config.bar_smoothing <= 1:
            raise ValueError("BAR_SMOOTHING must be greater than 0 and at most 1")
        return config
