# Lock-screen recovery

Recover a stuck KDE **lock screen after signing in**, without restarting the desktop session, KWin, or the initial login manager. This is separate from the Plasma desktop/taskbar watchdog.

## Requirements

KDE Plasma on Wayland with KWin owning `org.freedesktop.ScreenSaver`, systemd user services/journal, Bash, and Python 3 at `/usr/bin/python3` with `os.pidfd_open` and `signal.pidfd_send_signal`. The greeter must launch as `/usr/lib/kscreenlocker_greet`. No root access, external Python packages, or changes to PAM are required. X11 and other lockers are deliberately unsupported.

## Install

```sh
bash install.sh
```

Or select this utility from the repository root's `bash install.sh` menu. Installation enables the timer immediately. Files go into `~/.local/lib/cachy-qol/` and `${XDG_CONFIG_HOME:-~/.config}/systemd/user/`.

## Automatic recovery

Every 15 seconds, while the screen is locked:

1. Find the lock-controller PID through the session D-Bus owner. Require the current user's `kwin_wayland` command and expected launch path.
2. Inspect only that controller's direct children. Require exactly one current-user greeter with the expected command name and launch path, and reject `--nolock` processes.
3. Examine the greeter's current-boot journal entries from the last two minutes, excluding entries before its process start time. Require at least three `eglSwapBuffers failed with 0x3003` or `scenegraph is not functional` messages spanning at least one second, and a process age of at least 20 seconds.
4. Serialize recovery attempts and enforce a five-minute cooldown, including failed attempts. Revalidate the lock, controller and target. Request KDE's explicit `Lock` to end any idle-lock grace period.
5. Send SIGKILL **only to the greeter through a pidfd**. KDE's existing crash handler starts a replacement greeter with immediate locking and software rendering. The script does not launch a disconnected replacement by itself.
6. Check for a replacement greeter and a still-locked session for up to ten seconds. Log an error if recovery cannot be confirmed.

The utility never calls an unlock API, changes password requirements, signals KWin, or restarts a login manager/session. It cannot guarantee security or recovery for arbitrary KDE versions or failures inside the controller itself. KDE owns the lock boundary and crash handling; repeated crashes can lead to KDE's emergency lock screen. Review behavior after major KDE upgrades.

Normal display disconnects, `Worker not ready yet` startup messages, wrong-password attempts and authentication warnings do **not** trigger automatic recovery. Authentication-only hangs without persistent graphics errors need manual recovery; the watchdog is not a universal freeze detector.

## Manual recovery

From another terminal/TTY logged in as the same user:

```sh
/usr/bin/python3 ~/.local/lib/cachy-qol/lock-screen-recovery.py --recover
```

This bypasses only the graphics-error requirement, **not** lock/identity checks or the cooldown. It does nothing if the session is unlocked. The password prompt is interrupted and any in-progress entry must be retried. Do not use this as a substitute for normal unlocking.

Inspect status and logs:

```sh
systemctl --user status lock-screen-recovery.timer
journalctl --user -u lock-screen-recovery.service
```

Cooldown state is private under `$XDG_RUNTIME_DIR/lock-screen-recovery/`, survives oneshot exits, and is cleared when that runtime directory is removed at logout/reboot. It is shared by manual and automatic recovery.

## Uninstall

```sh
bash uninstall.sh
```

Removes only this utility's timer, service and installed script. Lock configuration and authentication settings are untouched.

## Verification and upstream behavior

Live-tested on KDE 6.8.1 / Wayland: the old greeter was replaced, the KWin PID remained unchanged, and the session stayed locked. A second attempt was suppressed by the persistent cooldown. The user confirmed the replacement password prompt worked and unlocked normally. The underlying GPU fault was not deliberately reproduced.

KDE's [`KSldApp` crash handler](https://invent.kde.org/plasma/kscreenlocker/-/blob/Plasma/6.8/ksldapp.cpp) handles an abnormal greeter exit by calling `startLockProcess(EstablishLock::Immediate)` with software rendering enabled. Normal successful exit follows a different, unlocking path; this is why the utility does not ask the greeter to exit normally. KDE also has emergency/failure paths, so this source-backed behavior is not a promise that every future version or greeter-start failure will preserve the same result.
