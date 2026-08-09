"""OLED resolution and alignment hardware test."""

from luma.core.render import canvas

from pi_dash_128.config import DisplayConfig


def main() -> None:
    config = DisplayConfig.from_env()
    device = config.create_device()
    right = device.width - 1
    bottom = device.height - 1
    center_x = right // 2
    center_y = bottom // 2

    try:
        with canvas(device) as draw:
            draw.rectangle((0, 0, right, bottom), outline="white", fill="black")

            draw.rectangle((2, 2, 7, 7), fill="white")
            draw.rectangle((right - 7, 2, right - 2, 7), fill="white")
            draw.rectangle((2, bottom - 7, 7, bottom - 2), fill="white")
            draw.rectangle((right - 7, bottom - 7, right - 2, bottom - 2), fill="white")

            draw.line((center_x, 10, center_x, bottom - 10), fill="white")
            draw.line((10, center_y, right - 10, center_y), fill="white")

            draw.text((11, 3), f"{device.width} x {device.height}", fill="white")
            draw.text((11, bottom - 11), "EDGE TEST", fill="white")

        input("Resolution test displayed. Press Enter to clear... ")
    finally:
        device.cleanup()


if __name__ == "__main__":
    main()
