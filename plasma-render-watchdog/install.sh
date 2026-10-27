#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
install -Dm644 "$source_dir/watchdog.py" "$HOME/.local/lib/cachey-qol/plasma-render-watchdog.py"
install -Dm644 "$source_dir/systemd/plasma-render-watchdog.service" "$config/plasma-render-watchdog.service"
install -Dm644 "$source_dir/systemd/plasma-render-watchdog.timer" "$config/plasma-render-watchdog.timer"
install -Dm644 "$source_dir/systemd/plasma-plasmashell.service.d/cachey-qol.conf" "$config/plasma-plasmashell.service.d/cachey-qol.conf"
systemctl --user daemon-reload
systemctl --user enable --now plasma-render-watchdog.timer
systemctl --user start plasma-render-watchdog.service
printf 'Plasma renderer watchdog installed. Logs: journalctl --user -u plasma-render-watchdog.service\n'
