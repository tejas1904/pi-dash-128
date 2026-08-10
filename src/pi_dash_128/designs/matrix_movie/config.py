"""Configuration for the Matrix movie system-information variant."""

from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values


@dataclass(frozen=True)
class MatrixMovieConfig:
    fps: float
    refresh_seconds: float
    stat_interval_frames: int

    @classmethod
    def load(cls) -> "MatrixMovieConfig":
        values = dotenv_values(Path(__file__).with_name("config.env"))
        try:
            config = cls(
                fps=float(values.get("FPS") or "10"),
                refresh_seconds=float(values.get("REFRESH_SECONDS") or "0.5"),
                stat_interval_frames=int(values.get("STAT_INTERVAL_FRAMES") or "45"),
            )
        except ValueError as error:
            raise ValueError("Matrix configuration values must be numbers") from error
        if min(config.fps, config.refresh_seconds, config.stat_interval_frames) <= 0:
            raise ValueError("Matrix configuration values must be greater than zero")
        return config
