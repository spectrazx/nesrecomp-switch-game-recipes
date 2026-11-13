#!/bin/bash
set -euo pipefail
cd "$(dirname "$0")/.."
workspace="$PWD"
: "${NESRECOMP_SMB_ROM:?Set NESRECOMP_SMB_ROM to the absolute path of your original NES ROM}"
[[ "$NESRECOMP_SMB_ROM" = /* && -f "$NESRECOMP_SMB_ROM" ]] || {
  printf '%s\n' 'NESRECOMP_SMB_ROM must be an existing absolute file path.' >&2; exit 2;
}
bash scripts/prepare-sources.sh
engine="$workspace/.local/src/nesrecomp"
mario="$workspace/.local/src/SuperMarioBrosNESRecomp"
config="$workspace/examples/smb-vanilla.toml"
mkdir -p build/smb1
python3 "$mario/tools/verify_usa_rom.py" --rom "$NESRECOMP_SMB_ROM" \
  --crc D445F698 --mapper 0 --title 'Super Mario Bros.'
cmake -S "$engine/recompiler" -B build/recompiler -G Ninja -DCMAKE_BUILD_TYPE=Release
cmake --build build/recompiler --parallel 4
cmake -S "$engine/runner/cyc/project" -B build/smb1/host -G Ninja \
  -DCMAKE_BUILD_TYPE=Release -DNESRECOMP_HEADLESS=ON -DNESRECOMP_RECOMP_UI=OFF \
  -DNESRECOMP_HOST_COMPILER="$workspace/build/recompiler/NESRecomp" \
  -DNESRECOMP_ROM="$NESRECOMP_SMB_ROM" -DNESRECOMP_GAME_CONFIG="$config" \
  -DNESRECOMP_CYCLE_SEEDS="$mario/cyc_seeds.txt"
cmake --build build/smb1/host --parallel 4
build/smb1/host/nes_game "$NESRECOMP_SMB_ROM" --frames 600 \
  --screenshot "$workspace/build/smb1/smb-boot.png" > build/smb1/host-boot.log 2>&1
source scripts/switch-env.sh
if [[ ! -x "$DEVKITA64/bin/aarch64-none-elf-gcc" ]]; then
  image=devkitpro/devkita64@sha256:1fc388c3a0d34bd2045a6dadcb1020e069d5f876a187fd705de14b4440c00282
  docker info > /dev/null
  # Only the supplied ROM file is exposed outside the workspace mount.
  # Linux cannot run the Mach-O host compiler; build a Linux host compiler too.
  docker run --rm -v "$workspace:$workspace" -v "$NESRECOMP_SMB_ROM:/private/smb1.nes:ro" \
    -w "$workspace" "$image" bash -c '
      set -euo pipefail
      cmake -S .local/src/nesrecomp/recompiler -B build/recompiler-linux -G Ninja -DCMAKE_BUILD_TYPE=Release
      cmake --build build/recompiler-linux --parallel 4
      cmake -S .local/src/nesrecomp/runner/cyc/project -B build/smb1/switch-docker -G Ninja \
        -DCMAKE_TOOLCHAIN_FILE=/opt/devkitpro/cmake/Switch.cmake -DCMAKE_BUILD_TYPE=Release \
        -DNESRECOMP_RECOMP_UI=OFF -DNESRECOMP_HOST_COMPILER="$PWD/build/recompiler-linux/NESRecomp" \
        -DNESRECOMP_ROM=/private/smb1.nes -DNESRECOMP_GAME_CONFIG="$PWD/examples/smb-vanilla.toml" \
        -DNESRECOMP_CYCLE_SEEDS="$PWD/.local/src/SuperMarioBrosNESRecomp/cyc_seeds.txt" \
        -DNESRECOMP_SWITCH_GAME_DIR=sdmc:/switch/nesrecomp/smb1 \
        "-DNESRECOMP_SWITCH_TITLE=Super Mario Bros. Recomp"
      cmake --build build/smb1/switch-docker --parallel 4
    '
  cp build/smb1/switch-docker/nes_game.nro build/smb1/SuperMarioBrosRecomp.nro
  printf 'Built %s/build/smb1/SuperMarioBrosRecomp.nro using Docker\n' "$workspace"
  exit 0
fi
cmake -S "$engine/runner/cyc/project" -B build/smb1/switch -G Ninja \
  -DCMAKE_TOOLCHAIN_FILE="$DEVKITPRO/cmake/Switch.cmake" \
  -DCMAKE_BUILD_TYPE=Release -DNESRECOMP_RECOMP_UI=OFF \
  -DNESRECOMP_HOST_COMPILER="$workspace/build/recompiler/NESRecomp" \
  -DNESRECOMP_ROM="$NESRECOMP_SMB_ROM" -DNESRECOMP_GAME_CONFIG="$config" \
  -DNESRECOMP_CYCLE_SEEDS="$mario/cyc_seeds.txt" \
  -DNESRECOMP_SWITCH_GAME_DIR=sdmc:/switch/nesrecomp/smb1 \
  '-DNESRECOMP_SWITCH_TITLE=Super Mario Bros. Recomp'
cmake --build build/smb1/switch --parallel 4
cp build/smb1/switch/nes_game.nro build/smb1/SuperMarioBrosRecomp.nro
printf 'Built %s/build/smb1/SuperMarioBrosRecomp.nro\n' "$workspace"
