"""Neuromancer-style ICE deck with animated circuit traces."""

from dataclasses import replace
import time
from PIL import Image, ImageDraw, ImageFont
from pi_dash_128.designs.cyberpunk.config import Config
from pi_dash_128.system_info import SystemInfo, SystemInfoProvider
from pi_dash_128.system_monitor import MetricsSnapshot, SystemMonitor
from pi_dash_128.weather import Weather, WeatherService

FONT = ImageFont.load_default(size=8)

def fit(draw, text: str, width: int) -> str:
    while text and draw.textbbox((0, 0), text, font=FONT)[2] > width:
        text = text[:-1]
    return text

def circuits(draw: ImageDraw.ImageDraw, phase: int) -> None:
    traces = (
        ((2, 11), (18, 11), (18, 12), (48, 12)),
        ((125, 11), (109, 11), (109, 12), (78, 12)),
        ((2, 25), (6, 25), (6, 38), (2, 38)),
        ((125, 25), (121, 25), (121, 38), (125, 38)),
        ((2, 51), (13, 51), (13, 57), (16, 57)),
        ((125, 51), (113, 51), (113, 47), (109, 47)),
    )
    for points in traces:
        draw.line(points, fill=1)
        x, y = points[0]
        draw.rectangle((x - 1, y - 1, x + 1, y + 1), outline=1)
    draw.rectangle((22 + phase % 23, 11, 24 + phase % 23, 12), fill=1)
    draw.rectangle((82 + phase % 22, 11, 84 + phase % 22, 12), fill=1)
    draw.point((6, 27 + phase % 10), fill=0 if phase % 2 else 1)

def segments(draw, x: int, y: int, value: float, phase: int) -> None:
    active = round(max(0, min(100, value)) * 9 / 100)
    for index in range(9):
        left = x + index * 7
        draw.rectangle((left, y, left + 4, y + 4), outline=1)
        if index < active:
            draw.rectangle((left + 1, y + 1, left + 3, y + 3), fill=1)
            if (phase + index) % 8 == 0:
                draw.point((left + 2, y + 2), fill=0)

def slab(draw, box, cut_left: bool) -> None:
    left, top, right, bottom = box
    if cut_left:
        points = ((left + 4, top), (right, top), (right, bottom), (left, bottom), (left, top + 4))
    else:
        points = ((left, top), (right - 4, top), (right, top + 4), (right, bottom), (left, bottom))
    draw.polygon(points, fill=0, outline=1)

def render_dashboard(size, metrics: MetricsSnapshot, info: SystemInfo, weather: Weather, unit: str, phase: int, show_network: bool):
    image = Image.new("1", size)
    draw = ImageDraw.Draw(image)
    circuits(draw, phase)
    slab(draw, (1, 0, 126, 9), True)
    draw.text((5, 0), "ICE//DECK", font=FONT, fill=1)
    draw.text((91, 0), "JACKED" if info.local_ip else "CLOSED", font=FONT, fill=1)
    slab(draw, (1, 14, 119, 24), False)
    draw.text((4, 14), "PROC", font=FONT, fill=1)
    segments(draw, 31, 17, metrics.cpu_percent, phase)
    draw.text((96, 14), f"{metrics.cpu_percent:.0f}%", font=FONT, fill=1)
    slab(draw, (8, 27, 126, 37), True)
    draw.text((11, 27), "MEM", font=FONT, fill=1)
    segments(draw, 36, 30, metrics.ram_percent, phase + 3)
    draw.text((102, 27), f"{metrics.ram_percent:.0f}%", font=FONT, fill=1)
    slab(draw, (1, 40, 108, 49), False)
    temp = "--" if metrics.temperature_c is None else f"{metrics.temperature_c:.0f}C"
    draw.text((4, 40), f"CORE:{temp}", font=FONT, fill=1)
    draw.line((76, 46, 80 + phase % 20, 46), fill=1)
    slab(draw, (17, 53, 126, 62), True)
    if show_network:
        detail = f"NODE:{info.local_ip or '--'}"
    else:
        value = weather.temperature_f if unit == "F" else weather.temperature_c
        detail = f"EXT:{value if value is not None else '--'}{unit} {weather.condition.upper()}"
    draw.text((21, 53), fit(draw, detail, 101), font=FONT, fill=1)
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
            phase = int((now - started) / config.frame)
            show_network = int(now / config.info_switch) % 2 == 1
            device.display(render_dashboard(device.size, smooth_metrics, info, weather, config.weather_unit, phase, show_network))
            time.sleep(max(0, config.frame - (time.monotonic() - frame_at)))
