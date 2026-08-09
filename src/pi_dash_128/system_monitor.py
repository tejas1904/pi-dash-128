"""Reusable system metrics with psutil.

This module has no OLED dependencies. Display pages can create a
``SystemMonitor`` and periodically call ``read()`` to get fresh values.
"""

from dataclasses import dataclass
import time

import psutil


@dataclass(frozen=True)
class MetricsSnapshot:
    """A single, read-only set of system measurements."""

    cpu_percent: float
    temperature_c: float | None
    ram_used_bytes: int
    ram_total_bytes: int
    ram_percent: float
    uptime_seconds: float

    @property
    def ram_used_mb(self) -> float:
        return self.ram_used_bytes / (1024 * 1024)

    @property
    def ram_total_mb(self) -> float:
        return self.ram_total_bytes / (1024 * 1024)


class SystemMonitor:
    """Collect CPU, temperature, and memory information."""

    def read(self, sample_seconds: float = 0.2) -> MetricsSnapshot:
        """Return one snapshot of the current system state."""
        if sample_seconds < 0:
            raise ValueError("sample_seconds cannot be negative")

        memory = psutil.virtual_memory()

        return MetricsSnapshot(
            cpu_percent=psutil.cpu_percent(interval=sample_seconds),
            temperature_c=self.read_temperature_c(),
            ram_used_bytes=memory.total - memory.available,
            ram_total_bytes=memory.total,
            ram_percent=memory.percent,
            uptime_seconds=max(0.0, time.time() - psutil.boot_time()),
        )

    def read_temperature_c(self) -> float | None:
        """Return CPU temperature in Celsius, or None when unavailable."""
        if not hasattr(psutil, "sensors_temperatures"):
            return None

        temperatures = psutil.sensors_temperatures()
        if not temperatures:
            return None

        # Raspberry Pi normally exposes its CPU sensor under this name.
        cpu_sensors = temperatures.get("cpu_thermal")
        if cpu_sensors:
            return cpu_sensors[0].current

        # Other Linux systems use names such as coretemp or k10temp.
        for sensors in temperatures.values():
            for sensor in sensors:
                if sensor.current is not None:
                    return sensor.current

        return None


def main() -> None:
    """Print one snapshot without accessing the OLED."""
    monitor = SystemMonitor()
    metrics = monitor.read()
    temperature = (
        f"{metrics.temperature_c:.1f} C"
        if metrics.temperature_c is not None
        else "unavailable"
    )

    print(f"CPU usage: {metrics.cpu_percent:.1f}%")
    print(f"CPU temperature: {temperature}")
    print(
        f"RAM usage: {metrics.ram_percent:.1f}% "
        f"({metrics.ram_used_mb:.0f}/{metrics.ram_total_mb:.0f} MiB)"
    )


if __name__ == "__main__":
    main()
