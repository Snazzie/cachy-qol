#!/usr/bin/env bash
set -euo pipefail
config="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
systemctl --user disable --now lock-screen-recovery.timer
systemctl --user stop lock-screen-recovery.service
rm -f -- "$config/lock-screen-recovery.timer" "$config/lock-screen-recovery.service" \
    "$HOME/.local/lib/cachy-qol/lock-screen-recovery.py"
systemctl --user daemon-reload
printf 'Lock-screen recovery removed. Lock and authentication settings left unchanged.\n'
