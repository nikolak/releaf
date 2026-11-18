# Changelog

Versions are `major.minor.patch`:

- **Major**: requires a new board or additional or different hardware.
- **Minor**: new features, for example optional firmware or 3D-printed shell changes, or support for other parts.
- **Patch**: bug fixes only.

## Unreleased

## 1.1.0

- The shell now holds the board more firmly, so it stays put when the linker pushes against it.
- New `disableTouch` option in the usermod settings turns off the panels' own reaction to touch.
- WLED updates are no longer rejected with "Firmware release name mismatch". The check runs in the firmware you already have, so when updating from 1.0.0, tick "Ignore firmware validation" on the update page once.

## 1.0.0

- WLED usermod and build configuration for controlling Nanoleaf Shapes with an ESP32-C3 SuperMini.
- Optional controller board with KiCad files and Gerbers for PCB fabrication.
- 3D-printable shell as STEP files and a Bambu Studio project.
- Build script and GitHub releases with firmware for USB installation and WLED updates.
