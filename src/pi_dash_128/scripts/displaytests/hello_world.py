"""Simple OLED hello-world hardware test."""

from luma.core.render import canvas

from pi_dash_128.config import DisplayConfig


def main() -> None:
    config = DisplayConfig.from_env()
    device = config.create_device()

    try:
        with canvas(device) as draw:
            draw.rectangle(device.bounding_box, outline="white", fill="black")
            draw.text((8, 16), "Hello, world!", fill="white")
            draw.text((8, 34), "OLED is working", fill="white")

        input("Message displayed. Press Enter to clear the OLED... ")
    finally:
        device.cleanup()


if __name__ == "__main__":
    main()
