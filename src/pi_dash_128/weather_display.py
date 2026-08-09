"""Render weather information and Font Awesome weather icons."""

from pathlib import Path

from PIL import ImageDraw, ImageFont

from pi_dash_128.weather import Weather


ICON_FONT = ImageFont.truetype(
    Path(__file__).parent / "assets/fonts/fontawesome-solid.otf",
    size=10,
)

SUNNY_CODES = {113}
FOG_CODES = {143, 248, 260}
THUNDER_CODES = {200, 386, 389, 392, 395}
SNOW_CODES = {
    179, 182, 185, 227, 230, 323, 326, 329, 332,
    335, 338, 368, 371, 374, 377,
}
RAIN_CODES = {
    176, 263, 266, 281, 284, 293, 296, 299, 302,
    305, 308, 311, 314, 317, 320, 350, 353, 356, 359, 362, 365,
}


def weather_icon(weather_code: int | None) -> str:
    """Return a Font Awesome glyph for a wttr.in weather code."""
    if weather_code in SUNNY_CODES:
        return "\uf185"  # sun
    if weather_code in FOG_CODES:
        return "\uf75f"  # smog
    if weather_code in THUNDER_CODES:
        return "\uf0e7"  # lightning bolt
    if weather_code in SNOW_CODES:
        return "\uf2dc"  # snowflake
    if weather_code in RAIN_CODES:
        return "\uf73d"  # cloud with rain
    return "\uf0c2"  # cloud


def weather_text(weather: Weather, unit: str) -> str:
    """Format the current outdoor temperature and condition."""
    if unit == "F" and weather.temperature_f is not None:
        return f"{weather.temperature_f}F {weather.condition}"
    if weather.temperature_c is not None:
        return f"{weather.temperature_c}C {weather.condition}"
    return weather.condition


def draw_weather(
    draw: ImageDraw.ImageDraw,
    weather: Weather,
    unit: str,
    show_location: bool,
    position: tuple[int, int],
) -> None:
    """Draw either the detected location or icon and current weather."""
    x, y = position

    if show_location:
        draw.text((x, y), weather.location[:10], fill="white")
    elif weather.weather_code is None:
        draw.text((x, y), weather.condition[:10], fill="white")
    else:
        draw.text(
            (x, y),
            weather_icon(weather.weather_code),
            font=ICON_FONT,
            fill="white",
        )
        draw.text((x + 12, y), weather_text(weather, unit)[:8], fill="white")
