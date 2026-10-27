#!/usr/bin/python3
"""Recover Plasma's fatal Qt renderer failure without restarting the session.

Run by the supplied user timer every 15 seconds. Only inspect the current
Plasma invocation's last two minutes of logs; ordinary display disconnects
are ignored. Record attempts before restarting, with a five-minute cooldown.
Runtime state is private, survives oneshot exits, and disappears on logout.
"""

import os
from pathlib import Path
import subprocess
import time

UNIT = "plasma-plasmashell.service"
FATAL = "Failed to create QRhi on the render thread; scenegraph is not functional"
COOLDOWN = 300


def command(*args, timeout=10, allow_no_matches=False):
    result = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
    if not (allow_no_matches and result.returncode == 1 and not result.stdout and not result.stderr):
        result.check_returncode()
    return result.stdout.strip()


def main():
    properties = dict(line.split("=", 1) for line in command(
        "/usr/bin/systemctl", "--user", "show", UNIT,
        "--property=ActiveState", "--property=InvocationID",
    ).splitlines())
    invocation = properties.get("InvocationID")
    if properties.get("ActiveState") != "active" or not invocation:
        return

    failure = command(
        "/usr/bin/journalctl", "--user", "--unit=" + UNIT,
        "_SYSTEMD_INVOCATION_ID=" + invocation, "--since=-2min",
        "--grep=" + FATAL, "--lines=1", "--output=cat", "--quiet", "--no-pager",
        allow_no_matches=True,
    )
    if FATAL not in failure:
        return

    state = Path(os.environ["RUNTIME_DIRECTORY"]) / "last-attempt"
    now = time.monotonic()
    try:
        previous = float(state.read_text())
    except FileNotFoundError:
        previous = None
    if previous is not None and now - previous < COOLDOWN:
        print("Renderer failure detected; recovery suppressed by five-minute cooldown.", flush=True)
        return

    # Persist first: failed restarts must not cause a restart storm either.
    state.write_text(str(now))
    print(f"Fatal renderer failure in Plasma invocation {invocation}; restarting {UNIT}.", flush=True)
    command("/usr/bin/systemctl", "--user", "restart", UNIT, timeout=65)
    print("Plasma desktop shell restarted; session and applications left running.", flush=True)


if __name__ == "__main__":
    main()
