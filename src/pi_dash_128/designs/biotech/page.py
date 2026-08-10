"""Clean organic biotech interface for a 128x64 OLED."""

import time

from PIL import Image, ImageDraw, ImageFont

from pi_dash_128.designs.biotech.config import BioTechConfig
from pi_dash_128.system_info import SystemInfo, SystemInfoProvider
from pi_dash_128.system_monitor import MetricsSnapshot, SystemMonitor
from pi_dash_128.weather import Weather, WeatherService


FONT = ImageFont.load_default(size=9)
SMALL = ImageFont.load_default(size=8)


def fit(draw, text: str, width: int, font=FONT) -> str:
    while text and draw.textbbox((0, 0), text, font=font)[2] > width:
        text = text[:-1]
    return text


def colony(draw, x: int, y: int, value: float, phase: int) -> None:
    active = round(max(0, min(100, value)) * 6 / 100)
    for index in range(6):
        left = x + index * 9
        draw.ellipse((left, y, left + 7, y + 7), outline=1)
        # A moving pore makes each membrane feel alive.
        pores = ((left + 3, y), (left + 7, y + 3), (left + 3, y + 7), (left, y + 3))
        draw.point(pores[(phase + index) % 4], fill=0)
        if index < active:
            nx = left + 2 + (phase + index) % 3
            draw.ellipse((nx, y + 2, nx + 2, y + 4), fill=1)


def capillary(draw, y: int, phase: int) -> None:
    """Draw a one-pixel vessel with slowly drifting blood-cell pulses."""
    flow_rates = (3, 5, 4, 6, 3, 4, 5, 3)
    cell_sizes = (1, 3, 2, 1, 2, 3, 1, 2)
    for index, (rate, cell_size) in enumerate(zip(flow_rates, cell_sizes)):
        cell_x = 2 + (index * 16 + phase // rate) % 124
        draw.line((cell_x, y, min(125, cell_x + cell_size - 1), y), fill=1)


def render_dashboard(size, metrics: MetricsSnapshot, info: SystemInfo, weather: Weather, unit: str, show_network: bool, phase: int):
    image = Image.new("1", size)
    draw = ImageDraw.Draw(image)
    width, _ = size
    bonded = info.local_ip is not None

    # Zone 1: identity and organism state.
    draw.text((2, 0), "BIO//TECH", font=FONT, fill=1)
    badge = "BONDED" if bonded else "DORMANT"
    badge_x = 87 if bonded else 81
    draw.polygon(((badge_x - 3, 0), (126, 0), (126, 9), (badge_x - 6, 9), (badge_x - 6, 3)), fill=1)
    badge_text_x = badge_x - 2 if bonded else badge_x
    draw.text((badge_text_x, 0), badge, font=FONT, fill=0)
    for x in range(49, 78, 4):
        draw.point((x, 4 + ((x // 4 + phase // 3) % 2)), fill=1)

    # Zone 2: two independent living cell colonies.
    draw.text((2, 14), f"NEURAL {metrics.cpu_percent:.0f}%", font=SMALL, fill=1)
    draw.text((68, 14), f"MEMBR {metrics.ram_percent:.0f}%", font=SMALL, fill=1)
    colony(draw, 2, 23, metrics.cpu_percent, phase)
    colony(draw, 68, 23, metrics.ram_percent, phase + 3)

    # Zone 3: reactor and animated molecule.
    temperature = "--" if metrics.temperature_c is None else f"{metrics.temperature_c:.0f}C"
    state = "FEVER" if metrics.temperature_c is not None and metrics.temperature_c >= 80 else "STABLE"
    draw.text((2, 36), f"REACT {temperature}", font=FONT, fill=1)
    draw.ellipse((63, 35, 71, 43), outline=1)
    draw.point((67, 39), fill=1)
    orbit = ((67, 34), (72, 39), (67, 44), (62, 39))
    draw.point(orbit[phase % 4], fill=1)
    draw.point(orbit[(phase + 2) % 4], fill=1)
    draw.text((78, 36), state, font=FONT, fill=1)

    # Give the bottom telemetry the space previously occupied by the animated helix.
    capillary(draw, 48, phase)
    if show_network:
        label = "BIO-LINK"
        detail = info.local_ip or "--"
        detail_font = FONT
    else:
        value = weather.temperature_f if unit == "F" else weather.temperature_c
        label = "ATMOSPHERE"
        detail = f"{value if value is not None else '--'}{unit}  {weather.condition.upper()}"
        detail_font = FONT
    label_x, row_y = 7, 51
    label_right = draw.textbbox((label_x, row_y), label, font=SMALL)[2]
    draw.polygon(
        (
            (label_x - 3, row_y),
            (label_right + 4, row_y),
            (label_right + 4, row_y + 7),
            (label_right + 1, row_y + 10),
            (label_x - 6, row_y + 10),
            (label_x - 6, row_y + 3),
        ),
        fill=1,
    )
    draw.text((label_x, row_y), label, font=SMALL, fill=0)
    detail_x = label_right + 7
    draw.text(
        (detail_x, row_y),
        fit(draw, detail, width - detail_x - 2, detail_font),
        font=detail_font,
        fill=1,
    )
    return image


class Design:
    def __init__(self) -> None:
        self.config = BioTechConfig.load()

    def run(self, device) -> None:
        config = self.config
        monitor, info_provider, weather_service = SystemMonitor(), SystemInfoProvider(), WeatherService()
        metrics, info, weather = monitor.read(0.1), info_provider.read(), weather_service.get_current()
        started = metrics_at = weather_at = network_at = time.monotonic()
        while True:
            frame_at = now = time.monotonic()
            if now - metrics_at >= config.refresh_seconds:
                metrics, metrics_at = monitor.read(0), now
            if now - weather_at >= config.weather_refresh_seconds:
                weather, weather_at = weather_service.get_current(), now
            if now - network_at >= config.network_refresh_seconds:
                info, network_at = info_provider.read(), now
            phase = int((now - started) / config.frame_seconds) if config.animate else 0
            show_network = int(now / config.info_switch_seconds) % 2 == 1
            device.display(render_dashboard(device.size, metrics, info, weather, config.weather_unit, show_network, phase))
            time.sleep(max(0, config.frame_seconds - (time.monotonic() - frame_at)))
