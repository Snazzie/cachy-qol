# cachy-qol

Standalone Linux desktop quality-of-life utilities. Each utility lives in its own folder with its own README, dependencies, installation and removal instructions.

- [plasma-render-watchdog](plasma-render-watchdog/): recover the desktop/taskbar after Plasma's fatal Qt renderer failure without logging out.
- [lock-screen-recovery](lock-screen-recovery/): replace a failed KDE Wayland lock-screen greeter while retaining the session and password authentication.

## Install

From an interactive terminal, run:

```sh
bash install.sh
```

All utilities are selected by default:

- **Up/Down**: move between utilities.
- **Space**: toggle the highlighted utility.
- **A**: select all utilities again.
- **Enter**: install the selected utilities.
- **Q**: quit without installing.

An empty selection will not install anything; select a utility or quit.
Installers run sequentially and stop on the first failure; already completed
installations are not rolled back. Each utility can also be installed directly
using the instructions in its own README.

The menu discovers immediate child folders containing `install.sh`, so new
utilities need no root-menu changes. It requires Bash and an interactive
ANSI-compatible terminal; each utility has its own additional requirements.
