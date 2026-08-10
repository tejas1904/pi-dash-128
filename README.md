# PiDash128

PiDash128 is a compact Raspberry Pi dashboard for a 128×64 I²C OLED. It shows
CPU load, temperature, RAM usage, IP-based weather, and scrolling user/network
information.

<img src="assets/pic.jpg" alt="PiDash128 running on a 128x64 OLED" width="25%">

## Design previews

| Alien | BioTech | Cyberpunk | F1 | Matrix Movie |
|:---:|:---:|:---:|:---:|:---:|
| <img src="assets/alien.jpg" alt="Alien dashboard design" width="125"> | <img src="assets/biotech.jpg" alt="BioTech dashboard design" width="125"> | <img src="assets/cyberpunk.jpg" alt="Cyberpunk dashboard design" width="125"> | <img src="assets/f1.jpg" alt="F1 dashboard design" width="125"> | <img src="assets/matrix_movie.jpg" alt="Matrix Movie dashboard design" width="125"> |

## Hardware

- Raspberry Pi
- 128×64 SH1106 OLED connected over I²C
- Default I²C bus `1` and address `0x3C`

## Setup

```bash
cp .env.example .env
uv sync
```

Adjust `.env` for your display, then run:

```bash
uv run pi-dash-128
```

Press `Ctrl+C` to stop.

## Test commands

```bash
uv run pidash128-hello-test
uv run pidash128-resolution-test
uv run pidash128-system-info
```

## Designs

Select a display design in `.env` with `DASHBOARD_DESIGN`; the default is
`classic`.

Available designs are:

- `classic` — CPU and RAM bars, weather, and a scrolling network ticker
- `biotech` — living cell colonies, bio-link status, and molecular animation
- `alien` — C-shaped living cells with animated liquid fill
- `cyberpunk` — Neuromancer ICE deck with animated circuit-board traces
- `matrix_movie` — single-pixel rain with randomly falling live stat values
- `f1` — rev lights, segmented meters, CPU trace, system and network telemetry
- `steampunk` — gauges, rotating gears, and rising steam

Design-specific settings are stored in the selected design's `config.env`.
To add another design, create a design folder following the same structure;
no central registration is needed.

Weather is provided by [wttr.in](https://wttr.in/) using IP-based location detection.
Set `WEATHER_UNIT=C` or `WEATHER_UNIT=F` in the page's `config.env` to choose
the outdoor temperature unit.
Weather icons use [Font Awesome Free](https://fontawesome.com/) under the SIL
Open Font License included with the packaged font.

## Start automatically

Install and start the systemd user service:

```bash
uv sync
./scripts/install-service.sh
sudo loginctl enable-linger "$USER"
```

Linger allows the user service to start during boot without an interactive
login. While developing, stop the background dashboard before running it
manually:

```bash
systemctl --user stop pi-dash-128
uv run pi-dash-128
```

Useful service commands:

```bash
systemctl --user start pi-dash-128
systemctl --user restart pi-dash-128
systemctl --user status pi-dash-128
journalctl --user -u pi-dash-128 -f
systemctl --user disable --now pi-dash-128
```
