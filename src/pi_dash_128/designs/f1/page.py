"""Animated one-bit Formula racing telemetry page."""

import time

from PIL import Image, ImageDraw, ImageFont

from pi_dash_128.designs.f1.config import F1Config
from pi_dash_128.system_info import SystemInfo, SystemInfoProvider
from pi_dash_128.system_monitor import MetricsSnapshot, SystemMonitor


FONT = ImageFont.load_default()
SMALL_FONT = ImageFont.load_default(size=9)


def _text_right(draw: ImageDraw.ImageDraw, right: int, y: int, text: str) -> None:
    width = draw.textbbox((0, 0), text, font=FONT)[2]
    draw.text((right - width, y), text, font=FONT, fill=1)


def _shift_lights(draw: ImageDraw.ImageDraw, percent: float, phase: int) -> None:
    """Draw the animated rev lights used across modern steering wheels."""
    lit = max(1, round(max(0.0, min(100.0, percent)) / 10))
    for index in range(10):
        x = 34 + index * 6
        on = index < lit
        if on and index == lit - 1 and phase % 4 == 0:
            on = False
        if on:
            draw.rectangle((x, 2, x + 3, 4), fill=1)
        else:
            draw.point((x, 3), fill=1)


def _telemetry_bar(
    draw: ImageDraw.ImageDraw, y: int, value: float, phase: int, reverse: bool = False
) -> None:
    """Draw a segmented racing telemetry strip."""
    segments = 12
    active = round(max(0.0, min(100.0, value)) * segments / 100)
    for index in range(segments):
        visual = segments - 1 - index if reverse else index
        x = 31 + visual * 6
        if index < active:
            draw.rectangle((x, y, x + 4, y + 4), fill=1)
            if (phase + index) % 9 == 0:
                draw.point((x + 2, y + 2), fill=0)
        else:
            draw.line((x, y + 4, x + 4, y + 4), fill=1)
            draw.point((x, y), fill=1)


def _fit(draw: ImageDraw.ImageDraw, text: str, width: int) -> str:
    while text and draw.textbbox((0, 0), text, font=SMALL_FONT)[2] > width:
        text = text[:-1]
    return text


def _uptime(seconds: float) -> str:
    days, remainder = divmod(int(seconds), 86400)
    hours, minutes = divmod(remainder, 3600)
    return f"{days}d{hours:02d}h" if days else f"{hours}h{minutes // 60:02d}m"


def _history(draw: ImageDraw.ImageDraw, values: list[float]) -> None:
    draw.text((3, 37), "CPU TRACE", font=SMALL_FONT, fill=1)
    draw.rectangle((61, 37, 125, 62), outline=1)
    draw.line((63, 49, 123, 49), fill=1)
    points = []
    for index, value in enumerate(values[-61:]):
        x = 63 + index
        y = 60 - round(max(0, min(100, value)) * 21 / 100)
        points.append((x, y))
    if len(points) > 1:
        draw.line(points, fill=1)
    elif points:
        draw.point(points[0], fill=1)
    average = sum(values) / len(values) if values else 0
    draw.text((3, 50), f"AVG {average:.0f}%", font=SMALL_FONT, fill=1)


def render_dashboard(
    size: tuple[int, int],
    metrics: MetricsSnapshot,
    info: SystemInfo,
    panel: int,
    cpu_history: list[float],
    phase: int = 0,
) -> Image.Image:
    """Render one 128x64 Formula telemetry frame."""
    image = Image.new("1", size)
    draw = ImageDraw.Draw(image)
    width, height = size

    # Chamfered timing-tower header.
    draw.polygon(((1, 1), (25, 1), (29, 5), (25, 10), (1, 10)), fill=1)
    draw.text((3, 0), "P01", font=FONT, fill=0)
    _shift_lights(draw, metrics.cpu_percent, phase)
    draw.line((97, 1, width - 2, 1, width - 2, 8), fill=1)
    _text_right(draw, 124, 1, "LIVE")

    draw.text((2, 13), "CPU", font=FONT, fill=1)
    _telemetry_bar(draw, 15, metrics.cpu_percent, phase)
    _text_right(draw, 126, 13, f"{metrics.cpu_percent:.0f}%")

    draw.text((2, 24), "RAM", font=FONT, fill=1)
    _telemetry_bar(draw, 26, metrics.ram_percent, phase + 3, reverse=True)
    _text_right(draw, 126, 24, f"{metrics.ram_percent:.0f}%")

    # Lower telemetry deck rotates through real system data.
    draw.line((1, 35, width - 2, 35), fill=1)
    if panel == 0:
        _history(draw, cpu_history)
    elif panel == 1:
        temp = "--C" if metrics.temperature_c is None else f"{metrics.temperature_c:.0f}C"
        draw.text((3, 38), f"CORE {temp}  RAM {metrics.ram_used_mb:.0f}M", font=SMALL_FONT, fill=1)
        draw.text((3, 50), f"UP {_uptime(metrics.uptime_seconds)}", font=SMALL_FONT, fill=1)
        draw.rectangle((101, 48, 125, 60), outline=1)
        load = round(max(0, min(100, metrics.temperature_c or 0)) * 21 / 100)
        draw.rectangle((103, 51, 103 + load, 57), fill=1)
    else:
        draw.text((3, 38), _fit(draw, f"LINK: {info.local_ip or 'NO LINK'}", 122), font=SMALL_FONT, fill=1)
        draw.text((3, 50), _fit(draw, f"PILOT: {info.username}@{info.hostname}", 122), font=SMALL_FONT, fill=1)
    return image


class Design:
    def __init__(self, config: F1Config | None = None) -> None:
        self.config = config or F1Config.load()

    def run(self, device) -> None:
        monitor = SystemMonitor()
        info_provider = SystemInfoProvider()
        metrics = monitor.read(sample_seconds=0.1)
        info = info_provider.read()
        started = updated = time.monotonic()
        cpu_history = [metrics.cpu_percent]

        while True:
            frame_started = time.monotonic()
            now = time.monotonic()
            if now - updated >= self.config.refresh_seconds:
                metrics = monitor.read(sample_seconds=0)
                info = info_provider.read()
                cpu_history.append(metrics.cpu_percent)
                cpu_history = cpu_history[-61:]
                updated = now
            phase = int((now - started) / self.config.frame_seconds) if self.config.animate else 0
            panel = int((now - started) / self.config.info_switch_seconds) % 3
            device.display(render_dashboard(device.size, metrics, info, panel, cpu_history, phase))
            elapsed = time.monotonic() - frame_started
            time.sleep(max(0, self.config.frame_seconds - elapsed))
