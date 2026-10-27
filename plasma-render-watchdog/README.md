# Plasma renderer watchdog

Recovers a KDE Plasma desktop/taskbar that stops rendering after a display disconnect/reconnect. It restarts only `plasma-plasmashell.service`, not KWin, the login session, or applications. Desktop widgets and notifications are briefly interrupted.

## Requirements

Linux, KDE Plasma using `plasma-plasmashell.service`, a systemd user manager/journal, Bash, and Python 3 at `/usr/bin/python3`. No root access or Python packages are required.

## Install

```sh
bash install.sh
```

The installer copies the watchdog to `~/.local/lib/cachey-qol/`, installs units in `${XDG_CONFIG_HOME:-~/.config}/systemd/user/`, enables the user timer, and performs an initial check. Re-running updates the installed files. It does not ordinarily restart Plasma during installation.

## Recovery policy

- Check every 15 seconds, starting 30 seconds after the user manager starts.
- Examine the last two minutes of logs from **only the current Plasma invocation**.
- Trigger only on `Failed to create QRhi on the render thread; scenegraph is not functional`.
- Ignore ordinary monitor disconnects, old process errors, and inactive Plasma sessions.
- Record an attempt before restarting, with a five-minute cooldown even if recovery fails.
- Reduce Plasma's graceful shutdown timeout to 10 seconds using a dedicated drop-in; systemd can then kill a stuck shell and replace it.
- Keep cooldown state private under `$XDG_RUNTIME_DIR/plasma-render-watchdog/`; it is cleared when the runtime directory is removed at logout/reboot.

This detects a specific observed fatal renderer failure, not every freeze. A running process or successful D-Bus ping alone does not prove rendering works. This does not prevent display-link or driver faults. Existing systemd crash recovery remains unchanged. Journal/query/restart errors fail the watchdog service and appear in its journal; the timer schedules another check.

## Inspect / recover manually

```sh
systemctl --user status plasma-render-watchdog.timer
journalctl --user -u plasma-render-watchdog.service
systemctl --user show plasma-plasmashell.service -p TimeoutStopUSec
# Manual restart bypasses the watchdog cooldown:
systemctl --user restart plasma-plasmashell.service
```

## Uninstall

```sh
bash uninstall.sh
```

Removes only this utility's installed files and override. It does not restart Plasma, reset your panel configuration, or remove other service overrides.
