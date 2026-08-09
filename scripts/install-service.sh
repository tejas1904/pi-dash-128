#!/usr/bin/env bash

set -euo pipefail

project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
service_dir="$HOME/.config/systemd/user"
service_file="$service_dir/pi-dash-128.service"
temporary_file="$(mktemp)"
trap 'rm -f "$temporary_file"' EXIT

mkdir -p "$service_dir"
sed "s|@PROJECT_DIR@|$project_dir|g" \
    "$project_dir/systemd/pi-dash-128.service" > "$temporary_file"
install -m 0644 "$temporary_file" "$service_file"

systemctl --user daemon-reload
systemctl --user enable --now pi-dash-128.service

echo "PiDash128 is installed and running."
echo "Check it with: systemctl --user status pi-dash-128"
