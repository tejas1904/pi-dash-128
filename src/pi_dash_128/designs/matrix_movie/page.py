"""Official Luma Matrix motion with falling live system information."""

from random import choice, gauss, randint
import time

from luma.core.render import canvas
from luma.core.sprite_system import framerate_regulator

from pi_dash_128.designs.matrix_movie.config import MatrixMovieConfig
from pi_dash_128.system_info import SystemInfoProvider
from pi_dash_128.system_monitor import SystemMonitor


TINY_FONT = {
    "0": (7, 5, 5, 5, 7), "1": (2, 6, 2, 2, 7),
    "2": (7, 1, 7, 4, 7), "3": (7, 1, 7, 1, 7),
    "4": (5, 5, 7, 1, 1), "5": (7, 4, 7, 1, 7),
    "6": (7, 4, 7, 5, 7), "7": (7, 1, 1, 1, 1),
    "8": (7, 5, 7, 5, 7), "9": (7, 5, 7, 1, 7),
    "A": (2, 5, 7, 5, 5), "C": (7, 4, 4, 4, 7),
    "E": (7, 4, 6, 4, 7), "I": (7, 2, 2, 2, 7),
    "M": (5, 7, 7, 5, 5),
    "N": (5, 7, 7, 7, 5), "P": (6, 5, 6, 4, 4),
    "R": (6, 5, 6, 5, 5), "T": (7, 2, 2, 2, 2),
    "U": (5, 5, 5, 5, 7), "-": (0, 0, 7, 0, 0),
    ":": (0, 2, 0, 2, 0),
}


def draw_tiny_text(draw, position: tuple[int, int], text: str, fill) -> None:
    """Draw compact 3x5 telemetry characters on the pixel grid."""
    origin_x, origin_y = position
    for index, character in enumerate(text):
        for row, bits in enumerate(TINY_FONT.get(character, TINY_FONT["-"])):
            for column in range(3):
                if bits & (1 << (2 - column)):
                    draw.point((origin_x + index * 4 + column, origin_y + row), fill=fill)


def stat_text(kind, metrics, info) -> str:
    if kind == "CPU":
        return f"CPU:{metrics.cpu_percent:.0f}"
    if kind == "RAM":
        return f"RAM:{metrics.ram_percent:.0f}"
    if kind == "TMP":
        value = "--" if metrics.temperature_c is None else f"{metrics.temperature_c:.0f}"
        return f"TMP:{value}"
    return f"IP:{(info.local_ip or '--').split('.')[-1]}"


class Design:
    def __init__(self) -> None:
        self.config = MatrixMovieConfig.load()

    def run(self, device) -> None:
        # This palette and rain population loop come directly from Luma's
        # official matrix.py. Falling stat_people are the only added layer.
        wrd_rgb = [
            (154, 173, 154),
            (0, 255, 0),
            (0, 235, 0),
            (0, 220, 0),
            (0, 185, 0),
            (0, 165, 0),
            (0, 128, 0),
            (0, 0, 0),
            (154, 173, 154),
            (0, 145, 0),
            (0, 125, 0),
            (0, 100, 0),
            (0, 80, 0),
            (0, 60, 0),
            (0, 40, 0),
            (0, 0, 0),
        ]
        monitor = SystemMonitor()
        info_provider = SystemInfoProvider()
        metrics = monitor.read(sample_seconds=0.1)
        info = info_provider.read()
        refreshed = time.monotonic()
        clock = 0
        blue_pilled_population = []
        stat_people = []
        max_population = device.width * 8
        regulator = framerate_regulator(fps=self.config.fps)

        def increase_population() -> None:
            blue_pilled_population.append(
                [randint(0, device.width), 0, gauss(1.2, 0.6)]
            )

        while True:
            clock += 1
            now = time.monotonic()
            if now - refreshed >= self.config.refresh_seconds:
                metrics = monitor.read(sample_seconds=0)
                info = info_provider.read()
                refreshed = now

            with regulator:
                with canvas(device, dither=True) as draw:
                    for person in blue_pilled_population:
                        x, y, speed = person
                        for rgb in wrd_rgb:
                            if 0 <= y < device.height:
                                draw.point((x, y), fill=rgb)
                            y -= 1
                        person[1] += speed

                    for person in stat_people:
                        x, y, speed, kind = person
                        draw_tiny_text(
                            draw,
                            (x, round(y)),
                            stat_text(kind, metrics, info),
                            fill=(210, 255, 210),
                        )
                        person[1] += speed

            if clock % 5 == 0 or clock % 3 == 0:
                increase_population()

            if clock % self.config.stat_interval_frames == 0:
                stat_people.append(
                    [randint(1, max(1, device.width - 26)), -6, gauss(0.8, 0.15), choice(("CPU", "RAM", "TMP", "IP"))]
                )

            stat_people[:] = [person for person in stat_people if person[1] < device.height]
            while len(blue_pilled_population) > max_population:
                blue_pilled_population.pop(0)
