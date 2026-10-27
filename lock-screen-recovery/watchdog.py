#!/usr/bin/python3
"""Recover a KDE Wayland lock greeter, never the compositor or session.

Default: require repeated recent graphics failures. --recover: request one
manual recovery without requiring a log signature. Both modes require an
actively locked session, a password-requiring greeter parented by the current
ScreenSaver owner, and a persistent five-minute cooldown. Linux pidfds prevent
PID-reuse races. KDE handles greeter respawn and software-rendering fallback.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import time

BUS = "org.freedesktop.ScreenSaver"
GREETER = Path("/usr/lib/kscreenlocker_greet")
COOLDOWN = 300


def command(*args):
    result = subprocess.run(args, capture_output=True, text=True, timeout=10)
    result.check_returncode()
    return result.stdout.strip()


def locked():
    return command("/usr/bin/busctl", "--user", "call", BUS, "/ScreenSaver", BUS, "GetActive") == "b true"


def controller():
    value = command("/usr/bin/busctl", "--user", "call", "org.freedesktop.DBus",
                    "/org/freedesktop/DBus", "org.freedesktop.DBus",
                    "GetConnectionUnixProcessID", "s", BUS)
    pid = int(value.removeprefix("u "))
    proc = Path(f"/proc/{pid}")
    # KWin's CAP_SYS_NICE can make /proc/PID/exe unreadable to its own user.
    # Bind to the bus-owned PID, UID, command name, and launch path instead.
    executable = (proc / "cmdline").read_bytes().split(b"\0", 1)[0]
    if (proc.stat().st_uid != os.getuid()
            or (proc / "comm").read_text().strip() != "kwin_wayland"
            or executable != b"/usr/bin/kwin_wayland"):
        raise RuntimeError("Recovery supports only the current user's KDE Wayland lock controller")
    return pid


def greeters(parent):
    found = []
    children = set()
    for task in Path(f"/proc/{parent}/task").iterdir():
        try:
            children.update((task / "children").read_text().split())
        except FileNotFoundError:
            continue
    for child in children:
        proc = Path("/proc") / child
        try:
            if proc.stat().st_uid != os.getuid() or (proc / "comm").read_text().strip() != "kscreenlocker_g":
                continue
            status = dict(line.split(":", 1) for line in (proc / "status").read_text().splitlines())
            args = (proc / "cmdline").read_bytes().split(b"\0")
            if int(status["PPid"]) == parent and args[0] == os.fsencode(GREETER) and b"--nolock" not in args:
                # Field 22 (starttime), accounting for spaces in the comm field.
                start = int((proc / "stat").read_text().rsplit(")", 1)[1].split()[19]) / os.sysconf("SC_CLK_TCK")
                found.append((int(proc.name), start))
        except (FileNotFoundError, ProcessLookupError, PermissionError):
            continue
    return found


def rendering_failed(pid, started):
    raw = command("/usr/bin/journalctl", "--user", "-b", "_PID=" + str(pid),
                  "_UID=" + str(os.getuid()), "--since=-2min", "--output=json", "--quiet", "--no-pager")
    failures = []
    for line in raw.splitlines():
        entry = json.loads(line)
        message = entry.get("MESSAGE", "")
        stamp = int(entry["__MONOTONIC_TIMESTAMP"]) / 1_000_000
        if stamp < started:
            continue
        if "eglSwapBuffers failed with 0x3003" in message or "scenegraph is not functional" in message:
            failures.append(stamp)
    # Avoid one-off transitions and startup; require persistent rendering failure.
    return len(failures) >= 3 and max(failures) - min(failures) >= 1 and time.monotonic() - started >= 20


def main(manual=False):
    if not locked():
        if manual:
            print("Session is not locked; nothing changed.")
        return
    parent = controller()
    targets = greeters(parent)
    if len(targets) != 1:
        if manual:
            raise RuntimeError("Expected exactly one password-requiring greeter; nothing changed")
        return
    pid, started = targets[0]
    if not manual and not rendering_failed(pid, started):
        return
    runtime = Path(os.environ.get("XDG_RUNTIME_DIR", f"/run/user/{os.getuid()}")) / "lock-screen-recovery"
    runtime.mkdir(mode=0o700, exist_ok=True)
    # Serialize manual runs and the timer as well as preserving cooldown state.
    import fcntl
    with (runtime / "state").open("a+") as state:
        fcntl.flock(state, fcntl.LOCK_EX)
        state.seek(0)
        previous = state.read().strip()
        now = time.monotonic()
        if previous and now - float(previous) < COOLDOWN:
            print("Lock greeter recovery suppressed by five-minute cooldown.", flush=True)
            return
        fd = os.pidfd_open(pid)
        try:
            # Re-check both the lock and process identity immediately before signalling.
            if not locked() or controller() != parent or (pid, started) not in greeters(parent):
                print("Lock state changed; recovery cancelled.", flush=True)
                return
            # KDE's explicit Lock request ends any idle-lock grace period.
            command("/usr/bin/busctl", "--user", "call", BUS, "/ScreenSaver", BUS, "Lock")
            if not locked():
                raise RuntimeError("Lock could not be confirmed; nothing signalled")
            state.seek(0)
            state.truncate()
            state.write(str(now))
            state.flush()
            print(f"Replacing lock greeter PID {pid}; leaving the compositor and session running.", flush=True)
            signal.pidfd_send_signal(fd, signal.SIGKILL)
        finally:
            os.close(fd)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if not locked():
                raise RuntimeError("Session became unlocked during recovery; inspect KDE logs")
            replacements = greeters(parent)
            if len(replacements) == 1 and replacements[0][0] != pid:
                print(f"Replacement greeter PID {replacements[0][0]} detected; session remains locked.", flush=True)
                return
            time.sleep(0.2)
        raise RuntimeError("No replacement greeter detected; session recovery requires manual attention")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--recover", action="store_true", help="manually recover a locked greeter without requiring graphics errors")
    main(parser.parse_args().recover)
