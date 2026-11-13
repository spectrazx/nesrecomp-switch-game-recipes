#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
source scripts/switch-env.sh
printf 'Host: '; uname -m
cmake --version | head -n 1
printf 'Ninja: '; ninja --version
python3 --version
xcrun --find clang
printf '\nHost SDL package:\n'
pkg-config --modversion sdl2
printf '\nSwitch compiler:\n'
if [[ ! -x "$DEVKITA64/bin/aarch64-none-elf-gcc" ]]; then
  printf '%s\n' 'Switch SDK is not installed. Run bash scripts/setup-switch.sh after installing devkitPro pacman.' >&2
  exit 1
fi
file "$DEVKITA64/bin/aarch64-none-elf-gcc"
aarch64-none-elf-gcc --version | head -n 1
for path in "$DEVKITPRO/cmake/Switch.cmake" "$DEVKITPRO/libnx/include/switch.h" \
  "$DEVKITPRO/portlibs/switch/include/SDL2/SDL.h"; do
  [[ -f "$path" ]] || { printf 'Missing: %s\n' "$path" >&2; exit 1; }
done
command -v elf2nro nacptool
printf '\nSwitch package versions:\n'
/usr/local/bin/dkp-pacman -Q devkitA64 libnx switch-tools switch-cmake switch-sdl2
