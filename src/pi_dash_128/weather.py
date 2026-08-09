"""Current weather from wttr.in."""

from dataclasses import dataclass
import json
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class Weather:
    temperature_c: int | None
    temperature_f: int | None
    condition: str
    location: str
    weather_code: int | None


class WeatherService:
    """Get weather for the public IP address of this Raspberry Pi."""

    def get_current(self) -> Weather:
        request = Request(
            "https://wttr.in/?format=j1",
            headers={"User-Agent": "PiDash128"},
        )

        try:
            with urlopen(request, timeout=5) as response:
                data = json.load(response)

            current = data["current_condition"][0]
            location = data["nearest_area"][0]["areaName"][0]["value"]
            return Weather(
                temperature_c=int(current["temp_C"]),
                temperature_f=int(current["temp_F"]),
                condition=current["weatherDesc"][0]["value"],
                location=location,
                weather_code=int(current["weatherCode"]),
            )
        except (OSError, KeyError, IndexError, TypeError, ValueError):
            return Weather(
                temperature_c=None,
                temperature_f=None,
                condition="No weather",
                location="Unknown",
                weather_code=None,
            )
