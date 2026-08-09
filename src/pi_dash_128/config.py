import os
from dataclasses import dataclass

from dotenv import load_dotenv
from luma.core.interface.serial import i2c
from luma.oled import device as oled_devices


SUPPORTED_DRIVERS = (
    "ch1115",
    "sh1106",
    "sh1107",
    "ssd1305",
    "ssd1306",
    "ssd1309",
    "ssd1315",
    "ssd1316",
    "ssd1322",
    "ssd1325",
    "ssd1327",
    "ssd1331",
    "ssd1351",
    "ssd1362",
)


def _integer(name: str, default: str) -> int:
    value = os.getenv(name, default)
    try:
        return int(value, 0)
    except ValueError as error:
        raise ValueError(f"{name} must be an integer; received {value!r}") from error


def _number(name: str, default: str) -> float:
    value = os.getenv(name, default)
    try:
        return float(value)
    except ValueError as error:
        raise ValueError(f"{name} must be a number; received {value!r}") from error


@dataclass(frozen=True)
class DisplayConfig:
    driver: str
    i2c_port: int
    i2c_address: int
    width: int
    height: int
    rotate: int
    contrast: int

    @classmethod
    def from_env(cls) -> "DisplayConfig":
        load_dotenv()
        config = cls(
            driver=os.getenv("OLED_DRIVER", "sh1106").strip().lower(),
            i2c_port=_integer("OLED_I2C_PORT", "1"),
            i2c_address=_integer("OLED_I2C_ADDRESS", "0x3C"),
            width=_integer("OLED_WIDTH", "128"),
            height=_integer("OLED_HEIGHT", "64"),
            rotate=_integer("OLED_ROTATE", "0"),
            contrast=_integer("OLED_CONTRAST", "128"),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.driver not in SUPPORTED_DRIVERS:
            choices = ", ".join(SUPPORTED_DRIVERS)
            raise ValueError(f"Unsupported OLED_DRIVER {self.driver!r}. Choose: {choices}")
        if self.i2c_port < 0:
            raise ValueError("OLED_I2C_PORT cannot be negative")
        if not 0x03 <= self.i2c_address <= 0x77:
            raise ValueError("OLED_I2C_ADDRESS must be between 0x03 and 0x77")
        if self.width <= 0 or self.height <= 0:
            raise ValueError("OLED_WIDTH and OLED_HEIGHT must be positive")
        if self.rotate not in (0, 1, 2, 3):
            raise ValueError("OLED_ROTATE must be 0, 1, 2, or 3")
        if not 0 <= self.contrast <= 255:
            raise ValueError("OLED_CONTRAST must be between 0 and 255")

    def create_device(self):
        serial = i2c(port=self.i2c_port, address=self.i2c_address)
        device_class = getattr(oled_devices, self.driver)
        device = device_class(
            serial,
            width=self.width,
            height=self.height,
            rotate=self.rotate,
        )
        device.contrast(self.contrast)
        return device


@dataclass(frozen=True)
class MonitorConfig:
    refresh_seconds: float
    frame_seconds: float
    scroll_pixels_per_second: float
    weather_unit: str

    @classmethod
    def from_env(cls) -> "MonitorConfig":
        load_dotenv()
        config = cls(
            refresh_seconds=_number("MONITOR_REFRESH_SECONDS", "0.5"),
            frame_seconds=_number("MONITOR_FRAME_SECONDS", "0.1"),
            scroll_pixels_per_second=_number("MONITOR_SCROLL_SPEED", "10"),
            weather_unit=os.getenv("WEATHER_UNIT", "C").strip().upper(),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if self.refresh_seconds <= 0:
            raise ValueError("MONITOR_REFRESH_SECONDS must be greater than zero")
        if self.frame_seconds <= 0:
            raise ValueError("MONITOR_FRAME_SECONDS must be greater than zero")
        if self.scroll_pixels_per_second <= 0:
            raise ValueError("MONITOR_SCROLL_SPEED must be greater than zero")
        if self.weather_unit not in ("C", "F"):
            raise ValueError("WEATHER_UNIT must be C or F")
