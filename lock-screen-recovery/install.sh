#!/usr/bin/env bash
set -euo pipefail
source_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
config="${XDG_CONFIG_HOME:-$HOME/.config}/systemd/user"
/usr/bin/python3 -c 'import os, signal; assert hasattr(os, "pidfd_open") and hasattr(signal, "pidfd_send_signal"), "Python/Linux pidfd support required"'
install -Dm644 "$source_dir/watchdog.py" "$HOME/.local/lib/cachy-qol/lock-screen-recovery.py"
install -Dm644 "$source_dir/systemd/lock-screen-recovery.service" "$config/lock-screen-recovery.service"
install -Dm644 "$source_dir/systemd/lock-screen-recovery.timer" "$config/lock-screen-recovery.timer"
systemctl --user daemon-reload
systemctl --user enable --now lock-screen-recovery.timer
systemctl --user start lock-screen-recovery.service
printf 'Lock-screen recovery installed. Logs: journalctl --user -u lock-screen-recovery.service\n'
