"""Alien HUD with animated broken-cell liquid meters."""

from dataclasses import replace
import time

from PIL import Image, ImageDraw, ImageFont

from pi_dash_128.designs.alien.config import Config
from pi_dash_128.system_info import SystemInfo, SystemInfoProvider
from pi_dash_128.system_monitor import MetricsSnapshot, SystemMonitor
from pi_dash_128.weather import Weather, WeatherService


FONT = ImageFont.load_default()
SMALL = ImageFont.load_default(size=8)


LEFT_ORGAN = ((2, 13), (15, 11), (28, 13), (39, 19), (39, 30), (28, 37), (15, 39), (2, 36))
RIGHT_ORGAN = tuple((117 - x, y) for x, y in LEFT_ORGAN)
CONTACT_RHYTHM = (
    (0, 5), (1, 3), (2, 7), (3, 4),
    (0, 8), (1, 4), (2, 5), (3, 6),
    (0, 4), (1, 5), (2, 8), (3, 3),
)


def contact_pulse(phase: int | None) -> int:
    """Advance the contact signal through an uneven, flicker-free rhythm."""
    if phase is None:
        return 0
    beat = phase % sum(duration for _, duration in CONTACT_RHYTHM)
    for state, duration in CONTACT_RHYTHM:
        if beat < duration:
            return state
        beat -= duration
    return 0


def fluid_cell(draw: ImageDraw.ImageDraw, x: int, y: int, filled: bool, phase: int | None, index: int, mirror: bool) -> None:
    """Draw a large C-shaped cell with a moving pocket of liquid."""
    if mirror:
        draw.line((x + 1, y, x + 8, y), fill=1)
        draw.line((x + 10, y + 2, x + 10, y + 6), fill=1)
        draw.line((x + 2, y + 8, x + 8, y + 8), fill=1)
        draw.point((x, y + 6), fill=1)
        draw.point((x + 9, y + 1), fill=1)
        draw.point((x + 9, y + 7), fill=1)
    else:
        draw.line((x + 2, y, x + 9, y), fill=1)
        draw.line((x, y + 2, x, y + 6), fill=1)
        draw.line((x + 2, y + 8, x + 8, y + 8), fill=1)
        draw.point((x + 10, y + 6), fill=1)
        draw.point((x + 1, y + 1), fill=1)
        draw.point((x + 1, y + 7), fill=1)

    if filled:
        draw.rectangle((x + 3, y + 3, x + 8, y + 6), fill=1)
        draw.point((x + (9 if mirror else 2), y + 5), fill=1)
        if phase is not None:
            wave = (phase // 2 + index) % 4
            draw.line((x + 4 + wave, y + 3, x + 5 + wave, y + 3), fill=0)
    elif phase is not None and index == (phase // 2) % 8:
        draw.ellipse((x + 4, y + 3, x + 6, y + 5), fill=1)


def organic_meter(draw: ImageDraw.ImageDraw, cells, percent: float, phase: int | None, mirror: bool = False) -> None:
    """Arrange liquid cells into one lobe of the alien organism."""
    active = round(max(0, min(100, percent)) * 8 / 100)
    for index, (x, y) in enumerate(cells):
        fluid_cell(draw, x, y, index < active, phase, index, mirror)


def fit(draw, text: str, width: int, font=FONT) -> str:
    while text and draw.textbbox((0, 0), text, font=font)[2] > width:
        text = text[:-1]
    return text


def render_dashboard(size, metrics: MetricsSnapshot, info: SystemInfo, weather: Weather, unit: str, show_network: bool, phase: int | None = None):
    image = Image.new("1", size)
    draw = ImageDraw.Draw(image)
    width, _ = size
    online = info.local_ip is not None
    cpu_text = f"CPU {metrics.cpu_percent:.0f}%"
    memory_text = f"MEM {metrics.ram_percent:.0f}%"
    draw.text((2, 0), cpu_text, font=SMALL, fill=1)
    draw.text((width - 2 - draw.textlength(memory_text, font=SMALL), 0), memory_text, font=SMALL, fill=1)

    organic_meter(draw, LEFT_ORGAN, metrics.cpu_percent, phase)
    memory_phase = None if phase is None else phase + 5
    organic_meter(draw, RIGHT_ORGAN, metrics.ram_percent, memory_phase, mirror=True)

    temperature = "--" if metrics.temperature_c is None else f"{metrics.temperature_c:.0f}C"
    state = "HOT" if metrics.temperature_c is not None and metrics.temperature_c >= 80 else "OK"
    draw.text((64, 17), temperature, font=SMALL, anchor="mt", fill=1)
    contact = "LINK" if online else "VOID"
    contact_x = int((width - draw.textlength(contact, font=SMALL)) / 2)
    pulse = contact_pulse(phase)
    contact_right = draw.textbbox((contact_x, 29), contact, font=SMALL)[2]
    contact_box = (contact_x - 1, 30, contact_right, 38)
    if pulse == 2:
        draw.rectangle(contact_box, fill=1)
    elif pulse in (1, 3):
        draw.rectangle(contact_box, outline=1)
    draw.text((contact_x, 29), contact, font=SMALL, fill=0 if pulse == 2 else 1)
    draw.text((64, 40), state, font=SMALL, anchor="mt", fill=1)

    if show_network:
        detail = f"RX {info.local_ip or '--'}"
    else:
        value = weather.temperature_f if unit == "F" else weather.temperature_c
        detail = f"ATMO {value if value is not None else '--'}{unit} {weather.condition.upper()}"
    detail = fit(draw, detail, width - 4, SMALL)
    detail_x = (width - draw.textlength(detail, font=SMALL)) / 2
    draw.text((detail_x, 53), detail, font=SMALL, fill=1)
    return image


class Design:
    def __init__(self) -> None:
        self.config = Config.load()

    def run(self, device) -> None:
        config = self.config
        monitor, info_provider, weather_service = SystemMonitor(), SystemInfoProvider(), WeatherService()
        metrics, info, weather = monitor.read(0.1), info_provider.read(), weather_service.get_current()
        started = metrics_at = weather_at = network_at = time.monotonic()
        smooth_cpu = metrics.cpu_percent
        smooth_ram = metrics.ram_percent
        while True:
            frame_at = now = time.monotonic()
            if now - metrics_at >= config.refresh:
                metrics, metrics_at = monitor.read(0), now
            if now - weather_at >= config.weather_refresh:
                weather, weather_at = weather_service.get_current(), now
            if now - network_at >= config.network_refresh:
                info, network_at = info_provider.read(), now
            smooth_cpu += (metrics.cpu_percent - smooth_cpu) * config.bar_smoothing
            smooth_ram += (metrics.ram_percent - smooth_ram) * config.bar_smoothing
            smooth_metrics = replace(metrics, cpu_percent=smooth_cpu, ram_percent=smooth_ram)
            phase = int((now - started) / config.frame) if config.animate else None
            show_network = int(now / config.info_switch) % 2 == 1
            device.display(render_dashboard(device.size, smooth_metrics, info, weather, config.weather_unit, show_network, phase))
            time.sleep(max(0, config.frame - (time.monotonic() - frame_at)))
