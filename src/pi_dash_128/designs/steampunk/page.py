"""Animated one-bit steampunk boiler console."""

import math
import time

from PIL import Image, ImageDraw, ImageFont

from pi_dash_128.designs.steampunk.config import Config
from pi_dash_128.system_info import SystemInfo, SystemInfoProvider
from pi_dash_128.system_monitor import MetricsSnapshot, SystemMonitor
from pi_dash_128.weather import Weather, WeatherService


FONT = ImageFont.load_default()
SMALL = ImageFont.load_default(size=8)


def fit(draw: ImageDraw.ImageDraw, text: str, width: int, font=SMALL) -> str:
    while text and draw.textbbox((0, 0), text, font=font)[2] > width:
        text = text[:-1]
    return text


def _dial(
    draw: ImageDraw.ImageDraw,
    center: tuple[int, int],
    value: float,
    label: str,
    phase: int,
) -> None:
    """Draw a riveted pressure dial with a live needle and value."""
    cx, cy = center
    bounded = max(0.0, min(100.0, value))
    draw.ellipse((cx - 14, cy - 12, cx + 14, cy + 14), outline=1)
    draw.arc((cx - 11, cy - 9, cx + 11, cy + 11), 198, 342, fill=1)
    for angle in range(200, 341, 35):
        radians = math.radians(angle)
        draw.point(
            (cx + round(9 * math.cos(radians)), cy + round(9 * math.sin(radians))),
            fill=1,
        )
    angle = math.radians(200 + bounded * 1.4)
    needle_end = (
        cx + round(8 * math.cos(angle)),
        cy + round(8 * math.sin(angle)),
    )
    draw.line((cx, cy, *needle_end), fill=1)
    draw.rectangle((cx - 1, cy - 1, cx + 1, cy + 1), fill=1)
    # A tiny glint gives the glass face some movement without disturbing readability.
    draw.point((cx - 7 + phase % 4, cy - 5 + (phase // 3) % 2), fill=1)
    value_text = f"{bounded:.0f}"
    draw.text((cx, cy + 4), value_text, font=SMALL, anchor="mt", fill=1)
    draw.text((cx, cy + 15), label, font=SMALL, anchor="mt", fill=1)


def render_dashboard(
    size: tuple[int, int],
    metrics: MetricsSnapshot,
    info: SystemInfo,
    weather: Weather,
    unit: str,
    show_network: bool,
    phase: int = 0,
) -> Image.Image:
    image = Image.new("1", size)
    draw = ImageDraw.Draw(image)
    width, height = size

    # Riveted maker's plate and boiler-state lamp. Everything stays one pixel
    # inside the panel so common OLED column/row offsets cannot clip it.
    draw.rectangle((2, 2, width - 3, height - 3), outline=1)
    for x, y in ((4, 4), (width - 5, 4), (4, height - 5), (width - 5, height - 5)):
        draw.point((x, y), fill=1)
    draw.line((7, 11, 96, 11), fill=1)
    draw.text((52, 2), "AETHERWORKS // PI", font=SMALL, anchor="mt", fill=1)
    online = info.local_ip is not None
    draw.ellipse((99, 3, 106, 10), outline=1)
    if online and phase % 8 != 0:
        draw.ellipse((101, 5, 104, 8), fill=1)
    draw.text((109, 2), "ON" if online else "OFF", font=SMALL, fill=1)

    # Offset position and timing keep the instruments from behaving as a
    # mirrored pair. The boiler glint moves slowly; the aether dial skips ahead.
    _dial(draw, (24, 27), metrics.cpu_percent, "CPU", phase // 2)
    _dial(draw, (68, 30), metrics.ram_percent, "RAM", (phase * 2 + 5) // 3)

    # Bottom engraved data plate alternates between the outside atmosphere and link.
    draw.rectangle((7, 53, 120, 61), outline=1)
    if show_network:
        detail = f"TELEGRAPH {info.local_ip or 'NO LINK'}"
    else:
        value = weather.temperature_f if unit == "F" else weather.temperature_c
        temperature = "--" if value is None else str(value)
        detail = f"ATMOS {temperature}{unit} {weather.condition.upper()}"
    draw.text((64, 53), fit(draw, detail, 108), font=SMALL, anchor="mt", fill=1)
    return image


class Design:
    def __init__(self, config: Config | None = None) -> None:
        self.config = config or Config.load()

    def run(self, device) -> None:
        config = self.config
        monitor = SystemMonitor()
        info_provider = SystemInfoProvider()
        weather_service = WeatherService()
        metrics = monitor.read(0.1)
        info = info_provider.read()
        weather = weather_service.get_current()
        started = metrics_at = weather_at = time.monotonic()
        while True:
            frame_at = now = time.monotonic()
            if now - metrics_at >= config.refresh:
                metrics = monitor.read(0)
                info = info_provider.read()
                metrics_at = now
            if now - weather_at >= config.weather_refresh:
                weather = weather_service.get_current()
                weather_at = now
            phase = int((now - started) / config.frame)
            show_network = int((now - started) / config.info_switch) % 2 == 1
            device.display(
                render_dashboard(
                    device.size,
                    metrics,
                    info,
                    weather,
                    config.weather_unit,
                    show_network,
                    phase,
                )
            )
            time.sleep(max(0, config.frame - (time.monotonic() - frame_at)))
