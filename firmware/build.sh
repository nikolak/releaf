#!/usr/bin/env bash
set -euo pipefail

FIRMWARE_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="$FIRMWARE_DIR/build"
WLED_DIR="$BUILD_DIR/WLED"
# WLED 17 development snapshot used by the ESP32-C3 usermod.
WLED_REVISION=961961fdde8c22150a0212243621ee71bc9a7639

for command in git node npm pio; do
  if ! command -v "$command" >/dev/null 2>&1; then
    printf 'Missing %s. See firmware/README.md for requirements.\n' "$command" >&2
    exit 1
  fi
done

mkdir -p "$BUILD_DIR"
if [[ ! -d "$WLED_DIR/.git" ]]; then
  git init -q "$WLED_DIR"
  git -C "$WLED_DIR" remote add origin https://github.com/wled/WLED.git
  git -C "$WLED_DIR" fetch --depth 1 origin "$WLED_REVISION"
  git -C "$WLED_DIR" checkout --detach "$WLED_REVISION"
fi
if [[ "$(git -C "$WLED_DIR" rev-parse HEAD)" != "$WLED_REVISION" ]]; then
  printf 'WLED checkout does not match the version required by build.sh.\n' >&2
  printf 'Save any private my_config.h, remove firmware/build/WLED, and rerun.\n' >&2
  exit 1
fi

cp -R "$FIRMWARE_DIR/usermods/nanoleaf_shapes" "$WLED_DIR/usermods/"
cp "$FIRMWARE_DIR/platformio_override.ini" "$WLED_DIR/platformio_override.ini"

export npm_config_cache="$BUILD_DIR/npm-cache"
export PLATFORMIO_CORE_DIR="$BUILD_DIR/platformio"
export PLATFORMIO_BUILD_CACHE_DIR="$BUILD_DIR/cache"

cd "$WLED_DIR"
# WLED's PlatformIO hook also builds the web interface.
pio run -e esp32c3_releaf "$@"
cp .pio/build/esp32c3_releaf/firmware.bin "$BUILD_DIR/firmware.bin"
printf '\nFirmware: %s/firmware.bin\n' "$BUILD_DIR"
