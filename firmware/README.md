# Firmware

The firmware is WLED with a usermod that handles communication with the Shapes panels. You can download it from [Releases](https://github.com/nikolak/releaf/releases), or build it yourself if you want to change something. These builds are for the ESP32-C3 SuperMini with 4 MB flash.

## Installing a release

### First installation over USB

1. Download `releaf-esp32c3-factory.bin` from the release. This includes the bootloader, partition table and firmware in one file.
2. If you're using the optional PCB, **switch it OFF before connecting USB**. Connect the C3 to your computer with a USB data cable.
3. Open [Espressif's browser flasher](https://espressif.github.io/esptool-js/) in Chrome or Edge, click **Connect**, and select the C3's serial port.
4. Select the downloaded file and set its flash address to **`0x0`**. Erase the flash, then program the file. Erasing removes any existing firmware and settings on the C3.
5. Reset the C3 and continue with [Getting started](../README.md#getting-started) to set up Wi-Fi. If you're using the PCB, unplug USB before switching it back ON.

If the flasher can't connect, hold BOOT, press and release RESET, then release BOOT and try again.

### Updating Releaf

Download `releaf-esp32c3.bin`. In WLED, open **Config → Security & Updates → Update WLED**, select the file, and upload it. Use the smaller firmware file for this, not the factory image. Keep a backup of your WLED settings and presets before updating.

## Building from source

The build script downloads WLED and adds the usermod and C3 SuperMini configuration before compiling.

### Requirements

You'll need these installed before running the script:

- Git
- Node.js 20+ and npm
- PlatformIO Core (`pio`)

### Build

Run this from the Releaf repository folder:

```sh
bash firmware/build.sh
```

The first run downloads WLED and its build dependencies, then compiles the firmware and web interface. Everything goes into `firmware/build/`, which is ignored by git. If you change the usermod, just run the same command again; it copies your changes into the existing WLED checkout before building.

The WLED version is pinned in `build.sh` to a specific WLED 17 development snapshot, so a fresh build won't suddenly pick up changes from upstream.

The resulting file is `firmware/build/firmware.bin`. You can stop a build with Ctrl+C. If you want to start over, delete `firmware/build/` and run the script again. If you've added a `my_config.h`, keep a copy before deleting the build folder.

### Flash your build over USB

If you're using the optional PCB, **switch it OFF before connecting USB**. Connect the C3 to your computer and run this from the same Releaf folder:

```sh
bash firmware/build.sh -t upload
```

PlatformIO should find the USB port automatically. If it doesn't, add `--upload-port PORT` to the command, using your C3's serial port in place of `PORT`.

Once it's flashed, follow [Getting started](../README.md#getting-started) to set up Wi-Fi. TX is GPIO4 and RX is GPIO5; leave those as they are.

If you use a private `my_config.h`, put it in `firmware/build/WLED/wled00/`. That keeps it out of git along with the build files.

## Publishing a release

Releaf releases use `vMAJOR.MINOR.PATCH` tags, for example `v1.0.0`. Increase the major version for breaking changes, the minor version for new features, and the patch version for fixes. This is the Releaf release version; the pinned WLED version and the revision printed on the PCB are separate.

Keep changes under `## Unreleased` in [CHANGELOG.md](../CHANGELOG.md). When a release is ready, move those notes under a heading matching the version, such as `## 1.0.0`, and leave an empty `## Unreleased` section above it.

Once the changes are committed and pushed, tag that commit and push the tag:

```sh
git tag v1.0.0
git push origin v1.0.0
```

The [release workflow](../.github/workflows/release.yml) builds the firmware, packages the USB installation image, and creates a GitHub release with both firmware files, the Gerber ZIP and the shell 3MF from that tag. The matching changelog entry becomes the release notes. If the notes are missing or the build fails, it won't publish a release.
