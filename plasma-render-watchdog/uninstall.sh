#!/usr/bin/env bash
set -euo pipefail
config="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
systemctl --user disable --now plasma-render-watchdog.timer
systemctl --user stop plasma-render-watchdog.service
rm -f -- "$config/plasma-render-watchdog.timer" "$config/plasma-render-watchdog.service" \
    "$config/plasma-plasmashell.service.d/cachey-qol.conf" \
    "$HOME/.local/lib/cachey-qol/plasma-render-watchdog.py"
systemctl --user daemon-reload
printf 'Plasma renderer watchdog removed. Other Plasma overrides were left unchanged.\n'
