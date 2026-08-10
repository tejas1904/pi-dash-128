"""Classic dashboard rendering and runtime loop."""

from dataclasses import replace
import time

from PIL import Image, ImageChops, ImageDraw

from pi_dash_128.designs.classic.config import ClassicConfig
from pi_dash_128.designs.classic.weather_display import draw_weather
from pi_dash_128.system_info import SystemInfo, SystemInfoProvider
from pi_dash_128.system_monitor import MetricsSnapshot, SystemMonitor
from pi_dash_128.weather import Weather, WeatherService


def draw_usage_bar(
    image: Image.Image,
    position: tuple[int, int, int, int],
    percent: float,
) -> None:
    """Draw the filled and unfilled parts of a usage bar."""
    draw = ImageDraw.Draw(image)
    left, top, right, bottom = position
    percent = max(0.0, min(100.0, percent))
    draw.rectangle(position, outline="white", fill="black")
    inner_width = right - left - 1
    filled_width = round(inner_width * percent / 100.0)
    if filled_width > 0:
        draw.rectangle(
            (left + 1, top + 1, left + filled_width, bottom - 1), fill="white"
        )


def draw_inverted_text(
    image: Image.Image, position: tuple[int, int], text: str
) -> None:
    """Draw text that stays visible over both parts of a usage bar."""
    text_image = Image.new("1", image.size)
    ImageDraw.Draw(text_image).text(position, text, fill="white")
    image.paste(ImageChops.logical_xor(image, text_image))


def ticker_text(info: SystemInfo) -> str:
    """Build the text that continuously scrolls across the bottom."""
    return "  |  ".join(
        (
            f"USER {info.username}",
            f"HOST {info.hostname}",
            f"LAN {info.local_ip or 'Not connected'}",
            f"TAIL {info.tailscale_ip or 'Not connected'}",
        )
    )


def render_dashboard(
    size: tuple[int, int],
    metrics: MetricsSnapshot,
    info: SystemInfo,
    weather: Weather,
    weather_unit: str,
    show_weather_location: bool,
    scroll_x: int,
) -> Image.Image:
    """Create one complete classic-design OLED frame."""
    width, height = size
    image = Image.new("1", size)
    draw = ImageDraw.Draw(image)
    temperature = (
        f"{metrics.temperature_c:.0f}C"
        if metrics.temperature_c is not None
        else "N/A"
    )

    draw_usage_bar(image, (0, 0, width - 1, 18), metrics.cpu_percent)
    draw_inverted_text(image, (8, 4), f"CPU {metrics.cpu_percent:3.0f}%")
    draw_inverted_text(image, (94, 4), temperature)
    draw_usage_bar(image, (0, 22, width - 1, 40), metrics.ram_percent)
    draw_inverted_text(image, (8, 26), f"RAM {metrics.ram_percent:3.0f}%")
    draw_inverted_text(image, (81, 26), f"{metrics.ram_used_mb:.0f}MB")

    bottom_y = height - 13
    ticker_left = width // 2 + 2
    draw.line((0, 45, width - 1, 45), fill="white")
    draw_weather(
        draw,
        weather,
        weather_unit,
        show_weather_location,
        position=(2, bottom_y),
    )
    ticker_image = Image.new("1", size)
    ImageDraw.Draw(ticker_image).text(
        (scroll_x, bottom_y), ticker_text(info), fill="white"
    )
    ticker_image.paste(0, (0, 0, ticker_left, height))
    image.paste(1, mask=ticker_image)
    draw.line((width // 2, 48, width // 2, height - 1), fill="white")
    return image


class Design:
    """Run the classic page with its independently loaded configuration."""

    def __init__(self, config: ClassicConfig | None = None) -> None:
        self.config = config or ClassicConfig.load()

    def run(self, device) -> None:
        config = self.config
        monitor = SystemMonitor()
        info_provider = SystemInfoProvider()
        weather_service = WeatherService()
        metrics = monitor.read(sample_seconds=0.1)
        info = info_provider.read()
        weather = weather_service.get_current()
        ticker = ticker_text(info)
        ticker_width = int(ImageDraw.Draw(Image.new("1", (1, 1))).textlength(ticker))
        ticker_started = time.monotonic()
        last_metrics_update = time.monotonic()
        last_weather_update = time.monotonic()
        last_network_update = time.monotonic()
        smooth_cpu = metrics.cpu_percent
        smooth_ram = metrics.ram_percent

        while True:
            frame_started = time.monotonic()
            now = time.monotonic()
            if now - last_metrics_update >= config.refresh_seconds:
                metrics = monitor.read(sample_seconds=0)
                last_metrics_update = now
            if now - last_weather_update >= config.weather_refresh_seconds:
                weather = weather_service.get_current()
                last_weather_update = now
            if now - last_network_update >= config.network_refresh_seconds:
                refreshed_info = info_provider.read()
                last_network_update = now
                if refreshed_info != info:
                    info = refreshed_info
                    ticker = ticker_text(info)
                    ticker_width = int(
                        ImageDraw.Draw(Image.new("1", (1, 1))).textlength(ticker)
                    )
                    ticker_started = now

            smooth_cpu += (metrics.cpu_percent - smooth_cpu) * config.bar_smoothing
            smooth_ram += (metrics.ram_percent - smooth_ram) * config.bar_smoothing
            smooth_metrics = replace(
                metrics, cpu_percent=smooth_cpu, ram_percent=smooth_ram
            )
            ticker_distance = int(
                (now - ticker_started) * config.scroll_pixels_per_second
            )
            ticker_area_width = device.width // 2 - 2
            scroll_x = device.width - (
                ticker_distance % (ticker_area_width + ticker_width)
            )
            show_location = int(now / config.weather_switch_seconds) % 2 == 1
            device.display(
                render_dashboard(
                    device.size,
                    smooth_metrics,
                    info,
                    weather,
                    config.weather_unit,
                    show_location,
                    scroll_x,
                )
            )
            frame_time = time.monotonic() - frame_started
            time.sleep(max(0, config.frame_seconds - frame_time))
