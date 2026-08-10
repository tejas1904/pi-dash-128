"""Select and run an OLED dashboard design."""

from pi_dash_128.config import AppConfig, DisplayConfig
from pi_dash_128.designs import load_design


def main() -> None:
    """Continuously show system information until Ctrl+C is pressed."""
    display_config = DisplayConfig.from_env()
    app_config = AppConfig.from_env()
    design = load_design(app_config.design)
    device = display_config.create_device()

    print(f"Dashboard design {app_config.design!r} is running. Press Ctrl+C to stop.")
    try:
        design.run(device)
    except KeyboardInterrupt:
        print("\nSystem monitor stopped.")
    finally:
        device.cleanup()


if __name__ == "__main__":
    main()
