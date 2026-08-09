"""OLED system-monitor application."""

from dataclasses import replace
import time

from PIL import Image, ImageChops, ImageDraw

from pi_dash_128.config import DisplayConfig, MonitorConfig
from pi_dash_128.system_info import SystemInfo, SystemInfoProvider
from pi_dash_128.system_monitor import MetricsSnapshot, SystemMonitor
from pi_dash_128.weather import Weather, WeatherService
from pi_dash_128.weather_display import draw_weather


BAR_SMOOTHING = 0.2
WEATHER_REFRESH_SECONDS = 15 * 60
WEATHER_SWITCH_SECONDS = 3
NETWORK_REFRESH_SECONDS = 10


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
            (left + 1, top + 1, left + filled_width, bottom - 1),
            fill="white",
        )


def draw_inverted_text(
    image: Image.Image,
    position: tuple[int, int],
    text: str,
) -> None:
    """Draw text that stays visible over both parts of a usage bar."""
    text_image = Image.new("1", image.size)
    text_draw = ImageDraw.Draw(text_image)
    text_draw.text(position, text, fill="white")

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
    """Create one complete OLED frame."""
    width, height = size
    image = Image.new("1", size)
    draw = ImageDraw.Draw(image)
    temperature = (
        f"{metrics.temperature_c:.0f}C"
        if metrics.temperature_c is not None
        else "N/A"
    )

    draw_usage_bar(
        image,
        (0, 0, width - 1, 18),
        metrics.cpu_percent,
    )
    draw_inverted_text(image, (8, 4), f"CPU {metrics.cpu_percent:3.0f}%")
    draw_inverted_text(image, (94, 4), temperature)

    draw_usage_bar(
        image,
        (0, 22, width - 1, 40),
        metrics.ram_percent,
    )
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

    # Draw the ticker on its own image, then hide the part behind weather.
    ticker_image = Image.new("1", size)
    ImageDraw.Draw(ticker_image).text((scroll_x, bottom_y), ticker_text(info), fill="white")
    ticker_image.paste(0, (0, 0, ticker_left, height))
    image.paste(1, mask=ticker_image)
    draw.line((width // 2, 48, width // 2, height - 1), fill="white")
    return image


def main() -> None:
    """Continuously show system information until Ctrl+C is pressed."""
    display_config = DisplayConfig.from_env()
    monitor_config = MonitorConfig.from_env()
    device = display_config.create_device()
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

    print("System monitor is running. Press Ctrl+C to stop.")
    try:
        while True:
            frame_started = time.monotonic()

            if time.monotonic() - last_metrics_update >= monitor_config.refresh_seconds:
                metrics = monitor.read(sample_seconds=0)
                last_metrics_update = time.monotonic()

            if time.monotonic() - last_weather_update >= WEATHER_REFRESH_SECONDS:
                weather = weather_service.get_current()
                last_weather_update = time.monotonic()

            if time.monotonic() - last_network_update >= NETWORK_REFRESH_SECONDS:
                refreshed_info = info_provider.read()
                last_network_update = time.monotonic()
                if refreshed_info != info:
                    info = refreshed_info
                    ticker = ticker_text(info)
                    ticker_width = int(
                        ImageDraw.Draw(Image.new("1", (1, 1))).textlength(ticker)
                    )
                    ticker_started = time.monotonic()

            # Move the displayed bars gradually toward the latest measurements.
            smooth_cpu += (metrics.cpu_percent - smooth_cpu) * BAR_SMOOTHING
            smooth_ram += (metrics.ram_percent - smooth_ram) * BAR_SMOOTHING
            smooth_metrics = replace(
                metrics,
                cpu_percent=smooth_cpu,
                ram_percent=smooth_ram,
            )

            ticker_distance = int(
                (time.monotonic() - ticker_started)
                * monitor_config.scroll_pixels_per_second
            )
            ticker_area_width = device.width // 2 - 2
            scroll_x = device.width - (
                ticker_distance % (ticker_area_width + ticker_width)
            )

            show_weather_location = (
                int(time.monotonic() / WEATHER_SWITCH_SECONDS) % 2 == 1
            )

            frame = render_dashboard(
                device.size,
                smooth_metrics,
                info,
                weather,
                monitor_config.weather_unit,
                show_weather_location,
                scroll_x,
            )
            device.display(frame)

            frame_time = time.monotonic() - frame_started
            time.sleep(max(0, monitor_config.frame_seconds - frame_time))
    except KeyboardInterrupt:
        print("\nSystem monitor stopped.")
    finally:
        device.cleanup()


if __name__ == "__main__":
    main()
